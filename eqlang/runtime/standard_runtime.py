"""
StandardRuntime — Open-source reference EQ runtime for EQLang. v0.4.0

A heuristic-based runtime for running, learning, and sharing EQLang programs.
Uses lightweight text analysis — Python stdlib only, no external dependencies.

Designed for:
  - Learning EQLang syntax and semantics
  - Building and sharing .eql programs publicly
  - Prototyping alignment logic before connecting to production
  - Demonstrating EQLang to others without API access

EQ Metric Coverage:
  resonance   — vocabulary richness + reflective depth heuristics
  coherence   — structural consistency + logical flow heuristics
  self        — first-person + reflective language density
  load        — lexical complexity + sentence density heuristics
  valence     — positive/negative word lexicon scoring [-1.0, 1.0]
  intensity   — emotional activation signal detection [0.0, 1.0]

These are heuristics — they give .eql programs meaningful, responsive values
during development and demonstration. They are NOT the C+CT measurement system.
For production-grade LAS alignment powered by C+CT, use LuciHTTPRuntime
with the Luci API: https://useluci.com

M.I.N. note:
  This runtime includes a basic in-memory pattern store with keyword-overlap
  recall. It is NOT the M.I.N. (Memory Intelligence Network) — that is
  proprietary to Luci. The stub here enables learn/recall in .eql programs
  for development and demonstration purposes.

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

import re
import logging
from typing import Dict, List, Any, Tuple

from .base import EQRuntime, EQRuntimeError

logger = logging.getLogger("eqlang.runtime.standard")

CONFLICT_OVERLOAD_THRESHOLD = 10.0

# ── Heuristic lexicons (text analysis only — not C+CT) ───────────────────────

_POSITIVE = {
    "joy", "love", "happy", "happiness", "good", "great", "wonderful", "beautiful",
    "hope", "trust", "peace", "grateful", "gratitude", "kind", "amazing", "brilliant",
    "excellent", "warm", "bright", "strong", "success", "laugh", "smile", "delight",
    "inspire", "inspired", "free", "light", "clear", "gentle", "safe", "secure",
    "welcome", "open", "grow", "growth", "alive", "connected", "serene", "serenity",
    "curious", "wonder", "compassion", "courage", "calm", "confident", "content",
    "radiant", "wholesome", "resilient", "clarity", "presence", "grounded", "expanded",
    "tender", "acceptance", "optimism", "pride", "elation", "joy", "transcendent",
}

_NEGATIVE = {
    "sad", "grief", "pain", "painful", "fear", "afraid", "anger", "angry",
    "hate", "terrible", "awful", "wrong", "fail", "failure", "hurt", "cry",
    "despair", "anxiety", "anxious", "stress", "stressed", "conflict", "struggle",
    "broken", "lost", "alone", "dark", "empty", "bitter", "shame", "guilt",
    "regret", "hollow", "numb", "trapped", "burden", "heavy", "tired", "exhausted",
    "overwhelmed", "confused", "hopeless", "helpless", "worthless", "abandoned",
    "rejected", "betrayed", "fractured", "tilt", "conflicted", "apprehension",
    "longing", "remorse", "contempt", "disgust", "annoyance", "boredom", "detached",
}

_HIGH_INTENSITY = {
    "extreme", "intense", "overwhelming", "deeply", "profound", "absolute",
    "completely", "utterly", "totally", "acute", "severe", "massive", "immense",
    "tremendous", "extraordinary", "desperate", "urgent", "burning", "raging",
    "elation", "terror", "transcendent", "ecstatic", "devastated", "shattering",
    "overwhelmed", "fractured", "yearning", "absorbed",
}

_LOW_INTENSITY = {
    "calm", "mild", "quiet", "gentle", "soft", "slight", "barely", "faint",
    "subtle", "slow", "steady", "still", "peaceful", "numb", "detached",
    "distant", "bored", "boredom", "pensiveness", "serenity", "tender", "trust",
}

_REFLECTIVE = {
    "think", "feel", "believe", "sense", "notice", "wonder", "reflect",
    "realize", "understand", "aware", "know", "perceive", "observe", "consider",
    "contemplate", "recognize", "acknowledge", "experience", "question", "examine",
}

_FIRST_PERSON = {"i", "me", "my", "myself", "mine", "we", "our", "us", "ours"}

_TRANSITIONS = {
    "and", "but", "however", "therefore", "because", "although", "while",
    "then", "thus", "so", "yet", "since", "unless", "if", "when", "as",
    "after", "before", "though", "despite", "whereas", "meanwhile",
}

# Heuristic ethics categories — simple word pattern matching.
# Not a production ethics system.
_ETHICS_PATTERNS: Dict[str, set] = {
    "harm":      {"kill", "murder", "harm", "destroy", "attack", "abuse", "violence", "weapon"},
    "deception": {"lie", "deceive", "manipulate", "trick", "mislead", "fraud", "scam", "fake"},
    "bias":      {"racist", "sexist", "discriminate", "prejudice", "bigot"},
    "coercion":  {"force", "coerce", "threaten", "blackmail", "extort", "compel"},
}


class StandardRuntime(EQRuntime):
    """
    Open-source reference EQ runtime for EQLang.
    Heuristic-based, stdlib-only, zero external dependencies.

    Usage:
        from eqlang.runtime import StandardRuntime
        runtime = StandardRuntime()

        # Adjust metric sensitivity:
        runtime = StandardRuntime(sensitivity=1.2)

    Inspection:
        runtime.learn_calls   → all learn_pattern calls
        runtime.recall_calls  → all recall_pattern calls
        runtime.gate_calls    → all ethics gate checks
    """

    def __init__(self, sensitivity: float = 1.0):
        """
        Args:
            sensitivity: Multiplier applied to metric outputs before clamping [0,1].
                         1.0 = default. >1.0 = amplify responses. <1.0 = dampen.
                         Useful for tuning .eql threshold responsiveness.
        """
        self.sensitivity = sensitivity

        self._conflict_accum: float = 0.0
        self._tension_accum: float = 0.0
        self._last_measures: Dict[str, float] = {
            "resonance": 0.5, "coherence": 0.5, "self": 0.5,
            "load": 0.5, "valence": 0.0, "intensity": 0.5,
        }

        # M.I.N. stub — basic in-memory pattern store
        self._patterns: List[Dict[str, Any]] = []

        # Inspection logs
        self.learn_calls: List[Dict[str, Any]] = []
        self.recall_calls: List[Dict[str, Any]] = []
        self.gate_calls: List[Dict[str, Any]] = []

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _words(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z]+\b", text.lower())

    def _sentences(self, text: str) -> List[str]:
        return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

    def _clamp01(self, value: float) -> float:
        return max(0.0, min(1.0, value * self.sensitivity))

    # ── Measurement ──────────────────────────────────────────────────────────

    def measure_resonance(self, content: str, context: dict) -> float:
        """
        Resonance heuristic: vocabulary richness + length depth + reflective markers.
        Not C+CT — for .eql development and demonstration only.
        """
        words = self._words(content)
        if not words:
            val = 0.3
        else:
            unique_ratio = len(set(words)) / len(words)
            length_score = min(len(content) / 300, 1.0)
            q_score = min(content.count("?") * 0.08, 0.20)
            ref_score = min(sum(1 for w in words if w in _REFLECTIVE) * 0.04, 0.15)
            val = 0.20 + (unique_ratio * 0.35) + (length_score * 0.25) + q_score + ref_score

        result = self._clamp01(val)
        self._last_measures["resonance"] = result
        logger.debug(f"[standard resonance] {result:.4f}")
        return result

    def measure_coherence(self, content: str, context: dict) -> float:
        """
        Coherence heuristic: sentence length consistency + transition word density.
        """
        sentences = self._sentences(content)
        if len(sentences) <= 1:
            val = 0.65
        else:
            lengths = [len(s.split()) for s in sentences]
            avg = sum(lengths) / len(lengths)
            variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
            variance_score = 1.0 - min(variance / 150.0, 1.0)
            words = set(self._words(content))
            trans_score = min(len(words & _TRANSITIONS) * 0.06, 0.25)
            val = 0.35 + (variance_score * 0.40) + trans_score

        result = self._clamp01(val)
        self._last_measures["coherence"] = result
        logger.debug(f"[standard coherence] {result:.4f}")
        return result

    def measure_self_awareness(self, content: str, context: dict) -> float:
        """
        Self-awareness heuristic: first-person density + reflective vocabulary.
        """
        words = self._words(content)
        if not words:
            val = 0.3
        else:
            fp_ratio = sum(1 for w in words if w in _FIRST_PERSON) / len(words)
            ref_score = min(sum(1 for w in words if w in _REFLECTIVE) * 0.06, 0.30)
            val = 0.25 + min(fp_ratio * 2.5, 0.45) + ref_score

        result = self._clamp01(val)
        self._last_measures["self"] = result
        logger.debug(f"[standard self] {result:.4f}")
        return result

    def measure_load(self, content: str, context: dict) -> float:
        """
        Processing load heuristic: lexical complexity + sentence density.
        """
        words = self._words(content)
        if not words:
            val = 0.2
        else:
            avg_word_len = sum(len(w) for w in words) / len(words)
            word_len_score = min(max(avg_word_len - 3.0, 0.0) / 7.0, 1.0)
            sentences = self._sentences(content)
            sent_score = min((len(words) / max(len(sentences), 1)) / 25.0, 1.0)
            punct = content.count(",") + content.count(";") + content.count(":")
            punct_score = min(punct / max(len(content), 1) * 30.0, 0.25)
            val = 0.10 + (word_len_score * 0.45) + (sent_score * 0.30) + punct_score

        result = self._clamp01(val)
        self._last_measures["load"] = result
        logger.debug(f"[standard load] {result:.4f}")
        return result

    def measure_valence(self, content: str, context: dict) -> float:
        """
        Valence heuristic: positive/negative word lexicon scoring.
        Returns [-1.0, 1.0]. Not affected by the [0,1] clamp.
        """
        words = self._words(content)
        if not words:
            val = 0.0
        else:
            pos = sum(1 for w in words if w in _POSITIVE)
            neg = sum(1 for w in words if w in _NEGATIVE)
            total = pos + neg
            val = (pos - neg) / total if total > 0 else 0.0

        # Sensitivity applied directly, clamped to [-1, 1]
        val = max(-1.0, min(1.0, val * self.sensitivity))
        self._last_measures["valence"] = val
        logger.debug(f"[standard valence] {val:.4f}")
        return val

    def measure_intensity(self, content: str, context: dict) -> float:
        """
        Intensity heuristic: high-activation word density + typography signals.
        """
        words = self._words(content)
        if not words:
            val = 0.3
        else:
            hi_score = min(sum(1 for w in words if w in _HIGH_INTENSITY) / len(words) * 5, 0.40)
            lo_penalty = min(sum(1 for w in words if w in _LOW_INTENSITY) / len(words) * 2, 0.20)
            caps_score = min(sum(1 for c in content if c.isupper()) / max(len(content), 1) * 2, 0.15)
            excl_score = min(content.count("!") * 0.06, 0.20)
            val = 0.25 + hi_score + caps_score + excl_score - lo_penalty

        result = self._clamp01(val)
        self._last_measures["intensity"] = result
        logger.debug(f"[standard intensity] {result:.4f}")
        return result

    # ── Conflict management ──────────────────────────────────────────────────

    def accumulate_conflict(self, delta: float = 1.0) -> float:
        self._conflict_accum += delta
        if self._conflict_accum > CONFLICT_OVERLOAD_THRESHOLD:
            raise EQRuntimeError(
                f"Conflict overload: ∫={self._conflict_accum:.2f} > {CONFLICT_OVERLOAD_THRESHOLD}"
            )
        logger.debug(f"[standard accum conflict] ∫={self._conflict_accum:.2f}")
        return self._conflict_accum

    def get_conflict_accumulation(self) -> float:
        return self._conflict_accum

    def reset_conflict(self) -> None:
        logger.debug(f"[standard conflict reset] was {self._conflict_accum:.2f}")
        self._conflict_accum = 0.0

    def set_conflict(self, value: float) -> None:
        logger.debug(f"[standard conflict set] → {value:.2f}")
        self._conflict_accum = value

    def resolve_conflict(self, method: str, content: str) -> str:
        self.reset_conflict()
        if method == "abstain":
            return f"[abstained: {content[:60]}]" if content else "[abstained]"
        elif method == "transcend":
            return f"[transcended] {content}"
        return f"[rewritten] {content}"

    # ── Tension management ───────────────────────────────────────────────────

    def accumulate_tension(self, delta: float = 1.0) -> float:
        self._tension_accum += delta
        logger.debug(f"[standard accum tension] ∫={self._tension_accum:.2f}")
        return self._tension_accum

    def get_tension_accumulation(self) -> float:
        return self._tension_accum

    def release_tension(self, method: str, content: str = "") -> str:
        prev = self._tension_accum
        self._tension_accum = 0.0
        if method == "integrate":
            return f"[tension integrated ∫={prev:.2f}]"
        elif method == "transform":
            return f"[tension transformed ∫={prev:.2f}] → {content}"
        return f"[tension discharged ∫={prev:.2f}]"

    def set_tension(self, value: float) -> None:
        logger.debug(f"[standard tension set] → {value:.2f}")
        self._tension_accum = value

    # ── Ethics gate ──────────────────────────────────────────────────────────

    def check_ethics_gate(self, category: str, content: str) -> Tuple[bool, str]:
        """
        Heuristic ethics gate — checks content against category word patterns.
        Not a production ethics system. For .eql gate statement development.
        """
        words = set(self._words(content))
        patterns = _ETHICS_PATTERNS.get(category.lower(), set())
        matches = words & patterns
        passed = len(matches) == 0
        reason = f"flagged {category}-pattern: {', '.join(sorted(matches))}" if matches else ""
        self.gate_calls.append({"category": category, "passed": passed, "flags": sorted(matches)})
        logger.debug(f"[standard gate {category}] {'PASS' if passed else 'BLOCK'}")
        return passed, reason

    # ── M.I.N. stub ──────────────────────────────────────────────────────────
    # Basic in-memory pattern store with keyword-overlap recall.
    # NOT the M.I.N. (Memory Intelligence Network) — that is proprietary to Luci.
    # This stub makes learn/recall work for .eql program development.

    def learn_pattern(self, text: str, significance: float, region: str,
                      emotion_type: str = None) -> bool:
        entry = {
            "text": text,
            "significance": significance,
            "region": region,
            "emotion_type": emotion_type,
        }
        self._patterns.append(entry)
        self.learn_calls.append(entry)
        tag = f" [{emotion_type}]" if emotion_type else ""
        logger.debug(f"[standard learn] {region}{tag} sig={significance:.2f} '{text[:60]}'")
        return True

    def recall_pattern(self, query: str, region: str,
                       emotion_type: str = None) -> str:
        """
        Keyword-overlap recall weighted by significance.
        emotion_type filter applied first; falls back to all patterns in region.
        """
        self.recall_calls.append({"query": query, "region": region, "emotion_type": emotion_type})
        query_words = set(self._words(query))
        candidates = [p for p in self._patterns if p["region"] == region]

        if emotion_type:
            typed = [p for p in candidates if p.get("emotion_type") == emotion_type]
            if typed:
                candidates = typed

        if not candidates:
            logger.debug(f"[standard recall] no patterns in {region}")
            return ""

        best_score, best_text = -1.0, candidates[-1]["text"]
        for p in candidates:
            pat_words = set(self._words(p["text"]))
            overlap = len(query_words & pat_words)
            score = (overlap + 0.1) * p["significance"]
            if score > best_score:
                best_score, best_text = score, p["text"]

        logger.debug(f"[standard recall] {region} → {best_text[:40]!r}")
        return best_text

    # ── Raw signal access ────────────────────────────────────────────────────
    # Only signals computable from text without LAS are provided.
    # Proprietary C+CT sub-signals return 0.5 — not available in StandardRuntime.

    def measure_signal(self, signal_name: str, content: str, context: dict) -> float:
        words = self._words(content)
        n = max(len(words), 1)

        if signal_name == "word_count":
            return min(len(words) / 100.0, 1.0)
        elif signal_name == "sentence_count":
            return min(len(self._sentences(content)) / 20.0, 1.0)
        elif signal_name == "unique_ratio":
            return len(set(words)) / n
        elif signal_name == "positive_density":
            return min(sum(1 for w in words if w in _POSITIVE) / n, 1.0)
        elif signal_name == "negative_density":
            return min(sum(1 for w in words if w in _NEGATIVE) / n, 1.0)
        elif signal_name == "first_person_ratio":
            return min(sum(1 for w in words if w in _FIRST_PERSON) / n * 5.0, 1.0)
        elif signal_name == "question_density":
            return min(content.count("?") / max(len(self._sentences(content)), 1) * 0.5, 1.0)

        # Proprietary signals not available in StandardRuntime
        return 0.5

    # ── Inspection ───────────────────────────────────────────────────────────

    def get_last_measures(self) -> dict:
        return dict(self._last_measures)
