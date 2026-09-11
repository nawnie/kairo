"""Small observed-trace transfer probe for the Kairo-N hypothesis.

The target mismatch is held outside the learner. N sees only donor
prefix/output observations and ranks candidates; an external checker counts
how quickly the first mismatch is found.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass

from kairo_r44.backprop import TraceHead


ALPHABET = ("a", "b", "c", "d")
TARGET = ("c", "b", "a")


def donor_observations():
    words = [
        (), ("a",), ("b",), ("c",), ("d",),
        ("a", "a"), ("a", "b"), ("b", "a"), ("b", "b"),
        ("c", "a"), ("d", "a"),
    ]
    return [(list(word), "zero" if not word or word[-1] in ("a", "b") else "one") for word in words]


def candidates():
    return [tuple(word) for length in (2, 3) for word in itertools.product(ALPHABET, repeat=length)]


def first_mismatch(order):
    for index, word in enumerate(order, start=1):
        if word == TARGET:
            return index
    raise AssertionError("target must be in candidate pool")


@dataclass
class N0Result:
    neural_rank: int
    random_ranks: list[int]
    candidate_count: int
    hidden_target: tuple[str, ...]

    @property
    def random_mean(self):
        return sum(self.random_ranks) / len(self.random_ranks)


def run(seed=5101, random_repeats=25):
    head = TraceHead(ALPHABET, history=3, hidden_size=8, seed=seed)
    head.fit(donor_observations(), epochs=80, learning_rate=0.08)
    pool = candidates()
    neural_order = sorted(pool, key=lambda word: (-head.challenge_score(list(word)), word))
    random_ranks = []
    for offset in range(random_repeats):
        order = list(pool); random.Random(seed + offset).shuffle(order)
        random_ranks.append(first_mismatch(order))
    return N0Result(first_mismatch(neural_order), random_ranks, len(pool), TARGET)
