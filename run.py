#!/usr/bin/env python3
"""
EQLang Runner — run .eql programs from the command line.

Usage:
    python run.py yourfile.eql
    python run.py yourfile.eql --quiet
    python run.py --repl
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from eqlang import run_file, run_string
from eqlang.runtime import StandardRuntime, MockRuntime


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        print("Options:")
        print("  --quiet      Suppress execution trace, show emitted values only")
        print("  --mock       Use MockRuntime (fixed values, for testing)")
        print("  --repl       Start interactive REPL")
        return

    quiet = "--quiet" in args
    mock  = "--mock" in args
    repl  = "--repl" in args
    files = [a for a in args if not a.startswith("--")]

    runtime = MockRuntime() if mock else StandardRuntime()

    if repl:
        _run_repl(runtime)
        return

    if not files:
        print("Error: no .eql file given.")
        print("Usage: python run.py yourfile.eql")
        sys.exit(1)

    for path in files:
        if not os.path.exists(path):
            print(f"Error: file not found — {path}")
            sys.exit(1)

        if not quiet:
            print(f"\n── {path} ──")

        try:
            emitted = run_file(path, runtime=runtime, verbose=not quiet)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

        if quiet and emitted:
            for v in emitted:
                print(v)


def _run_repl(runtime):
    from eqlang import Lexer, Parser, EQLangInterpreter
    from eqlang.lexer import LexError
    from eqlang.parser import ParseError

    print("EQLang REPL  (type .help for commands, .exit to quit)\n")
    interp = EQLangInterpreter(runtime=runtime, verbose=True)
    buf = []

    OPENERS = {"resonate", "dialogue", "when", "otherwise", "struggle",
               "cycle", "journal", "witness"}
    CLOSERS = {"end"}

    def depth(lines):
        d = 0
        for ln in lines:
            w = ln.strip().split()
            if w and w[0] in OPENERS:
                d += 1
            if w and w[0] in CLOSERS:
                d = max(0, d - 1)
        return d

    while True:
        prompt = "... " if buf else "eql> "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if line.strip() == ".exit":
            break
        if line.strip() == ".reset":
            interp = EQLangInterpreter(runtime=runtime, verbose=True)
            buf = []
            print("(interpreter reset)")
            continue
        if line.strip() == ".eq":
            for k, v in interp.eq_state.items():
                print(f"  {k:<12} {v:.4f}" if isinstance(v, float) else f"  {k:<12} {v}")
            continue
        if line.strip() == ".history":
            for e in interp.emit_log:
                print(f"  {e}")
            continue
        if line.strip() == ".help":
            print("  .exit      quit")
            print("  .reset     reset interpreter state")
            print("  .eq        show current EQ state")
            print("  .history   show emitted values")
            continue

        buf.append(line)

        if depth(buf) == 0 and buf:
            source = "\n".join(buf)
            buf = []
            try:
                tokens = Lexer(source).scan_tokens()
                program = Parser(tokens).parse()
                interp.interpret(program)
            except (LexError, ParseError) as e:
                print(f"[Error] {e}")
            except Exception as e:
                print(f"[Error] {e}")


if __name__ == "__main__":
    main()
