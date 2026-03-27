"""Internationalization (i18n) for Berb.

Multi-language support with language detection and translation.
"""

from .multilingual import (
    LanguageDetector,
    LanguageDetectionResult,
    PromptTranslator,
    MultilingualPipelineAdapter,
    SupportedLanguage,
    LANGUAGE_NAMES,
    get_multilingual_adapter,
)

__all__ = [
    "LanguageDetector",
    "LanguageDetectionResult",
    "PromptTranslator",
    "MultilingualPipelineAdapter",
    "SupportedLanguage",
    "LANGUAGE_NAMES",
    "get_multilingual_adapter",
]
