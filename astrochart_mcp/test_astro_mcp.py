#!/usr/bin/env python3
"""
Suite de tests complète pour Astro Chart MCP
"""

import sys
import os
import datetime
import json
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test des imports et dépendances"""
    print("📦 TEST IMPORTS")
    print("-" * 30)
    
    try:
        from skyfield.api import load
        print("✅ Skyfield: OK")
    except ImportError:
        print("❌ Skyfield: MANQUANT (pip install skyfield)")
        return False
    
    try:
        from fastmcp import FastMCP
        print("✅ FastMCP: OK")
    except ImportError:
        print("⚠️  FastMCP: MANQUANT (pip install fastmcp)")
    
    try:
        from astro_chart_mcp import astro_calculator, AstroCalculator
        print("✅ AstroChart MCP: OK")
        return True
    except ImportError as e:
        print(f"❌ AstroChart MCP: ERREUR - {e}")
        return False

def test_basic_functionality():
    """Test des fonctionnalités de base"""
    print("\n🔧 TEST FONCTIONNALITÉS")
    print("-" * 30)
    
    from astro_chart_mcp import astro_calculator
    
    # Test données de base
    today = datetime.date.today()
    print(f"📅 Date de test: {today}")
    
    # Test positions
    try:
        positions = astro_calculator.calculate_positions(today)
        print(f"✅ Positions calculées: {len(positions)} planètes")
        
        # Afficher quelques positions
        for pos in positions[:3]:
            print(f"   {pos.symbol} {pos.name}: {pos.sign_name} {pos.degree_in_sign:.1f}°")
        
    except Exception as e:
        print(f"❌ Erreur positions: {e}")
        return False
    
    # Test aspects
    try:
        aspects = astro_calculator.calculate_aspects(positions)
        print(f"✅ Aspects calculés: {len(aspects)}")
        
        # Afficher quelques aspects
        for aspect in aspects[:2]:
            print(f"   {aspect.planet1} {aspect.aspect_type} {aspect.planet2}")
        
    except Exception as e:
        print(f"❌ Erreur aspects: {e}")
        return False
    
    return True

def test_mcp_tools_simulation():
    """Simulation des outils MCP"""
    print("\n🛠️  TEST OUTILS MCP")
    print("-" * 30)
    
    from astro_chart_mcp import astro_calculator
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    # Simuler get_calculator_status
    print("🔍 get_calculator_status()")
    try:
        status = {
            "success": True,
            "status": {
                "skyfield_loaded": bool(astro_calculator.planets_data),
                "supported_planets": list(astro_calculator.planet_codes.keys()),
                "total_planets": len(astro_calculator.planet_codes)
            }
        }
        print(f"✅ Statut: {status['status']['total_planets']} planètes supportées")
    except Exception as e:
        print(f"❌ Erreur statut: {e}")
    
    # Simuler get_planetary_positions
    print(f"\n🪐 get_planetary_positions('{today}')")
    try:
        date_obj = datetime.datetime.strptime(today, '%Y-%m-%d').date()
        positions = astro_calculator.calculate_positions(date_obj)
        
        result = {
            "success": True,
            "date": today,
            "positions": [
                {
                    "name": pos.name,
                    "symbol": pos.symbol,
                    "sign_name": pos.sign_name,
                    "degree_in_sign": round(pos.degree_in_sign, 1)
                } for pos in positions
            ],
            "total_planets": len(positions)
        }
        
        print(f"✅ Positions: {result['total_planets']} planètes")
        print("📍 Exemple:")
        for pos in result['positions'][:3]:
            print(f"   {pos['symbol']} {pos['name']}: {pos['sign_name']} {pos['degree_in_sign']}°")
            
    except Exception as e:
        print(f"❌ Erreur positions: {e}")

def run_all_tests():
    """Lance tous les tests"""
    print("🧪 SUITE DE TESTS ASTRO CHART MCP")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Tests arrêtés: problème d'imports")
        return
    
    # Test 2: Fonctionnalités
    if not test_basic_functionality():
        print("\n❌ Tests arrêtés: problème fonctionnalités")
        return
    
    # Test 3: Simulation MCP
    test_mcp_tools_simulation()
    
    print("\n🎉 TOUS LES TESTS TERMINÉS!")
    print("\n💡 Pour tester le serveur MCP réel:")
    print("   1. python astro_chart_mcp.py")
    print("   2. Dans un autre terminal: curl ou client MCP")

if __name__ == "__main__":
    run_all_tests()