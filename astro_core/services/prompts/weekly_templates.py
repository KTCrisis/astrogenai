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
        
        ACCUEIL CHALEUREUX (100 mots):
        -"Bienvenue dans votre Guide AstroGenAI hebdomadaire !"
        - Salutation personnalisée selon la saison

        ACCROCHE COSMIQUE (150 mots):
        - Métaphore poétique sur l'énergie de la semaine
        - Image évocatrice du ciel étoilé actuel
        - Teasing de l'événement le plus spectaculaire

        ÉVÉNEMENT PHARE (300 mots):
        - Description détaillée de l'événement cosmique majeur
        - Contexte historique ou symbolique
        - Pourquoi c'est exceptionnel cette semaine
        - Impact émotionnel et spirituel attendu

        PREVIEW DE LA VIDÉO (200 mots):
        - Annonce des sections à venir avec enthousiasme
        - Promesse de révélations personnalisées par signe
        - Mention des rituels/pratiques qui seront partagés
        - Invitation à rester jusqu'à la fin

        TRANSITION VERS LE CONTENU (50 mots):
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
        """Template pour conseils par signe (1200 mots)"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

        MISSION: Écris UNIQUEMENT les conseils détaillés par signe de 1200 mots minimum.

        CONTEXTE ÉNERGÉTIQUE: {{events}}

        {base.get_length_requirements(2000)}
        {base.get_french_language_rules()}
        {base.get_astrological_language_rules()}
        {base.get_youtube_tone()}
        
        RÈGLES ABSOLUES - TRÈS IMPORTANT:
        - Tu DOIS traiter EXACTEMENT les 12 signes ci-dessous
        - Tu ne peux PAS sauter un seul signe
        - Tu ne peux PAS conclure avant d'avoir traité tous les signes
        - Chaque signe doit avoir environ 100 mots

        LISTE OBLIGATOIRE DES 12 SIGNES À TRAITER:
        1. Bélier : [100 mots minimum]
        2. Taureau : [100 mots minimum]
        3. Gémeaux : [100 mots minimum]
        4. Cancer : [100 mots minimum]
        5. Lion : [100 mots minimum]
        6. Vierge : [100 mots minimum]
        7. Balance : [100 mots minimum]
        8. Scorpion : [100 mots minimum]
        9. Sagittaire : [100 mots minimum]
        10. Capricorne : [100 mots minimum]
        11. Verseau : [100 mots minimum]
        12. Poissons : [100 mots minimum]

        FORMAT: "Bélier : ...", "Taureau : ...", etc.

        CONTENU POUR CHAQUE SIGNE:
        ÉNERGIE DE LA SEMAINE (30 mots)
        - Comment cette semaine résonne avec l'énergie du signe
        - Connexion avec les événements cosmiques majeurs
        
        DÉFI PRINCIPAL (25 mots)
        - Obstacle ou tension à surmonter
        - Aspect planétaire qui influence négativement
        
        OPPORTUNITÉ DORÉE (30 mots)
        - Ce qui est favorisé cette semaine
        - Domaine de vie à privilégier (amour, travail, santé, créativité)
        
        CONSEIL PRATIQUE CONCRET (20 mots)
        - Action spécifique à entreprendre
        - Jour de la semaine le plus favorable
        
        À ÉVITER ABSOLUMENT (10 mots)
        - Comportement ou décision à éviter

        VÉRIFICATION FINALE:
        Avant de terminer, compte les signes. Tu dois avoir EXACTEMENT 12 signes.
        Si tu en as moins de 12, CONTINUE jusqu'à avoir les 12.

        Commence maintenant par le Bélier et traite TOUS les 12 signes:"""

    @staticmethod
    def get_conclusion_section_template():
        """Template pour conclusion et rituels (500 mots)"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

            MISSION: Écris UNIQUEMENT une conclusion avec rituels de 500 mots minimum.

            PÉRIODE: {{period}}

            {base.get_length_requirements(500)}
            {base.get_french_language_rules()}
            {base.get_astrological_language_rules()}
            {base.get_youtube_tone()}

        STRUCTURE OBLIGATOIRE:

        SYNTHÈSE INSPIRANTE (100 mots):
        - Récapitulatif poétique de l'énergie de la semaine
        - Message d'espoir et d'encouragement
        - Lien entre tous les signes dans cette énergie commune

        RITUEL HEBDOMADAIRE GUIDÉ (200 mots):
        - Méditation spécifique à la semaine (étapes détaillées)
        - Affirmations à répéter quotidiennement
        - Pratique énergétique simple (respiration, visualisation)
        - Meilleur moment pour pratiquer

        CONSEILS PRATIQUES UNIVERSELS (100 mots):
        - 3 actions concrètes valables pour tous les signes
        - Element à privilégier (eau, feu, terre, air)
        - Couleurs ou objets porte-bonheur de la semaine

        CALL-TO-ACTION ENGAGEANT (100 mots):
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