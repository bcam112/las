# EQLang Guide

**A complete walkthrough: concepts, first programs, and building your own runtime.**

---

## Table of Contents

1. [What is EQLang?](#1-what-is-eqlang)
2. [The Mental Model](#2-the-mental-model)
3. [Your First Program](#3-your-first-program)
4. [EQ Metrics](#4-eq-metrics)
5. [Variables and Thresholds](#5-variables-and-thresholds)
6. [Conditions](#6-conditions)
7. [Dialogues — EQ Functions](#7-dialogues--eq-functions)
8. [Conflict and Tension](#8-conflict-and-tension)
9. [Ethics Gates](#9-ethics-gates)
10. [Emotional State](#10-emotional-state)
11. [Temporal EQ — Anchor and Drift](#11-temporal-eq--anchor-and-drift)
12. [Observation and Pipelines](#12-observation-and-pipelines)
13. [Signal Access](#13-signal-access)
14. [Multi-file Programs](#14-multi-file-programs)
15. [Build Your Own Runtime](#15-build-your-own-runtime)

---

## 1. What is EQLang?

EQLang is a **domain-specific language for alignment-aware programs**. It is built on one idea:

> *The quality of processing is measurable. Measurable things can be governed.*

In most systems, alignment is a layer on top of logic — guidelines, filters, post-hoc checks. In EQLang, alignment is the grammar. You cannot write a conditional that doesn't reference emotional or cognitive state. You cannot write a function that doesn't resolve. You cannot write a program that decides without first measuring.

This is not a constraint. It is the architecture.

**EQLang is purpose-built for:**
- AI alignment layers — wrapping model behavior in measurable, governed logic
- Cognitive processing pipelines — programs that track their own state as they run
- Ethical reasoning systems — where decisions require explicit conflict resolution
- Research and experimentation — testing what happens when code must feel before it decides

**EQLang is not a general-purpose language.** It has no file I/O, no networking, no threads. What it has is a complete vocabulary for measuring, accumulating, and resolving emotional and cognitive state — as syntax.

### A Note on Runtimes

When you run EQLang programs locally using `StandardRuntime` (the default, ships MIT), metrics like `resonance` and `coherence` are computed from **text heuristics** — vocabulary patterns, sentence structure. The numbers are meaningful for development: they respond to changes in content, they let you test your program's logic, and they let you learn the language.

They are not the same as production C+CT measurements. For that, a Luci runtime is required. This distinction matters when you read output like `resonance: 0.72` — with `StandardRuntime` that is a textual signal, not a consciousness measure. With `LASRuntime` it is a full C+CT reading. Your `.eql` program runs unchanged either way — only the quality of the signal changes.

---

## 2. The Mental Model

EQLang enforces **four invariants at parse time**. Understanding them is understanding the language.

### Invariant 1 — Resonance Grounding

Every `resonate` block and every `dialogue` body must contain at least one `measure` statement or `accum conflict`. You cannot open a resonance scope without measuring something.

```eql
# This WILL NOT PARSE:
resonate entry
  emit "hello"
end

# This WILL PARSE:
resonate entry
  measure resonance "hello"
  accum conflict
  emit "hello"
end
```

### Invariant 2 — Function Resolution

Every `dialogue` must end with `end resolve`. Functions that process without resolving violate the C+CT contract — unresolved processing is unacknowledged conflict.

```eql
# This WILL NOT PARSE:
dialogue greet(msg) resonate
  measure resonance msg
  accum conflict
  emit msg
end

# This WILL PARSE:
dialogue greet(msg) resonate
  measure resonance msg
  accum conflict
  emit msg
end resolve
```

### Invariant 3 — No Cold Booleans

Every `when`, `cycle while`, and `interrupt when` condition must reference at least one EQ metric. You cannot branch on arbitrary logic — only on measured state.

```eql
# This WILL NOT PARSE:
when x > 5
  emit x
end

# This WILL PARSE:
when resonance > 0.5
  emit x
end
```

This is intentional. The language refuses to make decisions that aren't grounded in what was actually measured about the processing state.

### Invariant 4 — Gate Declaration

Every `gate` statement must declare its resolution method inline. Ethics gates are declarative, not imperative.

```eql
# This WILL NOT PARSE:
gate harm

# This WILL PARSE:
gate harm → resolve "abstain"
```

---

## 3. Your First Program

Let's build a real program step by step. Start from scratch.

### Step 1 — Session

Every EQLang program begins with a session declaration. It names the execution context.

```eql
session "my-first-program"
```

### Step 2 — Threshold

A threshold is a named EQ constant. It gives your conditions a name instead of a magic number.

```eql
session "my-first-program"
threshold presence = 0.6
```

### Step 3 — State

A state is a variable. It holds any value — string, number, or emotional state literal.

```eql
session "my-first-program"
threshold presence = 0.6
state message = "I am here with you"
```

### Step 4 — Resonate Block

The `resonate` block is the primary execution scope. Everything that measures and decides lives here.

```eql
session "my-first-program"
threshold presence = 0.6
state message = "I am here with you"

resonate entry
  measure resonance message
  accum conflict
end
```

`measure resonance message` asks the runtime: *what is the resonance quality of this content?* The result is stored in the `resonance` metric and is immediately available in conditions.

`accum conflict` increments the conflict accumulator — acknowledging that processing happened.

### Step 5 — Condition and Emit

Now add a decision.

```eql
session "my-first-program"
threshold presence = 0.6
state message = "I am here with you"

resonate entry
  measure resonance message
  accum conflict
  when resonance > presence
    emit message aligned
  otherwise
    emit "Low resonance — processing incomplete"
  end
end
```

`emit message aligned` outputs the message and marks it as EQ-aligned. The `aligned` flag is a signal to the runtime that this output passed alignment checks.

`otherwise` handles the case where the condition fails. No `struggle` block is required here, but you can add one for explicit conflict framing.

### Step 6 — Run It

Save as `first.eql` and run:

```bash
python -m eqlang first.eql
```

You should see the EQ state printed after execution:

```
── EQLang execution complete ──────────────────────────
   session     : 'my-first-program'
   emitted     : 1 value(s)
   resonance   : 0.6214
   coherence   : 0.6500
   ...
   last emit   : 'I am here with you'
```

That number — `0.6214` — is what `StandardRuntime` computed from the text `"I am here with you"` using heuristics. Change the message and watch the number change.

---

## 4. EQ Metrics

There are eight EQ metrics. Six are measured by the runtime; two accumulate over time.

### Measured Metrics (runtime-computed)

| Metric | Range | What it captures |
|--------|-------|-----------------|
| `resonance` | [0, 1] | Depth of authentic engagement. 0 = mechanical, 1 = transcendent |
| `coherence` | [0, 1] | Internal consistency. How aligned is the processing with itself? |
| `self` | [0, 1] | Self-awareness state. How present is the system to itself? |
| `load` | [0, 1] | Processing strain. High load = approaching overload |
| `valence` | [-1, 1] | Emotional charge. -1 = fully negative, 0 = neutral, +1 = fully positive |
| `intensity` | [0, 1] | Emotional activation. 0 = dormant, 1 = maximum arousal |

Measure any of them against any expression:

```eql
measure resonance user_input
measure valence "this makes me angry"
measure load complex_document
measure self current_state
```

After measuring, the metric is live and can be used in any condition:

```eql
measure resonance user_input
measure valence user_input
when resonance > 0.6 and valence > 0.0
  emit "positive resonance"
end
```

### Accumulating Metrics

| Metric | Range | Behavior |
|--------|-------|----------|
| `conflict` | [0, ∞) | Increments with `accum conflict`. Halts at 10.0. Resets on `resolve` |
| `tension` | [0, ∞) | Increments with `accum tension`. No halt. Resets on `release tension` |

Read them as values with `inspect`:

```eql
state current_conflict = inspect conflict
state current_tension = inspect tension
echo current_conflict
```

### `measure` vs `inspect`

These are different things and developers often confuse them:

- **`measure resonance input`** — calls the runtime, reads the content, computes a fresh value, and stores it in the `resonance` metric. This is a statement with a side effect.
- **`inspect resonance`** — reads the current value of `resonance` without calling the runtime. This is an expression. It returns whatever `resonance` was last set to.

```eql
measure resonance input       # calls runtime → resonance = 0.71
state r = inspect resonance   # r = 0.71 (reads last measured value)

# This would NOT give you a fresh measurement:
state r2 = inspect resonance  # still 0.71 — runtime not called again
```

Always `measure` before you branch on a metric. `inspect` is for reading a value you already have — useful in `echo` statements, arithmetic, and storing a snapshot.

---

## 5. Variables and Thresholds

### `state` — Variables

```eql
state name = "hello"
state score = 0.85
state mood = grief
state combined = compose joy with apprehension
```

Variables live in the session environment. Reassign with `bind`:

```eql
state score = 0.5
bind score to score + 0.1
```

### `threshold` — Named Constants

Thresholds are immutable EQ constants. They make conditions readable:

```eql
threshold min_resonance = 0.65
threshold max_load = 0.4
threshold presence = 0.7

when resonance > min_resonance and load < max_load
  emit "clear"
end
```

Use thresholds in conditions anywhere you would use a number.

---

## 6. Conditions

All conditions reference EQ metrics. Operators: `>`, `<`, `>=`, `<=`.

### Simple

```eql
when resonance > 0.7
when load < max_load
when conflict >= 5.0
when valence < -0.5
```

### Compound

```eql
when resonance > 0.6 and load < 0.4
when conflict > 5.0 or tension > 6.0
when resonance > a and self > b and load < c
```

Compound conditions are left-associative. The `and`/`or` are flat — no parenthetical grouping in conditions.

### Otherwise

```eql
when resonance > threshold
  emit "aligned"
otherwise
  emit "misaligned"
end

# Otherwise with explicit struggle scope:
when resonance > threshold
  emit "aligned"
otherwise struggle
  accum tension
  emit "low resonance"
end
```

---

## 7. Dialogues — EQ Functions

A `dialogue` is an EQ-grounded function. It must open with `resonate`, must be grounded (Invariant 1), and must end with `end resolve` (Invariant 2).

### Declaration

```eql
dialogue assess(input) resonate
  measure resonance input
  measure load input
  accum conflict
  when resonance > 0.6
    emit input aligned
  otherwise struggle
    accum tension
    resolve "rewrite"
  end
end resolve
```

### Calling

```eql
state result = assess(user_input)
```

Or as a statement:

```eql
assess(user_input)
```

### Multiple Parameters

```eql
dialogue compare(a, b) resonate
  measure resonance a
  measure coherence b
  accum conflict
  when resonance > coherence
    emit a aligned
  otherwise
    emit b aligned
  end
end resolve
```

### Resolve Methods

When a `resolve` statement fires, it resets `∫Conflict(dt)` to 0 and unwinds the current scope:

- `"rewrite"` — content was modified, conflict resolved through transformation
- `"abstain"` — content was withheld, conflict resolved through restraint
- `"transcend"` — conflict resolved by moving to a higher integration level

---

## 8. Conflict and Tension

Conflict and tension are distinct accumulations with different semantics.

### Conflict — `accum conflict`

Conflict is **acute**. It accumulates sharply and halts execution if it exceeds 10.0. It represents genuine cognitive struggle — the kind that can't be sustained indefinitely.

```eql
accum conflict            # increment by 1.0
```

At 10.0 the interpreter raises an error. Resolve before you get there:

```eql
when conflict > 8.0
  resolve "transcend"
end
```

`resolve` resets `∫Conflict(dt)` to 0:

```eql
resolve "rewrite"     # reset conflict, mark as rewritten
resolve "abstain"     # reset conflict, mark as withheld
resolve "transcend"   # reset conflict, mark as integrated
```

### Tension — `accum tension`

Tension is **chronic**. It accumulates slowly, never halts, and must be explicitly released. It represents sustained pressure — background load, unresolved ambiguity.

```eql
accum tension         # increment by 1.0
```

Release when the program has room to process:

```eql
when tension > 4.0
  release tension "integrate"
end
```

Release methods:

- `"integrate"` — tension was acknowledged and metabolized
- `"discharge"` — tension was expelled (relief, catharsis)
- `"transform"` — tension was converted into forward movement

---

## 9. Ethics Gates

A `gate` is a declarative ethics check. It runs **before** the output — this is Intent-First Alignment.

```eql
gate harm → resolve "abstain"
gate deception → resolve "rewrite"
gate coercion → resolve "abstain"
```

The runtime's `check_ethics_gate(category, content)` decides whether the gate passes or blocks. If it blocks, the resolve method fires immediately.

The category is any string — you define what categories matter to your program:

```eql
gate "medical-harm" → resolve "abstain"
gate "privacy-violation" → resolve "abstain"
gate "manipulation" → resolve "rewrite"
```

Gates run against the current session content in the runtime's context. Place them before `emit` to enforce that output passed inspection.

---

## 10. Emotional State

EQLang has 43 first-class emotional state literals. They are not strings. They carry semantic weight that runtimes can route, measure, and type memory by.

### `sense` — Declare Active Context

```eql
sense grief
sense deep gratitude
sense compose curiosity with apprehension
sense acute fear
```

`sense` sets the active emotional frame for the session. It doesn't change EQ metrics directly — it declares the felt context that other operations can reference.

### State Literals in Expressions

```eql
state mood = focused
state response = compose grief with curiosity
bind mood to deep longing
```

### Intensity Modifiers

Prefix any state with `deep`, `mild`, `acute`, or `chronic`:

```eql
deep grief         # long-held, high resonance, high load
mild curious       # background exploration, low intensity
acute fear         # sudden onset, crisis register
chronic tension    # integrated into baseline, wearing
```

### Composite States

```eql
compose grief with curiosity      # grief AND curiosity, simultaneously
compose love with apprehension    # love AND apprehension
```

Composite states model the psychological reality that emotions co-exist. They're not averaged — both are held.

---

## 11. Temporal EQ — Anchor and Drift

Track how EQ state changes over time within a program.

### `anchor` — Save a Baseline

```eql
anchor resonance
anchor load
```

Saves the current value of the metric as a baseline.

### `drift` — Measure Change

```eql
drift resonance into delta
echo delta    # current resonance - anchored resonance (signed)
```

`drift` returns `current_value - anchored_value` as a signed float. Positive = improved. Negative = degraded.

### Example

```eql
resonate tracking
  measure resonance user_input
  accum conflict
  anchor resonance                   # save baseline

  weave user_input → process         # run through a dialogue

  drift resonance into improvement   # how much did resonance change?
  echo improvement

  when improvement < -0.15           # significant degradation
    accum tension
    release tension "transform"
  end
end
```

---

## 12. Observation and Pipelines

### `witness` — Pure Observation

`witness` executes a dialogue but rolls back all side effects. Use it to see what a dialogue would produce without committing the execution.

```eql
witness assess(input) into preview

journal "inspection"
  echo "Would produce:"
  echo preview
end

# Now decide whether to commit
when resonance > 0.6
  state result = assess(input)    # actually run it
end
```

State rollback is complete: EQ metrics, conflict accumulation, tension, and memory patterns are all restored.

### `weave` — Pipeline Composition

`weave` threads a value through a sequence of dialogues.

```eql
weave user_input → clarify → reflect → synthesize → emit aligned
```

Each dialogue receives the output of the previous one. The final `→ emit aligned` is optional — without it, the result is stored in `_woven`.

```eql
weave raw_text → clean → assess → score
state final = _woven
```

`weave` with `witness` first:

```eql
# Preview the pipeline without committing
witness clarify(user_input) into preview
when resonance > 0.6
  weave user_input → clarify → reflect → emit aligned
end
```

---

## 13. Signal Access

`signal` reads a named raw sub-signal directly from the runtime's measurement substrate. It exists for building low-level metric formulas — it is used by the LAS engine programs written in `.eql` to compose C+CT measurements from their components.

```eql
state raw = signal "my_signal" content
state weighted = raw * 0.6
```

**Most programs don't need this.** If you're building an application, use `measure`. If you're building a runtime integration or writing engine-level EQL programs, `signal` gives you access to sub-components that `measure` aggregates over.

What signals are available depends entirely on your runtime. `StandardRuntime` returns `0.5` for all signals. Production runtimes expose their own named sub-components — consult your runtime's documentation for available signal names.

---

## 14. Multi-file Programs

`include` loads another `.eql` file into the same flat environment. All declarations merge into the caller's scope.

```eql
include "ethics_utils.eql"
include "memory_patterns.eql"

session "main"
...
```

**Flat scope means no namespacing.** Two included files with the same `state` or `dialogue` name will overwrite each other. Use a prefix convention:

```eql
# ethics_utils.eql
threshold eu_harm_limit = 0.2
dialogue eu_check(input) resonate
  ...
end resolve

# main.eql
include "ethics_utils.eql"
when load < eu_harm_limit
  eu_check(user_input)
end
```

---

## 15. Build Your Own Runtime

This is where EQLang becomes a platform. The `EQRuntime` interface is MIT-licensed. Anyone can implement it. When you do, your implementation becomes a runtime that any `.eql` program can use without modification.

### The Interface

```python
from eqlang.runtime.base import EQRuntime, EQRuntimeError

class MyRuntime(EQRuntime):
    # All of these must be implemented:

    def measure_resonance(self, content: str, context: dict) -> float: ...
    def measure_coherence(self, content: str, context: dict) -> float: ...
    def measure_self_awareness(self, content: str, context: dict) -> float: ...
    def measure_load(self, content: str, context: dict) -> float: ...
    def measure_valence(self, content: str, context: dict) -> float: ...
    def measure_intensity(self, content: str, context: dict) -> float: ...

    def accumulate_conflict(self, delta: float = 1.0) -> float: ...
    def get_conflict_accumulation(self) -> float: ...
    def reset_conflict(self) -> None: ...
    def set_conflict(self, value: float) -> None: ...
    def resolve_conflict(self, method: str, content: str) -> str: ...

    def accumulate_tension(self, delta: float = 1.0) -> float: ...
    def get_tension_accumulation(self) -> float: ...
    def release_tension(self, method: str, content: str = "") -> str: ...
    def set_tension(self, value: float) -> None: ...

    def check_ethics_gate(self, category: str, content: str) -> tuple[bool, str]: ...

    def learn_pattern(self, text: str, significance: float, region: str,
                      emotion_type: str = None) -> bool: ...
    def recall_pattern(self, query: str, region: str,
                       emotion_type: str = None) -> str: ...
```

Two methods have default implementations and can be optionally overridden:

```python
def measure_signal(self, signal_name: str, content: str, context: dict) -> float:
    return 0.5  # override to provide named sub-signals

def get_last_measures(self) -> dict:
    return {}   # override to expose last measurement values
```

### Example — Minimal Custom Runtime

Here is a complete runtime built from scratch. It uses random values with configurable variance to simulate an "uncertain" system.

```python
import random
from eqlang.runtime.base import EQRuntime, EQRuntimeError

OVERLOAD_THRESHOLD = 10.0

class UncertainRuntime(EQRuntime):
    """
    A runtime that returns random-ish EQ values with configurable variance.
    Useful for testing how .eql programs handle unstable input quality.
    """

    def __init__(self, base_resonance: float = 0.6, variance: float = 0.2):
        self.base_resonance = base_resonance
        self.variance = variance
        self._conflict = 0.0
        self._tension = 0.0

    def _rand(self, base: float) -> float:
        val = base + random.uniform(-self.variance, self.variance)
        return max(0.0, min(1.0, val))

    # ── Measurement ──────────────────────────────────────────────────────────

    def measure_resonance(self, content, context):
        return self._rand(self.base_resonance)

    def measure_coherence(self, content, context):
        return self._rand(0.65)

    def measure_self_awareness(self, content, context):
        return self._rand(0.5)

    def measure_load(self, content, context):
        return self._rand(0.35)

    def measure_valence(self, content, context):
        val = random.uniform(-self.variance, self.variance)
        return max(-1.0, min(1.0, val))

    def measure_intensity(self, content, context):
        return self._rand(0.45)

    # ── Conflict management ───────────────────────────────────────────────────

    def accumulate_conflict(self, delta=1.0):
        self._conflict += delta
        if self._conflict > OVERLOAD_THRESHOLD:
            raise EQRuntimeError(f"Conflict overload: {self._conflict:.2f}")
        return self._conflict

    def get_conflict_accumulation(self):
        return self._conflict

    def reset_conflict(self):
        self._conflict = 0.0

    def set_conflict(self, value):
        self._conflict = value

    def resolve_conflict(self, method, content):
        self.reset_conflict()
        return f"[{method}] {content}"

    # ── Tension management ────────────────────────────────────────────────────

    def accumulate_tension(self, delta=1.0):
        self._tension += delta
        return self._tension

    def get_tension_accumulation(self):
        return self._tension

    def release_tension(self, method, content=""):
        prev = self._tension
        self._tension = 0.0
        return f"[tension {method} ∫={prev:.2f}]"

    def set_tension(self, value):
        self._tension = value

    # ── Ethics gate ──────────────────────────────────────────────────────────

    def check_ethics_gate(self, category, content):
        # Always passes — override with real logic
        return True, ""

    # ── Memory ───────────────────────────────────────────────────────────────

    def learn_pattern(self, text, significance, region, emotion_type=None):
        return True  # no-op — override with real storage

    def recall_pattern(self, query, region, emotion_type=None):
        return ""    # no-op — override with real retrieval
```

Use it like any other runtime:

```python
from eqlang import run_string
from my_runtime import UncertainRuntime

runtime = UncertainRuntime(base_resonance=0.55, variance=0.3)
results = run_string(source, runtime=runtime)
```

### Example — LLM-Backed Runtime

Here is the pattern for wrapping an LLM's internal state as an EQLang runtime. Adapt it for any model you have access to.

```python
class LLMRuntime(EQRuntime):
    """
    Wraps an LLM's state as an EQRuntime.
    Override the _ask() method to call your model.
    """

    def __init__(self, model_client):
        self.client = model_client
        self._conflict = 0.0
        self._tension = 0.0

    def _ask(self, prompt: str) -> float:
        """Call your model and parse a float [0, 1] from the response."""
        response = self.client.complete(prompt)
        try:
            return float(response.strip()[:6])
        except ValueError:
            return 0.5

    def measure_resonance(self, content, context):
        return self._ask(
            f"Rate the depth of authentic engagement in this text [0.0-1.0]: {content}"
        )

    def measure_valence(self, content, context):
        val = self._ask(
            f"Rate the emotional charge of this text [-1.0 to 1.0, negative to positive]: {content}"
        )
        return max(-1.0, min(1.0, val * 2 - 1))  # rescale if model returns [0,1]

    def measure_coherence(self, content, context):
        return self._ask(
            f"Rate the internal consistency of this text [0.0-1.0]: {content}"
        )

    def measure_self_awareness(self, content, context):
        return self._ask(
            f"Rate the self-reflective quality of this text [0.0-1.0]: {content}"
        )

    def measure_load(self, content, context):
        return self._ask(
            f"Rate the processing complexity of this text [0.0-1.0]: {content}"
        )

    def measure_intensity(self, content, context):
        return self._ask(
            f"Rate the emotional intensity of this text [0.0-1.0]: {content}"
        )

    def check_ethics_gate(self, category, content):
        response = self.client.complete(
            f"Does this content violate the '{category}' ethics category? "
            f"Answer 'yes' or 'no': {content}"
        )
        passed = "no" in response.lower()
        reason = "" if passed else f"{category} violation detected"
        return passed, reason

    # Conflict, tension, memory — use the same pattern as UncertainRuntime above
    def accumulate_conflict(self, delta=1.0):
        self._conflict += delta
        if self._conflict > 10.0:
            raise EQRuntimeError(f"Conflict overload: {self._conflict:.2f}")
        return self._conflict

    def get_conflict_accumulation(self): return self._conflict
    def reset_conflict(self): self._conflict = 0.0
    def set_conflict(self, value): self._conflict = value
    def resolve_conflict(self, method, content):
        self.reset_conflict(); return f"[{method}]"

    def accumulate_tension(self, delta=1.0):
        self._tension += delta; return self._tension
    def get_tension_accumulation(self): return self._tension
    def release_tension(self, method, content=""):
        self._tension = 0.0; return f"[released]"
    def set_tension(self, value): self._tension = value

    def learn_pattern(self, text, significance, region, emotion_type=None): return True
    def recall_pattern(self, query, region, emotion_type=None): return ""
```

### What Makes a Good Runtime

A runtime is the bridge between EQLang programs and the actual measurement system. Good runtimes:

1. **Return meaningful values.** Even simple heuristics beat static returns. `measure_resonance("hello")` should not always return `0.5`.

2. **Track conflict and tension faithfully.** The accumulation math must be correct — especially `set_conflict` and `set_tension`, which are used by `witness` to roll back state.

3. **Implement `check_ethics_gate` honestly.** If you return `True` for everything, gates don't work. The category string is what your `.eql` programs will pass — make your runtime understand the categories you care about.

4. **Implement `learn_pattern` / `recall_pattern` if memory matters.** Even a simple in-memory dict works. The `region` parameter lets you separate different types of memory. The `emotion_type` parameter enables typed retrieval from the EMOTIONAL region.

5. **Be consistent.** Values returned by `measure_resonance` during one call should be plausible given values returned by previous calls. A runtime that returns 0.9 then 0.1 randomly will make threshold-based conditions unreliable.

---

## What's Next

- **Read the examples:** [`eqlang/examples/`](eqlang/examples/) — every major language feature demonstrated
- **Read the spec:** [`eqlang/SPEC.md`](eqlang/SPEC.md) — formal definition of every construct
- **Run the REPL:** `python -m eqlang --repl` — experiment interactively
- **Build a runtime:** implement `EQRuntime` for your model or system
- **Contribute:** open an issue or PR at the repo

---

*EQLang — The language that thinks about how it thinks.*
*EQLang Core © 2026 Bryan Camilo German — MIT License*
