"""Shared enumerations: verification status, novelty, stages, autonomy levels, roles."""

from enum import Enum


class VerificationStatus(str, Enum):
    PROVEN = "PROVEN"
    COMPUTATIONALLY_SUPPORTED = "COMPUTATIONALLY_SUPPORTED"
    CONJECTURE = "CONJECTURE"
    GAP = "GAP"
    REFUTED = "REFUTED"
    KNOWN_RESULT = "KNOWN_RESULT"
    UNVERIFIED = "UNVERIFIED"


class NoveltyStatus(str, Enum):
    NEW_TO_EXPERIMENT = "NEW_TO_EXPERIMENT"
    NOT_CHECKED = "NOT_CHECKED"
    KNOWN = "KNOWN"
    POTENTIALLY_NOVEL = "POTENTIALLY_NOVEL"
    VERIFIED_NOVEL = "VERIFIED_NOVEL"


class ExperimentStage(str, Enum):
    CREATED = "created"
    SPECIFIED = "specified"
    ANALOGY_GENERATED = "analogy_generated"
    ANALOGY_APPROVED = "analogy_approved"
    SOLVING = "solving"
    SOLVED = "solved"
    CROSS_EXAM = "cross_exam"
    RECONSTRUCTED = "reconstructed"
    AUDITED = "audited"
    REPORTED = "reported"


class AutonomyLevel(int, Enum):
    MANUAL = 0
    ASSISTED = 1
    SUPERVISED = 2
    AUTONOMOUS = 3


class AgentRole(str, Enum):
    ANALOGY_GENERATOR = "analogy_generator"
    SOLVER = "solver"
    CRITIC = "critic"
    COUNTEREXAMPLE = "counterexample_hunter"
    ALTERNATIVE = "alternative_explorer"
    SYNTHESIZER = "synthesizer"
    CONTROLLER = "research_controller"
    RECONSTRUCTOR = "reconstructor"
    VERIFIER = "verifier"


class ConditionKind(str, Enum):
    """Four experimental conditions A-D from the research protocol."""

    DIRECT_SINGLE = "A_direct_single"
    DIRECT_MULTI = "B_direct_multi"
    ANALOGY_NO_DIALOGUE = "C_analogy_no_dialogue"
    FULL_ARCHITECTURE = "D_full_architecture"
