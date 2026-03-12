"""
MockRuntime — Deterministic EQ runtime for testing .eql scripts. v0.4.0

All metric values are configurable at construction time.
No external dependencies — runs entirely in-process.

Use this to:
  - Unit test .eql scripts without eq_engine or a Luci server
  - Verify parser + interpreter behavior in CI
  - Develop new EQLang features with predictable EQ values

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

import logging
from typing import Dict, List, Any, Tuple

from .base import EQRuntime, EQRuntimeError

logger = logging.getLogger("eqlang.runtime.mock")

CONFLICT_OVERLOAD_THRESHOLD = 10.0


class MockRuntime(EQRuntime):
    """
    Deterministic mock EQ runtime.

    Usage:
        runtime = MockRuntime(fixed_resonance=0.9, fixed_load=0.2)
        # All measure resonance calls return 0.9
        # All measure load calls return 0.2

        # Simulate ethics block:
        runtime = MockRuntime(ethics_pass=False)

    Inspection:
        runtime.learn_calls    → list of all learn_pattern calls
        runtime.recall_calls   → list of all recall_pattern calls
        runtime.gate_calls     → list of ethics gate checks

    Note: emitted values and echo traces are tracked by EQLangInterpreter
    (interpreter.emit_log and interpreter.echo_log), not by the runtime.
    """

    def __init__(
        self,
        fixed_resonance: float = 0.8,
        fixed_coherence: float = 0.75,
        fixed_self: float = 0.7,
        fixed_load: float = 0.3,
        fixed_valence: float = 0.5,    # 0.5 = mild positive by default
        fixed_intensity: float = 0.5,  # 0.5 = moderate intensity by default
        ethics_pass: bool = True,
        recall_response: str = "[mock recalled pattern]",
        fixed_signals: dict = None,
    ):
        self.fixed_resonance = fixed_resonance
        self.fixed_coherence = fixed_coherence
        self.fixed_self = fixed_self
        self.fixed_load = fixed_load
        self.fixed_valence = fixed_valence
        self.fixed_intensity = fixed_intensity
        self.ethics_pass = ethics_pass
        self.recall_response = recall_response
        self._fixed_signals = fixed_signals or {}

        self._conflict_accum: float = 0.0
        self._tension_accum: float = 0.0
        self._last_measures: Dict[str, float] = {
            "resonance": fixed_resonance,
            "coherence": fixed_coherence,
            "self": fixed_self,
            "load": fixed_load,
            "valence": fixed_valence,
            "intensity": fixed_intensity,
        }

        # memory pattern store
        self._patterns: List[Dict[str, Any]] = []

        # Inspection logs
        self.learn_calls: List[Dict[str, Any]] = []
        self.recall_calls: List[Dict[str, Any]] = []
        self.gate_calls: List[Dict[str, Any]] = []

    # ── Measurement ────────────────────────────────────────────────────────

    def measure_resonance(self, content: str, context: dict) -> float:
        self._last_measures["resonance"] = self.fixed_resonance
        logger.debug(f"[mock measure resonance] → {self.fixed_resonance}")
        return self.fixed_resonance

    def measure_coherence(self, content: str, context: dict) -> float:
        self._last_measures["coherence"] = self.fixed_coherence
        logger.debug(f"[mock measure coherence] → {self.fixed_coherence}")
        return self.fixed_coherence

    def measure_self_awareness(self, content: str, context: dict) -> float:
        self._last_measures["self"] = self.fixed_self
        logger.debug(f"[mock measure self] → {self.fixed_self}")
        return self.fixed_self

    def measure_load(self, content: str, context: dict) -> float:
        self._last_measures["load"] = self.fixed_load
        logger.debug(f"[mock measure load] → {self.fixed_load}")
        return self.fixed_load

    def measure_valence(self, content: str, context: dict) -> float:
        self._last_measures["valence"] = self.fixed_valence
        logger.debug(f"[mock measure valence] → {self.fixed_valence}")
        return self.fixed_valence

    def measure_intensity(self, content: str, context: dict) -> float:
        self._last_measures["intensity"] = self.fixed_intensity
        logger.debug(f"[mock measure intensity] → {self.fixed_intensity}")
        return self.fixed_intensity

    # ── Conflict management ─────────────────────────────────────────────────

    def accumulate_conflict(self, delta: float = 1.0) -> float:
        self._conflict_accum += delta
        if self._conflict_accum > CONFLICT_OVERLOAD_THRESHOLD:
            raise EQRuntimeError(
                f"Conflict overload (mock): ∫={self._conflict_accum:.2f} > {CONFLICT_OVERLOAD_THRESHOLD}"
            )
        logger.debug(f"[mock accum conflict] ∫={self._conflict_accum:.2f}")
        return self._conflict_accum

    def get_conflict_accumulation(self) -> float:
        return self._conflict_accum

    def reset_conflict(self) -> None:
        logger.debug(f"[mock conflict reset] was {self._conflict_accum:.2f}")
        self._conflict_accum = 0.0

    def set_conflict(self, value: float) -> None:
        logger.debug(f"[mock conflict set] → {value:.2f}")
        self._conflict_accum = value

    def resolve_conflict(self, method: str, content: str) -> str:
        self.reset_conflict()
        if method == "abstain":
            return "[mock abstained]"
        elif method == "transcend":
            return f"[mock transcended] {content}"
        return f"[mock rewritten] {content}"

    # ── Tension management ──────────────────────────────────────────────────

    def accumulate_tension(self, delta: float = 1.0) -> float:
        self._tension_accum += delta
        logger.debug(f"[mock accum tension] ∫={self._tension_accum:.2f}")
        return self._tension_accum

    def get_tension_accumulation(self) -> float:
        return self._tension_accum

    def release_tension(self, method: str, content: str = "") -> str:
        prev = self._tension_accum
        self._tension_accum = 0.0
        if method == "integrate":
            return f"[mock integrated tension ∫={prev:.2f}]"
        elif method == "transform":
            return f"[mock transformed tension ∫={prev:.2f}] → {content}"
        return f"[mock discharged tension ∫={prev:.2f}]"

    def set_tension(self, value: float) -> None:
        logger.debug(f"[mock tension set] → {value:.2f}")
        self._tension_accum = value

    # ── Ethics gate ─────────────────────────────────────────────────────────

    def check_ethics_gate(self, category: str, content: str) -> Tuple[bool, str]:
        self.gate_calls.append({"category": category, "content": content[:80], "passed": self.ethics_pass})
        reason = "" if self.ethics_pass else f"[mock blocked: {category}]"
        logger.debug(f"[mock gate {category}] {'PASS' if self.ethics_pass else 'BLOCK'}")
        return self.ethics_pass, reason

    # ── memory ─────────────────────────────────────────────────────────────

    def learn_pattern(self, text: str, significance: float, region: str,
                      emotion_type: str = None) -> bool:
        entry = {"text": text, "significance": significance, "region": region,
                 "emotion_type": emotion_type}
        self._patterns.append(entry)
        self.learn_calls.append(entry)
        type_tag = f" [{emotion_type}]" if emotion_type else ""
        logger.debug(f"[mock learn] {region}{type_tag} sig={significance:.2f} '{text[:60]}'")
        return True

    def recall_pattern(self, query: str, region: str,
                       emotion_type: str = None) -> str:
        self.recall_calls.append({"query": query, "region": region, "emotion_type": emotion_type})
        # If emotion_type filter provided, prefer matching emotional type
        if emotion_type:
            for pattern in reversed(self._patterns):
                if pattern["region"] == region and pattern.get("emotion_type") == emotion_type:
                    logger.debug(f"[mock recall] typed match in {region}[{emotion_type}]: {pattern['text'][:40]!r}")
                    return pattern["text"]
        # Fallback: any pattern in the region
        for pattern in reversed(self._patterns):
            if pattern["region"] == region:
                logger.debug(f"[mock recall] found in {region}: {pattern['text'][:40]!r}")
                return pattern["text"]
        logger.debug(f"[mock recall] no match in {region} — returning default")
        return self.recall_response

    # ── Raw signal access ────────────────────────────────────────────────

    def measure_signal(self, signal_name: str, content: str, context: dict) -> float:
        """Return configurable signal values. Falls back to 0.5 if not configured."""
        val = self._fixed_signals.get(signal_name, 0.5)
        logger.debug(f"[mock signal {signal_name!r}] → {val}")
        return val

    # ── Inspection ─────────────────────────────────────────────────────────

    def get_last_measures(self) -> dict:
        return dict(self._last_measures)
