"""Dynamic skills library for AutoResearchClaw.

Provides a registry of reusable research/engineering/writing skills
that can be automatically matched to pipeline stages and injected
into LLM prompts.
"""

from berb.skills.schema import Skill
from berb.skills.registry import SkillRegistry

__all__ = ["Skill", "SkillRegistry"]
