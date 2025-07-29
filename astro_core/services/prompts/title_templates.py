"""
Templates pour la génération d'horoscopes individuels et quotidiens
"""

from .base_templates import BasePromptTemplates

class TitlePromptTemplates:
    """Templates pour extraction de titres YouTube"""
    
    @staticmethod
    def get_indivual_title_template():
        """Template pour extraire un titre percutant d'un horoscope"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}
            {base.get_french_language_rules()}

            MISSION: Extrais l'idée principale d'un horoscope en un titre YouTube percutant.

            HOROSCOPE À ANALYSER:
            {{horoscope_text}}

            RÈGLES STRICTES POUR LE TITRE:
            - EXACTEMENT 3 à 5 mots maximum
            - Français uniquement, AUCUN mot anglais
            - PAS de nom de signe astrologique
            - PAS de date, année, ou période
            - PAS de guillemets dans la réponse
            - PAS d'explication ou commentaire
            - TITRE ORIGINAL et CRÉATIF (évite les termes génériques)
            - Trouve l'IDÉE UNIQUE de cet horoscope

            ❌ INTERDIS CES TITRES TROP RÉPÉTITIFS
            ✅ PRIVILÉGIE LA CRÉATIVITÉ:
            - Analyse le CONTENU SPÉCIFIQUE de l'horoscope
            - Trouve l'élément le plus MARQUANT ou SURPRENANT
            - Utilise des mots VIVANTS et IMAGÉS

            EXEMPLES À ÉVITER:
            ❌ "Horoscope Lion du 28 juillet"
            ❌ "Your daily horoscope" 
            ❌ "Voici votre prédiction"
            ❌ "Astrologie et prédictions"
            ❌"Énergie de transformation" (déjà trop utilisé)
            ❌ "Élan de motivation" (déjà trop utilisé)
            ❌ "Force intérieure" (trop générique)
            
            THÈMES VARIÉS À EXPLORER:
            - Amour: "rencontre decisive", "cœur qui s'ouvre", "passion nouvelle"
            - Travail: "projet révélateur", "reconnaissance méritée", "tournant professionnel" 
            - Changement: "métamorphose personnelle", "cap nouveau", "réveil intérieur"
            - Succès: "réussite inattendue", "accomplissement majeur", "victoire personnelle"
            
            Réponds UNIQUEMENT avec le titre de 4-8 mots:"""

    @staticmethod
    def get_weekly_title_template():
        """Template pour extraire un titre percutant d'un horoscope"""
        base = BasePromptTemplates()
        
        return f"""{base.get_astrologer_persona()}

            MISSION: Extrais l'idée principale d'un horoscope en un titre YouTube percutant.

            HOROSCOPE À ANALYSER:
            {{horoscope_text}}
            {base.get_french_language_rules()}

            RÈGLES STRICTES POUR LE TITRE:
            - EXACTEMENT 3 à 5 mots maximum
            - Français uniquement, AUCUN mot anglais
            - PAS de nom de signe astrologique
            - PAS de date, année, ou période
            - PAS de guillemets dans la réponse
            - PAS d'explication ou commentaire
            - Titre accrocheur et positif

            EXEMPLES DE BONS TITRES:
            ✅ "Opportunité financière inattendue"
            ✅ "Rencontre amoureuse prometteuse" 
            ✅ "Créativité en pleine expansion"
            ✅ "Confiance retrouvée aujourd'hui"
            ✅ "Énergie de transformation"

            EXEMPLES À ÉVITER:
            ❌ "Horoscope Lion du 28 juillet"
            ❌ "Your daily horoscope" 
            ❌ "Voici votre prédiction"
            ❌ "Astrologie et prédictions"

            THÈMES FRÉQUENTS À UTILISER:
            - Amour: "nouvelle rencontre", "passion renaissante", "harmonie relationnelle"
            - Travail: "opportunité professionnelle", "reconnaissance méritée", "projet créatif"
            - Énergie: "vitalité retrouvée", "élan de motivation", "force intérieure"
            - Transformation: "changement positif", "évolution personnelle", "nouveau départ"

            Réponds UNIQUEMENT avec le titre de 3-5 mots:"""