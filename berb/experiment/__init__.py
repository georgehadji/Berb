"""Experiment execution — sandbox, runner, git manager."""

from berb.experiment.factory import create_sandbox
from berb.experiment.sandbox import (
    ExperimentSandbox,
    SandboxProtocol,
    SandboxResult,
    parse_metrics,
)
from berb.experiment.progress import (
    ExperimentProgressManager,
    ExperimentProgressConfig,
    ExperimentStage,
    StageConfig,
    StageResult,
    ExperimentReport,
    run_structured_experiment,
)
from berb.experiment.auto_debugger import (
    AutomatedDebugger,
    ErrorCategory,
    ErrorSeverity,
    ErrorDiagnosis,
    FixSuggestion,
    DebugResult,
    auto_debug,
)
from berb.experiment.self_correcting import (
    SelfCorrectingExecutor,
    SimulationStatus,
    SimulationResult,
    InputClarifierAgent,
    CodeBuilderAgent,
    SimulationExecutorAgent,
    ErrorDiagnosisAgent,
    InputRewriterAgent,
    MechanicalInsightAgent,
    run_self_correcting_simulation,
)

__all__ = [
    "ExperimentSandbox",
    "SandboxProtocol",
    "SandboxResult",
    "create_sandbox",
    "parse_metrics",
    "ExperimentProgressManager",
    "ExperimentProgressConfig",
    "ExperimentStage",
    "StageConfig",
    "StageResult",
    "ExperimentReport",
    "run_structured_experiment",
    "AutomatedDebugger",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorDiagnosis",
    "FixSuggestion",
    "DebugResult",
    "auto_debug",
    "SelfCorrectingExecutor",
    "SimulationStatus",
    "SimulationResult",
    "InputClarifierAgent",
    "CodeBuilderAgent",
    "SimulationExecutorAgent",
    "ErrorDiagnosisAgent",
    "InputRewriterAgent",
    "MechanicalInsightAgent",
    "run_self_correcting_simulation",
]
