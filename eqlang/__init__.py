"""
EQLang — The Emotional Quotient Language. v0.5.0

A first-class EQ programming language where resonance, conflict,
self-dialogue, valence, intensity, and ethics gates are syntax primitives,
not library calls.

Core invariants (enforced at parse time):
  1. Every `resonate` block must contain >=1 `measure` or `accum conflict`
  2. Every `dialogue` must end with `end resolve`
  3. Every `when` / `cycle` / `interrupt` condition must reference an EQ metric
  4. `gate` must declare its resolution method inline

New in v0.5.0 — Data Structures, Error Handling & Full Builtins:
  - nothing literal — explicit absence value
  - Block comments: #{ ... }# — multi-line
  - Lists: [a, b, c] — immutable ordered collections, indexable
  - Maps: {"key": val} — immutable key-value dictionaries
  - Each loop: each x in list ... end — iterate lists
  - Condition negation: not — prefix negation for EQ conditions
  - Error handling: shelter ... recover err ... end
  - Dynamic dispatch: invoke name(args) — call dialogues by computed name
  - Recursion protection: MAX_CALL_DEPTH = 100
  - String builtins: slice, find, replace, split, join, upper, lower, trim, starts_with, ends_with
  - Collection builtins: contains, push, pop, range, sort, reverse, index_of, flatten
  - Map builtins: keys, values, has_key
  - Type builtins: type, is_nothing, is_number, is_string, is_list, is_map, to_number
  - Mutation: set_at(col, key_or_idx, val) — returns new collection

New in v0.4.0 — Arithmetic Completeness + Signal Access:
  - Operators: % (modulo), ** (exponentiation), () (parenthesized grouping)
  - Math builtins: min, max, clamp, abs, round, sqrt, pow, floor, ceil, log
  - String builtins: len, str, concat
  - Signal access: signal "name" <expr> — read raw sub-signals from runtime

New in v0.3.0 — Full Emotional Spectrum:
  - 28 new emotional state literals (43 total)
  - Intensity modifiers: deep grief | mild curious | acute fear | chronic tension
  - Composite states: compose grief with curious
  - New EQ metrics: valence [-1.0, 1.0] and intensity [0.0, 1.0]
  - Emotional context: sense <state>
  - Typed memory: learn ... as <state>

Quick start:
    from eqlang import run_string, run_file

    run_string('''
    session "demo"
    threshold presence = 0.7
    state message = "hello from EQLang"
    resonate entry
      measure resonance message
      accum conflict
      when resonance > presence
        emit message aligned
      end
    end
    ''')

    run_file("script.eql")

Custom runtime:
    from eqlang import EQLangInterpreter
    from eqlang.runtime import StandardRuntime

    runtime = StandardRuntime()
    interpreter = EQLangInterpreter(runtime=runtime, verbose=True)
    from eqlang import Lexer, Parser
    tokens = Lexer(source).scan_tokens()
    program = Parser(tokens).parse()
    results = interpreter.interpret(program)

Production runtimes (LASRuntime, LuciHTTPRuntime, EQEngineRuntime)
are available with a Luci API key at https://useluci.com

Theory: C+CT (Consciousness + Conflict Theory) — Intent-First Alignment
Author: Bryan Camilo German
License: MIT (EQLang Core)
"""

import os
from .lexer import Lexer, LexerError
from .parser import Parser, ParseError
from .interpreter import EQLangInterpreter, EQLangError
from .runtime.base import EQRuntime, EQRuntimeError
from .runtime.standard_runtime import StandardRuntime
from .runtime.mock_runtime import MockRuntime

__version__ = "0.5.0"
__language__ = "EQLang — Emotional Quotient Language"
__author__ = "Bryan Camilo German"
__theory__ = "C+CT (Consciousness + Conflict Theory) — Intent-First Alignment"
__license__ = "MIT"


def run_string(
    source: str,
    runtime: EQRuntime = None,
    verbose: bool = True,
    include_dirs: list = None,
) -> list:
    """
    Parse and run EQLang source text.

    Args:
        source:       EQLang source code string
        runtime:      EQRuntime adapter. Defaults to StandardRuntime (heuristic,
                      no API needed). For production LAS alignment, use LASRuntime
                      or LuciHTTPRuntime (available with a Luci API key).
        verbose:      Print live execution trace to stdout.
        include_dirs: Directories to search for include "file.eql" paths.

    Returns:
        List of all values emitted by the script (in order).

    Raises:
        LexerError:   Unrecognized character in source
        ParseError:   Syntax or EQ invariant violation
        EQLangError:  Runtime error (undefined variable, conflict overload, etc.)
    """
    if runtime is None:
        runtime = StandardRuntime()

    tokens = Lexer(source).scan_tokens()
    program = Parser(tokens).parse()
    interpreter = EQLangInterpreter(
        runtime=runtime, verbose=verbose, include_dirs=include_dirs or ["."]
    )
    return interpreter.interpret(program)


def run_file(
    path: str,
    runtime: EQRuntime = None,
    verbose: bool = True,
    include_dirs: list = None,
) -> list:
    """
    Load and run a .eql file.

    Args:
        path:         Path to .eql script file
        runtime:      EQRuntime adapter (see run_string)
        verbose:      Print live execution trace to stdout.
        include_dirs: Additional directories to search for include paths.
                      The file's directory is always included automatically.

    Returns:
        List of all values emitted by the script (in order).
    """
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    file_dir = os.path.dirname(os.path.abspath(path))
    dirs = [file_dir] + (include_dirs or [])
    return run_string(source, runtime=runtime, verbose=verbose, include_dirs=dirs)


__all__ = [
    # Core pipeline
    "Lexer", "LexerError",
    "Parser", "ParseError",
    "EQLangInterpreter", "EQLangError",
    # Runtime adapters (MIT)
    "EQRuntime", "EQRuntimeError", "StandardRuntime", "MockRuntime",
    # Convenience runners
    "run_string", "run_file",
    # Metadata
    "__version__", "__language__", "__author__", "__theory__", "__license__",
]
