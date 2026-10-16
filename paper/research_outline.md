# Intuition Solver: An Analogy-Mediated Multi-Agent Framework for Mathematical Exploration and Proof Discovery

## Paper outline (pre-registration style; NO fabricated results)

### Abstract [TODO]
State the hypothesis, architecture, and evaluation plan. No claims until experiments run.

### 1. Motivation
Anchoring on known problems, objective drift, conjecture/proof confusion, correlated failures,
premature discarding of ideas, invalid analogy transfer. Each gets an explicit mechanism.

### 2. Research questions & hypotheses
RQ1 candidate lemmas? RQ2 diversity? RQ3 validity/counterexamples? RQ4 anchoring reduction?
RQ5 preservation requirements? RQ6 dialogue vs agreement? RQ7 vs baselines? RQ8 cost?
Each with falsifiable prediction + measure (see `evaluation/metrics.py`).

### 3. Related work [research plan]
Analogical reasoning (Gentner SMT; Holyoak); LLM multi-agent debate; self-critique limits;
formal verification (Lean); problem obfuscation/contamination controls. Fill before submission.

### 4. Architecture
Stages 1-6; blind vs audit prompts; information-disclosure protocol (who sees what, when,
event-logged); roles as prompt configs; reconstruction transfer schema; verification statuses.

### 5. Analogy construction & preservation
Domain selection (no forced fit); correspondence maps; must-preserve vs lost; introduced
assumptions; invalidating questions; leakage heuristic + mandatory human audit.

### 6. Operating modes
Manual (no API key; copy/import loop) vs autonomous (levels 0-3, budgets, gates, resume).
Shared models/prompts/records.

### 7. Experimental design
Conditions A-D; solved problems (correctness), false conjectures (counterexample detection),
open problems (exploration only); comparability requirements; deviation logging.

### 8. Baselines & metrics
Proof validity, lemma counts, transfer success, counterexample discovery, Jaccard diversity,
novelty status, gaps, researcher assessment, time/tokens. No success rates from incomplete data.

### 9. Results [TEMPLATE: do not fill without data]
Per-condition tables + raw pointers + failed approaches + cost breakdown.

### 10. Threats to validity
Leakage, contamination, researcher degrees of freedom, model/version drift, small-N, metric gaming.

### 11. Limitations
Heuristic concealment; model triage is not proof; finite checks are not general proofs; novelty needs literature;
no claim of solving open problems without evidence.

### 12. Future work
Better preservation metrics, automated correspondence checking, Lean tactic integration,
larger controlled trials, cost/benefit analysis.
