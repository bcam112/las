"""
EQLang CLI entry point. v0.5.0

Usage:
    python -m eqlang script.eql
    python -m eqlang script.eql --runtime standard    (default, no API needed)
    python -m eqlang script.eql --runtime mock
    python -m eqlang script.eql --runtime http --base-url https://api.usecami.com/v1
    python -m eqlang --repl
    python -m eqlang --version

Copyright (c) 2026 Bryan Camilo German — MIT License (EQLang Core)
"""

import sys
import argparse
import json


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="eqlang",
        description="EQLang v0.5.0 — Emotional Quotient Language interpreter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m eqlang hello_world.eql
  python -m eqlang script.eql --runtime standard    (default, no API needed)
  python -m eqlang script.eql --runtime mock
  python -m eqlang script.eql --runtime http --base-url https://api.usecami.com/v1
  python -m eqlang script.eql --quiet
  python -m eqlang script.eql --dump-ast
  python -m eqlang --repl
  python -m eqlang --repl --runtime mock
        """,
    )

    ap.add_argument("file", nargs="?", help=".eql script to run")
    ap.add_argument(
        "--runtime",
        choices=["standard", "mock", "http"],
        default="standard",
        help="EQ runtime adapter (default: standard — heuristic, no API needed)",
    )
    ap.add_argument(
        "--base-url",
        default="https://api.usecami.com/v1",
        help="Base URL for HTTP runtime",
    )
    ap.add_argument("--api-key", default="", help="API key for HTTP runtime")
    ap.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress live execution trace",
    )
    ap.add_argument(
        "--dump-ast",
        action="store_true",
        help="Print AST and exit without running",
    )
    ap.add_argument(
        "--dump-tokens",
        action="store_true",
        help="Print token stream and exit without parsing",
    )
    ap.add_argument(
        "--repl",
        action="store_true",
        help="Launch interactive EQLang REPL",
    )
    ap.add_argument("--version", action="store_true", help="Print EQLang version")
    args = ap.parse_args()

    if args.version:
        from . import __version__, __language__, __theory__
        print(f"{__language__} v{__version__}")
        print(f"Theory: {__theory__}")
        return

    # Build runtime
    from .runtime import StandardRuntime, MockRuntime

    def build_runtime(quiet=False):
        if args.runtime == "mock":
            return MockRuntime()
        elif args.runtime == "http":
            try:
                from eqlang.runtime.http_runtime import LuciHTTPRuntime
                return LuciHTTPRuntime(base_url=args.base_url, api_key=args.api_key)
            except ImportError:
                if not quiet:
                    print("[info] LuciHTTPRuntime requires a Luci API key — see useluci.com")
                return StandardRuntime()
        else:
            return StandardRuntime()

    # REPL mode
    if args.repl:
        runtime = build_runtime(quiet=args.quiet)
        _run_repl(runtime, verbose=not args.quiet)
        return

    if not args.file:
        ap.print_help()
        sys.exit(1)

    # Load source
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"[EQLang] File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"[EQLang] Cannot read {args.file}: {e}", file=sys.stderr)
        sys.exit(1)

    from .lexer import Lexer, LexerError
    from .parser import Parser, ParseError
    from .interpreter import EQLangInterpreter, EQLangError

    # Token dump mode
    if args.dump_tokens:
        try:
            tokens = Lexer(source).scan_tokens()
            for tok in tokens:
                print(tok)
        except LexerError as e:
            print(f"[LexerError] {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Parse
    try:
        tokens = Lexer(source).scan_tokens()
        program = Parser(tokens).parse()
    except LexerError as e:
        print(f"[LexerError] {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"[ParseError] {e}", file=sys.stderr)
        sys.exit(1)

    # AST dump mode
    if args.dump_ast:
        import dataclasses
        def _to_dict(obj):
            if dataclasses.is_dataclass(obj):
                return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
            if isinstance(obj, list):
                return [_to_dict(i) for i in obj]
            return obj
        print(json.dumps(_to_dict(program), indent=2, default=str))
        return

    runtime = build_runtime(quiet=args.quiet)

    import os
    file_dir = os.path.dirname(os.path.abspath(args.file))
    interpreter = EQLangInterpreter(
        runtime=runtime,
        verbose=not args.quiet,
        include_dirs=[file_dir],
    )

    try:
        results = interpreter.interpret(program)
    except EQLangError as e:
        print(f"[EQLangError] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[EQLang RuntimeError] {e}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        eq = interpreter.get_eq_state()
        print(f"\n── EQLang execution complete ──────────────────────────")
        print(f"   session     : {eq['session_id']!r}")
        print(f"   emitted     : {eq['emit_count']} value(s)")
        print(f"   echoes      : {eq['echo_count']}")
        print(f"   resonance   : {eq['resonance']:.4f}")
        print(f"   coherence   : {eq['coherence']:.4f}")
        print(f"   self        : {eq['self']:.4f}")
        print(f"   load        : {eq['load']:.4f}")
        print(f"   conflict∫   : {eq['conflict_accum']:.2f}")
        print(f"   tension∫    : {eq['tension_accum']:.2f}")
        if eq.get('anchors'):
            print(f"   anchors     : {eq['anchors']}")
        if eq.get('thresholds'):
            print(f"   thresholds  : {eq['thresholds']}")
        if results:
            print(f"   last emit   : {results[-1]!r}")


def _run_repl(runtime, verbose: bool = True) -> None:
    """
    Interactive EQLang REPL.

    Supports multi-line input (tracks open blocks). Special commands:
      .exit        — quit
      .reset       — reset interpreter state (keep runtime)
      .eq          — show current EQ state
      .history     — show emit log
      .echoes      — show echo log
      .thresholds  — show declared thresholds
      .help        — show REPL commands
    """
    from . import __version__, __language__
    from .lexer import Lexer, LexerError
    from .parser import Parser, ParseError
    from .interpreter import EQLangInterpreter, EQLangError

    BANNER = f"""
