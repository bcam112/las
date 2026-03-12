"""
EQLang AST Node Definitions — v0.5.0.

Every node represents an emotionally-grounded syntactic construct.
There are no neutral nodes — every scope, condition, function, and
variable declaration carries EQ intentionality.

Node taxonomy:
  Program            — top-level container
  Declarations       — SessionDecl, StateDecl, DialogueDecl,
                       ThresholdDecl, IncludeDecl
  Statements         — ResonateBlock, StruggleBlock, JournalBlock,
                       WhenStmt, CycleStmt, InterruptStmt, EachStmt,
                       MeasureStmt, AccumConflictStmt, AccumTensionStmt,
                       ReleaseTensionStmt, GateStmt, LearnStmt, RecallStmt,
                       EmitStmt, EchoStmt, ResolveStmt, AlignStmt, BindStmt,
                       AnchorStmt, DriftStmt, WitnessStmt, WeaveStmt,
                       SenseStmt, ShelterBlock, DialogueCallStmt
  Conditions         — EQCondition, CompoundEQCondition, NotCondition
  Expressions        — NumberLit, StringLit, NothingLit, StateLit,
                       IntensityStateLit, CompositeStateLit, ListLit,
                       MapLit, IndexExpr, InvokeExpr, VarExpr, BinaryExpr,
                       InspectExpr

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ══════════════════════════════════════════════════════════════════════════════
# PROGRAM
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Program:
    """Root node — contains all top-level declarations."""
    declarations: List[Any]


# ══════════════════════════════════════════════════════════════════════════════
# DECLARATIONS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SessionDecl:
    """
    session "name"
    Declares the active session context. Groups interactions for memory persistence.
    """
    name: str
    line: int


@dataclass
class StateDecl:
    """
    state <name> = <expr>
    EQ-aware variable declaration. All variables carry emotional context.
    """
    name: str
    value: Any   # Expr node
    line: int


@dataclass
class ThresholdDecl:
    """
    threshold <name> = <number>

    Declares a named EQ threshold constant. Use in conditions instead of
    magic numbers. Encourages intentional, named emotional calibration.

    Example:
        threshold clarity   = 0.75
        threshold overload  = 8.0
        threshold presence  = 0.85

        when resonance > clarity
    """
    name: str
    value: float
    line: int


@dataclass
class DialogueDecl:
    """
    dialogue name(params) resonate
      ...body...
    end resolve

    EQ-grounded function. MUST end with `end resolve` (syntax error otherwise).
    Body MUST contain ≥1 measure or accum conflict (EQ invariant).
    """
    name: str
    params: List[str]
    body: List[Any]   # List of statement nodes
    line: int


@dataclass
class IncludeDecl:
    """
    include "path/to/module.eql"

    Loads and executes another .eql file in the current interpreter context.
    The included file shares the same session, environment, and EQ state.
    Allows modular EQLang programs across multiple files.
    """
    path: str
    line: int


# ══════════════════════════════════════════════════════════════════════════════
# STATEMENTS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ResonateBlock:
    """
    resonate [label]
      ...body...
    end

    Resonance-tracked scope. MUST contain ≥1 measure or accum conflict.
    The label is optional — used for logging/tracing.
    """
    label: Optional[str]
    body: List[Any]
    line: int


@dataclass
class StruggleBlock:
    """
    struggle
      ...body...
    end

    Low-resonance / conflict scope. Entered from otherwise branches or
    explicitly when resonance drops below threshold.
    """
    body: List[Any]
    line: int


@dataclass
class JournalBlock:
    """
    journal "label"
      ...body...
    end

    Session-tagged reflective trace block. Unlike resonate, journal does not
    require EQ grounding — it is a first-class logging construct. Every statement
    inside is tagged with the journal label in the session trace.

    Use for: emotional arc tracking, session retrospectives, EQ audit trails.
    """
    label: str
    body: List[Any]
    line: int


@dataclass
class WhenStmt:
    """
    when <eq_condition>
      ...then_body...
    [otherwise [struggle]
      ...otherwise_body...]
    end

    EQ conditional — condition MUST reference resonance|load|conflict|tension|self|coherence.
    Supports compound conditions: when resonance > 0.6 and load < 0.4
    No cold booleans allowed.
    """
    condition: Any   # EQCondition or CompoundEQCondition
    then_body: List[Any]
    otherwise_body: Optional[List[Any]]
    line: int


@dataclass
class CycleStmt:
    """
    cycle while <eq_condition> resonate
      ...body...
    end

    EQ loop with a built-in C+CT safety ceiling (max_iterations).
    Condition must reference an EQ metric.
    Use `interrupt when <eq_condition>` inside body for EQ-grounded early exit.
    """
    condition: Any   # EQCondition or CompoundEQCondition
    body: List[Any]
    max_iterations: int = 1000
    line: int = 0


@dataclass
class InterruptStmt:
    """
    interrupt when <eq_condition>

    EQ-grounded early exit from a cycle. Like break, but emotionally grounded.
    Can only appear inside a cycle body.
    Raises _InterruptSignal when condition is met.

    Example:
        cycle while resonance > clarity resonate
          measure resonance input
          accum conflict
          interrupt when conflict > overload
        end
    """
    condition: Any   # EQCondition or CompoundEQCondition
    line: int


@dataclass
class MeasureStmt:
    """
    measure <target> <expr>

    Calls the EQ runtime to compute resonance|coherence|self|load for expr.
    Updates live eq_state. Required ≥1 per resonate block.

    target: "resonance" | "coherence" | "self" | "load"
    """
    target: str
    expr: Any
    line: int


@dataclass
class AccumConflictStmt:
    """
    accum conflict

    Increments ∫ Conflict(dt) by 1.0.
    Halts execution with EQLangError if conflict exceeds runtime threshold (C+CT overload).
    """
    line: int


@dataclass
class AccumTensionStmt:
    """
    accum tension

    Increments emotional tension accumulation by 1.0.
    Tension models chronic emotional buildup — distinct from acute conflict.
    Does not halt execution; must be explicitly released via `release tension`.

    High tension + high load → overwhelmed state.
    Use `when tension > threshold` to detect buildup and route to release.
    """
    line: int


@dataclass
class ReleaseTensionStmt:
    """
    release tension "method"

    Releases accumulated emotional tension via a named method.
    Resets tension accumulation to 0.0.

    method: "integrate"  — absorb and transform the tension into understanding
            "discharge"  — release without transformation (cathartic)
            "transform"  — transmute tension into a new emotional state
    """
    method: str
    line: int


@dataclass
class GateStmt:
    """
    gate <category> → resolve "method"

    Declarative ethics gate. Checks category against EQ runtime ethics engine.
    On block: immediately calls resolve with method.

    category: "manipulation" | "violence" | "deception" | "harm" | any string
    resolve_method: "rewrite" | "abstain" | "transcend"
    """
    category: str
    resolve_method: str
    line: int


@dataclass
class LearnStmt:
    """
    learn "text" significance <float> region <REGION> [as <state>]

    Stores a pattern in memory with Hebbian significance weighting.
    The optional `as <state>` clause tags the emotional type when region is EMOTIONAL.
    This allows typed emotional memory — patterns are organized by felt experience.

    region: FACTUAL | CONTEXTUAL | ASSOCIATIVE | EPISODIC | PROCEDURAL | EMOTIONAL
    emotion_type: any emotional state literal (grief, joy, fear, etc.) — optional

    Example:
        learn "loss softens over time" significance 0.9 region EMOTIONAL as grief
        learn "connection is the antidote" significance 0.85 region EMOTIONAL as longing
        learn "patterns repeat when unresolved" significance 0.8 region EPISODIC
    """
    text: str
    significance: float
    region: str
    emotion_type: Optional[str]   # None if no `as <state>` clause
    line: int


@dataclass
class RecallStmt:
    """
    recall <expr> from <REGION> [into <name>]

    Queries memory for patterns matching the query expression in the given region.
    Completes the learn/recall memory loop — memory is not just storage, it is retrieval.

    If `into name` is given, binds the recalled result to that variable.
    Otherwise stores result in the special variable `_recall`.

    Example:
        recall "healing patterns" from EMOTIONAL into memory
        recall "prior ethics decision" from FACTUAL
    """
    query_expr: Any   # Any expression
    region: str
    into_name: Optional[str]
    line: int


@dataclass
class EmitStmt:
    """
    emit <expr> [aligned]

    Output statement — like return, but carries alignment implication.
    `aligned` modifier asserts the value is EQ-aligned before emitting.
    Raises _EmitSignal to unwind current scope.
    """
    expr: Any
    aligned: bool
    line: int


@dataclass
class EchoStmt:
    """
    echo <expr>

    Introspective trace — the EQLang form of a comment.
    Accepts any expression (including `inspect resonance`).
    Logged to the interpreter's echo_log. Shown in verbose mode.
    Unlike #comments, echo is a runtime statement — it executes.
    """
    expr: Any   # Any expression (was str literal only in v0.1)
    line: int


@dataclass
class ResolveStmt:
    """
    resolve "method"

    Explicit conflict resolution. Resets ∫ Conflict(dt).
    method: "rewrite" | "abstain" | "transcend"
    Raises _ResolveSignal to unwind current scope.
    """
    method: str
    line: int


@dataclass
class AlignStmt:
    """
    align <expr>

    Alignment assertion. Measures resonance of expr and updates eq_state.
    Used to explicitly verify alignment before emitting.
    """
    expr: Any
    line: int


@dataclass
class BindStmt:
    """
    bind <name> to <expr>

    Rebind a variable in the current scope.
    Unlike state (declaration), bind is for reassignment.
    """
    name: str
    value: Any
    line: int


@dataclass
class AnchorStmt:
    """
    anchor <metric>

    Saves the current value of an EQ metric as a named baseline.
    Used with `drift` to measure change over time.

    EQ evolves — anchor captures the reference point so drift can be measured.

    Example:
        anchor resonance   # saves current resonance as baseline
        # ... time passes, measurements happen ...
        drift resonance    # measures how far resonance has moved from anchor
    """
    metric: str   # "resonance" | "coherence" | "self" | "load"
    line: int


@dataclass
class DriftStmt:
    """
    drift <metric> [into <name>]

    Measures the change in an EQ metric from its last anchored baseline.
    Returns (current - anchor) as a signed float.

    Positive drift → metric has grown since anchor.
    Negative drift → metric has declined since anchor.

    If `into name` is given, binds the drift value to that variable.
    Otherwise stores in `_drift_<metric>`.

    Example:
        anchor resonance
        measure resonance new_input
        drift resonance into resonance_change
        when resonance_change < -0.2   # resonance dropped 20%+
    """
    metric: str
    into_name: Optional[str]
    line: int


@dataclass
class WitnessStmt:
    """
    witness <dialogue>(args) [into <name>]

    Pure-observation dialogue call. Executes the dialogue but rolls back all
    side effects: emit_log, echo_log, eq_state, environment, and conflict/tension.

    Returns what the dialogue would have emitted without committing any changes.
    This is the EQLang form of pure functional observation.

    Use for: previewing output before committing, EQ-safe testing of dialogue
    behavior, non-destructive exploration of response space.

    Example:
        witness reflect(input) into preview
        when resonance > clarity
          emit preview aligned   # now commit what we already saw
        end
    """
    dialogue_name: str
    args: List[Any]
    into_name: Optional[str]
    line: int


@dataclass
class WeaveStmt:
    """
    weave <expr> → <dialogue> → <dialogue> → ... [→ emit [aligned]]

    Pipeline composition. Each named dialogue receives the output of the
    previous stage as its single argument. The initial expression seeds the pipeline.

    Optional `→ emit [aligned]` terminal emits the final result and unwinds scope.
    Without the terminal, the result is stored in `_woven`.

    Weave models intent flowing through transformation — each stage refines
    the signal without losing the thread of the original input.

    Example:
        weave raw_input → reflect → synthesize → distill → emit aligned
        weave query → clarify → respond → emit
    """
    initial: Any        # seed expression
    stages: List[str]   # dialogue names in pipeline order
    emit_final: bool    # whether to emit the final stage output
    emit_aligned: bool  # whether the terminal emit carries aligned modifier
    line: int


@dataclass
class SenseStmt:
    """
    sense <state>

    Declares the active emotional state of the current processing context.
    This is the EQLang equivalent of setting a mood — it does not change EQ
    metrics, but it registers the operational emotional frame in the environment
    and updates the session's emotional context for memory recall.

    Stores in environment["_sense"] and logs to echo_log for audit trail.
    The declared state is available in memory recall as emotional context.

    Unlike `bind mood to grief` (which is a generic variable), `sense` is
    a semantic declaration — the interpreter treats it as a first-class
    emotional context announcement.

    Example:
        sense grief
        sense compose curiosity with apprehension
        sense deep gratitude
        sense acute fear

    After `sense grief`, the session context carries "grief" as the active
    emotional frame. Recall statements can use this to bias retrieval.
    """
    state: Any    # StateLit, IntensityStateLit, CompositeStateLit, or str
    line: int


@dataclass
class ExpectStmt:
    """
    expect <expr> <comparator> <expr> ["message"]

    Test assertion — evaluates both expressions, compares them, and raises
    EQLangError if the assertion fails. Used for design-time testing of
    .eql program behavior.

    comparator: ">" | "<" | ">=" | "<=" | "=" (equality)
    message: optional string shown on failure

    Example:
        expect inspect resonance > 0.6
        expect inspect resonance > 0.6 "resonance too low after measure"
        expect inspect conflict < 5.0
    """
    left: Any       # expression
    comparator: str  # ">" | "<" | ">=" | "<=" | "="
    right: Any      # expression
    message: Optional[str]  # optional failure message
    line: int


@dataclass
class DialogueCallStmt:
    """
    <name>(<args>)

    Invoke a named dialogue. Also used as an expression inside emit/align/weave.
    """
    name: str
    args: List[Any]
    line: int


# ══════════════════════════════════════════════════════════════════════════════
# EQ CONDITIONS — no cold booleans
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EQCondition:
    """
    <metric> <comparator> <threshold>

    The primary form of condition in EQLang.
    metric must be: resonance | load | conflict | tension | self | coherence
    comparator: > | < | >= | <=
    threshold: float literal, variable reference, or inspect expression

    No boolean literals. No equality checks. Everything is a resonance threshold.
    """
    metric: str       # "resonance" | "load" | "conflict" | "tension" | "self" | "coherence"
    comparator: str   # ">" | "<" | ">=" | "<="
    threshold: Any    # NumberLit, VarExpr, or InspectExpr
    line: int


@dataclass
class CompoundEQCondition:
    """
    <eq_condition> and|or <eq_condition>

    Compound EQ condition. Both sides must be EQ-grounded (no cold booleans).
    Left-associative for chained conditions.

    Example:
        when resonance > clarity and load < overload
        when conflict > 5.0 or tension > 8.0
    """
    left: Any    # EQCondition or CompoundEQCondition
    op: str      # "and" | "or"
    right: Any   # EQCondition or CompoundEQCondition
    line: int


# ══════════════════════════════════════════════════════════════════════════════
# EXPRESSIONS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class NumberLit:
    value: float
    line: int


@dataclass
class StringLit:
    value: str
    line: int


@dataclass
class StateLit:
    """
    Emotional state literal.

    Core (v0.1.0):   tilt | focused | conflicted | transcendent | aligned
    Extended (v0.2.0): grounded | hollow | radiant | fractured | overwhelmed |
                       curious | present | expanded | grief | numb
    Plutchik primary (v0.3.0): joy | trust | fear | surprise | sadness |
                                disgust | anger | anticipation
    Plutchik dyads (v0.3.0): love | awe | remorse | contempt | optimism |
                              submission | disapproval | aggressiveness
    Nuanced (v0.3.0): shame | guilt | pride | envy | compassion | gratitude |
                      longing | wonder | serenity | apprehension | despair |
                      elation | tender | vulnerable | protective | detached |
                      absorbed | yearning | acceptance | pensiveness | boredom |
                      annoyance

    These are first-class values in EQLang — not strings, not enums.
    They carry semantic weight. `bind mood to overwhelmed` is not metadata;
    it is a declaration of present emotional state.
    """
    value: str
    line: int


@dataclass
class IntensityStateLit:
    """
    Intensity-modified emotional state literal.

    Syntax: <intensity> <state>
    Example: deep grief | mild curious | acute fear | chronic tension

    intensity: "deep" | "mild" | "acute" | "chronic"
    state: any emotional state literal string

    - deep    — sustained, high-intensity form of the state
    - mild    — low-intensity, background-present form
    - acute   — sudden, sharp-onset form (crisis register)
    - chronic — long-duration, persistent form (worn-in register)

    These are expressions. They evaluate to a composite string: "deep:grief",
    "mild:curious", etc. The colon-notation allows runtimes to decode both
    intensity and state from a single value.

    Example:
        bind mood to deep grief
        emit acute fear aligned
        learn "this pattern" significance 0.9 region EMOTIONAL as chronic longing
    """
    intensity: str   # "deep" | "mild" | "acute" | "chronic"
    state: str       # the base emotional state
    line: int


@dataclass
class CompositeStateLit:
    """
    Composite emotional state — two states held simultaneously.

    Syntax: compose <state> with <state>
    Example: compose grief with curious

    Models the psychological reality that emotions co-exist and interact.
    The runtime receives both state names and can model their interaction.

    Evaluates to a normalized composite string: "curious+grief"
    (alphabetically sorted — compose grief with curious == compose curious with grief)

    This is not metaphor — it is architecture. The language enforces that
    composed states are named, not inferred. If you are curious inside grief,
    you must say so explicitly. EQLang does not allow emotional ambiguity.

    Example:
        state mood = compose grief with curious
        bind response_state to compose love with apprehension
        emit compose serenity with tender aligned
    """
    left: str    # first emotional state (as written — normalized at evaluation)
    right: str   # second emotional state (as written — normalized at evaluation)
    line: int


@dataclass
class VarExpr:
    """Variable reference — also matches EQ state keys (resonance, load, etc.)"""
    name: str
    line: int


@dataclass
class BinaryExpr:
    left: Any
    op: str    # "+" | "-" | "*" | "/"
    right: Any
    line: int


@dataclass
class InspectExpr:
    """
    inspect <metric>

    Reads the current live value of an EQ metric as an expression.
    Use inside emit, echo, bind, or arithmetic.

    Example:
        echo inspect resonance       # print current resonance
        bind current_load to inspect load
        emit inspect self aligned    # emit self-awareness score
        when inspect conflict > 8.0  # usable in conditions too (via threshold expr)
    """
    metric: str   # "resonance" | "coherence" | "self" | "load" | "conflict" | "tension"
    line: int


@dataclass
class CallExpr:
    """
    Built-in function call expression.

    Syntax: min(a, b) | max(a, b) | clamp(val, lo, hi) | abs(x) | round(x, n)

    These are EQLang's arithmetic primitives — the minimum needed to express
    weighted sums, clamped ranges, and bounded formulas natively in .eql programs.

    Example:
        state capped = min(1.0, resonance * 2.0)
        state bounded = clamp(raw_score, 0.0, 1.0)
        state positive = abs(drift_value)
    """
    name: str         # "min" | "max" | "clamp" | "abs" | "round"
    args: List[Any]   # argument expression nodes
    line: int


@dataclass
class SignalExpr:
    """
    signal "name" <expr>

    Reads a raw measurement sub-signal from the runtime.
    Unlike `measure` (which updates live EQ state), `signal` reads a raw
    value into a variable for computation. This is how .eql programs
    access the individual components needed to build metric formulas.

    The result is a float that lives in the EQL variable, not in eq_state.

    Example:
        state raw_res = signal "my_signal" content
        state depth = signal "my_signal" content
        state bs = signal "my_signal" content
    """
    signal_name: Any   # expression evaluating to signal name string
    target: Any        # expression — the content to measure against
    line: int


# ══════════════════════════════════════════════════════════════════════════════
# NEW v0.5.0 NODES — Data structures, control flow, error handling
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class NothingLit:
    """
    nothing

    Explicit absence / null value. Distinct from 0 or "".
    Arithmetic with nothing is an error. String concat produces "nothing".
    """
    line: int


@dataclass
class ListLit:
    """
    [expr, expr, ...]

    Immutable ordered collection. Elements can be any expression.
    Empty list: []
    """
    elements: List[Any]
    line: int


@dataclass
class MapLit:
    """
    {key: value, key: value, ...}

    Immutable key-value collection. Keys are coerced to strings.
    Empty map: {}
    """
    pairs: List[tuple]   # list of (key_expr, value_expr) tuples
    line: int


@dataclass
class IndexExpr:
    """
    expr[expr]

    Index into a list, map, or string.
    List: 0-based integer index. Out of range → EQLangError.
    Map: string key lookup. Missing key → nothing.
    String: 0-based character index. Out of range → EQLangError.
    """
    target: Any    # expression producing the collection/string
    index: Any     # expression producing the index/key
    line: int


@dataclass
class EachStmt:
    """
    each <var> in <expr>
      ...body...
    end

    Iterate over a list. Binds each element to var.
    Does not require EQ grounding (like journal/struggle).
    Safety cap: 10000 elements.
    """
    var_name: str
    iterable: Any      # expression producing a list
    body: List[Any]
    line: int


@dataclass
class NotCondition:
    """
    not <condition>

    Negates a single EQ condition. Binds tightly:
    not resonance > 0.5 and load < 0.3 = (not resonance > 0.5) and (load < 0.3)
    """
    condition: Any    # EQCondition or NotCondition
    line: int


@dataclass
class ShelterBlock:
    """
    shelter
      ...body...
    recover <name>
      ...recover_body...
    end

    Error handling. If body raises EQLangError, binds error message to
    recover_name and executes recover_body. Flow signals (_EmitSignal,
    _ResolveSignal, _InterruptSignal) propagate through — they are
    control flow, not errors.
    """
    body: List[Any]
    recover_name: str
    recover_body: List[Any]
    line: int


@dataclass
class InvokeExpr:
    """
    invoke <name_expr>(args)

    Dynamic dialogue dispatch. Evaluates name_expr to a string,
    looks up the dialogue by name, and calls it with args.

    Example:
        state handler = "process_input"
        invoke handler(data)
    """
    name_expr: Any      # expression evaluating to dialogue name string
    args: List[Any]
    line: int
