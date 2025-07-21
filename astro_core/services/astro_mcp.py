#!/usr/bin/env python3
"""
MCP Astro Generator Server avec FastMCP
Serveur MCP génération automatique d'horoscopes avec Ollama
"""

import datetime
import logging
import sys
import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
from pathlib import Path
from config import settings

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️  Ollama non disponible")

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️  FastMCP non disponible")

try:
    astrochart_path = os.path.join(os.path.dirname(__file__), 'astrochart')
    if astrochart_path not in sys.path:
        sys.path.insert(0, astrochart_path)
    from astrochart_mcp import astro_calculator  
    ASTROCHART_AVAILABLE = True
    print("✅ AstroChart Calculator importé")
except ImportError:
    ASTROCHART_AVAILABLE = False
    astro_calculator = None
    print("⚠️ AstroChart non disponible")
try:
    from gtts import gTTS
    from mutagen.mp3 import MP3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️  TTS non disponible (gTTS, mutagen)")
try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  Matplotlib non disponible pour les cartes astrales")

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION CENTRALISÉE
# =============================================================================

@dataclass
class AstralContext:
    date: str
    day_of_week: str
    lunar_phase: str
    season: str
    influential_planets: List[Dict[str, str]]
    lunar_cycle_day: int
    seasonal_energy: str

@dataclass
class SignMetadata:
    name: str
    dates: str
    element: str
    ruling_planet: str
    constellation: str
    traits: List[str]
    colors: List[str]
    stone: str
    keywords: List[str]
    compatible_signs: List[str]

@dataclass
class HoroscopeResult:
    sign: str
    date: str
    horoscope_text: str
    astral_context: AstralContext
    metadata: SignMetadata
    lunar_influence_score: float
    generation_timestamp: str
    word_count: int
    astrochart_data: Optional[Dict] = None  

# =============================================================================
# CLASS ASTROCHART IMAGE GENERATOR
# =============================================================================

