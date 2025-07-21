#!/usr/bin/env python3
"""
MCP Workflow Orchestrator Server - AstroGenAI
Serveur MCP pour orchestration intelligente des workflows d'horoscopes
Agent coordinateur utilisant Ollama pour la planification et l'optimisation
"""

import os
import re
import sys
import datetime
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import time
import logging

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️ FastMCP non disponible")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️ Ollama non disponible")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION ET DATACLASSES
# =============================================================================

@dataclass
class WorkflowStep:
    """Étape d'un workflow"""
    service: str
    action: str
    params: Dict[str, Any]
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    estimated_duration: float = 0.0
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class WorkflowPlan:
    """Plan d'exécution d'un workflow"""
    workflow_id: str
    steps: List[WorkflowStep]
    execution_strategy: str  # "sequential", "parallel", "hybrid"
    estimated_total_duration: float
    resource_requirements: Dict[str, Any]
    fallback_strategy: str
    optimization_goals: List[str]
    created_at: str

@dataclass
class ExecutionResult:
    """Résultat d'exécution d'un workflow"""
    workflow_id: str
    success: bool
    completed_steps: List[str]
    failed_steps: List[str]
    execution_time: float
    results: Dict[str, Any]
    optimizations_applied: List[str]
    performance_metrics: Dict[str, float]
    agent_insights: Dict[str, str]

@dataclass
class ServiceStatus:
    """État d'un service MCP"""
    name: str
    available: bool
    load: float  # 0.0 à 1.0
    last_response_time: float
    error_rate: float
    capabilities: List[str]

# =============================================================================
# ORCHESTRATEUR INTELLIGENT
# =============================================================================

