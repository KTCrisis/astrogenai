#!/usr/bin/env python3
"""
WeeklyGenerator - Module séparé pour la génération d'horoscopes hebdomadaires
Fichier: astro_core/services/weekly/weekly_generator.py
"""

import asyncio
import logging
from typing import Tuple, List, Dict
from datetime import date
from pathlib import Path

# Imports des modules contextuels
try:
    from ..context.weekly_context import WeeklyGenerationContext, ToneType, ThemeCategory
    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False

try:
    from ..prompts.weekly_templates import WeeklyPromptTemplates
    TEMPLATES_AVAILABLE = True
except ImportError:
    TEMPLATES_AVAILABLE = False

logger = logging.getLogger(__name__)

class WeeklyGenerator:
    """
    Générateur d'horoscopes hebdomadaires avec contexte évolutif
    Module séparé pour alléger AstroGenerator principal
    """
    
    def __init__(self, astro_generator):
        """
        Initialise le générateur hebdomadaire
        
        Args:
            astro_generator: Instance de AstroGenerator parent pour accéder aux méthodes communes
        """
        self.parent = astro_generator
        
        # Accès aux propriétés du parent
        self.ollama_model = astro_generator.ollama_model
        self.signs_data = astro_generator.signs_data
        self.astro_calculator = astro_generator.astro_calculator
        self.max_retries = astro_generator.max_retries
        
        # Vérification des dépendances
        if not CONTEXT_AVAILABLE:
            logger.error("WeeklyGenerationContext non disponible")
            raise ImportError("Module context requis pour WeeklyGenerator")
        
        if not TEMPLATES_AVAILABLE:
            logger.error("WeeklyPromptTemplates non disponible")
            raise ImportError("Module templates requis pour WeeklyGenerator")
        
        logger.info("✅ WeeklyGenerator initialisé avec contexte évolutif")
    
    # =============================================================================
    # MÉTHODE PRINCIPALE - Point d'entrée
    # =============================================================================
    
    async def generate_weekly_summary_with_context(
        self, 
        start_date: date, 
        end_date: date
    ) -> Tuple[str, str, float]:
        """
        Génère un résumé hebdomadaire complet avec contexte évolutif
        
        Returns:
            Tuple[script_text, audio_path, audio_duration]
        """
        logger.info("🚀 WeeklyGenerator: Démarrage génération contextuelle")
        
        # === INITIALISATION DU CONTEXTE ===
        context = WeeklyGenerationContext()
        context.weekly_events = self.astro_calculator.get_major_events_for_week(start_date, end_date)
        context.astral_context = self.parent._format_astral_context_for_weekly(start_date, end_date)
        context.period_description = f"{start_date.strftime('%d/%m')} au {end_date.strftime('%d/%m')}"
        context.target_words = 2400
        
        sections = []
        
        try:
            # === 1. INTRODUCTION ===
            logger.info("📝 Section 1/4: Introduction contextuelle...")
            intro_section = await self._generate_intro_with_context(start_date, end_date, context)
            context.update_from_section(intro_section, "intro", "Introduction")
            sections.append(intro_section)
            
            logger.info(f"✅ Contexte établi - Tonalité: {context.tone_style}, Thèmes: {len(context.themes_introduced)}")
            
            # === 2. ÉVÉNEMENTS ===
            logger.info("📝 Section 2/4: Analyse événements contextuels...")
            events_section = await self._generate_events_with_context(context)
            context.update_from_section(events_section, "events", "Événements cosmiques")
            sections.append(events_section)
            
            # === 3. SIGNES SÉQUENTIELS ===
            logger.info("📝 Section 3/4: Conseils signes séquentiels...")
            signs_section = await self._generate_signs_with_context(context)
            context.update_from_section(signs_section, "signs", "Conseils par signe")
            sections.append(signs_section)
            
            # === 4. CONCLUSION ===
            logger.info("📝 Section 4/4: Conclusion synthétique...")
            conclusion_section = await self._generate_conclusion_with_context(start_date, end_date, context)
            context.update_from_section(conclusion_section, "conclusion", "Conclusion")
            sections.append(conclusion_section)
            
            # === ASSEMBLAGE ET NETTOYAGE ===
            script_text = "\n\n".join(sections)
            script_text = self._clean_script_with_context_awareness(script_text, context)
            
            # === GÉNÉRATION AUDIO ===
            filename = f"hub_weekly_contextual_{start_date.strftime('%Y%m%d')}"
            audio_path, audio_duration = self.parent.generate_tts_audio(script_text, filename)
            
            # === MÉTRIQUES FINALES ===
            final_stats = context.export_context_summary()
            logger.info(f"✅ WeeklyGenerator terminé:")
            logger.info(f"   📊 {final_stats['total_words']} mots ({final_stats['completion_percentage']:.1f}%)")
            logger.info(f"   🎭 Tonalité: {final_stats['tone_style']}")
            logger.info(f"   🎯 Thèmes: {final_stats['themes_count']}/8")
            logger.info(f"   ⏱️ Durée audio: {audio_duration:.2f}s")
            
            return script_text, audio_path, audio_duration
            
        except Exception as e:
            logger.error(f"❌ Erreur WeeklyGenerator contextuel: {e}")
            # Fallback vers méthode parallèle du parent
            logger.info("🔄 Fallback vers génération parallèle standard...")
            return await self._fallback_to_parallel_generation(start_date, end_date)
    
    # =============================================================================
    # MÉTHODES DE GÉNÉRATION CONTEXTUELLES
    # =============================================================================
    
    async def _generate_intro_with_context(
        self, 
        start_date: date, 
        end_date: date, 
        context: WeeklyGenerationContext
    ) -> str:
        """Génère l'introduction en établissant le contexte"""
        events_str = "\n".join([f"- Le {e['date']}: {e['description']} ({e['type']})" 
                               for e in context.weekly_events])
        
        template = WeeklyPromptTemplates.get_intro_section_template()
        
        prompt = template.format(
            period=context.period_description,
            events=events_str,
            astral_context=context.astral_context,
            context_summary=context.get_context_summary(),
            avoid_repetition="",  # Vide pour l'intro
            previous_tone="",     
            word_target=context.get_remaining_word_budget(4)
        )
        
        intro_text = await self.parent._call_ollama_for_long_content(prompt)
        logger.info(f"📝 Introduction générée: {len(intro_text.split())} mots")
        return intro_text
    
    async def _generate_events_with_context(self, context: WeeklyGenerationContext) -> str:
        """Génère l'analyse des événements avec contexte"""
        events_str = "\n".join([f"- Le {e['date']}: {e['description']} ({e['type']})" 
                               for e in context.weekly_events])
        
        template = WeeklyPromptTemplates.get_events_analysis_template()
        
        prompt = template.format(
            events=events_str,
            context_summary=context.get_context_summary(),
            word_target=context.get_remaining_word_budget(3),
            avoid_repetition=", ".join(list(context.key_phrases_used)[:5]),
            previous_tone=context.tone_style.value if context.tone_style else "cohérente"
        )
        
        events_text = await self.parent._call_ollama_for_long_content(prompt)
        logger.info(f"📝 Événements générés: {len(events_text.split())} mots")
        return events_text
    
    async def _generate_signs_with_context(self, context: WeeklyGenerationContext) -> str:
        """Génère les conseils par signe en séquentiel avec contexte"""
        events_str = "\n".join([f"- Le {e['date']}: {e['description']}" 
                               for e in context.weekly_events])
        
        logger.info("🔮 WeeklyGenerator: Génération séquentielle des signes...")
        
        signs_content = []
        success_count = 0
        
        # GÉNÉRATION SÉQUENTIELLE signe par signe
        for i, sign_key in enumerate(self.signs_data.keys(), 1):
            logger.info(f"📝 Signe {i}/12: {sign_key.title()}...")
            
            try:
                sign_content = await self._generate_single_weekly_sign_with_context(
                    sign_key, events_str, context, position=i
                )
                signs_content.append(sign_content)
                success_count += 1
                
                # Mise à jour du contexte tous les 4 signes
                if i % 4 == 0:
                    partial_signs_text = "\n\n".join(signs_content[-4:])
                    context.update_from_section(partial_signs_text, "partial_signs", f"Signes {i-3}-{i}")
                    logger.debug(f"🔄 Contexte mis à jour après {i} signes")
                
            except Exception as e:
                logger.error(f"❌ Erreur {sign_key}: {e}")
                # Fallback
                fallback = self._generate_weekly_fallback(sign_key, events_str)
                signs_content.append(fallback)
        
        logger.info(f"✅ Signes générés séquentiellement: {success_count}/{len(self.signs_data)}")
        
        # Assemblage avec transition contextuelle
        signs_text = "\n\n".join(signs_content)
        contextual_transition = self._generate_contextual_transition_to_conclusion(context)
        signs_text += f"\n\n{contextual_transition}"
        
        return signs_text
    
    async def _generate_single_weekly_sign_with_context(
        self, 
        sign_key: str, 
        events_str: str, 
        context: WeeklyGenerationContext,
        position: int = 1
    ) -> str:
        """Génère le conseil pour un seul signe avec contexte"""
        try:
            validated_sign = self.parent._validate_sign(sign_key)
            sign_data = self.parent.get_sign_metadata(validated_sign)
            
            template = WeeklyPromptTemplates.get_signs_section_template()
            
            # Corrections des noms de signes AVANT la génération
            corrected_events_str = self._fix_sign_names_in_events(events_str)
            
            prompt = template.format(
                sign_name=sign_data.name,
                sign_dates=sign_data.dates,
                period=context.period_description,
                events=corrected_events_str,
                element=sign_data.element,
                ruling_planet=sign_data.ruling_planet,
                traits=', '.join(sign_data.traits),
                context_summary=context.get_context_summary(),
                avoid_repetition=", ".join([t.value for t in context.themes_introduced][:3]),
                previous_tone=context.tone_style.value if context.tone_style else "établie",
                word_target=context.get_remaining_word_budget(2)//12
            )
            
            content = await self.parent._call_ollama_for_long_content(prompt)
            
            # Validation du format
            if f"{sign_data.name} :" not in content:
                logger.warning(f"⚠️ Format incorrect pour {sign_data.name}, correction...")
                content = f"{sign_data.name} : {content}"
            
            # Correction supplémentaire des noms de signes dans le contenu généré
            content = self._fix_sign_names_in_content(content)
            
            logger.debug(f"✅ {sign_data.name}: {len(content.split())} mots")
            return content
            
        except Exception as e:
            logger.error(f"❌ Erreur génération contextuelle {sign_key}: {e}")
            return self._generate_weekly_fallback(sign_key, events_str)
    
    async def _generate_conclusion_with_context(
        self, 
        start_date: date, 
        end_date: date, 
        context: WeeklyGenerationContext
    ) -> str:
        """Génère la conclusion avec synthèse contextuelle"""
        template = WeeklyPromptTemplates.get_conclusion_section_template()
        
        prompt = template.format(
            period=context.period_description,
            context_summary=context.get_context_summary(),
            avoid_repetition=", ".join([t.value for t in context.themes_introduced]),
            previous_tone=context.tone_style.value if context.tone_style else "établie",
            word_target=context.get_remaining_word_budget(1)
        )
        
        conclusion_text = await self.parent._call_ollama_for_long_content(prompt)
        logger.info(f"📝 Conclusion générée: {len(conclusion_text.split())} mots")
        return conclusion_text
    
    # =============================================================================
    # MÉTHODES UTILITAIRES
    # =============================================================================
    
    def _generate_weekly_fallback(self, sign_key: str, events_str: str) -> str:
        """Fallback pour un signe en cas d'échec"""
        sign_data = self.parent.get_sign_metadata(sign_key)
        
        fallback = f"""{sign_data.name} : Cette semaine apporte des énergies cosmiques particulières pour votre signe {sign_data.element.lower()}. 
        Les influences planétaires actuelles résonnent avec votre nature {', '.join(sign_data.traits[:2])}, 
        vous invitant à rester attentif aux opportunités qui se présentent. 
        Conseil pratique : privilégiez {sign_data.keywords[0]} cette semaine tout en évitant les décisions impulsives. 
        Votre planète maîtresse {sign_data.ruling_planet} vous guide vers de nouveaux horizons."""
        
        return fallback
    
    def _generate_contextual_transition_to_conclusion(self, context: WeeklyGenerationContext) -> str:
        """Génère une transition contextuelle vers la conclusion"""
        if context.tone_style == ToneType.POETIQUE:
            return "Ces guidance personnalisées trouvent leur accomplissement dans la mélodie cosmique qui nous unit tous..."
        elif context.tone_style == ToneType.ENERGETIQUE:
            return "Pour canaliser pleinement cette énergie puissante et la transformer en actions concrètes..."
        elif context.tone_style == ToneType.SPIRITUEL:
            return "Ces révélations trouvent leur essence dans la sagesse universelle qui nous guide tous..."
        else:
            return "Pour intégrer harmonieusement ces énergies dans votre quotidien et en tirer le meilleur parti..."
    
    def _fix_sign_names_in_events(self, events_str: str) -> str:
        """Corrige les noms de signes dans la liste d'événements"""
        corrections = {
            'Scorpionn': 'Scorpion',
            'Scorpionnnn': 'Scorpion',
            'Capricornee': 'Capricorne',
            'Capricorneee': 'Capricorne',
            'Capricorneeee': 'Capricorne',
        }
        
        for wrong, correct in corrections.items():
            events_str = events_str.replace(wrong, correct)
        
        return events_str
    
    def _fix_sign_names_in_content(self, content: str) -> str:
        """Corrige les noms de signes dans le contenu généré"""
        corrections = {
            'Scorpionn': 'Scorpion',
            'Scorpionnnn': 'Scorpion', 
            'Capricornee': 'Capricorne',
            'Capricorneee': 'Capricorne',
            'Capricorneeee': 'Capricorne',
        }
        
        for wrong, correct in corrections.items():
            content = content.replace(wrong, correct)
            content = content.replace(wrong.lower(), correct.lower())
            content = content.replace(wrong.capitalize(), correct)
        
        return content
    
    def _clean_script_with_context_awareness(
        self, 
        script_text: str, 
        context: WeeklyGenerationContext
    ) -> str:
        """Nettoyage intelligent avec conscience du contexte"""
        logger.info("🧹 WeeklyGenerator: Nettoyage contextuel...")
        
        # 1. Nettoyage de base du parent
        script_text = self.parent._clean_script_text(script_text)
        
        # 2. Corrections supplémentaires spécifiques au weekly
        script_text = self._fix_sign_names_in_content(script_text)
        
        # 3. Suppression des répétitions contextuelles
        script_text = self._remove_contextual_repetitions(script_text, context)
        
        return script_text
    
    def _remove_contextual_repetitions(self, text: str, context: WeeklyGenerationContext) -> str:
        """Supprime les répétitions basées sur le contexte"""
        # Logique de suppression des répétitions contextuelles
        # À implémenter selon vos besoins spécifiques
        return text
    
    async def _fallback_to_parallel_generation(self, start_date: date, end_date: date) -> Tuple[str, str, float]:
        """Fallback vers la génération parallèle du parent en cas d'erreur"""
        logger.info("🔄 WeeklyGenerator: Utilisation du fallback parallèle...")
        return await self.parent.generate_weekly_summary_by_sections_parallel(start_date, end_date)
    
    # =============================================================================
    # MÉTHODES POUR COMPATIBILITÉ AVEC L'EXISTANT
    # =============================================================================
    
    async def generate_weekly_summary(self, start_date: date, end_date: date) -> Tuple[str, str, float]:
        """
        Point d'entrée principal - compatible avec l'interface existante
        """
        return await self.generate_weekly_summary_with_context(start_date, end_date)
    
    def get_system_status(self) -> Dict:
        """Retourne l'état du système WeeklyGenerator"""
        return {
            "weekly_generator": True,
            "context_available": CONTEXT_AVAILABLE,
            "templates_available": TEMPLATES_AVAILABLE,
            "signs_count": len(self.signs_data),
            "target_words": 2400,
            "generation_mode": "contextual_sequential"
        }