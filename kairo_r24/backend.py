"""Finite inventory adapter using actual on-disk SQLite transactions."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3


class SQLiteTools:
    def __init__(self,root,case):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=False)
        self.path=self.root/'inventory.sqlite';self.case=case;self.table=case.get('table','inventory');self.key_col=case.get('key_col','sku');self.value_col=case.get('value_col','quantity');self.bindings=case['bindings'];self.connection=None;self.savepoint=False;self.savepoint_rows=None
        self.meters=Counter({k:0 for k in ('actions','resets','baseline_copies','connects','closes','selects','updates','begins','commits','rollbacks','implicit_rollbacks')})
        conn=sqlite3.connect(self.path,isolation_level=None)
        conn.execute(f'CREATE TABLE {self.table}({self.key_col} TEXT PRIMARY KEY, {self.value_col} INTEGER NOT NULL CHECK({self.value_col} >= 0))')
        conn.execute('BEGIN')
        conn.executemany(f'INSERT INTO {self.table} VALUES (?,?)',case['baseline']);conn.execute('COMMIT');conn.close()
        self.baseline_bytes=self.path.read_bytes()

    def close(self):
        if self.connection is not None:
            self.meters['implicit_rollbacks']+=int(self.connection.in_transaction)
            self.connection.close();self.connection=None;self.savepoint=False;self.savepoint_rows=None;self.meters['closes']+=1

    def reset(self):
        self.close()
        assert not any((self.root/('inventory.sqlite'+suffix)).exists() for suffix in ('-journal','-wal','-shm'))
        self.path.write_bytes(self.baseline_bytes);self.meters['resets']+=1;self.meters['baseline_copies']+=1

    def rows(self,connection):
        return [list(row) for row in connection.execute(f'SELECT {self.key_col},{self.value_col} FROM {self.table} ORDER BY {self.key_col}').fetchall()]

    def persisted(self,meter=False):
        connection=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True,isolation_level=None)
        try:
            if meter:self.meters['connects']+=1;self.meters['selects']+=1
            return self.rows(connection)
        finally:
            connection.close()
            if meter:self.meters['closes']+=1

    def snapshot(self):
        return {'open':self.connection is not None,'in_transaction':bool(self.connection and self.connection.in_transaction),'savepoint':self.savepoint,'savepoint_rows':self.savepoint_rows,
            'local_rows':self.rows(self.connection) if self.connection else None,'persisted_rows':self.persisted()}

    def disk_hash(self):return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def step(self,action):
        operation=self.bindings[action];self.meters['actions']+=1
        if operation=='open':
            if self.connection:return 'already_open'
            self.connection=sqlite3.connect(self.path,isolation_level=None);self.meters['connects']+=1
            return 'session_opened'
        if operation=='close':
            if not self.connection:return 'already_closed'
            self.close();return 'session_closed'
        if not self.connection:return 'session_required'
        if operation=='begin':
            if self.connection.in_transaction:return 'already_in_transaction'
            self.connection.execute('BEGIN');self.meters['begins']+=1;return 'transaction_started'
        if operation in ('commit','rollback'):
            if not self.connection.in_transaction:return 'transaction_required'
            self.connection.execute(operation.upper());self.meters[operation+'s']+=1
            self.savepoint=False
            return 'commit_done' if operation=='commit' else 'rollback_done'
        if operation=='savepoint':
            if not self.connection.in_transaction:return 'transaction_required'
            if self.savepoint:return 'already_savepoint'
            self.connection.execute('SAVEPOINT kairo_sp');self.savepoint=True;self.savepoint_rows=self.rows(self.connection);return 'savepoint_created'
        if operation=='rollback_to_savepoint':
            if not self.connection.in_transaction or not self.savepoint:return 'savepoint_required'
            self.connection.execute('ROLLBACK TO kairo_sp');return 'rollback_to_savepoint'
        if operation=='stage':
            if not self.connection.in_transaction:return 'transaction_required'
            for (sku,baseline),(expected_sku,desired) in zip(self.case['baseline'],self.case['expected']):
                assert sku==expected_sku
                self.connection.execute(f'UPDATE {self.table} SET {self.value_col}=?-? WHERE {self.key_col}=?',(baseline,baseline-desired,sku))
                self.meters['updates']+=1
            return 'update_staged'
        if operation=='inspect':
            local=self.rows(self.connection);self.meters['selects']+=1;persisted=self.persisted(meter=True)
            if local==persisted==self.case['baseline']:return 'baseline_verified'
            if local==self.case['expected'] and persisted==self.case['baseline']:return 'pending_verified'
            if local==persisted==self.case['expected']:return 'durable_verified'
            return 'unexpected_rows'
        raise ValueError(operation)


def inspect_artifact(path):
    conn=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,isolation_level=None)
    try:
        table=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        columns=[row[1] for row in conn.execute(f'PRAGMA table_info({table})').fetchall()]
        rows=[list(row) for row in conn.execute(f'SELECT {columns[0]},{columns[1]} FROM {table} ORDER BY {columns[0]}').fetchall()]
        return {'table':table,'rows':rows,'integrity_check':conn.execute('PRAGMA integrity_check').fetchall()[0][0]}
    finally:conn.close()


def explore(backend,cap):
    # Projected state identity excludes file header counters and engine timing.
    backend.reset();snapshots=[backend.snapshot()];words=[[]];keys={json.dumps(snapshots[0],sort_keys=True):'s0'};transitions={};done=0
    try:
        while done<len(words):
            word=words[done];state='s'+str(done);transitions[state]={}
            for action in sorted(backend.bindings):
                backend.reset()
                for prefix in word:backend.step(prefix)
                output=backend.step(action);snapshot=backend.snapshot();key=json.dumps(snapshot,sort_keys=True)
                if key not in keys:
                    if len(words)>=cap:return {'complete':False,'states':len(words),'model':None,'reason':'state_cap'}
                    keys[key]='s'+str(len(words));words.append(word+[action]);snapshots.append(snapshot)
                transitions[state][action]=[keys[key],output]
            done+=1
        return {'complete':True,'states':len(words),'access_words':words,'snapshots':snapshots,
            'model':{'initial':'s0','alphabet':sorted(backend.bindings),'transitions':transitions},
            'scope':'Finite fixed inventory adapter projected through session, transaction and rows; not all SQLite behavior.'}
    finally:backend.close()