╔══════════════════════════════════════════════════════════════╗
║  {__language__} v{__version__}
║  C+CT — Consciousness + Conflict Theory
║  Intent-First Alignment
║  Type .help for commands, .exit to quit
╚══════════════════════════════════════════════════════════════╝
"""
    print(BANNER)

    interpreter = EQLangInterpreter(runtime=runtime, verbose=verbose)

    # Block-opening keywords increase depth
    OPEN_KEYWORDS = {"resonate", "struggle", "journal", "when", "cycle", "dialogue", "each", "shelter"}
    CLOSE_KEYWORDS = {"end"}

    buffer = []
    depth = 0

    def _show_eq():
        eq = interpreter.get_eq_state()
        print(f"\n  ── EQ State ──────────────────────────────────────────")
        print(f"  session     : {eq['session_id']!r}")
        print(f"  resonance   : {eq['resonance']:.4f}")
        print(f"  coherence   : {eq['coherence']:.4f}")
        print(f"  self        : {eq['self']:.4f}")
        print(f"  load        : {eq['load']:.4f}")
        print(f"  conflict∫   : {eq['conflict_accum']:.2f}")
        print(f"  tension∫    : {eq['tension_accum']:.2f}")
        if eq.get('anchors'):
            print(f"  anchors     : {eq['anchors']}")
        print()

    def _show_help():
        print("""
  ── REPL Commands ─────────────────────────────────────────────
  .exit        quit the REPL
  .reset       reset interpreter state (thresholds, dialogues, env)
  .eq          show current EQ state
  .history     show emit log
  .echoes      show echo log
  .thresholds  show declared threshold constants
  .types       show available types and builtins
  .help        show this message

  ── Multi-line input ──────────────────────────────────────────
  resonate / struggle / journal / when / cycle / dialogue / each /
  shelter blocks stay open until you type 'end'. The prompt shows
  '...' when you're inside an open block.

  ── EQLang v0.5.0 quick reference ────────────────────────────
  session "name"                   declare session
  threshold name = 0.75            named EQ constant
  state x = "value"                declare variable
  bind x to expr                   reassign variable
  resonate [label] ... end         resonance scope
  struggle ... end                 conflict scope
  journal "label" ... end          reflective trace
  when metric > value ... end      EQ conditional
  when not metric > val ... end    negated conditional
  when a > x and b < y ... end     compound conditional
  cycle while metric > x resonate  EQ loop
  interrupt when metric > x        EQ-grounded break
  each x in list ... end           iterate a list
  shelter ... recover e ... end    error handling
  invoke name(args)                dynamic dialogue dispatch
  measure resonance|coherence|self|load expr
  accum conflict | accum tension
  release tension "integrate"
  anchor metric | drift metric [into name]
  gate category → resolve "method"
  expect expr > expr ["msg"]       test assertion
  learn "text" significance 0.8 region EMOTIONAL
  recall "query" from REGION [into name]
  emit expr [aligned]
  echo expr
  align expr
  inspect metric                   read EQ state as value
  witness dialogue(args) [into x]  pure observation
  weave expr → fn → fn [→ emit]    pipeline
  include "file.eql"               multi-file

  ── Data types ────────────────────────────────────────────────
  nothing                          explicit absence
  42, 3.14                         numbers
  "hello"                          strings
  [1, "a", nothing]                lists (immutable)
  {"key": value}                   maps (immutable, string keys)

  ── Builtins ──────────────────────────────────────────────────
  Math:    min max clamp abs round sqrt pow floor ceil log
  String:  len str concat slice find replace split join
           upper lower trim starts_with ends_with
  List:    contains push pop range sort reverse index_of flatten
  Map:     keys values has_key
  Type:    type is_nothing is_number is_string is_list is_map
           to_number
  Mutate:  set_at(col, key_or_idx, val) → new collection
