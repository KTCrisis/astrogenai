"""
Module de gestion des prompts pour AstroGenAI
Centralise tous les templates de prompts par type de contenu
"""

from .prompt_manager import PromptManager
from .horoscope_templates import HoroscopePromptTemplates
from .weekly_templates import WeeklyPromptTemplates
from .title_templates import TitlePromptTemplates
from .base_templates import BasePromptTemplates

__all__ = [
    'PromptManager',
    'HoroscopePromptTemplates', 
    'WeeklyPromptTemplates',
    'BasePromptTemplates',
    'TitlePromptTemplates'
]