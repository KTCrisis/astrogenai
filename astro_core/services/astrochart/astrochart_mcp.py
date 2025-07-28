#!/usr/bin/env python3
"""
MCP Astro Chart Server - Calculs Astronomiques Purs
Serveur MCP dédié aux positions planétaires et calculs astronomiques
"""

import datetime
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from skyfield.api import Loader
import json

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

DATA_DIR = Path(__file__).parent.resolve()
load = Loader(DATA_DIR, verbose=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlanetaryPosition:
    """Position d'une planète"""
    name: str
    symbol: str
    longitude: float
    sign_index: int
    sign_name: str
    degree_in_sign: float
    retrograde: bool = False

@dataclass
class AstralAspect:
    """Aspect entre deux planètes"""
    planet1: str
    planet2: str
    aspect_type: str  # conjunction, opposition, trine, square, sextile
    orb: float
    exact: bool

@dataclass
class AstroChartData:
    """Données complètes d'une carte astrologique"""
    date: str
    timestamp: str
    sun_sign: str
    moon_phase: str
    planets: List[PlanetaryPosition]
    aspects: List[AstralAspect]
    houses: Optional[Dict] = None  # Pour futur usage
    calculation_method: str = "skyfield_de440s"

class AstroCalculator:
    """Calculateur astronomique pur"""
    
    def __init__(self):
        self.planets_data = load('de440s.bsp')
        self.ts = load.timescale()
        self.earth = self.planets_data[399]
        
        # Codes planétaires
        self.planet_codes = {
            'sun': 10, 'moon': 301, 'mercury': 199, 'venus': 299,
            'mars': 4, 'jupiter': 5, 'saturn': 6, 
            'uranus': 7, 'neptune': 8, 'pluto': 9
        }
        
        # Métadonnées planétaires
        self.planet_info = {
            'sun': {'symbol': '☉', 'name': 'Soleil'},
            'moon': {'symbol': '☽', 'name': 'Lune'},
            'mercury': {'symbol': '☿', 'name': 'Mercure'},
            'venus': {'symbol': '♀', 'name': 'Vénus'},
            'mars': {'symbol': '♂', 'name': 'Mars'},
            'jupiter': {'symbol': '♃', 'name': 'Jupiter'},
            'saturn': {'symbol': '♄', 'name': 'Saturne'},
            'uranus': {'symbol': '♅', 'name': 'Uranus'},
            'neptune': {'symbol': '♆', 'name': 'Neptune'},
            'pluto': {'symbol': '♇', 'name': 'Pluton'}
        }
        
        self.zodiac_names = [
            'Bélier', 'Taureau', 'Gémeaux', 'Cancer', 'Lion', 'Vierge',
            'Balance', 'Scorpion', 'Sagittaire', 'Capricorne', 'Verseau', 'Poissons'
        ]
    
    def calculate_positions(self, date: datetime.date) -> List[PlanetaryPosition]:
        """Calcule les positions planétaires pour une date"""
        t = self.ts.utc(date.year, date.month, date.day, 12, 0, 0)
        positions = []
        
        for planet_key, planet_code in self.planet_codes.items():
            try:
                planet = self.planets_data[planet_code]
                astrometric = self.earth.at(t).observe(planet)
                lat, lon, distance = astrometric.ecliptic_latlon()
                
                sign_index = int(lon.degrees // 30)
                degree_in_sign = lon.degrees % 30
                
                position = PlanetaryPosition(
                    name=self.planet_info[planet_key]['name'],
                    symbol=self.planet_info[planet_key]['symbol'],
                    longitude=lon.degrees,
                    sign_index=sign_index,
                    sign_name=self.zodiac_names[sign_index],
                    degree_in_sign=degree_in_sign,
                    retrograde=False  # TODO: Calculer rétrogradation
                )
                
                positions.append(position)
                
            except Exception as e:
                logger.error(f"Erreur calcul {planet_key}: {e}")
                continue
        
        return positions
    
    def calculate_aspects(self, positions: List[PlanetaryPosition]) -> List[AstralAspect]:
        """Calcule les aspects entre planètes"""
        aspects = []
        
        # Aspects majeurs et leurs orbes
        aspect_definitions = {
            'conjunction': (0, 8),      # 0° ± 8°
            'opposition': (180, 8),     # 180° ± 8°
            'trine': (120, 6),          # 120° ± 6°
            'square': (90, 6),          # 90° ± 6°
            'sextile': (60, 4),         # 60° ± 4°
        }
        
        # Comparer chaque paire de planètes
        for i, planet1 in enumerate(positions):
            for planet2 in positions[i+1:]:
                angle_diff = abs(planet1.longitude - planet2.longitude)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                # Vérifier chaque aspect
                for aspect_name, (target_angle, orb) in aspect_definitions.items():
                    if abs(angle_diff - target_angle) <= orb:
                        actual_orb = abs(angle_diff - target_angle)
                        aspects.append(AstralAspect(
                            planet1=planet1.name,
                            planet2=planet2.name,
                            aspect_type=aspect_name,
                            orb=actual_orb,
                            exact=(actual_orb <= 2.0)
                        ))
                        break
        
        return aspects
    
    def get_moon_phase(self, date: datetime.date) -> str:
        """Calcule la phase lunaire"""
        # Logique simplifiée (à améliorer avec Skyfield)
        reference = datetime.date(2024, 1, 11)  # Nouvelle lune de référence
        days_since = (date - reference).days
        lunar_cycle = days_since % 29.5
        
        if lunar_cycle < 7.4:
            return "Nouvelle Lune"
        elif lunar_cycle < 14.8:
            return "Premier Quartier"
        elif lunar_cycle < 22.1:
            return "Pleine Lune"
        else:
            return "Dernier Quartier"
    
    def generate_chart_data(self, date: datetime.date) -> AstroChartData:
        """Génère toutes les données d'une carte astrologique"""
        positions = self.calculate_positions(date)
        aspects = self.calculate_aspects(positions)
        moon_phase = self.get_moon_phase(date)
        
        # Trouver le signe solaire
        sun_position = next((p for p in positions if p.name == 'Soleil'), None)
        sun_sign = sun_position.sign_name if sun_position else "Inconnu"
        
        return AstroChartData(
            date=date.strftime('%Y-%m-%d'),
            timestamp=datetime.datetime.now().isoformat(),
            sun_sign=sun_sign,
            moon_phase=moon_phase,
            planets=positions,
            aspects=aspects,
            calculation_method="skyfield_de440s"
        )
        
    def get_major_events_for_week(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict[str, str]]:
        """
        Identifie les événements astrologiques majeurs sur une période donnée.
        Retourne une liste d'événements (Ingrès, Phases lunaires, Aspects exacts).
        """
        events = []
        previous_positions = self.calculate_positions(start_date - datetime.timedelta(days=1))

        for day_offset in range((end_date - start_date).days + 1):
            current_date = start_date + datetime.timedelta(days=day_offset)
            current_positions = self.calculate_positions(current_date)

            # 1. Détecter les Ingrès (changement de signe)
            for i, planet in enumerate(current_positions):
                if planet.sign_name != previous_positions[i].sign_name:
                    events.append({
                        "date": current_date.strftime('%Y-%m-%d'),
                        "type": "Ingrès",
                        "description": f"{planet.name} entre en {planet.sign_name}"
                    })

            # 2. Détecter la Nouvelle et la Pleine Lune
            moon_phase = self.get_moon_phase(current_date)
            if "Nouvelle Lune" in moon_phase or "Pleine Lune" in moon_phase:
                # Éviter les doublons si la phase dure plusieurs jours
                if not any(e.get("description") == moon_phase for e in events):
                    events.append({
                        "date": current_date.strftime('%Y-%m-%d'),
                        "type": "Phase Lunaire",
                        "description": moon_phase
                    })

            # 3. Détecter les Aspects qui deviennent exacts
            aspects = self.calculate_aspects(current_positions)
            for aspect in aspects:
                if aspect.exact:
                    events.append({
                        "date": current_date.strftime('%Y-%m-%d'),
                        "type": "Aspect Exact",
                        "description": f"{aspect.planet1} {aspect.aspect_type} {aspect.planet2}"
                    })

            previous_positions = current_positions

        # Optionnel : Filtrer pour ne garder que les événements uniques par description
        unique_events = list({event['description']: event for event in events}.values())
        return unique_events
# Initialisation du calculateur
astro_calculator = AstroCalculator()

# Serveur FastMCP
if FASTMCP_AVAILABLE:
    mcp = FastMCP("AstroChart Calculator")

    @mcp.tool()
    def get_planetary_positions(date: str = None) -> dict:
        """
        Calcule les positions planétaires pour une date donnée.
        
        Args:
            date: Date au format YYYY-MM-DD (optionnel, défaut: aujourd'hui)
        
        Returns:
            Positions de toutes les planètes avec détails astrologiques
        """
        try:
            if date:
                target_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            else:
                target_date = datetime.date.today()
            
            positions = astro_calculator.calculate_positions(target_date)
            
            return {
                "success": True,
                "date": target_date.strftime('%Y-%m-%d'),
                "positions": [asdict(pos) for pos in positions],
                "total_planets": len(positions)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_planetary_aspects(date: str = None) -> dict:
        """
        Calcule les aspects planétaires pour une date donnée.
        
        Args:
            date: Date au format YYYY-MM-DD (optionnel, défaut: aujourd'hui)
        
        Returns:
            Aspects majeurs entre planètes avec orbes
        """
        try:
            if date:
                target_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            else:
                target_date = datetime.date.today()
            
            positions = astro_calculator.calculate_positions(target_date)
            aspects = astro_calculator.calculate_aspects(positions)
            
            return {
                "success": True,
                "date": target_date.strftime('%Y-%m-%d'),
                "aspects": [asdict(aspect) for aspect in aspects],
                "total_aspects": len(aspects)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_complete_chart_data(date: str = None) -> dict:
        """
        Génère toutes les données d'une carte astrologique complète.
        
        Args:
            date: Date au format YYYY-MM-DD (optionnel, défaut: aujourd'hui)
        
        Returns:
            Données complètes: positions, aspects, phase lunaire, etc.
        """
        try:
            if date:
                target_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            else:
                target_date = datetime.date.today()
            
            chart_data = astro_calculator.generate_chart_data(target_date)
            
            return {
                "success": True,
                "chart_data": asdict(chart_data)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_calculator_status() -> dict:
        """
        Retourne l'état du calculateur astronomique.
        
        Returns:
            Informations sur les capacités et la configuration
        """
        return {
            "success": True,
            "status": {
                "skyfield_loaded": True,
                "ephemeris_file": "de440s.bsp",
                "supported_planets": list(astro_calculator.planet_codes.keys()),
                "supported_aspects": ["conjunction", "opposition", "trine", "square", "sextile"],
                "calculation_precision": "astronomical",
                "zodiac_system": "tropical"
            }
        }

    @mcp.tool()
    def generate_astrological_chart_image(date: str = None) -> dict:
        """
        Génère une image de la carte astrologique pour une date donnée.
        
        Args:
            date: Date au format YYYY-MM-DD (optionnel, défaut: aujourd'hui)
        
        Returns:
            Chemin web vers l'image générée.
        """
        try:
            target_date = datetime.datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.date.today()
            output_dir = Path("static/charts")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"astro_chart_{target_date.strftime('%Y%m%d_%H%M%S')}.png"
            filesystem_path = output_dir / filename
            
            # Générer et sauvegarder le graphique
            saved_path = astro_chart_generator.create_chart(target_date, filesystem_path)
            
            if saved_path:
                # Retourner le chemin accessible depuis le web, pas le chemin du système de fichiers
                web_path = f"/static/charts/{filename}"
                return {"success": True, "image_url": web_path}
            else:
                return {"success": False, "error": "Échec de la génération de l'image de la carte."}
                
        except Exception as e:
            logger.error(f"Erreur tool generate_astrological_chart_image: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🌟 MCP Astro Chart Calculator")
    print("=" * 40)
    
    if FASTMCP_AVAILABLE:
        print("🚀 Démarrage serveur MCP...")
        mcp.run()
    else:
        print("❌ FastMCP non disponible")
        
        # Test en mode direct
        print("🧪 Test en mode direct...")
        today = datetime.date.today()
        chart_data = astro_calculator.generate_chart_data(today)
        
        print(f"\n📊 Carte pour {today}:")
        print(f"Signe solaire: {chart_data.sun_sign}")
        print(f"Phase lunaire: {chart_data.moon_phase}")
        print(f"Planètes calculées: {len(chart_data.planets)}")
        print(f"Aspects trouvés: {len(chart_data.aspects)}")