class WorkflowOrchestrator:
    """Orchestrateur de workflows intelligent utilisant Ollama"""
    
    def __init__(self, ollama_model: str = "llama3.1:8b-instruct-q8_0"):
        self.ollama_model = ollama_model
        self.active_workflows = {}
        self.service_registry = {}
        self.performance_history = []
        
        # Configuration de l'agent
        self.agent_contexts = {
            "planning": {
                "temperature": 0.2,
                "system_prompt": self._get_planning_prompt(),
                "max_tokens": 800
            },
            "optimization": {
                "temperature": 0.3,
                "system_prompt": self._get_optimization_prompt(),
                "max_tokens": 600
            },
            "recovery": {
                "temperature": 0.4,
                "system_prompt": self._get_recovery_prompt(),
                "max_tokens": 500
            },
            "analysis": {
                "temperature": 0.1,
                "system_prompt": self._get_analysis_prompt(),
                "max_tokens": 700
            }
        }
    
    def _get_planning_prompt(self) -> str:
        return """Tu es un orchestrateur de workflows d'horoscopes IA expert.

MISSION: Créer des plans d'exécution optimaux pour les demandes utilisateur.

SERVICES DISPONIBLES:
- astro_server: Génération horoscopes + audio (TTS)
- astrochart_server : Generation des positions planétaires et calculs astronomiques
- video_server: Montage vidéo avec synchronisation
- comfyui_server: Génération vidéos constellations
- youtube_server: Upload automatique sur YouTube

STRATÉGIES D'EXÉCUTION:
- sequential: Une étape après l'autre (sûr, lent)
- parallel: Plusieurs étapes simultanées (rapide, consomme plus)
- hybrid: Mix intelligent selon les dépendances

OPTIMISATIONS POSSIBLES:
- Réutilisation de contenu existant
- Parallélisation intelligente
- Prédiction de charge
- Gestion proactive d'erreurs

Réponds TOUJOURS en JSON valide avec un plan détaillé."""

    def _get_optimization_prompt(self) -> str:
        return """Tu es un optimiseur de performance pour workflows d'horoscopes IA.

MISSION: Analyser et optimiser les workflows en cours d'exécution.

MÉTRIQUES IMPORTANTES:
- Temps d'exécution total
- Utilisation des ressources
- Taux d'erreur
- Qualité du contenu généré
- Engagement utilisateur

OPTIMISATIONS DISPONIBLES:
- Cache intelligent des horoscopes
- Pré-génération de contenu populaire
- Load balancing des services
- Compression/qualité des vidéos
- Timing optimal pour upload

Suggère des améliorations concrètes en JSON."""

    def _get_recovery_prompt(self) -> str:
        return """Tu es un expert en récupération d'erreurs pour workflows IA.

MISSION: Analyser les échecs et proposer des solutions de récupération.

STRATÉGIES DE RÉCUPÉRATION:
- Retry avec paramètres modifiés
- Contournement par service alternatif
- Dégradation gracieuse de qualité
- Workflow partiel avec notification
- Reprogrammation différée

ANALYSE REQUISE:
- Type d'erreur et cause probable
- Impact sur le workflow global
- Services affectés vs disponibles
- Faisabilité des alternatives

Propose un plan de récupération en JSON."""

    def _get_analysis_prompt(self) -> str:
        return """Tu es un analyste de performance pour workflows d'horoscopes IA.

MISSION: Analyser les résultats et extraire des insights.

ANALYSES À EFFECTUER:
- Performance comparative des services
- Tendances d'utilisation
- Goulots d'étranglement identifiés
- Prédictions de charge future
- Recommandations d'amélioration

MÉTRIQUES CLÉS:
- Temps de réponse par service
- Taux de succès des workflows
- Satisfaction utilisateur estimée
- Efficacité des ressources

Fournis des insights actionnables en JSON."""

    async def _call_ollama_with_context(self, context_type: str, prompt: str) -> Dict[str, Any]:
        """Appelle Ollama avec un contexte spécifique"""
        if not OLLAMA_AVAILABLE:
            raise Exception("Ollama non disponible")
        
        context = self.agent_contexts.get(context_type, self.agent_contexts["planning"])
        
        full_prompt = f"{context['system_prompt']}\n\n{prompt}\n\nRéponds UNIQUEMENT avec un JSON valide, sans texte additionnel."
        
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{'role': 'user', 'content': full_prompt}],
                options={
                    'temperature': context['temperature'],
                    'top_p': 0.9,
                    'num_predict': context['max_tokens']
                }
            )
            
            content = response['message']['content'].strip()
            
            # Debug: Afficher la réponse brute
            print(f"🔍 Réponse Ollama brute ({context_type}):")
            print(content[:500] + "..." if len(content) > 500 else content)
            print("=" * 50)
            
            # Méthode 1: JSON direct
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
            
            # Méthode 2: Extraire le JSON entre { }
            import re
            json_patterns = [
                r'\{.*?\}',  # JSON simple
                r'\{[\s\S]*\}',  # JSON avec newlines
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, content, re.DOTALL)
                if json_match:
                    try:
                        json_text = json_match.group()
                        # Nettoyer le JSON
                        json_text = self._clean_json_text(json_text)
                        return json.loads(json_text)
                    except json.JSONDecodeError:
                        continue
            
            # Méthode 3: Fallback avec structure par défaut
            print("⚠️  JSON parsing échoué, utilisation de fallback intelligent")
            return self._create_fallback_response(context_type, content, prompt)
                    
        except Exception as e:
            raise Exception(f"Erreur Ollama: {e}")

    def _clean_json_text(self, json_text: str) -> str:
        """Nettoie le texte JSON pour le parsing"""
        # Supprimer les commentaires
        json_text = re.sub(r'//.*?\n', '\n', json_text)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        # Corriger les quotes simples en doubles
        json_text = re.sub(r"'([^']*)':", r'"\1":', json_text)
        json_text = re.sub(r': *\'([^\']*)\'', r': "\1"', json_text)
        
        # Supprimer les virgules en fin de ligne
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Supprimer les caractères de contrôle
        json_text = ''.join(char for char in json_text if ord(char) >= 32 or char in '\n\r\t')
        
        return json_text.strip()

    def _create_fallback_response(self, context_type: str, raw_content: str, original_prompt: str) -> Dict[str, Any]:
        """Crée une réponse de fallback intelligente"""
        
        if context_type == "planning":
            # Parser intelligent pour extraction d'informations
            signs_mentioned = []
            for sign in ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
                        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]:
                if sign in original_prompt.lower():
                    signs_mentioned.append(sign)
            
            # Déterminer la stratégie basée sur le contenu
            if "parallel" in raw_content.lower() or "simultané" in raw_content.lower():
                strategy = "parallel"
            elif "hybrid" in raw_content.lower() or "hybride" in raw_content.lower():
                strategy = "hybrid"
            else:
                strategy = "sequential"
            
            # Créer des étapes intelligentes
            steps = []
            base_services = ["astrochart_server", "astro_server", "video_server"]
            
            if "comfyui" in original_prompt.lower() or "video" in original_prompt.lower():
                base_services.append("comfyui_server")
            
            if "youtube" in original_prompt.lower() or "upload" in original_prompt.lower():
                base_services.append("youtube_server")
            
            for i, service in enumerate(base_services):
                steps.append({
                    "service": service,
                    "action": "generate" if "generate" in service else "process",
                    "params": {"signs": signs_mentioned} if signs_mentioned else {},
                    "priority": i + 1,
                    "estimated_duration": 30.0 * (i + 1),
                    "dependencies": [base_services[i-1]] if i > 0 else []
                })
            
            return {
                "execution_strategy": strategy,
                "steps": steps,
                "estimated_total_duration": len(steps) * 45.0,
                "resource_requirements": {
                    "cpu_intensive": True,
                    "io_intensive": True,
                    "memory_usage": "medium"
                },
                "fallback_strategy": "Retry avec paramètres simplifiés",
                "optimization_goals": ["quality", "speed"],
                "reasoning": f"Plan de fallback basé sur analyse du prompt. Stratégie: {strategy}",
                "fallback_used": True
            }
        
        elif context_type == "optimization":
            return {
                "performance_assessment": "good",
                "bottlenecks_identified": ["parsing_issues"],
                "optimization_recommendations": ["améliorer_prompts", "fallback_robuste"],
                "future_predictions": "Performance stable avec fallbacks",
                "learning_points": ["JSON parsing nécessite robustesse"],
                "fallback_used": True
            }
        
        elif context_type == "recovery":
            return {
                "recovery_possible": True,
                "recovery_strategy": "Utiliser workflow simplifié avec fallbacks",
                "modified_steps": [
                    {"service": "astro_server", "action": "generate_simple", "params": {}}
                ],
                "estimated_success_probability": 0.8,
                "reasoning": "Fallback vers approche simplifiée",
                "fallback_used": True
            }
        
        else:  # analysis
            return {
                "performance_trends": "Stable avec adaptation nécessaire",
                "bottlenecks_identified": ["JSON parsing", "prompt complexity"],
                "success_factors": ["fallback mechanisms", "robust error handling"],
                "optimization_opportunities": ["prompt engineering", "response parsing"],
                "strategic_recommendations": ["Implémenter fallbacks systématiques"],
                "predicted_improvements": "Amélioration de robustesse avec fallbacks",
                "fallback_used": True
            }

    # =============================================================================
    # MÉTHODES DE PLANIFICATION
    # =============================================================================

    async def create_intelligent_plan(self, user_request: Dict[str, Any]) -> WorkflowPlan:
        """Crée un plan de workflow intelligent"""
        
        # Analyser la demande avec l'agent
        planning_prompt = f"""
        DEMANDE UTILISATEUR:
        {json.dumps(user_request, indent=2)}
        
        SERVICES ACTUELLEMENT DISPONIBLES:
        {json.dumps(self._get_services_status(), indent=2)}
        
        HISTORIQUE DE PERFORMANCE:
        {json.dumps(self._get_performance_summary(), indent=2)}
        
        Crée un plan d'exécution optimal. Réponds en JSON avec cette structure:
        {{
            "execution_strategy": "sequential|parallel|hybrid",
            "steps": [
                {{
                    "service": "nom_service",
                    "action": "action_à_effectuer", 
                    "params": {{}},
                    "priority": 1-5,
                    "estimated_duration": 0.0,
                    "dependencies": []
                }}
            ],
            "estimated_total_duration": 0.0,
            "resource_requirements": {{
                "cpu_intensive": true/false,
                "io_intensive": true/false,
                "memory_usage": "low|medium|high"
            }},
            "fallback_strategy": "description",
            "optimization_goals": ["speed", "quality", "resource_efficiency"],
            "reasoning": "explication du plan choisi"
        }}
        """
        
        agent_response = await self._call_ollama_with_context("planning", planning_prompt)
        
        # Construire le plan
        workflow_id = f"workflow_{int(time.time())}"
        
        steps = []
        for step_data in agent_response.get("steps", []):
            step = WorkflowStep(
                service=step_data["service"],
                action=step_data["action"],
                params=step_data["params"],
                priority=step_data.get("priority", 1),
                estimated_duration=step_data.get("estimated_duration", 30.0),
                dependencies=step_data.get("dependencies", [])
            )
            steps.append(step)
        
        plan = WorkflowPlan(
            workflow_id=workflow_id,
            steps=steps,
            execution_strategy=agent_response.get("execution_strategy", "sequential"),
            estimated_total_duration=agent_response.get("estimated_total_duration", 120.0),
            resource_requirements=agent_response.get("resource_requirements", {}),
            fallback_strategy=agent_response.get("fallback_strategy", "Retry avec paramètres réduits"),
            optimization_goals=agent_response.get("optimization_goals", ["quality"]),
            created_at=datetime.datetime.now().isoformat()
        )
        
        self.active_workflows[workflow_id] = plan
        return plan

    async def execute_workflow_plan(self, plan: WorkflowPlan) -> ExecutionResult:
        """Exécute un plan de workflow avec monitoring intelligent"""
        
        start_time = time.time()
        completed_steps = []
        failed_steps = []
        results = {}
        optimizations_applied = []
        
        try:
            if plan.execution_strategy == "sequential":
                results = await self._execute_sequential(plan, completed_steps, failed_steps)
            elif plan.execution_strategy == "parallel":
                results = await self._execute_parallel(plan, completed_steps, failed_steps)
            else:  # hybrid
                results = await self._execute_hybrid(plan, completed_steps, failed_steps)
                
        except Exception as e:
            # Tentative de récupération intelligente
            recovery_result = await self._attempt_intelligent_recovery(plan, str(e), completed_steps)
            if recovery_result["success"]:
                optimizations_applied.append("intelligent_error_recovery")
                results.update(recovery_result["results"])
            else:
                failed_steps.append("workflow_execution")
        
        execution_time = time.time() - start_time
        
        # Analyse post-exécution
        performance_metrics = await self._analyze_performance(plan, execution_time, completed_steps, failed_steps)
        agent_insights = await self._generate_insights(plan, results, performance_metrics)
        
        result = ExecutionResult(
            workflow_id=plan.workflow_id,
            success=len(failed_steps) == 0,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            execution_time=execution_time,
            results=results,
            optimizations_applied=optimizations_applied,
            performance_metrics=performance_metrics,
            agent_insights=agent_insights
        )
        
        # Sauvegarder pour apprentissage
        self.performance_history.append(asdict(result))
        
        return result

    # =============================================================================
    # MÉTHODES D'EXÉCUTION
    # =============================================================================

    async def _execute_sequential(self, plan: WorkflowPlan, completed: List, failed: List) -> Dict:
        """Exécution séquentielle avec optimisations"""
        results = {}
        
        for step in plan.steps:
            try:
                step_result = await self._execute_step(step)
                results[step.service] = step_result
                completed.append(f"{step.service}:{step.action}")
                
                # Optimization: early exit si suffisant
                if await self._should_early_exit(step_result, plan):
                    break
                    
            except Exception as e:
                failed.append(f"{step.service}:{step.action}")
                if not await self._can_continue_after_failure(step, plan):
                    break
        
        return results

    async def _execute_parallel(self, plan: WorkflowPlan, completed: List, failed: List) -> Dict:
        """Exécution parallèle avec gestion des dépendances"""
        results = {}
        
        # Grouper par niveau de dépendances
        execution_groups = self._group_by_dependencies(plan.steps)
        
        for group in execution_groups:
            # Exécuter le groupe en parallèle
            tasks = [self._execute_step(step) for step in group]
            group_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(group_results):
                step = group[i]
                if isinstance(result, Exception):
                    failed.append(f"{step.service}:{step.action}")
                else:
                    results[step.service] = result
                    completed.append(f"{step.service}:{step.action}")
        
        return results

    async def _execute_hybrid(self, plan: WorkflowPlan, completed: List, failed: List) -> Dict:
        """Exécution hybride - le plus intelligent"""
        # L'agent décide dynamiquement de la stratégie pour chaque étape
        optimization_prompt = f"""
        WORKFLOW EN COURS:
        Plan: {plan.execution_strategy}
        Étapes restantes: {len([s for s in plan.steps if f"{s.service}:{s.action}" not in completed])}
        Échecs: {failed}
        
        Quelle est la meilleure stratégie pour les étapes suivantes?
        
        Réponds en JSON:
        {{
            "next_strategy": "sequential|parallel",
            "reasoning": "pourquoi cette stratégie",
            "optimizations": ["liste des optimisations à appliquer"]
        }}
        """
        
        strategy_response = await self._call_ollama_with_context("optimization", optimization_prompt)
        
        # Exécuter selon la stratégie dynamique
        if strategy_response.get("next_strategy") == "parallel":
            return await self._execute_parallel(plan, completed, failed)
        else:
            return await self._execute_sequential(plan, completed, failed)

    async def _execute_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """Exécute une étape individuelle"""
        # Ici, vous feriez des appels aux vrais services MCP
        # Pour l'exemple, simulation
        
        await asyncio.sleep(step.estimated_duration / 10)  # Simulation
        
        return {
            "service": step.service,
            "action": step.action,
            "success": True,
            "result": f"Résultat simulé pour {step.service}:{step.action}",
            "execution_time": step.estimated_duration / 10
        }

    # =============================================================================
    # MÉTHODES D'ANALYSE ET OPTIMISATION
    # =============================================================================

    async def _analyze_performance(self, plan: WorkflowPlan, execution_time: float, 
                                 completed: List, failed: List) -> Dict[str, float]:
        """Analyse les performances du workflow"""
        return {
            "total_execution_time": execution_time,
            "planned_vs_actual_ratio": execution_time / plan.estimated_total_duration,
            "success_rate": len(completed) / (len(completed) + len(failed)) if (completed or failed) else 1.0,
            "efficiency_score": len(completed) / execution_time if execution_time > 0 else 0.0,
            "resource_utilization": 0.75  # Simulation
        }

    async def _generate_insights(self, plan: WorkflowPlan, results: Dict, 
                               metrics: Dict[str, float]) -> Dict[str, str]:
        """Génère des insights intelligents"""
        
        analysis_prompt = f"""
        WORKFLOW TERMINÉ:
        Plan original: {plan.execution_strategy}
        Résultats: {len(results)} services exécutés
        Métriques: {json.dumps(metrics, indent=2)}
        
        Génère des insights actionnables. Réponds en JSON:
        {{
            "performance_assessment": "excellent|good|fair|poor",
            "bottlenecks_identified": ["liste des goulots"],
            "optimization_recommendations": ["recommandations concrètes"],
            "future_predictions": "prédictions pour workflows similaires",
            "learning_points": ["points d'apprentissage pour l'IA"]
        }}
        """
        
        return await self._call_ollama_with_context("analysis", analysis_prompt)

    # =============================================================================
    # MÉTHODES UTILITAIRES
    # =============================================================================

    def _get_services_status(self) -> Dict[str, Any]:
        """Obtient l'état des services (simulation)"""
        return {
            "astrochart_server": {"available": True, "load": 0.3},
            "astro_server": {"available": True, "load": 0.3},
            "video_server": {"available": True, "load": 0.7},
            "comfyui_server": {"available": True, "load": 0.5},
            "youtube_server": {"available": True, "load": 0.2}
        }

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Résumé des performances historiques"""
        if not self.performance_history:
            return {"average_execution_time": 120.0, "success_rate": 0.95}
        
        recent = self.performance_history[-10:]  # 10 derniers
        avg_time = sum(r["execution_time"] for r in recent) / len(recent)
        success_rate = sum(1 for r in recent if r["success"]) / len(recent)
        
        return {
            "average_execution_time": avg_time,
            "success_rate": success_rate,
            "total_workflows": len(self.performance_history)
        }

    def _group_by_dependencies(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Groupe les étapes par niveau de dépendances"""
        groups = []
        remaining = steps.copy()
        
        while remaining:
            current_group = []
            for step in remaining[:]:
                if not step.dependencies or all(dep in [s.service for group in groups for s in group] for dep in step.dependencies):
                    current_group.append(step)
                    remaining.remove(step)
            
            if current_group:
                groups.append(current_group)
            else:
                # Éviter les boucles infinies
                groups.append(remaining)
                break
        
        return groups

    async def _attempt_intelligent_recovery(self, plan: WorkflowPlan, error: str, 
                                          completed: List) -> Dict[str, Any]:
        """Tentative de récupération intelligente"""
        
        recovery_prompt = f"""
        ÉCHEC DE WORKFLOW:
        Erreur: {error}
        Étapes complétées: {completed}
        Plan original: {plan.execution_strategy}
        
        Propose une stratégie de récupération. Réponds en JSON:
        {{
            "recovery_possible": true/false,
            "recovery_strategy": "description",
            "modified_steps": [
                {{"service": "...", "action": "...", "params": {{}}}}
            ],
            "estimated_success_probability": 0.0-1.0,
            "reasoning": "explication"
        }}
        """
        
        recovery_plan = await self._call_ollama_with_context("recovery", recovery_prompt)
        
        if recovery_plan.get("recovery_possible", False):
            # Tenter l'exécution du plan de récupération
            try:
                recovery_results = {}
                for step_data in recovery_plan.get("modified_steps", []):
                    # Simulation d'exécution de récupération
                    recovery_results[step_data["service"]] = {
                        "success": True,
                        "recovered": True,
                        "result": f"Récupération réussie pour {step_data['service']}"
                    }
                
                return {"success": True, "results": recovery_results}
            except:
                return {"success": False, "results": {}}
        
        return {"success": False, "results": {}}

    async def _should_early_exit(self, step_result: Dict, plan: WorkflowPlan) -> bool:
        """Détermine si on peut arrêter le workflow plus tôt"""
        # Logic d'optimisation: si le résultat est suffisant
        return False  # Simulation

    async def _can_continue_after_failure(self, failed_step: WorkflowStep, plan: WorkflowPlan) -> bool:
        """Détermine si on peut continuer après un échec"""
        # Logic: continuer si l'étape n'est pas critique
        return failed_step.priority <= 3  # Les priorités 4-5 sont critiques

    # =============================================================================
    # MÉTHODES D'INTERFACE (pour tests et intégration)
    # =============================================================================

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Retourne l'état de l'orchestrateur (méthode de classe)"""
        try:
            return {
                "success": True,
                "status": {
                    "ollama_available": OLLAMA_AVAILABLE,
                    "fastmcp_available": FASTMCP_AVAILABLE,
                    "active_workflows": len(self.active_workflows),
                    "total_workflows_processed": len(self.performance_history),
                    "average_success_rate": self._get_performance_summary().get("success_rate", 0.0),
                    "agent_contexts": list(self.agent_contexts.keys()),
                    "capabilities": [
                        "intelligent_planning",
                        "adaptive_execution", 
                        "error_recovery",
                        "performance_optimization",
                        "multi_strategy_execution"
                    ]
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def analyze_workflow_performance_method(self, time_range_days: int = 7) -> Dict[str, Any]:
        """Analyse les performances (méthode de classe pour intégration)"""
        try:
            # Filtrer l'historique par période
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=time_range_days)
            recent_workflows = [
                w for w in self.performance_history 
                if datetime.datetime.fromisoformat(w.get("created_at", "1970-01-01T00:00:00")) > cutoff_date
            ]
            
            if not recent_workflows:
                return {
                    "success": True,
                    "analysis": {"message": "Aucun workflow dans la période spécifiée"},
                    "recommendations": []
                }
            
            # Analyse avec l'agent
            analysis_prompt = f"""
            DONNÉES DE PERFORMANCE ({time_range_days} derniers jours):
            Workflows analysés: {len(recent_workflows)}
            
            MÉTRIQUES GLOBALES:
            {json.dumps({
                "total_workflows": len(recent_workflows),
                "avg_execution_time": sum(w["execution_time"] for w in recent_workflows) / len(recent_workflows),
                "success_rate": sum(1 for w in recent_workflows if w["success"]) / len(recent_workflows),
                "most_used_strategies": {}  # À calculer
            }, indent=2)}
            
            Fournis une analyse complète en JSON:
            {{
                "performance_trends": "analyse des tendances",
                "bottlenecks_identified": ["liste des problèmes"],
                "success_factors": ["facteurs de réussite"],
                "optimization_opportunities": ["opportunités d'amélioration"],
                "strategic_recommendations": ["recommandations stratégiques"],
                "predicted_improvements": "prédictions si recommandations appliquées"
            }}
            """
            
            analysis = await self._call_ollama_with_context("analysis", analysis_prompt)
            
            return {
                "success": True,
                "period_analyzed": f"{time_range_days} jours",
                "workflows_count": len(recent_workflows),
                "analysis": analysis,
                "raw_metrics": {
                    "total_execution_time": sum(w["execution_time"] for w in recent_workflows),
                    "average_execution_time": sum(w["execution_time"] for w in recent_workflows) / len(recent_workflows),
                    "success_rate": sum(1 for w in recent_workflows if w["success"]) / len(recent_workflows)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# INITIALISATION ET SERVEUR MCP
# =============================================================================

# Instance globale de l'orchestrateur
workflow_orchestrator = WorkflowOrchestrator()

if FASTMCP_AVAILABLE:
    mcp = FastMCP("WorkflowOrchestrator")

    @mcp.tool()
    async def create_intelligent_workflow(user_request: Dict[str, Any]) -> dict:
        """
        Crée et exécute un workflow intelligent basé sur la demande utilisateur.
        
        Args:
            user_request: Demande utilisateur avec paramètres et préférences
        
        Returns:
            Plan et résultats d'exécution du workflow
        """
        try:
            # L'agent analyse et planifie
            plan = await workflow_orchestrator.create_intelligent_plan(user_request)
            
            # Exécution du plan
            result = await workflow_orchestrator.execute_workflow_plan(plan)
            
            return {
                "success": True,
                "workflow_plan": asdict(plan),
                "execution_result": asdict(result),
                "agent_recommendations": result.agent_insights
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def optimize_existing_workflow(workflow_id: str, optimization_goals: List[str]) -> dict:
        """
        Optimise un workflow existant selon des objectifs spécifiques.
        
        Args:
            workflow_id: ID du workflow à optimiser
            optimization_goals: Objectifs d'optimisation (speed, quality, cost, etc.)
        
        Returns:
            Plan optimisé et recommandations
        """
        try:
            if workflow_id not in workflow_orchestrator.active_workflows:
                return {"success": False, "error": "Workflow non trouvé"}
            
            current_plan = workflow_orchestrator.active_workflows[workflow_id]
            
            optimization_prompt = f"""
            WORKFLOW À OPTIMISER:
            {json.dumps(asdict(current_plan), indent=2)}
            
            OBJECTIFS D'OPTIMISATION:
            {optimization_goals}
            
            Propose des optimisations. Réponds en JSON:
            {{
                "optimized_strategy": "nouvelle stratégie",
                "modified_steps": [{{...}}],
                "expected_improvements": {{
                    "time_reduction": "pourcentage",
                    "quality_improvement": "description",
                    "resource_savings": "description"
                }},
                "implementation_priority": "high|medium|low",
                "recommendations": ["liste de recommandations"]
            }}
            """
            
            optimizations = await workflow_orchestrator._call_ollama_with_context(
                "optimization", optimization_prompt
            )
            
            return {
                "success": True,
                "current_plan": asdict(current_plan),
                "optimizations": optimizations,
                "implementation_ready": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_orchestrator_status() -> dict:
        """
        Retourne l'état de l'orchestrateur et des workflows actifs.
        
        Returns:
            État détaillé de l'orchestrateur
        """
        try:
            return {
                "success": True,
                "status": {
                    "ollama_available": OLLAMA_AVAILABLE,
                    "fastmcp_available": FASTMCP_AVAILABLE,
                    "active_workflows": len(workflow_orchestrator.active_workflows),
                    "total_workflows_processed": len(workflow_orchestrator.performance_history),
                    "average_success_rate": workflow_orchestrator._get_performance_summary().get("success_rate", 0.0),
                    "agent_contexts": list(workflow_orchestrator.agent_contexts.keys()),
                    "capabilities": [
                        "intelligent_planning",
                        "adaptive_execution", 
                        "error_recovery",
                        "performance_optimization",
                        "multi_strategy_execution"
                    ]
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool() 
    async def analyze_workflow_performance(time_range_days: int = 7) -> dict:
        """
        Analyse les performances des workflows sur une période donnée.
        
        Args:
            time_range_days: Période d'analyse en jours
            
        Returns:
            Analyse détaillée des performances
        """
        try:
            # Filtrer l'historique par période
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=time_range_days)
            recent_workflows = [
                w for w in workflow_orchestrator.performance_history 
                if datetime.datetime.fromisoformat(w.get("created_at", "1970-01-01")) > cutoff_date
            ]
            
            if not recent_workflows:
                return {
                    "success": True,
                    "analysis": {"message": "Aucun workflow dans la période spécifiée"},
                    "recommendations": []
                }
            
            # Analyse avec l'agent
            analysis_prompt = f"""
            DONNÉES DE PERFORMANCE ({time_range_days} derniers jours):
            Workflows analysés: {len(recent_workflows)}
            
            MÉTRIQUES GLOBALES:
            {json.dumps({
                "total_workflows": len(recent_workflows),
                "avg_execution_time": sum(w["execution_time"] for w in recent_workflows) / len(recent_workflows),
                "success_rate": sum(1 for w in recent_workflows if w["success"]) / len(recent_workflows),
                "most_used_strategies": {}  # À calculer
            }, indent=2)}
            
            Fournis une analyse complète en JSON:
            {{
                "performance_trends": "analyse des tendances",
                "bottlenecks_identified": ["liste des problèmes"],
                "success_factors": ["facteurs de réussite"],
                "optimization_opportunities": ["opportunités d'amélioration"],
                "strategic_recommendations": ["recommandations stratégiques"],
                "predicted_improvements": "prédictions si recommandations appliquées"
            }}
            """
            
            analysis = await workflow_orchestrator._call_ollama_with_context(
                "analysis", analysis_prompt
            )
            
            return {
                "success": True,
                "period_analyzed": f"{time_range_days} jours",
                "workflows_count": len(recent_workflows),
                "analysis": analysis,
                "raw_metrics": {
                    "total_execution_time": sum(w["execution_time"] for w in recent_workflows),
                    "average_execution_time": sum(w["execution_time"] for w in recent_workflows) / len(recent_workflows),
                    "success_rate": sum(1 for w in recent_workflows if w["success"]) / len(recent_workflows)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🤖" + "="*60)
    print("🤖 WORKFLOW ORCHESTRATOR MCP - AGENT INTELLIGENT")
    print("🤖" + "="*60)
    
    # Vérification des dépendances
    print(f"📦 Dépendances:")
    print(f"   • Ollama: {'✅' if OLLAMA_AVAILABLE else '❌'}")
    print(f"   • FastMCP: {'✅' if FASTMCP_AVAILABLE else '❌'}")
    
    if OLLAMA_AVAILABLE:
        print(f"🧠 Configuration Agent:")
        print(f"   • Modèle: {workflow_orchestrator.ollama_model}")
        print(f"   • Contextes: {len(workflow_orchestrator.agent_contexts)} disponibles")
        print(f"   • Stratégies: Sequential, Parallel, Hybrid")
    
    print(f"🎯 Capacités:")
    print(f"   • Planification intelligente de workflows")
    print(f"   • Exécution adaptative (sequential/parallel/hybrid)")
    print(f"   • Récupération automatique d'erreurs")
    print(f"   • Optimisation en temps réel")
    print(f"   • Analyse de performance et insights")
    print(f"   • Apprentissage continu des patterns")
    
    # Test rapide de l'agent
    if OLLAMA_AVAILABLE:
        print(f"\n🧪 Test de l'agent...")
        try:
            import asyncio
            
            async def test_agent():
                test_request = {
                    "type": "batch_generation",
                    "signs": ["aries", "taurus"],
                    "include_video": True,
                    "optimization_goals": ["speed", "quality"]
                }
                
                plan = await workflow_orchestrator.create_intelligent_plan(test_request)
                print(f"✅ Agent opérationnel - Plan créé: {plan.execution_strategy}")
                return True
            
            # Exécuter le test
            test_result = asyncio.run(test_agent())
            if test_result:
                print("🚀 Agent prêt pour orchestration intelligente!")
            
        except Exception as e:
            print(f"⚠️  Test agent échoué: {e}")
            print("💡 Vérifiez qu'Ollama est démarré et que le modèle est disponible")
    
    # Démarrage du serveur MCP
    if FASTMCP_AVAILABLE:
        print(f"\n🌐 Démarrage serveur MCP...")
        print(f"🔧 Outils disponibles:")
        print(f"   • create_intelligent_workflow")
        print(f"   • optimize_existing_workflow") 
        print(f"   • get_orchestrator_status")
        print(f"   • analyze_workflow_performance")
        
        print(f"\n💡 Utilisation depuis app.py:")
        print(f"   from workflow_orchestrator_mcp import workflow_orchestrator")
        print(f"   result = await workflow_orchestrator.create_intelligent_plan(request)")
        
        mcp.run()
    else:
        print("❌ FastMCP non disponible - Serveur MCP non démarré")
        print("💡 pip install fastmcp pour activer le serveur")
        print("📄 L'orchestrateur peut être utilisé en mode module direct")