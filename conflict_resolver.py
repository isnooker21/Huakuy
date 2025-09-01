"""
Conflict Resolver for AI Gold Grid Trading System v3.0
Intelligent conflict resolution with priority-based decision matrix
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    """Types of conflicts that can occur in the trading system"""
    SAFETY_VS_OPPORTUNITY = "safety_vs_opportunity"
    PORTFOLIO_VS_ZONE = "portfolio_vs_zone"  
    IMMEDIATE_VS_LONGTERM = "immediate_vs_longterm"
    PERFORMANCE_VS_ACCURACY = "performance_vs_accuracy"
    VOLUME_VS_BALANCE = "volume_vs_balance"
    ZONE_CLUSTERING = "zone_clustering"

class Resolution(Enum):
    """Resolution strategies"""
    SAFETY_ALWAYS = "safety_always"
    ADAPTIVE_WEIGHTED = "adaptive_weighted" 
    BALANCED_60_40 = "balanced_60_40"
    ACCURACY_FIRST = "accuracy_first"
    PORTFOLIO_PRIORITY = "portfolio_priority"
    ZONE_PRIORITY = "zone_priority"

@dataclass
class ConflictDecision:
    """Result of conflict resolution"""
    conflict_type: ConflictType
    resolution: Resolution
    chosen_option: str
    confidence: float  # 0.0 - 1.0
    reasoning: str
    impact_score: float  # Expected impact of decision
    alternative_considered: Optional[str] = None

class ConflictResolver:
    """Intelligent conflict resolver with priority matrix and adaptive weights"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.conflict_history: List[ConflictDecision] = []
        self.resolution_strategies = self._setup_resolution_strategies()
        self.adaptive_weights = self._initialize_adaptive_weights()
        self.performance_tracker = {}
        
        # Load conflict resolution rules from config
        self.resolution_rules = config_manager.get_section("conflict_resolution")
        
    def _setup_resolution_strategies(self) -> Dict[ConflictType, Resolution]:
        """Setup default resolution strategies for each conflict type"""
        return {
            ConflictType.SAFETY_VS_OPPORTUNITY: Resolution.SAFETY_ALWAYS,
            ConflictType.PORTFOLIO_VS_ZONE: Resolution.ADAPTIVE_WEIGHTED,
            ConflictType.IMMEDIATE_VS_LONGTERM: Resolution.BALANCED_60_40,
            ConflictType.PERFORMANCE_VS_ACCURACY: Resolution.ACCURACY_FIRST,
            ConflictType.VOLUME_VS_BALANCE: Resolution.PORTFOLIO_PRIORITY,
            ConflictType.ZONE_CLUSTERING: Resolution.ZONE_PRIORITY
        }
    
    def _initialize_adaptive_weights(self) -> Dict[str, float]:
        """Initialize adaptive weights based on historical performance"""
        return {
            "safety_factor": 1.0,
            "portfolio_factor": 1.0,
            "zone_factor": 1.0,
            "performance_factor": 1.0,
            "recent_success_rate": 0.5,
            "volatility_adjustment": 1.0
        }
    
    def resolve_conflict(self, 
                        conflict_type: ConflictType,
                        option_a: Dict[str, Any],
                        option_b: Dict[str, Any],
                        context: Dict[str, Any] = None) -> ConflictDecision:
        """
        Resolve conflict between two options using intelligent priority matrix
        
        Args:
            conflict_type: Type of conflict to resolve
            option_a: First option with details
            option_b: Second option with details  
            context: Additional context for decision making
            
        Returns:
            ConflictDecision with resolution details
        """
        try:
            context = context or {}
            
            # Get resolution strategy
            strategy = self._get_resolution_strategy(conflict_type)
            
            # Apply resolution logic based on strategy
            decision = self._apply_resolution_strategy(
                conflict_type, strategy, option_a, option_b, context
            )
            
            # Record decision for learning
            self.conflict_history.append(decision)
            self._update_adaptive_weights(decision)
            
            logger.info(f"Conflict resolved: {conflict_type.value} → {decision.chosen_option} "
                       f"(confidence: {decision.confidence:.2f})")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict_type}: {str(e)}")
            # Return safe default
            return ConflictDecision(
                conflict_type=conflict_type,
                resolution=Resolution.SAFETY_ALWAYS,
                chosen_option="safe_default",
                confidence=0.5,
                reasoning=f"Error in resolution: {str(e)}",
                impact_score=0.0
            )
    
    def _get_resolution_strategy(self, conflict_type: ConflictType) -> Resolution:
        """Get resolution strategy from config or default"""
        try:
            config_key = conflict_type.value
            config_value = self.resolution_rules.get(config_key)
            
            if config_value:
                # Map config string to Resolution enum
                strategy_map = {
                    "safety_always": Resolution.SAFETY_ALWAYS,
                    "adaptive_weighted": Resolution.ADAPTIVE_WEIGHTED,
                    "balanced_60_40": Resolution.BALANCED_60_40,
                    "accuracy_first": Resolution.ACCURACY_FIRST,
                    "portfolio_priority": Resolution.PORTFOLIO_PRIORITY,
                    "zone_priority": Resolution.ZONE_PRIORITY
                }
                return strategy_map.get(config_value, self.resolution_strategies[conflict_type])
            
            return self.resolution_strategies[conflict_type]
            
        except Exception:
            return Resolution.SAFETY_ALWAYS  # Safe default
    
    def _apply_resolution_strategy(self,
                                 conflict_type: ConflictType,
                                 strategy: Resolution,
                                 option_a: Dict[str, Any],
                                 option_b: Dict[str, Any],
                                 context: Dict[str, Any]) -> ConflictDecision:
        """Apply specific resolution strategy"""
        
        if strategy == Resolution.SAFETY_ALWAYS:
            return self._resolve_safety_always(conflict_type, option_a, option_b, context)
        elif strategy == Resolution.ADAPTIVE_WEIGHTED:
            return self._resolve_adaptive_weighted(conflict_type, option_a, option_b, context)
        elif strategy == Resolution.BALANCED_60_40:
            return self._resolve_balanced_60_40(conflict_type, option_a, option_b, context)
        elif strategy == Resolution.ACCURACY_FIRST:
            return self._resolve_accuracy_first(conflict_type, option_a, option_b, context)
        elif strategy == Resolution.PORTFOLIO_PRIORITY:
            return self._resolve_portfolio_priority(conflict_type, option_a, option_b, context)
        elif strategy == Resolution.ZONE_PRIORITY:
            return self._resolve_zone_priority(conflict_type, option_a, option_b, context)
        else:
            return self._resolve_safety_always(conflict_type, option_a, option_b, context)
    
    def _resolve_safety_always(self, conflict_type, option_a, option_b, context) -> ConflictDecision:
        """Always choose the safer option"""
        
        safety_score_a = option_a.get('safety_score', 0.0)
        safety_score_b = option_b.get('safety_score', 0.0)
        
        if safety_score_a >= safety_score_b:
            chosen = 'option_a'
            confidence = min(0.9, 0.5 + (safety_score_a - safety_score_b) * 0.5)
            reasoning = f"Safety priority: option A score {safety_score_a:.2f} vs B {safety_score_b:.2f}"
        else:
            chosen = 'option_b'
            confidence = min(0.9, 0.5 + (safety_score_b - safety_score_a) * 0.5)
            reasoning = f"Safety priority: option B score {safety_score_b:.2f} vs A {safety_score_a:.2f}"
        
        return ConflictDecision(
            conflict_type=conflict_type,
            resolution=Resolution.SAFETY_ALWAYS,
            chosen_option=chosen,
            confidence=confidence,
            reasoning=reasoning,
            impact_score=max(safety_score_a, safety_score_b)
        )
    
    def _resolve_adaptive_weighted(self, conflict_type, option_a, option_b, context) -> ConflictDecision:
        """Use adaptive weights based on current market conditions and performance"""
        
        # Get decision weights from config
        weights = self.config_manager.get_section("decision_weights")
        
        # Calculate weighted scores for each option
        score_a = self._calculate_weighted_score(option_a, weights, context)
        score_b = self._calculate_weighted_score(option_b, weights, context)
        
        # Apply adaptive adjustments
        adjusted_score_a = score_a * self._get_adaptive_factor(option_a, context)
        adjusted_score_b = score_b * self._get_adaptive_factor(option_b, context)
        
        if adjusted_score_a >= adjusted_score_b:
            chosen = 'option_a'
            confidence = min(0.95, 0.5 + abs(adjusted_score_a - adjusted_score_b) * 0.5)
            impact = adjusted_score_a
        else:
            chosen = 'option_b'
            confidence = min(0.95, 0.5 + abs(adjusted_score_b - adjusted_score_a) * 0.5)
            impact = adjusted_score_b
        
        reasoning = f"Adaptive weighted: A={adjusted_score_a:.3f} vs B={adjusted_score_b:.3f}"
        
        return ConflictDecision(
            conflict_type=conflict_type,
            resolution=Resolution.ADAPTIVE_WEIGHTED,
            chosen_option=chosen,
            confidence=confidence,
            reasoning=reasoning,
            impact_score=impact
        )
    
    def _resolve_balanced_60_40(self, conflict_type, option_a, option_b, context) -> ConflictDecision:
        """Balance immediate vs long-term considerations 60:40"""
        
        immediate_score_a = option_a.get('immediate_score', 0.0)
        longterm_score_a = option_a.get('longterm_score', 0.0)
        immediate_score_b = option_b.get('immediate_score', 0.0)
        longterm_score_b = option_b.get('longterm_score', 0.0)
        
        balanced_score_a = immediate_score_a * 0.6 + longterm_score_a * 0.4
        balanced_score_b = immediate_score_b * 0.6 + longterm_score_b * 0.4
        
        if balanced_score_a >= balanced_score_b:
            chosen = 'option_a'
            confidence = min(0.9, 0.5 + abs(balanced_score_a - balanced_score_b) * 0.5)
            impact = balanced_score_a
        else:
            chosen = 'option_b'
            confidence = min(0.9, 0.5 + abs(balanced_score_b - balanced_score_a) * 0.5)
            impact = balanced_score_b
        
        reasoning = f"Balanced 60:40: A={balanced_score_a:.3f} vs B={balanced_score_b:.3f}"
        
        return ConflictDecision(
            conflict_type=conflict_type,
            resolution=Resolution.BALANCED_60_40,
            chosen_option=chosen,
            confidence=confidence,
            reasoning=reasoning,
            impact_score=impact
        )
    
    def _resolve_accuracy_first(self, conflict_type, option_a, option_b, context) -> ConflictDecision:
        """Prioritize accuracy over speed"""
        
        accuracy_score_a = option_a.get('accuracy_score', 0.0)
        accuracy_score_b = option_b.get('accuracy_score', 0.0)
        
        # If accuracy is similar, consider performance
        if abs(accuracy_score_a - accuracy_score_b) < 0.05:
            performance_score_a = option_a.get('performance_score', 0.0)
            performance_score_b = option_b.get('performance_score', 0.0)
            
            total_score_a = accuracy_score_a * 0.8 + performance_score_a * 0.2
            total_score_b = accuracy_score_b * 0.8 + performance_score_b * 0.2
        else:
            total_score_a = accuracy_score_a
            total_score_b = accuracy_score_b
        
        if total_score_a >= total_score_b:
            chosen = 'option_a'
            confidence = min(0.95, 0.6 + abs(total_score_a - total_score_b) * 0.4)
            impact = total_score_a
        else:
            chosen = 'option_b'
            confidence = min(0.95, 0.6 + abs(total_score_b - total_score_a) * 0.4)
            impact = total_score_b
        
        reasoning = f"Accuracy first: A={total_score_a:.3f} vs B={total_score_b:.3f}"
        
        return ConflictDecision(
            conflict_type=conflict_type,
            resolution=Resolution.ACCURACY_FIRST,
            chosen_option=chosen,
            confidence=confidence,
            reasoning=reasoning,
            impact_score=impact
        )
    
    def _resolve_portfolio_priority(self, conflict_type, option_a, option_b, context) -> ConflictDecision:
        """Prioritize portfolio health and balance"""
        
        portfolio_score_a = option_a.get('portfolio_score', 0.0)
        portfolio_score_b = option_b.get('portfolio_score', 0.0)
        
        # Consider current portfolio health
        portfolio_health = context.get('portfolio_health', 100.0)
        health_factor = 1.0 if portfolio_health > 80 else (portfolio_health / 80)
        
        adjusted_score_a = portfolio_score_a * health_factor
        adjusted_score_b = portfolio_score_b * health_factor
        
        if adjusted_score_a >= adjusted_score_b:
            chosen = 'option_a'
            confidence = min(0.9, 0.5 + abs(adjusted_score_a - adjusted_score_b) * 0.5)
            impact = adjusted_score_a
        else:
            chosen = 'option_b'
            confidence = min(0.9, 0.5 + abs(adjusted_score_b - adjusted_score_a) * 0.5)
            impact = adjusted_score_b
        
        reasoning = f"Portfolio priority: A={adjusted_score_a:.3f} vs B={adjusted_score_b:.3f} (health: {portfolio_health:.1f})"
        
        return ConflictDecision(
            conflict_type=conflict_type,
            resolution=Resolution.PORTFOLIO_PRIORITY,
            chosen_option=chosen,
            confidence=confidence,
            reasoning=reasoning,
            impact_score=impact
        )
    
    def _resolve_zone_priority(self, conflict_type, option_a, option_b, context) -> ConflictDecision:
        """Prioritize zone distribution and clustering prevention"""
        
        zone_score_a = option_a.get('zone_score', 0.0)
        zone_score_b = option_b.get('zone_score', 0.0)
        
        # Consider zone distribution quality
        zone_distribution = context.get('zone_distribution_score', 100.0)
        distribution_factor = zone_distribution / 100.0
        
        adjusted_score_a = zone_score_a * distribution_factor
        adjusted_score_b = zone_score_b * distribution_factor
        
        if adjusted_score_a >= adjusted_score_b:
            chosen = 'option_a'
            confidence = min(0.9, 0.5 + abs(adjusted_score_a - adjusted_score_b) * 0.5)
            impact = adjusted_score_a
        else:
            chosen = 'option_b'
            confidence = min(0.9, 0.5 + abs(adjusted_score_b - adjusted_score_a) * 0.5)
            impact = adjusted_score_b
        
        reasoning = f"Zone priority: A={adjusted_score_a:.3f} vs B={adjusted_score_b:.3f} (distribution: {zone_distribution:.1f})"
        
        return ConflictDecision(
            conflict_type=conflict_type,
            resolution=Resolution.ZONE_PRIORITY,
            chosen_option=chosen,
            confidence=confidence,
            reasoning=reasoning,
            impact_score=impact
        )
    
    def _calculate_weighted_score(self, option: Dict[str, Any], weights: Dict[str, float], context: Dict[str, Any]) -> float:
        """Calculate weighted score for an option"""
        try:
            score = 0.0
            score += option.get('safety_score', 0.0) * weights.get('safety_check', 0.35)
            score += option.get('portfolio_score', 0.0) * weights.get('portfolio_health', 0.25)
            score += option.get('zone_score', 0.0) * weights.get('zone_distribution', 0.20)
            score += option.get('balance_score', 0.0) * weights.get('balance_optimization', 0.15)
            score += option.get('signal_score', 0.0) * weights.get('signal_quality', 0.05)
            
            return score
        except Exception:
            return 0.0
    
    def _get_adaptive_factor(self, option: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate adaptive factor based on recent performance"""
        try:
            # Base factor
            factor = 1.0
            
            # Adjust based on recent success rate
            success_rate = self.adaptive_weights.get('recent_success_rate', 0.5)
            if success_rate > 0.7:
                factor *= 1.1  # Boost if performing well
            elif success_rate < 0.3:
                factor *= 0.9  # Reduce if performing poorly
            
            # Adjust for volatility
            volatility = context.get('market_volatility', 1.0)
            volatility_adjustment = self.adaptive_weights.get('volatility_adjustment', 1.0)
            if volatility > 2.0:
                factor *= 0.9  # More conservative in high volatility
            elif volatility < 0.5:
                factor *= 1.1  # More aggressive in low volatility
            
            return max(0.5, min(1.5, factor))  # Bound the factor
            
        except Exception:
            return 1.0
    
    def _update_adaptive_weights(self, decision: ConflictDecision):
        """Update adaptive weights based on decision outcomes"""
        try:
            # This would be called after we know the outcome of a decision
            # For now, just track the decision
            conflict_key = decision.conflict_type.value
            if conflict_key not in self.performance_tracker:
                self.performance_tracker[conflict_key] = {
                    'total_decisions': 0,
                    'successful_outcomes': 0,
                    'avg_confidence': 0.0,
                    'avg_impact': 0.0
                }
            
            tracker = self.performance_tracker[conflict_key]
            tracker['total_decisions'] += 1
            
            # Update running averages
            total = tracker['total_decisions']
            tracker['avg_confidence'] = ((tracker['avg_confidence'] * (total - 1)) + decision.confidence) / total
            tracker['avg_impact'] = ((tracker['avg_impact'] * (total - 1)) + decision.impact_score) / total
            
        except Exception as e:
            logger.error(f"Error updating adaptive weights: {str(e)}")
    
    def record_decision_outcome(self, decision: ConflictDecision, outcome_success: bool, actual_impact: float = 0.0):
        """Record the actual outcome of a decision for learning"""
        try:
            conflict_key = decision.conflict_type.value
            if conflict_key in self.performance_tracker:
                tracker = self.performance_tracker[conflict_key]
                if outcome_success:
                    tracker['successful_outcomes'] += 1
                
                # Update success rate
                success_rate = tracker['successful_outcomes'] / tracker['total_decisions']
                self.adaptive_weights['recent_success_rate'] = success_rate
                
                logger.info(f"Decision outcome recorded: {conflict_key} success={outcome_success}, "
                           f"new success rate: {success_rate:.3f}")
                
        except Exception as e:
            logger.error(f"Error recording decision outcome: {str(e)}")
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """Get statistics about conflict resolution performance"""
        try:
            stats = {
                'total_conflicts_resolved': len(self.conflict_history),
                'performance_by_type': {},
                'overall_success_rate': self.adaptive_weights.get('recent_success_rate', 0.5),
                'adaptive_weights': self.adaptive_weights.copy()
            }
            
            for conflict_type, tracker in self.performance_tracker.items():
                if tracker['total_decisions'] > 0:
                    stats['performance_by_type'][conflict_type] = {
                        'total_decisions': tracker['total_decisions'],
                        'success_rate': tracker['successful_outcomes'] / tracker['total_decisions'],
                        'avg_confidence': tracker['avg_confidence'],
                        'avg_impact': tracker['avg_impact']
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting conflict statistics: {str(e)}")
            return {}