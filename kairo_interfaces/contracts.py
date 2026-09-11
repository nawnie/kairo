"""Evidence-safe interfaces for future S/N/R integration.

R0/R1 and N1 can suggest context or proposals. Only the symbolic path and
fresh verification can create the immutable canonical result.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DynamicContext:
    source: str
    features: tuple[float, ...]
    weight: float
    model_hash: str
    observed_event_ids: tuple[str, ...]

    def __post_init__(self):
        if self.source not in {"r0", "r1"}: raise ValueError("unknown dynamic-context source")
        if not 0.0 <= self.weight <= 1.0: raise ValueError("context weight outside [0,1]")
        if not self.model_hash or not self.observed_event_ids: raise ValueError("context provenance is required")


@dataclass(frozen=True)
class NeuralProposal:
    candidate: tuple[str, ...]
    confidence: float
    source: str = "n1"

    def __post_init__(self):
        if self.source != "n1": raise ValueError("neural proposal source must be n1")
        if not 0.0 <= self.confidence <= 1.0: raise ValueError("proposal confidence outside [0,1]")


@dataclass(frozen=True)
class CanonicalResult:
    answer: Any
    evidence_status: str
    verification_class: str
    locked: bool = True

    def __post_init__(self):
        if not self.locked: raise ValueError("canonical result must be locked")


@dataclass(frozen=True)
class ContextApplication:
    context: DynamicContext
    proposal: NeuralProposal | None
    canonical_before: CanonicalResult
    canonical_after: CanonicalResult
    authority_changed: bool = False

    def __post_init__(self):
        if self.canonical_before != self.canonical_after or self.authority_changed:
            raise ValueError("context application cannot change canonical authority")


def apply_context(context, canonical, proposal=None):
    """Attach bounded context/proposal metadata without changing the result."""
    return ContextApplication(context, proposal, canonical, canonical)
