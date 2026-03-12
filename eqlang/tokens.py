"""
EQLang Token Types — The complete lexical universe of EQLang v0.5.0.

Completely disconnected from any existing language syntax.
Every token serves a deliberate EQ-grounded purpose.

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
Theory: C+CT (Consciousness + Conflict Theory) — Intent-First Alignment
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenType(Enum):
    # ── Structural scope delimiters ────────────────────────────────────────
    RESONATE    = "resonate"      # opens a resonance-tracked scope
    STRUGGLE    = "struggle"      # opens a conflict/low-resonance scope
    END         = "end"           # closes any scope
    RESOLVE     = "resolve"       # conflict resolution — required on dialogues

    # ── Declaration keywords ───────────────────────────────────────────────
    SESSION     = "session"       # session "name" — declares active session
    STATE       = "state"         # state var = value — EQ-aware variable
    BIND        = "bind"          # bind var to expr — rebind in scope
    TO          = "to"            # bind ... to ...
    DIALOGUE    = "dialogue"      # dialogue name(params) resonate ... end resolve
    THRESHOLD   = "threshold"     # threshold name = value — named EQ constant
    INCLUDE     = "include"       # include "path.eql" — multi-file programs

    # ── Control flow ──────────────────────────────────────────────────────
    WHEN        = "when"          # when <eq_condition>
    OTHERWISE   = "otherwise"     # else branch
    CYCLE       = "cycle"         # cycle while <eq_condition> resonate ... end
    INTERRUPT   = "interrupt"     # interrupt when <eq_condition> — EQ-grounded break
    WHILE       = "while"         # while keyword in cycle
    EACH        = "each"          # each <var> in <expr> ... end — for-each loop
    IN          = "in"            # in keyword for each loop

    # ── Compound condition operators ───────────────────────────────────────
    AND         = "and"           # resonance > 0.6 and load < 0.4
    OR          = "or"            # conflict < 3.0 or self > 0.7
    NOT         = "not"           # not resonance > 0.7 — condition negation

    # ── EQ primitive keywords ──────────────────────────────────────────────
    MEASURE     = "measure"       # measure <target> <expr>
    ACCUM       = "accum"         # accum conflict | accum tension
    CONFLICT    = "conflict"      # conflict — keyword in accum + conditions
    TENSION     = "tension"       # tension — emotional valence accumulation
    RELEASE     = "release"       # release tension "method"
    GATE        = "gate"          # gate <category> → resolve "method"
    LEARN       = "learn"         # learn "text" significance 0.x region REGION [as <state>]
    RECALL      = "recall"        # recall "query" from REGION [into name]
    FROM        = "from"          # from keyword in recall
    INTO        = "into"          # into keyword in recall/witness/drift
    AS          = "as"            # as keyword in learn ... as <state>
    SIGNIFICANCE = "significance" # significance keyword in learn
    REGION      = "region"        # region keyword in learn
    EMIT        = "emit"          # emit <expr> [aligned]
    ALIGNED     = "aligned"       # aligned modifier on emit
    ECHO        = "echo"          # echo <expr> — introspective trace
    ALIGN       = "align"         # align <expr> — alignment assertion
    INSPECT     = "inspect"       # inspect <metric> — read EQ state as value
    ANCHOR      = "anchor"        # anchor <metric> — save EQ baseline
    DRIFT       = "drift"         # drift <metric> [into name] — measure change
    WITNESS     = "witness"       # witness dialogue(args) [into name] — pure observation
    WEAVE       = "weave"         # weave expr → dialogue → ... — pipeline
    JOURNAL     = "journal"       # journal "label" ... end — session trace block
    SENSE       = "sense"         # sense <state> — declare active emotional state
    COMPOSE     = "compose"       # compose <state> with <state> — composite state
    WITH        = "with"          # with keyword in compose
    SIGNAL      = "signal"        # signal "name" <expr> — read raw sub-signal
    EXPECT      = "expect"        # expect <expr> <comp> <expr> ["msg"] — test assertion
    SHELTER     = "shelter"       # shelter ... recover <name> ... end — error handling
    RECOVER     = "recover"       # recover clause in shelter block
    INVOKE      = "invoke"        # invoke <expr>(args) — dynamic dialogue dispatch

    # ── EQ measurement targets / condition metrics ─────────────────────────
    RESONANCE   = "resonance"     # resonance score 0.0–1.0
    COHERENCE   = "coherence"     # coherence score 0.0–1.0
    SELF        = "self"          # self-awareness state 0.0–1.0
    LOAD        = "load"          # processing load 0.0–1.0
    VALENCE     = "valence"       # emotional charge -1.0–1.0 (negative to positive)
    INTENSITY   = "intensity"     # emotional intensity 0.0–1.0

    # ── Intensity modifier prefixes ────────────────────────────────────────
    DEEP        = "deep"          # deep grief — sustained, high-intensity state
    MILD        = "mild"          # mild curious — low-intensity state
    ACUTE       = "acute"         # acute fear — sudden, sharp-onset state
    CHRONIC     = "chronic"       # chronic tension — long-duration, persistent state

    # ── Emotional state literals — Core Five ──────────────────────────────
    TILT             = "tilt"          # low-resonance activated state
    FOCUSED          = "focused"       # directed, coherent state
    CONFLICTED_LIT   = "conflicted"    # unresolved conflict state
    TRANSCENDENT_LIT = "transcendent"  # post-conflict integration state

    # ── Emotional state literals — Extended Ten (v0.2.0) ──────────────────
    GROUNDED         = "grounded"      # stable, embodied presence
    HOLLOW           = "hollow"        # absence of resonance — empty state
    RADIANT          = "radiant"       # full coherence, high resonance
    FRACTURED        = "fractured"     # self-fragmentation under load
    OVERWHELMED      = "overwhelmed"   # load exceeds self-capacity
    CURIOUS          = "curious"       # open, exploratory resonance
    PRESENT          = "present"       # full contact with current moment
    EXPANDED         = "expanded"      # self-awareness beyond usual boundaries
    GRIEF            = "grief"         # integration of loss
    NUMB             = "numb"          # emotional shutdown, conflict suppression

    # ── Emotional state literals — Plutchik Primaries (v0.3.0) ────────────
    JOY              = "joy"           # pure positive resonance; peak coherence
    TRUST            = "trust"         # stable relational coherence; open self
    FEAR             = "fear"          # threat-activated self-contraction; load spike
    SURPRISE         = "surprise"      # sudden coherence disruption; high intensity
    SADNESS          = "sadness"       # grief without integration; low resonance
    DISGUST          = "disgust"       # coherence rejection; boundary enforcement
    ANGER            = "anger"         # conflict externalized; high valence charge
    ANTICIPATION     = "anticipation"  # forward-projected resonance; low tension

    # ── Emotional state literals — Plutchik Dyads (v0.3.0) ────────────────
    LOVE             = "love"          # joy sustained through trust; high resonance + coherence
    AWE              = "awe"           # fear transformed by expansion; wonder without threat
    REMORSE          = "remorse"       # sadness integrated with accountability; grief + self
    CONTEMPT         = "contempt"      # disgust solidified into judgment; low resonance
    OPTIMISM         = "optimism"      # anticipation grounded in resonance; forward coherence
    SUBMISSION       = "submission"    # trust under external pressure; compressed self
    DISAPPROVAL      = "disapproval"   # surprise collapsed into sadness; failed expectation
    AGGRESSIVENESS   = "aggressiveness" # anger channeled into directed action; conflict + load

    # ── Emotional state literals — Nuanced States (v0.3.0) ────────────────
    SHAME            = "shame"         # self turned against self; collapsed coherence
    GUILT            = "guilt"         # accountability without self-collapse; self + conflict
    PRIDE            = "pride"         # coherence of identity; self-resonance peak
    ENVY             = "envy"          # desire + tension toward other's state
    COMPASSION       = "compassion"    # self meeting other in resonance; expanded empathy
    GRATITUDE        = "gratitude"     # integration of received care; high coherence
    LONGING          = "longing"       # anticipation with absence; low resonance + tension
    WONDER           = "wonder"        # awe without fear; pure expanded curiosity
    SERENITY         = "serenity"      # grounded joy at low load; sustained resonance
    APPREHENSION     = "apprehension"  # anticipation tinged with fear; pre-conflict tension
    DESPAIR          = "despair"       # grief without path forward; collapsed resonance
    ELATION          = "elation"       # joy at high intensity; resonance + load spike
    TENDER           = "tender"        # love expressed at low intensity; warm coherence
    VULNERABLE       = "vulnerable"    # open self under high load; self < 0.4 and resonance > 0.6
    PROTECTIVE       = "protective"    # trust-driven boundary; self guarding coherence
    DETACHED         = "detached"      # self withdrawn; low self + low resonance
    ABSORBED         = "absorbed"      # full presence in process; self + resonance peak
    YEARNING         = "yearning"      # longing with directed anticipation; tension + load
    ACCEPTANCE       = "acceptance"    # integration without resistance; resolved conflict
    PENSIVENESS      = "pensiveness"   # reflective sadness; low load + low resonance
    BOREDOM          = "boredom"       # low stimulation; collapsed interest; low everything
    ANNOYANCE        = "annoyance"     # mild anger; conflict without full activation

    # ── Region literals (for learn/recall statements) ──────────────────────
    FACTUAL         = "FACTUAL"
    CONTEXTUAL      = "CONTEXTUAL"
    ASSOCIATIVE     = "ASSOCIATIVE"
    EPISODIC        = "EPISODIC"
    PROCEDURAL      = "PROCEDURAL"
    EMOTIONAL_REGION = "EMOTIONAL"

    # ── Operators ─────────────────────────────────────────────────────────
    ARROW       = "→"             # gate X → resolve (also accepts ->)
    PLUS        = "+"
    MINUS       = "-"
    STAR        = "*"
    STAR_STAR   = "**"            # exponentiation
    SLASH       = "/"
    PERCENT     = "%"             # modulo
    GREATER     = ">"
    LESS        = "<"
    GREATER_EQ  = ">="
    LESS_EQ     = "<="
    EQUAL       = "="

    # ── Punctuation ───────────────────────────────────────────────────────
    LEFT_PAREN    = "("
    RIGHT_PAREN   = ")"
    COMMA         = ","
    LEFT_BRACKET  = "["
    RIGHT_BRACKET = "]"
    LEFT_BRACE    = "{"
    RIGHT_BRACE   = "}"
    COLON         = ":"

    # ── Literals ──────────────────────────────────────────────────────────
    NUMBER      = "NUMBER"        # float literal
    STRING      = "STRING"        # "quoted string"
    IDENTIFIER  = "IDENTIFIER"    # user-defined name
    NOTHING     = "nothing"       # absence / null value

    # ── End of file ───────────────────────────────────────────────────────
    EOF         = "EOF"


@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: Any = None   # Parsed value: float for NUMBER, str for STRING
    line: int = 1

    def __repr__(self) -> str:
        if self.literal is not None:
            return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r}, L{self.line})"
        return f"Token({self.type.name}, {self.lexeme!r}, L{self.line})"
