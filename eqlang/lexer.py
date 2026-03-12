"""
EQLang Lexer — Scans EQLang source text into a flat token stream. v0.5.0

Handles:
  - Unicode arrow → (also accepts ASCII ->)
  - All EQLang keywords (completely disconnected from other langs)
  - Float and integer number literals
  - Double-quoted strings with escape sequences
  - Single-line comments via # (for human tooling; echo is the EQLang form)
  - Block comments via #{ ... }# (multi-line)
  - Multiline source with line tracking
  - List/map/index punctuation: [ ] { } :

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

from typing import List
from .tokens import Token, TokenType


class LexerError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"[Line {line}] Lexer Error: {message}")
        self.line = line


# All EQLang keywords — maps source text → TokenType
KEYWORDS: dict = {
    # Structural
    "resonate":    TokenType.RESONATE,
    "struggle":    TokenType.STRUGGLE,
    "end":         TokenType.END,
    "resolve":     TokenType.RESOLVE,
    # Declarations
    "session":     TokenType.SESSION,
    "state":       TokenType.STATE,
    "bind":        TokenType.BIND,
    "to":          TokenType.TO,
    "dialogue":    TokenType.DIALOGUE,
    "threshold":   TokenType.THRESHOLD,
    "include":     TokenType.INCLUDE,
    # Control flow
    "when":        TokenType.WHEN,
    "otherwise":   TokenType.OTHERWISE,
    "cycle":       TokenType.CYCLE,
    "interrupt":   TokenType.INTERRUPT,
    "while":       TokenType.WHILE,
    # Compound condition operators
    "and":         TokenType.AND,
    "or":          TokenType.OR,
    # EQ primitives
    "measure":     TokenType.MEASURE,
    "accum":       TokenType.ACCUM,
    "conflict":    TokenType.CONFLICT,
    "tension":     TokenType.TENSION,
    "release":     TokenType.RELEASE,
    "gate":        TokenType.GATE,
    "learn":       TokenType.LEARN,
    "recall":      TokenType.RECALL,
    "from":        TokenType.FROM,
    "into":        TokenType.INTO,
    "as":          TokenType.AS,
    "significance": TokenType.SIGNIFICANCE,
    "region":      TokenType.REGION,
    "emit":        TokenType.EMIT,
    "aligned":     TokenType.ALIGNED,
    "echo":        TokenType.ECHO,
    "align":       TokenType.ALIGN,
    "inspect":     TokenType.INSPECT,
    "anchor":      TokenType.ANCHOR,
    "drift":       TokenType.DRIFT,
    "witness":     TokenType.WITNESS,
    "weave":       TokenType.WEAVE,
    "journal":     TokenType.JOURNAL,
    "sense":       TokenType.SENSE,
    "compose":     TokenType.COMPOSE,
    "with":        TokenType.WITH,
    "signal":      TokenType.SIGNAL,
    "expect":      TokenType.EXPECT,
    # EQ metrics
    "resonance":   TokenType.RESONANCE,
    "coherence":   TokenType.COHERENCE,
    "self":        TokenType.SELF,
    "load":        TokenType.LOAD,
    "valence":     TokenType.VALENCE,
    "intensity":   TokenType.INTENSITY,
    # Intensity modifier prefixes
    "deep":        TokenType.DEEP,
    "mild":        TokenType.MILD,
    "acute":       TokenType.ACUTE,
    "chronic":     TokenType.CHRONIC,
    # Core emotional state literals
    "tilt":        TokenType.TILT,
    "focused":     TokenType.FOCUSED,
    "conflicted":  TokenType.CONFLICTED_LIT,
    "transcendent": TokenType.TRANSCENDENT_LIT,
    # Extended emotional state literals (v0.2.0)
    "grounded":    TokenType.GROUNDED,
    "hollow":      TokenType.HOLLOW,
    "radiant":     TokenType.RADIANT,
    "fractured":   TokenType.FRACTURED,
    "overwhelmed": TokenType.OVERWHELMED,
    "curious":     TokenType.CURIOUS,
    "present":     TokenType.PRESENT,
    "expanded":    TokenType.EXPANDED,
    "grief":       TokenType.GRIEF,
    "numb":        TokenType.NUMB,
    # Plutchik primary emotional states (v0.3.0)
    "joy":         TokenType.JOY,
    "trust":       TokenType.TRUST,
    "fear":        TokenType.FEAR,
    "surprise":    TokenType.SURPRISE,
    "sadness":     TokenType.SADNESS,
    "disgust":     TokenType.DISGUST,
    "anger":       TokenType.ANGER,
    "anticipation": TokenType.ANTICIPATION,
    # Plutchik dyad states (v0.3.0)
    "love":        TokenType.LOVE,
    "awe":         TokenType.AWE,
    "remorse":     TokenType.REMORSE,
    "contempt":    TokenType.CONTEMPT,
    "optimism":    TokenType.OPTIMISM,
    "submission":  TokenType.SUBMISSION,
    "disapproval": TokenType.DISAPPROVAL,
    "aggressiveness": TokenType.AGGRESSIVENESS,
    # Nuanced emotional states (v0.3.0)
    "shame":       TokenType.SHAME,
    "guilt":       TokenType.GUILT,
    "pride":       TokenType.PRIDE,
    "envy":        TokenType.ENVY,
    "compassion":  TokenType.COMPASSION,
    "gratitude":   TokenType.GRATITUDE,
    "longing":     TokenType.LONGING,
    "wonder":      TokenType.WONDER,
    "serenity":    TokenType.SERENITY,
    "apprehension": TokenType.APPREHENSION,
    "despair":     TokenType.DESPAIR,
    "elation":     TokenType.ELATION,
    "tender":      TokenType.TENDER,
    "vulnerable":  TokenType.VULNERABLE,
    "protective":  TokenType.PROTECTIVE,
    "detached":    TokenType.DETACHED,
    "absorbed":    TokenType.ABSORBED,
    "yearning":    TokenType.YEARNING,
    "acceptance":  TokenType.ACCEPTANCE,
    "pensiveness": TokenType.PENSIVENESS,
    "boredom":     TokenType.BOREDOM,
    "annoyance":   TokenType.ANNOYANCE,
    # Additional control flow (v0.5.0)
    "each":        TokenType.EACH,
    "in":          TokenType.IN,
    # Condition negation (v0.5.0)
    "not":         TokenType.NOT,
    # Error handling & dynamic dispatch (v0.5.0)
    "shelter":     TokenType.SHELTER,
    "recover":     TokenType.RECOVER,
    "invoke":      TokenType.INVOKE,
    # Nothing literal (v0.5.0)
    "nothing":     TokenType.NOTHING,
    # Region literals (UPPER_CASE in .eql source)
    "FACTUAL":     TokenType.FACTUAL,
    "CONTEXTUAL":  TokenType.CONTEXTUAL,
    "ASSOCIATIVE": TokenType.ASSOCIATIVE,
    "EPISODIC":    TokenType.EPISODIC,
    "PROCEDURAL":  TokenType.PROCEDURAL,
    "EMOTIONAL":   TokenType.EMOTIONAL_REGION,
}


class Lexer:
    """
    Scans EQLang source into tokens.

    Usage:
        tokens = Lexer(source).scan_tokens()
    """

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        while not self._at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def _scan_token(self):
        c = self._advance()

        # Whitespace
        if c in (' ', '\r', '\t'):
            return
        if c == '\n':
            self.line += 1
            return

        # Comments: single-line (#) or block (#{...}#)
        if c == '#':
            if self._peek() == '{':
                self._advance()  # consume '{'
                self._block_comment()
            else:
                while self._peek() != '\n' and not self._at_end():
                    self._advance()
            return

        # Single-char tokens
        if c == '(':
            self._add_token(TokenType.LEFT_PAREN)
        elif c == ')':
            self._add_token(TokenType.RIGHT_PAREN)
        elif c == ',':
            self._add_token(TokenType.COMMA)
        elif c == '+':
            self._add_token(TokenType.PLUS)
        elif c == '*':
            self._add_token(TokenType.STAR_STAR if self._match('*') else TokenType.STAR)
        elif c == '%':
            self._add_token(TokenType.PERCENT)
        elif c == '/':
            if self._peek() == '/':
                # // single-line comment (C-style, also valid in EQLang)
                while self._peek() != '\n' and not self._at_end():
                    self._advance()
            else:
                self._add_token(TokenType.SLASH)
        elif c == '=':
            self._add_token(TokenType.EQUAL)
        # List/map/index punctuation
        elif c == '[':
            self._add_token(TokenType.LEFT_BRACKET)
        elif c == ']':
            self._add_token(TokenType.RIGHT_BRACKET)
        elif c == '{':
            self._add_token(TokenType.LEFT_BRACE)
        elif c == '}':
            self._add_token(TokenType.RIGHT_BRACE)
        elif c == ':':
            self._add_token(TokenType.COLON)

        # Comparison operators
        elif c == '>':
            self._add_token(TokenType.GREATER_EQ if self._match('=') else TokenType.GREATER)
        elif c == '<':
            self._add_token(TokenType.LESS_EQ if self._match('=') else TokenType.LESS)

        # Minus or ASCII arrow ->
        elif c == '-':
            if self._match('>'):
                self._add_token(TokenType.ARROW)
            else:
                self._add_token(TokenType.MINUS)

        # Unicode arrow →
        elif c == '\u2192':
            self._add_token(TokenType.ARROW)

        # String literals
        elif c == '"':
            self._string()

        # Number literals
        elif c.isdigit():
            self._number()

        # Identifiers and keywords
        elif c.isalpha() or c == '_':
            self._identifier()

        else:
            raise LexerError(
                f"Unexpected character: {c!r} (ord={ord(c)}). "
                "EQLang uses its own token set — check your syntax.",
                self.line
            )

    def _block_comment(self):
        """Scan a block comment: #{ ... }#. Tracks newlines."""
        start_line = self.line
        while not self._at_end():
            if self._peek() == '\n':
                self.line += 1
            if self._peek() == '}' and self._peek_next() == '#':
                self._advance()  # consume '}'
                self._advance()  # consume '#'
                return
            self._advance()
        raise LexerError("Unterminated block comment (opened with '#{', expected '}#')", start_line)

    def _string(self):
        while self._peek() != '"' and not self._at_end():
            if self._peek() == '\n':
                self.line += 1
            # Basic escape handling
            if self._peek() == '\\' and self._peek_next() in ('"', '\\', 'n', 't'):
                self._advance()
            self._advance()

        if self._at_end():
            raise LexerError("Unterminated string literal", self.line)

        self._advance()  # consume closing "
        # Trim surrounding quotes; handle basic escapes
        raw = self.source[self.start + 1: self.current - 1]
        value = raw.replace('\\\\', '\\').replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        self._add_token(TokenType.STRING, value)

    def _number(self):
        while self._peek().isdigit():
            self._advance()
        if self._peek() == '.' and self._peek_next().isdigit():
            self._advance()  # consume '.'
            while self._peek().isdigit():
                self._advance()
        value = float(self.source[self.start:self.current])
        self._add_token(TokenType.NUMBER, value)

    def _identifier(self):
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()
        text = self.source[self.start:self.current]
        ttype = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._add_token(ttype)

    # ── Token helpers ──────────────────────────────────────────────────────

    def _add_token(self, ttype: TokenType, literal=None):
        lexeme = self.source[self.start:self.current]
        self.tokens.append(Token(ttype, lexeme, literal, self.line))

    def _advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        return c

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        return '\0' if self._at_end() else self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _at_end(self) -> bool:
        return self.current >= len(self.source)
