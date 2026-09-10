import argparse
import json
from pathlib import Path
import shutil
import tempfile
from kairo_r11.benchmark import write
from kairo_r11.reference import equivalence
from kairo_r12.benchmark import sha
from kairo_r23.host import Host
from kairo_r23.process import child
from .backend import SQLiteTools,explore,inspect_artifact


def frozen(root,data):
    load=lambda name:json.loads((data/name).read_text());freeze=load('FREEZE.json')
    assert sha(root/'R24_PROTOCOL.md')==freeze['protocol_sha256']
    assert all(sha(data/name)==value for name,value in freeze['files'].items())
    assert all(sha(root/name)==value for name,value in freeze['sources'].items())
    return data,load


def finalize(host,dest,case):
    before=host.actual.snapshot();disk=host.actual.disk_hash()
    if host.checkpoint is not None:assert before==host.checkpoint
    io={'probe':dict(host.probe.meters),'execution':dict(host.actual.meters),'checkpoint':before,'checkpoint_disk_sha256':disk}
    host.actual.close();host.probe.close()
    io['execution_after_close']=dict(host.actual.meters);io['probe_after_close']=dict(host.probe.meters)
    artifacts=dest/'ARTIFACTS';artifacts.mkdir();shutil.copyfile(host.actual.path,artifacts/'inventory.sqlite')
    observed=inspect_artifact(artifacts/'inventory.sqlite');matches=observed['rows']==case['final_expected'] and observed['integrity_check']=='ok'
    io.update(artifact_sha256=sha(artifacts/'inventory.sqlite'),independent_artifact_read=observed,
        persisted_expected_match=matches,artifact_unchanged_after_challenges=before==host.checkpoint if host.checkpoint else True)
    write(dest/'DATABASE_IO.json',io);return io


def run(root,out,policy,data_dir='datasets/r24'):
    data,load=frozen(root,root/data_dir);protocol=load('PROTOCOL.json');assert policy in protocol['policies'];artifact=None;rows=[]
    for ordinal,case in enumerate(load('private_cases.json')):
        dest=out/case['id'];boot={'policy':'cold_model' if policy=='cold' else policy,'protocol':protocol,
            'alphabet':sorted(case['bindings']),'ordinal':ordinal,'goal':case['goal'],'retained':None if policy=='cold' else artifact}
        with tempfile.TemporaryDirectory(prefix='kairo_r24_sql_') as directory:
            make=lambda name:SQLiteTools(Path(directory)/name,case)
            host=Host(make('probe'),make('actual'),protocol)
            # Checkpoint hashing is recorded immediately, outside child input.
            old_handle=host.handle;checkpoint_hash=[]
            def handle(request):
                response=old_handle(request)
                if request['op']=='task_checkpoint':checkpoint_hash.append(host.actual.disk_hash())
                return response
            host.handle=handle
            entry='kairo_r22.file_client' if policy=='cold' else 'kairo_r23.client'
            result=child(root,dest,boot,host,entry)
            assert result['queries']==host.queries and result['input_symbols']==host.symbols and not host.acquiring
            if checkpoint_hash:assert checkpoint_hash==[host.actual.disk_hash()]
            io=finalize(host,dest,case)
            evaluation=explore(make('evaluator'),protocol['state_cap']);target=evaluation['model']
            def compare(value):return equivalence(target,value['model']) if target and value and value.get('model') else None
            before=result['retained'] if policy=='cold' else result['base']['retained']
            evaluation.update(incoming_equivalence=compare(boot['retained']),before_challenges_equivalence=compare(before),final_equivalence=compare(result['retained']))
            write(dest/'EVALUATION.json',evaluation)
        write(dest/'RETAINED.json',result['retained']);artifact=json.loads((dest/'RETAINED.json').read_text())
        row={'case':case['id'],'policy':policy,'status':result['status'],'artifact_verified':io['persisted_expected_match'],
            'queries':host.queries,'input_symbols':host.symbols,'acquisition_queries':host.aq,'challenge_queries':host.cq,
            'challenge_symbols':host.csym,'validation_queries':host.dq,'execution_actions':host.steps,
            'mismatches':len(result.get('mismatching_words',[])),'post_success_repair':result.get('repair') is not None,
            'final_equivalent':evaluation['final_equivalence']['equivalent'] if evaluation['final_equivalence'] else None}
        write(dest/'SUMMARY.json',row);rows.append(row);print(json.dumps(row),flush=True)
    summary={'policy':policy,'tasks':rows,'successes':sum(r['status']=='success' and r['artifact_verified'] for r in rows),
        'exact_models':sum(r['final_equivalent'] is True for r in rows),'goal_achieved':False,
        **{key:sum(r[key] for r in rows) for key in ('queries','input_symbols','execution_actions','challenge_queries','challenge_symbols')}}
    write(out/'SUMMARY.json',summary)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--policy',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--data-dir',default='datasets/r24')
    a=p.parse_args();run(Path.cwd(),a.output,a.policy,a.data_dir)