class AstroChartImageGenerator:
    """Générateur d'images de cartes astrales intégré"""
    
    def __init__(self, astro_calculator=None):
        self.images_dir = settings.STATIC_CHARTS_DIR
        self.images_dir.mkdir(exist_ok=True, parents=True)
        
        self.chart_image_size = (6, 6) 
        self.chart_background_color = "#0c0e1c" 
        self.chart_text_color = "#e6e6fa" 
        self.chart_image_format = "png"
        self.chart_image_dpi = 200
        
        # Dictionnaires de correspondances
        self.planet_symbols = {
            'sun': '☉', 'moon': '☽', 'mercury': '☿', 'venus': '♀', 'mars': '♂', 
            'jupiter': '♃', 'saturn': '♄', 'uranus': '♅', 'neptune': '♆', 'pluto': '♇'
        }
        self.zodiac_symbols = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
        self.planet_colors = {
            'sun': '#FFD700', 'moon': '#C0C0C0', 'mercury': '#FFA500', 
            'venus': '#FF69B4', 'mars': '#FF4500', 'jupiter': '#4169E1', 
            'saturn': '#8B4513', 'uranus': '#40E0D0', 'neptune': '#4B0082', 
            'pluto': '#8B008B'
        }
        self.name_to_key_map = {
            'soleil': 'sun', 'lune': 'moon', 'mercure': 'mercury', 'vénus': 'venus',
            'mars': 'mars', 'jupiter': 'jupiter', 'saturne': 'saturn',
            'uranus': 'uranus', 'neptune': 'neptune', 'pluton': 'pluto'
        }

    def create_chart_from_positions(self, positions, date: datetime.date, 
                                  output_path: Optional[str] = None) -> Optional[str]:
        """Crée une carte à partir des positions calculées par AstroCalculator"""
        try:
            if not MATPLOTLIB_AVAILABLE:
                logger.error("Matplotlib non disponible pour génération d'images")
                return None
            if not positions:
                logger.error("Aucune position planétaire fournie")
                return None
            
            fig, ax = plt.subplots(figsize=self.chart_image_size, subplot_kw=dict(projection='polar'))
            ax.set_facecolor(self.chart_background_color)
            fig.patch.set_facecolor(self.chart_background_color)
            
            for i in range(12):
                angle = np.radians(i * 30)
                ax.plot([angle, angle], [0.6, 1.1], color=self.chart_text_color, alpha=0.5, linewidth=1)
                sign_angle = np.radians(i * 30 + 15)
                ax.text(sign_angle, 1.05, self.zodiac_symbols[i], ha='center', va='center', fontsize=20, color=self.chart_text_color, weight='bold')
            
            for planet_data in positions:
                # Utiliser le dictionnaire de mapping pour trouver la bonne clé
                planet_key = self.name_to_key_map.get(planet_data.name.lower(), "unknown")
                
                longitude = planet_data.longitude
                degree_in_sign = planet_data.degree_in_sign
                angle = np.radians(longitude)
                color = self.planet_colors.get(planet_key, 'white')
                symbol = self.planet_symbols.get(planet_key, '?')
                
                ax.scatter(angle, 0.85, s=300, c=color, edgecolors='white', linewidth=2, zorder=10)
                ax.text(angle, 0.85, symbol, ha='center', va='center', fontsize=16, color='black', weight='bold', zorder=11)
                ax.text(angle, 0.75, f"{degree_in_sign:.0f}°", ha='center', va='center', fontsize=8, color='white')
            
            ax.set_theta_zero_location('N')  
            ax.set_theta_direction(1)        
            
            ax.set_ylim(0, 1.2)
            ax.set_rticks([])
            ax.set_thetagrids([])
            ax.grid(False)
            
            ax.set_title(f"skyfield(de440s) - {date.strftime('%d/%m/%Y')}", fontsize=8, color=self.chart_text_color, pad=30, weight='bold')
            legend_text = []
            for planet_data in positions:
                planet_key = self.name_to_key_map.get(planet_data.name.lower(), "unknown")
                symbol = self.planet_symbols.get(planet_key, '?')
                sign = planet_data.sign_name
                degree = planet_data.degree_in_sign
                legend_text.append(f"{symbol} {planet_data.name.title()}: {sign} {degree:.1f}°")
            
            fig.text(0.98, 0.98, '\n'.join(legend_text), 
                    fontsize=6, 
                    color='white', 
                    ha='right',  
                    va='top',    
                    fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.4", facecolor='black', alpha=0.8))
            if not output_path:
                filename = f"astro_chart_{date.strftime('%Y%m%d')}.{self.chart_image_format}"
                output_path = self.images_dir / filename
            
            plt.savefig(output_path, facecolor=self.chart_background_color, dpi=self.chart_image_dpi, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"✅ Carte astrologique sauvegardée: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Erreur création carte astrologique: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None

# =============================================================================
# CLASS ASTRO GENERATOR
# =============================================================================

class AstroGenerator:
    """Générateur d'horoscopes astrologique"""
    
    def __init__(self):
        self.ollama_model = settings.OLLAMA_TEXT_MODEL
        self.audio_output_dir = settings.GENERATED_AUDIO_DIR
        self.max_retries = 3 
        self.horoscope_min_words = 20
        self.horoscope_max_words = 50
        self.signs_data = self._load_signs_data()
        self.planetary_influences = self._load_planetary_influences()
        self.audio_lang = "fr"
        os.makedirs(self.audio_output_dir, exist_ok=True)
        if MATPLOTLIB_AVAILABLE:
            self.chart_generator = AstroChartImageGenerator(astro_calculator)
        else:
            self.chart_generator = None
        if ASTROCHART_AVAILABLE:
            self.astro_calculator = astro_calculator

    def _load_signs_data(self) -> Dict[str, SignMetadata]:
        signs_raw = {
            "aries": {"name": "Bélier", "dates": "21 mars - 19 avril", "element": "Feu", "ruling_planet": "Mars", "constellation": "Aries", "traits": ["énergique", "impulsif", "leader", "courageux", "direct"], "colors": ["rouge", "orange vif"], "stone": "Diamant", "keywords": ["action", "initiative", "énergie", "nouveauté"], "compatible_signs": ["Lion", "Sagittaire", "Gémeaux"]},
            "taurus": {"name": "Taureau", "dates": "20 avril - 20 mai", "element": "Terre", "ruling_planet": "Vénus", "constellation": "Taurus", "traits": ["stable", "sensuel", "têtu", "pratique", "loyal"], "colors": ["vert", "rose"], "stone": "Émeraude", "keywords": ["stabilité", "plaisir", "patience", "beauté"], "compatible_signs": ["Vierge", "Capricorne", "Cancer"]},
            "gemini": {"name": "Gémeaux", "dates": "21 mai - 20 juin", "element": "Air", "ruling_planet": "Mercure", "constellation": "Gemini", "traits": ["communicatif", "curieux", "adaptable", "versatile", "sociable"], "colors": ["jaune", "argent"], "stone": "Agate", "keywords": ["communication", "curiosité", "adaptabilité", "échange"], "compatible_signs": ["Balance", "Verseau", "Bélier"]},
            "cancer": {"name": "Cancer", "dates": "21 juin - 22 juillet", "element": "Eau", "ruling_planet": "Lune", "constellation": "Cancer", "traits": ["émotionnel", "protecteur", "intuitif", "familial", "sensible"], "colors": ["blanc", "argenté"], "stone": "Pierre de lune", "keywords": ["émotion", "famille", "intuition", "protection"], "compatible_signs": ["Scorpion", "Poissons", "Taureau"]},
            "leo": {"name": "Lion", "dates": "23 juillet - 22 août", "element": "Feu", "ruling_planet": "Soleil", "constellation": "Leo", "traits": ["généreux", "fier", "créatif", "charismatique", "théâtral"], "colors": ["or", "orange"], "stone": "Rubis", "keywords": ["créativité", "leadership", "générosité", "spectacle"], "compatible_signs": ["Bélier", "Sagittaire", "Gémeaux"]},
            "virgo": {"name": "Vierge", "dates": "23 août - 22 septembre", "element": "Terre", "ruling_planet": "Mercure", "constellation": "Virgo", "traits": ["perfectionniste", "analytique", "serviable", "modeste", "pratique"], "colors": ["bleu marine", "gris"], "stone": "Saphir", "keywords": ["précision", "service", "analyse", "amélioration"], "compatible_signs": ["Taureau", "Capricorne", "Cancer"]},
            "libra": {"name": "Balance", "dates": "23 septembre - 22 octobre", "element": "Air", "ruling_planet": "Vénus", "constellation": "Libra", "traits": ["équilibré", "diplomatique", "esthète", "indécis", "charmant"], "colors": ["bleu pastel", "rose"], "stone": "Opale", "keywords": ["harmonie", "beauté", "justice", "partenariat"], "compatible_signs": ["Gémeaux", "Verseau", "Lion"]},
            "scorpio": {"name": "Scorpion", "dates": "23 octobre - 21 novembre", "element": "Eau", "ruling_planet": "Pluton", "constellation": "Scorpius", "traits": ["intense", "mystérieux", "passionné", "déterminé", "magnétique"], "colors": ["rouge sombre", "noir"], "stone": "Topaze", "keywords": ["transformation", "passion", "mystère", "pouvoir"], "compatible_signs": ["Cancer", "Poissons", "Vierge"]},
            "sagittarius": {"name": "Sagittaire", "dates": "22 novembre - 21 décembre", "element": "Feu", "ruling_planet": "Jupiter", "constellation": "Sagittarius", "traits": ["aventurier", "optimiste", "philosophe", "libre", "direct"], "colors": ["violet", "turquoise"], "stone": "Turquoise", "keywords": ["aventure", "sagesse", "liberté", "expansion"], "compatible_signs": ["Bélier", "Lion", "Balance"]},
            "capricorn": {"name": "Capricorne", "dates": "22 décembre - 19 janvier", "element": "Terre", "ruling_planet": "Saturne", "constellation": "Capricornus", "traits": ["ambitieux", "discipliné", "responsable", "patient", "traditionaliste"], "colors": ["marron", "noir"], "stone": "Grenat", "keywords": ["ambition", "structure", "persévérance", "réussite"], "compatible_signs": ["Taureau", "Vierge", "Scorpion"]},
            "aquarius": {"name": "Verseau", "dates": "20 janvier - 18 février", "element": "Air", "ruling_planet": "Uranus", "constellation": "Aquarius", "traits": ["original", "indépendant", "humanitaire", "rebelle", "visionnaire"], "colors": ["bleu électrique", "argent"], "stone": "Améthyste", "keywords": ["innovation", "humanité", "indépendance", "futur"], "compatible_signs": ["Gémeaux", "Balance", "Sagittaire"]},
            "pisces": {"name": "Poissons", "dates": "19 février - 20 mars", "element": "Eau", "ruling_planet": "Neptune", "constellation": "Pisces", "traits": ["intuitif", "artistique", "empathique", "rêveur", "spirituel"], "colors": ["bleu mer", "violet"], "stone": "Aigue-marine", "keywords": ["intuition", "art", "spiritualité", "compassion"], "compatible_signs": ["Cancer", "Scorpion", "Capricorne"]},
        }
        return {key: SignMetadata(**data) for key, data in signs_raw.items()}

    def _load_planetary_influences(self) -> Dict[str, Dict]:
        return {
            "mercury": {"domains": ["communication", "voyage", "intellect", "commerce"], "direct": "clarté mentale et communication fluide", "retrograde": "malentendus possibles, patience requise"},
            "venus": {"domains": ["amour", "beauté", "argent", "art"], "direct": "harmonie en amour et créativité épanouie", "retrograde": "remise en question des relations"},
            "mars": {"domains": ["énergie", "action", "conflit", "passion"], "direct": "énergie débordante et initiatives couronnées de succès", "retrograde": "frustrations possibles, agir avec prudence"},
            "jupiter": {"domains": ["chance", "expansion", "sagesse", "voyage"], "direct": "opportunités et croissance positive", "retrograde": "réflexion intérieure et réévaluation des objectifs"},
            "saturn": {"domains": ["discipline", "responsabilité", "limites", "karma"], "direct": "structure et récompenses du travail accompli", "retrograde": "leçons importantes et restructuration nécessaire"}
        }

    def _calculate_lunar_phase(self, date: datetime.date) -> tuple[str, int]:
        reference, cycle_days = datetime.date(2024, 1, 11), 29.5
        cycle_day = ((date - reference).days) % cycle_days
        if cycle_day < 7.4: phase = "Nouvel Lune"
        elif cycle_day < 14.8: phase = "Lune croissante"
        elif cycle_day < 22.1: phase = "Pleine Lune"
        else: phase = "Lune décroissante"
        return phase, int(cycle_day)
    
    def _get_season(self, date: datetime.date) -> str:
        month = date.month
        if month in [12, 1, 2]: return "hiver"
        if month in [3, 4, 5]: return "printemps"
        if month in [6, 7, 8]: return "été"
        return "automne"
    
    def get_astral_context(self, date: datetime.date) -> AstralContext:
        lunar_phase, cycle_day = self._calculate_lunar_phase(date)
        season = self._get_season(date)
        energies = {"hiver": "introspection et renouveau", "printemps": "croissance et nouveaux départs", "été": "expansion et réalisation", "automne": "récolte et transformation"}
        planets = []
        if date.month in [3, 7, 11]: planets.append({"name": "Mercure", "state": "rétrograde", "influence": self.planetary_influences["mercury"]["retrograde"]})
        if date.day % 7 == 0: planets.append({"name": "Jupiter", "state": "direct", "influence": self.planetary_influences["jupiter"]["direct"]})
        if date.day % 2 == 1: planets.append({"name": "Mars", "state": "direct", "influence": self.planetary_influences["mars"]["direct"]})
        if date.month in [6, 7, 8]: planets.append({"name": "Vénus", "state": "direct", "influence": self.planetary_influences["venus"]["direct"]})
        return AstralContext(date=date.strftime("%Y-%m-%d"), day_of_week=date.strftime("%A"), lunar_phase=lunar_phase, season=season, influential_planets=planets[:2], lunar_cycle_day=cycle_day, seasonal_energy=energies.get(season, "équilibre"))

    def get_sign_metadata(self, sign: str) -> Optional[SignMetadata]:
        return self.signs_data.get(sign.lower())

    # =============================================================================
    # MÉTHODES DE VALIDATION
    # =============================================================================

    def _validate_sign(self, sign: str) -> str:
        """Valide et normalise un signe astrologique."""
        if not sign:
            raise ValueError("Signe manquant")
        
        sign_lower = sign.lower().strip()
        if sign_lower not in self.signs_data:
            available = ", ".join(self.signs_data.keys())
            raise ValueError(f"Signe invalide '{sign}'. Disponibles: {available}")
        
        return sign_lower

    def _validate_date(self, date_str: Optional[str]) -> datetime.date:
        """Valide et parse une date."""
        if not date_str:
            return datetime.date.today()
        
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Format de date invalide '{date_str}'. Utilisez YYYY-MM-DD")

    # =============================================================================
    # MÉTHODES UTILITAIRES 
    # =============================================================================

    def calculate_lunar_influence(self, sign: str, date: datetime.date) -> float:
        """Calcule l'influence lunaire sur un signe pour une date donnée."""
        try:
            # Validation des entrées
            validated_sign = self._validate_sign(sign)
            sign_data = self.get_sign_metadata(validated_sign)
            astral_context = self.get_astral_context(date)
            
            # Scores par phase lunaire
            phase_scores = {
                "Nouvelle lune": 0.2,      # Nouvelle lune - faible influence
                "Lune croissante ": 0.6,   # Lune croissante - influence modérée
                "Pleine lune ": 1.0,     # Pleine lune - influence maximale
                "Lune décroissante": 0.4    # Lune décroissante - influence modérée-faible
            }
            
            # Multiplicateurs par élément (certains éléments plus sensibles à la lune)
            element_multipliers = {
                "Eau": 1.2, 
                "Air": 0.9,
                "Feu": 0.8,
                "Terre": 0.7
            }
            
            # Score de base selon la phase
            base_score = phase_scores.get(astral_context.lunar_phase, 0.5)
            # Multiplicateur selon l'élément du signe
            element_mult = element_multipliers.get(sign_data.element, 1.0)
            # Influence du jour dans le cycle lunaire (pic au milieu du cycle)
            cycle_influence = 1.0 - abs(astral_context.lunar_cycle_day - 14.5) / 14.5
            # Calcul final
            final_score = base_score * element_mult * cycle_influence
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Erreur calcul influence lunaire pour {sign}: {e}")
            return 0.5


    async def _call_ollama_with_retry(self, prompt: str) -> str:
        """Appelle Ollama avec retry automatique."""
        if not OLLAMA_AVAILABLE:
            raise Exception("Ollama non disponible")
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Essayer avec la bibliothèque ollama
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    options={
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'num_predict': 2500, 
                        'stop': None  
                    }
                )
                return response['message']['content']
                
            except Exception as e:
                last_error = e
                logger.warning(f"Tentative {attempt + 1}/{self.max_retries} échouée: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Backoff progressif
        
        raise Exception(f"Impossible de générer l'horoscope après {self.max_retries} tentatives: {last_error}")

    def _create_horoscope_prompt(self, sign, astral_context, astrochart_data=None):
        """Crée le prompt pour générer un horoscope avec données astronomiques précises"""
        sign_data = self.get_sign_metadata(sign)
    # =============================================================================
    # PROMPT ASTROCHART
    # =============================================================================
        if astrochart_data:
            # UTILISER LES VRAIES DONNÉES ASTRONOMIQUES
            chart_data = astrochart_data["chart_data"]
            positions = astrochart_data["positions"] 
            aspects = astrochart_data["aspects"]
            
            # 1. CONSTRUIRE LA LISTE DES POSITIONS PLANÉTAIRES
            positions_text = "POSITIONS PLANÉTAIRES EXACTES:\n"
            for planet in positions:
                positions_text += f"- {planet.name} ({planet.symbol}): {planet.degree_in_sign:.1f}° en {planet.sign_name}"
                if planet.retrograde:
                    positions_text += " (Rétrograde)"
                positions_text += f" (longitude: {planet.longitude:.1f}°)\n"
            
            # 2. CONSTRUIRE LA LISTE DES ASPECTS MAJEURS
            aspects_text = "ASPECTS PLANÉTAIRES ACTIFS:\n"
            if aspects:
                for aspect in aspects[:5]:  # Limiter aux 5 plus importants
                    exactness = "EXACT" if aspect.exact else f"orbe {aspect.orb:.1f}°"
                    aspects_text += f"- {aspect.planet1} {aspect.aspect_type.upper()} {aspect.planet2} ({exactness})\n"
            else:
                aspects_text += "- Aucun aspect majeur aujourd'hui\n"
            
            # 3. INFORMATIONS LUNAIRES PRÉCISES
            lunar_info = f"PHASE LUNAIRE: {chart_data.moon_phase}"
            
            # 4. PROMPT ENRICHI AVEC VRAIES DONNÉES
            prompt = f"""Tu es un astrologue expert et bienveillant s'appuyant sur les données astronomiques.

    DONNÉES ASTRONOMIQUES RÉELLES pour le {chart_data.date}:

    {positions_text}
    {aspects_text}
    {lunar_info}

    SIGNE À ANALYSER: {sign_data.name} ({sign_data.dates})
    Élément: {sign_data.element} | Planète maîtresse: {sign_data.ruling_planet}
    Traits: {', '.join(sign_data.traits)}

    INSTRUCTIONS:
    - Crée un horoscope de {self.horoscope_min_words}-{self.horoscope_max_words} mots
    - UTILISE les positions et aspects RÉELS ci-dessus (pas des généralités)
    - Mentionne 1 seul aspect le plus significatif s'ils concernent le signe
    - N'INDIQUE pas les orbes et degrés comme par exemple : Trine (30°) ou Sextile (60°) quand tu réponds, donne juste Trine, Sextile
    - Adapte selon la phase lunaire actuelle
    - Ta réponse doit être en français uniquement
    - Termine par une phrase complète avec ponctuation
    - Ton moderne, bienveillant, précis et motivant
    - Donne 1 conseil pratique adapté au signe.
    - N'utilise pas le mot Astrologue pour te définir mais "AstroGenAI"
    - Commence par "Cher {sign_data.name},"

    Réponds UNIQUEMENT avec le texte de l'horoscope."""

        else:
    # =============================================================================
    # PROMPT STANDARD
    # =============================================================================
            planets_str = ", ".join([f"{p['name']} ({p['state']})" for p in astral_context.influential_planets])
            prompt = f"""Tu es un astrologue expert et bienveillant. Écris un horoscope court et engageant pour le signe {sign_data.name} ({sign_data.dates}).

    CONTEXTE ASTROLOGIQUE:
    - Date: {astral_context.date} ({astral_context.day_of_week})
    - Saison: {astral_context.season} - {astral_context.seasonal_energy}
    - Phase lunaire: {astral_context.lunar_phase}
    - Planètes influentes: {planets_str}

    CARACTÉRISTIQUES DU SIGNE:
    - Élément: {sign_data.element}
    - Planète maîtresse: {sign_data.ruling_planet}
    - Traits principaux: {', '.join(sign_data.traits)}

    INSTRUCTIONS:
    - Horoscope de {self.horoscope_min_words}-{self.horoscope_max_words} mots maximum.
    - Ta réponse doit être en français uniquement
    - Termine par une phrase complète avec ponctuation
    - Ton moderne, bienveillant et motivant.
    - Donne 1 conseil pratique adapté au signe.
    - Commence par "Cher {sign_data.name},"
    - Adapte le contenu au contexte astral fourni.
    - N'utilise pas le mot Astrologue pour te définir mais AstroGenAI

    Réponds UNIQUEMENT avec le texte de l'horoscope."""
        return prompt

    async def generate_single_horoscope(self, sign: str, date: Optional[datetime.date] = None, astrochart_data=None, generate_audio: bool = False):
        try:  

            validated_sign = self._validate_sign(sign)
            validated_date = date or datetime.date.today()
            
            sign_data = self.get_sign_metadata(validated_sign)
            astral_context = self.get_astral_context(validated_date)
            
            astrochart_data = None
            if ASTROCHART_AVAILABLE and astro_calculator:
                try:
                    positions = astro_calculator.calculate_positions(validated_date)
                    astrochart_data = {
                        "chart_data": astro_calculator.generate_chart_data(validated_date),
                        "positions": positions, 
                        "aspects": astro_calculator.calculate_aspects(positions)
                    }
                    logger.info("✅ AstroChart data calculée")
                except Exception as e:
                    logger.warning(f"⚠️  Erreur AstroChart, fallback: {e}")
                    astrochart_data = None
            
            prompt = self._create_horoscope_prompt(validated_sign, astral_context, astrochart_data)
            logger.info(f"--- Prompt {'enrichi' if astrochart_data else 'standard'} envoyé à Ollama ---")
            
            horoscope_text = await self._call_ollama_with_retry(prompt)
            
            # Calculer l'influence lunaire
            lunar_influence = self.calculate_lunar_influence(validated_sign, validated_date)
            
            result = HoroscopeResult(
                sign=sign_data.name,
                date=astral_context.date,
                horoscope_text=horoscope_text,
                astral_context=astral_context,
                metadata=sign_data,
                lunar_influence_score=lunar_influence,
                generation_timestamp=datetime.datetime.now().isoformat(),
                word_count=len(horoscope_text.split()),
                astrochart_data=astrochart_data  # ✅ AJOUTER SI VOUS AVEZ MODIFIÉ LA DATACLASS
            )
            
            # Génération audio optionnelle
            audio_path, audio_duration = None, 0.0
            if generate_audio and TTS_AVAILABLE:
                audio_path, audio_duration = self.generate_tts_audio(
                    horoscope_text, 
                    f"{validated_sign}_{validated_date.strftime('%Y%m%d')}"
                )
            elif generate_audio:
                logger.warning("Génération audio demandée mais TTS non disponible")
            
            return result, audio_path, audio_duration
            
        except Exception as e:  
            logger.error(f"Erreur génération horoscope pour {sign}: {e}")
            raise     

    async def generate_daily_horoscopes(self, date: Optional[datetime.date] = None) -> Dict[str, HoroscopeResult]:
        """Génère tous les horoscopes du jour en parallèle - Version optimisée."""
        validated_date = date or datetime.date.today()
        logger.info(f"Génération des horoscopes pour {validated_date}")

        # Création des tâches parallèles
        tasks = []
        for sign_key in self.signs_data.keys():
            task = self.generate_single_horoscope(sign_key, validated_date)
            tasks.append((sign_key, task))

        # Exécution parallèle avec gestion d'erreur
        results = await asyncio.gather(
            *[task for _, task in tasks], 
            return_exceptions=True
        )

        # Traitement des résultats
        horoscopes = {}
        for i, (sign_key, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Erreur génération {sign_key}: {result}")
                horoscopes[sign_key] = {"error": str(result)}
            else:
                horoscopes[sign_key] = result[0]  # HoroscopeResult seulement

        success_count = sum(1 for r in horoscopes.values() if not isinstance(r, dict) or "error" not in r)
        logger.info(f"Génération terminée: {success_count}/{len(self.signs_data)} horoscopes créés")

        return horoscopes

    async def generate_weekly_summary(self, start_date: datetime.date, end_date: datetime.date) -> Tuple[str, str, float]:
        """
        Génère le script et l'audio pour la vidéo "Hub" hebdomadaire.
        Retourne (script_text, audio_path, audio_duration).
        """
        logger.info(f"Génération du résumé hebdomadaire du {start_date} au {end_date}")

        # 1. Obtenir les données astrologiques de la semaine
        # Assurez-vous que astro_calculator est accessible via self.
        weekly_events = self.astro_calculator.get_major_events_for_week(start_date, end_date)

        if not weekly_events:
            logger.warning("Aucun événement majeur trouvé pour la semaine.")
            return "Aucun événement majeur cette semaine.", None, 0.0

        # 2. Construire le prompt pour Ollama
        events_str = "\n".join([f"- Le {e['date']}: {e['description']} ({e['type']})" for e in weekly_events])
        print(events_str)

        prompt = f"""
        Tu es un astrologue expert et un conteur captivant pour une chaîne YouTube.
        Ta mission est de créer un script engageant de 8-10 minutes (environ 1300 mots) pour la vidéo "Guide Astrologique de la Semaine".

        CONTEXTE POUR LA SEMAINE DU {start_date.strftime('%d/%m')} AU {end_date.strftime('%d/%m')}:
        Événements Cosmiques Clés:
        {events_str}

        INSTRUCTIONS:
        - Ta réponse doit être en français uniquement
        - Termine par une phrase complète avec ponctuation
        - Environ 1300 mots
        - Ne dis pas les sections (ex : Titre)
        
      
    STRUCTURE DU SCRIPT REQUIS :
        1.  Introduction: Commence par une accroche puissante. Présente l'énergie générale de la semaine en te basant sur l'événement le plus important.
        2.  Analyse des Événements Majeurs: Plonge en détail dans 2 ou 3 des événements les plus significatifs listés ci-dessus. Explique leur signification et leur impact potentiel de manière claire et accessible.
        3.  Conseils par Signe: Donne un conseil court (une phrase) et percutant pour chacun des 12 signes. Suis STRICTEMENT la structure et les groupes ci-dessous.
            - Fais des transitions entre chaque groupe de Signes comme : commencons par les Signes de Feu, enchainons avec les Signes de Terre, passons aux Signes d'air et pour finir les Signes d'air)
            - Signes de Feu :
                - Bélier: [ton conseil ici]
                - Lion: [ton conseil ici]
                - Sagittaire: [ton conseil ici]
            - Signes de Terre:
                - Taureau: [ton conseil ici]
                - Vierge: [ton conseil ici]
                - Capricorne: [ton conseil ici]
            - Signes d'Air:
                - Gémeaux: [ton conseil ici]
                - Balance: [ton conseil ici]
                - Verseau: [ton conseil ici]
            - Signes d'Eau :
                - Cancer: [ton conseil ici]
                - Scorpion: [ton conseil ici]
                - Poissons: [ton conseil ici]
        4.Conclusion: Résume l'énergie de la semaine et termine par un appel à l'action positif et engageant comme "Abonnez-vous pour votre guide hebdomadaire et dites-moi en commentaire quel événement vous inspire le plus cette semaine !".
        
        TON:
        - Inspirant, bienveillant et moderne.
        - Évite le jargon trop technique.
        - Sois un guide, pas un devin.
        - Adapte le contenu au 
        - N'utilise pas le mot Astrologue pour te définir mais AstroGenAI
        """

        # 3. Appeler Ollama pour générer le script
        logger.info("Génération du script hebdomadaire avec Ollama...")
        script_text = await self._call_ollama_with_retry(prompt)

        # 4. Générer le fichier audio long
        logger.info("Génération du fichier audio TTS pour le script hebdomadaire...")
        filename = f"hub_weekly_{start_date.strftime('%Y%m%d')}"
        audio_path, audio_duration = self.generate_tts_audio(script_text, filename)

        logger.info(f"Résumé hebdomadaire généré. Durée audio : {audio_duration:.2f}s")
        return script_text, audio_path, audio_duration

    def generate_tts_audio(self, text: str, filename: str) -> Tuple[Optional[str], float]:
        """Génère un fichier audio à partir du texte - Version améliorée."""
        if not TTS_AVAILABLE:
            logger.warning("TTS non disponible")
            return None, 0.0
        
        try:
            output_path = os.path.join(self.audio_output_dir, f"{filename}.mp3")
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(output_path):
                logger.info(f"Fichier audio existant trouvé: {output_path}")
                try:
                    duration = MP3(output_path).info.length
                    return output_path, duration
                except:
                    # Si erreur de lecture, régénérer
                    logger.warning(f"Fichier audio corrompu, régénération: {output_path}")
                    os.remove(output_path)
            logger.info("Normalisation du texte pour la synthèse vocale...")
            normalized_text = ' '.join(text.replace('\n', ' ').split())
            cleaned_text = normalized_text.replace('**', '').replace('*', '')
            # Générer le fichier audio
            tts = gTTS(text=cleaned_text, lang=self.audio_lang, slow=False)
            tts.save(output_path)
            
            # Obtenir la durée
            try:
                duration = MP3(output_path).info.length
            except:
                # Estimation approximative si erreur de lecture
                duration = len(text.split()) * 0.5  # ~0.5 sec par mot
                logger.warning(f"Impossible de lire la durée, estimation: {duration:.1f}s")
            
            logger.info(f"Audio généré: {output_path} (Durée: {duration:.2f}s)")
            return output_path, duration
            
        except Exception as e:
            logger.error(f"Erreur génération TTS: {e}")
            return None, 0.0

    # =============================================================================
    # MÉTHODES UTILITAIRES SUPPLÉMENTAIRES
    # =============================================================================

    def get_system_status(self) -> Dict:
        """Retourne l'état du système."""
        status = {
            "ollama_available": OLLAMA_AVAILABLE,
            "fastmcp_available": FASTMCP_AVAILABLE,
            "tts_available": TTS_AVAILABLE,
            "signs_count": len(self.signs_data),
            "audio_files_count": 0
        }
        
        # Compter les fichiers audio
        try:
            audio_files = [f for f in os.listdir(self.audio_output_dir) if f.endswith('.mp3')]
            status["audio_files_count"] = len(audio_files)
        except:
            pass
        
        return status

    def export_horoscopes_data(self, horoscopes: Dict) -> str:
        """Exporte les horoscopes au format JSON."""
        try:
            export_data = {
                "export_timestamp": datetime.datetime.now().isoformat(),
                "total_horoscopes": len(horoscopes),
                "horoscopes": {}
            }
            
            for sign_key, horoscope in horoscopes.items():
                if isinstance(horoscope, HoroscopeResult):
                    export_data["horoscopes"][sign_key] = asdict(horoscope)
                else:
                    export_data["horoscopes"][sign_key] = horoscope
            
            filename = f"horoscopes_export_{datetime.date.today().strftime('%Y%m%d')}.json"
            filepath = os.path.join(self.audio_output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Export réussi: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erreur export: {e}")
            raise

# =============================================================================
# INITIALISATION ET OUTILS MCP
# =============================================================================

astro_generator = AstroGenerator()

if FASTMCP_AVAILABLE:
    mcp = FastMCP("Astro Generator")

    @mcp.tool()
    async def generate_daily_horoscopes_tool(date: Optional[str] = None) -> dict:
        """Génère tous les horoscopes du jour."""
        try:
            parse_date = astro_generator._validate_date(date)
            horoscopes = await astro_generator.generate_daily_horoscopes(parse_date)
            
            # Conversion pour sérialisation JSON
            result = {}
            for key, h in horoscopes.items():
                if isinstance(h, HoroscopeResult):
                    result[key] = asdict(h)
                else:
                    result[key] = h
            
            return {
                "success": True, 
                "date": parse_date.strftime("%Y-%m-%d"),
                "horoscopes": result,
                "total_generated": len([h for h in result.values() if "error" not in h])
            }
            
        except Exception as e:
            logger.error(f"Erreur tool generate_daily_horoscopes: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def generate_single_horoscope_with_audio_tool(sign: str, date: Optional[str] = None) -> dict:
        """Génère un horoscope et son fichier audio TTS."""
        try:
            validated_sign = astro_generator._validate_sign(sign)
            parse_date = astro_generator._validate_date(date)
            
            horoscope_result, audio_path, audio_duration = await astro_generator.generate_single_horoscope(
                validated_sign, parse_date, generate_audio=True
            )
            
            return {
                "success": True, 
                "horoscope": asdict(horoscope_result),
                "audio_path": audio_path,
                "audio_duration_seconds": audio_duration
            }
            
        except Exception as e:
            logger.error(f"Erreur tool generate_single_horoscope_with_audio: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_astral_context_tool(date: str) -> dict:
        """Obtient le contexte astrologique complet pour une date donnée."""
        try:
            parse_date = astro_generator._validate_date(date)
            context = astro_generator.get_astral_context(parse_date)
            
            return {
                "success": True,
                "context": asdict(context)
            }
            
        except Exception as e:
            logger.error(f"Erreur tool get_astral_context: {e}")
            return {"success": False, "error": str(e)}

@mcp.tool()
def generate_chart_image_tool(date: Optional[str] = None) -> dict:
    """
    Génère une image de carte astrologique pour une date donnée.
    Intégration directe - plus de proxy vers astro_chart_mcp
    """
    try:
        if not ASTROCHART_AVAILABLE:
            return {
                "success": False, 
                "error": "Le module AstroChart n'est pas disponible."
            }
        
        if not astro_generator.chart_generator:
            return {
                "success": False,
                "error": "Générateur d'images non disponible (Matplotlib requis)"
            }
        
        # Validation de la date
        target_date = astro_generator._validate_date(date)
        
        # Réutilisation des calculs existants d'AstroCalculator
        positions = astro_calculator.calculate_positions(target_date)
        
        if not positions:
            return {
                "success": False,
                "error": "Impossible de calculer les positions planétaires"
            }
        
        # Génération de l'image directement
        chart_path = astro_generator.chart_generator.create_chart_from_positions(
            positions, target_date
        )
        
        if chart_path:
            return {
                "success": True,
                "chart_image_path": chart_path,
                "date": target_date.strftime('%Y-%m-%d'),
                "positions_count": len(positions),
                "message": f"Carte astrologique générée pour le {target_date.strftime('%d/%m/%Y')}"
            }
        else:
            return {
                "success": False,
                "error": "Échec de la génération de l'image"
            }
            
    except Exception as e:
        logger.error(f"Erreur generate_chart_image_tool: {e}")
        return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_sign_metadata_tool(sign: str) -> dict:
        """Obtient toutes les métadonnées d'un signe astrologique."""
        try:
            validated_sign = astro_generator._validate_sign(sign)
            metadata = astro_generator.get_sign_metadata(validated_sign)
            
            if metadata:
                return {
                    "success": True,
                    "metadata": asdict(metadata)
                }
            else:
                return {
                    "success": False,
                    "error": f"Signe inconnu: {sign}",
                    "available_signs": list(astro_generator.signs_data.keys())
                }
                
        except Exception as e:
            logger.error(f"Erreur tool get_sign_metadata: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def calculate_lunar_influence_tool(sign: str, date: str) -> dict:
        """Calcule l'influence de la lune sur un signe pour une date donnée."""
        try:
            validated_sign = astro_generator._validate_sign(sign)
            parse_date = astro_generator._validate_date(date)
            
            influence = astro_generator.calculate_lunar_influence(validated_sign, parse_date)
            
            # Interprétation du score
            if influence < 0.3:
                interpretation = "Faible"
            elif influence < 0.6:
                interpretation = "Modérée"
            elif influence < 0.8:
                interpretation = "Forte"
            else:
                interpretation = "Très forte"
            
            return {
                "success": True,
                "sign": astro_generator.get_sign_metadata(validated_sign).name,
                "date": date,
                "lunar_influence_score": round(influence, 3),
                "interpretation": interpretation,
                "astral_context": asdict(astro_generator.get_astral_context(parse_date))
            }
            
        except Exception as e:
            logger.error(f"Erreur tool calculate_lunar_influence: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_system_status_tool() -> dict:
        """Retourne l'état complet du système."""
        try:
            status = astro_generator.get_system_status()
            return {"success": True, "status": status}
        except Exception as e:
            logger.error(f"Erreur tool get_system_status: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def export_daily_horoscopes_tool(date: Optional[str] = None) -> dict:
        """Génère et exporte tous les horoscopes du jour."""
        try:
            parse_date = astro_generator._validate_date(date)
            horoscopes = await astro_generator.generate_daily_horoscopes(parse_date)
            
            export_path = astro_generator.export_horoscopes_data(horoscopes)
            
            return {
                "success": True,
                "export_path": export_path,
                "date": parse_date.strftime("%Y-%m-%d"),
                "total_horoscopes": len(horoscopes)
            }
            
        except Exception as e:
            logger.error(f"Erreur tool export_daily_horoscopes: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🌟" + "="*60)
    print("🌟 ASTRO GENERATOR SERVER")
    print("🌟" + "="*60)
    
    # Affichage du statut
    status = astro_generator.get_system_status()
    print(f"📊 Configuration:")
    print(f"   • Modèle Ollama: {astro_generator.ollama_model}")
    print(f"   • Dossier audio: {astro_generator.audio_output_dir}")
    print(f"   • Max retries: {astro_generator.max_retries}")
    
    print(f"📦 Dépendances:")
    print(f"   • Ollama: {'✅' if status['ollama_available'] else '❌'}")
    print(f"   • FastMCP: {'✅' if status['fastmcp_available'] else '❌'}")
    print(f"   • TTS: {'✅' if status['tts_available'] else '❌'}")
    
    print(f"🎯 Capacités:")
    print(f"   • {len(astro_generator.signs_data)} signes astrologiques")
    print(f"   • {status['audio_files_count']} fichiers audio existants")
    print(f"   • Génération parallèle optimisée")
    print(f"   • Cache et retry automatique")
    print(f"   • Validation des entrées")
    
    # Démarrage du serveur FastMCP
    if FASTMCP_AVAILABLE:
        print(f"🚀 Démarrage du serveur MCP...")
        mcp.run()
    else:
        print("⚠️  FastMCP non disponible, serveur MCP non démarré")
        print("💡 Le générateur peut être utilisé en mode module")