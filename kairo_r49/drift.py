"""Minimal drifting adapter used only to verify Kairo's refusal boundary."""


class DriftingAdapter:
    bindings = {"op_0": "observe"}

    def __init__(self): self.epoch = 0
    def reset(self): self.epoch += 1
    def step(self, action):
        if action not in self.bindings: raise ValueError(action)
        return "state_a" if self.epoch % 2 else "state_b"
