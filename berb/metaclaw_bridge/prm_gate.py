"""PRM (Process Reward Model) quality gate for Berb.

Uses an LLM-as-judge approach (compatible with MetaClaw's PRMScorer)
to evaluate the quality of pipeline stage outputs at key gate stages.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Stage-specific evaluation instructions
_GATE_INSTRUCTIONS: dict[int, str] = {
    5: (
        "Evaluate the quality of a literature screening result for academic research. "
        "Check: (1) Are the selected papers relevant to the research topic? "
        "(2) Is there sufficient coverage of key approaches? "
        "(3) Are low-quality or irrelevant papers properly filtered out?"
    ),
    9: (
        "Evaluate the quality of an experiment design for academic research. "
        "Check: (1) Are there proper baselines for comparison? "
        "(2) Are ablation studies planned? "
        "(3) Are statistical methods and metrics well-chosen? "
        "(4) Is the experiment reproducible?"
    ),
    15: (
        "Evaluate whether a research PROCEED/PIVOT decision is well-justified. "
        "Check: (1) Is there sufficient evidence to support the decision? "
        "(2) Are alternative interpretations considered? "
        "(3) Is the rationale logically sound?"
    ),
    20: (
        "Evaluate the overall quality of an academic paper. "
        "Check: (1) Is the contribution novel and clearly stated? "
        "(2) Is the methodology sound and well-described? "
        "(3) Do the experiments adequately support the claims? "
        "(4) Is the writing clear and well-structured?"
    ),
}

_JUDGE_SYSTEM = """\
You are a quality reviewer for an automated academic research pipeline.
Based on the evaluation criteria and the provided output, decide:
  +1 = clearly meets quality standards and is ready to proceed
  -1 = fails core requirements or has critical issues
   0 = ambiguous or insufficient evidence to decide

Respond with ONLY "Score: 1", "Score: -1", or "Score: 0" on the first line,
followed by a brief justification."""


@dataclass(frozen=True)
class PRMOutcome:
    """Result of one gate evaluation.

    ``score`` is -1.0, 0.0 or 1.0. ``status`` says what the score means:
    ``ok`` (a clear majority voted), ``ambiguous`` (the votes split or the
    majority voted 0), or ``unavailable`` (no judge call returned a score,
    so there was no evaluation at all). Only ``ok`` is evidence.
    """

    score: float
    status: str
    n_votes: int


def _single_judge_call(
    api_base: str,
    api_key: str,
    model: str,
    instruction: str,
    output_text: str,
    temperature: float,
) -> float | None:
    """Make a single PRM judge call and parse the score."""
    messages = [
        {"role": "system", "content": _JUDGE_SYSTEM},
        {
            "role": "user",
            "content": (
                f"## Evaluation Criteria\n{instruction}\n\n"
                f"## Output to Evaluate\n{output_text[:6000]}"
            ),
        },
    ]
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": 512,
        }
    ).encode("utf-8")

    url = f"{api_base.rstrip('/')}/chat/completions"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        # Parse "Score: X"
        match = re.search(r"Score:\s*([+-]?[01])", content)
        if match:
            return float(match.group(1))
        return None
    except Exception:
        logger.debug("PRM judge call failed", exc_info=True)
        return None


class ResearchPRMGate:
    """PRM quality gate using majority-vote LLM-as-judge scoring."""

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str = "gpt-5.4",
        votes: int = 3,
        temperature: float = 0.6,
    ) -> None:
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.votes = votes
        self.temperature = temperature

    @classmethod
    def from_bridge_config(cls, prm_config: object) -> ResearchPRMGate | None:
        """Create from MetaClawBridgeConfig.prm section.

        Returns None if PRM is not enabled or not configured.
        """
        if not getattr(prm_config, "enabled", False):
            return None

        api_key = str(
            getattr(prm_config, "api_key", "")
            or os.environ.get(getattr(prm_config, "api_key_env", ""), "")
            or ""
        )
        api_base = getattr(prm_config, "api_base", "")
        if not api_base or not api_key:
            return None

        return cls(
            api_base=api_base,
            api_key=api_key,
            model=getattr(prm_config, "model", "gpt-5.4"),
            votes=getattr(prm_config, "votes", 3),
            temperature=getattr(prm_config, "temperature", 0.6),
        )

    def evaluate_stage(
        self,
        stage_num: int,
        output_text: str,
        *,
        custom_instruction: str | None = None,
    ) -> float:
        """Score only: -1.0 (fail), 0.0 (ambiguous or unavailable), 1.0 (pass).

        Use :meth:`evaluate_stage_outcome` when the caller must tell an
        outage apart from a genuinely ambiguous verdict.
        """
        return self.evaluate_stage_outcome(
            stage_num, output_text, custom_instruction=custom_instruction
        ).score

    def evaluate_stage_outcome(
        self,
        stage_num: int,
        output_text: str,
        *,
        custom_instruction: str | None = None,
    ) -> PRMOutcome:
        """Evaluate a stage output using majority-vote PRM scoring.

        Args:
            stage_num: Pipeline stage number (5, 9, 15, or 20).
            output_text: The stage output text to evaluate.
            custom_instruction: Override the default evaluation instruction.

        Returns:
            A :class:`PRMOutcome`. A tie between the leading scores is
            ``ambiguous`` (0.0) regardless of the order the votes arrived in.
        """
        instruction = custom_instruction or _GATE_INSTRUCTIONS.get(
            stage_num,
            "Evaluate the quality and correctness of this research output.",
        )

        # Parallel judge calls
        scores: list[float] = []
        with ThreadPoolExecutor(max_workers=self.votes) as pool:
            futures = [
                pool.submit(
                    _single_judge_call,
                    self.api_base,
                    self.api_key,
                    self.model,
                    instruction,
                    output_text,
                    self.temperature,
                )
                for _ in range(self.votes)
            ]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    scores.append(result)

        if not scores:
            logger.warning("All PRM judge calls failed for stage %d", stage_num)
            return PRMOutcome(0.0, "unavailable", 0)

        # Explicit majority: statistics.mode returns whichever tied value was
        # seen first, which here means whichever judge thread finished first.
        ranked = Counter(scores).most_common()
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            return PRMOutcome(0.0, "ambiguous", len(scores))
        winner = float(ranked[0][0])
        return PRMOutcome(winner, "ok" if winner != 0.0 else "ambiguous", len(scores))

    def should_gate(self, stage_num: int) -> bool:
        """Check if PRM gating is configured for this stage."""
        return stage_num in _GATE_INSTRUCTIONS
