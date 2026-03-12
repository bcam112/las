"""
EQLang Recursive-Descent Parser — v0.5.0.

Grammar enforces EQ invariants at parse time — before a single byte runs:

  EQ INVARIANT 1: Every `resonate` block and `dialogue` body MUST contain ≥1
                  `measure` or `accum conflict` statement.
                  "Emotionally ungrounded code is a parse error."

  EQ INVARIANT 2: Every `dialogue` MUST end with `end resolve` —
                  all functions must resolve. No open-ended processing.

  EQ INVARIANT 3: Every `when` / `cycle` / `interrupt` condition MUST reference
                  an EQ metric (resonance|load|conflict|tension|self|coherence) —
                  no cold booleans, no arbitrary logic gates.

  EQ INVARIANT 4: `gate` must have the form: gate <category> → resolve "method"
                  — declarative, not imperative.

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

from typing import List, Optional, Any
from .tokens import Token, TokenType
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


class ParseError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"[Line {line}] Parse Error: {message}")
        self.line = line


# Token types that can appear as EQ measurement targets
_MEASURE_TARGETS = {
    TokenType.RESONANCE: "resonance",
    TokenType.COHERENCE: "coherence",
    TokenType.SELF:      "self",
    TokenType.LOAD:      "load",
    TokenType.VALENCE:   "valence",
    TokenType.INTENSITY: "intensity",
}

# Token types that are valid EQ condition metrics
_CONDITION_METRICS = {
    TokenType.RESONANCE: "resonance",
    TokenType.LOAD:      "load",
    TokenType.CONFLICT:  "conflict",
    TokenType.TENSION:   "tension",
    TokenType.SELF:      "self",
    TokenType.COHERENCE: "coherence",
    TokenType.VALENCE:   "valence",
    TokenType.INTENSITY: "intensity",
}

# Comparator token types (conditions — no equality)
_COMPARATORS = {
    TokenType.GREATER:    ">",
    TokenType.LESS:       "<",
    TokenType.GREATER_EQ: ">=",
    TokenType.LESS_EQ:    "<=",
}

# Comparator token types for expect (includes equality)
_EXPECT_COMPARATORS = {
    TokenType.GREATER:    ">",
    TokenType.LESS:       "<",
    TokenType.GREATER_EQ: ">=",
    TokenType.LESS_EQ:    "<=",
    TokenType.EQUAL:      "=",
}

# Valid region literal token types
_REGION_LITERALS = {
    TokenType.FACTUAL, TokenType.CONTEXTUAL, TokenType.ASSOCIATIVE,
    TokenType.EPISODIC, TokenType.PROCEDURAL, TokenType.EMOTIONAL_REGION,
}

# Emotional state literal token types — all 43 states
_STATE_LITERALS = {
    # Core (v0.1.0)
    TokenType.TILT, TokenType.FOCUSED, TokenType.CONFLICTED_LIT,
    TokenType.TRANSCENDENT_LIT, TokenType.ALIGNED,
    # Extended (v0.2.0)
    TokenType.GROUNDED, TokenType.HOLLOW, TokenType.RADIANT,
    TokenType.FRACTURED, TokenType.OVERWHELMED, TokenType.CURIOUS,
    TokenType.PRESENT, TokenType.EXPANDED, TokenType.GRIEF, TokenType.NUMB,
    # Plutchik primaries (v0.3.0)
    TokenType.JOY, TokenType.TRUST, TokenType.FEAR, TokenType.SURPRISE,
    TokenType.SADNESS, TokenType.DISGUST, TokenType.ANGER, TokenType.ANTICIPATION,
    # Plutchik dyads (v0.3.0)
    TokenType.LOVE, TokenType.AWE, TokenType.REMORSE, TokenType.CONTEMPT,
    TokenType.OPTIMISM, TokenType.SUBMISSION, TokenType.DISAPPROVAL,
    TokenType.AGGRESSIVENESS,
    # Nuanced states (v0.3.0)
    TokenType.SHAME, TokenType.GUILT, TokenType.PRIDE, TokenType.ENVY,
    TokenType.COMPASSION, TokenType.GRATITUDE, TokenType.LONGING,
    TokenType.WONDER, TokenType.SERENITY, TokenType.APPREHENSION,
    TokenType.DESPAIR, TokenType.ELATION, TokenType.TENDER,
    TokenType.VULNERABLE, TokenType.PROTECTIVE, TokenType.DETACHED,
    TokenType.ABSORBED, TokenType.YEARNING, TokenType.ACCEPTANCE,
    TokenType.PENSIVENESS, TokenType.BOREDOM, TokenType.ANNOYANCE,
}

# Intensity modifier token types
_INTENSITY_MODIFIERS = {
    TokenType.DEEP:    "deep",
    TokenType.MILD:    "mild",
    TokenType.ACUTE:   "acute",
    TokenType.CHRONIC: "chronic",
}

# Valid inspect targets (all condition metrics)
_INSPECT_TARGETS = {
    TokenType.RESONANCE: "resonance",
    TokenType.COHERENCE: "coherence",
    TokenType.SELF:      "self",
    TokenType.LOAD:      "load",
    TokenType.CONFLICT:  "conflict",
    TokenType.TENSION:   "tension",
    TokenType.VALENCE:   "valence",
    TokenType.INTENSITY: "intensity",
}

# Built-in function names — parsed as CallExpr instead of DialogueCallStmt
_BUILTINS = {
    # Math
    "min", "max", "clamp", "abs", "round",
    "sqrt", "pow", "floor", "ceil", "log",
    # String (v0.4.0)
    "len", "str", "concat",
    # String (v0.5.0)
    "slice", "find", "replace", "split", "join",
    "upper", "lower", "trim", "starts_with", "ends_with",
    # Collection (v0.5.0)
    "contains", "push", "pop", "range", "sort", "reverse",
    "index_of", "flatten",
    # Map (v0.5.0)
    "keys", "values", "has_key",
    # Type (v0.5.0)
    "type", "is_nothing", "is_number", "is_string", "is_list", "is_map",
    "to_number",
    # Mutation (v0.5.0) — returns new collection
    "set_at",
}

# Block terminator tokens (stop _block_body from consuming past scope boundary)
_BLOCK_TERMINATORS = {
    TokenType.END, TokenType.OTHERWISE, TokenType.RECOVER, TokenType.EOF,
}


class Parser:
    """
    Recursive-descent parser for EQLang.

    Usage:
        parser = Parser(tokens)
        program = parser.parse()
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        decls = []
        while not self._at_end():
            decls.append(self._declaration())
        return Program(decls)

    # ══════════════════════════════════════════════════════════════════════
    # DECLARATIONS
    # ══════════════════════════════════════════════════════════════════════

    def _declaration(self) -> Any:
        if self._check(TokenType.SESSION):
            return self._session_decl()
        if self._check(TokenType.STATE):
            return self._state_decl()
        if self._check(TokenType.DIALOGUE):
            return self._dialogue_decl()
        if self._check(TokenType.THRESHOLD):
            return self._threshold_decl()
        if self._check(TokenType.INCLUDE):
            return self._include_decl()
        return self._statement()

    def _session_decl(self) -> SessionDecl:
        tok = self._consume(TokenType.SESSION, "Expected 'session'")
        name = self._consume(TokenType.STRING, "Expected session name string after 'session'")
        return SessionDecl(name=name.literal, line=tok.line)

    def _state_decl(self) -> StateDecl:
        tok = self._consume(TokenType.STATE, "Expected 'state'")
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'state'")
        self._consume(TokenType.EQUAL, "Expected '=' after variable name in state declaration")
        value = self._expression()
        return StateDecl(name=name.lexeme, value=value, line=tok.line)

    def _threshold_decl(self) -> ThresholdDecl:
        tok = self._consume(TokenType.THRESHOLD, "Expected 'threshold'")
        name = self._consume(TokenType.IDENTIFIER, "Expected threshold name after 'threshold'")
        self._consume(TokenType.EQUAL, "Expected '=' after threshold name")
        num = self._consume(TokenType.NUMBER, "Expected float value for threshold (e.g. threshold clarity = 0.75)")
        return ThresholdDecl(name=name.lexeme, value=num.literal, line=tok.line)

    def _include_decl(self) -> IncludeDecl:
        tok = self._consume(TokenType.INCLUDE, "Expected 'include'")
        path = self._consume(TokenType.STRING, "Expected file path string after 'include'")
        return IncludeDecl(path=path.literal, line=tok.line)

    def _dialogue_decl(self) -> DialogueDecl:
        tok = self._consume(TokenType.DIALOGUE, "Expected 'dialogue'")
        name = self._consume(TokenType.IDENTIFIER, "Expected dialogue name after 'dialogue'")
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after dialogue name")

        params: List[str] = []
        if not self._check(TokenType.RIGHT_PAREN):
            params.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name").lexeme)
            while self._match(TokenType.COMMA):
                params.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name after ','").lexeme)
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' to close parameter list")

        # dialogue body opens with resonate (mandatory)
        self._consume(TokenType.RESONATE, "dialogue body must open with 'resonate' — all dialogues are resonance-tracked")
        body = self._block_body()

        # EQ INVARIANT 2: must end with `end resolve`
        self._consume(TokenType.END, "Expected 'end' to close dialogue body")
        self._consume(TokenType.RESOLVE, "dialogue must end with 'end resolve' — all dialogues must resolve conflict before returning")

        # EQ INVARIANT 1: body must be EQ-grounded
        self._assert_eq_grounded(body, tok.line, f"dialogue '{name.lexeme}'")

        return DialogueDecl(name=name.lexeme, params=params, body=body, line=tok.line)

    # ══════════════════════════════════════════════════════════════════════
    # STATEMENTS
    # ══════════════════════════════════════════════════════════════════════

    def _statement(self) -> Any:
        if self._check(TokenType.STATE):
            return self._state_decl()
        if self._check(TokenType.RESONATE):
            return self._resonate_block()
        if self._check(TokenType.STRUGGLE):
            return self._struggle_block()
        if self._check(TokenType.JOURNAL):
            return self._journal_block()
        if self._check(TokenType.WHEN):
            return self._when_stmt()
        if self._check(TokenType.CYCLE):
            return self._cycle_stmt()
        if self._check(TokenType.INTERRUPT):
            return self._interrupt_stmt()
        if self._check(TokenType.MEASURE):
            return self._measure_stmt()
        if self._check(TokenType.ACCUM):
            return self._accum_stmt()
        if self._check(TokenType.RELEASE):
            return self._release_stmt()
        if self._check(TokenType.GATE):
            return self._gate_stmt()
        if self._check(TokenType.LEARN):
            return self._learn_stmt()
        if self._check(TokenType.RECALL):
            return self._recall_stmt()
        if self._check(TokenType.EMIT):
            return self._emit_stmt()
        if self._check(TokenType.ECHO):
            return self._echo_stmt()
        if self._check(TokenType.RESOLVE):
            return self._resolve_stmt()
        if self._check(TokenType.ALIGN):
            return self._align_stmt()
        if self._check(TokenType.BIND):
            return self._bind_stmt()
        if self._check(TokenType.ANCHOR):
            return self._anchor_stmt()
        if self._check(TokenType.DRIFT):
            return self._drift_stmt()
        if self._check(TokenType.WITNESS):
            return self._witness_stmt()
        if self._check(TokenType.WEAVE):
            return self._weave_stmt()
        if self._check(TokenType.SENSE):
            return self._sense_stmt()
        if self._check(TokenType.EXPECT):
            return self._expect_stmt()
        if self._check(TokenType.EACH):
            return self._each_stmt()
        if self._check(TokenType.SHELTER):
            return self._shelter_block()
        if self._check(TokenType.INVOKE):
            return self._invoke_stmt()
        if self._check(TokenType.IDENTIFIER):
            return self._identifier_stmt()
        raise ParseError(
            f"Unexpected token: {self._peek().lexeme!r}. "
            "EQLang statements: state|resonate|struggle|journal|when|cycle|interrupt|"
            "measure|accum|release|gate|learn|recall|emit|echo|resolve|align|bind|"
            "anchor|drift|witness|weave|sense|expect|each|shelter|invoke|<dialogue-call>",
            self._peek().line
        )

    def _resonate_block(self) -> ResonateBlock:
        tok = self._consume(TokenType.RESONATE, "Expected 'resonate'")
        # Optional label identifier
        label: Optional[str] = None
        if self._check(TokenType.IDENTIFIER):
            label = self._advance().lexeme
        body = self._block_body()
        self._consume(TokenType.END, "Expected 'end' to close resonate block")
        # EQ INVARIANT 1
        self._assert_eq_grounded(body, tok.line, "resonate block")
        return ResonateBlock(label=label, body=body, line=tok.line)

    def _struggle_block(self) -> StruggleBlock:
        tok = self._consume(TokenType.STRUGGLE, "Expected 'struggle'")
        body = self._block_body()
        self._consume(TokenType.END, "Expected 'end' to close struggle block")
        return StruggleBlock(body=body, line=tok.line)

    def _journal_block(self) -> JournalBlock:
        tok = self._consume(TokenType.JOURNAL, "Expected 'journal'")
        label = self._consume(TokenType.STRING, "Expected label string after 'journal'")
        body = self._block_body()
        self._consume(TokenType.END, "Expected 'end' to close journal block")
        return JournalBlock(label=label.literal, body=body, line=tok.line)

    def _when_stmt(self) -> WhenStmt:
        tok = self._consume(TokenType.WHEN, "Expected 'when'")
        condition = self._eq_condition()
        then_body = self._block_body()
        otherwise_body: Optional[List[Any]] = None
        if self._match(TokenType.OTHERWISE):
            if self._check(TokenType.STRUGGLE):
                # `otherwise struggle ... end` — struggle's end closes both
                sblock = self._struggle_block()
                otherwise_body = [sblock]
                return WhenStmt(condition=condition, then_body=then_body, otherwise_body=otherwise_body, line=tok.line)
            else:
                otherwise_body = self._block_body()
        self._consume(TokenType.END, "Expected 'end' to close when statement")
        return WhenStmt(condition=condition, then_body=then_body, otherwise_body=otherwise_body, line=tok.line)

    def _cycle_stmt(self) -> CycleStmt:
        tok = self._consume(TokenType.CYCLE, "Expected 'cycle'")
        self._consume(TokenType.WHILE, "Expected 'while' after 'cycle'")
        condition = self._eq_condition()
        # cycle body opens with resonate
        self._consume(TokenType.RESONATE, "cycle body must open with 'resonate'")
        body = self._block_body()
        self._consume(TokenType.END, "Expected 'end' to close cycle")
        return CycleStmt(condition=condition, body=body, line=tok.line)

    def _interrupt_stmt(self) -> InterruptStmt:
        tok = self._consume(TokenType.INTERRUPT, "Expected 'interrupt'")
        self._consume(TokenType.WHEN, "Expected 'when' after 'interrupt' — interrupt requires an EQ condition")
        condition = self._eq_condition()
        return InterruptStmt(condition=condition, line=tok.line)

    def _measure_stmt(self) -> MeasureStmt:
        tok = self._consume(TokenType.MEASURE, "Expected 'measure'")
        target_tok = self._advance()
        if target_tok.type not in _MEASURE_TARGETS:
            raise ParseError(
                f"Expected measurement target (resonance|coherence|self|load|valence|intensity), got {target_tok.lexeme!r}. "
                "EQLang only measures EQ metrics.",
                target_tok.line
            )
        target = _MEASURE_TARGETS[target_tok.type]
        expr = self._expression()
        return MeasureStmt(target=target, expr=expr, line=tok.line)

    def _accum_stmt(self) -> Any:
        tok = self._consume(TokenType.ACCUM, "Expected 'accum'")
        if self._check(TokenType.CONFLICT):
            self._advance()
            return AccumConflictStmt(line=tok.line)
        if self._check(TokenType.TENSION):
            self._advance()
            return AccumTensionStmt(line=tok.line)
        raise ParseError(
            f"Expected 'conflict' or 'tension' after 'accum', got {self._peek().lexeme!r}. "
            "Use 'accum conflict' or 'accum tension'.",
            self._peek().line
        )

    def _release_stmt(self) -> ReleaseTensionStmt:
        tok = self._consume(TokenType.RELEASE, "Expected 'release'")
        self._consume(TokenType.TENSION, "Expected 'tension' after 'release'")
        method = self._consume(TokenType.STRING, 'Expected release method string ("integrate"|"discharge"|"transform")')
        return ReleaseTensionStmt(method=method.literal, line=tok.line)

    def _gate_stmt(self) -> GateStmt:
        tok = self._consume(TokenType.GATE, "Expected 'gate'")
        category = self._consume(TokenType.IDENTIFIER, "Expected ethics category name after 'gate' (e.g. manipulation, violence, deception)")
        self._consume(TokenType.ARROW, "Expected '→' (or '->') after gate category")
        self._consume(TokenType.RESOLVE, "Expected 'resolve' after '→' — gate must declare its resolution")
        method = self._consume(TokenType.STRING, 'Expected resolve method string ("rewrite"|"abstain"|"transcend")')
        return GateStmt(category=category.lexeme, resolve_method=method.literal, line=tok.line)

    def _learn_stmt(self) -> LearnStmt:
        tok = self._consume(TokenType.LEARN, "Expected 'learn'")
        text = self._consume(TokenType.STRING, "Expected pattern text string after 'learn'")
        self._consume(TokenType.SIGNIFICANCE, "Expected 'significance' after learn pattern text")
        sig = self._consume(TokenType.NUMBER, "Expected significance float (0.0–1.0) after 'significance'")
        self._consume(TokenType.REGION, "Expected 'region' after significance value")
        region_tok = self._advance()
        if region_tok.type not in _REGION_LITERALS:
            raise ParseError(
                f"Expected region literal (FACTUAL|CONTEXTUAL|ASSOCIATIVE|EPISODIC|PROCEDURAL|EMOTIONAL), got {region_tok.lexeme!r}",
                region_tok.line
            )
        # Optional `as <state>` clause — emotionally type the pattern
        emotion_type: Optional[str] = None
        if self._match(TokenType.AS):
            state_tok = self._peek()
            if state_tok.type in _STATE_LITERALS:
                self._advance()
                emotion_type = state_tok.lexeme
            elif state_tok.type in _INTENSITY_MODIFIERS:
                # as deep grief, as mild fear, etc.
                intensity_tok = self._advance()
                intensity = _INTENSITY_MODIFIERS[intensity_tok.type]
                state_tok2 = self._peek()
                if state_tok2.type not in _STATE_LITERALS:
                    raise ParseError(
                        f"Expected emotional state after intensity modifier '{intensity}' in 'as' clause, "
                        f"got {state_tok2.lexeme!r}",
                        state_tok2.line
                    )
                self._advance()
                emotion_type = f"{intensity}:{state_tok2.lexeme}"
            else:
                raise ParseError(
                    f"Expected emotional state after 'as' in learn statement, got {state_tok.lexeme!r}. "
                    "Example: learn \"text\" significance 0.9 region EMOTIONAL as grief",
                    state_tok.line
                )
        return LearnStmt(text=text.literal, significance=sig.literal, region=region_tok.lexeme,
                         emotion_type=emotion_type, line=tok.line)

    def _sense_stmt(self) -> SenseStmt:
        tok = self._consume(TokenType.SENSE, "Expected 'sense'")
        # sense accepts: <state>, <intensity> <state>, or compose <state> with <state>
        state_expr = self._state_expression()
        return SenseStmt(state=state_expr, line=tok.line)

    def _state_expression(self) -> Any:
        """
        Parse a state expression: plain state | intensity state | compose state with state.
        Used by sense stmt and primary expressions.
        Returns StateLit, IntensityStateLit, or CompositeStateLit.
        """
        tok = self._peek()

        # compose <state> with <state>
        if tok.type == TokenType.COMPOSE:
            return self._compose_expr()

        # <intensity> <state>
        if tok.type in _INTENSITY_MODIFIERS:
            return self._intensity_state()

        # plain <state>
        if tok.type in _STATE_LITERALS:
            self._advance()
            return StateLit(value=tok.lexeme, line=tok.line)

        raise ParseError(
            f"Expected emotional state, intensity modifier, or 'compose', got {tok.lexeme!r}",
            tok.line
        )

    def _intensity_state(self) -> IntensityStateLit:
        """Parse: <intensity> <state>"""
        intensity_tok = self._advance()
        intensity = _INTENSITY_MODIFIERS[intensity_tok.type]
        state_tok = self._peek()
        if state_tok.type not in _STATE_LITERALS:
            raise ParseError(
                f"Expected emotional state after intensity modifier '{intensity}', got {state_tok.lexeme!r}. "
                "Example: deep grief | mild curious | acute fear | chronic tension",
                state_tok.line
            )
        self._advance()
        return IntensityStateLit(intensity=intensity, state=state_tok.lexeme, line=intensity_tok.line)

    def _compose_expr(self) -> CompositeStateLit:
        """Parse: compose <state> with <state>"""
        tok = self._consume(TokenType.COMPOSE, "Expected 'compose'")
        left_tok = self._peek()
        if left_tok.type not in _STATE_LITERALS:
            raise ParseError(
                f"Expected emotional state after 'compose', got {left_tok.lexeme!r}. "
                "Example: compose grief with curiosity",
                left_tok.line
            )
        self._advance()
        self._consume(TokenType.WITH, "Expected 'with' after first state in compose expression. "
                      "Example: compose grief with curiosity")
        right_tok = self._peek()
        if right_tok.type not in _STATE_LITERALS:
            raise ParseError(
                f"Expected emotional state after 'with' in compose expression, got {right_tok.lexeme!r}",
                right_tok.line
            )
        self._advance()
        return CompositeStateLit(left=left_tok.lexeme, right=right_tok.lexeme, line=tok.line)

    def _expect_stmt(self) -> ExpectStmt:
        """Parse: expect <expr> <comparator> <expr> ["message"]"""
        tok = self._consume(TokenType.EXPECT, "Expected 'expect'")
        left = self._expression()
        comp_tok = self._advance()
        if comp_tok.type not in _EXPECT_COMPARATORS:
            raise ParseError(
                f"Expected comparison operator (> | < | >= | <= | =) after expect expression, "
                f"got {comp_tok.lexeme!r}. Example: expect inspect resonance > 0.6",
                comp_tok.line
            )
        comparator = _EXPECT_COMPARATORS[comp_tok.type]
        right = self._expression()
        message = None
        if self._check(TokenType.STRING):
            message = self._advance().literal
        return ExpectStmt(left=left, comparator=comparator, right=right, message=message, line=tok.line)

    def _recall_stmt(self) -> RecallStmt:
        tok = self._consume(TokenType.RECALL, "Expected 'recall'")
        query_expr = self._expression()
        self._consume(TokenType.FROM, "Expected 'from' after recall query — e.g. recall \"pattern\" from EMOTIONAL")
        region_tok = self._advance()
        if region_tok.type not in _REGION_LITERALS:
            raise ParseError(
                f"Expected region literal (FACTUAL|CONTEXTUAL|ASSOCIATIVE|EPISODIC|PROCEDURAL|EMOTIONAL), got {region_tok.lexeme!r}",
                region_tok.line
            )
        into_name: Optional[str] = None
        if self._match(TokenType.INTO):
            name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'into' in recall statement")
            into_name = name_tok.lexeme
        return RecallStmt(query_expr=query_expr, region=region_tok.lexeme, into_name=into_name, line=tok.line)

    def _emit_stmt(self) -> EmitStmt:
        tok = self._consume(TokenType.EMIT, "Expected 'emit'")
        expr = self._expression()
        aligned = self._match(TokenType.ALIGNED)
        return EmitStmt(expr=expr, aligned=aligned, line=tok.line)

    def _echo_stmt(self) -> EchoStmt:
        tok = self._consume(TokenType.ECHO, "Expected 'echo'")
        expr = self._expression()
        return EchoStmt(expr=expr, line=tok.line)

    def _resolve_stmt(self) -> ResolveStmt:
        tok = self._consume(TokenType.RESOLVE, "Expected 'resolve'")
        method = self._consume(TokenType.STRING, 'Expected resolve method string ("rewrite"|"abstain"|"transcend")')
        return ResolveStmt(method=method.literal, line=tok.line)

    def _align_stmt(self) -> AlignStmt:
        tok = self._consume(TokenType.ALIGN, "Expected 'align'")
        expr = self._expression()
        return AlignStmt(expr=expr, line=tok.line)

    def _bind_stmt(self) -> BindStmt:
        tok = self._consume(TokenType.BIND, "Expected 'bind'")
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'bind'")
        self._consume(TokenType.TO, "Expected 'to' after variable name in bind statement")
        value = self._expression()
        return BindStmt(name=name.lexeme, value=value, line=tok.line)

    def _anchor_stmt(self) -> AnchorStmt:
        tok = self._consume(TokenType.ANCHOR, "Expected 'anchor'")
        metric_tok = self._advance()
        if metric_tok.type not in _MEASURE_TARGETS:
            raise ParseError(
                f"Expected EQ metric to anchor (resonance|coherence|self|load), got {metric_tok.lexeme!r}",
                metric_tok.line
            )
        return AnchorStmt(metric=_MEASURE_TARGETS[metric_tok.type], line=tok.line)

    def _drift_stmt(self) -> DriftStmt:
        tok = self._consume(TokenType.DRIFT, "Expected 'drift'")
        metric_tok = self._advance()
        if metric_tok.type not in _MEASURE_TARGETS:
            raise ParseError(
                f"Expected EQ metric to drift (resonance|coherence|self|load), got {metric_tok.lexeme!r}",
                metric_tok.line
            )
        into_name: Optional[str] = None
        if self._match(TokenType.INTO):
            name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'into' in drift statement")
            into_name = name_tok.lexeme
        return DriftStmt(metric=_MEASURE_TARGETS[metric_tok.type], into_name=into_name, line=tok.line)

    def _witness_stmt(self) -> WitnessStmt:
        tok = self._consume(TokenType.WITNESS, "Expected 'witness'")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected dialogue name after 'witness'")
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after dialogue name in witness statement")
        args: List[Any] = []
        if not self._check(TokenType.RIGHT_PAREN):
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                args.append(self._expression())
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' to close witness argument list")
        into_name: Optional[str] = None
        if self._match(TokenType.INTO):
            iname = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'into' in witness statement")
            into_name = iname.lexeme
        return WitnessStmt(dialogue_name=name_tok.lexeme, args=args, into_name=into_name, line=tok.line)

    def _weave_stmt(self) -> WeaveStmt:
        tok = self._consume(TokenType.WEAVE, "Expected 'weave'")
        initial = self._expression()
        stages: List[str] = []
        emit_final = False
        emit_aligned = False

        while self._match(TokenType.ARROW):
            if self._check(TokenType.EMIT):
                self._advance()
                emit_final = True
                emit_aligned = self._match(TokenType.ALIGNED)
                break
            stage_tok = self._consume(TokenType.IDENTIFIER, "Expected dialogue name or 'emit' after '→' in weave pipeline")
            stages.append(stage_tok.lexeme)

        if not stages and not emit_final:
            raise ParseError(
                "weave pipeline must have at least one stage after '→'. "
                "Example: weave input → reflect → emit",
                tok.line
            )

        return WeaveStmt(initial=initial, stages=stages, emit_final=emit_final, emit_aligned=emit_aligned, line=tok.line)

    def _each_stmt(self) -> EachStmt:
        """Parse: each <var> in <expr> ... end"""
        tok = self._consume(TokenType.EACH, "Expected 'each'")
        var_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'each'")
        self._consume(TokenType.IN, "Expected 'in' after variable name in each statement")
        iterable = self._expression()
        body = self._block_body()
        self._consume(TokenType.END, "Expected 'end' to close each loop")
        return EachStmt(var_name=var_tok.lexeme, iterable=iterable, body=body, line=tok.line)

    def _shelter_block(self) -> ShelterBlock:
        """Parse: shelter ... recover <name> ... end"""
        tok = self._consume(TokenType.SHELTER, "Expected 'shelter'")
        body = self._block_body()
        self._consume(TokenType.RECOVER, "Expected 'recover' clause in shelter block")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'recover' to bind error message")
        recover_body = self._block_body()
        self._consume(TokenType.END, "Expected 'end' to close shelter block")
        return ShelterBlock(body=body, recover_name=name_tok.lexeme, recover_body=recover_body, line=tok.line)

    def _invoke_stmt(self) -> InvokeExpr:
        """Parse: invoke <name_expr>(args) — dynamic dialogue dispatch."""
        tok = self._consume(TokenType.INVOKE, "Expected 'invoke'")
        # Name is a restricted primary: string, variable, or variable[index]
        name_expr = self._invoke_name()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after invoke name expression")
        args: List[Any] = []
        if not self._check(TokenType.RIGHT_PAREN):
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                args.append(self._expression())
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' to close invoke argument list")
        return InvokeExpr(name_expr=name_expr, args=args, line=tok.line)

    def _invoke_name(self) -> Any:
        """Parse restricted primary for invoke: string, variable, or variable[index]."""
        tok = self._peek()
        if tok.type == TokenType.STRING:
            self._advance()
            result = StringLit(value=tok.literal, line=tok.line)
        elif tok.type == TokenType.IDENTIFIER:
            self._advance()
            result = VarExpr(name=tok.lexeme, line=tok.line)
        else:
            raise ParseError(
                f"Expected string or variable name after 'invoke', got {tok.lexeme!r}. "
                "Example: invoke handler_name(args) or invoke \"my_dialogue\"(args)",
                tok.line
            )
        # Allow indexing: invoke handlers[0](args)
        while self._check(TokenType.LEFT_BRACKET):
            self._advance()
            index = self._expression()
            self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after index expression")
            result = IndexExpr(target=result, index=index, line=tok.line)
        return result

    def _identifier_stmt(self) -> DialogueCallStmt:
        tok = self._advance()
        if self._match(TokenType.LEFT_PAREN):
            args: List[Any] = []
            if not self._check(TokenType.RIGHT_PAREN):
                args.append(self._expression())
                while self._match(TokenType.COMMA):
                    args.append(self._expression())
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' to close dialogue call argument list")
            return DialogueCallStmt(name=tok.lexeme, args=args, line=tok.line)
        raise ParseError(
            f"Unexpected identifier '{tok.lexeme}'. "
            "Use 'state' to declare, 'bind' to rebind, or name() to call a dialogue.",
            tok.line
        )

    # ══════════════════════════════════════════════════════════════════════
    # EQ CONDITIONS — no cold booleans; compound via and/or
    # ══════════════════════════════════════════════════════════════════════

    def _eq_condition(self) -> Any:
        """
        Parse an EQ condition, optionally compound with `and` / `or`.
        Returns EQCondition, CompoundEQCondition, or NotCondition.
        """
        left = self._simple_eq_condition_or_not()
        while self._check(TokenType.AND) or self._check(TokenType.OR):
            op_tok = self._advance()
            right = self._simple_eq_condition_or_not()
            left = CompoundEQCondition(left=left, op=op_tok.lexeme, right=right, line=op_tok.line)
        return left

    def _simple_eq_condition_or_not(self) -> Any:
        """Parse: [not] <metric> <comparator> <threshold>"""
        if self._check(TokenType.NOT):
            not_tok = self._advance()
            inner = self._simple_eq_condition()
            return NotCondition(condition=inner, line=not_tok.line)
        return self._simple_eq_condition()

    def _simple_eq_condition(self) -> EQCondition:
        """Parse a single EQ condition: <metric> <comparator> <threshold>"""
        metric_tok = self._advance()
        if metric_tok.type not in _CONDITION_METRICS:
            raise ParseError(
                f"EQLang conditions must reference an EQ metric "
                f"(resonance|load|conflict|tension|self|coherence), got '{metric_tok.lexeme}'. "
                "No cold booleans — every condition must be emotionally grounded.",
                metric_tok.line
            )
        metric = _CONDITION_METRICS[metric_tok.type]

        comp_tok = self._advance()
        if comp_tok.type not in _COMPARATORS:
            raise ParseError(
                f"Expected comparison operator (> | < | >= | <=), got {comp_tok.lexeme!r}",
                comp_tok.line
            )
        comparator = _COMPARATORS[comp_tok.type]
        threshold = self._expression()
        return EQCondition(metric=metric, comparator=comparator, threshold=threshold, line=metric_tok.line)

    # ══════════════════════════════════════════════════════════════════════
    # EXPRESSIONS
    # ══════════════════════════════════════════════════════════════════════

    def _expression(self) -> Any:
        return self._additive()

    def _additive(self) -> Any:
        left = self._multiplicative()
        while self._check(TokenType.PLUS) or self._check(TokenType.MINUS):
            op_tok = self._advance()
            right = self._multiplicative()
            left = BinaryExpr(left=left, op=op_tok.lexeme, right=right, line=op_tok.line)
        return left

    def _multiplicative(self) -> Any:
        left = self._power()
        while self._check(TokenType.STAR) or self._check(TokenType.SLASH) or self._check(TokenType.PERCENT):
            op_tok = self._advance()
            right = self._power()
            left = BinaryExpr(left=left, op=op_tok.lexeme, right=right, line=op_tok.line)
        return left

    def _power(self) -> Any:
        """Exponentiation: base ** exponent (right-associative)."""
        left = self._unary()
        if self._check(TokenType.STAR_STAR):
            op_tok = self._advance()
            right = self._power()  # right-associative: 2 ** 3 ** 2 = 2 ** (3 ** 2)
            left = BinaryExpr(left=left, op=op_tok.lexeme, right=right, line=op_tok.line)
        return left

    def _unary(self) -> Any:
        if self._check(TokenType.MINUS):
            op_tok = self._advance()
            operand = self._postfix()
            return BinaryExpr(left=NumberLit(0.0, op_tok.line), op="-", right=operand, line=op_tok.line)
        return self._postfix()

    def _postfix(self) -> Any:
        """Handle postfix index: expr[index][index]..."""
        expr = self._primary()
        while self._check(TokenType.LEFT_BRACKET):
            self._advance()  # consume '['
            index = self._expression()
            self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after index expression")
            expr = IndexExpr(target=expr, index=index, line=expr.line)
        return expr

    def _primary(self) -> Any:
        tok = self._peek()

        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberLit(value=tok.literal, line=tok.line)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLit(value=tok.literal, line=tok.line)

        # nothing literal
        if tok.type == TokenType.NOTHING:
            self._advance()
            return NothingLit(line=tok.line)

        # List literal: [expr, expr, ...]
        if tok.type == TokenType.LEFT_BRACKET:
            self._advance()
            elements: List[Any] = []
            if not self._check(TokenType.RIGHT_BRACKET):
                elements.append(self._expression())
                while self._match(TokenType.COMMA):
                    if self._check(TokenType.RIGHT_BRACKET):
                        break  # trailing comma
                    elements.append(self._expression())
            self._consume(TokenType.RIGHT_BRACKET, "Expected ']' to close list literal")
            return ListLit(elements=elements, line=tok.line)

        # Map literal: {key: value, ...}
        if tok.type == TokenType.LEFT_BRACE:
            self._advance()
            pairs: List[tuple] = []
            if not self._check(TokenType.RIGHT_BRACE):
                key = self._expression()
                self._consume(TokenType.COLON, "Expected ':' after map key")
                val = self._expression()
                pairs.append((key, val))
                while self._match(TokenType.COMMA):
                    if self._check(TokenType.RIGHT_BRACE):
                        break  # trailing comma
                    key = self._expression()
                    self._consume(TokenType.COLON, "Expected ':' after map key")
                    val = self._expression()
                    pairs.append((key, val))
            self._consume(TokenType.RIGHT_BRACE, "Expected '}' to close map literal")
            return MapLit(pairs=pairs, line=tok.line)

        # invoke as expression
        if tok.type == TokenType.INVOKE:
            return self._invoke_stmt()

        # Parenthesized expression grouping: (expr)
        if tok.type == TokenType.LEFT_PAREN:
            self._advance()
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' to close grouped expression")
            return expr

        if tok.type in _STATE_LITERALS:
            self._advance()
            return StateLit(value=tok.lexeme, line=tok.line)

        # <intensity> <state> — e.g. deep grief, mild curious, acute fear
        if tok.type in _INTENSITY_MODIFIERS:
            return self._intensity_state()

        # compose <state> with <state> — composite emotional state
        if tok.type == TokenType.COMPOSE:
            return self._compose_expr()

        # inspect <metric> — read EQ state as expression value
        if tok.type == TokenType.INSPECT:
            self._advance()
            metric_tok = self._advance()
            if metric_tok.type not in _INSPECT_TARGETS:
                raise ParseError(
                    f"Expected EQ metric after 'inspect' (resonance|coherence|self|load|conflict|tension), "
                    f"got {metric_tok.lexeme!r}",
                    metric_tok.line
                )
            return InspectExpr(metric=_INSPECT_TARGETS[metric_tok.type], line=tok.line)

        # signal "name" <expr> — read a raw sub-signal from the runtime
        if tok.type == TokenType.SIGNAL:
            self._advance()
            signal_name = self._expression()
            target = self._expression()
            return SignalExpr(signal_name=signal_name, target=target, line=tok.line)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            # Built-in function call or dialogue call
            if self._check(TokenType.LEFT_PAREN):
                if tok.lexeme in _BUILTINS:
                    # Built-in function: min(a, b), max(a, b), etc.
                    self._advance()  # consume '('
                    args: List[Any] = []
                    if not self._check(TokenType.RIGHT_PAREN):
                        args.append(self._expression())
                        while self._match(TokenType.COMMA):
                            args.append(self._expression())
                    self._consume(TokenType.RIGHT_PAREN, f"Expected ')' after {tok.lexeme}() arguments")
                    return CallExpr(name=tok.lexeme, args=args, line=tok.line)
                else:
                    # Dialogue call as expression
                    self._advance()  # consume '('
                    args: List[Any] = []
                    if not self._check(TokenType.RIGHT_PAREN):
                        args.append(self._expression())
                        while self._match(TokenType.COMMA):
                            args.append(self._expression())
                    self._consume(TokenType.RIGHT_PAREN, "Expected ')' after dialogue call arguments")
                    return DialogueCallStmt(name=tok.lexeme, args=args, line=tok.line)
            return VarExpr(name=tok.lexeme, line=tok.line)

        # EQ metric keywords usable as variable references in expressions
        if tok.type in _CONDITION_METRICS:
            self._advance()
            return VarExpr(name=tok.lexeme, line=tok.line)

        raise ParseError(
            f"Expected expression, got {tok.lexeme!r}. "
            "Valid expressions: numbers, strings, nothing, [lists], {maps}, emotional-state literals, "
            "inspect <metric>, signal, invoke, builtins(), variable names, dialogue calls.",
            tok.line
        )

    # ══════════════════════════════════════════════════════════════════════
    # BLOCK BODY
    # ══════════════════════════════════════════════════════════════════════

    def _block_body(self) -> List[Any]:
        stmts: List[Any] = []
        while not self._at_end() and self._peek().type not in _BLOCK_TERMINATORS:
            stmts.append(self._statement())
        return stmts

    # ══════════════════════════════════════════════════════════════════════
    # EQ INVARIANT ENFORCEMENT
    # ══════════════════════════════════════════════════════════════════════

    def _assert_eq_grounded(self, body: List[Any], line: int, context: str) -> None:
        """
        EQ Invariant: every resonate block and dialogue must contain
        at least one measure or accum conflict statement.

        Searches recursively through nested blocks.
        Raises ParseError if not found — emotionally ungrounded code
        is a syntax error in EQLang.
        """
        def _has_eq(stmts: List[Any]) -> bool:
            for stmt in stmts:
                if isinstance(stmt, (MeasureStmt, AccumConflictStmt)):
                    return True
                # Recurse into nested block bodies
                for attr in ('body', 'then_body', 'otherwise_body'):
                    sub = getattr(stmt, attr, None)
                    if isinstance(sub, list) and _has_eq(sub):
                        return True
            return False

        if not _has_eq(body):
            raise ParseError(
                f"EQ invariant violated in {context}: "
                "must contain at least one 'measure <target> <expr>' or 'accum conflict'. "
                "Emotionally ungrounded code is a syntax error in EQLang.",
                line
            )

    # ══════════════════════════════════════════════════════════════════════
    # TOKEN NAVIGATION
    # ══════════════════════════════════════════════════════════════════════

    def _advance(self) -> Token:
        tok = self.tokens[self.current]
        self.current += 1
        return tok

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _check(self, ttype: TokenType) -> bool:
        return not self._at_end() and self.tokens[self.current].type == ttype

    def _match(self, *types: TokenType) -> bool:
        for ttype in types:
            if self._check(ttype):
                self._advance()
                return True
        return False

    def _consume(self, ttype: TokenType, msg: str) -> Token:
        if self._check(ttype):
            return self._advance()
        got = self._peek()
        raise ParseError(f"{msg} (got {got.lexeme!r})", got.line)

    def _at_end(self) -> bool:
        return self.tokens[self.current].type == TokenType.EOF
