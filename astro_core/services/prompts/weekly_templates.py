"""
Templates pour contenu hebdomadaire (Hub videos)
"""

from .base_templates import BasePromptTemplates

class WeeklyPromptTemplates:
    """Templates pour contenu vidéo hebdomadaire"""
    
    @staticmethod
    def get_intro_section_template():
        """Template pour section introduction (800 mots)"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

MISSION: Écris UNIQUEMENT une introduction détaillée de 800 mots minimum pour une vidéo astrologique hebdomadaire.

PÉRIODE: {{period}}
ÉVÉNEMENTS MAJEURS: {{events}}

{base.get_length_requirements(800)}
{base.get_french_language_rules()}
{base.get_youtube_tone()}

CONTENU À INCLURE:
- Accueil chaleureux : "Bienvenue dans votre Guide Astrologique hebdomadaire !"
- Présentation de l'énergie générale de la semaine
- Mise en avant de l'événement cosmique le plus important
- Contexte historique ou symbolique de cet événement
- Annonce détaillée de ce qui sera couvert dans la vidéo

Écris maintenant cette introduction substantielle:"""

    def get_events_analysis_template():
        """Template pour analyse des événements (1200 mots)"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

    MISSION: Raconte l'histoire astrologique de la semaine en 1200 mots minimum, comme un conteur passionné.

    ÉVÉNEMENTS À NARRER: {{events}}

    {base.get_length_requirements(1200)}
    {base.get_french_language_rules()}
    {base.get_astrological_language_rules()}
    {base.get_youtube_tone()}

    STYLE NARRATIF OBLIGATOIRE:
    - Raconte chaque événement comme une "scène cosmique"
    - Utilise des métaphores vivantes (danse, rencontre, dialogue entre planètes)
    - Varie tes formulations - ne répète jamais la même structure
    - Intègre naturellement les aspects astrologiques dans le récit
    - Évite le jargon technique - explique avec des images poétiques

    EXEMPLE DE STYLE ATTENDU:
    ❌ "Le 3 août, Saturne sextile Uranus indique..."
    ✅ "Le 3 août, le sage Saturne tend la main vers l'innovateur Uranus, créant une alliance magique entre tradition et révolution..."

    Raconte maintenant cette épopée cosmique:"""

    @staticmethod
    def get_signs_section_template():
        """Template pour conseils par signe (1200 mots)"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

MISSION: Écris UNIQUEMENT les conseils détaillés par signe de 1200 mots minimum.

CONTEXTE ÉNERGÉTIQUE: {{events}}

{base.get_length_requirements(1200)}
{base.get_french_language_rules()}
{base.get_youtube_tone()}

INSTRUCTIONS STRICTES:
- Conseils pour LES 12 SIGNES individuellement (100 mots par signe)
- Pour chaque signe, donne:
  * Un conseil principal développé (3-4 phrases)
  * Un exemple concret de situation
  * Une action pratique à entreprendre
  * Ce qu'il faut éviter cette semaine

SIGNES À TRAITER (dans cet ordre):
1. Bélier, 2. Taureau, 3. Gémeaux, 4. Cancer, 5. Lion, 6. Vierge
7. Balance, 8. Scorpion, 9. Sagittaire, 10. Capricorne, 11. Verseau, 12. Poissons

FORMAT: "**Bélier :** ...", "**Taureau :** ...", etc.

Commence les conseils maintenant:"""

    @staticmethod
    def get_conclusion_section_template():
        """Template pour conclusion et rituels (400 mots)"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

MISSION: Écris UNIQUEMENT une conclusion avec rituels de 400 mots minimum.

PÉRIODE: {{period}}

{base.get_length_requirements(400)}
{base.get_french_language_rules()}
{base.get_youtube_tone()}

CONTENU À INCLURE:
- Méditation ou affirmation spécifique
- Pratiques quotidiennes suggérées
- Message d'encouragement personnalisé
- Call-to-action YouTube engageant (abonnement, commentaires, partage)

Écris cette conclusion substantielle maintenant:"""