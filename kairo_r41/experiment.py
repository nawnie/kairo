"""Use the existing learner unchanged; preserve and hash all experiment inputs."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import random
import sqlite3
import subprocess

from kairo_r24.benchmark import run


ROOT = Path(__file__).resolve().parents[1]
POLICIES = ('cold', 'retain', 'random_challenges', 'plan_challenges')
LANES = {'r40_depth1': POLICIES, 'r40_depth2': POLICIES,
         'holdout_depth2': ('cold', 'retain')}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes(paths):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths)) if p.is_file()}


def holdouts():
    rng = random.Random(4102026)
    operations = ['open', 'begin', 'stage', 'commit', 'rollback', 'close', 'inspect']
    cases = []
    for index, count in enumerate((1, 17, 64, 3, 32, 127)):
        if index % 2 == 0:
            rng.shuffle(operations)
            bindings = {f'op_{i}': operation for i, operation in enumerate(operations)}
        baseline = [[f'h{index + 1}_{row:04d}', rng.randint(500, 50000)] for row in range(count)]
        expected = [[key, value - rng.randint(1, 100)] for key, value in baseline]
        cases.append({'id': f'H{index + 1}', 'table': f'register_{index + 1}',
                      'key_col': f'key_{index + 1}', 'value_col': f'value_{index + 1}',
                      'baseline': baseline, 'expected': expected, 'final_expected': expected,
                      'bindings': dict(bindings),
                      'goal': {'require': ['pending_verified', 'session_closed',
                                           'session_opened', 'durable_verified'], 'forbid': []}})
    return cases


def prepare():
    folder = ROOT / 'datasets/r41'
    if folder.exists():
        raise FileExistsError('R41 already frozen; never overwrite a previous experiment')
    sources = [ROOT / 'R41_PROTOCOL.md']
    for package in ROOT.glob('kairo_r*'):
        sources.extend(package.glob('*.py'))
    source_hashes = hashes(sources)
    preserved = [ROOT / 'R5_SOURCE.zip', ROOT / 'R24_PROTOCOL.md']
    for parent in ('results', 'datasets', 'verification',
                   'Kairo_Discovery_Lab_R5_Endogenous_Explanations'):
        preserved.extend(p for p in (ROOT / parent).rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts)
    preservation = hashes(preserved)
    original_protocol = read(ROOT / 'datasets/r40/PROTOCOL.json')
    original_cases = read(ROOT / 'datasets/r40/private_cases.json')
    for lane in LANES:
        data = folder / lane
        protocol = copy.deepcopy(original_protocol)
        if lane != 'r40_depth1':
            protocol['learning']['middle_depth'] = 2
        cases = holdouts() if lane == 'holdout_depth2' else original_cases
        write(data / 'PROTOCOL.json', protocol)
        write(data / 'private_cases.json', cases)
        write(data / 'FREEZE.json', {
            'protocol_sha256': sha(ROOT / 'R24_PROTOCOL.md'),
            'files': {name: sha(data / name) for name in ('PROTOCOL.json', 'private_cases.json')},
            'sources': source_hashes,
            'r41_protocol_sha256': sha(ROOT / 'R41_PROTOCOL.md')})
    write(folder / 'PRESERVATION.json', preservation)
    write(folder / 'MANIFEST.json', {
        'sources': source_hashes, 'inputs': hashes(p for p in folder.rglob('*') if p.is_file()),
        'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'runtime': {'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version},
        'lanes': {k: list(v) for k, v in LANES.items()}, 'holdout_seed': 4102026})
    print(json.dumps({'frozen': str(folder), 'sources': len(source_hashes),
                      'preserved_files': len(preservation), 'lanes': list(LANES)}))


def check_freeze():
    manifest = read(ROOT / 'datasets/r41/MANIFEST.json')
    for group in ('sources', 'inputs'):
        changed = [path for path, digest in manifest[group].items() if sha(ROOT / path) != digest]
        if changed:
            raise AssertionError({'changed_frozen_' + group: changed})
    return manifest


def execute(lane, policy, replica):
    assert policy in LANES[lane] and replica in ('primary', 'repro')
    check_freeze()
    output = ROOT / 'results/r41' / replica / lane / policy
    if output.exists():
        raise FileExistsError(output)
    run(ROOT, output, policy, f'datasets/r41/{lane}')
    check_freeze()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('prepare', 'run'))
    parser.add_argument('--lane', choices=tuple(LANES))
    parser.add_argument('--policy', choices=POLICIES)
    parser.add_argument('--replica', choices=('primary', 'repro'), default='primary')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    else:
        execute(args.lane, args.policy, args.replica)
