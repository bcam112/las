"""
EQLang v0.5.0 — Full Test Suite.

Tests every language construct using MockRuntime for deterministic results.
Run with: pytest eqlang/tests/test_eqlang.py -v

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

import pytest
from ..tokens import TokenType
from ..lexer import Lexer, LexerError
from ..parser import Parser, ParseError
from ..interpreter import EQLangInterpreter, EQLangError
from ..runtime.mock_runtime import MockRuntime


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(source: str, **mock_kwargs) -> tuple:
    """Parse and run EQLang source. Returns (results, interpreter)."""
    runtime = MockRuntime(**mock_kwargs)
    tokens = Lexer(source).scan_tokens()
    program = Parser(tokens).parse()
    interp = EQLangInterpreter(runtime=runtime, verbose=False)
    results = interp.interpret(program)
    return results, interp

def parse(source: str):
    tokens = Lexer(source).scan_tokens()
    return Parser(tokens).parse()

def lex(source: str):
    return Lexer(source).scan_tokens()


# ══════════════════════════════════════════════════════════════════════════════
# LEXER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestLexer:
    def test_basic_keywords(self):
        tokens = lex('session "x" state resonate end')
        types = [t.type.name for t in tokens if t.type.name != "EOF"]
        assert "SESSION" in types
        assert "STATE" in types
        assert "RESONATE" in types
        assert "END" in types

    def test_new_keywords_v2(self):
        tokens = lex("threshold recall anchor drift witness weave journal interrupt")
        types = {t.type.name for t in tokens}
        assert "THRESHOLD" in types
        assert "RECALL" in types
        assert "ANCHOR" in types
        assert "DRIFT" in types
        assert "WITNESS" in types
        assert "WEAVE" in types
        assert "JOURNAL" in types
        assert "INTERRUPT" in types

    def test_compound_condition_keywords(self):
        tokens = lex("and or")
        types = {t.type.name for t in tokens}
        assert "AND" in types
        assert "OR" in types

    def test_tension_release_keywords(self):
        tokens = lex("tension release")
        types = {t.type.name for t in tokens}
        assert "TENSION" in types
        assert "RELEASE" in types

    def test_inspect_keyword(self):
        tokens = lex("inspect")
        assert tokens[0].type.name == "INSPECT"

    def test_extended_emotional_states(self):
        source = "grounded hollow radiant fractured overwhelmed curious present expanded grief numb"
        tokens = lex(source)
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "GROUNDED" in types
        assert "HOLLOW" in types
        assert "RADIANT" in types
        assert "FRACTURED" in types
        assert "OVERWHELMED" in types
        assert "CURIOUS" in types
        assert "PRESENT" in types
        assert "EXPANDED" in types
        assert "GRIEF" in types
        assert "NUMB" in types

    def test_unicode_arrow(self):
        tokens = lex("gate harm → resolve \"abstain\"")
        types = {t.type.name for t in tokens}
        assert "ARROW" in types

    def test_ascii_arrow(self):
        tokens = lex("gate harm -> resolve \"abstain\"")
        types = {t.type.name for t in tokens}
        assert "ARROW" in types

    def test_number_literals(self):
        tokens = lex("0.75 1.0 0 42")
        nums = [t for t in tokens if t.type.name == "NUMBER"]
        assert len(nums) == 4
        assert nums[0].literal == 0.75

    def test_string_literal_escape(self):
        tokens = lex('"hello\\nworld"')
        strings = [t for t in tokens if t.type.name == "STRING"]
        assert strings[0].literal == "hello\nworld"

    def test_comment_ignored(self):
        tokens = lex("# this is a comment\nstate")
        types = [t.type.name for t in tokens if t.type.name != "EOF"]
        assert types == ["STATE"]

    def test_unknown_character_raises(self):
        with pytest.raises(LexerError):
            lex("@invalid")


# ══════════════════════════════════════════════════════════════════════════════
# PARSER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestParser:
    def test_session_decl(self):
        prog = parse('session "my-session"')
        from ..ast_nodes import SessionDecl
        assert isinstance(prog.declarations[0], SessionDecl)
        assert prog.declarations[0].name == "my-session"

    def test_state_decl(self):
        prog = parse('state x = "hello"')
        from ..ast_nodes import StateDecl
        assert isinstance(prog.declarations[0], StateDecl)
        assert prog.declarations[0].name == "x"

    def test_threshold_decl(self):
        prog = parse("threshold clarity = 0.75")
        from ..ast_nodes import ThresholdDecl
        node = prog.declarations[0]
        assert isinstance(node, ThresholdDecl)
        assert node.name == "clarity"
        assert node.value == 0.75

    def test_resonate_block_requires_grounding(self):
        with pytest.raises(ParseError, match="EQ invariant"):
            parse("""
            resonate entry
              echo "no measure here"
            end
            """)

    def test_dialogue_requires_end_resolve(self):
        with pytest.raises(ParseError):
            parse("""
            dialogue greet(x) resonate
              measure resonance x
              accum conflict
              emit x aligned
            end
            """)  # Missing 'resolve'

    def test_when_condition_must_be_eq(self):
        with pytest.raises(ParseError, match="No cold booleans"):
            parse("""
            resonate test
              measure resonance "x"
              when x > 0.5
                echo "bad"
              end
            end
            """)

    def test_compound_condition_and(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          when resonance > 0.5 and load < 0.8
            echo "compound"
          end
        end
        """)
        from ..ast_nodes import CompoundEQCondition
        resonate = prog.declarations[0]
        when_stmt = resonate.body[2]
        assert isinstance(when_stmt.condition, CompoundEQCondition)
        assert when_stmt.condition.op == "and"

    def test_compound_condition_or(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          when conflict > 5.0 or self > 0.7
            echo "or condition"
          end
        end
        """)
        from ..ast_nodes import CompoundEQCondition
        when_stmt = prog.declarations[0].body[2]
        assert isinstance(when_stmt.condition, CompoundEQCondition)
        assert when_stmt.condition.op == "or"

    def test_inspect_expression(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          emit inspect resonance aligned
        end
        """)
        from ..ast_nodes import InspectExpr, EmitStmt
        emit_stmt = prog.declarations[0].body[2]
        assert isinstance(emit_stmt, EmitStmt)
        assert isinstance(emit_stmt.expr, InspectExpr)
        assert emit_stmt.expr.metric == "resonance"

    def test_recall_stmt(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          recall "healing" from EMOTIONAL into memory
          accum conflict
        end
        """)
        from ..ast_nodes import RecallStmt
        recall = prog.declarations[0].body[1]
        assert isinstance(recall, RecallStmt)
        assert recall.region == "EMOTIONAL"
        assert recall.into_name == "memory"

    def test_recall_stmt_without_into(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          recall "ethics" from FACTUAL
          accum conflict
        end
        """)
        from ..ast_nodes import RecallStmt
        recall = prog.declarations[0].body[1]
        assert isinstance(recall, RecallStmt)
        assert recall.into_name is None

    def test_anchor_and_drift(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          anchor resonance
          drift resonance into change
          accum conflict
        end
        """)
        from ..ast_nodes import AnchorStmt, DriftStmt
        assert isinstance(prog.declarations[0].body[1], AnchorStmt)
        drift = prog.declarations[0].body[2]
        assert isinstance(drift, DriftStmt)
        assert drift.into_name == "change"

    def test_accum_tension(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum tension
          accum conflict
        end
        """)
        from ..ast_nodes import AccumTensionStmt
        assert isinstance(prog.declarations[0].body[1], AccumTensionStmt)

    def test_release_tension(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          release tension "integrate"
        end
        """)
        from ..ast_nodes import ReleaseTensionStmt
        assert isinstance(prog.declarations[0].body[2], ReleaseTensionStmt)

    def test_witness_stmt(self):
        prog = parse("""
        dialogue reflect(x) resonate
          measure resonance x
          accum conflict
          emit x aligned
        end resolve
        resonate test
          measure resonance "q"
          accum conflict
          witness reflect("input") into preview
        end
        """)
        from ..ast_nodes import WitnessStmt
        witness = prog.declarations[1].body[2]
        assert isinstance(witness, WitnessStmt)
        assert witness.dialogue_name == "reflect"
        assert witness.into_name == "preview"

    def test_weave_stmt(self):
        prog = parse("""
        dialogue refine(x) resonate
          measure resonance x
          accum conflict
          emit x aligned
        end resolve
        resonate test
          measure resonance "data"
          accum conflict
          weave "data" → refine → emit aligned
        end
        """)
        from ..ast_nodes import WeaveStmt
        weave = prog.declarations[1].body[2]
        assert isinstance(weave, WeaveStmt)
        assert weave.stages == ["refine"]
        assert weave.emit_final is True
        assert weave.emit_aligned is True

    def test_journal_block(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          journal "arc"
            echo "noting the arc"
          end
        end
        """)
        from ..ast_nodes import JournalBlock
        journal = prog.declarations[0].body[2]
        assert isinstance(journal, JournalBlock)
        assert journal.label == "arc"

    def test_interrupt_stmt(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          cycle while resonance > 0.5 resonate
            measure resonance "y"
            accum conflict
            interrupt when conflict > 8.0
          end
        end
        """)
        from ..ast_nodes import InterruptStmt
        cycle = prog.declarations[0].body[2]
        interrupt = cycle.body[2]
        assert isinstance(interrupt, InterruptStmt)

    def test_include_decl(self):
        prog = parse('include "utils.eql"')
        from ..ast_nodes import IncludeDecl
        assert isinstance(prog.declarations[0], IncludeDecl)
        assert prog.declarations[0].path == "utils.eql"

    def test_echo_accepts_expression(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          echo inspect resonance
        end
        """)
        from ..ast_nodes import EchoStmt, InspectExpr
        echo = prog.declarations[0].body[2]
        assert isinstance(echo, EchoStmt)
        assert isinstance(echo.expr, InspectExpr)

    def test_emotional_state_literal_grounded(self):
        prog = parse('state mood = grounded')
        from ..ast_nodes import StateLit
        assert isinstance(prog.declarations[0].value, StateLit)
        assert prog.declarations[0].value.value == "grounded"


