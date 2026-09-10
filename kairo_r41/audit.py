"""Independent product traversal, event replay and SQLite artifact checks."""
from __future__ import annotations

from collections import deque
import json
from pathlib import Path
import re
import sqlite3
import tempfile

from kairo_r24.backend import SQLiteTools
from .experiment import ROOT, LANES, check_freeze, read, sha, write


def product_check(target, hypothesis):
    """Traverse every reachable pair; no call to the benchmark comparator."""
    assert target['alphabet'] == hypothesis['alphabet']
    pending = deque([(target['initial'], 0, [])])
    visited = {(target['initial'], 0)}
    edges = 0
    while pending:
        actual, inferred, path = pending.popleft()
        for column, action in enumerate(target['alphabet']):
            actual_next, actual_output = target['transitions'][actual][action]
            inferred_next, inferred_output = hypothesis['transitions'][inferred][column]
            edges += 1
            if actual_output != inferred_output:
                return {'equivalent': False, 'counterexample': path + [action],
                        'reachable_pairs': len(visited), 'transitions_checked': edges}
            pair = actual_next, inferred_next
            if pair not in visited:
                visited.add(pair)
                pending.append((actual_next, inferred_next, path + [action]))
    return {'equivalent': True, 'counterexample': None,
            'reachable_pairs': len(visited), 'transitions_checked': edges}


def minimum_states(target):
    """Refine output-equivalence classes until stable (evaluator only)."""
    states = sorted(target['transitions'])
    classes = {state: 0 for state in states}
    while True:
        identifiers, new_classes = {}, {}
        for state in states:
            signature = tuple((output, classes[next_state]) for action in target['alphabet']
                              for next_state, output in [target['transitions'][state][action]])
            new_classes[state] = identifiers.setdefault(signature, len(identifiers))
        if all((classes[a] == classes[b]) == (new_classes[a] == new_classes[b])
               for a in states for b in states):
            return len(identifiers)
        classes = new_classes


def database_check(path, case):
    """Do not call the benchmark's inspect_artifact helper."""
    assert all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', case[key])
               for key in ('table', 'key_col', 'value_col'))
    connection = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    try:
        schema = connection.execute(f'PRAGMA table_info("{case["table"]}")').fetchall()
        assert [column[1] for column in schema] == [case['key_col'], case['value_col']]
        actual = [list(row) for row in connection.execute(
            f'SELECT "{case["key_col"]}", "{case["value_col"]}" '
            f'FROM "{case["table"]}" ORDER BY "{case["key_col"]}"').fetchall()]
        integrity = connection.execute('PRAGMA integrity_check').fetchall()
        assert actual == case['final_expected'], 'independent persisted row mismatch'
        assert integrity == [('ok',)], integrity
        return {'rows': len(actual), 'integrity': 'ok', 'schema_verified': True,
                'sha256': sha(path)}
    finally:
        connection.close()


def replay(events, case, expected_summary, artifact_path):
    with tempfile.TemporaryDirectory(prefix='kairo_r41_audit_') as temp:
        probe = SQLiteTools(Path(temp) / 'probe', case)
        actual = SQLiteTools(Path(temp) / 'actual', case)
        queries = symbols = actions = 0
        aq = cq = dq = challenge_symbols = 0
        checkpoint = None
        try:
            for index, event in enumerate(events):
                request, expected = event['request'], event['response']
                op = request['op']
                if op == 'query':
                    word = request['word']
                    probe.reset()
                    response = {'outputs': [probe.step(action) for action in word]}
                    queries += 1
                    symbols += len(word)
                    purpose = request['purpose']
                    aq += purpose == 'acquisition'
                    cq += purpose == 'challenge'
                    dq += purpose == 'validation'
                    challenge_symbols += len(word) if purpose == 'challenge' else 0
                elif op == 'restart':
                    actual.reset()
                    response = {}
                elif op == 'step':
                    response = {'output': actual.step(request['action'])}
                    actions += 1
                elif op == 'task_checkpoint':
                    checkpoint = actual.snapshot()
                    response = {}
                elif op in ('begin_acquisition', 'end_acquisition'):
                    response = {}
                else:
                    raise AssertionError(('unexpected event', op))
                assert response == expected, ('event replay mismatch', index, request, response, expected)
            assert checkpoint is None or actual.snapshot() == checkpoint
            actual.close()
            assert sha(actual.path) == sha(artifact_path), 'replay artifact differs'
            recomputed = {'queries': queries, 'input_symbols': symbols,
                          'execution_actions': actions, 'acquisition_queries': aq,
                          'challenge_queries': cq, 'validation_queries': dq,
                          'challenge_symbols': challenge_symbols}
            assert all(expected_summary[k] == v for k, v in recomputed.items()), recomputed
            return {'events_replayed': len(events), **recomputed,
                    'artifact_reproduced': True, 'checkpoint_unchanged': True}
        finally:
            actual.close()
            probe.close()


def compare_trees(left, right):
    left_files = {p.relative_to(left).as_posix(): sha(p) for p in left.rglob('*') if p.is_file()}
    right_files = {p.relative_to(right).as_posix(): sha(p) for p in right.rglob('*') if p.is_file()}
    assert left_files == right_files, {'different_files': sorted(
        k for k in left_files.keys() | right_files.keys() if left_files.get(k) != right_files.get(k))}
    return len(left_files)


