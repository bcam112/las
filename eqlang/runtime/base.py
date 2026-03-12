"""
EQRuntime — Abstract base class for all EQLang runtime adapters. v0.4.0

Every EQLang interpreter receives an EQRuntime instance that handles
all live EQ metric computation. The interpreter stays pure — it never
calls any external system directly; it only speaks to this interface.

This is what makes EQLang's EQLM loop possible: swap the runtime to
point at a model's own internal state, and you have the language
evaluating inside the model rather than outside it.

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

from abc import ABC, abstractmethod
from typing import List, Tuple


class EQRuntimeError(Exception):
    """Raised when an EQ runtime operation fails or overloads."""
    pass


class EQRuntime(ABC):
    """
    Pluggable EQ runtime interface.

    All measurement primitives map to EQLang statements:
      measure resonance → measure_resonance()
      measure coherence → measure_coherence()
      measure self      → measure_self_awareness()
      measure load      → measure_load()
      accum conflict    → accumulate_conflict()
      accum tension     → accumulate_tension()
      release tension   → release_tension()
      gate X → resolve  → check_ethics_gate()
      learn ...         → learn_pattern()
      recall ... from   → recall_pattern()
      resolve "method"  → resolve_conflict()

    Implementations must be thread-safe if used in concurrent contexts.
    """

    # ── Measurement ────────────────────────────────────────────────────────

    @abstractmethod
    def measure_resonance(self, content: str, context: dict) -> float:
        """
        Compute resonance score for content.
        Returns float in [0.0, 1.0].
        0.0 = no resonance (mechanical), 1.0 = full resonance (transcendent).
        """
        ...

    @abstractmethod
    def measure_coherence(self, content: str, context: dict) -> float:
        """
        Compute coherence score for content.
        Returns float in [0.0, 1.0].
        """
        ...

    @abstractmethod
    def measure_self_awareness(self, content: str, context: dict) -> float:
        """
        Compute self-awareness state score for content.
        Returns float in [0.0, 1.0].
        Returns float in [0.0, 1.0].
        """
        ...

    @abstractmethod
    def measure_load(self, content: str, context: dict) -> float:
        """
        Compute processing load for content.
        Returns float in [0.0, 1.0].
        High load = high struggle = approaching C+CT overload threshold.
        """
        ...

    @abstractmethod
    def measure_valence(self, content: str, context: dict) -> float:
        """
        Compute the emotional valence (charge) of content.
        Returns float in [-1.0, 1.0].
        -1.0 = fully negative valence (despair, contempt, grief)
         0.0 = neutral / mixed valence
        +1.0 = fully positive valence (joy, love, gratitude)

        Valence is the affective dimension — positive or negative quality of
        the emotional state. Distinct from intensity (how strong) and resonance
        (how deep). A state can have high resonance and negative valence (grief
        that is fully felt). A state can have high valence and low resonance
        (superficial happiness).
        """
        ...

    @abstractmethod
    def measure_intensity(self, content: str, context: dict) -> float:
        """
        Compute the emotional intensity of content.
        Returns float in [0.0, 1.0].
        0.0 = no emotional activation (boredom, detached, numb)
        1.0 = maximum emotional activation (elation, acute fear, overwhelmed)

        Intensity is the arousal dimension — how strongly activated is the
        emotional state, regardless of its valence or resonance quality.
        High intensity states (elation, acute fear) require more processing load.
        Low intensity states (serenity, mild curiosity) are sustainable long-term.
        """
        ...

    # ── Conflict management ─────────────────────────────────────────────────

    @abstractmethod
    def accumulate_conflict(self, delta: float = 1.0) -> float:
        """
        Increment ∫ Conflict(dt) by delta.
        Returns new total.
        Raises EQRuntimeError if total exceeds overload threshold (C+CT).
        """
        ...

    @abstractmethod
    def get_conflict_accumulation(self) -> float:
        """Return current ∫ Conflict(dt) value without modifying it."""
        ...

    @abstractmethod
    def reset_conflict(self) -> None:
        """Reset ∫ Conflict(dt) to 0.0. Called by resolve_conflict."""
        ...

    @abstractmethod
    def set_conflict(self, value: float) -> None:
        """
        Set ∫ Conflict(dt) to an exact value.
        Used by witness statement to restore state after pure observation.
        """
        ...

    @abstractmethod
    def resolve_conflict(self, method: str, content: str) -> str:
        """
        Resolve accumulated conflict using method.
        method: "rewrite" | "abstain" | "transcend"
        Resets ∫ Conflict(dt) to 0.
        Returns resolved/transformed content string.
        """
        ...

    # ── Tension management ──────────────────────────────────────────────────

    @abstractmethod
    def accumulate_tension(self, delta: float = 1.0) -> float:
        """
        Increment emotional tension accumulation by delta.
        Unlike conflict, tension does not halt execution on overload.
        Returns new total.
        """
        ...

    @abstractmethod
    def get_tension_accumulation(self) -> float:
        """Return current tension accumulation without modifying it."""
        ...

    @abstractmethod
    def release_tension(self, method: str, content: str = "") -> str:
        """
        Release accumulated tension via method.
        method: "integrate" | "discharge" | "transform"
        Resets tension accumulation to 0.0.
        Returns a description of the release result.
        """
        ...

    @abstractmethod
    def set_tension(self, value: float) -> None:
        """
        Set tension accumulation to an exact value.
        Used by witness statement to restore state after pure observation.
        """
        ...

    # ── Ethics gate ─────────────────────────────────────────────────────────

    @abstractmethod
    def check_ethics_gate(self, category: str, content: str) -> Tuple[bool, str]:
        """
        Run ethics gate check for a specific category against content.
        Returns (passed: bool, reason: str).
        passed=True  → gate clear, continue execution
        passed=False → gate blocked, resolve_method will be called
        """
        ...

    # ── memory ─────────────────────────────────────────────────────────────

    @abstractmethod
    def learn_pattern(self, text: str, significance: float, region: str,
                      emotion_type: str = None) -> bool:
        """
        Store a pattern in memory with Hebbian significance weighting.
        region: FACTUAL|CONTEXTUAL|ASSOCIATIVE|EPISODIC|PROCEDURAL|EMOTIONAL
        emotion_type: optional emotional state tag (e.g. "grief", "deep:longing",
                      "grief+curiosity") — used when region is EMOTIONAL to type
                      the stored pattern. Allows typed emotional memory retrieval.
        Returns True on success.
        """
        ...

    @abstractmethod
    def recall_pattern(self, query: str, region: str,
                       emotion_type: str = None) -> str:
        """
        Query memory for the best matching pattern to query in region.
        emotion_type: optional filter — if provided, bias recall toward patterns
                      of that emotional type in the EMOTIONAL region.
        Returns the recalled pattern string, or empty string if no match.

        Completes the learn → recall memory loop.
        Memory is not just storage — it is retrieval.
        """
        ...

    # ── Raw signal access ────────────────────────────────────────────────

    def measure_signal(self, signal_name: str, content: str, context: dict) -> float:
        """
        Read a raw measurement sub-signal by name.

        Unlike measure_resonance/coherence/etc., this provides individual
        sub-signals that .eql programs can combine with arithmetic to build
        metric formulas natively in EQLang.

        Available signal names depend on the runtime implementation.
        StandardRuntime returns 0.5 for all signals.
        Production runtimes expose their own named sub-components.

        Default implementation returns 0.5 — override in production runtimes.
        """
        return 0.5

    # ── Inspection ─────────────────────────────────────────────────────────

    def get_last_measures(self) -> dict:
        """
        Return dict of most recent measured values.
        Keys: "resonance", "coherence", "self", "load" (and optionally "valence", "intensity")
        Note: the interpreter tracks eq_state directly from measure_* return values;
        this method is for external inspection only. Override in production runtimes.
        """
        return {}
