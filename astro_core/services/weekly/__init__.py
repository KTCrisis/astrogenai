#!/usr/bin/env python3
"""
Module Weekly - Génération d'horoscopes hebdomadaires avec contexte évolutif
Fichier: astro_core/services/weekly/__init__.py
"""

from .weekly_generator import WeeklyGenerator

__all__ = ['WeeklyGenerator']
__version__ = '1.0.0'

# Information sur le module
MODULE_INFO = {
    "name": "WeeklyGenerator",
    "version": __version__,
    "description": "Générateur d'horoscopes hebdomadaires avec contexte évolutif",
    "features": [
        "Génération séquentielle avec contexte",
        "Gestion intelligente des répétitions", 
        "Corrections automatiques des noms de signes",
        "Fallback vers génération parallèle",
        "Métriques détaillées de génération"
    ],
    "dependencies": [
        "WeeklyGenerationContext",
        "WeeklyPromptTemplates",
        "AstroGenerator (parent)"
    ]
}