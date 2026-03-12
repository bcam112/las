"""
EQLang Runtime — Pluggable EQ adapter interface. v0.5.0

Open source (MIT):
  EQRuntime       — Abstract base class for all runtime adapters
  StandardRuntime — Heuristic text analysis, stdlib-only, no API needed. Default.
  MockRuntime     — Deterministic fixed values for testing and CI

Production runtimes (proprietary, requires Luci API key):
  LASRuntime       — EQLang-native v7.0 engine (from luci import LASRuntime)
  EQEngineRuntime  — In-process eq_engine binding
  LuciHTTPRuntime  — Cloud API runtime

Get production runtimes at: https://useluci.com

Usage:
    from eqlang.runtime import StandardRuntime, MockRuntime

    # Default: heuristic EQ metrics, no API needed (MIT)
    runtime = StandardRuntime()
    runtime = StandardRuntime(sensitivity=1.2)   # amplify metric responses

    # Testing: deterministic fixed values (MIT)
    runtime = MockRuntime(fixed_resonance=0.85)

    # Production (licensed):
    # from luci import LASRuntime
    # runtime = LASRuntime()
"""

from .base import EQRuntime, EQRuntimeError
from .standard_runtime import StandardRuntime
from .mock_runtime import MockRuntime

__all__ = [
    "EQRuntime",
    "EQRuntimeError",
    "StandardRuntime",
    "MockRuntime",
]
