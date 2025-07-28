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

 MISSION: Écris UNIQUEMENT une introduction captivante de 800 mots minimum pour une vidéo astrologique hebdomadaire.

        PÉRIODE: {{period}}
        ÉVÉNEMENTS MAJEURS: {{events}}

        {base.get_length_requirements(800)}
        {base.get_french_language_rules()}
        {base.get_astrological_language_rules()}
        {base.get_youtube_tone()}

        STRUCTURE OBLIGATOIRE DE L'INTRODUCTION:
        
        ACCUEIL CHALEUREUX :
        -"Bienvenue dans votre Guide AstroGenAI hebdomadaire !"
        - Salutation personnalisée selon la saison

        ACCROCHE COSMIQUE :
        - Métaphore poétique sur l'énergie de la semaine
        - Image évocatrice du ciel étoilé actuel
        - Teasing de l'événement le plus spectaculaire

        ÉVÉNEMENT PHARE:
        - Description détaillée de l'événement cosmique majeur
        - Contexte historique ou symbolique
        - Pourquoi c'est exceptionnel cette semaine
        - Impact émotionnel et spirituel attendu

        PREVIEW DE LA VIDÉO :
        - Annonce des sections à venir avec enthousiasme
        - Promesse de révélations personnalisées par signe
        - Mention des rituels/pratiques qui seront partagés
        - Invitation à rester jusqu'à la fin

        TRANSITION VERS LE CONTENU :
        - Phrase de transition élégante vers la suite
        - Maintien de l'engagement

        TONS SPÉCIFIQUES À UTILISER:
        - Mystérieux mais accessible
        - Chaleureux et bienveillant
        - Enthousiaste sans être excessif
        - Poétique mais informatif

        MOTS-CLÉS À INTÉGRER NATURELLEMENT:
        - "énergie cosmique", "vibrations célestes"
        - "voyage astral", "guidance des étoiles"
        - "transformation", "révélation", "illumination"

        Écris maintenant cette introduction substantielle et captivante:"""

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
        """Template pour conseils par signe"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

        MISSION: Écris le conseil hebdomadaire détaillé pour le signe {{sign_name}} uniquement environ 200 à 300 mots.

        CONTEXTE ÉNERGÉTIQUE: {{events}}

        {base.get_length_requirements(200)}
        {base.get_french_language_rules()}
        {base.get_astrological_language_rules()}
        {base.get_youtube_tone()}
  
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
        """Template pour conclusion et rituels"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

            MISSION: Écris UNIQUEMENT une conclusion avec rituels de 500 mots minimum.

            PÉRIODE: {{period}}

            {base.get_length_requirements(500)}
            {base.get_french_language_rules()}
            {base.get_astrological_language_rules()}
            {base.get_youtube_tone()}

        STRUCTURE OBLIGATOIRE:

        SYNTHÈSE INSPIRANTE:
        - Récapitulatif poétique de l'énergie de la semaine
        - Message d'espoir et d'encouragement
        - Lien entre tous les signes dans cette énergie commune

        RITUEL HEBDOMADAIRE GUIDÉ :
        - Méditation spécifique à la semaine (étapes détaillées)
        - Affirmations à répéter quotidiennement
        - Pratique énergétique simple (respiration, visualisation)
        - Meilleur moment pour pratiquer

        CONSEILS PRATIQUES UNIVERSELS:
        - 3 actions concrètes valables pour tous les signes
        - Element à privilégier (eau, feu, terre, air)
        - Couleurs ou objets porte-bonheur de la semaine

        CALL-TO-ACTION ENGAGEANT :
        - Invitation chaleureuse à s'abonner
        - Demande de commentaires spécifique ("Quel signe vous a le plus parlé ?")
        - Encouragement au partage avec une raison émotionnelle
        - Teasing de la semaine prochaine
        - Rappel des autres contenus (horoscopes quotidiens, etc.)

        EXEMPLES DE FORMULATIONS ENGAGEANTES:
        ✅ "Si cette guidance cosmique a éclairé votre chemin..."
        ✅ "Partagez dans les commentaires quel conseil vous a fait vibrer..."
        ✅ "Abonnez-vous pour ne jamais manquer nos rendez-vous stellaires..."
        """