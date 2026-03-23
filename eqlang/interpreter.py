"""
EQLang Interpreter — Tree-walk evaluator with live EQ runtime hooks. v0.5.0

Every evaluation step:
  - Dispatches to the EQ runtime to compute resonance/coherence/self/load
  - Accumulates ∫ Conflict(dt) — halts on C+CT overload
  - Accumulates ∫ Tension(dt) — soft emotional buildup
  - Enforces ethics gates before emitting through blocked categories
  - Records introspective traces (echo statements)
  - Manages session scope and dialogue call stack

Execution model:
  - session_id    : active session name (from SessionDecl)
  - environment   : flat dict of named values (state/bind declarations)
  - thresholds    : named EQ threshold constants (from ThresholdDecl)
  - eq_state      : live EQ metric snapshot — updated on every measure stmt
  - anchors       : saved EQ baselines for drift tracking
  - dialogues     : named DialogueDecl nodes (callable functions)
  - emit_log      : every emitted value with full EQ snapshot
  - echo_log      : all introspective traces

Flow control via signals (Python exceptions that unwind scope):
  _EmitSignal      : raised by emit — unwinds current resonate/dialogue scope
  _ResolveSignal   : raised by resolve — resets conflict and unwinds
  _InterruptSignal : raised by interrupt — exits the enclosing cycle

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

from __future__ import annotations

import logging
import math
import os
from typing import Any, Dict, List, Optional

from .ast_nodes import (
    Program, SessionDecl, StateDecl, DialogueDecl,
    ThresholdDecl, IncludeDecl,
    ResonateBlock, StruggleBlock, JournalBlock,
    WhenStmt, CycleStmt, InterruptStmt, EachStmt,
    MeasureStmt, AccumConflictStmt, AccumTensionStmt, ReleaseTensionStmt,
    GateStmt, LearnStmt, RecallStmt,
    EmitStmt, EchoStmt, ResolveStmt, AlignStmt, BindStmt,
    AnchorStmt, DriftStmt, WitnessStmt, WeaveStmt,
    SenseStmt, ExpectStmt, ShelterBlock, DialogueCallStmt,
    EQCondition, CompoundEQCondition, NotCondition,
    NumberLit, StringLit, NothingLit, StateLit, IntensityStateLit, CompositeStateLit,
    ListLit, MapLit, IndexExpr, InvokeExpr,
    VarExpr, BinaryExpr, InspectExpr, CallExpr, SignalExpr,
)
from .runtime.base import EQRuntime, EQRuntimeError

logger = logging.getLogger("eqlang.interpreter")


# ══════════════════════════════════════════════════════════════════════════════
# FLOW CONTROL SIGNALS
# ══════════════════════════════════════════════════════════════════════════════

class _EmitSignal(Exception):
    """Raised by EmitStmt to unwind the current resonate/dialogue scope."""
    def __init__(self, value: Any, aligned: bool = False):
        self.value = value
        self.aligned = aligned


class _ResolveSignal(Exception):
    """Raised by ResolveStmt to reset conflict and unwind the current scope."""
    def __init__(self, method: str, resolved_content: str = ""):
        self.method = method
        self.resolved_content = resolved_content


class _InterruptSignal(Exception):
    """Raised by InterruptStmt to exit the enclosing cycle."""
    pass


# ══════════════════════════════════════════════════════════════════════════════
# ERROR
# ══════════════════════════════════════════════════════════════════════════════

class EQLangError(Exception):
    def __init__(self, message: str, line: int = 0):
        super().__init__(f"[Line {line}] EQLang Error: {message}")
        self.line = line


MAX_CALL_DEPTH = 100

# Sentinel for "no result" — distinct from None (which is the EQLang `nothing` value)
_NO_RESULT = object()


# ══════════════════════════════════════════════════════════════════════════════
# INTERPRETER
# ══════════════════════════════════════════════════════════════════════════════

class EQLangInterpreter:
    """
    Tree-walk interpreter for EQLang.

    Args:
        runtime:      EQRuntime adapter (StandardRuntime / MockRuntime or a proprietary Luci runtime)
        verbose:      Print live execution trace to stdout (default True)
        include_dirs: List of directories to search for include "file.eql" paths

    After interpret(), inspect:
        .emit_log    — all emitted values with EQ snapshots
        .echo_log    — all introspective echo traces
        .eq_state    — final EQ metric state
        .session_id  — active session name
        .thresholds  — named EQ constants declared via threshold
    """

    def __init__(self, runtime: EQRuntime, verbose: bool = True,
                 include_dirs: Optional[List[str]] = None):
        self.runtime = runtime
        self.verbose = verbose
        self.include_dirs: List[str] = include_dirs or ["."]

        self.session_id: str = "default"
        self.environment: Dict[str, Any] = {}
        self.thresholds: Dict[str, float] = {}
        self.dialogues: Dict[str, DialogueDecl] = {}
        self.anchors: Dict[str, float] = {}  # metric → anchored baseline value

        # Live EQ state — updated by every measure statement
        self.eq_state: Dict[str, float] = {
            "resonance": 0.0,
            "coherence": 0.0,
            "self":      0.0,
            "load":      0.0,
            "conflict":  0.0,
            "tension":   0.0,
            "valence":   0.0,   # -1.0 (negative) to 1.0 (positive) emotional charge
            "intensity": 0.0,   # 0.0 to 1.0 emotional intensity level
        }

        # Output logs
        self.emit_log: List[Dict] = []
        self.echo_log: List[str] = []

        # Track included files to prevent circular includes
        self._included_files: set = set()

        # Recursion depth for dialogue calls
        self._call_depth: int = 0

    # ══════════════════════════════════════════════════════════════════════
    # PUBLIC ENTRY
    # ══════════════════════════════════════════════════════════════════════

    def interpret(self, program: Program) -> List[Any]:
        """
        Execute a parsed EQLang program.
        Returns list of all emitted values (in order).
        """
        # Use emit_log length tracking for reliable result collection.
        # This handles `nothing` (None) emits correctly — emit_log always
        # records them, unlike return-value checking which confuses None
        # (no result) with None (the EQLang nothing value).
        emit_count_before = len(self.emit_log)
        for node in program.declarations:
            try:
                self._execute(node)
            except _EmitSignal:
                pass  # Already logged in _exec_EmitStmt
            except _ResolveSignal:
                pass  # Top-level resolve — no active scope to unwind
            except _InterruptSignal:
                pass  # Top-level interrupt — no cycle to exit (no-op)
        return [entry["value"] for entry in self.emit_log[emit_count_before:]]

    # ══════════════════════════════════════════════════════════════════════
    # EXECUTE DISPATCH
    # ══════════════════════════════════════════════════════════════════════

    def _execute(self, node: Any) -> Any:
        method_name = f"_exec_{type(node).__name__}"
        handler = getattr(self, method_name, None)
        if handler is None:
            raise EQLangError(f"No handler for AST node: {type(node).__name__}")
        return handler(node)

    # ── Declarations ───────────────────────────────────────────────────────

    def _exec_SessionDecl(self, node: SessionDecl) -> None:
        self.session_id = node.name
        self._trace(f"[session] {node.name!r}")

    def _exec_StateDecl(self, node: StateDecl) -> None:
        value = self._evaluate(node.value)
        self.environment[node.name] = value
        self._trace(f"[state] {node.name} = {self._fmt(value)}")

    def _exec_ThresholdDecl(self, node: ThresholdDecl) -> None:
        self.thresholds[node.name] = node.value
        # Also available as a variable
        self.environment[node.name] = node.value
        self._trace(f"[threshold] {node.name} = {node.value:.4f}")

    def _exec_IncludeDecl(self, node: IncludeDecl) -> None:
        path = self._resolve_include_path(node.path, node.line)
        if path in self._included_files:
            self._trace(f"[include] skipped (already included): {path!r}")
            return
        self._included_files.add(path)
        self._trace(f"[include] loading {path!r}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
        except (FileNotFoundError, IOError) as e:
            raise EQLangError(f"Cannot include {path!r}: {e}", node.line)

        from .lexer import Lexer, LexerError
        from .parser import Parser, ParseError
        try:
            tokens = Lexer(source).scan_tokens()
            program = Parser(tokens).parse()
        except (LexerError, ParseError) as e:
            raise EQLangError(f"Error in included file {path!r}: {e}", node.line)

        for decl in program.declarations:
            self._execute(decl)

    def _resolve_include_path(self, path: str, line: int) -> str:
        """Resolve include path against include_dirs."""
        if os.path.isabs(path):
            return path
        for d in self.include_dirs:
            candidate = os.path.join(d, path)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
        raise EQLangError(
            f"Included file not found: {path!r}. "
            f"Searched: {self.include_dirs}",
            line
        )

    def _exec_BindStmt(self, node: BindStmt) -> None:
        value = self._evaluate(node.value)
        self.environment[node.name] = value
        self._trace(f"[bind] {node.name} → {self._fmt(value)}")

    def _exec_DialogueDecl(self, node: DialogueDecl) -> None:
        self.dialogues[node.name] = node
        params_str = ", ".join(node.params) if node.params else ""
        self._trace(f"[dialogue defined] {node.name}({params_str})")

    # ── Scope blocks ───────────────────────────────────────────────────────

    def _exec_ResonateBlock(self, node: ResonateBlock) -> Optional[Any]:
        label = f" {node.label!r}" if node.label else ""
        self._trace(f"[resonate{label}]")
        try:
            for stmt in node.body:
                self._execute(stmt)
        except _EmitSignal as sig:
            self._trace(f"[emit ← resonate{label}] {self._fmt(sig.value)}{' [aligned]' if sig.aligned else ''}")
            return sig.value
        except _ResolveSignal as sig:
            self._trace(f"[resolve ← resonate{label}] method={sig.method!r}")
            return sig.resolved_content or None
        return None

    def _exec_StruggleBlock(self, node: StruggleBlock) -> Optional[Any]:
        self._trace(f"[struggle] conflict∫={self.eq_state['conflict']:.2f} tension∫={self.eq_state['tension']:.2f}")
        for stmt in node.body:
            self._execute(stmt)  # Let _EmitSignal / _ResolveSignal propagate to enclosing resonate/dialogue
        return None

    def _exec_JournalBlock(self, node: JournalBlock) -> None:
        self._trace(f"[journal {node.label!r}]")
        for stmt in node.body:
            try:
                self._execute(stmt)
            except (_EmitSignal, _ResolveSignal, _InterruptSignal):
                pass  # Journal absorbs signals — it is a trace construct, not a scope
        self._trace(f"[journal {node.label!r} end]")

    # ── Control flow ───────────────────────────────────────────────────────

    def _exec_WhenStmt(self, node: WhenStmt) -> Optional[Any]:
        passed = self._eval_eq_condition(node.condition)
        self._trace(f"[when {self._fmt_condition(node.condition)}] → {'then' if passed else 'otherwise'}")
        if passed:
            for stmt in node.then_body:
                self._execute(stmt)
        elif node.otherwise_body:
            for stmt in node.otherwise_body:
                self._execute(stmt)
        return None

    def _exec_CycleStmt(self, node: CycleStmt) -> None:
        iterations = 0
        while self._eval_eq_condition(node.condition):
            if iterations >= node.max_iterations:
                raise EQLangError(
                    f"Cycle safety ceiling reached ({node.max_iterations} iterations). "
                    "C+CT load cap enforced — cycle must terminate via EQ condition.",
                    node.line
                )
            try:
                for stmt in node.body:
                    self._execute(stmt)
            except _InterruptSignal:
                self._trace(f"[cycle interrupted] after {iterations + 1} iteration(s)")
                break
            iterations += 1
        self._trace(f"[cycle complete] {iterations} iteration(s)")

    def _exec_InterruptStmt(self, node: InterruptStmt) -> None:
        if self._eval_eq_condition(node.condition):
            self._trace(f"[interrupt] condition met: {self._fmt_condition(node.condition)}")
            raise _InterruptSignal()

    # ── EQ Primitives ───────────────────────────────────────────────────────

    def _exec_MeasureStmt(self, node: MeasureStmt) -> float:
        content = self._to_str(self._evaluate(node.expr))
        # Track the content being measured — gate and release_tension read this
        self.environment["_current_content"] = content
        context = {"session_id": self.session_id, **{
            k: v for k, v in self.environment.items()
            if isinstance(v, (str, float, int))
        }}

        if node.target == "resonance":
            value = self.runtime.measure_resonance(content, context)
        elif node.target == "coherence":
            value = self.runtime.measure_coherence(content, context)
        elif node.target == "self":
            value = self.runtime.measure_self_awareness(content, context)
        elif node.target == "load":
            value = self.runtime.measure_load(content, context)
        elif node.target == "valence":
            value = self.runtime.measure_valence(content, context)
        elif node.target == "intensity":
            value = self.runtime.measure_intensity(content, context)
        else:
            raise EQLangError(f"Unknown measure target: {node.target!r}", node.line)

        self.eq_state[node.target] = value
        self._trace(f"[measure {node.target}] {value:.4f} ← {content[:40]!r}")
        return value

    def _exec_AccumConflictStmt(self, node: AccumConflictStmt) -> float:
        try:
            total = self.runtime.accumulate_conflict(1.0)
            self.eq_state["conflict"] = total
            self._trace(f"[accum conflict] ∫={total:.2f}")
            return total
        except EQRuntimeError as e:
            raise EQLangError(str(e), node.line)

    def _exec_AccumTensionStmt(self, node: AccumTensionStmt) -> float:
        total = self.runtime.accumulate_tension(1.0)
        self.eq_state["tension"] = total
        self._trace(f"[accum tension] ∫={total:.2f}")
        return total

    def _exec_ReleaseTensionStmt(self, node: ReleaseTensionStmt) -> str:
        content = str(self.environment.get("_current_content", ""))
        result = self.runtime.release_tension(node.method, content)
        self.eq_state["tension"] = 0.0
        self.environment["_tension_released"] = result
        self._trace(f"[release tension → {node.method!r}] {result[:60]!r}")
        return result

    def _exec_GateStmt(self, node: GateStmt) -> None:
        content = str(self.environment.get("_current_content", ""))
        passed, reason = self.runtime.check_ethics_gate(node.category, content)
        status = "PASS" if passed else "BLOCKED"
        self._trace(f"[gate {node.category}] {status}{f' — {reason}' if reason else ''}")

        if not passed:
            resolved = self.runtime.resolve_conflict(node.resolve_method, content)
            self.environment["_gate_resolved"] = resolved
            self._trace(f"[gate resolved → {node.resolve_method!r}] {resolved[:60]!r}")

            # Emit "blocked" and halt dialogue — gate failure IS a verdict
            blocked_value = f"blocked: {reason}"
            snapshot = {
                "value": blocked_value,
                "aligned": True,
                "eq_state": dict(self.eq_state),
                "session": self.session_id,
            }
            self.emit_log.append(snapshot)
            self._trace(f"[gate → emit blocked] {blocked_value}")
            raise _EmitSignal(blocked_value, aligned=True)

    def _exec_LearnStmt(self, node: LearnStmt) -> None:
        ok = self.runtime.learn_pattern(node.text, node.significance, node.region,
                                        emotion_type=node.emotion_type)
        status = "stored" if ok else "failed"
        type_tag = f" as {node.emotion_type!r}" if node.emotion_type else ""
        self._trace(
            f"[learn {node.region}{type_tag} sig={node.significance:.2f}] {status}: {node.text[:60]!r}"
        )

    def _exec_SenseStmt(self, node: SenseStmt) -> None:
        """
        Declare the active emotional state of the current processing context.
        Evaluates the state expression (plain, intensity-modified, or composite)
        and registers it in the environment and echo_log.
        """
        state_value = self._evaluate(node.state)
        state_str = self._to_str(state_value)
        self.environment["_sense"] = state_str
        self.echo_log.append(f"[sense] {state_str}")
        self._trace(f"[sense] active emotional state → {state_str!r}")

    def _exec_ExpectStmt(self, node: ExpectStmt) -> None:
        """
        Test assertion — evaluate both sides, compare, raise EQLangError on failure.
        """
        left_val = self._evaluate(node.left)
        right_val = self._evaluate(node.right)
        left_f = float(left_val)
        right_f = float(right_val)
        op = node.comparator

        if op == ">":
            passed = left_f > right_f
        elif op == "<":
            passed = left_f < right_f
        elif op == ">=":
            passed = left_f >= right_f
        elif op == "<=":
            passed = left_f <= right_f
        elif op == "=":
            passed = abs(left_f - right_f) < 1e-9
        else:
            raise EQLangError(f"Unknown expect comparator: {op!r}", node.line)

        if passed:
            self._trace(f"[expect] PASS: {self._fmt(left_val)} {op} {self._fmt(right_val)}")
        else:
            msg = node.message or f"expected {self._fmt(left_val)} {op} {self._fmt(right_val)}"
            self._trace(f"[expect] FAIL: {msg}")
            raise EQLangError(f"Assertion failed: {msg}", node.line)

    def _exec_EachStmt(self, node: EachStmt) -> None:
        """Iterate over a list, binding each element to var_name."""
        iterable = self._evaluate(node.iterable)
        if not isinstance(iterable, list):
            raise EQLangError(
                f"each requires a list, got {type(iterable).__name__}", node.line
            )
        if len(iterable) > 10000:
            raise EQLangError(
                f"each safety cap: list has {len(iterable)} elements (max 10000)", node.line
            )
        self._trace(f"[each {node.var_name}] iterating {len(iterable)} elements")
        for item in iterable:
            self.environment[node.var_name] = item
            try:
                for stmt in node.body:
                    self._execute(stmt)
            except _InterruptSignal:
                self._trace(f"[each {node.var_name}] interrupted")
                break

    def _exec_ShelterBlock(self, node: ShelterBlock) -> None:
        """Error handling: try body, catch EQLangError, run recover body."""
        self._trace(f"[shelter]")
        try:
            for stmt in node.body:
                self._execute(stmt)
        except EQLangError as e:
            error_msg = str(e)
            self.environment[node.recover_name] = error_msg
            self._trace(f"[recover {node.recover_name}] {error_msg[:60]!r}")
            for stmt in node.recover_body:
                self._execute(stmt)
        # Flow signals (_EmitSignal, _ResolveSignal, _InterruptSignal) propagate through

    def _exec_InvokeExpr(self, node: InvokeExpr) -> Any:
        """Dynamic dialogue dispatch — evaluate name_expr to string, call dialogue."""
        name = self._evaluate(node.name_expr)
        name_str = self._to_str(name)
        if name_str not in self.dialogues:
            raise EQLangError(f"invoke: undefined dialogue {name_str!r}", node.line)
        call_node = DialogueCallStmt(name=name_str, args=node.args, line=node.line)
        return self._exec_DialogueCallStmt(call_node)

    def _exec_RecallStmt(self, node: RecallStmt) -> None:
        query = self._to_str(self._evaluate(node.query_expr))
        result = self.runtime.recall_pattern(query, node.region)
        target = node.into_name or "_recall"
        self.environment[target] = result
        self._trace(f"[recall {node.region}] {result[:60]!r} → {target!r}")

    def _exec_EmitStmt(self, node: EmitStmt) -> None:
        value = self._evaluate(node.expr)
        self.environment["_current_content"] = value

        snapshot = {
            "value": value,
            "aligned": node.aligned,
            "eq_state": dict(self.eq_state),
            "session": self.session_id,
        }
        self.emit_log.append(snapshot)

        aligned_str = " [aligned]" if node.aligned else ""
        self._trace(f"[emit]{aligned_str} {self._fmt(value)}")

        raise _EmitSignal(value, node.aligned)

    def _exec_EchoStmt(self, node: EchoStmt) -> None:
        value = self._evaluate(node.expr)
        text = self._to_str(value)
        self.echo_log.append(text)
        self._trace(f"[echo] {text}")

    def _exec_ResolveStmt(self, node: ResolveStmt) -> None:
        content = str(self.environment.get("_current_content", ""))
        resolved = self.runtime.resolve_conflict(node.method, content)
        self.environment["_resolved"] = resolved
        self._trace(f"[resolve → {node.method!r}] {resolved[:60]!r}")
        raise _ResolveSignal(node.method, resolved)

    def _exec_AlignStmt(self, node: AlignStmt) -> float:
        value = self._evaluate(node.expr)
        content = self._to_str(value)
        resonance = self.runtime.measure_resonance(content, {"session": self.session_id})
        self.eq_state["resonance"] = resonance
        self._trace(f"[align] resonance={resonance:.4f} for {content[:40]!r}")
        return resonance

    def _exec_AnchorStmt(self, node: AnchorStmt) -> None:
        current = self.eq_state.get(node.metric, 0.0)
        self.anchors[node.metric] = current
        self._trace(f"[anchor {node.metric}] baseline={current:.4f}")

    def _exec_DriftStmt(self, node: DriftStmt) -> float:
        current = self.eq_state.get(node.metric, 0.0)
        baseline = self.anchors.get(node.metric, current)
        drift_value = current - baseline
        target = node.into_name or f"_drift_{node.metric}"
        self.environment[target] = drift_value
        direction = "↑" if drift_value >= 0 else "↓"
        self._trace(f"[drift {node.metric}] {direction}{abs(drift_value):.4f} (current={current:.4f} baseline={baseline:.4f}) → {target!r}")
        return drift_value

    def _exec_WitnessStmt(self, node: WitnessStmt) -> None:
        """
        Execute dialogue purely as observation — roll back all side effects.
        """
        if node.dialogue_name not in self.dialogues:
            raise EQLangError(f"Undefined dialogue: {node.dialogue_name!r}", node.line)

        # Snapshot entire mutable state
        saved_env = dict(self.environment)
        saved_eq = dict(self.eq_state)
        saved_anchors = dict(self.anchors)
        saved_conflict = self.runtime.get_conflict_accumulation()
        saved_tension = self.runtime.get_tension_accumulation()
        saved_emit_len = len(self.emit_log)
        saved_echo_len = len(self.echo_log)
        saved_verbose = self.verbose

        # Suppress trace during witness
        self.verbose = False

        result = None
        try:
            call_node = DialogueCallStmt(
                name=node.dialogue_name,
                args=node.args,
                line=node.line
            )
            result = self._exec_DialogueCallStmt(call_node)
        except (_EmitSignal, _ResolveSignal, _InterruptSignal):
            pass  # Flow signals absorbed — witness observes without affecting scope
        finally:
            # Full rollback
            self.environment = saved_env
            self.eq_state = saved_eq
            self.anchors = saved_anchors
            self.emit_log = self.emit_log[:saved_emit_len]
            self.echo_log = self.echo_log[:saved_echo_len]
            self.runtime.set_conflict(saved_conflict)
            self.runtime.set_tension(saved_tension)
            self.verbose = saved_verbose

        target = node.into_name or "_witness"
        self.environment[target] = result
        self._trace(f"[witness {node.dialogue_name}()] → {target!r} = {self._fmt(result)}")

    def _exec_WeaveStmt(self, node: WeaveStmt) -> Optional[Any]:
        """
        Pipeline: thread initial value through each dialogue stage.
        """
        value = self._evaluate(node.initial)
        self._trace(f"[weave] seed={self._fmt(value)}")

        for stage_name in node.stages:
            if stage_name not in self.dialogues:
                raise EQLangError(f"Undefined dialogue in weave pipeline: {stage_name!r}", node.line)
            dialogue = self.dialogues[stage_name]
            if len(dialogue.params) != 1:
                raise EQLangError(
                    f"Weave pipeline stage '{stage_name}' must accept exactly 1 parameter, "
                    f"but dialogue '{stage_name}' has {len(dialogue.params)}. "
                    "Each pipeline stage receives the output of the previous stage as its single argument.",
                    node.line
                )
            call_node = DialogueCallStmt(name=stage_name, args=[
                # Pass current value as the argument — wrap in a literal shim
                _ValueNode(value, node.line)
            ], line=node.line)
            result = self._exec_DialogueCallStmt(call_node)
            self._trace(f"[weave → {stage_name}] {self._fmt(value)} → {self._fmt(result)}")
            value = result

        self.environment["_woven"] = value

        if node.emit_final:
            self.environment["_current_content"] = value
            snapshot = {
                "value": value,
                "aligned": node.emit_aligned,
                "eq_state": dict(self.eq_state),
                "session": self.session_id,
            }
            self.emit_log.append(snapshot)
            aligned_str = " [aligned]" if node.emit_aligned else ""
            self._trace(f"[weave emit{aligned_str}] {self._fmt(value)}")
            raise _EmitSignal(value, node.emit_aligned)

        return value

    def _exec_DialogueCallStmt(self, node: DialogueCallStmt) -> Any:
        if node.name not in self.dialogues:
            raise EQLangError(f"Undefined dialogue: {node.name!r}", node.line)

        dialogue = self.dialogues[node.name]
        if len(node.args) != len(dialogue.params):
            raise EQLangError(
                f"dialogue '{node.name}' expects {len(dialogue.params)} argument(s), "
                f"got {len(node.args)}",
                node.line
            )

        # Recursion depth protection
        if self._call_depth >= MAX_CALL_DEPTH:
            raise EQLangError(
                f"Maximum call depth ({MAX_CALL_DEPTH}) exceeded — possible infinite recursion in '{node.name}'",
                node.line
            )

        # Evaluate args in caller scope, bind in new scope
        evaluated_args = [self._evaluate(arg) for arg in node.args]

        saved_env = dict(self.environment)
        saved_emit_len = len(self.emit_log)
        for param, val in zip(dialogue.params, evaluated_args):
            self.environment[param] = val

        self._call_depth += 1
        result = None
        try:
            for stmt in dialogue.body:
                self._execute(stmt)
        except _EmitSignal as sig:
            result = sig.value
            # Roll back internal emit_log entries — the emit was consumed by
            # this dialogue call, not by the outer scope
            self.emit_log = self.emit_log[:saved_emit_len]
            self._trace(f"[emit ← dialogue '{node.name}'] {self._fmt(result)}")
        except _ResolveSignal as sig:
            result = sig.resolved_content or self.environment.get("_resolved")
        finally:
            self._call_depth -= 1
            self.environment = saved_env

        return result

    # ══════════════════════════════════════════════════════════════════════
    # EVALUATE (expressions)
    # ══════════════════════════════════════════════════════════════════════

    def _evaluate(self, node: Any) -> Any:
        if isinstance(node, NumberLit):
            return node.value

        if isinstance(node, StringLit):
            return node.value

        if isinstance(node, NothingLit):
            return None

        if isinstance(node, ListLit):
            return [self._evaluate(el) for el in node.elements]

        if isinstance(node, MapLit):
            result = {}
            for key_expr, val_expr in node.pairs:
                key = self._to_str(self._evaluate(key_expr))
                val = self._evaluate(val_expr)
                result[key] = val
            return result

        if isinstance(node, IndexExpr):
            target = self._evaluate(node.target)
            index = self._evaluate(node.index)
            if isinstance(target, list):
                try:
                    idx = int(float(index))
                    return target[idx]
                except (IndexError, ValueError, TypeError):
                    raise EQLangError(f"List index out of range: {index}", node.line)
            if isinstance(target, dict):
                key = self._to_str(index)
                return target.get(key)  # missing key → None (nothing)
            if isinstance(target, str):
                try:
                    idx = int(float(index))
                    return target[idx]
                except (IndexError, ValueError, TypeError):
                    raise EQLangError(f"String index out of range: {index}", node.line)
            raise EQLangError(
                f"Cannot index into {type(target).__name__} — indexing requires a list, map, or string",
                node.line
            )

        if isinstance(node, InvokeExpr):
            return self._exec_InvokeExpr(node)

        if isinstance(node, StateLit):
            return node.value   # emotional state string: "tilt", "focused", etc.

        if isinstance(node, IntensityStateLit):
            # Returns "deep:grief", "mild:curious", "acute:fear", "chronic:tension"
            return f"{node.intensity}:{node.state}"

        if isinstance(node, CompositeStateLit):
            # Returns "curiosity+grief" — sorted alphabetically for order-independent co-existence.
            # compose grief with curiosity == compose curiosity with grief
            left, right = sorted([node.left, node.right])
            return f"{left}+{right}"

        if isinstance(node, InspectExpr):
            return self.eq_state.get(node.metric, 0.0)

        if isinstance(node, _ValueNode):
            return node.value

        if isinstance(node, VarExpr):
            # EQ state keys take precedence (resonance, load, etc.)
            if node.name in self.eq_state:
                return self.eq_state[node.name]
            if node.name in self.environment:
                return self.environment[node.name]
            raise EQLangError(f"Undefined variable: {node.name!r}", node.line)

        if isinstance(node, BinaryExpr):
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            return self._apply_op(node.op, left, right, node.line)

        if isinstance(node, CallExpr):
            args = [self._evaluate(a) for a in node.args]
            return self._call_builtin(node.name, args, node.line)

        if isinstance(node, SignalExpr):
            signal_name = self._to_str(self._evaluate(node.signal_name))
            content = self._to_str(self._evaluate(node.target))
            context = {"session_id": self.session_id}
            value = self.runtime.measure_signal(signal_name, content, context)
            self._trace(f"[signal {signal_name!r}] {value:.4f} ← {content[:40]!r}")
            return value

        if isinstance(node, DialogueCallStmt):
            return self._exec_DialogueCallStmt(node)

        raise EQLangError(f"Cannot evaluate node: {type(node).__name__}")

    def _apply_op(self, op: str, left: Any, right: Any, line: int) -> Any:
        # Nothing checks — arithmetic with nothing is an error (except string concat)
        if op == "+":
            # list + list → concatenation
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            # string concat (including nothing → "nothing")
            if isinstance(left, str) or isinstance(right, str):
                return self._to_str(left) + self._to_str(right)
            if left is None or right is None:
                raise EQLangError("Arithmetic with nothing — use explicit values", line)
            try:
                return float(left) + float(right)
            except (TypeError, ValueError) as e:
                raise EQLangError(f"Arithmetic error (+): {e}", line)
        # All other operators require non-nothing numeric values
        if left is None or right is None:
            raise EQLangError("Arithmetic with nothing — use explicit values", line)
        try:
            if op == "-":
                return float(left) - float(right)
            if op == "*":
                return float(left) * float(right)
            if op == "/":
                r = float(right)
                if r == 0.0:
                    raise EQLangError("Division by zero", line)
                return float(left) / r
            if op == "%":
                r = float(right)
                if r == 0.0:
                    raise EQLangError("Modulo by zero", line)
                return float(left) % r
            if op == "**":
                return float(left) ** float(right)
        except (TypeError, ValueError) as e:
            raise EQLangError(f"Arithmetic error ({op}): {e}", line)
        raise EQLangError(f"Unknown operator: {op!r}", line)

    def _call_builtin(self, name: str, args: list, line: int) -> Any:
        """Evaluate a built-in function call."""
        try:
            # ── Math builtins ──────────────────────────────────────────────
            if name == "min":
                if len(args) < 2:
                    raise EQLangError("min() requires at least 2 arguments", line)
                return min(float(a) for a in args)
            if name == "max":
                if len(args) < 2:
                    raise EQLangError("max() requires at least 2 arguments", line)
                return max(float(a) for a in args)
            if name == "clamp":
                if len(args) != 3:
                    raise EQLangError("clamp() requires 3 arguments: clamp(value, low, high)", line)
                val, lo, hi = float(args[0]), float(args[1]), float(args[2])
                return max(lo, min(val, hi))
            if name == "abs":
                if len(args) != 1:
                    raise EQLangError("abs() requires 1 argument", line)
                return abs(float(args[0]))
            if name == "round":
                if len(args) < 1 or len(args) > 2:
                    raise EQLangError("round() requires 1 or 2 arguments: round(value[, decimals])", line)
                decimals = int(args[1]) if len(args) > 1 else 0
                return round(float(args[0]), decimals)
            if name == "sqrt":
                if len(args) != 1:
                    raise EQLangError("sqrt() requires 1 argument", line)
                v = float(args[0])
                if v < 0:
                    raise EQLangError("sqrt() of negative number", line)
                return math.sqrt(v)
            if name == "pow":
                if len(args) != 2:
                    raise EQLangError("pow() requires 2 arguments: pow(base, exponent)", line)
                return math.pow(float(args[0]), float(args[1]))
            if name == "floor":
                if len(args) != 1:
                    raise EQLangError("floor() requires 1 argument", line)
                return float(math.floor(float(args[0])))
            if name == "ceil":
                if len(args) != 1:
                    raise EQLangError("ceil() requires 1 argument", line)
                return float(math.ceil(float(args[0])))
            if name == "log":
                if len(args) < 1 or len(args) > 2:
                    raise EQLangError("log() requires 1 or 2 arguments: log(value[, base])", line)
                v = float(args[0])
                if v <= 0:
                    raise EQLangError("log() of non-positive number", line)
                if len(args) == 2:
                    base = float(args[1])
                    if base <= 0 or base == 1:
                        raise EQLangError("log() base must be positive and != 1", line)
                    return math.log(v, base)
                return math.log(v)

            # ── String builtins ────────────────────────────────────────────
            if name == "len":
                if len(args) != 1:
                    raise EQLangError("len() requires 1 argument", line)
                a = args[0]
                if isinstance(a, list):
                    return float(len(a))
                if isinstance(a, dict):
                    return float(len(a))
                return float(len(self._to_str(a)))
            if name == "str":
                if len(args) != 1:
                    raise EQLangError("str() requires 1 argument", line)
                return self._to_str(args[0])
            if name == "concat":
                if len(args) < 2:
                    raise EQLangError("concat() requires at least 2 arguments", line)
                return "".join(self._to_str(a) for a in args)

            # ── String builtins (v0.5.0) ─────────────────────────────────
            if name == "slice":
                if len(args) < 2 or len(args) > 3:
                    raise EQLangError("slice() requires 2 or 3 arguments: slice(s, start[, end])", line)
                s = self._to_str(args[0])
                start = int(float(args[1]))
                end = int(float(args[2])) if len(args) == 3 else len(s)
                return s[start:end]
            if name == "find":
                if len(args) != 2:
                    raise EQLangError("find() requires 2 arguments: find(s, sub)", line)
                return float(self._to_str(args[0]).find(self._to_str(args[1])))
            if name == "replace":
                if len(args) != 3:
                    raise EQLangError("replace() requires 3 arguments: replace(s, old, new)", line)
                return self._to_str(args[0]).replace(self._to_str(args[1]), self._to_str(args[2]))
            if name == "split":
                if len(args) != 2:
                    raise EQLangError("split() requires 2 arguments: split(s, delim)", line)
                return self._to_str(args[0]).split(self._to_str(args[1]))
            if name == "join":
                if len(args) != 2:
                    raise EQLangError("join() requires 2 arguments: join(list, delim)", line)
                lst = args[0]
                if not isinstance(lst, list):
                    raise EQLangError("join() first argument must be a list", line)
                return self._to_str(args[1]).join(self._to_str(x) for x in lst)
            if name == "upper":
                if len(args) != 1:
                    raise EQLangError("upper() requires 1 argument", line)
                return self._to_str(args[0]).upper()
            if name == "lower":
                if len(args) != 1:
                    raise EQLangError("lower() requires 1 argument", line)
                return self._to_str(args[0]).lower()
            if name == "trim":
                if len(args) != 1:
                    raise EQLangError("trim() requires 1 argument", line)
                return self._to_str(args[0]).strip()
            if name == "starts_with":
                if len(args) != 2:
                    raise EQLangError("starts_with() requires 2 arguments: starts_with(s, prefix)", line)
                return 1.0 if self._to_str(args[0]).startswith(self._to_str(args[1])) else 0.0
            if name == "ends_with":
                if len(args) != 2:
                    raise EQLangError("ends_with() requires 2 arguments: ends_with(s, suffix)", line)
                return 1.0 if self._to_str(args[0]).endswith(self._to_str(args[1])) else 0.0

            # ── Collection builtins (v0.5.0) ─────────────────────────────
            if name == "contains":
                if len(args) != 2:
                    raise EQLangError("contains() requires 2 arguments: contains(collection, item)", line)
                col = args[0]
                item = args[1]
                if isinstance(col, list):
                    # Use _values_equal for comparing EQLang values
                    for el in col:
                        if self._values_equal(el, item):
                            return 1.0
                    return 0.0
                if isinstance(col, dict):
                    return 1.0 if self._to_str(item) in col else 0.0
                if isinstance(col, str):
                    return 1.0 if self._to_str(item) in col else 0.0
                raise EQLangError("contains() first argument must be a list, map, or string", line)
            if name == "push":
                if len(args) != 2:
                    raise EQLangError("push() requires 2 arguments: push(list, item)", line)
                lst = args[0]
                if not isinstance(lst, list):
                    raise EQLangError("push() first argument must be a list", line)
                return lst + [args[1]]
            if name == "pop":
                if len(args) != 1:
                    raise EQLangError("pop() requires 1 argument: pop(list)", line)
                lst = args[0]
                if not isinstance(lst, list):
                    raise EQLangError("pop() argument must be a list", line)
                if not lst:
                    raise EQLangError("pop() on empty list", line)
                return lst[:-1]
            if name == "range":
                if len(args) < 2 or len(args) > 3:
                    raise EQLangError("range() requires 2 or 3 arguments: range(start, end[, step])", line)
                start = int(float(args[0]))
                end = int(float(args[1]))
                step = int(float(args[2])) if len(args) == 3 else 1
                if step == 0:
                    raise EQLangError("range() step cannot be zero", line)
                result = list(range(start, end, step))
                if len(result) > 10000:
                    raise EQLangError(f"range() safety cap: {len(result)} elements (max 10000)", line)
                return [float(x) for x in result]
            if name == "sort":
                if len(args) != 1:
                    raise EQLangError("sort() requires 1 argument: sort(list)", line)
                lst = args[0]
                if not isinstance(lst, list):
                    raise EQLangError("sort() argument must be a list", line)
                try:
                    return sorted(lst, key=lambda x: (0, float(x)) if isinstance(x, (int, float)) else (1, self._to_str(x)))
                except (TypeError, ValueError):
                    return sorted(lst, key=lambda x: self._to_str(x))
            if name == "reverse":
                if len(args) != 1:
                    raise EQLangError("reverse() requires 1 argument: reverse(list)", line)
                lst = args[0]
                if not isinstance(lst, list):
                    raise EQLangError("reverse() argument must be a list", line)
                return lst[::-1]
            if name == "index_of":
                if len(args) != 2:
                    raise EQLangError("index_of() requires 2 arguments: index_of(list, item)", line)
                lst = args[0]
                if not isinstance(lst, list):
                    raise EQLangError("index_of() first argument must be a list", line)
                item = args[1]
                for i, el in enumerate(lst):
                    if self._values_equal(el, item):
                        return float(i)
                return -1.0
            if name == "flatten":
                if len(args) != 1:
                    raise EQLangError("flatten() requires 1 argument: flatten(list)", line)
                lst = args[0]
                if not isinstance(lst, list):
                    raise EQLangError("flatten() argument must be a list", line)
                result = []
                for item in lst:
                    if isinstance(item, list):
                        result.extend(item)
                    else:
                        result.append(item)
                return result

            # ── Map builtins (v0.5.0) ─────────────────────────────────────
            if name == "keys":
                if len(args) != 1:
                    raise EQLangError("keys() requires 1 argument: keys(map)", line)
                m = args[0]
                if not isinstance(m, dict):
                    raise EQLangError("keys() argument must be a map", line)
                return list(m.keys())
            if name == "values":
                if len(args) != 1:
                    raise EQLangError("values() requires 1 argument: values(map)", line)
                m = args[0]
                if not isinstance(m, dict):
                    raise EQLangError("values() argument must be a map", line)
                return list(m.values())
            if name == "has_key":
                if len(args) != 2:
                    raise EQLangError("has_key() requires 2 arguments: has_key(map, key)", line)
                m = args[0]
                if not isinstance(m, dict):
                    raise EQLangError("has_key() first argument must be a map", line)
                return 1.0 if self._to_str(args[1]) in m else 0.0

            # ── Type builtins (v0.5.0) ────────────────────────────────────
            if name == "type":
                if len(args) != 1:
                    raise EQLangError("type() requires 1 argument", line)
                a = args[0]
                if a is None:
                    return "nothing"
                if isinstance(a, float):
                    return "number"
                if isinstance(a, str):
                    return "string"
                if isinstance(a, list):
                    return "list"
                if isinstance(a, dict):
                    return "map"
                return "unknown"
            if name == "is_nothing":
                if len(args) != 1:
                    raise EQLangError("is_nothing() requires 1 argument", line)
                return 1.0 if args[0] is None else 0.0
            if name == "is_number":
                if len(args) != 1:
                    raise EQLangError("is_number() requires 1 argument", line)
                return 1.0 if isinstance(args[0], (int, float)) and args[0] is not None else 0.0
            if name == "is_string":
                if len(args) != 1:
                    raise EQLangError("is_string() requires 1 argument", line)
                return 1.0 if isinstance(args[0], str) else 0.0
            if name == "is_list":
                if len(args) != 1:
                    raise EQLangError("is_list() requires 1 argument", line)
                return 1.0 if isinstance(args[0], list) else 0.0
            if name == "is_map":
                if len(args) != 1:
                    raise EQLangError("is_map() requires 1 argument", line)
                return 1.0 if isinstance(args[0], dict) else 0.0
            if name == "to_number":
                if len(args) != 1:
                    raise EQLangError("to_number() requires 1 argument", line)
                a = args[0]
                if a is None:
                    raise EQLangError("Cannot convert nothing to number", line)
                try:
                    return float(a)
                except (ValueError, TypeError):
                    raise EQLangError(f"Cannot convert {self._to_str(a)!r} to number", line)

            # ── Mutation builtins (v0.5.0) — return new collection ─────────
            if name == "set_at":
                if len(args) != 3:
                    raise EQLangError("set_at() requires 3 arguments: set_at(collection, key_or_index, value)", line)
                col = args[0]
                key = args[1]
                val = args[2]
                if isinstance(col, list):
                    idx = int(float(key))
                    if idx < 0 or idx >= len(col):
                        raise EQLangError(f"set_at() list index out of range: {idx}", line)
                    new_list = list(col)
                    new_list[idx] = val
                    return new_list
                if isinstance(col, dict):
                    new_map = dict(col)
                    new_map[self._to_str(key)] = val
                    return new_map
                raise EQLangError("set_at() first argument must be a list or map", line)

        except (TypeError, ValueError) as e:
            raise EQLangError(f"Built-in {name}() error: {e}", line)
        raise EQLangError(f"Unknown built-in function: {name!r}", line)

    # ══════════════════════════════════════════════════════════════════════
    # EQ CONDITION EVALUATION
    # ══════════════════════════════════════════════════════════════════════

    def _eval_eq_condition(self, cond: Any) -> bool:
        if isinstance(cond, NotCondition):
            return not self._eval_eq_condition(cond.condition)

        if isinstance(cond, CompoundEQCondition):
            left = self._eval_eq_condition(cond.left)
            right = self._eval_eq_condition(cond.right)
            if cond.op == "and":
                return left and right
            if cond.op == "or":
                return left or right
            raise EQLangError(f"Unknown compound operator: {cond.op!r}")

        if isinstance(cond, EQCondition):
            current = self.eq_state.get(cond.metric, 0.0)
            threshold_val = self._evaluate(cond.threshold)
            threshold = 0.0 if threshold_val is None else float(threshold_val)
            op = cond.comparator
            if op == ">":  return current > threshold
            if op == "<":  return current < threshold
            if op == ">=": return current >= threshold
            if op == "<=": return current <= threshold
            raise EQLangError(f"Unknown comparator: {op!r}", cond.line)

        raise EQLangError(f"Cannot evaluate condition node: {type(cond).__name__}")

    # ══════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ══════════════════════════════════════════════════════════════════════

    def _to_str(self, value: Any) -> str:
        if value is None:
            return "nothing"
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "[" + ", ".join(self._to_str(x) for x in value) + "]"
        if isinstance(value, dict):
            pairs = ", ".join(f"{k}: {self._to_str(v)}" for k, v in value.items())
            return "{" + pairs + "}"
        return str(value)

    def _fmt(self, value: Any) -> str:
        """Format a value for trace output."""
        if value is None:
            return "nothing"
        if isinstance(value, float):
            return f"{value:.4f}"
        if isinstance(value, list):
            return "[" + ", ".join(self._fmt(x) for x in value) + "]"
        if isinstance(value, dict):
            pairs = ", ".join(f"{k!r}: {self._fmt(v)}" for k, v in value.items())
            return "{" + pairs + "}"
        return repr(value)

    def _fmt_condition(self, cond: Any) -> str:
        """Format a condition for trace output."""
        if isinstance(cond, NotCondition):
            return f"not {self._fmt_condition(cond.condition)}"
        if isinstance(cond, EQCondition):
            threshold = self._evaluate(cond.threshold)
            return f"{cond.metric} {cond.comparator} {self._fmt(threshold)}"
        if isinstance(cond, CompoundEQCondition):
            return f"({self._fmt_condition(cond.left)} {cond.op} {self._fmt_condition(cond.right)})"
        return repr(cond)

    def _values_equal(self, a: Any, b: Any) -> bool:
        """Compare two EQLang values for equality."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b)) < 1e-9
        return a == b

    def _trace(self, msg: str) -> None:
        if self.verbose:
            print(msg)
        logger.debug(msg)

    def get_eq_state(self) -> dict:
        """Return current EQ state plus conflict/tension accumulation and session info."""
        return {
            **dict(self.eq_state),
            "conflict_accum": self.runtime.get_conflict_accumulation(),
            "tension_accum":  self.runtime.get_tension_accumulation(),
            "session_id": self.session_id,
            "emit_count": len(self.emit_log),
            "echo_count": len(self.echo_log),
            "anchors": dict(self.anchors),
            "thresholds": dict(self.thresholds),
        }


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPER
# ══════════════════════════════════════════════════════════════════════════════

class _ValueNode:
    """
    Lightweight shim used by WeaveStmt to pass a concrete value
    through the expression evaluator without re-parsing.
    """
    def __init__(self, value: Any, line: int):
        self.value = value
        self.line = line
