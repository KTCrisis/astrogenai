#!/usr/bin/env python3
"""
Contexte évolutif pour génération hebdomadaire cohérente
Fichier: astro_core/services/context/weekly_context.py
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class ToneType(Enum):
    """Types de tonalité détectés"""
    MYSTIQUE = "mystique"
    PRATIQUE = "pratique" 
    POETIQUE = "poétique"
    ENERGETIQUE = "énergétique"
    SPIRITUEL = "spirituel"
    BIENVEILLANT = "bienveillant"

class ThemeCategory(Enum):
    """Catégories de thèmes astrologiques"""
    TRANSFORMATION = "transformation_personnelle"
    RELATIONS = "relations_sociales"
    CREATIVITE = "créativité_inspiration"
    CARRIERE = "carrière_ambitions"
    SANTE = "bien_être_santé"
    SPIRITUALITE = "éveil_spirituel"
    FINANCES = "argent_matériel"
    FAMILLE = "famille_foyer"

@dataclass
class WeeklyGenerationContext:
    """
    Contexte évolutif pour maintenir la cohérence narrative
    entre les sections d'une vidéo hebdomadaire
    """
    
    # === CONTENU DÉJÀ GÉNÉRÉ ===
    previous_sections: List[Dict[str, str]] = field(default_factory=list)
    
    # === ÉLÉMENTS DE CONTINUITÉ ===
    themes_introduced: Set[ThemeCategory] = field(default_factory=set)
    tone_style: Optional[ToneType] = None
    key_phrases_used: Set[str] = field(default_factory=set)
    vocabulary_established: Set[str] = field(default_factory=set)
    
    # === DONNÉES ASTRONOMIQUES PARTAGÉES ===
    weekly_events: List[Dict] = field(default_factory=list)
    astral_context: str = ""
    period_description: str = ""
    
    # === MÉTRIQUES ET OBJECTIFS ===
    total_words: int = 0
    target_words: int = 2400
    sections_completed: int = 0
    
    # === CACHE POUR OPTIMISATION ===
    _tone_indicators: Dict[ToneType, List[str]] = field(default_factory=dict)
    _theme_keywords: Dict[ThemeCategory, List[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialise les dictionnaires de détection"""
        self._initialize_detection_patterns()
    
    def _initialize_detection_patterns(self):
        """Initialise les patterns de détection de tonalité et thèmes"""
        
        # Indicateurs de tonalité
        self._tone_indicators = {
            ToneType.MYSTIQUE: [
                "mystères", "voiles", "secrets", "révélations", "énigmes",
                "arcanes", "mystique", "occulte", "ésotérique"
            ],
            ToneType.PRATIQUE: [
                "conseils", "actions", "étapes", "méthode", "pratique",
                "concret", "application", "mise en œuvre", "stratégie"
            ],
            ToneType.POETIQUE: [
                "danse", "symphonie", "mélodie", "tableau", "fresque",
                "poésie", "vers", "lumière dorée", "écrin"
            ],
            ToneType.ENERGETIQUE: [
                "énergie", "vibrations", "pulsations", "rythme", "dynamisme",
                "vitalité", "intensité", "puissance", "force"
            ],
            ToneType.SPIRITUEL: [
                "âme", "esprit", "divin", "sacré", "élévation",
                "transcendance", "éveil", "conscience", "illumination"
            ],
            ToneType.BIENVEILLANT: [
                "douceur", "bienveillance", "accompagne", "guide", "soutient",
                "réconfort", "tendresse", "chaleur", "protection"
            ]
        }
        
        # Mots-clés thématiques
        self._theme_keywords = {
            ThemeCategory.TRANSFORMATION: [
                "transformation", "métamorphose", "évolution", "changement",
                "renaissance", "mutation", "développement personnel"
            ],
            ThemeCategory.RELATIONS: [
                "relations", "amour", "couple", "amitié", "famille",
                "social", "rencontres", "liens", "communication"
            ],
            ThemeCategory.CREATIVITE: [
                "créativité", "inspiration", "art", "expression", "imagination",
                "innovation", "création", "artistique", "talents"
            ],
            ThemeCategory.CARRIERE: [
                "carrière", "travail", "profession", "ambitions", "réussite",
                "projets", "objectifs", "leadership", "reconnaissance"
            ],
            ThemeCategory.SANTE: [
                "santé", "bien-être", "vitalité", "équilibre", "harmonie",
                "énergie vitale", "forme physique", "repos"
            ],
            ThemeCategory.SPIRITUALITE: [
                "spiritualité", "méditation", "conscience", "éveil",
                "intériorité", "sagesse", "connexion divine"
            ],
            ThemeCategory.FINANCES: [
                "finances", "argent", "matériel", "prospérité", "abondance",
                "investissements", "stabilité financière"
            ],
            ThemeCategory.FAMILLE: [
                "famille", "foyer", "maison", "racines", "héritage",
                "traditions", "liens familiaux", "générations"
            ]
        }
    
    def get_context_summary(self) -> str:
        """
        Résumé du contexte pour injection dans les prompts suivants
        """
        themes_str = ", ".join([theme.value for theme in list(self.themes_introduced)[:5]])
        tone_str = self.tone_style.value if self.tone_style else "non défini"
        
        return f"""CONTEXTE ÉTABLI DANS LES SECTIONS PRÉCÉDENTES:
- Tonalité dominante: {tone_str}
- Thèmes déjà abordés: {themes_str}
- Progression: {self.total_words}/{self.target_words} mots ({self.sections_completed} sections)
- Style vocabulaire: {', '.join(list(self.vocabulary_established)[:8])}

ÉLÉMENTS À MAINTENIR:
- Cohérence tonale avec le style {tone_str}
- Continuité thématique sans répétitions
- Éviter les phrases-clés déjà utilisées: {', '.join(list(self.key_phrases_used)[:5])}"""
    
    def update_from_section(self, section_text: str, section_type: str, section_name: str = ""):
        """
        Met à jour le contexte après génération d'une section
        """
        logger.info(f"📊 Mise à jour contexte depuis section: {section_type}")
        
        # Stockage de la section
        self.previous_sections.append({
            'type': section_type,
            'name': section_name,
            'content': section_text,
            'word_count': len(section_text.split())
        })
        
        # Mise à jour des métriques
        section_words = len(section_text.split())
        self.total_words += section_words
        self.sections_completed += 1
        
        # Analyse du contenu pour extraction
        if section_type == "intro":
            self.tone_style = self._extract_tone(section_text)
            logger.info(f"✅ Tonalité établie: {self.tone_style.value if self.tone_style else 'indéterminée'}")
        
        # Extraction des thèmes et vocabulaire
        new_themes = self._extract_themes(section_text)
        self.themes_introduced.update(new_themes)
        
        new_phrases = self._extract_key_phrases(section_text)
        self.key_phrases_used.update(new_phrases)
        
        new_vocab = self._extract_vocabulary(section_text)
        self.vocabulary_established.update(new_vocab)
        
        logger.info(f"📈 Contexte mis à jour: {section_words} mots, {len(new_themes)} nouveaux thèmes")
    
    def _extract_tone(self, section_text: str) -> Optional[ToneType]:
        """
        Extrait la tonalité dominante d'une section
        """
        text_lower = section_text.lower()
        tone_scores = {}
        
        for tone_type, indicators in self._tone_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                tone_scores[tone_type] = score
        
        if tone_scores:
            dominant_tone = max(tone_scores, key=tone_scores.get)
            logger.debug(f"Scores de tonalité: {tone_scores}")
            return dominant_tone
        
        return None
    
    def _extract_themes(self, section_text: str) -> Set[ThemeCategory]:
        """
        Extrait les thèmes abordés dans une section
        """
        text_lower = section_text.lower()
        detected_themes = set()
        
        for theme, keywords in self._theme_keywords.items():
            theme_score = sum(1 for keyword in keywords if keyword in text_lower)
            if theme_score >= 2:  # Seuil de détection
                detected_themes.add(theme)
        
        return detected_themes
    
    def _extract_key_phrases(self, section_text: str) -> Set[str]:
        """
        Extrait les phrases-clés caractéristiques pour éviter les répétitions
        """
        # Patterns pour phrases astrологiques typiques
        patterns = [
            r"les étoiles [^.!?]*[.!?]",
            r"cette semaine [^.!?]*[.!?]",
            r"l'énergie cosmique [^.!?]*[.!?]",
            r"votre signe [^.!?]*[.!?]",
            r"les influences [^.!?]*[.!?]"
        ]
        
        key_phrases = set()
        for pattern in patterns:
            matches = re.findall(pattern, section_text.lower())
            key_phrases.update(matches[:3])  # Max 3 par pattern
        
        return key_phrases
    
    def _extract_vocabulary(self, section_text: str) -> Set[str]:
        """
        Extrait le vocabulaire astrologique distinctif
        """
        astro_vocab = [
            "conjonction", "trigone", "carré", "opposition", "sextile",
            "ascendant", "maisons", "planètes", "luminaires", "aspects",
            "rétrograde", "direct", "culmination", "éclipse", "nouvelle lune",
            "pleine lune", "équinoxe", "solstice", "transit", "révolution"
        ]
        
        text_lower = section_text.lower()
        found_vocab = {word for word in astro_vocab if word in text_lower}
        
        return found_vocab
    
    def get_repetition_warnings(self) -> List[str]:
        """
        Identifie les risques de répétition pour la prochaine section
        """
        warnings = []
        
        if len(self.key_phrases_used) > 10:
            warnings.append("Attention: beaucoup de phrases-clés déjà utilisées")
        
        if len(self.themes_introduced) >= 6:
            warnings.append("Attention: risque de surcharge thématique")
        
        if self.total_words > self.target_words * 0.8:
            warnings.append("Attention: approche de la limite de mots")
        
        return warnings
    
    def get_remaining_word_budget(self, sections_remaining: int) -> int:
        """
        Calcule le budget de mots restant par section
        """
        remaining_words = max(0, self.target_words - self.total_words)
        if sections_remaining <= 0:
            return 0
        
        return remaining_words // sections_remaining
    
    def should_vary_vocabulary(self) -> bool:
        """
        Détermine s'il faut varier le vocabulaire
        """
        return len(self.vocabulary_established) > 15
    
    def get_alternative_themes(self) -> List[ThemeCategory]:
        """
        Retourne les thèmes pas encore abordés
        """
        all_themes = set(ThemeCategory)
        return list(all_themes - self.themes_introduced)
    
    def export_context_summary(self) -> Dict:
        """
        Exporte un résumé complet du contexte pour debugging
        """
        return {
            'sections_completed': self.sections_completed,
            'total_words': self.total_words,
            'tone_style': self.tone_style.value if self.tone_style else None,
            'themes_count': len(self.themes_introduced),
            'themes_list': [t.value for t in self.themes_introduced],
            'key_phrases_count': len(self.key_phrases_used),
            'vocabulary_size': len(self.vocabulary_established),
            'completion_percentage': (self.total_words / self.target_words) * 100,
            'sections_data': [
                {
                    'type': s['type'],
                    'words': s['word_count'],
                    'name': s.get('name', '')
                } for s in self.previous_sections
            ]
        }