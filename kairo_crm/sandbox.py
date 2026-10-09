"""Synthetic SQLite CRM adapter. Not a production identity or sync service."""
import json
from dataclasses import asdict
import sqlite3
from collections import defaultdict
from .engine import Evidence, Proposal, digest, propose, validate_approval

FIELDS = {'task.status', 'task.priority', 'task.note'}

class SandboxCRM:
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS records(tenant TEXT, property TEXT, id TEXT,
            revision INTEGER, data TEXT, PRIMARY KEY(tenant,property,id));
        CREATE TABLE IF NOT EXISTS grants(tenant TEXT, actor TEXT, property TEXT,
            PRIMARY KEY(tenant,actor,property));
        CREATE TABLE IF NOT EXISTS proposals(hash TEXT PRIMARY KEY, payload TEXT);
        CREATE TABLE IF NOT EXISTS receipts(hash TEXT PRIMARY KEY, request_hash TEXT,
            body TEXT);
        CREATE TABLE IF NOT EXISTS outbox(hash TEXT PRIMARY KEY, body TEXT);
        ''')

    def close(self):
        self.db.close()

    def seed(self, context, record_id, data, revision=1):
        """Fixture setup only. Never expose this method to model/client input."""
        for prop in context.property_ids:
            self.db.execute('INSERT INTO grants VALUES(?,?,?)',
                            (context.tenant_id, context.actor_id, prop))
            self.db.execute('INSERT INTO records VALUES(?,?,?,?,?)',
                            (context.tenant_id,prop,record_id,revision,json.dumps(data)))

    def authorized(self, context):
        return all(self.db.execute('SELECT 1 FROM grants WHERE tenant=? AND actor=? AND property=?',
                   (context.tenant_id,context.actor_id,p)).fetchone()
                   for p in context.property_ids)

    def snapshot(self, context, record_id, now, expires_at):
        if not self.authorized(context):
            raise ValueError('unauthorized scope')
        result=[]
        for prop in context.property_ids:
            row=self.db.execute('SELECT revision,data FROM records WHERE tenant=? AND property=? AND id=?',
                                (context.tenant_id,prop,record_id)).fetchone()
            if row:
                rev,raw=row
                for field,value in json.loads(raw).items():
                    result.append(Evidence(f'crm:{prop}:{record_id}:{field}:{rev}',context.tenant_id,
                        prop,record_id,field,value,rev,now,expires_at,digest(json.loads(raw)),True))
        return result

    def preview(self, context, changes, now, expires_at):
        sources=[]
        for rid in sorted({c.record_id for c in changes}):
            sources.extend(self.snapshot(context,rid,now,expires_at))
        proposal=propose(context,changes,sources,FIELDS,now,expires_at)
        self.db.execute('INSERT OR IGNORE INTO proposals VALUES(?,?)',
                        (proposal.proposal_id,proposal.payload_json))
        return proposal

    def execute(self, context, proposal_hash, selected, now, *, fault=None):
        """Synthetic approval endpoint: server-owned payload and atomic write.

        Calling this method represents an explicit human approval in the fixture.
        Real deployment needs authenticated approval transport and real RBAC.
        """
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if not self.authorized(context):
                raise ValueError('unauthorized actor or property')
            row=self.db.execute('SELECT payload FROM proposals WHERE hash=?',(proposal_hash,)).fetchone()
            if not row: raise ValueError('unknown proposal')
            p=Proposal(proposal_hash,row[0])
            request_hash=digest(dict(context=asdict(context),selected=selected))
            prior=self.db.execute('SELECT request_hash,body FROM receipts WHERE hash=?',(proposal_hash,)).fetchone()
            if prior:
                if request_hash != prior[0]: raise ValueError('approval already consumed with different selection')
                self.db.execute('COMMIT')
                return json.loads(prior[1])
            records={}
            for change in p.payload()['changes']:
                key=(change['property_id'],change['record_id'])
                row=self.db.execute('SELECT revision,data FROM records WHERE tenant=? AND property=? AND id=?',
                                   (context.tenant_id,*key)).fetchone()
                if row: records[key]=(row[0],json.loads(row[1]))
            approved=validate_approval(p,context,proposal_hash,selected,
                                      {k:v[0] for k,v in records.items()},now,True)
            grouped=defaultdict(list)
            for change in approved:
                if change['field'] not in FIELDS: raise ValueError('field not allowed')
                if change['field']=='task.status' and change['after'] not in {'open','review','closed'}:
                    raise ValueError('invalid task status')
                if change['field']=='task.priority' and change['after'] not in {'low','normal','high'}:
                    raise ValueError('invalid task priority')
                if change['field']=='task.note' and (not isinstance(change['after'],str) or len(change['after'])>4000):
                    raise ValueError('invalid task note')
                grouped[(change['property_id'],change['record_id'])].append(change)
            for key,changes in grouped.items():
                rev,data=records[key]
                for change in changes:
                    if digest(data.get(change['field'])) != digest(change['before']):
                        raise ValueError('before value mismatch')
                    data[change['field']]=change['after']
                self.db.execute('UPDATE records SET revision=?,data=? WHERE tenant=? AND property=? AND id=?',
                                (rev+1,json.dumps(data),context.tenant_id,*key))
            if fault=='after_write': raise RuntimeError('synthetic interruption')
            receipt=dict(proposal_hash=proposal_hash,actor_id=context.actor_id,
                         tenant_id=context.tenant_id,run_id=context.run_id,approved_at=now,
                         changes=approved,status='committed')
            body=json.dumps(receipt,sort_keys=True)
            self.db.execute('INSERT INTO receipts VALUES(?,?,?)',(proposal_hash,request_hash,body))
            self.db.execute('INSERT INTO outbox VALUES(?,?)',(proposal_hash,body))
            if fault=='before_commit': raise RuntimeError('synthetic interruption')
            self.db.execute('COMMIT')
            return receipt
        except BaseException:
            if self.db.in_transaction: self.db.execute('ROLLBACK')
            raise