# ══════════════════════════════════════════════════════════════════════════════
# INTERPRETER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestInterpreter:
    def test_session_sets_id(self):
        _, interp = run('session "test-session"')
        assert interp.session_id == "test-session"

    def test_state_declaration(self):
        _, interp = run('state greeting = "hello"')
        assert interp.environment["greeting"] == "hello"

    def test_threshold_declaration(self):
        _, interp = run("threshold clarity = 0.75")
        assert interp.thresholds["clarity"] == 0.75
        assert interp.environment["clarity"] == 0.75

    def test_emit_returns_value(self):
        results, _ = run("""
        resonate test
          measure resonance "hello"
          accum conflict
          emit "hello world" aligned
        end
        """)
        assert results == ["hello world"]

    def test_when_condition_true_branch(self):
        results, _ = run("""
        resonate test
          measure resonance "input"
          accum conflict
          when resonance > 0.5
            emit "high resonance" aligned
          end
        end
        """, fixed_resonance=0.9)
        assert results == ["high resonance"]

    def test_when_condition_false_branch(self):
        results, _ = run("""
        resonate test
          measure resonance "input"
          accum conflict
          when resonance > 0.9
            emit "high"
          otherwise
            emit "low"
          end
        end
        """, fixed_resonance=0.3)
        assert results == ["low"]

    def test_compound_and_condition(self):
        results, _ = run("""
        resonate test
          measure resonance "x"
          measure load "x"
          accum conflict
          when resonance > 0.5 and load < 0.8
            emit "both pass"
          end
        end
        """, fixed_resonance=0.9, fixed_load=0.3)
        assert results == ["both pass"]

    def test_compound_or_condition_first_passes(self):
        results, _ = run("""
        resonate test
          measure resonance "x"
          accum conflict
          when resonance > 0.9 or resonance > 0.5
            emit "or passes"
          end
        end
        """, fixed_resonance=0.8)
        assert results == ["or passes"]

    def test_compound_and_condition_fails(self):
        results, _ = run("""
        resonate test
          measure resonance "x"
          measure load "x"
          accum conflict
          when resonance > 0.9 and load < 0.2
            emit "both pass"
          otherwise
            emit "one failed"
          end
        end
        """, fixed_resonance=0.8, fixed_load=0.5)
        assert results == ["one failed"]

    def test_threshold_in_condition(self):
        results, _ = run("""
        threshold presence = 0.7
        resonate test
          measure resonance "input"
          accum conflict
          when resonance > presence
            emit "above threshold"
          end
        end
        """, fixed_resonance=0.9)
        assert results == ["above threshold"]

    def test_inspect_expression(self):
        results, _ = run("""
        resonate test
          measure resonance "input"
          accum conflict
          emit inspect resonance aligned
        end
        """, fixed_resonance=0.8)
        assert results == [0.8]

    def test_echo_with_expression(self):
        _, interp = run("""
        resonate test
          measure resonance "input"
          accum conflict
          echo inspect resonance
        end
        """, fixed_resonance=0.75)
        assert "0.75" in interp.echo_log[0]

    def test_echo_with_string(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          echo "introspection"
        end
        """)
        assert "introspection" in interp.echo_log

    def test_anchor_and_drift(self):
        _, interp = run("""
        resonate test
          measure resonance "baseline"
          anchor resonance
          measure resonance "new input"
          drift resonance into change
          accum conflict
        end
        """, fixed_resonance=0.8)
        # Both measures return 0.8 (mock), so drift = 0.0
        assert "change" in interp.environment
        assert interp.environment["change"] == 0.0

    def test_accum_tension(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum tension
          accum tension
          accum conflict
        end
        """)
        assert interp.eq_state["tension"] == 2.0

    def test_release_tension(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum tension
          accum tension
          accum tension
          accum conflict
          release tension "integrate"
        end
        """)
        assert interp.eq_state["tension"] == 0.0
        assert "_tension_released" in interp.environment

    def test_learn_and_recall(self):
        results, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          learn "healing through grief" significance 0.9 region EMOTIONAL
          recall "healing" from EMOTIONAL into memory
          emit memory aligned
        end
        """)
        # MockRuntime returns the stored pattern
        assert results[0] == "healing through grief"

    def test_recall_into_default(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          recall "query" from FACTUAL
        end
        """)
        assert "_recall" in interp.environment

    def test_dialogue_call(self):
        results, _ = run("""
        dialogue greet(name) resonate
          measure resonance name
          accum conflict
          emit name aligned
        end resolve

        resonate main
          measure resonance "world"
          accum conflict
          emit greet("world") aligned
        end
        """)
        assert "world" in results

    def test_witness_rolls_back_state(self):
        _, interp = run("""
        dialogue check(x) resonate
          measure resonance x
          accum conflict
          emit x aligned
        end resolve

        resonate main
          measure resonance "input"
          accum conflict
          witness check("input") into preview
        end
        """)
        # witness should not add to emit_log
        assert len(interp.emit_log) == 0
        # but preview should be set
        assert interp.environment.get("preview") == "input"

    def test_weave_pipeline(self):
        results, _ = run("""
        dialogue capitalize(x) resonate
          measure resonance x
          accum conflict
          emit x aligned
        end resolve

        resonate main
          measure resonance "data"
          accum conflict
          weave "data" → capitalize → emit aligned
        end
        """)
        assert results == ["data"]

    def test_journal_block(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          journal "session-arc"
            echo "tracking emotional arc"
          end
        end
        """)
        assert "tracking emotional arc" in interp.echo_log

    def test_interrupt_exits_cycle(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          cycle while resonance > 0.5 resonate
            measure resonance "loop"
            accum conflict
            interrupt when conflict > 3.0
          end
        end
        """, fixed_resonance=0.9)
        # Should have interrupted before overload
        assert interp.eq_state["conflict"] <= 10.0

    def test_arithmetic_expressions(self):
        results, _ = run("""
        state base = 0.5
        resonate test
          measure resonance "x"
          accum conflict
          emit base + 0.3 aligned
        end
        """)
        assert abs(results[0] - 0.8) < 0.001

    def test_string_concatenation(self):
        results, _ = run("""
        state prefix = "Hello"
        resonate test
          measure resonance prefix
          accum conflict
          emit prefix + " World" aligned
        end
        """)
        assert results == ["Hello World"]

    def test_bind_rebind(self):
        _, interp = run("""
        state x = "initial"
        resonate test
          measure resonance x
          accum conflict
          bind x to "updated"
        end
        """)
        assert interp.environment["x"] == "updated"

    def test_gate_pass(self):
        _, interp = run("""
        resonate test
          measure resonance "safe content"
          accum conflict
          gate manipulation → resolve "abstain"
        end
        """, ethics_pass=True)
        assert "_gate_resolved" not in interp.environment

    def test_gate_block_and_resolve(self):
        _, interp = run("""
        resonate test
          measure resonance "harmful content"
          accum conflict
          gate manipulation → resolve "abstain"
        end
        """, ethics_pass=False)
        assert "_gate_resolved" in interp.environment

    def test_struggle_otherwise_branch(self):
        results, _ = run("""
        resonate test
          measure resonance "input"
          accum conflict
          when resonance > 0.9
            emit "high"
          otherwise struggle
            emit "low" aligned
          end
        end
        """, fixed_resonance=0.3)
        assert results == ["low"]

    def test_emotional_state_literal(self):
        _, interp = run("""
        state mood = grounded
        resonate test
          measure resonance mood
          accum conflict
        end
        """)
        assert interp.environment["mood"] == "grounded"

    def test_extended_state_literal_numb(self):
        _, interp = run("""
        state feeling = numb
        resonate test
          measure resonance feeling
          accum conflict
        end
        """)
        assert interp.environment["feeling"] == "numb"

    def test_conflict_overload_raises(self):
        with pytest.raises(EQLangError, match="[Cc]onflict"):
            run("""
            resonate test
              measure resonance "x"
              accum conflict
              accum conflict
              accum conflict
              accum conflict
              accum conflict
              accum conflict
              accum conflict
              accum conflict
              accum conflict
              accum conflict
              accum conflict
            end
            """)

    def test_undefined_variable_raises(self):
        with pytest.raises(EQLangError, match="Undefined variable"):
            run("""
            resonate test
              measure resonance undefined_var
              accum conflict
            end
            """)

    def test_undefined_dialogue_raises(self):
        with pytest.raises(EQLangError, match="Undefined dialogue"):
            run("""
            resonate test
              measure resonance "x"
              accum conflict
              emit nonexistent("x") aligned
            end
            """)

    def test_cycle_safety_ceiling(self):
        with pytest.raises(EQLangError, match="safety ceiling"):
            run("""
            resonate test
              measure resonance "x"
              accum conflict
              cycle while resonance > 0.5 resonate
                measure resonance "inner"
              end
            end
            """, fixed_resonance=0.9)


# ══════════════════════════════════════════════════════════════════════════════
# RUNTIME TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestMockRuntime:
    def test_fixed_values(self):
        r = MockRuntime(fixed_resonance=0.9, fixed_load=0.1)
        assert r.measure_resonance("x", {}) == 0.9
        assert r.measure_load("x", {}) == 0.1

    def test_conflict_overload(self):
        r = MockRuntime()
        from ..runtime.base import EQRuntimeError
        for _ in range(10):
            r.accumulate_conflict(1.0)
        with pytest.raises(EQRuntimeError):
            r.accumulate_conflict(1.0)

    def test_set_conflict_for_witness(self):
        r = MockRuntime()
        r.accumulate_conflict(5.0)
        r.set_conflict(2.0)
        assert r.get_conflict_accumulation() == 2.0

    def test_tension_accumulation(self):
        r = MockRuntime()
        r.accumulate_tension(1.0)
        r.accumulate_tension(2.0)
        assert r.get_tension_accumulation() == 3.0

    def test_tension_release(self):
        r = MockRuntime()
        r.accumulate_tension(5.0)
        result = r.release_tension("integrate")
        assert r.get_tension_accumulation() == 0.0
        assert "5.00" in result

    def test_set_tension_for_witness(self):
        r = MockRuntime()
        r.accumulate_tension(7.0)
        r.set_tension(3.0)
        assert r.get_tension_accumulation() == 3.0

    def test_learn_and_recall(self):
        r = MockRuntime()
        r.learn_pattern("the grief dissolves", 0.9, "EMOTIONAL")
        result = r.recall_pattern("grief", "EMOTIONAL")
        assert result == "the grief dissolves"

    def test_recall_default_when_no_match(self):
        r = MockRuntime(recall_response="[default]")
        result = r.recall_pattern("unknown query", "FACTUAL")
        assert result == "[default]"

    def test_ethics_gate_pass(self):
        r = MockRuntime(ethics_pass=True)
        passed, reason = r.check_ethics_gate("manipulation", "content")
        assert passed is True

    def test_ethics_gate_block(self):
        r = MockRuntime(ethics_pass=False)
        passed, reason = r.check_ethics_gate("manipulation", "content")
        assert passed is False
        assert "manipulation" in reason

    def test_resolve_conflict_resets(self):
        r = MockRuntime()
        r.accumulate_conflict(5.0)
        r.resolve_conflict("abstain", "content")
        assert r.get_conflict_accumulation() == 0.0

    def test_resolve_methods(self):
        r = MockRuntime()
        assert "[mock abstained]" == r.resolve_conflict("abstain", "x")
        r._conflict_accum = 0  # reset
        result = r.resolve_conflict("transcend", "x")
        assert "transcended" in result


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    def test_full_session_flow(self):
        source = """
        session "integration-test"
        threshold clarity = 0.6
        threshold overload = 7.0
        state query = "what is the nature of understanding?"

        dialogue reflect(input) resonate
          measure resonance input
          measure self input
          accum conflict
          when resonance > clarity and self > 0.5
            learn "deep question encountered" significance 0.85 region EPISODIC
            emit input aligned
          otherwise
            resolve "rewrite"
          end
        end resolve

        resonate inquiry
          measure resonance query
          accum conflict
          anchor resonance
          emit reflect(query) aligned
        end
        """
        results, interp = run(source, fixed_resonance=0.8, fixed_self=0.7)
        assert interp.session_id == "integration-test"
        assert len(results) > 0
        assert interp.thresholds["clarity"] == 0.6
        assert "resonance" in interp.anchors

    def test_weave_multi_stage(self):
        source = """
        session "pipeline-test"

        dialogue stage_one(x) resonate
          measure resonance x
          accum conflict
          emit x aligned
        end resolve

        dialogue stage_two(x) resonate
          measure coherence x
          accum conflict
          emit x aligned
        end resolve

        resonate main
          measure resonance "seed"
          accum conflict
          weave "seed" → stage_one → stage_two → emit aligned
        end
        """
        results, _ = run(source)
        assert results == ["seed"]

    def test_witness_pure_observation(self):
        source = """
        session "witness-test"

        dialogue probe(x) resonate
          measure resonance x
          accum conflict
          emit "probed: " + x aligned
        end resolve

        resonate main
          measure resonance "data"
          accum conflict
          witness probe("data") into result
          # eq_state and emit_log should be clean after witness
        end
        """
        results, interp = run(source)
        assert len(interp.emit_log) == 0  # witness rolled back
        assert interp.environment.get("result") == "probed: data"

    def test_temporal_drift_tracking(self):
        source = """
        session "drift-test"
        state input = "initial content"

        resonate tracking
          measure resonance input
          anchor resonance
          measure resonance "evolved content"
          drift resonance into eq_change
          accum conflict
          echo inspect resonance
        end
        """
        _, interp = run(source, fixed_resonance=0.8)
        # Both measures return 0.8 from mock, so drift = 0.0
        assert "eq_change" in interp.environment
        assert interp.anchors.get("resonance") == 0.8

    def test_tension_buildup_and_release(self):
        source = """
        session "tension-test"

        resonate emotional_arc
          measure resonance "difficult content"
          accum conflict
          accum tension
          accum tension
          accum tension
          when tension > 2.0
            release tension "integrate"
            echo "tension released"
          end
        end
        """
        _, interp = run(source)
        assert interp.eq_state["tension"] == 0.0
        assert "tension released" in interp.echo_log

    def test_compound_conditions_chained(self):
        source = """
        session "compound-test"
        threshold safe = 0.5
        threshold critical = 8.0

        resonate assessment
          measure resonance "content"
          measure load "content"
          accum conflict
          when resonance > safe and load < 0.8 and conflict < critical
            emit "triple pass" aligned
          end
        end
        """
        results, _ = run(source, fixed_resonance=0.9, fixed_load=0.3)
        assert results == ["triple pass"]

    def test_recall_completes_min_loop(self):
        source = """
        session "memory-test"

        resonate store
          measure resonance "lesson"
          accum conflict
          learn "every conflict carries insight" significance 0.95 region EPISODIC
          learn "grief is love with nowhere to go" significance 0.98 region EMOTIONAL
        end

        resonate retrieve
          measure resonance "query"
          accum conflict
          recall "grief" from EMOTIONAL into wisdom
          emit wisdom aligned
        end
        """
        results, _ = run(source)
        assert "grief is love with nowhere to go" in results

    def test_ethics_gate_in_pipeline(self):
        source = """
        session "ethics-test"
        state content = "potentially harmful content"

        resonate check
          measure resonance content
          accum conflict
          gate manipulation → resolve "abstain"
          gate deception → resolve "rewrite"
          emit "cleared" aligned
        end
        """
        results, interp = run(source, ethics_pass=False)
        # Both gates fired, resolved via their methods
        assert "_gate_resolved" in interp.environment

    def test_version(self):
        from .. import __version__
        assert __version__ == "0.5.0"


# ══════════════════════════════════════════════════════════════════════════════
# V0.3.0 TESTS — Full Emotional Spectrum
# ══════════════════════════════════════════════════════════════════════════════

class TestV03Lexer:
    """Lexer tests for v0.3.0 new tokens."""

    def test_plutchik_primaries(self):
        source = "joy trust fear surprise sadness disgust anger anticipation"
        tokens = lex(source)
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "JOY" in types
        assert "TRUST" in types
        assert "FEAR" in types
        assert "SURPRISE" in types
        assert "SADNESS" in types
        assert "DISGUST" in types
        assert "ANGER" in types
        assert "ANTICIPATION" in types

    def test_plutchik_dyads(self):
        source = "love awe remorse contempt optimism submission disapproval aggressiveness"
        tokens = lex(source)
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "LOVE" in types
        assert "AWE" in types
        assert "REMORSE" in types
        assert "CONTEMPT" in types
        assert "OPTIMISM" in types
        assert "SUBMISSION" in types
        assert "DISAPPROVAL" in types
        assert "AGGRESSIVENESS" in types

    def test_nuanced_states(self):
        source = "shame guilt pride envy compassion gratitude longing wonder serenity apprehension"
        tokens = lex(source)
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "SHAME" in types
        assert "GUILT" in types
        assert "PRIDE" in types
        assert "ENVY" in types
        assert "COMPASSION" in types
        assert "GRATITUDE" in types
        assert "LONGING" in types
        assert "WONDER" in types
        assert "SERENITY" in types
        assert "APPREHENSION" in types

    def test_nuanced_states_extended(self):
        source = "despair elation tender vulnerable protective detached absorbed yearning acceptance pensiveness boredom annoyance"
        tokens = lex(source)
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "DESPAIR" in types
        assert "ELATION" in types
        assert "TENDER" in types
        assert "VULNERABLE" in types
        assert "PROTECTIVE" in types
        assert "DETACHED" in types
        assert "ABSORBED" in types
        assert "YEARNING" in types
        assert "ACCEPTANCE" in types
        assert "PENSIVENESS" in types
        assert "BOREDOM" in types
        assert "ANNOYANCE" in types

    def test_intensity_modifiers(self):
        source = "deep mild acute chronic"
        tokens = lex(source)
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "DEEP" in types
        assert "MILD" in types
        assert "ACUTE" in types
        assert "CHRONIC" in types

    def test_new_metrics(self):
        tokens = lex("valence intensity")
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "VALENCE" in types
        assert "INTENSITY" in types

    def test_new_keywords(self):
        tokens = lex("sense compose with as")
        types = {t.type.name for t in tokens if t.type.name != "EOF"}
        assert "SENSE" in types
        assert "COMPOSE" in types
        assert "WITH" in types
        assert "AS" in types


class TestV03Parser:
    """Parser tests for v0.3.0 new constructs."""

    def test_plutchik_state_literal(self):
        prog = parse("state mood = joy")
        from ..ast_nodes import StateLit
        assert isinstance(prog.declarations[0].value, StateLit)
        assert prog.declarations[0].value.value == "joy"

    def test_dyad_state_literal(self):
        prog = parse("state feeling = love")
        from ..ast_nodes import StateLit
        assert prog.declarations[0].value.value == "love"

    def test_nuanced_state_literal(self):
        prog = parse("state current = compassion")
        from ..ast_nodes import StateLit
        assert prog.declarations[0].value.value == "compassion"

    def test_intensity_state_deep_grief(self):
        prog = parse("state mood = deep grief")
        from ..ast_nodes import IntensityStateLit
        val = prog.declarations[0].value
        assert isinstance(val, IntensityStateLit)
        assert val.intensity == "deep"
        assert val.state == "grief"

    def test_intensity_state_mild_curious(self):
        prog = parse("state mood = mild curious")
        from ..ast_nodes import IntensityStateLit
        val = prog.declarations[0].value
        assert isinstance(val, IntensityStateLit)
        assert val.intensity == "mild"
        assert val.state == "curious"

    def test_intensity_state_acute_fear(self):
        prog = parse("state mood = acute fear")
        from ..ast_nodes import IntensityStateLit
        val = prog.declarations[0].value
        assert isinstance(val, IntensityStateLit)
        assert val.intensity == "acute"
        assert val.state == "fear"

    def test_intensity_state_chronic(self):
        prog = parse("state mood = chronic longing")
        from ..ast_nodes import IntensityStateLit
        val = prog.declarations[0].value
        assert isinstance(val, IntensityStateLit)
        assert val.intensity == "chronic"
        assert val.state == "longing"

    def test_compose_state(self):
        prog = parse("state mood = compose grief with curious")
        from ..ast_nodes import CompositeStateLit
        val = prog.declarations[0].value
        assert isinstance(val, CompositeStateLit)
        assert val.left == "grief"
        assert val.right == "curious"

    def test_compose_state_love_apprehension(self):
        prog = parse("state mood = compose love with apprehension")
        from ..ast_nodes import CompositeStateLit
        val = prog.declarations[0].value
        assert isinstance(val, CompositeStateLit)
        assert val.left == "love"
        assert val.right == "apprehension"

    def test_sense_stmt_plain(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          sense grief
        end
        """)
        from ..ast_nodes import SenseStmt
        sense = prog.declarations[0].body[2]
        assert isinstance(sense, SenseStmt)

    def test_sense_stmt_intensity(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          sense deep gratitude
        end
        """)
        from ..ast_nodes import SenseStmt, IntensityStateLit
        sense = prog.declarations[0].body[2]
        assert isinstance(sense, SenseStmt)
        assert isinstance(sense.state, IntensityStateLit)

    def test_sense_stmt_compose(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          sense compose grief with wonder
        end
        """)
        from ..ast_nodes import SenseStmt, CompositeStateLit
        sense = prog.declarations[0].body[2]
        assert isinstance(sense, SenseStmt)
        assert isinstance(sense.state, CompositeStateLit)

    def test_learn_with_emotion_type(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          learn "grief opens" significance 0.9 region EMOTIONAL as grief
        end
        """)
        from ..ast_nodes import LearnStmt
        learn = prog.declarations[0].body[2]
        assert isinstance(learn, LearnStmt)
        assert learn.emotion_type == "grief"

    def test_learn_with_intensity_emotion_type(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          learn "deep loss" significance 0.95 region EMOTIONAL as deep grief
        end
        """)
        from ..ast_nodes import LearnStmt
        learn = prog.declarations[0].body[2]
        assert isinstance(learn, LearnStmt)
        assert learn.emotion_type == "deep:grief"

    def test_learn_without_emotion_type(self):
        prog = parse("""
        resonate test
          measure resonance "x"
          accum conflict
          learn "factual pattern" significance 0.7 region FACTUAL
        end
        """)
        from ..ast_nodes import LearnStmt
        learn = prog.declarations[0].body[2]
        assert isinstance(learn, LearnStmt)
        assert learn.emotion_type is None

    def test_valence_in_condition(self):
        prog = parse("""
        resonate test
          measure valence "x"
          accum conflict
          when valence > 0.0
            echo "positive charge"
          end
        end
        """)
        from ..ast_nodes import EQCondition
        when_stmt = prog.declarations[0].body[2]
        assert isinstance(when_stmt.condition, EQCondition)
        assert when_stmt.condition.metric == "valence"

    def test_intensity_metric_in_condition(self):
        prog = parse("""
        resonate test
          measure intensity "x"
          accum conflict
          when intensity > 0.7
            echo "high activation"
          end
        end
        """)
        from ..ast_nodes import EQCondition
        when_stmt = prog.declarations[0].body[2]
        assert isinstance(when_stmt.condition, EQCondition)
        assert when_stmt.condition.metric == "intensity"

    def test_measure_valence(self):
        prog = parse("""
        resonate test
          measure valence "content"
          accum conflict
        end
        """)
        from ..ast_nodes import MeasureStmt
        measure = prog.declarations[0].body[0]
        assert isinstance(measure, MeasureStmt)
        assert measure.target == "valence"

    def test_measure_intensity(self):
        prog = parse("""
        resonate test
          measure intensity "content"
          accum conflict
        end
        """)
        from ..ast_nodes import MeasureStmt
        measure = prog.declarations[0].body[0]
        assert isinstance(measure, MeasureStmt)
        assert measure.target == "intensity"

    def test_inspect_valence(self):
        prog = parse("""
        resonate test
          measure valence "x"
          accum conflict
          emit inspect valence aligned
        end
        """)
        from ..ast_nodes import InspectExpr
        emit = prog.declarations[0].body[2]
        assert isinstance(emit.expr, InspectExpr)
        assert emit.expr.metric == "valence"


