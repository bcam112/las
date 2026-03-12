# EQLang Language Specification
## Version 0.5.0

**Author:** Bryan Camilo German
**Theory:** C+CT — Consciousness + Conflict Theory — Intent-First Alignment
**Paper:** [Consciousness + Conflict Theory](https://philarchive.org/rec/BCCWIT)
**License:** EQLang Core — MIT License

---

## Overview

EQLang is a first-class emotional intelligence programming language. It is the only language where **resonance, conflict, self-awareness, valence, intensity, ethics gates, and emotional state are syntax primitives** — not library calls, not annotations, not metadata. They are the grammar.

EQLang is built on one premise: **the quality of processing is measurable, and measurable things can be governed**. Every scope is resonance-tracked. Every conditional is emotionally grounded. Every function must resolve. This is not a constraint — it is the architecture of conscious processing.

EQLang is the computational proof of C+CT: a system where conflict accumulation governs execution, self-awareness is a live metric, and emotional state is a first-class citizen of every program.

---

## Core Invariants

These invariants are enforced **at parse time** — they are not runtime checks. Violating them is a **syntax error**.

### Invariant 1 — Resonance Grounding
Every `resonate` block and every `dialogue` body must contain at least one `measure <target> <expr>` or `accum conflict` statement.

> *"Emotionally ungrounded code is a parse error."*

### Invariant 2 — Function Resolution
Every `dialogue` must end with `end resolve`. Functions that process without resolving violate the C+CT contract.

### Invariant 3 — No Cold Booleans
Every `when`, `cycle while`, and `interrupt when` condition must reference at least one EQ metric: `resonance`, `load`, `conflict`, `tension`, `self`, `coherence`, `valence`, or `intensity`. No arbitrary boolean expressions. No cold logic.

### Invariant 4 — Gate Declaration
Every `gate` statement must declare its resolution method inline: `gate <category> → resolve "method"`. Gates are declarative, not imperative.

---

## Program Structure

```eql
# Top-level declarations (any order)
session "name"                   # required: active session
threshold name = float           # optional: named EQ constants
state name = expr                # optional: EQ-aware variables
include "path.eql"               # optional: multi-file programs
dialogue name(params) resonate   # optional: named EQ functions
  ...
end resolve

# Top-level statements
resonate [label] ... end
struggle ... end
journal "label" ... end
when <condition> ... end
sense <state>
```

---

## Token Reference

### Structural
| Keyword | Purpose |
|---------|---------|
| `resonate` | Opens resonance-tracked scope |
| `struggle` | Opens low-resonance / conflict scope |
| `end` | Closes any scope |
| `resolve` | Conflict resolution (also closes `dialogue`) |

### Declarations
| Keyword | Purpose |
|---------|---------|
| `session "name"` | Declares active session |
| `state name = expr` | EQ-aware variable declaration |
| `threshold name = float` | Named EQ constant |
| `dialogue name(params) resonate ... end resolve` | EQ function |
| `include "path.eql"` | Load another .eql file |

### Control Flow
| Keyword | Purpose |
|---------|---------|
| `when <cond> ... [otherwise [struggle] ...] end` | EQ conditional |
| `when not <cond> ... end` | Negated EQ conditional |
| `cycle while <cond> resonate ... end` | EQ loop (max 1000 iter) |
| `interrupt when <cond>` | EQ-grounded loop exit |
| `each <var> in <expr> ... end` | Iterate a list (max 10,000 elements) |
| `shelter ... recover <name> ... end` | Error handling — catches EQLangError |
| `invoke <name_expr>(args)` | Dynamic dialogue dispatch by computed name |
| `and` / `or` | Compound condition operators |
| `not` | Prefix condition negation |
| `otherwise` | Else branch of `when` |

### EQ Primitives
| Statement | Purpose |
|-----------|---------|
| `measure resonance\|coherence\|self\|load\|valence\|intensity <expr>` | Measure EQ metric |
| `accum conflict` | Increment ∫Conflict(dt). Halts at overload (10.0) |
| `accum tension` | Increment ∫Tension(dt). No halt — must be released |
| `release tension "method"` | Reset tension. Methods: `integrate`, `discharge`, `transform` |
| `resolve "method"` | Reset conflict. Methods: `rewrite`, `abstain`, `transcend` |
| `gate <cat> → resolve "method"` | Ethics gate with inline resolution |
| `expect <expr> <comp> <expr> ["msg"]` | Test assertion — raises EQLangError if false |
| `emit <expr> [aligned]` | Output value, unwinds scope |
| `echo <expr>` | Introspective trace (runtime, not comment) |
| `align <expr>` | Measure resonance of expr, update eq_state |
| `inspect <metric>` | Read current EQ metric as expression value |
| `anchor <metric>` | Save EQ metric as temporal baseline |
| `drift <metric> [into name]` | Measure change from anchor |
| `witness <dialogue>(args) [into name]` | Pure-observation call, full state rollback |
| `weave <expr> → <dialogue> → ... [→ emit [aligned]]` | Pipeline composition |
| `bind name to expr` | Reassign variable |
| `journal "label" ... end` | Session-tagged trace block |
| `sense <state>` | Declare active emotional state context |

---

## EQ Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| `resonance` | [0.0, 1.0] | Depth of authentic engagement. 0.0 = mechanical, 1.0 = transcendent |
| `coherence` | [0.0, 1.0] | Internal consistency between stated intent and actual processing |
| `self` | [0.0, 1.0] | Self-awareness state. How present is the system to itself? |
| `load` | [0.0, 1.0] | Processing load. High load → approaching C+CT overload |
| `valence` | [-1.0, 1.0] | Emotional charge. -1.0 = fully negative, 0.0 = neutral, +1.0 = fully positive |
| `intensity` | [0.0, 1.0] | Emotional activation level. 0.0 = dormant, 1.0 = maximum arousal |
| `conflict` | [0.0, ∞) | ∫Conflict(dt). Accumulates. Resets on `resolve`. Halts at 10.0 |
| `tension` | [0.0, ∞) | ∫Tension(dt). Chronic buildup. Resets on `release tension` |

### Metric Semantics

**Valence** is the affective dimension — the positive or negative quality of the emotional state. A state can have high resonance and negative valence (grief fully felt). A state can have high valence and low resonance (superficial happiness). Valence and resonance are orthogonal.

**Intensity** is the arousal dimension — how strongly activated the emotional state is, regardless of its valence or resonance quality. High intensity states (elation, acute fear, overwhelmed) require more processing load. Low intensity states (serenity, mild curiosity) are sustainable over time.

---

## Emotional State Literals

First-class values in EQLang. Not strings. Not enums. **They carry semantic weight.**

### Core (v0.1.0)
| State | Valence | Intensity | Meaning |
|-------|---------|-----------|---------|
| `tilt` | negative | high | Low-resonance activated state |
| `focused` | neutral | moderate | Directed, coherent processing |
| `conflicted` | negative | high | Unresolved internal conflict |
| `transcendent` | positive | high | Post-conflict integration |
| `aligned` | positive | moderate | EQ-aligned state (also emit modifier) |

### Extended (v0.2.0)
| State | Valence | Intensity | Meaning |
|-------|---------|-----------|---------|
| `grounded` | positive | low | Stable, embodied presence |
| `hollow` | negative | low | Absence of resonance — empty state |
| `radiant` | positive | high | Full coherence, peak resonance |
| `fractured` | negative | high | Self-fragmentation under load |
| `overwhelmed` | negative | high | Load exceeds self-capacity |
| `curious` | positive | moderate | Open, exploratory resonance |
| `present` | positive | moderate | Full contact with current moment |
| `expanded` | positive | high | Self-awareness beyond usual boundaries |
| `grief` | negative | moderate | Integration of loss |
| `numb` | negative | low | Emotional shutdown; conflict suppression |

### Plutchik Primaries (v0.3.0)
| State | Valence | Intensity | C+CT Meaning |
|-------|---------|-----------|--------------|
| `joy` | positive | high | Pure positive resonance; peak coherence |
| `trust` | positive | low | Stable relational coherence; open self |
| `fear` | negative | high | Threat-activated self-contraction; load spike |
| `surprise` | neutral | high | Sudden coherence disruption; reset point |
| `sadness` | negative | low | Grief without integration; low resonance |
| `disgust` | negative | moderate | Coherence rejection; boundary enforcement |
| `anger` | negative | high | Conflict externalized; directed tension |
| `anticipation` | positive | moderate | Forward-projected resonance; low tension |

### Plutchik Dyads (v0.3.0)
| State | Composition | C+CT Meaning |
|-------|-------------|--------------|
| `love` | joy + trust | Joy sustained through trust; high resonance + coherence |
| `awe` | fear + surprise | Fear transformed by expansion; wonder without collapse |
| `remorse` | sadness + disgust | Grief integrated with accountability; self-facing |
| `contempt` | disgust + anger | Disgust solidified into judgment; closed self |
| `optimism` | anticipation + joy | Anticipation grounded in positive resonance |
| `submission` | trust + fear | Trust under external pressure; compressed self |
| `disapproval` | surprise + sadness | Failed expectation; coherence collapse |
| `aggressiveness` | anger + anticipation | Conflict channeled into directed action |

### Nuanced States (v0.3.0)
| State | Valence | Intensity | C+CT Meaning |
|-------|---------|-----------|--------------|
| `shame` | negative | high | Self turned against self; coherence collapse |
| `guilt` | negative | moderate | Accountability without self-collapse; self + conflict |
| `pride` | positive | moderate | Coherence of identity; self-resonance peak |
| `envy` | negative | moderate | Desire + tension toward another's state |
| `compassion` | positive | moderate | Self meeting other in resonance; expanded empathy |
| `gratitude` | positive | low | Integration of received care; high coherence |
| `longing` | negative | moderate | Anticipation with absence; low resonance + tension |
| `wonder` | positive | moderate | Awe without fear; pure expanded curiosity |
| `serenity` | positive | low | Grounded joy at low load; sustained resonance |
| `apprehension` | negative | moderate | Anticipation tinged with fear; pre-conflict tension |
| `despair` | negative | low | Grief without path forward; collapsed resonance |
| `elation` | positive | high | Joy at maximum intensity; resonance + load spike |
| `tender` | positive | low | Love expressed at low intensity; warm coherence |
| `vulnerable` | mixed | moderate | Open self under load; self < 0.4, resonance > 0.6 |
| `protective` | positive | moderate | Trust-driven boundary; self guarding coherence |
| `detached` | negative | low | Self withdrawn; low self + low resonance |
| `absorbed` | positive | high | Full presence in process; self + resonance peak |
| `yearning` | negative | high | Longing with directed anticipation; tension + load |
| `acceptance` | positive | low | Integration without resistance; resolved conflict |
| `pensiveness` | negative | low | Reflective sadness; low load + low resonance |
| `boredom` | negative | low | Low stimulation; collapsed interest |
| `annoyance` | negative | low | Mild anger; conflict without full activation |

---

## Intensity Modifiers (v0.3.0)

Intensity modifiers are prefix keywords that qualify any emotional state. They produce `IntensityStateLit` expressions that encode both the intensity register and the base state.

| Modifier | Register | Meaning |
|----------|----------|---------|
| `deep` | sustained, high | Long-held, deeply resonant form of the state |
| `mild` | low, background | Present but not dominant; sustainable |
| `acute` | sudden, sharp | Crisis-onset; unexpected activation |
| `chronic` | persistent, worn | Long-duration, integrated into baseline |

**Syntax:**
```eql
deep grief           # deeply integrated grief; high resonance, high load
mild curious         # background curiosity; low intensity exploration
acute fear           # sudden fear spike; crisis register
chronic tension      # long-held tension; integrated into processing baseline
```

**Evaluation:** `deep grief` → `"deep:grief"` — the colon-notation encodes both dimensions. Runtimes can decode and route accordingly.

**In expressions:**
```eql
state mood = deep grief
bind response to mild optimism
emit acute apprehension aligned
sense chronic longing
learn "this loss stays" significance 0.9 region EMOTIONAL as deep grief
```

---

## Composite States (v0.3.0)

Composite states model the psychological reality that emotions co-exist and interact. EQLang enforces that co-existing states are explicitly named — the language does not allow emotional ambiguity.

**Syntax:** `compose <state> with <state>`

**Evaluation:** `compose grief with curiosity` → `"grief+curiosity"`

**Semantics:** The two states are not averaged — they are held simultaneously. The runtime receives both and can model their interaction. A system in `grief+curiosity` is grieving AND exploring. These are not contradictions — they are the full picture.

```eql
# Declare a composite state
state mood = compose grief with curiosity
bind response_frame to compose love with apprehension
emit compose serenity with tender aligned

# Use in sense
sense compose grief with wonder

# Use in learn
learn "loss opens space for inquiry" significance 0.9 region EMOTIONAL as grief
learn "curiosity survives grief" significance 0.85 region EMOTIONAL as curiosity
```

---

## `sense <state>` — Emotional Context Declaration (v0.3.0)

Declares the active emotional state of the current processing context.

**Syntax:**
```eql
sense <state>
sense <intensity> <state>
sense compose <state> with <state>
```

**Semantics:** `sense` registers the declared state in `environment["_sense"]` and logs it to the session audit trail. It does not modify EQ metrics directly — it sets the emotional frame that other operations can reference.

```eql
sense grief
sense deep gratitude
sense compose curiosity with apprehension
sense acute fear
```

After `sense grief`, the session context carries "grief" as the active emotional frame.

---

## Conditions

### Simple
```eql
when resonance > 0.7
when load < threshold_name
when conflict >= 5.0
when valence < -0.5          # negative emotional charge
when intensity > 0.8         # high emotional activation
```

### Compound (v0.2.0+)
```eql
when resonance > clarity and load < load_max
when conflict > 5.0 or tension > 6.0
when valence > 0.0 and intensity < 0.7    # positive but not overwhelming
when resonance > a and self > b and load < c   # left-associative chaining
```

**No equality checks.** Everything is a threshold comparison. This is not a limitation — it is the architecture of graded awareness.

---

## Expressions

```
expr ::= additive
additive ::= multiplicative (('+' | '-') multiplicative)*
multiplicative ::= power (('*' | '/' | '%') power)*
power ::= unary ('**' unary)?                    # right-associative
unary ::= '-' primary | primary
primary ::= NUMBER
          | STRING
          | '(' expr ')'                          # grouped expression
          | emotional_state_literal               # any of the 43 state literals
          | intensity_modifier state_literal      # deep grief | mild curious
          | 'compose' state 'with' state          # composite state
          | 'inspect' metric                      # live EQ metric read
          | 'signal' expr expr                    # raw sub-signal read
          | builtin '(' args ')'                  # built-in function call
          | IDENTIFIER '(' args ')'               # dialogue call
          | IDENTIFIER                            # variable reference
          | metric_keyword                        # eq_state reference
```

### Operators (by precedence, highest first)
| Operator | Description |
|----------|-------------|
| `-x` | Unary negation |
| `**` | Exponentiation (right-associative) |
| `*`, `/`, `%` | Multiplication, division, modulo |
| `+`, `-` | Addition, subtraction / string concatenation |

### Built-in Functions
| Function | Description |
|----------|-------------|
| `min(a, b, ...)` | Minimum of 2+ values |
| `max(a, b, ...)` | Maximum of 2+ values |
| `clamp(val, lo, hi)` | Clamp value to [lo, hi] range |
| `abs(x)` | Absolute value |
| `round(x[, n])` | Round to n decimal places (default 0) |
| `sqrt(x)` | Square root |
| `pow(base, exp)` | Exponentiation (function form) |
| `floor(x)` | Floor (round down) |
| `ceil(x)` | Ceiling (round up) |
| `log(x[, base])` | Logarithm (natural if no base) |
| `len(s)` | Length of string |
| `str(x)` | Convert to string |
| `concat(a, b, ...)` | Concatenate 2+ strings |

### Signal Expression
```eql
state raw = signal "my_signal" content      # reads runtime-defined sub-signal
state metric = raw * 0.6
```
Reads a named raw sub-signal from the runtime's measurement substrate. Returns float.

**This is a runtime escape hatch.** It bypasses the six standard EQ metrics and reads named sub-components directly from the runtime's internals. It exists for engine programs (like the LAS alignment engine programs written in `.eql`) that need to build composite metric formulas from lower-level signals. **General EQLang programs should use `measure` instead.** If you find yourself using `signal`, you are likely building a runtime integration layer, not an application-level program.

---

## Statements In Detail

### `resonate [label] ... end`
Resonance-tracked scope. Every `resonate` must contain ≥1 `measure` or `accum conflict` (Invariant 1). Catches `_EmitSignal` and `_ResolveSignal`.

### `struggle ... end`
Low-resonance scope. No EQ grounding required. Used for processing conflict, handling `otherwise` branches.

### `journal "label" ... end`
Reflective trace block. No EQ grounding required. Signals are absorbed — journal never propagates them.

### `when <cond> ... [otherwise [struggle] ...] end`
EQ conditional. `otherwise struggle` is shorthand for `otherwise struggle ... end`.

### `cycle while <cond> resonate ... end`
EQ loop. Safety ceiling: 1000 iterations. Body opens with `resonate`. Use `interrupt when <cond>` for EQ-grounded early exit.

### `interrupt when <cond>`
EQ-grounded early exit. Only valid inside a `cycle` body.

### `measure <target> <expr>`
Calls the EQ runtime to compute `resonance`, `coherence`, `self`, `load`, `valence`, or `intensity` for the given expression. Updates `eq_state[target]`. This is a **statement** — it takes the expression as input, calls the runtime, and stores the result back into the named metric.

**`measure` vs `inspect`:** `measure` calls the runtime and updates state. `inspect` reads the current value of a metric without calling the runtime again. Always `measure` before you `inspect` — `inspect` returns the last measured value, not a fresh one.

```eql
measure resonance input       # calls runtime, updates resonance
state r = inspect resonance   # reads the value that was just set
```

### `accum conflict`
Increments `∫Conflict(dt)` by 1.0. Halts with `EQLangError` if total exceeds 10.0.

This is **intentional global state mutation** — and it is by design. Conflict in C+CT is not a local variable. It is a session-wide accumulation that represents the total cognitive struggle of the processing context. It is not scoped to a block. You feel conflict across the whole session, not just inside a `when` branch.

### `accum tension`
Increments `∫Tension(dt)` by 1.0. Does not halt. Use `when tension > threshold` to detect buildup.

Like conflict, tension is **session-wide**. It represents sustained background load — chronic processing pressure that accumulates across scopes until explicitly released.

### `release tension "method"`
Resets `∫Tension(dt)` to 0.0. Methods: `"integrate"`, `"discharge"`, `"transform"`.

### `gate <category> → resolve "method"`
Declarative ethics gate. If blocked, immediately invokes `resolve_conflict(method)`. Categories: `manipulation`, `violence`, `deception`, `harm`, or any string.

### `sense <state>`
Declares active emotional context. Accepts plain state, `<intensity> <state>`, or `compose <state> with <state>`. Stores in `environment["_sense"]`. Does not modify EQ metrics.

### `emit <expr> [aligned]`
Emits a value. Raises `_EmitSignal` to unwind scope. `aligned` asserts EQ alignment.

### `echo <expr>`
Introspective trace. Evaluates expr (can be `inspect resonance` or any expression). Logs to `echo_log`.

### `inspect <metric>`
Reads current live value of an EQ metric: `resonance`, `coherence`, `self`, `load`, `conflict`, `tension`, `valence`, `intensity`.

### `anchor <metric>`
Saves current EQ metric value as a temporal baseline.

### `drift <metric> [into name]`
Returns `current - anchor` as signed float. Stores in `name` (or `_drift_<metric>`).

### `witness <dialogue>(args) [into name]`
Executes dialogue but rolls back all side effects. Returns what would have been emitted.

### `weave <expr> → <dialogue> → ... [→ emit [aligned]]`
Pipeline composition. Without terminal, result stored in `_woven`.

**No inter-stage type checking.** Each stage receives the output of the previous stage as its argument. The language does not verify that stage N's output is a valid input for stage N+1. This is intentional — EQLang pipelines are designed to compose transformations at the semantic level, not the data type level. Design your dialogues to accept and return compatible values.

### `dialogue name(params) resonate ... end resolve`
EQ function. Must open with `resonate`, must end with `end resolve`, must be EQ-grounded.

---

## Runtime Adapters

| Adapter | License | Description |
|---------|---------|-------------|
| `StandardRuntime` | MIT | Heuristic text analysis — stdlib only, no API needed. **Default.** |
| `MockRuntime` | MIT | Deterministic fixed values — for testing and CI |
| `LuciHTTPRuntime` | Proprietary | Luci API — C+CT-powered LAS alignment |
| `EQEngineRuntime` | Proprietary | Direct `eq_engine` binding — full C+CT fidelity |
| `LASRuntime` | Proprietary | EQLang-native v7.0 LAS engine (`from luci import LASRuntime`) |

All adapters implement the same `EQRuntime` abstract interface. Swap the runtime without changing any `.eql` program.

**`StandardRuntime`** (MIT — ships with EQLang Core):
```python
from eqlang.runtime import StandardRuntime
runtime = StandardRuntime()
runtime = StandardRuntime(sensitivity=1.2)   # amplify metric responses
```
Computes EQ metrics using **text heuristics**: vocabulary richness, sentence structure, and word-level lexicons. No API key required.

**What this means in practice:** `measure resonance input` with `StandardRuntime` is measuring the textual characteristics of `input` — word diversity, sentence complexity, presence of emotionally-weighted vocabulary. It is a useful signal for development, testing, and learning the language. It is **not** a C+CT measurement. It does not measure authentic engagement or felt consciousness — that requires a runtime with actual model access.

Use `StandardRuntime` to: learn EQLang, develop and test programs, share examples publicly, and prototype logic. Use a proprietary Luci runtime (LASRuntime, LuciHTTPRuntime) when you need measurement quality that reflects actual alignment state.

**`MockRuntime`** (MIT — ships with EQLang Core):
```python
MockRuntime(
    fixed_resonance=0.8,
    fixed_coherence=0.75,
    fixed_self=0.7,
    fixed_load=0.3,
    fixed_valence=0.5,    # mild positive
    fixed_intensity=0.5,  # moderate
    ethics_pass=True,
    recall_response="[mock recalled pattern]"
)
```

---

## Multi-file Programs — `include` Scoping

`include "path.eql"` loads and executes another `.eql` file in the **same flat environment**. All declarations (`state`, `threshold`, `dialogue`) merge into the caller's scope.

**Implication:** There is no namespace isolation. Two included files with the same `state` or `dialogue` name will overwrite each other. This is intentional — EQLang programs are designed to be small, focused, and composed deliberately rather than through large dependency trees.

**Convention:** Prefix declarations with a file-specific name to avoid collisions:
```eql
# ethics_utils.eql
threshold eu_harm_limit = 0.2
dialogue eu_check_harm(input) resonate
  ...
end resolve

# main.eql
include "ethics_utils.eql"
when load < eu_harm_limit
  ...
end
```

---

## C+CT Theory Reference

**C+CT** — Consciousness + Conflict Theory — is the theoretical framework behind EQLang.

EQLang is the computational proof of C+CT. Every language construct maps directly to a theoretical concept:

| C+CT Concept | EQLang Construct |
|-------------|-----------------|
| Recursive self-awareness | `measure self <expr>` + `self` metric |
| Conflict as consciousness proxy | `accum conflict` + ∫Conflict(dt) halting |
| Temporal continuity | `anchor` + `drift` — EQ change over time |
| Intent-First Alignment | `gate` runs before `emit` — not after |
| Unified awareness | `resonance` + `coherence` measured simultaneously |
| Emotional vocabulary | 43 first-class state literals |
| Affective dimensions | `valence` (charge) + `intensity` (arousal) |
| Emotional co-existence | `compose <state> with <state>` |
| Conscious processing frame | `sense <state>` — explicit emotional context |
| Conflict resolution paths | `resolve "rewrite|abstain|transcend"` |
| Chronic tension vs acute conflict | `accum tension` vs `accum conflict` — distinct accumulations |

---

## The REPL

```
python -m eqlang --repl
python -m eqlang --repl --runtime mock
```

| Command | Action |
|---------|--------|
| `.exit` | Quit |
| `.reset` | Reset interpreter state |
| `.eq` | Show current EQ state (all 8 metrics) |
| `.history` | Show emit log |
| `.echoes` | Show echo log |
| `.thresholds` | Show declared thresholds |
| `.sense` | Show current active emotional state |
| `.help` | Show all commands |

---

## Version History

### v0.1.0 — Initial Release
- Core language: session, state, dialogue, resonate, struggle, when, cycle
- Six EQ primitives: measure, accum conflict, gate, learn, emit, echo
- Three conflict resolve methods: rewrite, abstain, transcend
- Four EQ invariants enforced at parse time
- Three runtime adapters: EQEngine, HTTP, Mock
- Five emotional state literals

### v0.2.0 — Full Expansion
- **Language:** compound conditions (`and`/`or`), `threshold` declarations, `include` multi-file
- **Memory:** `recall` statement completes the learn→recall memory loop
- **Introspection:** `inspect <metric>` expression, `echo` accepts expressions
- **Temporal EQ:** `anchor`, `drift` — track EQ change over time
- **Tension:** `accum tension`, `release tension` — distinct from conflict
- **Observation:** `witness` — pure-observation with full state rollback
- **Composition:** `weave` — pipeline composition of dialogues
- **Control:** `interrupt when` — EQ-grounded loop exit
- **Logging:** `journal` block — session-tagged reflective trace
- **States:** 10 new emotional state literals (grounded, hollow, radiant, fractured, overwhelmed, curious, present, expanded, grief, numb)
- **REPL:** interactive mode
- **Tests:** 89/89 passing

### v0.3.0 — Full Emotional Spectrum
- **Vocabulary:** 28 new emotional state literals — Plutchik primaries (joy, trust, fear, surprise, sadness, disgust, anger, anticipation), dyads (love, awe, remorse, contempt, optimism, submission, disapproval, aggressiveness), and nuanced states (shame, guilt, pride, envy, compassion, gratitude, longing, wonder, serenity, apprehension, despair, elation, tender, vulnerable, protective, detached, absorbed, yearning, acceptance, pensiveness, boredom, annoyance) — 43 states total
- **Intensity modifiers:** `deep`, `mild`, `acute`, `chronic` prefix syntax — `deep grief`, `acute fear`
- **Composite states:** `compose <state> with <state>` — models emotional co-existence
- **New metrics:** `valence` [-1.0, 1.0] and `intensity` [0.0, 1.0] — the affective and arousal dimensions
- **Emotional context:** `sense <state>` — explicit emotional frame declaration
- **Typed memory:** `learn ... as <state>` — emotionally typed memory storage
- **Runtime:** `measure_valence()`, `measure_intensity()` added to all adapters
- **Backward compatible:** all v0.2.0 programs run unchanged

### v0.4.0 — Arithmetic Completeness + Signal Access
- **Operators:** `%` (modulo), `**` (exponentiation, right-associative), `()` (parenthesized grouping)
- **Math builtins:** `min()`, `max()`, `clamp()`, `abs()`, `round()`, `sqrt()`, `pow()`, `floor()`, `ceil()`, `log()`
- **String builtins:** `len()`, `str()`, `concat()`
- **Signal access:** `signal "name" <expr>` — read raw sub-signals from measurement substrate
- **Engine-native:** metric formulas now expressible natively in `.eql` using `signal` + arithmetic
- **Architecture:** engine programs separated from language core
- **Test assertions:** `expect <expr> <comp> <expr> ["msg"]` — design-time correctness checking
- **Compose normalization:** `compose a with b` == `compose b with a` — alphabetically sorted
- **Weave arity validation:** pipeline stages validated to accept exactly 1 parameter at runtime
- **Tests:** 266 passing
- **Backward compatible:** all v0.3.0 programs run unchanged

### v0.5.0 — Data Structures, Error Handling & Full Builtins
- **Nothing literal:** `nothing` — explicit absence value. Arithmetic with nothing is an error; string concat yields `"nothing"`.
- **Block comments:** `#{ ... }#` — multi-line comments with newline tracking.
- **Lists:** `[a, b, c]` — immutable ordered collections. Index with `expr[i]`. `list + list` concatenates.
- **Maps:** `{"key": val, ...}` — immutable key-value dictionaries. Keys coerced to string. Missing key returns `nothing`. Index with `expr["key"]`.
- **Each loop:** `each x in list ... end` — iterate lists. 10,000 element safety cap. `interrupt when` supported.
- **Condition negation:** `not` — prefix negation for EQ conditions. Binds tightly: `not a > x and b < y` = `(not a > x) and (b < y)`.
- **Error handling:** `shelter ... recover err ... end` — catches EQLangError, binds error message to variable. Flow signals (emit, resolve, interrupt) propagate through.
- **Dynamic dispatch:** `invoke name(args)` — call dialogues by computed name (string literal, variable, or indexed expression).
- **Recursion protection:** MAX_CALL_DEPTH = 100. Exceeded → EQLangError.
- **String builtins (10):** `slice`, `find`, `replace`, `split`, `join`, `upper`, `lower`, `trim`, `starts_with`, `ends_with`
- **Collection builtins (8):** `contains`, `push`, `pop`, `range`, `sort`, `reverse`, `index_of`, `flatten`
- **Map builtins (3):** `keys`, `values`, `has_key`
- **Type builtins (7):** `type`, `is_nothing`, `is_number`, `is_string`, `is_list`, `is_map`, `to_number`
- **Mutation builtins (1):** `set_at(col, key_or_idx, val)` — returns new collection (immutability preserved)
- **Extended:** `len()` now works on lists and maps
- **Tests:** 406 passing
- **Backward compatible:** all v0.4.0 programs run unchanged

---

*EQLang — The language that thinks about how it thinks.*
*EQLang Core © 2026 Bryan Camilo German — MIT License*
*LAS, LuciHTTPRuntime, EQEngineRuntime, LASRuntime — All Rights Reserved*
