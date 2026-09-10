"""Fault injection for the independent R41 audit gates."""
import copy
from pathlib import Path
import sqlite3
import tempfile
import unittest

from kairo_r41.audit import database_check, minimum_states, product_check, replay
from kairo_r41.experiment import holdouts
from kairo_r24.backend import SQLiteTools


class AuditTests(unittest.TestCase):
    def test_product_rejects_deep_output_error(self):
        target = {'initial': 'a', 'alphabet': ['x'], 'transitions':
                  {'a': {'x': ['b', 'off']}, 'b': {'x': ['c', 'off']}, 'c': {'x': ['c', 'on']}}}
        good = {'alphabet': ['x'], 'transitions': [[[1, 'off']], [[2, 'off']], [[2, 'on']]]}
        self.assertTrue(product_check(target, good)['equivalent'])
        self.assertEqual(minimum_states(target), 3)
        wrong = copy.deepcopy(good)
        wrong['transitions'][2][0][1] = 'off'
        self.assertEqual(product_check(target, wrong)['counterexample'], ['x', 'x', 'x'])

    def test_minimizer_merges_behaviorally_equal_states(self):
        target = {'initial': 'a', 'alphabet': ['x'], 'transitions':
                  {'a': {'x': ['b', 'ok']}, 'b': {'x': ['b', 'ok']}}}
        self.assertEqual(minimum_states(target), 1)

    def test_database_check_rejects_wrong_persisted_values(self):
        case = holdouts()[0]
        with tempfile.TemporaryDirectory() as temp:
            backend = SQLiteTools(Path(temp) / 'actual', case)
            with self.assertRaises(AssertionError):
                database_check(backend.path, case)
            baseline_case = {**case, 'final_expected': case['baseline']}
            self.assertEqual(database_check(backend.path, baseline_case)['rows'], 1)
            connection = sqlite3.connect(backend.path)
            connection.execute(f'UPDATE {case["table"]} SET {case["value_col"]}=0')
            connection.commit()
            connection.close()
            with self.assertRaises(AssertionError):
                database_check(backend.path, baseline_case)

    def test_replay_rejects_fabricated_observation(self):
        case = holdouts()[0]
        op = next(a for a, name in case['bindings'].items() if name == 'open')
        events = [{'request': {'op': 'query', 'word': [op], 'purpose': 'acquisition'},
                   'response': {'outputs': ['fabricated']}}]
        with self.assertRaisesRegex(AssertionError, 'event replay mismatch'):
            replay(events, case, {}, Path('unused'))


if __name__ == '__main__':
    unittest.main()