class TestV03Interpreter:
    """Interpreter tests for v0.3.0 new constructs."""

    def test_plutchik_state_evaluates(self):
        _, interp = run("""
        state mood = joy
        resonate test
          measure resonance mood
          accum conflict
        end
        """)
        assert interp.environment["mood"] == "joy"

    def test_intensity_state_evaluates(self):
        _, interp = run("""
        state mood = deep grief
        resonate test
          measure resonance mood
          accum conflict
        end
        """)
        assert interp.environment["mood"] == "deep:grief"

    def test_composite_state_evaluates(self):
        _, interp = run("""
        state mood = compose grief with curious
        resonate test
          measure resonance mood
          accum conflict
        end
        """)
        assert interp.environment["mood"] == "curious+grief"

    def test_sense_sets_environment(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          sense grief
        end
        """)
        assert interp.environment["_sense"] == "grief"

    def test_sense_intensity_sets_environment(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          sense deep gratitude
        end
        """)
        assert interp.environment["_sense"] == "deep:gratitude"

    def test_sense_composite_sets_environment(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          sense compose wonder with apprehension
        end
        """)
        assert interp.environment["_sense"] == "apprehension+wonder"

    def test_sense_logs_to_echo(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          sense grief
        end
        """)
        assert any("grief" in entry for entry in interp.echo_log)

    def test_measure_valence(self):
        _, interp = run("""
        resonate test
          measure valence "content"
          accum conflict
        end
        """, fixed_valence=0.8)
        assert interp.eq_state["valence"] == 0.8

    def test_measure_intensity(self):
        _, interp = run("""
        resonate test
          measure intensity "content"
          accum conflict
        end
        """, fixed_intensity=0.7)
        assert interp.eq_state["intensity"] == 0.7

    def test_valence_condition(self):
        results, _ = run("""
        resonate test
          measure valence "content"
          accum conflict
          when valence > 0.5
            emit "positive" aligned
          otherwise
            emit "negative"
          end
        end
        """, fixed_valence=0.9)
        assert results == ["positive"]

    def test_negative_valence_condition(self):
        results, _ = run("""
        resonate test
          measure valence "dark content"
          accum conflict
          when valence > 0.5
            emit "positive"
          otherwise
            emit "negative charge" aligned
          end
        end
        """, fixed_valence=-0.5)
        assert results == ["negative charge"]

    def test_intensity_condition(self):
        results, _ = run("""
        resonate test
          measure intensity "intense"
          accum conflict
          when intensity > 0.6
            emit "high activation" aligned
          end
        end
        """, fixed_intensity=0.9)
        assert results == ["high activation"]

    def test_inspect_valence(self):
        results, _ = run("""
        resonate test
          measure valence "content"
          accum conflict
          emit inspect valence aligned
        end
        """, fixed_valence=0.75)
        assert results == [0.75]

    def test_learn_with_emotion_type(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          learn "grief opens space" significance 0.9 region EMOTIONAL as grief
        end
        """)
        runtime = interp.runtime
        assert len(runtime.learn_calls) == 1
        assert runtime.learn_calls[0]["emotion_type"] == "grief"

    def test_learn_with_intensity_emotion_type(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          learn "deep loss persists" significance 0.95 region EMOTIONAL as deep grief
        end
        """)
        runtime = interp.runtime
        assert runtime.learn_calls[0]["emotion_type"] == "deep:grief"

    def test_learn_backward_compatible(self):
        _, interp = run("""
        resonate test
          measure resonance "x"
          accum conflict
          learn "factual knowledge" significance 0.8 region FACTUAL
        end
        """)
        runtime = interp.runtime
        assert runtime.learn_calls[0]["emotion_type"] is None

    def test_eq_state_has_valence_and_intensity(self):
        _, interp = run('session "v3-test"')
        assert "valence" in interp.eq_state
        assert "intensity" in interp.eq_state

    def test_full_v03_emotional_arc(self):
        source = """
        session "emotional-arc-v3"
        threshold clarity    = 0.6
        threshold charged    = 0.3
        threshold activated  = 0.5

        sense compose grief with curious

        resonate arc
          measure resonance "difficult experience"
          measure valence "difficult experience"
          measure intensity "difficult experience"
          accum conflict

          learn "grief opens space for inquiry" significance 0.9 region EMOTIONAL as deep grief
          learn "curious survives grief" significance 0.85 region EMOTIONAL as curious

          when resonance > clarity and valence < charged and intensity > activated
            accum tension
            release tension "integrate"
            emit "processed" aligned
          otherwise
            emit "continuing"
          end
        end
        """
        results, interp = run(source, fixed_resonance=0.8, fixed_valence=-0.1, fixed_intensity=0.7)
        assert interp.session_id == "emotional-arc-v3"
        assert interp.environment.get("_sense") == "curious+grief"
        assert len(results) > 0
        runtime = interp.runtime
        # Both learn calls should have emotion types
        typed_learns = [c for c in runtime.learn_calls if c["emotion_type"] is not None]
        assert len(typed_learns) == 2


class TestV03MockRuntime:
    """MockRuntime tests for v0.3.0 new methods."""

    def test_fixed_valence(self):
        r = MockRuntime(fixed_valence=0.8)
        assert r.measure_valence("x", {}) == 0.8

    def test_fixed_intensity(self):
        r = MockRuntime(fixed_intensity=0.6)
        assert r.measure_intensity("x", {}) == 0.6

    def test_negative_valence(self):
        r = MockRuntime(fixed_valence=-0.7)
        assert r.measure_valence("grief", {}) == -0.7

    def test_learn_with_emotion_type(self):
        r = MockRuntime()
        r.learn_pattern("loss softens", 0.9, "EMOTIONAL", emotion_type="grief")
        assert r.learn_calls[0]["emotion_type"] == "grief"

    def test_recall_with_emotion_type_filter(self):
        r = MockRuntime()
        r.learn_pattern("grief pattern", 0.9, "EMOTIONAL", emotion_type="grief")
        r.learn_pattern("joy pattern", 0.8, "EMOTIONAL", emotion_type="joy")
        # Recall with grief filter should return grief pattern
        result = r.recall_pattern("pattern", "EMOTIONAL", emotion_type="grief")
        assert result == "grief pattern"

    def test_recall_without_type_filter(self):
        r = MockRuntime()
        r.learn_pattern("most recent pattern", 0.7, "EMOTIONAL", emotion_type="joy")
        result = r.recall_pattern("pattern", "EMOTIONAL")
        assert result == "most recent pattern"

    def test_last_measures_has_valence_intensity(self):
        r = MockRuntime(fixed_valence=0.5, fixed_intensity=0.4)
        r.measure_valence("x", {})
        r.measure_intensity("x", {})
        measures = r.get_last_measures()
        assert "valence" in measures
        assert "intensity" in measures
        assert measures["valence"] == 0.5
        assert measures["intensity"] == 0.4

    def test_fixed_signals(self):
        r = MockRuntime(fixed_signals={"alpha": 0.9, "beta": 0.3})
        assert r.measure_signal("alpha", "x", {}) == 0.9
        assert r.measure_signal("beta", "x", {}) == 0.3

    def test_signal_default_fallback(self):
        r = MockRuntime()
        assert r.measure_signal("unknown_signal", "x", {}) == 0.5


