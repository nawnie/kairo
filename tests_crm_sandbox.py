import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from kairo_crm import Context,Change
from kairo_crm.sandbox import SandboxCRM

NOW='2026-10-09T20:00:00Z'
END='2026-10-09T21:00:00Z'

class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/'synthetic.sqlite')
        self.crm=SandboxCRM(self.path)
        self.ctx=Context('a',('p',),'owner','run')
        self.crm.seed(self.ctx,'task1',{'task.status':'open','task.priority':'normal'})
        self.changes=[Change('task1','p','task.status','open','review',1,('crm:p:task1:task.status:1',)),
                      Change('task1','p','task.priority','normal','high',1,('crm:p:task1:task.priority:1',))]
        self.p=self.crm.preview(self.ctx,self.changes,NOW,END)
    def tearDown(self):
        self.crm.close()
        self.tmp.cleanup()
    def execute(self,**kw):
        return self.crm.execute(self.ctx,self.p.proposal_id,[0],NOW,**kw)
    def counts(self):
        return [self.crm.db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['receipts','outbox']]
    def test_selected_only(self):
        self.execute()
        values={e.field:e.value for e in self.crm.snapshot(self.ctx,'task1',NOW,END)}
        self.assertEqual(values,{'task.status':'review','task.priority':'normal'})
        self.assertEqual(self.counts(),[1,1])
    def test_multiple_fields_one_revision(self):
        self.crm.execute(self.ctx,self.p.proposal_id,[0,1],NOW)
        self.assertEqual({e.revision for e in self.crm.snapshot(self.ctx,'task1',NOW,END)},{2})
    def test_retry_after_restart(self):
        first=self.execute()
        self.crm.close(); self.crm=SandboxCRM(self.path)
        self.assertEqual(first,self.execute())
        self.assertEqual(self.counts(),[1,1])
    def test_different_replay_denied(self):
        self.execute()
        with self.assertRaises(ValueError): self.crm.execute(self.ctx,self.p.proposal_id,[1],NOW)
    def test_rollback_at_each_boundary(self):
        for fault in ['after_write','before_commit']:
            with self.assertRaises(RuntimeError): self.execute(fault=fault)
            self.assertEqual(self.counts(),[0,0])
            self.assertEqual(self.crm.snapshot(self.ctx,'task1',NOW,END)[0].revision,1)
        self.execute()
    def test_permission_revocation(self):
        self.crm.db.execute('DELETE FROM grants')
        with self.assertRaises(ValueError): self.execute()
        self.assertEqual(self.counts(),[0,0])
    def test_foreign_actor_and_tenant(self):
        for ctx in [replace(self.ctx,actor_id='intruder'),replace(self.ctx,tenant_id='b')]:
            with self.assertRaises(ValueError): self.crm.execute(ctx,self.p.proposal_id,[0],NOW)
    def test_record_conflict(self):
        self.crm.db.execute('UPDATE records SET revision=2')
        with self.assertRaises(ValueError): self.execute()
        self.assertEqual(self.counts(),[0,0])
    def test_expiry(self):
        with self.assertRaises(ValueError): self.crm.execute(self.ctx,self.p.proposal_id,[0],END)
    def test_same_revision_wrong_value(self):
        self.crm.db.execute('UPDATE records SET data=?',('{"task.status":"closed"}',))
        with self.assertRaises(ValueError): self.execute()
    def test_bad_model_candidate(self):
        p=self.crm.preview(self.ctx,[replace(self.changes[0],after='delete everything')],NOW,END)
        with self.assertRaises(ValueError): self.crm.execute(self.ctx,p.proposal_id,[0],NOW)
        self.assertEqual(self.counts(),[0,0])
    def test_two_connections_cannot_double_apply(self):
        other=SandboxCRM(self.path)
        try:
            first=self.execute()
            self.assertEqual(first,other.execute(self.ctx,self.p.proposal_id,[0],NOW))
            self.assertEqual(self.counts(),[1,1])
        finally: other.close()

if __name__=='__main__': unittest.main()
