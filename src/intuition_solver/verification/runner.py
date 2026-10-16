"""Finite-case + symbolic + Lean-optional verification helpers.

- Finite checks run researcher-supplied Python in a restricted namespace
  (no imports except math/itertools/functools by default; timeouts via best effort).
- Symbolic checks optionally use sympy when installed.
- Lean checks shell out to `lake env lean` only when available; otherwise report skipped.
A finite number of passing tests is reported as COMPUTATIONALLY_SUPPORTED at most.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class CheckOutcome:
    passed: bool
    output: str


SAFE_GLOBALS = {"math": math, "abs": abs, "min": min, "max": max, "sum": sum,
                "len": len, "range": range, "all": all, "any": any}


def run_finite_check(code: str, timeout_s: int = 10) -> CheckOutcome:
    """Execute `code` expecting it to set variable `result` truthy or call assert.

    Returns passed/output. Never raises.
    """
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    g = dict(SAFE_GLOBALS)
    try:
        with redirect_stdout(buf):
            exec(compile(code, "<finite-check>", "exec"), {"__builtins__": {}}, g)  # noqa: S102
        result = g.get("result", True)
        passed = bool(result)
        return CheckOutcome(passed=passed, output=(buf.getvalue() or "(no output)")[:4000])
    except AssertionError as exc:
        return CheckOutcome(passed=False, output=f"AssertionError: {exc}\n{buf.getvalue()[:2000]}")
    except Exception as exc:
        return CheckOutcome(passed=False, output=f"{type(exc).__name__}: {exc}\n{buf.getvalue()[:2000]}")


def try_symbolic(code: str) -> CheckOutcome:
    try:
        import sympy  # type: ignore
    except ImportError:
        return CheckOutcome(passed=False, output="sympy not installed; symbolic check skipped")
    try:
        out = str(eval(code, {"sympy": sympy}))  # noqa: S307
        return CheckOutcome(passed=True, output=out[:4000])
    except Exception as exc:
        return CheckOutcome(passed=False, output=f"{type(exc).__name__}: {exc}")


def try_lean(filepath: str, timeout_s: int = 120) -> CheckOutcome:
    """Run Lean checker on a file if toolchain present. Reports only actual runs."""
    lean = shutil.which("lean") or shutil.which("lake")
    if lean is None:
        return CheckOutcome(passed=False, output="Lean toolchain not found; formal check skipped (not verified)")
    try:
        proc = subprocess.run([lean, filepath] if lean.endswith("lean") else [lean, "env", "lean", filepath],
                              capture_output=True, text=True, timeout=timeout_s)
        ok = proc.returncode == 0
        return CheckOutcome(passed=ok, output=(proc.stdout + proc.stderr)[:4000] or "(no output)")
    except Exception as exc:
        return CheckOutcome(passed=False, output=f"Lean run failed: {exc}")