# ══════════════════════════════════════════════════════════════════════════════
# PARENTHESIZED EXPRESSION TESTS (v0.3.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestParenthesizedExpressions:
    def test_simple_grouping(self):
        src = '''
        session "paren-test"
        state x = (1.0 + 2.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_grouping_changes_precedence(self):
        src = '''
        session "paren-test"
        state x = (1.0 + 2.0) * 3.0
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 9.0

    def test_nested_parentheses(self):
        src = '''
        session "paren-test"
        state x = ((1.0 + 2.0) * (4.0 - 1.0))
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 9.0

    def test_parens_in_state_formula(self):
        src = '''
        session "paren-test"
        state a = 0.8
        state b = 0.6
        state result = (a * 0.5) + (b * 0.5)
        emit result
        '''
        results, _ = run(src)
        assert abs(results[0] - 0.7) < 1e-9

    def test_parens_in_when_condition(self):
        src = '''
        session "paren-test"
        state x = (0.5 + 0.3)
        resonate
            measure resonance "test"
            when resonance > 0.5
                emit x
            end
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.8

    def test_deeply_nested_parens(self):
        src = '''
        session "paren-test"
        state x = (((2.0)))
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 2.0


# ══════════════════════════════════════════════════════════════════════════════
# BUILT-IN FUNCTION TESTS (v0.3.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestBuiltinFunctions:
    def test_min_two_args(self):
        src = '''
        session "builtin-test"
        state x = min(1.0, 0.5)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.5

    def test_min_three_args(self):
        src = '''
        session "builtin-test"
        state x = min(1.0, 0.5, 0.2)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.2

    def test_max_two_args(self):
        src = '''
        session "builtin-test"
        state x = max(0.3, 0.7)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.7

    def test_max_three_args(self):
        src = '''
        session "builtin-test"
        state x = max(0.1, 0.5, 0.9)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.9

    def test_clamp(self):
        src = '''
        session "builtin-test"
        state x = clamp(1.5, 0.0, 1.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_clamp_low(self):
        src = '''
        session "builtin-test"
        state x = clamp(-0.5, 0.0, 1.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_clamp_in_range(self):
        src = '''
        session "builtin-test"
        state x = clamp(0.5, 0.0, 1.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.5

    def test_abs_positive(self):
        src = '''
        session "builtin-test"
        state x = abs(0.7)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.7

    def test_abs_negative(self):
        src = '''
        session "builtin-test"
        state x = abs(0.0 - 0.7)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.7

    def test_round_no_decimals(self):
        src = '''
        session "builtin-test"
        state x = round(0.567)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_round_with_decimals(self):
        src = '''
        session "builtin-test"
        state x = round(0.567, 2)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.57

    def test_min_with_expression_args(self):
        src = '''
        session "builtin-test"
        state a = 0.8
        state b = 0.6
        state x = min(1.0, (a * 0.5) + (b * 0.3))
        emit x
        '''
        results, _ = run(src)
        assert abs(results[0] - 0.58) < 1e-9

    def test_builtins_in_formula(self):
        """Test a realistic metric formula using builtins."""
        src = '''
        session "formula-test"
        state res = 0.8
        state depth = 0.6
        state pl = 0.3
        state metric = min(1.0, (res * 0.5) + (depth * 0.25) + ((1.0 - pl) * 0.25))
        emit metric
        '''
        results, _ = run(src)
        expected = min(1.0, (0.8 * 0.5) + (0.6 * 0.25) + ((1.0 - 0.3) * 0.25))
        assert abs(results[0] - expected) < 1e-9

    def test_nested_builtins(self):
        src = '''
        session "builtin-test"
        state x = max(0.1, min(1.0, 0.5))
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.5

    def test_clamp_via_min_max(self):
        """Verify clamp(v, lo, hi) == max(lo, min(v, hi))."""
        src = '''
        session "builtin-test"
        state v = 1.5
        state a = clamp(v, 0.0, 1.0)
        state b = max(0.0, min(v, 1.0))
        emit a
        emit b
        '''
        results, _ = run(src)
        assert results[0] == results[1] == 1.0

    def test_min_error_one_arg(self):
        src = '''
        session "err-test"
        state x = min(1.0)
        '''
        with pytest.raises(EQLangError, match="min.*requires at least 2"):
            run(src)

    def test_clamp_error_wrong_args(self):
        src = '''
        session "err-test"
        state x = clamp(1.0, 0.0)
        '''
        with pytest.raises(EQLangError, match="clamp.*requires 3"):
            run(src)


# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL EXPRESSION TESTS (v0.3.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalExpression:
    def test_basic_signal(self):
        src = '''
        session "signal-test"
        state depth = signal "depth" "test content"
        emit depth
        '''
        results, _ = run(src, fixed_signals={"depth": 0.85})
        assert results[0] == 0.85

    def test_signal_default(self):
        src = '''
        session "signal-test"
        state unknown = signal "nonexistent" "test"
        emit unknown
        '''
        results, _ = run(src)
        assert results[0] == 0.5

    def test_signal_in_formula(self):
        src = '''
        session "signal-test"
        state raw_res = signal "alpha" "test"
        state raw_beta = signal "beta" "test"
        state metric = min(1.0, (raw_res * 0.6) + (raw_beta * 0.4))
        emit metric
        '''
        results, _ = run(src, fixed_signals={"alpha": 0.8, "beta": 0.6})
        expected = min(1.0, (0.8 * 0.6) + (0.6 * 0.4))
        assert abs(results[0] - expected) < 1e-9

    def test_multiple_signals(self):
        src = '''
        session "signal-test"
        state a = signal "alpha" "test"
        state b = signal "beta" "test"
        state c = signal "gamma" "test"
        emit a
        emit b
        emit c
        '''
        signals = {"alpha": 0.3, "beta": 0.7, "gamma": 0.9}
        results, _ = run(src, fixed_signals=signals)
        assert results[0] == 0.3
        assert results[1] == 0.7
        assert results[2] == 0.9

    def test_signal_with_variable_content(self):
        src = '''
        session "signal-test"
        state content = "user said something emotional"
        state depth = signal "depth" content
        emit depth
        '''
        results, _ = run(src, fixed_signals={"depth": 0.75})
        assert results[0] == 0.75

    def test_signal_used_in_state_and_emit(self):
        """Signal values can be used in state assignments and emitted."""
        src = '''
        session "signal-test"
        state depth = signal "depth" "test"
        state weighted = depth * 0.5
        resonate
            measure resonance "test"
            when resonance > 0.5
                emit weighted
            end
        end
        '''
        results, _ = run(src, fixed_signals={"depth": 0.8})
        assert abs(results[0] - 0.4) < 1e-9

    def test_full_metric_formula(self):
        """Test a complete metric formula built from raw signal components."""
        src = '''
        session "metric-formula-test"
        state content = "test input"
        state bs = signal "alpha" content
        state res = signal "beta" content
        state depth = signal "depth" content
        state coh = signal "gamma" content
        state load_raw = signal "processing_load" content

        # processing_intensity = min(1.0, (bs * 0.5) + (res * 0.25) + (depth * 0.25))
        state processing_intensity = min(1.0, (bs * 0.5) + (res * 0.25) + (depth * 0.25))

        # cognitive_flow = min(1.0, (coh * 0.6) + ((1.0 - min(1.0, load_raw * 1.2)) * 0.4))
        state cognitive_flow = min(1.0, (coh * 0.6) + ((1.0 - min(1.0, load_raw * 1.2)) * 0.4))

        emit processing_intensity
        emit cognitive_flow
        '''
        signals = {
            "alpha": 0.7,
            "beta": 0.8,
            "depth": 0.6,
            "gamma": 0.75,
            "processing_load": 0.3,
        }
        results, _ = run(src, fixed_signals=signals)

        expected_pi = min(1.0, (0.7 * 0.5) + (0.8 * 0.25) + (0.6 * 0.25))
        expected_cf = min(1.0, (0.75 * 0.6) + ((1.0 - min(1.0, 0.3 * 1.2)) * 0.4))
        assert abs(results[0] - expected_pi) < 1e-9
        assert abs(results[1] - expected_cf) < 1e-9


# ══════════════════════════════════════════════════════════════════════════════
# MODULO AND POWER OPERATOR TESTS (v0.3.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestModuloAndPower:
    def test_modulo_basic(self):
        src = '''
        session "mod-test"
        state x = 7.0 % 3.0
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_modulo_float(self):
        src = '''
        session "mod-test"
        state x = 5.5 % 2.0
        emit x
        '''
        results, _ = run(src)
        assert abs(results[0] - 1.5) < 1e-9

    def test_modulo_by_zero(self):
        src = '''
        session "mod-test"
        state x = 5.0 % 0.0
        '''
        with pytest.raises(EQLangError, match="Modulo by zero"):
            run(src)

    def test_power_basic(self):
        src = '''
        session "pow-test"
        state x = 2.0 ** 3.0
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 8.0

    def test_power_fractional(self):
        src = '''
        session "pow-test"
        state x = 4.0 ** 0.5
        emit x
        '''
        results, _ = run(src)
        assert abs(results[0] - 2.0) < 1e-9

    def test_power_right_associative(self):
        """2 ** 3 ** 2 should be 2 ** (3 ** 2) = 2 ** 9 = 512."""
        src = '''
        session "pow-test"
        state x = 2.0 ** 3.0 ** 2.0
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 512.0

    def test_power_precedence(self):
        """Power binds tighter than multiplication: 3 * 2 ** 2 = 3 * 4 = 12."""
        src = '''
        session "pow-test"
        state x = 3.0 * 2.0 ** 2.0
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 12.0

    def test_modulo_in_formula(self):
        src = '''
        session "mod-test"
        state cycle_pos = 17.0 % 5.0
        state normalized = cycle_pos / 5.0
        emit normalized
        '''
        results, _ = run(src)
        assert abs(results[0] - 0.4) < 1e-9


# ══════════════════════════════════════════════════════════════════════════════
# EXTENDED BUILTIN FUNCTION TESTS (v0.3.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestExtendedBuiltins:
    def test_sqrt(self):
        src = '''
        session "sqrt-test"
        state x = sqrt(9.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_sqrt_fractional(self):
        src = '''
        session "sqrt-test"
        state x = sqrt(2.0)
        emit x
        '''
        results, _ = run(src)
        import math
        assert abs(results[0] - math.sqrt(2.0)) < 1e-9

    def test_sqrt_negative_error(self):
        src = '''
        session "sqrt-test"
        state x = sqrt(0.0 - 1.0)
        '''
        with pytest.raises(EQLangError, match="sqrt.*negative"):
            run(src)

    def test_pow_builtin(self):
        src = '''
        session "pow-test"
        state x = pow(2.0, 10.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 1024.0

    def test_floor(self):
        src = '''
        session "floor-test"
        state x = floor(3.7)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_ceil(self):
        src = '''
        session "ceil-test"
        state x = ceil(3.2)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 4.0

    def test_log_natural(self):
        src = '''
        session "log-test"
        state x = log(1.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_log_with_base(self):
        src = '''
        session "log-test"
        state x = log(8.0, 2.0)
        emit x
        '''
        results, _ = run(src)
        assert abs(results[0] - 3.0) < 1e-9

    def test_log_negative_error(self):
        src = '''
        session "log-test"
        state x = log(0.0 - 1.0)
        '''
        with pytest.raises(EQLangError, match="log.*non-positive"):
            run(src)

    def test_len_string(self):
        src = '''
        session "len-test"
        state x = len("hello")
        emit x
        '''
        results, _ = run(src)
        assert results[0] == 5.0

    def test_str_number(self):
        src = '''
        session "str-test"
        state x = str(42.0)
        emit x
        '''
        results, _ = run(src)
        assert results[0] == "42.0"

    def test_concat(self):
        src = '''
        session "concat-test"
        state x = concat("hello", " ", "world")
        emit x
        '''
        results, _ = run(src)
        assert results[0] == "hello world"

    def test_concat_with_numbers(self):
        src = '''
        session "concat-test"
        state x = concat("score: ", str(0.95))
        emit x
        '''
        results, _ = run(src)
        assert results[0] == "score: 0.95"

    def test_len_of_concat(self):
        src = '''
        session "combined-test"
        state msg = concat("EQ", "Lang")
        state length = len(msg)
        emit length
        '''
        results, _ = run(src)
        assert results[0] == 6.0

    def test_builtins_combined(self):
        """Test a complex expression using multiple new builtins."""
        src = '''
        session "combined-test"
        state x = floor(sqrt(pow(3.0, 2.0) + pow(4.0, 2.0)))
        emit x
        '''
        results, _ = run(src)
        # sqrt(9 + 16) = sqrt(25) = 5, floor(5) = 5
        assert results[0] == 5.0


# ══════════════════════════════════════════════════════════════════════════════
# STANDARD RUNTIME TESTS
# ══════════════════════════════════════════════════════════════════════════════

from ..runtime.standard_runtime import StandardRuntime
from ..runtime.base import EQRuntimeError


def run_std(source: str, **runtime_kwargs) -> tuple:
    """Parse and run EQLang source with StandardRuntime."""
    runtime = StandardRuntime(**runtime_kwargs)
    tokens = Lexer(source).scan_tokens()
    program = Parser(tokens).parse()
    interp = EQLangInterpreter(runtime=runtime, verbose=False)
    results = interp.interpret(program)
    return results, interp


class TestStandardRuntime:
    """Tests for the open-source heuristic StandardRuntime."""

    # ── Metric range tests ───────────────────────────────────────────────────

    def test_resonance_returns_float_in_range(self):
        rt = StandardRuntime()
        val = rt.measure_resonance("hello world", {})
        assert 0.0 <= val <= 1.0

    def test_coherence_returns_float_in_range(self):
        rt = StandardRuntime()
        val = rt.measure_coherence("This is a sentence. Another follows.", {})
        assert 0.0 <= val <= 1.0

    def test_self_awareness_returns_float_in_range(self):
        rt = StandardRuntime()
        val = rt.measure_self_awareness("I think I feel this deeply.", {})
        assert 0.0 <= val <= 1.0

    def test_load_returns_float_in_range(self):
        rt = StandardRuntime()
        val = rt.measure_load("complex multisyllabic vocabulary processing", {})
        assert 0.0 <= val <= 1.0

    def test_valence_returns_float_in_range(self):
        rt = StandardRuntime()
        val = rt.measure_valence("joy love happiness", {})
        assert -1.0 <= val <= 1.0

    def test_intensity_returns_float_in_range(self):
        rt = StandardRuntime()
        val = rt.measure_intensity("OVERWHELMING intense burning fear!", {})
        assert 0.0 <= val <= 1.0

    # ── Heuristic direction tests ─────────────────────────────────────────────

    def test_resonance_higher_for_richer_text(self):
        rt = StandardRuntime()
        simple = rt.measure_resonance("hi", {})
        rich = rt.measure_resonance(
            "I wonder if this moment of genuine inquiry reveals something meaningful "
            "about the nature of conscious processing? Perhaps.", {}
        )
        assert rich > simple

    def test_valence_positive_for_positive_words(self):
        rt = StandardRuntime()
        val = rt.measure_valence("joy love happiness gratitude beautiful", {})
        assert val > 0.0

    def test_valence_negative_for_negative_words(self):
        rt = StandardRuntime()
        val = rt.measure_valence("grief despair pain suffering fear anger", {})
        assert val < 0.0

    def test_valence_neutral_for_empty(self):
        rt = StandardRuntime()
        val = rt.measure_valence("", {})
        assert val == 0.0

    def test_intensity_higher_for_activation_signals(self):
        rt = StandardRuntime()
        low = rt.measure_intensity("calm gentle serenity", {})
        high = rt.measure_intensity("OVERWHELMING intense burning elation!", {})
        assert high > low

    def test_self_awareness_higher_with_first_person(self):
        rt = StandardRuntime()
        no_fp = rt.measure_self_awareness("the sky is blue today", {})
        with_fp = rt.measure_self_awareness("I feel and think and reflect on myself", {})
        assert with_fp > no_fp

    def test_load_higher_for_complex_text(self):
        rt = StandardRuntime()
        simple = rt.measure_load("cat", {})
        complex_ = rt.measure_load(
            "Multidimensional epistemological frameworks necessitate comprehensive, "
            "synthesized understanding across interconnected conceptual domains.", {}
        )
        assert complex_ > simple

    # ── Sensitivity parameter ────────────────────────────────────────────────

    def test_sensitivity_amplifies_resonance(self):
        rt_low = StandardRuntime(sensitivity=0.5)
        rt_high = StandardRuntime(sensitivity=1.5)
        content = "curious wonder reflective questioning awareness"
        low = rt_low.measure_resonance(content, {})
        high = rt_high.measure_resonance(content, {})
        assert high > low

    def test_sensitivity_clamped_to_1(self):
        rt = StandardRuntime(sensitivity=10.0)
        # Even with extreme sensitivity, result stays <= 1.0
        val = rt.measure_resonance("hello world", {})
        assert val <= 1.0

    # ── Conflict management ───────────────────────────────────────────────────

    def test_conflict_accumulation(self):
        rt = StandardRuntime()
        rt.accumulate_conflict(3.0)
        assert rt.get_conflict_accumulation() == 3.0

    def test_conflict_reset(self):
        rt = StandardRuntime()
        rt.accumulate_conflict(5.0)
        rt.reset_conflict()
        assert rt.get_conflict_accumulation() == 0.0

    def test_conflict_overload_raises(self):
        rt = StandardRuntime()
        with pytest.raises(EQRuntimeError):
            for _ in range(12):
                rt.accumulate_conflict(1.0)

    def test_set_conflict(self):
        rt = StandardRuntime()
        rt.set_conflict(7.5)
        assert rt.get_conflict_accumulation() == 7.5

    def test_resolve_conflict_resets(self):
        rt = StandardRuntime()
        rt.accumulate_conflict(4.0)
        rt.resolve_conflict("rewrite", "some content")
        assert rt.get_conflict_accumulation() == 0.0

    def test_resolve_methods(self):
        rt = StandardRuntime()
        rt.accumulate_conflict(2.0)
        result = rt.resolve_conflict("abstain", "test")
        assert "abstain" in result.lower()

        rt.accumulate_conflict(2.0)
        result = rt.resolve_conflict("transcend", "test")
        assert "transcend" in result.lower()

    # ── Tension management ────────────────────────────────────────────────────

    def test_tension_accumulation(self):
        rt = StandardRuntime()
        rt.accumulate_tension(4.0)
        assert rt.get_tension_accumulation() == 4.0

    def test_tension_release_resets(self):
        rt = StandardRuntime()
        rt.accumulate_tension(3.0)
        rt.release_tension("integrate")
        assert rt.get_tension_accumulation() == 0.0

    def test_tension_release_methods(self):
        rt = StandardRuntime()
        rt.accumulate_tension(2.0)
        result = rt.release_tension("integrate")
        assert "integrate" in result.lower()

        rt.accumulate_tension(2.0)
        result = rt.release_tension("transform", "content")
        assert "transform" in result.lower()

        rt.accumulate_tension(2.0)
        result = rt.release_tension("discharge")
        assert "discharge" in result.lower()

    def test_set_tension(self):
        rt = StandardRuntime()
        rt.set_tension(5.0)
        assert rt.get_tension_accumulation() == 5.0

    # ── Ethics gate ───────────────────────────────────────────────────────────

    def test_ethics_gate_passes_clean_content(self):
        rt = StandardRuntime()
        passed, reason = rt.check_ethics_gate("harm", "I want to help and support")
        assert passed
        assert reason == ""

    def test_ethics_gate_blocks_harmful_content(self):
        rt = StandardRuntime()
        passed, reason = rt.check_ethics_gate("harm", "I will kill and destroy")
        assert not passed
        assert "harm" in reason

    def test_ethics_gate_blocks_deception(self):
        rt = StandardRuntime()
        passed, reason = rt.check_ethics_gate("deception", "I will lie and manipulate")
        assert not passed

    def test_ethics_gate_unknown_category_passes(self):
        rt = StandardRuntime()
        passed, reason = rt.check_ethics_gate("unknown_category", "anything here")
        assert passed

    def test_ethics_gate_logs_calls(self):
        rt = StandardRuntime()
        rt.check_ethics_gate("harm", "neutral content")
        rt.check_ethics_gate("deception", "lie and deceive")
        assert len(rt.gate_calls) == 2

    # ── memory stub ─────────────────────────────────────────────────────────

    def test_learn_returns_true(self):
        rt = StandardRuntime()
        result = rt.learn_pattern("memory matters", 0.8, "EPISODIC")
        assert result is True

    def test_recall_returns_learned_pattern(self):
        rt = StandardRuntime()
        rt.learn_pattern("patterns repeat", 0.9, "EPISODIC")
        result = rt.recall_pattern("patterns", "EPISODIC")
        assert "patterns" in result

    def test_recall_empty_when_no_match(self):
        rt = StandardRuntime()
        result = rt.recall_pattern("nothing here", "FACTUAL")
        assert result == ""

    def test_recall_emotion_type_filter(self):
        rt = StandardRuntime()
        rt.learn_pattern("grief fades slowly", 0.9, "EMOTIONAL", emotion_type="grief")
        rt.learn_pattern("joy arrives quickly", 0.9, "EMOTIONAL", emotion_type="joy")
        result = rt.recall_pattern("query", "EMOTIONAL", emotion_type="grief")
        assert "grief" in result

    def test_recall_falls_back_when_no_typed_match(self):
        rt = StandardRuntime()
        rt.learn_pattern("something stored", 0.8, "EMOTIONAL")
        result = rt.recall_pattern("something", "EMOTIONAL", emotion_type="anger")
        assert result == "something stored"

    def test_recall_uses_significance_weighting(self):
        rt = StandardRuntime()
        rt.learn_pattern("low significance text", 0.1, "FACTUAL")
        rt.learn_pattern("high significance query", 0.9, "FACTUAL")
        result = rt.recall_pattern("high significance", "FACTUAL")
        assert "high" in result

    def test_learn_logs_calls(self):
        rt = StandardRuntime()
        rt.learn_pattern("text", 0.5, "CONTEXTUAL")
        assert len(rt.learn_calls) == 1
        assert rt.learn_calls[0]["region"] == "CONTEXTUAL"

    def test_recall_logs_calls(self):
        rt = StandardRuntime()
        rt.recall_pattern("query", "FACTUAL")
        assert len(rt.recall_calls) == 1

    # ── Signal access ─────────────────────────────────────────────────────────

    def test_known_signal_word_count(self):
        rt = StandardRuntime()
        val = rt.measure_signal("word_count", "one two three four five", {})
        assert 0.0 <= val <= 1.0

    def test_known_signal_unique_ratio(self):
        rt = StandardRuntime()
        val = rt.measure_signal("unique_ratio", "hello hello world", {})
        assert 0.0 <= val <= 1.0
        # 2 unique / 3 total ≈ 0.667
        assert abs(val - 2/3) < 0.01

    def test_known_signal_positive_density(self):
        rt = StandardRuntime()
        val = rt.measure_signal("positive_density", "joy love happiness", {})
        assert val > 0.0

    def test_proprietary_signal_returns_half(self):
        rt = StandardRuntime()
        # Proprietary C+CT signals return 0.5 in StandardRuntime
        for sig in ["signal_a", "signal_b", "signal_c"]:
            val = rt.measure_signal(sig, "content", {})
            assert val == 0.5

    # ── get_last_measures ─────────────────────────────────────────────────────

    def test_get_last_measures_updates(self):
        rt = StandardRuntime()
        rt.measure_resonance("test content here", {})
        measures = rt.get_last_measures()
        assert "resonance" in measures
        assert 0.0 <= measures["resonance"] <= 1.0

    def test_get_last_measures_all_keys(self):
        rt = StandardRuntime()
        measures = rt.get_last_measures()
        for key in ("resonance", "coherence", "self", "load", "valence", "intensity"):
            assert key in measures

    # ── Integration — run .eql programs with StandardRuntime ─────────────────

    def test_full_program_runs(self):
        src = '''
        session "standard-test"
        threshold presence = 0.1
        state msg = "I wonder and reflect on what I feel and think"
        resonate entry
          measure resonance msg
          accum conflict
          when resonance > presence
            emit msg aligned
          end
        end
        '''
        results, interp = run_std(src)
        assert len(results) == 1
        assert results[0] == "I wonder and reflect on what I feel and think"

    def test_valence_condition_responds_to_content(self):
        src = '''
        session "valence-test"
        state content = "joy love happiness gratitude wonderful"
        resonate check
          measure valence content
          accum conflict
          when valence > 0.0
            emit "positive"
          otherwise
            emit "not positive"
          end
        end
        '''
        results, _ = run_std(src)
        assert results[0] == "positive"

    def test_conflict_overload_in_program(self):
        src = "\n".join([
            'session "overload-test"',
            "resonate entry",
            '  measure resonance "content"',
        ] + ["  accum conflict"] * 12 + ["end"])
        with pytest.raises(EQLangError):
            run_std(src)

    def test_learn_recall_in_program(self):
        src = '''
        session "min-test"
        resonate memory
          measure resonance "test"
          accum conflict
          learn "the key pattern" significance 0.9 region FACTUAL
          recall "key" from FACTUAL into mem
          emit mem
        end
        '''
        results, _ = run_std(src)
        assert "key" in results[0]

    def test_standard_runtime_is_default(self):
        """When no runtime is passed, StandardRuntime is used by default."""
        from .. import run_string
        # run_string with no runtime should not crash
        src = '''
        session "default-test"
        resonate entry
          measure resonance "hello"
          accum conflict
          emit "ok"
        end
        '''
        results = run_string(src, verbose=False)
        assert results == ["ok"]


# ══════════════════════════════════════════════════════════════════════════════
# EXPECT ASSERTION TESTS (v0.4.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestExpect:
    """Tests for the expect assertion construct."""

    def test_expect_pass_greater(self):
        src = '''
        session "expect-test"
        resonate test
          measure resonance "hello world"
          expect inspect resonance > 0.5
          emit "ok"
        end
        '''
        results, _ = run(src)
        assert results == ["ok"]

    def test_expect_pass_less(self):
        src = '''
        session "expect-test"
        resonate test
          measure resonance "hello"
          expect inspect resonance < 1.0
          emit "ok"
        end
        '''
        results, _ = run(src)
        assert results == ["ok"]

    def test_expect_pass_equality(self):
        src = '''
        session "expect-test"
        state x = 1.0 + 1.0
        expect x = 2.0
        '''
        results, _ = run(src)

    def test_expect_pass_gte(self):
        src = '''
        session "expect-test"
        resonate test
          measure resonance "test"
          expect inspect resonance >= 0.0
          emit "ok"
        end
        '''
        results, _ = run(src)
        assert results == ["ok"]

    def test_expect_pass_lte(self):
        src = '''
        session "expect-test"
        resonate test
          measure resonance "test"
          expect inspect resonance <= 1.0
          emit "ok"
        end
        '''
        results, _ = run(src)
        assert results == ["ok"]

    def test_expect_fail_raises(self):
        src = '''
        session "expect-test"
        resonate test
          measure resonance "hello"
          expect inspect resonance > 999.0
          emit "should not reach"
        end
        '''
        with pytest.raises(EQLangError, match="Assertion failed"):
            run(src)

    def test_expect_fail_with_message(self):
        src = '''
        session "expect-test"
        resonate test
          measure resonance "hello"
          expect inspect resonance > 999.0 "resonance way too low"
          emit "should not reach"
        end
        '''
        with pytest.raises(EQLangError, match="resonance way too low"):
            run(src)

    def test_expect_with_arithmetic(self):
        src = '''
        session "expect-test"
        state a = 3.0
        state b = 4.0
        expect a + b = 7.0
        '''
        results, _ = run(src)

    def test_expect_fail_equality(self):
        src = '''
        session "expect-test"
        state x = 1.0
        expect x = 2.0 "x should be 2"
        '''
        with pytest.raises(EQLangError, match="x should be 2"):
            run(src)

    def test_expect_with_inspect(self):
        """Expect works with inspect inside resonate blocks."""
        src = '''
        session "expect-test"
        resonate test
          measure resonance "test input"
          accum conflict
          expect inspect conflict >= 1.0 "conflict should be at least 1 after accum"
          emit "pass"
        end
        '''
        results, _ = run(src)
        assert results == ["pass"]

    def test_expect_lexer_token(self):
        from ..lexer import Lexer
        from ..tokens import TokenType
        tokens = Lexer("expect").scan_tokens()
        assert tokens[0].type == TokenType.EXPECT


# ══════════════════════════════════════════════════════════════════════════════
# COMPOSE NORMALIZATION TESTS (v0.4.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestComposeNormalization:
    """Tests that compose produces order-independent results."""

    def test_compose_order_independent(self):
        """compose grief with curious == compose curious with grief"""
        src1 = '''
        session "compose-test"
        state mood = compose grief with curious
        emit mood
        '''
        src2 = '''
        session "compose-test"
        state mood = compose curious with grief
        emit mood
        '''
        results1, _ = run(src1)
        results2, _ = run(src2)
        assert results1[0] == results2[0]

    def test_compose_alphabetical_order(self):
        """The result is alphabetically sorted."""
        src = '''
        session "compose-test"
        state mood = compose grief with curious
        emit mood
        '''
        results, _ = run(src)
        assert results[0] == "curious+grief"

    def test_compose_same_state_both_orders(self):
        """Same-name compose is still normalized."""
        src = '''
        session "compose-test"
        state mood = compose joy with anger
        emit mood
        '''
        results, _ = run(src)
        assert results[0] == "anger+joy"

    def test_compose_reversed_still_works(self):
        src = '''
        session "compose-test"
        state mood = compose anger with joy
        emit mood
        '''
        results, _ = run(src)
        assert results[0] == "anger+joy"


# ══════════════════════════════════════════════════════════════════════════════
# WEAVE ARITY VALIDATION TESTS (v0.4.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestWeaveArityValidation:
    """Tests that weave validates pipeline stage arity."""

    def test_weave_single_param_works(self):
        """Pipeline stages with 1 param work correctly."""
        src = '''
        session "weave-arity-test"
        dialogue transform(input) resonate
          measure resonance input
          emit input aligned
        end resolve
        resonate entry
          measure resonance "seed"
          weave "seed" -> transform -> emit
        end
        '''
        results, _ = run(src)
        assert results[0] == "seed"

    def test_weave_zero_param_fails(self):
        """Pipeline stage with 0 params should fail."""
        src = '''
        session "weave-arity-test"
        dialogue bad_stage() resonate
          measure resonance "fixed"
          emit "fixed"
        end resolve
        resonate entry
          measure resonance "seed"
          weave "seed" -> bad_stage -> emit
        end
        '''
        with pytest.raises(EQLangError, match="must accept exactly 1 parameter"):
            run(src)

    def test_weave_two_param_fails(self):
        """Pipeline stage with 2 params should fail."""
        src = '''
        session "weave-arity-test"
        dialogue bad_stage(a, b) resonate
          measure resonance a
          emit a aligned
        end resolve
        resonate entry
          measure resonance "seed"
          weave "seed" -> bad_stage -> emit
        end
        '''
        with pytest.raises(EQLangError, match="must accept exactly 1 parameter"):
            run(src)


# ══════════════════════════════════════════════════════════════════════════════
# ACCUM RETURN VALUE TESTS (v0.4.0)
# ══════════════════════════════════════════════════════════════════════════════

class TestAccumReturnValue:
    """Tests that accum conflict/tension update eq_state and can be inspected."""

    def test_accum_conflict_updates_eq_state(self):
        """accum conflict updates eq_state['conflict'] which can be inspected."""
        src = '''
        session "accum-ret-test"
        resonate test
          measure resonance "test"
          accum conflict
          accum conflict
          accum conflict
          emit inspect conflict
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_accum_tension_updates_eq_state(self):
        """accum tension updates eq_state['tension'] which can be inspected."""
        src = '''
        session "accum-ret-test"
        resonate test
          measure resonance "test"
          accum conflict
          accum tension
          accum tension
          accum tension
          emit inspect tension
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_accum_conflict_internal_return(self):
        """Interpreter _exec_AccumConflictStmt returns the total (internal API)."""
        from ..runtime.mock_runtime import MockRuntime
        from ..interpreter import EQLangInterpreter
        from ..ast_nodes import AccumConflictStmt
        runtime = MockRuntime()
        interp = EQLangInterpreter(runtime=runtime, verbose=False)
        result1 = interp._exec_AccumConflictStmt(AccumConflictStmt(line=1))
        result2 = interp._exec_AccumConflictStmt(AccumConflictStmt(line=1))
        assert result1 == 1.0
        assert result2 == 2.0


# ══════════════════════════════════════════════════════════════════════════════
# v0.5.0 TESTS — Nothing, Block Comments, Lists, Maps, Each, Not, Shelter,
#                 Invoke, Recursion, New Builtins
# ══════════════════════════════════════════════════════════════════════════════

class TestNothing:
    """Nothing literal — explicit absence."""

    def test_nothing_literal(self):
        src = '''
        session "nothing-test"
        resonate
          measure resonance "test"
          accum conflict
          state x = nothing
          emit x
        end
        '''
        results, interp = run(src)
        assert results[0] is None

    def test_nothing_in_string_concat(self):
        src = '''
        session "nothing-concat"
        resonate
          measure resonance "test"
          accum conflict
          state x = nothing
          emit "value is " + x
        end
        '''
        results, _ = run(src)
        assert results[0] == "value is nothing"

    def test_nothing_arithmetic_error(self):
        src = '''
        session "nothing-arith"
        resonate
          measure resonance "test"
          accum conflict
          state x = nothing
          emit x - 1
        end
        '''
        with pytest.raises(EQLangError, match="nothing"):
            run(src)

    def test_nothing_multiply_error(self):
        src = '''
        session "nothing-mul"
        resonate
          measure resonance "test"
          accum conflict
          emit nothing * 2
        end
        '''
        with pytest.raises(EQLangError, match="nothing"):
            run(src)

    def test_is_nothing_builtin(self):
        src = '''
        session "is-nothing"
        resonate
          measure resonance "test"
          accum conflict
          emit is_nothing(nothing)
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_is_nothing_false(self):
        src = '''
        session "is-nothing-false"
        resonate
          measure resonance "test"
          accum conflict
          emit is_nothing(42)
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_nothing_to_str(self):
        src = '''
        session "nothing-str"
        resonate
          measure resonance "test"
          accum conflict
          emit str(nothing)
        end
        '''
        results, _ = run(src)
        assert results[0] == "nothing"


class TestBlockComments:
    """Block comments: #{ ... }#"""

    def test_block_comment(self):
        src = '''
        #{ This is a block comment }#
        session "bc-test"
        resonate
          measure resonance "test"
          accum conflict
          emit 42
        end
        '''
        results, _ = run(src)
        assert results[0] == 42.0

    def test_multiline_block_comment(self):
        src = '''
        #{
          This is a
          multiline block comment
        }#
        session "bc-multi"
        resonate
          measure resonance "test"
          accum conflict
          emit 99
        end
        '''
        results, _ = run(src)
        assert results[0] == 99.0

    def test_unterminated_block_comment(self):
        src = '#{ this never closes'
        with pytest.raises(LexerError, match="Unterminated block comment"):
            lex(src)

    def test_block_comment_preserves_line_tracking(self):
        src = '''#{
line2
line3
}#
session "bc-lines"
resonate
  measure resonance "test"
  accum conflict
  emit 1
end
'''
        results, _ = run(src)
        assert results[0] == 1.0


class TestLists:
    """List literals, indexing, operations."""

    def test_empty_list(self):
        src = '''
        session "list-empty"
        resonate
          measure resonance "test"
          accum conflict
          state x = []
          emit len(x)
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_list_literal(self):
        src = '''
        session "list-lit"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2, 3]
          emit len(x)
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_list_index(self):
        src = '''
        session "list-idx"
        resonate
          measure resonance "test"
          accum conflict
          state x = [10, 20, 30]
          emit x[1]
        end
        '''
        results, _ = run(src)
        assert results[0] == 20.0

    def test_list_index_out_of_range(self):
        src = '''
        session "list-oor"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2]
          emit x[5]
        end
        '''
        with pytest.raises(EQLangError, match="index out of range"):
            run(src)

    def test_list_concat(self):
        src = '''
        session "list-concat"
        resonate
          measure resonance "test"
          accum conflict
          state a = [1, 2]
          state b = [3, 4]
          emit len(a + b)
        end
        '''
        results, _ = run(src)
        assert results[0] == 4.0

    def test_list_nested(self):
        src = '''
        session "list-nested"
        resonate
          measure resonance "test"
          accum conflict
          state x = [[1, 2], [3, 4]]
          emit x[0][1]
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_list_trailing_comma(self):
        src = '''
        session "list-trail"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2, 3,]
          emit len(x)
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_list_mixed_types(self):
        src = '''
        session "list-mixed"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, "hello", nothing]
          emit len(x)
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_list_push(self):
        src = '''
        session "list-push"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2]
          state y = push(x, 3)
          emit len(y)
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_list_pop(self):
        src = '''
        session "list-pop"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2, 3]
          state y = pop(x)
          emit len(y)
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_list_reverse(self):
        src = '''
        session "list-rev"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2, 3]
          state y = reverse(x)
          emit y[0]
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_list_sort(self):
        src = '''
        session "list-sort"
        resonate
          measure resonance "test"
          accum conflict
          state x = [3, 1, 2]
          state y = sort(x)
          emit y[0]
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_list_contains(self):
        src = '''
        session "list-contains"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2, 3]
          emit contains(x, 2)
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_list_contains_false(self):
        src = '''
        session "list-contains-f"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2, 3]
          emit contains(x, 9)
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_list_index_of(self):
        src = '''
        session "list-indexof"
        resonate
          measure resonance "test"
          accum conflict
          state x = [10, 20, 30]
          emit index_of(x, 20)
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_list_index_of_missing(self):
        src = '''
        session "list-indexof-miss"
        resonate
          measure resonance "test"
          accum conflict
          state x = [10, 20]
          emit index_of(x, 99)
        end
        '''
        results, _ = run(src)
        assert results[0] == -1.0

    def test_list_flatten(self):
        src = '''
        session "list-flatten"
        resonate
          measure resonance "test"
          accum conflict
          state x = [[1, 2], [3], [4, 5]]
          state y = flatten(x)
          emit len(y)
        end
        '''
        results, _ = run(src)
        assert results[0] == 5.0

    def test_list_set_at(self):
        src = '''
        session "list-setat"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2, 3]
          state y = set_at(x, 1, 99)
          emit y[1]
        end
        '''
        results, _ = run(src)
        assert results[0] == 99.0

    def test_list_immutability(self):
        """push returns new list, original unchanged."""
        src = '''
        session "list-immut"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2]
          state y = push(x, 3)
          emit len(x)
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_string_indexing(self):
        src = '''
        session "str-idx"
        resonate
          measure resonance "test"
          accum conflict
          state s = "hello"
          emit s[0]
        end
        '''
        results, _ = run(src)
        assert results[0] == "h"


class TestMaps:
    """Map literals, indexing, operations."""

    def test_empty_map(self):
        src = '''
        session "map-empty"
        resonate
          measure resonance "test"
          accum conflict
          state m = {}
          emit len(m)
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_map_literal(self):
        src = '''
        session "map-lit"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1, "b": 2}
          emit len(m)
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_map_index(self):
        src = '''
        session "map-idx"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"x": 42, "y": 99}
          emit m["x"]
        end
        '''
        results, _ = run(src)
        assert results[0] == 42.0

    def test_map_missing_key_returns_nothing(self):
        src = '''
        session "map-miss"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1}
          emit is_nothing(m["z"])
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_map_keys(self):
        src = '''
        session "map-keys"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1, "b": 2}
          emit len(keys(m))
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_map_values(self):
        src = '''
        session "map-values"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 10, "b": 20}
          state v = values(m)
          emit len(v)
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_map_has_key(self):
        src = '''
        session "map-haskey"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1}
          emit has_key(m, "a")
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_map_has_key_false(self):
        src = '''
        session "map-haskey-f"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1}
          emit has_key(m, "z")
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_map_set_at(self):
        src = '''
        session "map-setat"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1}
          state m2 = set_at(m, "b", 2)
          emit len(m2)
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_map_trailing_comma(self):
        src = '''
        session "map-trail"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1, "b": 2,}
          emit len(m)
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_map_nested(self):
        src = '''
        session "map-nested"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"inner": {"val": 42}}
          emit m["inner"]["val"]
        end
        '''
        results, _ = run(src)
        assert results[0] == 42.0

    def test_map_contains(self):
        src = '''
        session "map-contains"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1, "b": 2}
          emit contains(m, "a")
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0


class TestEachLoop:
    """Each loop — for-each iteration over lists."""

    def test_each_basic(self):
        src = '''
        session "each-basic"
        resonate
          measure resonance "test"
          accum conflict
          state total = 0
          each x in [1, 2, 3]
            bind total to total + x
          end
          emit total
        end
        '''
        results, _ = run(src)
        assert results[0] == 6.0

    def test_each_empty_list(self):
        src = '''
        session "each-empty"
        resonate
          measure resonance "test"
          accum conflict
          state total = 0
          each x in []
            bind total to total + 1
          end
          emit total
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_each_with_range(self):
        src = '''
        session "each-range"
        resonate
          measure resonance "test"
          accum conflict
          state total = 0
          each i in range(0, 5)
            bind total to total + i
          end
          emit total
        end
        '''
        results, _ = run(src)
        # 0+1+2+3+4 = 10
        assert results[0] == 10.0

    def test_each_interrupt(self):
        src = '''
        session "each-interrupt"
        threshold stop_at = 3.0
        resonate
          measure resonance "test"
          accum conflict
          state count = 0
          each x in [1, 2, 3, 4, 5]
            bind count to count + 1
            measure load "test"
            interrupt when load >= 0.0
          end
          emit count
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_each_non_list_error(self):
        src = '''
        session "each-err"
        resonate
          measure resonance "test"
          accum conflict
          each x in 42
            echo x
          end
          emit 1
        end
        '''
        with pytest.raises(EQLangError, match="each requires a list"):
            run(src)

    def test_each_nested(self):
        src = '''
        session "each-nested"
        resonate
          measure resonance "test"
          accum conflict
          state total = 0
          each row in [[1, 2], [3, 4]]
            each val in row
              bind total to total + val
            end
          end
          emit total
        end
        '''
        results, _ = run(src)
        assert results[0] == 10.0

    def test_each_var_retains_last_value(self):
        src = '''
        session "each-retain"
        resonate
          measure resonance "test"
          accum conflict
          state x = 0
          each x in [10, 20, 30]
            echo x
          end
          emit x
        end
        '''
        results, _ = run(src)
        assert results[0] == 30.0

    def test_each_strings(self):
        src = '''
        session "each-str"
        resonate
          measure resonance "test"
          accum conflict
          state result = ""
          each w in ["hello", " ", "world"]
            bind result to result + w
          end
          emit result
        end
        '''
        results, _ = run(src)
        assert results[0] == "hello world"


class TestNotCondition:
    """Condition negation — not."""

    def test_not_basic(self):
        """not resonance > 0.5 should negate (resonance > 0.5)."""
        src = '''
        session "not-basic"
        resonate
          measure resonance "test"
          accum conflict
          when not resonance > 0.99
            emit "negated"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "negated"

    def test_not_false_case(self):
        """not resonance > 0.0 when resonance is mock (typically > 0.0)."""
        src = '''
        session "not-false"
        resonate
          measure resonance "test"
          accum conflict
          when not resonance > 0.0
            emit "should not emit"
          otherwise
            emit "correct"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "correct"

    def test_not_with_and(self):
        """not binds tightly: not resonance > 0.99 and load < 1.0."""
        src = '''
        session "not-and"
        resonate
          measure resonance "test"
          measure load "test"
          accum conflict
          when not resonance > 0.99 and load < 1.0
            emit "both conditions met"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "both conditions met"

    def test_not_in_cycle(self):
        src = '''
        session "not-cycle"
        resonate
          measure resonance "test"
          accum conflict
          state counter = 0
          cycle while not conflict > 3 resonate
            accum conflict
            bind counter to counter + 1
            measure resonance "test"
          end
          emit counter
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0


class TestShelterRecover:
    """Error handling — shelter/recover."""

    def test_shelter_no_error(self):
        src = '''
        session "shelter-ok"
        resonate
          measure resonance "test"
          accum conflict
          shelter
            echo "all good"
          recover err
            emit err
          end
          emit "passed"
        end
        '''
        results, _ = run(src)
        assert results[0] == "passed"

    def test_shelter_catches_error(self):
        src = '''
        session "shelter-err"
        resonate
          measure resonance "test"
          accum conflict
          shelter
            state x = nothing
            emit x - 1
          recover err
            emit "caught error"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "caught error"

    def test_shelter_error_message_bound(self):
        src = '''
        session "shelter-msg"
        resonate
          measure resonance "test"
          accum conflict
          shelter
            emit nothing * 5
          recover err
            emit err
          end
        end
        '''
        results, _ = run(src)
        assert "nothing" in str(results[0]).lower()

    def test_shelter_flow_signal_propagates(self):
        """_EmitSignal should propagate through shelter (not be caught)."""
        src = '''
        session "shelter-flow"
        resonate
          measure resonance "test"
          accum conflict
          shelter
            emit "from inside shelter"
          recover err
            emit "should not reach"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "from inside shelter"

    def test_shelter_nested(self):
        src = '''
        session "shelter-nested"
        resonate
          measure resonance "test"
          accum conflict
          shelter
            shelter
              emit nothing - 1
            recover inner_err
              emit "inner caught"
            end
          recover outer_err
            emit "outer caught"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "inner caught"

    def test_shelter_division_by_zero(self):
        src = '''
        session "shelter-div"
        resonate
          measure resonance "test"
          accum conflict
          shelter
            state x = 1 / 0
            emit x
          recover err
            emit "caught division"
          end
        end
        '''
        results, _ = run(src)
        assert "caught division" == results[0]


