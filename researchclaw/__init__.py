"""Compatibility shim for researchclaw imports.

This module allows tests written for researchclaw to work with berb package.
"""

import sys

# Import berb submodules first
import berb.llm
import berb.utils
import berb.pipeline
import berb.literature
import berb.agents
import berb.experiment
import berb.knowledge
import berb.memory
import berb.self_evolve
import berb.metaclaw_bridge
import berb.mnemo_bridge
import berb.reasoner_bridge
import berb.learning

import berb

# Make imports work as if they were from researchclaw
sys.modules['researchclaw'] = berb
sys.modules['researchclaw.llm'] = berb.llm
sys.modules['researchclaw.utils'] = berb.utils
sys.modules['researchclaw.pipeline'] = berb.pipeline
sys.modules['researchclaw.literature'] = berb.literature
sys.modules['researchclaw.agents'] = berb.agents
sys.modules['researchclaw.experiment'] = berb.experiment
sys.modules['researchclaw.knowledge'] = berb.knowledge
sys.modules['researchclaw.memory'] = berb.memory
sys.modules['researchclaw.self_evolve'] = berb.self_evolve
sys.modules['researchclaw.metaclaw_bridge'] = berb.metaclaw_bridge
sys.modules['researchclaw.mnemo_bridge'] = berb.mnemo_bridge
sys.modules['researchclaw.reasoner_bridge'] = berb.reasoner_bridge
sys.modules['researchclaw.learning'] = berb.learning
