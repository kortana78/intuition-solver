# Illustrative reconstruction (NOT a genuine finding; template for researcher replacement).

CLAIM: For all even integers n, m, the sum n + m is even.
ASSUMPTIONS: n = 2k, m = 2l for integers k, l (definition of even); integer arithmetic.
MOTIVATED_BY: L1 "pair-counts add under merger" (solver-1/solver-2).
DERIVATION: n + m = 2k + 2l = 2(k + l). Take k' = k + l; then n + m = 2k', so even.
TRANSFER_VALID: yes: correspondence (pairs <-> factor 2, merger <-> addition) preserves exactly
the structure used; capacity-limit worries do not transfer since integers have no capacity bound.
MISSING_LEMMAS: none for this elementary claim.
PROOF_OBLIGATIONS: discharges P1 (exhibit k').
COUNTEREXAMPLES_OR_ISSUES: none; fails only if inputs are not even (out of scope).
STATUS_SUGGESTION: proven (pending human audit sign-off).