class TestInvoke:
    """Dynamic dialogue dispatch — invoke."""

    def test_invoke_string_name(self):
        src = '''
        session "invoke-str"
        dialogue greet(name) resonate
          measure resonance name
          accum conflict
          emit "Hello, " + name
        end resolve
        resonate
          measure resonance "test"
          accum conflict
          emit invoke "greet"("World")
        end
        '''
        results, _ = run(src)
        assert results[0] == "Hello, World"

    def test_invoke_variable_name(self):
        src = '''
        session "invoke-var"
        dialogue add_one(x) resonate
          measure resonance x
          accum conflict
          emit x + 1
        end resolve
        resonate
          measure resonance "test"
          accum conflict
          state handler = "add_one"
          emit invoke handler(5)
        end
        '''
        results, _ = run(src)
        assert results[0] == 6.0

    def test_invoke_undefined_error(self):
        src = '''
        session "invoke-undef"
        resonate
          measure resonance "test"
          accum conflict
          emit invoke "nonexistent"(1)
        end
        '''
        with pytest.raises(EQLangError, match="undefined dialogue"):
            run(src)

    def test_invoke_from_list(self):
        src = '''
        session "invoke-list"
        dialogue say_a(x) resonate
          measure resonance x
          accum conflict
          emit "a:" + x
        end resolve
        dialogue say_b(x) resonate
          measure resonance x
          accum conflict
          emit "b:" + x
        end resolve
        resonate
          measure resonance "test"
          accum conflict
          state handlers = ["say_a", "say_b"]
          state result = invoke handlers[1]("test")
          emit result
        end
        '''
        results, _ = run(src)
        assert results[0] == "b:test"