def original_diagnostics():
    policies = LANES['r40_depth1']
    cases = read(ROOT / 'datasets/r40/private_cases.json')
    rows = []
    for case in cases:
        base = ROOT / 'results/r40'
        plan_result = read(base / 'plan_challenges' / case['id'] / 'RESULT.json')
        random_result = read(base / 'random_challenges' / case['id'] / 'RESULT.json')
        evaluation = read(base / 'cold' / case['id'] / 'EVALUATION.json')
        learned = read(base / 'cold' / case['id'] / 'RETAINED.json')
        witness = evaluation['final_equivalence']['counterexample']
        rows.append({'case': case['id'], 'complete_evaluation': evaluation['complete'],
                     'target_states': evaluation['states'], 'minimal_target_states': minimum_states(evaluation['model']),
                     'learner_states': len(learned['model']['transitions']), 'acquisition_queries': learned['queries'],
                     'stop_status': learned['status'], 'witness': witness,
                     'decoded_witness': [case['bindings'][a] for a in witness],
                     'challenge_words_identical': [r['word'] for r in plan_result['challenges']] ==
                                                   [r['word'] for r in random_result['challenges']],
                     'challenge_lengths_identical': [len(r['word']) for r in plan_result['challenges']] ==
                                                     [len(r['word']) for r in random_result['challenges']],
                     'plan_result_sha256': sha(base / 'plan_challenges' / case['id'] / 'RESULT.json'),
                     'random_result_sha256': sha(base / 'random_challenges' / case['id'] / 'RESULT.json')})
    return {'summaries': {p: read(ROOT / 'results/r40' / p / 'SUMMARY.json') for p in policies},
            'cases': rows,
            'goal_achieved_scope': 'benchmark.py writes False unconditionally for the full research objective'}


def audit():
    manifest = check_freeze()
    frozen = read(ROOT / 'datasets/r41/PRESERVATION.json')
    changed = [p for p, digest in frozen.items() if not (ROOT / p).is_file() or sha(ROOT / p) != digest]
    assert not changed, {'changed_prior_files': changed}
    report = {'original_r40': original_diagnostics(), 'lanes': {}, 'tasks': [],
              'source_freeze_verified': True, 'prior_files_preserved': len(frozen),
              'manifest_sha256': sha(ROOT / 'datasets/r41/MANIFEST.json')}
    for lane, policies in LANES.items():
        cases = read(ROOT / 'datasets/r41' / lane / 'private_cases.json')
        report['lanes'][lane] = {}
        for policy in policies:
            base = ROOT / 'results/r41/primary' / lane / policy
            repro = ROOT / 'results/r41/repro' / lane / policy
            identical = compare_trees(base, repro)
            summary = read(base / 'SUMMARY.json')
            if lane == 'r40_depth1':
                assert summary == read(ROOT / 'results/r40' / policy / 'SUMMARY.json')
                for case in cases:
                    for file in ('RESULT.json', 'RETAINED.json', 'EVENTS.json', 'EVALUATION.json',
                                 'DATABASE_IO.json', 'ARTIFACTS/inventory.sqlite'):
                        assert sha(base / case['id'] / file) == sha(ROOT / 'results/r40' / policy / case['id'] / file), file
            summed = {k: 0 for k in ('queries', 'input_symbols', 'execution_actions',
                                     'challenge_queries', 'challenge_symbols')}
            exact = success = 0
            for case in cases:
                folder = base / case['id']
                task_summary = read(folder / 'SUMMARY.json')
                evaluation = read(folder / 'EVALUATION.json')
                retained = read(folder / 'RETAINED.json')
                boundary = read(folder / 'BOUNDARY.json')
                boot = read(folder / 'BOOTSTRAP.json')
                assert boundary['private_files_copied'] == [] and boundary['child_exitcode'] == 0
                assert not any(token in p for p in boundary['copied_files']
                               for token in ('backend', 'reference', 'datasets', 'r41'))
                assert set(boot) == {'policy', 'protocol', 'alphabet', 'ordinal', 'goal', 'retained'}
                assert evaluation['complete'], 'no exact verdict allowed for incomplete projection'
                proof = product_check(evaluation['model'], retained['model']) if retained and retained.get('model') else None
                assert proof == evaluation['final_equivalence'], 'independent comparator disagrees'
                artifact = folder / 'ARTIFACTS/inventory.sqlite'
                db = database_check(artifact, case)
                replay_result = replay(read(folder / 'EVENTS.json'), case, task_summary, artifact)
                exact += bool(proof and proof['equivalent'])
                success += task_summary['status'] == 'success'
                for key in summed:
                    summed[key] += task_summary[key]
                row = {'lane': lane, 'policy': policy, 'case': case['id'],
                       'proof': proof, 'database': db, 'replay': replay_result,
                       'target_states': evaluation['states'],
                       'minimal_target_states': minimum_states(evaluation['model']),
                       'model_states': len(retained['model']['transitions']) if retained else None}
                report['tasks'].append(row)
                print(json.dumps({'audited': f'{lane}/{policy}/{case["id"]}',
                                  'equivalent': bool(proof and proof['equivalent']),
                                  'events': replay_result['events_replayed']}), flush=True)
            assert exact == summary['exact_models'] and success == summary['successes']
            assert all(summary[k] == v for k, v in summed.items())
            report['lanes'][lane][policy] = {**summary, 'identical_reproduction_files': identical}
    check_freeze()
    report['all_experiment_tasks_audited'] = len(report['tasks'])
    report['verdict'] = 'passed_integrity_and_reproduction_checks'
    report['goal_achieved'] = False
    destination = ROOT / 'verification/R41_AUDIT.json'
    if destination.exists():
        raise FileExistsError(destination)
    write(destination, report)
    print(json.dumps({'report': str(destination), 'tasks': len(report['tasks'])}), flush=True)


if __name__ == '__main__':
    audit()
