"""
Templates pour la génération d'horoscopes individuels et quotidiens
"""

from .base_templates import BasePromptTemplates

class HoroscopePromptTemplates:
    """Templates pour horoscopes individuels et quotidiens"""
    
    @staticmethod
    def get_individual_horoscope_template():
        """Template pour horoscope individuel standard"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

            MISSION: Écris un horoscope court et engageant pour le signe {{sign_name}} ({{sign_dates}}).

            CONTEXTE ASTROLOGIQUE:
            - Date: {{date}} ({{day_of_week}})
            - Saison: {{season}} - {{seasonal_energy}}
            - Phase lunaire: {{lunar_phase}}
            - Planètes influentes: {{planets_str}}

            CARACTÉRISTIQUES DU SIGNE:
            - Élément: {{element}}
            - Planète maîtresse: {{ruling_planet}}
            - Traits principaux: {{traits}}

            {base.get_length_requirements(50)}
            {base.get_french_language_rules()}

            INSTRUCTIONS SPÉCIFIQUES:
            - Horoscope de {{min_words}}-{{max_words}} mots maximum
            - Ton moderne, bienveillant et motivant
            - Donne 1 conseil pratique adapté au signe
            - Commence par "Cher {{sign_name}},"
            - Adapte le contenu au contexte astral fourni

            Réponds UNIQUEMENT avec le texte de l'horoscope."""

    @staticmethod
    def get_enriched_horoscope_template():
        """Template pour horoscope enrichi avec données astronomiques"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

            MISSION: Crée un horoscope de {{min_words}}-{{max_words}} mots en utilisant les données astronomiques RÉELLES.

            DONNÉES ASTRONOMIQUES RÉELLES pour le {{date}}:

            {{positions_text}}
            {{aspects_text}}
            {{lunar_info}}
            
            SIGNE À ANALYSER: {{sign_name}} ({{sign_dates}})
            Élément: {{element}} | Planète maîtresse: {{ruling_planet}}
            Traits: {{traits}}

            {base.get_french_language_rules()}

            INSTRUCTIONS:
            - UTILISE les positions et aspects RÉELS ci-dessus (pas des généralités)
            - Fais une analyse pour le {{date}}
            - Ne mentionne pas la semaine, mais utilise la date du jour
            - Mentionne 1 seul aspect le plus significatif s'ils concernent le signe
            - N'INDIQUE pas les orbes et degrés dans ta réponse
            - Adapte selon la phase lunaire actuelle
            - Ton moderne, bienveillant, précis et motivant
            - Donne 1 conseil pratique adapté au signe
            - Commence par "Cher {{sign_name}},"

            Réponds UNIQUEMENT avec le texte de l'horoscope."""

    @staticmethod
    def get_daily_batch_template():
        """Template pour génération quotidienne en lot"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

            MISSION: Génère les horoscopes pour TOUS les 12 signes pour la date {{date}}.

            CONTEXTE ASTRAL GLOBAL:
            {{astral_context}}

            {base.get_french_language_rules()}

            INSTRUCTIONS:
            - Horoscope de 30-50 mots par signe
            - Adapte chaque horoscope aux traits spécifiques du signe
            - Utilise le contexte astral fourni
            - Ton bienveillant et motivant
            - 1 conseil pratique par signe

            FORMAT ATTENDU:
            **Bélier:** [horoscope]
            **Taureau:** [horoscope]
            [...tous les 12 signes...]

            Génère maintenant les 12 horoscopes:"""