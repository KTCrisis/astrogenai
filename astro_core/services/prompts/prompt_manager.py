"""
Gestionnaire centralisé de tous les prompts AstroGenAI
"""

from .base_templates import BasePromptTemplates
from .horoscope_templates import HoroscopePromptTemplates  
from .weekly_templates import WeeklyPromptTemplates
from .title_templates import TitlePromptTemplates

class PromptManager:
    """Gestionnaire centralisé de tous les prompts"""
    
    def __init__(self):
        self.base = BasePromptTemplates()
        self.horoscope = HoroscopePromptTemplates()
        self.weekly = WeeklyPromptTemplates()
        self.title = TitlePromptTemplates()
    
    def get_horoscope_prompt(self, prompt_type: str, **kwargs):
        """Retourne un prompt d'horoscope formaté"""
        if prompt_type == "individual":
            template = self.horoscope.get_individual_horoscope_template()
        elif prompt_type == "enriched":
            template = self.horoscope.get_enriched_horoscope_template()
        elif prompt_type == "daily_batch":
            template = self.horoscope.get_daily_batch_template()
        else:
            raise ValueError(f"Type de prompt inconnu: {prompt_type}")
        
        return template.format(**kwargs)
    
    def get_weekly_prompt(self, section: str, **kwargs):
        """Retourne un prompt de section hebdomadaire formaté"""
        if section == "intro":
            template = self.weekly.get_intro_section_template()
        elif section == "events":
            template = self.weekly.get_events_analysis_template()
        elif section == "signs":
            template = self.weekly.get_signs_section_template()
        elif section == "conclusion":
            template = self.weekly.get_conclusion_section_template()
        else:
            raise ValueError(f"Section inconnue: {section}")
        
        return template.format(**kwargs)

    def get_titlle_prompt(self, prompt_type: str, **kwargs):
        """Retourne un prompt d'horoscope formaté"""
        if prompt_type == "individual":
            template = self.title.get_individual_title_template()
        elif prompt_type == "weekly":
            template = self.title.get_weekly_title_template()
        else:
            raise ValueError(f"Type de prompt inconnu: {prompt_type}")
        
        return template.format(**kwargs)
        
    def get_system_status(self):
        """Retourne l'état du système de prompts"""
        return {
            "base_templates": True,
            "horoscope_templates": True,
            "weekly_templates": True,
            "total_templates": 7  # Nombre total de templates disponibles
        }