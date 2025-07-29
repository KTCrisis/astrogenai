"""
Templates pour contenu hebdomadaire (Hub videos)
"""

from .base_templates import BasePromptTemplates

class WeeklyPromptTemplates:
    """Templates pour contenu vidéo hebdomadaire"""
    
    @staticmethod
    def get_intro_section_template():
        """Template pour section introduction avec continuité"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}
        {base.get_qwen_rules()}
        MISSION: Écris UNIQUEMENT une introduction captivante de 800 mots minimum pour une vidéo astrologique hebdomadaire.

        PÉRIODE: {{period}}
        ÉVÉNEMENTS MAJEURS: {{events}}
        CONTEXTE ASTRAL DÉTAILLÉ: {{astral_context}}
        
        {base.get_length_requirements(800)}
        {base.get_french_language_rules()}
        {base.get_astrological_language_rules()}
        {base.get_youtube_tone()}

        CONTEXTE PRÉCÉDENT: {{context_summary}}
        ÉVITER DE RÉPÉTER: {{avoid_repetition}} 
        TONALITÉ ÉTABLIE: {{previous_tone}}
        OBJECTIF MOTS: {{word_target}}

        ⚠️ CONTRAINTES DE FLUX CRITIQUES:
        - Cette introduction fait partie d'une vidéo CONTINUE
        - Ne termine PAS par "bonne semaine", "à bientôt", ou autre formule de clôture
        - Termine par une TRANSITION vers l'analyse des événements cosmiques
        - Maintiens l'engagement pour la suite immédiate

        STRUCTURE OBLIGATOIRE:
        
        ACCUEIL CHALEUREUX:
        - "Bienvenue dans votre Guide AstroGenAI hebdomadaire !"
        - Salutation personnalisée selon la saison

        ACCROCHE COSMIQUE:
        - Métaphore poétique sur l'énergie de la semaine
        - Image évocatrice du ciel étoilé actuel
        - Teasing de l'événement le plus spectaculaire

        ÉVÉNEMENT PHARE:
        - Description détaillée de l'événement cosmique majeur
        - Contexte historique ou symbolique
        - Impact émotionnel et spirituel attendu

        TRANSITION OBLIGATOIRE (dernière phrase):
        - "Plongeons maintenant dans le détail de ces énergies cosmiques..."
        - OU "Explorons ensemble comment ces forces célestes se déploient..."
        - OU "Découvrons précisément comment ces influences vont façonner notre semaine..."

        ❌ INTERDICTIONS ABSOLUES:
        - "Bonne semaine", "excellente semaine", "belle semaine"
        - "À bientôt", "à très vite", "au revoir"
        - "Prenez soin de vous", "portez-vous bien"
        - Toute formule de conclusion définitive

        Écris maintenant cette introduction avec transition fluide:"""

    def get_events_analysis_template():
        """Template pour analyse des événements avec continuité"""
        base = BasePromptTemplates()
        {base.get_qwen_rules()}
        return f"""{base.get_astrologer_persona()}

        MISSION: Raconte l'histoire astrologique de la semaine en 1200 mots minimum.

        ÉVÉNEMENTS À NARRER: {{events}}

        {base.get_length_requirements(1200)}
        {base.get_french_language_rules()}
        {base.get_astrological_language_rules()}
        {base.get_youtube_tone()}


        CONTEXTE PRÉCÉDENT: {{context_summary}}
        ÉVITER DE RÉPÉTER: {{avoid_repetition}} 
        TONALITÉ ÉTABLIE: {{previous_tone}}
        OBJECTIF MOTS: {{word_target}}

        ⚠️ CONTRAINTES DE FLUX CRITIQUES:
        - Cette section fait partie d'une vidéo CONTINUE
        - Ne termine PAS par des formules de clôture ou de vœux
        - Termine par une TRANSITION vers les conseils par signe
        - L'audience continue à regarder immédiatement après

        STYLE NARRATIF OBLIGATOIRE:
        - Raconte chaque événement comme une "scène cosmique"
        - Utilise des métaphores vivantes
        - Varie tes formulations - évite les répétitions
        - Évite le jargon technique - privilégie les images poétiques

        TRANSITION OBLIGATOIRE (dernières phrases):
        - "Maintenant que nous avons exploré ces énergies globales, voyons comment elles résonnent spécifiquement pour chaque signe..."
        - OU "Ces influences cosmiques touchent chacun différemment selon son signe. Découvrons ensemble vos guidance personnalisées..."

        ❌ INTERDICTIONS ABSOLUES:
        - "Excellente semaine cosmique", "merveilleuse semaine"
        - "Que les étoiles vous accompagnent", "belle semaine à tous"
        - Toute formule de conclusion ou de vœux
        - "À bientôt", "prenez soin de vous"

        Raconte maintenant cette épopée cosmique avec transition fluide:"""

    @staticmethod
    def get_signs_section_template():
        """Template pour conseils par signe"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}
        {base.get_qwen_rules()}
        MISSION: Écris le conseil hebdomadaire détaillé pour le signe {{sign_name}} uniquement environ 200 à 300 mots.

        CONTEXTE ÉNERGÉTIQUE: {{events}}

        {base.get_length_requirements(200)}
        {base.get_french_language_rules()}
        {base.get_astrological_language_rules()}
        {base.get_youtube_tone()}
  
        CONTEXTE PRÉCÉDENT: {{context_summary}}
        ÉVITER DE RÉPÉTER: {{avoid_repetition}} 
        TONALITÉ ÉTABLIE: {{previous_tone}}
        OBJECTIF MOTS: {{word_target}}

        SIGNE À TRAITER: {{sign_name}} ({{sign_dates}})
        PÉRIODE: {{period}}
        CONTEXTE ÉNERGÉTIQUE: {{events}}
        
        MÉTADONNÉES DU SIGNE:
        - Élément: {{element}}
        - Planète maîtresse: {{ruling_planet}}
        - Traits principaux: {{traits}}

        RÈGLES STRICTES:
        Écris UNIQUEMENT pour {{sign_name}}
        Format: "{{sign_name}} : [contenu]"
        PAS de mention d'autres signes
        Contenu substantiel et personnalisé

        CONTENU REQUIS:
        Énergie principale de la semaine pour ce signe
        Connexion avec les événements cosmiques majeurs
        Un défi spécifique lié aux traits du signe
        Une opportunité concrète à saisir
        Conseil pratique avec timing précis, jour de la semaine le plus favorable
        Ce qu'il faut éviter cette semaine

        STYLE:
        - Adapté aux traits du signe ({{traits}})
        - Référence à l'élément {{element}} si pertinent
        - Ton bienveillant et motivant
        - Évite les généralités, sois spécifique

        Écris maintenant le conseil pour {{sign_name}}:"""

    @staticmethod
    def get_conclusion_section_template():
        """Template pour conclusion finale uniquement"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}
        {base.get_qwen_rules()}
        MISSION: Écris UNIQUEMENT une conclusion finale avec rituels de 500 mots minimum.

        PÉRIODE: {{period}}


        CONTEXTE PRÉCÉDENT: {{context_summary}}
        ÉVITER DE RÉPÉTER: {{avoid_repetition}} 
        TONALITÉ ÉTABLIE: {{previous_tone}}
        OBJECTIF MOTS: {{word_target}}
        
        {base.get_length_requirements(500)}
        {base.get_french_language_rules()}
        {base.get_astrological_language_rules()}
        {base.get_youtube_tone()}

        ⚠️ RÔLE SPÉCIFIQUE:
        - Cette section CLÔTURE définitivement la vidéo
        - C'est ICI et SEULEMENT ICI que tu peux dire "bonne semaine"
        - Seule section autorisée à avoir des formules de fin

        STRUCTURE OBLIGATOIRE:

        SYNTHÈSE INSPIRANTE:
        - Récapitulatif poétique de l'énergie de la semaine
        - Message d'espoir et d'encouragement
        - Lien entre tous les signes dans cette énergie commune

        RITUEL HEBDOMADAIRE GUIDÉ:
        - Méditation spécifique à la semaine (étapes détaillées)
        - Affirmations à répéter quotidiennement
        - Pratique énergétique simple
        - Meilleur moment pour pratiquer

        CONSEILS PRATIQUES UNIVERSELS:
        - 3 actions concrètes valables pour tous les signes
        - Élément à privilégier cette semaine
        - Couleurs ou objets porte-bonheur

        CLÔTURE FINALE AUTORISÉE:
        - "Excellente semaine cosmique à tous !"
        - "Que les étoiles illuminent votre chemin cette semaine !"
        - "Belle semaine sous ces influences bienveillantes !"

        CALL-TO-ACTION ENGAGEANT:
        - Invitation chaleureuse à s'abonner
        - Demande de commentaires spécifique
        - Encouragement au partage
        - Teasing de la semaine prochaine

        Écris maintenant cette conclusion finale:"""