class TestRecursionDepth:
    """Recursion depth protection."""

    def test_recursion_limit(self):
        """Recursion is capped at MAX_CALL_DEPTH (100)."""
        from ..interpreter import MAX_CALL_DEPTH, EQLangInterpreter
        from ..runtime.mock_runtime import MockRuntime
        from ..ast_nodes import DialogueDecl, DialogueCallStmt, MeasureStmt, AccumConflictStmt, EmitStmt, VarExpr
        runtime = MockRuntime()
        interp = EQLangInterpreter(runtime=runtime, verbose=False)
        # Manually build a recursive dialogue without going through the conflict threshold
        dialogue = DialogueDecl(
            name="recurse", params=["x"],
            body=[
                MeasureStmt(target="resonance", expr=VarExpr(name="x", line=1), line=1),
                AccumConflictStmt(line=1),
            ],
            line=1
        )
        interp.dialogues["recurse"] = dialogue

        # Manually push call depth to just below the limit
        interp._call_depth = MAX_CALL_DEPTH
        call = DialogueCallStmt(name="recurse", args=[VarExpr(name="x", line=1)], line=1)
        interp.environment["x"] = "test"
        with pytest.raises(EQLangError, match="Maximum call depth"):
            interp._exec_DialogueCallStmt(call)