""")

    while True:
        prompt = "... " if depth > 0 else ">>> "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\n[EQLang] goodbye")
            break

        stripped = line.strip()

        # Special REPL commands (only at top level)
        if depth == 0:
            if stripped == ".exit":
                print("[EQLang] goodbye")
                break
            if stripped == ".reset":
                interpreter = EQLangInterpreter(runtime=runtime, verbose=verbose)
                print("[EQLang] interpreter reset")
                continue
            if stripped == ".eq":
                _show_eq()
                continue
            if stripped == ".history":
                if not interpreter.emit_log:
                    print("  (no emits yet)")
                else:
                    print(f"\n  ── Emit History ({len(interpreter.emit_log)}) ──────────────────────")
                    for i, entry in enumerate(interpreter.emit_log):
                        aligned = " [aligned]" if entry.get("aligned") else ""
                        print(f"  [{i+1}]{aligned} {entry['value']!r}")
                    print()
                continue
            if stripped == ".echoes":
                if not interpreter.echo_log:
                    print("  (no echoes yet)")
                else:
                    print(f"\n  ── Echo Log ({len(interpreter.echo_log)}) ──────────────────────────")
                    for text in interpreter.echo_log:
                        print(f"  {text}")
                    print()
                continue
            if stripped == ".thresholds":
                if not interpreter.thresholds:
                    print("  (no thresholds declared)")
                else:
                    print(f"\n  ── Thresholds ────────────────────────────────────────")
                    for name, val in interpreter.thresholds.items():
                        print(f"  {name} = {val:.4f}")
                    print()
                continue
            if stripped == ".types":
                print("""
  ── EQLang Types ────────────────────────────────────────────
  number       42, 3.14, -1.0        (64-bit float internally)
  string       "hello world"         (immutable, indexable)
  list         [1, "a", [2, 3]]      (immutable, indexable)
  map          {"k": v, "k2": v2}    (immutable, string keys)
  nothing      nothing               (explicit absence)
  boolean      1.0 = true, 0.0 = false (no boolean type)

  ── Builtins ────────────────────────────────────────────────
  Math (10):
    min(a, b)  max(a, b)  clamp(x, lo, hi)  abs(x)  round(x)
    sqrt(x)    pow(x, y)  floor(x)  ceil(x)  log(x)

  String (13):
    len(s)  str(x)  concat(a, b)  slice(s, start[, end])
    find(s, sub)  replace(s, old, new)  split(s, delim)
    join(list, delim)  upper(s)  lower(s)  trim(s)
    starts_with(s, pre)  ends_with(s, suf)

  Collection (8):
    contains(col, item)  push(list, item)  pop(list)
    range(start, end[, step])  sort(list)  reverse(list)
    index_of(list, item)  flatten(list)

  Map (3):
    keys(map)  values(map)  has_key(map, key)

  Type (7):
    type(x)  is_nothing(x)  is_number(x)  is_string(x)
    is_list(x)  is_map(x)  to_number(x)

  Mutation (1):
    set_at(col, key_or_idx, val) → returns new collection
""")
                continue
            if stripped == ".help":
                _show_help()
                continue
            if stripped.startswith(".") and stripped not in (".exit", ".reset"):
                print(f"  unknown command: {stripped!r}. Type .help")
                continue

        # Track block depth for multi-line input
        words = stripped.split()
        first_word = words[0] if words else ""
        if first_word in OPEN_KEYWORDS:
            depth += 1
        # `end resolve` closes dialogue (two keywords on one line)
        close_count = stripped.count("end")
        for _ in range(close_count):
            if depth > 0:
                depth -= 1

        buffer.append(line)

        # Execute when depth returns to 0
        if depth == 0 and buffer:
            source = "\n".join(buffer)
            buffer = []

            if not source.strip():
                continue

            try:
                tokens = Lexer(source).scan_tokens()
                program = Parser(tokens).parse()
                results = interpreter.interpret(program)
                if results:
                    for r in results:
                        print(f"  → {r!r}")
            except LexerError as e:
                print(f"  [LexerError] {e}")
                depth = 0
                buffer = []
            except ParseError as e:
                print(f"  [ParseError] {e}")
                depth = 0
                buffer = []
            except EQLangError as e:
                print(f"  [EQLangError] {e}")
            except Exception as e:
                print(f"  [Error] {e}")


if __name__ == "__main__":
    main()
