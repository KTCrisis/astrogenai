from skyfield.api import load, utc
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

class AstroChart:
    def __init__(self):
        # Charger les données planétaires
        self.planets = load('de440s.bsp')
        self.ts = load.timescale()
        self.earth = self.planets[399]  # Code numérique pour la Terre
        
        # CODES NUMÉRIQUES CORRECTS pour de421.bsp
        self.planet_codes = {
            'sun': 10,      # ✅ Soleil
            'moon': 301,    # ✅ Lune  
            'mercury': 199, # ✅ Mercure
            'venus': 299,   # ✅ Vénus
            'mars': 4,      # ✅ MARS BARYCENTER (pas 499 !)
            'jupiter': 5,   # ✅ JUPITER BARYCENTER (pas 599 !)
            'saturn': 6,    # ✅ SATURN BARYCENTER (pas 699 !)
            'uranus': 7,    # ✅ URANUS BARYCENTER (pas 799 !)
            'neptune': 8,   # ✅ NEPTUNE BARYCENTER (pas 899 !)
            'pluto': 9      # ✅ PLUTO BARYCENTER (pas 999 !)
        }
        # Symboles Unicode
        self.planet_symbols = {
            'sun': '☉', 'moon': '☽', 'mercury': '☿', 'venus': '♀', 
            'mars': '♂', 'jupiter': '♃', 'saturn': '♄',
            'uranus': '♅', 'neptune': '♆', 'pluto': '♇'
        }
        
        
        self.zodiac_symbols = ['♈', '♉', '♊', '♋', '♌', '♍', 
                              '♎', '♏', '♐', '♑', '♒', '♓']
        
        self.zodiac_names = ['Bélier', 'Taureau', 'Gémeaux', 'Cancer', 
                            'Lion', 'Vierge', 'Balance', 'Scorpion',
                            'Sagittaire', 'Capricorne', 'Verseau', 'Poissons']
    
    def get_planetary_positions(self, date):
        """Calcule les positions planétaires pour une date"""
        t = self.ts.utc(date.year, date.month, date.day, 12, 0, 0)
        
        positions = {}
        
        for planet_name, planet_code in self.planet_codes.items():
            try:
                planet = self.planets[planet_code]
                astrometric = self.earth.at(t).observe(planet)
                lat, lon, distance = astrometric.ecliptic_latlon()
                
                positions[planet_name] = {
                    'longitude': lon.degrees,
                    'sign_index': int(lon.degrees // 30),
                    'degree_in_sign': lon.degrees % 30,
                    'sign_name': self.zodiac_names[int(lon.degrees // 30)]
                }
            except KeyError as e:
                print(f"⚠️  {planet_name} non disponible dans de421.bsp: {e}")
                continue
        
        return positions
    
    def create_chart(self, date, output_path=None):
        """Crée la carte astrologique"""
        positions = self.get_planetary_positions(date)
        
        if not positions:
            print("❌ Aucune position planétaire calculée")
            return None, None
        
        # Configuration du graphique
        fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
        ax.set_facecolor('black')
        fig.patch.set_facecolor('black')
        
        # Cercles concentriques
        for radius in [0.7, 0.9, 1.0]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gold', alpha=0.3, transform=ax.transData._b)
        
        # Divisions zodiacales (12 signes)
        for i in range(12):
            angle = np.radians(i * 30)
            ax.plot([angle, angle], [0.6, 1.1], color='gold', alpha=0.5, linewidth=1)
            
            # Symboles zodiacaux au centre de chaque signe
            sign_angle = np.radians(i * 30 + 15)
            ax.text(sign_angle, 1.05, self.zodiac_symbols[i], 
                   ha='center', va='center', fontsize=20, color='gold', weight='bold')
        
        # Couleurs des planètes
        planet_colors = {
            'sun': '#FFD700', 'moon': '#C0C0C0', 'mercury': '#FFA500',
            'venus': '#FF69B4', 'mars': '#FF4500', 'jupiter': '#4169E1', 'saturn': '#8B4513'
        }
        
        # Placer les planètes
        for planet_name, data in positions.items():
            angle = np.radians(data['longitude'])
            color = planet_colors.get(planet_name, 'white')
            
            # Point planète
            ax.scatter(angle, 0.85, s=300, c=color, edgecolors='white', linewidth=2, zorder=10)
            
            # Symbole planétaire
            symbol = self.planet_symbols.get(planet_name, '?')
            ax.text(angle, 0.85, symbol, ha='center', va='center', 
                   fontsize=16, color='black', weight='bold', zorder=11)
            
            # Degré dans le signe
            ax.text(angle, 0.75, f"{data['degree_in_sign']:.0f}°", 
                   ha='center', va='center', fontsize=8, color='white')
        
        # Configuration des axes
        ax.set_theta_zero_location('N')  # 0° en haut (Bélier)
        ax.set_theta_direction(-1)       # Sens horaire
        ax.set_ylim(0, 1.2)
        ax.set_rticks([])               # Supprimer les graduations radiales
        ax.set_thetagrids([])           # Supprimer les graduations angulaires
        ax.grid(False)
        
        # Titre
        ax.set_title(f"Carte Astrologique - {date.strftime('%d/%m/%Y')}", 
                    fontsize=16, color='gold', pad=30, weight='bold')
        
        # Légende avec positions
        legend_text = []
        for planet_name, data in positions.items():
            symbol = self.planet_symbols.get(planet_name, '?')
            sign = data['sign_name']
            degree = data['degree_in_sign']
            legend_text.append(f"{symbol} {planet_name.title()}: {sign} {degree:.1f}°")
        
        # Afficher légende
        fig.text(0.02, 0.98, '\n'.join(legend_text), fontsize=10, color='white', 
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.8))
        
        # Sauvegarder si demandé
        if output_path:
            plt.savefig(output_path, facecolor='black', dpi=300, bbox_inches='tight')
            print(f"✅ Carte sauvegardée: {output_path}")
        
        return fig, positions

# Utilisation
if __name__ == "__main__":
    print("🌟 Création de la carte astrologique...")
    
    chart = AstroChart()
    
    # Test avec la date d'aujourd'hui
    today = datetime.now()
    fig, positions = chart.create_chart(today, f"astro_chart_{today.strftime('%Y%m%d')}.png")
    
    if positions:
        print("\n📊 Positions planétaires calculées:")
        for planet, data in positions.items():
            symbol = chart.planet_symbols.get(planet, '?')
            print(f"{symbol} {planet.title()}: {data['sign_name']} {data['degree_in_sign']:.1f}°")
        
        plt.show()
    else:
        print("❌ Échec du calcul des positions")