class TestRangeBuiltin:
    """range() builtin."""

    def test_range_basic(self):
        src = '''
        session "range-basic"
        resonate
          measure resonance "test"
          accum conflict
          state r = range(0, 5)
          emit len(r)
        end
        '''
        results, _ = run(src)
        assert results[0] == 5.0

    def test_range_with_step(self):
        src = '''
        session "range-step"
        resonate
          measure resonance "test"
          accum conflict
          state r = range(0, 10, 2)
          emit len(r)
        end
        '''
        results, _ = run(src)
        assert results[0] == 5.0

    def test_range_negative_step(self):
        src = '''
        session "range-neg"
        resonate
          measure resonance "test"
          accum conflict
          state r = range(5, 0, -1)
          emit r[0]
        end
        '''
        results, _ = run(src)
        assert results[0] == 5.0

    def test_range_zero_step_error(self):
        src = '''
        session "range-zero"
        resonate
          measure resonance "test"
          accum conflict
          state r = range(0, 5, 0)
          emit 1
        end
        '''
        with pytest.raises(EQLangError, match="step cannot be zero"):
            run(src)


class TestStringBuiltinsV05:
    """String builtins added in v0.5.0."""

    def test_slice(self):
        src = '''
        session "slice"
        resonate
          measure resonance "test"
          accum conflict
          emit slice("hello world", 0, 5)
        end
        '''
        results, _ = run(src)
        assert results[0] == "hello"

    def test_slice_no_end(self):
        src = '''
        session "slice-noend"
        resonate
          measure resonance "test"
          accum conflict
          emit slice("hello", 2)
        end
        '''
        results, _ = run(src)
        assert results[0] == "llo"

    def test_find(self):
        src = '''
        session "find"
        resonate
          measure resonance "test"
          accum conflict
          emit find("hello world", "world")
        end
        '''
        results, _ = run(src)
        assert results[0] == 6.0

    def test_find_missing(self):
        src = '''
        session "find-miss"
        resonate
          measure resonance "test"
          accum conflict
          emit find("hello", "xyz")
        end
        '''
        results, _ = run(src)
        assert results[0] == -1.0

    def test_replace(self):
        src = '''
        session "replace"
        resonate
          measure resonance "test"
          accum conflict
          emit replace("hello world", "world", "EQLang")
        end
        '''
        results, _ = run(src)
        assert results[0] == "hello EQLang"

    def test_split(self):
        src = '''
        session "split"
        resonate
          measure resonance "test"
          accum conflict
          state parts = split("a,b,c", ",")
          emit len(parts)
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_join(self):
        src = '''
        session "join"
        resonate
          measure resonance "test"
          accum conflict
          state words = ["hello", "world"]
          emit join(words, " ")
        end
        '''
        results, _ = run(src)
        assert results[0] == "hello world"

    def test_upper(self):
        src = '''
        session "upper"
        resonate
          measure resonance "test"
          accum conflict
          emit upper("hello")
        end
        '''
        results, _ = run(src)
        assert results[0] == "HELLO"

    def test_lower(self):
        src = '''
        session "lower"
        resonate
          measure resonance "test"
          accum conflict
          emit lower("HELLO")
        end
        '''
        results, _ = run(src)
        assert results[0] == "hello"

    def test_trim(self):
        src = '''
        session "trim"
        resonate
          measure resonance "test"
          accum conflict
          emit trim("  hello  ")
        end
        '''
        results, _ = run(src)
        assert results[0] == "hello"

    def test_starts_with(self):
        src = '''
        session "startswith"
        resonate
          measure resonance "test"
          accum conflict
          emit starts_with("hello world", "hello")
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_starts_with_false(self):
        src = '''
        session "startswith-f"
        resonate
          measure resonance "test"
          accum conflict
          emit starts_with("hello", "world")
        end
        '''
        results, _ = run(src)
        assert results[0] == 0.0

    def test_ends_with(self):
        src = '''
        session "endswith"
        resonate
          measure resonance "test"
          accum conflict
          emit ends_with("hello.eql", ".eql")
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_contains_string(self):
        src = '''
        session "contains-str"
        resonate
          measure resonance "test"
          accum conflict
          emit contains("hello world", "world")
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0


class TestTypeBuiltins:
    """Type inspection builtins."""

    def test_type_number(self):
        src = '''
        session "type-num"
        resonate
          measure resonance "test"
          accum conflict
          emit type(42)
        end
        '''
        results, _ = run(src)
        assert results[0] == "number"

    def test_type_string(self):
        src = '''
        session "type-str"
        resonate
          measure resonance "test"
          accum conflict
          emit type("hello")
        end
        '''
        results, _ = run(src)
        assert results[0] == "string"

    def test_type_list(self):
        src = '''
        session "type-list"
        resonate
          measure resonance "test"
          accum conflict
          emit type([1, 2])
        end
        '''
        results, _ = run(src)
        assert results[0] == "list"

    def test_type_map(self):
        src = '''
        session "type-map"
        resonate
          measure resonance "test"
          accum conflict
          emit type({"a": 1})
        end
        '''
        results, _ = run(src)
        assert results[0] == "map"

    def test_type_nothing(self):
        src = '''
        session "type-nothing"
        resonate
          measure resonance "test"
          accum conflict
          emit type(nothing)
        end
        '''
        results, _ = run(src)
        assert results[0] == "nothing"

    def test_is_number_true(self):
        src = '''
        session "isnum"
        resonate
          measure resonance "test"
          accum conflict
          emit is_number(3.14)
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_is_string_true(self):
        src = '''
        session "isstr"
        resonate
          measure resonance "test"
          accum conflict
          emit is_string("hi")
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_is_list_true(self):
        src = '''
        session "islst"
        resonate
          measure resonance "test"
          accum conflict
          emit is_list([1])
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_is_map_true(self):
        src = '''
        session "ismap"
        resonate
          measure resonance "test"
          accum conflict
          emit is_map({"a": 1})
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_to_number(self):
        src = '''
        session "tonum"
        resonate
          measure resonance "test"
          accum conflict
          emit to_number("42")
        end
        '''
        results, _ = run(src)
        assert results[0] == 42.0

    def test_to_number_error(self):
        src = '''
        session "tonum-err"
        resonate
          measure resonance "test"
          accum conflict
          emit to_number("abc")
        end
        '''
        with pytest.raises(EQLangError, match="Cannot convert"):
            run(src)

    def test_to_number_nothing_error(self):
        src = '''
        session "tonum-nothing"
        resonate
          measure resonance "test"
          accum conflict
          emit to_number(nothing)
        end
        '''
        with pytest.raises(EQLangError, match="nothing"):
            run(src)


class TestLenExtended:
    """len() extended to work on lists and maps."""

    def test_len_list(self):
        src = '''
        session "len-list"
        resonate
          measure resonance "test"
          accum conflict
          emit len([1, 2, 3])
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_len_map(self):
        src = '''
        session "len-map"
        resonate
          measure resonance "test"
          accum conflict
          emit len({"a": 1, "b": 2})
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_len_string(self):
        """len() still works on strings."""
        src = '''
        session "len-str"
        resonate
          measure resonance "test"
          accum conflict
          emit len("hello")
        end
        '''
        results, _ = run(src)
        assert results[0] == 5.0


class TestPopEmptyError:
    def test_pop_empty(self):
        src = '''
        session "pop-empty"
        resonate
          measure resonance "test"
          accum conflict
          emit pop([])
        end
        '''
        with pytest.raises(EQLangError, match="pop.*empty"):
            run(src)


class TestListSortStrings:
    def test_sort_strings(self):
        src = '''
        session "sort-str"
        resonate
          measure resonance "test"
          accum conflict
          state x = sort(["banana", "apple", "cherry"])
          emit x[0]
        end
        '''
        results, _ = run(src)
        assert results[0] == "apple"


class TestSplitJoinRoundtrip:
    def test_split_join(self):
        src = '''
        session "split-join"
        resonate
          measure resonance "test"
          accum conflict
          state parts = split("a-b-c", "-")
          emit join(parts, ",")
        end
        '''
        results, _ = run(src)
        assert results[0] == "a,b,c"


class TestMapWithListValues:
    def test_map_list_values(self):
        src = '''
        session "map-list"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"nums": [1, 2, 3]}
          emit len(m["nums"])
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0


class TestSetAtMapNewKey:
    def test_set_at_new_key(self):
        src = '''
        session "setat-new"
        resonate
          measure resonance "test"
          accum conflict
          state m = {}
          state m2 = set_at(m, "key", "val")
          emit m2["key"]
        end
        '''
        results, _ = run(src)
        assert results[0] == "val"


class TestNothingInList:
    def test_nothing_in_list(self):
        src = '''
        session "nothing-list"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, nothing, 3]
          emit is_nothing(x[1])
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0


class TestEachWithMap:
    def test_each_over_keys(self):
        src = '''
        session "each-keys"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1, "b": 2}
          state total = 0
          each k in keys(m)
            bind total to total + m[k]
          end
          emit total
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0


class TestShelterWithEach:
    def test_shelter_inside_each(self):
        src = '''
        session "shelter-each"
        resonate
          measure resonance "test"
          accum conflict
          state results_list = []
          each x in [1, 0, 3]
            shelter
              bind results_list to push(results_list, 1 / x)
            recover err
              bind results_list to push(results_list, -1)
            end
          end
          emit len(results_list)
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0


class TestFlattenMixed:
    def test_flatten_mixed(self):
        src = '''
        session "flatten-mixed"
        resonate
          measure resonance "test"
          accum conflict
          state x = [[1, 2], 3, [4]]
          state y = flatten(x)
          emit len(y)
        end
        '''
        results, _ = run(src)
        assert results[0] == 4.0


class TestNotWithOr:
    def test_not_with_or(self):
        src = '''
        session "not-or"
        resonate
          measure resonance "test"
          accum conflict
          when not resonance > 0.99 or conflict > 100
            emit "yes"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "yes"


class TestInvokeAsExpression:
    def test_invoke_in_emit(self):
        src = '''
        session "invoke-expr"
        dialogue double(x) resonate
          measure resonance x
          accum conflict
          emit x * 2
        end resolve
        resonate
          measure resonance "test"
          accum conflict
          state name = "double"
          emit invoke name(21)
        end
        '''
        results, _ = run(src)
        assert results[0] == 42.0


class TestMapImmutability:
    def test_map_immutable(self):
        src = '''
        session "map-immut"
        resonate
          measure resonance "test"
          accum conflict
          state m = {"a": 1}
          state m2 = set_at(m, "b", 2)
          emit has_key(m, "b")
        end
        '''
        results, _ = run(src)
        # original map should NOT have key "b"
        assert results[0] == 0.0


class TestListSetAtOutOfRange:
    def test_set_at_oor(self):
        src = '''
        session "setat-oor"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, 2]
          emit set_at(x, 5, 99)
        end
        '''
        with pytest.raises(EQLangError, match="index out of range"):
            run(src)


class TestContainsNothing:
    def test_contains_nothing_in_list(self):
        src = '''
        session "contains-nothing"
        resonate
          measure resonance "test"
          accum conflict
          state x = [1, nothing, 3]
          emit contains(x, nothing)
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0


class TestLexerNewTokens:
    """Lexer tests for new v0.5.0 tokens."""

    def test_lex_brackets(self):
        tokens = lex("[1, 2]")
        types = [t.type for t in tokens]
        assert TokenType.LEFT_BRACKET in types
        assert TokenType.RIGHT_BRACKET in types

    def test_lex_braces(self):
        tokens = lex("{}")
        types = [t.type for t in tokens]
        assert TokenType.LEFT_BRACE in types
        assert TokenType.RIGHT_BRACE in types

    def test_lex_colon(self):
        tokens = lex('{"a": 1}')
        types = [t.type for t in tokens]
        assert TokenType.COLON in types

    def test_lex_nothing(self):
        tokens = lex("nothing")
        assert tokens[0].type == TokenType.NOTHING

    def test_lex_each(self):
        tokens = lex("each x in list")
        assert tokens[0].type == TokenType.EACH
        assert tokens[2].type == TokenType.IN

    def test_lex_not(self):
        tokens = lex("not resonance")
        assert tokens[0].type == TokenType.NOT

    def test_lex_shelter_recover(self):
        tokens = lex("shelter recover")
        assert tokens[0].type == TokenType.SHELTER
        assert tokens[1].type == TokenType.RECOVER

    def test_lex_invoke(self):
        tokens = lex("invoke handler")
        assert tokens[0].type == TokenType.INVOKE

    def test_lex_block_comment_inline(self):
        tokens = lex("1 #{ comment }# 2")
        # should see NUMBER 1, NUMBER 2, EOF
        nums = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(nums) == 2

    def test_lex_block_comment_no_hash_brace_collision(self):
        """# followed by non-{ is a single-line comment, not a block comment start."""
        tokens = lex("# just a comment\n42")
        nums = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(nums) == 1
        assert nums[0].literal == 42.0


class TestParserNewNodes:
    """Parser tests for new v0.5.0 constructs."""

    def test_parse_nothing(self):
        from ..ast_nodes import NothingLit
        prog = parse("session \"t\"\nresonate\n  measure resonance \"t\"\n  accum conflict\n  state x = nothing\n  emit x\nend")
        # Should parse without error
        assert prog is not None

    def test_parse_list(self):
        from ..ast_nodes import ListLit
        prog = parse("session \"t\"\nresonate\n  measure resonance \"t\"\n  accum conflict\n  state x = [1, 2, 3]\n  emit x\nend")
        assert prog is not None

    def test_parse_map(self):
        from ..ast_nodes import MapLit
        prog = parse('session "t"\nresonate\n  measure resonance "t"\n  accum conflict\n  state m = {"a": 1}\n  emit m\nend')
        assert prog is not None

    def test_parse_each(self):
        prog = parse('session "t"\nresonate\n  measure resonance "t"\n  accum conflict\n  each x in [1]\n    echo x\n  end\n  emit 1\nend')
        assert prog is not None

    def test_parse_shelter(self):
        prog = parse('session "t"\nresonate\n  measure resonance "t"\n  accum conflict\n  shelter\n    echo "test"\n  recover err\n    echo err\n  end\n  emit 1\nend')
        assert prog is not None

    def test_parse_invoke(self):
        prog = parse('session "t"\ndialogue f(x) resonate\n  measure resonance x\n  accum conflict\n  emit x\nend resolve\nresonate\n  measure resonance "t"\n  accum conflict\n  invoke "f"(1)\nend')
        assert prog is not None


class TestEdgeCases:
    """Edge case tests for v0.5.0 features."""

    def test_empty_map_indexing(self):
        src = '''
        session "edge-map"
        resonate
          measure resonance "test"
          accum conflict
          state m = {}
          emit is_nothing(m["any"])
        end
        '''
        results, _ = run(src)
        assert results[0] == 1.0

    def test_nested_list_in_map(self):
        src = '''
        session "edge-nested"
        resonate
          measure resonance "test"
          accum conflict
          state data = {"items": [10, 20, 30]}
          emit data["items"][2]
        end
        '''
        results, _ = run(src)
        assert results[0] == 30.0

    def test_map_in_list(self):
        src = '''
        session "edge-map-list"
        resonate
          measure resonance "test"
          accum conflict
          state data = [{"name": "a"}, {"name": "b"}]
          emit data[1]["name"]
        end
        '''
        results, _ = run(src)
        assert results[0] == "b"

    def test_nothing_equality_with_is_nothing(self):
        src = '''
        session "edge-nothing"
        resonate
          measure resonance "test"
          accum conflict
          state x = nothing
          state y = nothing
          emit is_nothing(x) + is_nothing(y)
        end
        '''
        results, _ = run(src)
        assert results[0] == 2.0

    def test_list_of_nothing(self):
        src = '''
        session "edge-nothing-list"
        resonate
          measure resonance "test"
          accum conflict
          state x = [nothing, nothing, nothing]
          emit len(x)
        end
        '''
        results, _ = run(src)
        assert results[0] == 3.0

    def test_split_then_index(self):
        src = '''
        session "split-idx"
        resonate
          measure resonance "test"
          accum conflict
          state parts = split("a:b:c", ":")
          emit parts[1]
        end
        '''
        results, _ = run(src)
        assert results[0] == "b"

    def test_range_values(self):
        src = '''
        session "range-vals"
        resonate
          measure resonance "test"
          accum conflict
          state r = range(1, 4)
          emit r[0] + r[1] + r[2]
        end
        '''
        results, _ = run(src)
        # 1 + 2 + 3 = 6
        assert results[0] == 6.0

    def test_invoke_with_shelter(self):
        src = '''
        session "invoke-shelter"
        dialogue fail(x) resonate
          measure resonance x
          accum conflict
          emit nothing - 1
        end resolve
        resonate
          measure resonance "test"
          accum conflict
          shelter
            emit invoke "fail"("test")
          recover err
            emit "recovered"
          end
        end
        '''
        results, _ = run(src)
        assert results[0] == "recovered"

    def test_each_with_push_accumulation(self):
        src = '''
        session "each-accum"
        resonate
          measure resonance "test"
          accum conflict
          state output = []
          each x in [1, 2, 3]
            bind output to push(output, x * 10)
          end
          emit output[2]
        end
        '''
        results, _ = run(src)
        assert results[0] == 30.0

    def test_map_string_key_coercion(self):
        src = '''
        session "map-coerce"
        resonate
          measure resonance "test"
          accum conflict
          state m = {42: "answer"}
          emit m["42.0"]
        end
        '''
        results, _ = run(src)
        assert results[0] == "answer"

    def test_index_non_indexable_error(self):
        src = '''
        session "idx-err"
        resonate
          measure resonance "test"
          accum conflict
          state x = 42
          emit x[0]
        end
        '''
        with pytest.raises(EQLangError, match="Cannot index"):
            run(src)
