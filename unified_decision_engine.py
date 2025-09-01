"""
Unified Decision Engine for AI Gold Grid Trading System v3.0
Single point of control for all trading decisions with conflict resolution
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import our new components
from config_manager import ConfigurationManager
from conflict_resolver import ConflictResolver, ConflictType, ConflictDecision
from performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)

class DecisionAction(Enum):
    """Possible decision actions"""
    EXECUTE = "execute"
    REDIRECT = "redirect"
    SKIP = "skip"
    CLOSE = "close"
    HEDGE = "hedge"

@dataclass
class DecisionResult:
    """Unified decision result"""
    action: DecisionAction
    lot_size: float
    target_position: Optional[Any] = None
    confidence: float = 0.0
    reasoning: str = ""
    safety_score: float = 0.0
    portfolio_score: float = 0.0
    zone_score: float = 0.0
    balance_score: float = 0.0
    signal_score: float = 0.0
    weighted_score: float = 0.0
    conflicts_resolved: List[ConflictDecision] = None
    execution_time_ms: float = 0.0
    cache_used: bool = False

class UnifiedDecisionEngine:
    """
    Unified decision engine that eliminates conflicts and provides single point of control
    Implements weighted scoring system with intelligent conflict resolution
    """
    
    def __init__(self, config_manager: ConfigurationManager, 
                 performance_optimizer: PerformanceOptimizer):
        self.config = config_manager
        self.performance = performance_optimizer
        self.conflict_resolver = ConflictResolver(config_manager)
        
        # Load decision weights from config
        self.weights = config_manager.get_section("decision_weights")
        
        # Load trading parameters
        self.trading_params = config_manager.get_section("trading_parameters")
        self.portfolio_params = config_manager.get_section("portfolio_management")
        self.zone_params = config_manager.get_section("zone_based_trading")
        self.lot_params = config_manager.get_section("lot_sizing")
        self.risk_params = config_manager.get_section("risk_management")
        
        # Decision statistics
        self.decision_history = []
        self.performance_tracker = {
            "total_decisions": 0,
            "execution_times": [],
            "cache_hit_rate": 0.0,
            "conflicts_resolved": 0
        }
        
        # Circuit breaker state
        self.circuit_breaker = config_manager.get_section("circuit_breaker")
        self.circuit_breaker_open = False
        self.circuit_breaker_last_failure = None
        
        logger.info("UnifiedDecisionEngine initialized with weighted scoring system")
    
    def process_signal(self, signal: Any, trading_system_state: Dict[str, Any]) -> DecisionResult:
        """
        Main decision processing method - single point of control
        
        Args:
            signal: Trading signal to process
            trading_system_state: Current state of trading system
            
        Returns:
            DecisionResult with final decision and reasoning
        """
        start_time = time.time()
        
        try:
            # Circuit breaker check
            if self._is_circuit_breaker_open():
                return self._create_safe_default_decision(signal, "Circuit breaker open")
            
            # Phase 1: Safety validation (hard requirements)
            safety_result = self._validate_safety_requirements(signal, trading_system_state)
            if not safety_result["passed"]:
                return self._create_decision_result(
                    action=DecisionAction.SKIP,
                    lot_size=0.0,
                    reasoning=f"Safety check failed: {safety_result['reason']}",
                    safety_score=0.0
                )
            
            # Phase 2: Calculate all factor scores (no redundancy)
            scores = self._calculate_all_scores(signal, trading_system_state)
            
            # Phase 3: Check for conflicts and resolve them
            conflicts_resolved = self._identify_and_resolve_conflicts(scores, signal, trading_system_state)
            
            # Phase 4: Apply weighted scoring
            weighted_score = self._calculate_weighted_score(scores)
            
            # Phase 5: Make final decision
            final_decision = self._make_final_decision(scores, weighted_score, signal, trading_system_state)
            
            # Phase 6: Calculate lot size (single method)
            lot_size = self._calculate_unified_lot_size(signal, scores, final_decision)
            
            # Create decision result
            decision_result = DecisionResult(
                action=final_decision["action"],
                lot_size=lot_size,
                target_position=final_decision.get("target_position"),
                confidence=final_decision["confidence"],
                reasoning=final_decision["reasoning"],
                safety_score=scores["safety"],
                portfolio_score=scores["portfolio"],
                zone_score=scores["zone"],
                balance_score=scores["balance"],
                signal_score=scores["signal"],
                weighted_score=weighted_score,
                conflicts_resolved=conflicts_resolved,
                execution_time_ms=(time.time() - start_time) * 1000,
                cache_used=False  # Will be set by cache decorator
            )
            
            # Record decision for learning
            self._record_decision(decision_result, signal, trading_system_state)
            
            return decision_result
            
        except Exception as e:
            logger.error(f"Error in unified decision processing: {str(e)}")
            return self._create_safe_default_decision(signal, f"Processing error: {str(e)}")
    
    def _validate_safety_requirements(self, signal: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Hard safety validation"""
        try:
            # Check margin level
            margin_level = state.get("margin_level", 0.0)
            if margin_level < self.trading_params.get("min_margin_level", 200.0):
                return {
                    "passed": False,
                    "reason": f"Margin level {margin_level:.1f}% below minimum {self.trading_params.get('min_margin_level', 200.0)}%"
                }
            
            # Check maximum positions
            position_count = len(state.get("positions", []))
            if position_count >= self.trading_params.get("max_positions", 50):
                return {
                    "passed": False,
                    "reason": f"Maximum positions reached: {position_count}"
                }
            
            # Check signal cooldown
            last_signal_time = state.get("last_signal_time")
            if last_signal_time:
                time_since_last = (datetime.now() - last_signal_time).seconds
                if time_since_last < self.trading_params.get("signal_cooldown", 60):
                    return {
                        "passed": False,
                        "reason": f"Signal cooldown: {time_since_last}s < {self.trading_params.get('signal_cooldown', 60)}s"
                    }
            
            # Check hourly signal limit
            hourly_signals = state.get("hourly_signals", [])
            if len(hourly_signals) >= self.trading_params.get("max_signals_per_hour", 40):
                return {
                    "passed": False,
                    "reason": f"Hourly signal limit reached: {len(hourly_signals)}"
                }
            
            # Check portfolio health
            portfolio_health = state.get("portfolio_health", 100.0)
            if portfolio_health < 25.0:  # Emergency threshold
                return {
                    "passed": False,
                    "reason": f"Portfolio health critical: {portfolio_health:.1f}%"
                }
            
            return {"passed": True, "reason": "All safety checks passed"}
            
        except Exception as e:
            logger.error(f"Safety validation error: {str(e)}")
            return {"passed": False, "reason": f"Safety validation error: {str(e)}"}
    
    def _calculate_all_scores(self, signal: Any, state: Dict[str, Any]) -> Dict[str, float]:
        """Phase 2: Calculate all factor scores once (no redundancy)"""
        try:
            scores = {}
            
            # Safety score (0.0 - 1.0)
            scores["safety"] = self._calculate_safety_score(signal, state)
            
            # Portfolio health score (0.0 - 1.0)
            scores["portfolio"] = self._calculate_portfolio_score(signal, state)
            
            # Zone distribution score (0.0 - 1.0)
            scores["zone"] = self._calculate_zone_score(signal, state)
            
            # Balance optimization score (0.0 - 1.0)
            scores["balance"] = self._calculate_balance_score(signal, state)
            
            # Signal quality score (0.0 - 1.0)
            scores["signal"] = self._calculate_signal_score(signal, state)
            
            return scores
            
        except Exception as e:
            logger.error(f"Score calculation error: {str(e)}")
            return {
                "safety": 0.5,
                "portfolio": 0.5,
                "zone": 0.5,
                "balance": 0.5,
                "signal": 0.5
            }
    
    def _calculate_safety_score(self, signal: Any, state: Dict[str, Any]) -> float:
        """Calculate safety score based on risk factors"""
        try:
            score = 1.0
            
            # Margin level factor
            margin_level = state.get("margin_level", 200.0)
            margin_factor = min(1.0, (margin_level - 100) / 200)  # 100% = 0, 300%+ = 1
            score *= margin_factor
            
            # Portfolio health factor
            portfolio_health = state.get("portfolio_health", 100.0)
            health_factor = portfolio_health / 100.0
            score *= health_factor
            
            # Position count factor
            position_count = len(state.get("positions", []))
            max_positions = self.trading_params.get("max_positions", 50)
            position_factor = 1.0 - (position_count / max_positions)
            score *= position_factor
            
            # Exposure risk factor
            if self.risk_params.get("anti_exposure_enabled", True):
                exposure_distance = state.get("exposure_distance", 0)
                max_exposure = self.risk_params.get("max_exposure_distance", 150)
                if exposure_distance > 0:
                    exposure_factor = 1.0 - (exposure_distance / max_exposure)
                    score *= max(0.1, exposure_factor)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Safety score calculation error: {str(e)}")
            return 0.5
    
    def _calculate_portfolio_score(self, signal: Any, state: Dict[str, Any]) -> float:
        """Calculate portfolio health and balance score"""
        try:
            score = 1.0
            
            # Portfolio health component
            portfolio_health = state.get("portfolio_health", 100.0)
            health_score = portfolio_health / 100.0
            
            # Volume balance component
            buy_volume = state.get("buy_volume", 0.0)
            sell_volume = state.get("sell_volume", 0.0)
            total_volume = buy_volume + sell_volume
            
            if total_volume > 0:
                buy_ratio = buy_volume / total_volume
                target_ratio = self.portfolio_params.get("balance_target_ratio", 0.5)
                balance_deviation = abs(buy_ratio - target_ratio)
                balance_score = 1.0 - (balance_deviation * 2)  # Max deviation is 0.5
                
                # Combine health and balance
                score = (health_score * 0.7) + (balance_score * 0.3)
            else:
                score = health_score
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Portfolio score calculation error: {str(e)}")
            return 0.5
    
    def _calculate_zone_score(self, signal: Any, state: Dict[str, Any]) -> float:
        """Calculate zone distribution and clustering score"""
        try:
            # Get cached zone analysis
            cache_key = f"zone_analysis:{state.get('positions_hash', 'default')}"
            zone_analysis = self.performance.get(cache_key)
            
            if zone_analysis is None:
                zone_analysis = self._analyze_zones(state)
                self.performance.set(cache_key, zone_analysis, ttl_seconds=30)
            
            # Extract distribution score
            distribution_score = zone_analysis.get("distribution_score", 100.0) / 100.0
            
            # Check signal zone clustering
            signal_price = getattr(signal, 'price', 0.0)
            if signal_price > 0:
                clustering_score = self._calculate_zone_clustering_score(signal_price, zone_analysis)
                # Combine distribution and clustering
                score = (distribution_score * 0.6) + (clustering_score * 0.4)
            else:
                score = distribution_score
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Zone score calculation error: {str(e)}")
            return 0.5
    
    def _calculate_balance_score(self, signal: Any, state: Dict[str, Any]) -> float:
        """Calculate BUY/SELL balance optimization score"""
        try:
            buy_volume = state.get("buy_volume", 0.0)
            sell_volume = state.get("sell_volume", 0.0)
            total_volume = buy_volume + sell_volume
            
            if total_volume == 0:
                return 1.0  # Perfect score for empty portfolio
            
            buy_ratio = buy_volume / total_volume
            target_ratio = self.portfolio_params.get("balance_target_ratio", 0.5)
            tolerance = self.portfolio_params.get("balance_tolerance", 0.15)
            
            # Calculate how this signal would affect balance
            signal_direction = getattr(signal, 'direction', 'BUY')
            signal_strength = getattr(signal, 'strength', 1.0)
            
            # Simulate adding this signal
            simulated_volume = self.lot_params.get("base_lot_size", 0.01) * signal_strength
            if signal_direction == 'BUY':
                new_buy_volume = buy_volume + simulated_volume
                new_sell_volume = sell_volume
            else:
                new_buy_volume = buy_volume
                new_sell_volume = sell_volume + simulated_volume
            
            new_total = new_buy_volume + new_sell_volume
            new_buy_ratio = new_buy_volume / new_total if new_total > 0 else 0.5
            
            # Score based on how close to target this gets us
            current_deviation = abs(buy_ratio - target_ratio)
            new_deviation = abs(new_buy_ratio - target_ratio)
            
            if new_deviation < current_deviation:
                # Signal improves balance
                score = 1.0 - new_deviation / (target_ratio + tolerance)
            else:
                # Signal worsens balance
                score = 1.0 - new_deviation / (target_ratio + tolerance)
                score *= 0.5  # Penalty for worsening balance
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Balance score calculation error: {str(e)}")
            return 0.5
    
    def _calculate_signal_score(self, signal: Any, state: Dict[str, Any]) -> float:
        """Calculate signal quality score"""
        try:
            score = 0.5  # Base score
            
            # Signal strength component
            signal_strength = getattr(signal, 'strength', 1.0)
            strength_score = min(1.0, signal_strength / 3.0)  # Normalize to 0-1 (assuming max strength is 3.0)
            
            # Signal timing component (fresher signals are better)
            signal_time = getattr(signal, 'timestamp', datetime.now())
            if isinstance(signal_time, datetime):
                age_minutes = (datetime.now() - signal_time).seconds / 60
                timing_score = max(0.1, 1.0 - (age_minutes / 60))  # Degrade over 1 hour
            else:
                timing_score = 1.0
            
            # Signal reason quality (basic heuristic)
            signal_reason = getattr(signal, 'reason', '')
            if signal_reason:
                reason_quality = min(1.0, len(signal_reason) / 50)  # Longer reasons might be more detailed
            else:
                reason_quality = 0.5
            
            # Combine components
            score = (strength_score * 0.5) + (timing_score * 0.3) + (reason_quality * 0.2)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Signal score calculation error: {str(e)}")
            return 0.5
    
    def _identify_and_resolve_conflicts(self, scores: Dict[str, float], 
                                      signal: Any, state: Dict[str, Any]) -> List[ConflictDecision]:
        """Phase 3: Identify and resolve conflicts"""
        try:
            conflicts_resolved = []
            
            # Check safety vs opportunity conflict
            if scores["safety"] < 0.6 and scores["signal"] > 0.8:
                conflict = self.conflict_resolver.resolve_conflict(
                    ConflictType.SAFETY_VS_OPPORTUNITY,
                    {"safety_score": scores["safety"], "name": "safety_priority"},
                    {"signal_score": scores["signal"], "name": "opportunity_priority"},
                    {"portfolio_health": state.get("portfolio_health", 100.0)}
                )
                conflicts_resolved.append(conflict)
                
                # Apply conflict resolution
                if conflict.chosen_option == "safety_priority":
                    scores["safety"] *= 1.2  # Boost safety consideration
                    scores["signal"] *= 0.8  # Reduce signal weight
            
            # Check portfolio vs zone conflict
            if abs(scores["portfolio"] - scores["zone"]) > 0.3:
                conflict = self.conflict_resolver.resolve_conflict(
                    ConflictType.PORTFOLIO_VS_ZONE,
                    {"portfolio_score": scores["portfolio"], "name": "portfolio_priority"},
                    {"zone_score": scores["zone"], "name": "zone_priority"},
                    state
                )
                conflicts_resolved.append(conflict)
                
                # Apply adaptive weighting
                if conflict.chosen_option == "portfolio_priority":
                    scores["portfolio"] *= 1.1
                    scores["zone"] *= 0.9
                else:
                    scores["zone"] *= 1.1
                    scores["portfolio"] *= 0.9
            
            # Check volume vs balance conflict
            buy_volume = state.get("buy_volume", 0.0)
            sell_volume = state.get("sell_volume", 0.0)
            total_volume = buy_volume + sell_volume
            
            if total_volume > 0:
                buy_ratio = buy_volume / total_volume
                signal_direction = getattr(signal, 'direction', 'BUY')
                
                # High volume but poor balance
                if total_volume > 1.0 and abs(buy_ratio - 0.5) > 0.2:
                    conflict = self.conflict_resolver.resolve_conflict(
                        ConflictType.VOLUME_VS_BALANCE,
                        {"balance_score": scores["balance"], "name": "balance_priority"},
                        {"portfolio_score": scores["portfolio"], "name": "volume_priority"},
                        {"buy_ratio": buy_ratio, "signal_direction": signal_direction}
                    )
                    conflicts_resolved.append(conflict)
            
            return conflicts_resolved
            
        except Exception as e:
            logger.error(f"Conflict resolution error: {str(e)}")
            return []
    
    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Phase 4: Apply weighted scoring"""
        try:
            weighted_score = 0.0
            total_weight = 0.0
            
            for factor, score in scores.items():
                weight = self.weights.get(f"{factor}_check" if factor == "safety" else factor, 0.0)
                if weight > 0:
                    weighted_score += score * weight
                    total_weight += weight
            
            # Normalize by total weight
            if total_weight > 0:
                weighted_score /= total_weight
            
            return max(0.0, min(1.0, weighted_score))
            
        except Exception as e:
            logger.error(f"Weighted score calculation error: {str(e)}")
            return 0.5
    
    def _make_final_decision(self, scores: Dict[str, float], weighted_score: float,
                           signal: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 5: Make final decision based on all factors"""
        try:
            # Decision thresholds
            execute_threshold = 0.6
            redirect_threshold = 0.4
            
            # Check for redirect opportunities first
            if self._should_redirect(scores, state):
                redirect_target = self._find_redirect_target(signal, state)
                if redirect_target:
                    return {
                        "action": DecisionAction.REDIRECT,
                        "confidence": min(0.9, weighted_score + 0.1),
                        "reasoning": f"Redirect to optimize portfolio (score: {weighted_score:.3f})",
                        "target_position": redirect_target
                    }
            
            # Main decision logic
            if weighted_score >= execute_threshold:
                return {
                    "action": DecisionAction.EXECUTE,
                    "confidence": weighted_score,
                    "reasoning": f"Execute signal (weighted score: {weighted_score:.3f})"
                }
            elif weighted_score >= redirect_threshold:
                # Look for alternative actions
                if scores["balance"] < 0.4:
                    return {
                        "action": DecisionAction.SKIP,
                        "confidence": 1.0 - weighted_score,
                        "reasoning": f"Skip for balance protection (score: {weighted_score:.3f})"
                    }
                else:
                    return {
                        "action": DecisionAction.EXECUTE,
                        "confidence": weighted_score * 0.8,
                        "reasoning": f"Cautious execute (score: {weighted_score:.3f})"
                    }
            else:
                return {
                    "action": DecisionAction.SKIP,
                    "confidence": 1.0 - weighted_score,
                    "reasoning": f"Skip signal (low score: {weighted_score:.3f})"
                }
                
        except Exception as e:
            logger.error(f"Final decision error: {str(e)}")
            return {
                "action": DecisionAction.SKIP,
                "confidence": 0.5,
                "reasoning": f"Decision error: {str(e)}"
            }
    
    def _calculate_unified_lot_size(self, signal: Any, scores: Dict[str, float], 
                                  decision: Dict[str, Any]) -> float:
        """Phase 6: Calculate lot size using single unified method"""
        try:
            # Base lot size
            base_lot = self.lot_params.get("base_lot_size", 0.01)
            
            # Signal strength multiplier
            signal_strength = getattr(signal, 'strength', 1.0)
            if self.lot_params.get("signal_strength_multiplier", True):
                strength_multiplier = max(0.5, min(3.0, signal_strength))
            else:
                strength_multiplier = 1.0
            
            # Risk-based sizing
            risk_range = self.lot_params.get("risk_percent_range", [0.01, 0.03])
            risk_percent = risk_range[0] + (scores["safety"] * (risk_range[1] - risk_range[0]))
            
            # Portfolio health adjustment
            portfolio_health = scores["portfolio"]
            health_multiplier = 0.5 + (portfolio_health * 0.5)  # 0.5 to 1.0 range
            
            # Zone risk adjustment
            zone_multiplier = 0.7 + (scores["zone"] * 0.6)  # 0.7 to 1.3 range
            
            # Balance adjustment
            balance_multiplier = 0.8 + (scores["balance"] * 0.4)  # 0.8 to 1.2 range
            
            # Confidence adjustment
            confidence_multiplier = 0.7 + (decision["confidence"] * 0.3)  # 0.7 to 1.0 range
            
            # Calculate final lot size
            calculated_lot = (base_lot * 
                            strength_multiplier * 
                            health_multiplier * 
                            zone_multiplier * 
                            balance_multiplier * 
                            confidence_multiplier)
            
            # Apply bounds
            min_lot = self.lot_params.get("base_lot_size", 0.01)
            max_lot = self.lot_params.get("max_lot_size", 0.10)
            
            final_lot = max(min_lot, min(max_lot, calculated_lot))
            
            # Round to valid increments (0.01)
            final_lot = round(final_lot, 2)
            
            return final_lot
            
        except Exception as e:
            logger.error(f"Lot size calculation error: {str(e)}")
            return self.lot_params.get("base_lot_size", 0.01)
    
    def _should_redirect(self, scores: Dict[str, float], state: Dict[str, Any]) -> bool:
        """Check if redirect is beneficial"""
        try:
            # Check redirect conditions
            buy_volume = state.get("buy_volume", 0.0)
            sell_volume = state.get("sell_volume", 0.0)
            total_volume = buy_volume + sell_volume
            
            if total_volume == 0:
                return False
            
            buy_ratio = buy_volume / total_volume
            redirect_threshold = self.portfolio_params.get("redirect_threshold", 0.65)
            
            # Redirect if balance is too skewed
            if buy_ratio > redirect_threshold or buy_ratio < (1 - redirect_threshold):
                return scores["portfolio"] > 0.3  # Only if portfolio is reasonably healthy
            
            return False
            
        except Exception:
            return False
    
    def _find_redirect_target(self, signal: Any, state: Dict[str, Any]) -> Optional[Any]:
        """Find best position to close for redirect"""
        try:
            positions = state.get("positions", [])
            if not positions:
                return None
            
            # Find positions with profit that can be closed
            profitable_positions = [p for p in positions if getattr(p, 'profit', 0) > 0]
            
            if profitable_positions:
                # Return the most profitable position
                return max(profitable_positions, key=lambda p: getattr(p, 'profit', 0))
            
            return None
            
        except Exception:
            return None
    
    def _analyze_zones(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze position zones (simplified version)"""
        try:
            positions = state.get("positions", [])
            if not positions:
                return {
                    "distribution_score": 100.0,
                    "clustered_zones": [],
                    "total_zones_used": 0
                }
            
            # Simple zone analysis
            zone_size = self.zone_params.get("zone_size_pips", 25)
            zones = {}
            
            for pos in positions:
                price = getattr(pos, 'open_price', 0.0)
                if price > 0:
                    zone_index = int(price / zone_size)
                    if zone_index not in zones:
                        zones[zone_index] = []
                    zones[zone_index].append(pos)
            
            # Calculate distribution score
            max_positions_per_zone = self.zone_params.get("max_positions_per_zone", 3)
            clustered_zones = []
            
            for zone_index, zone_positions in zones.items():
                if len(zone_positions) > max_positions_per_zone:
                    clustered_zones.append({
                        "zone_index": zone_index,
                        "position_count": len(zone_positions)
                    })
            
            # Score: 100 - (clustering penalty)
            clustering_penalty = len(clustered_zones) * 20
            distribution_score = max(0.0, 100.0 - clustering_penalty)
            
            return {
                "distribution_score": distribution_score,
                "clustered_zones": clustered_zones,
                "total_zones_used": len(zones),
                "zones": zones
            }
            
        except Exception as e:
            logger.error(f"Zone analysis error: {str(e)}")
            return {"distribution_score": 50.0, "clustered_zones": [], "total_zones_used": 0}
    
    def _calculate_zone_clustering_score(self, signal_price: float, zone_analysis: Dict[str, Any]) -> float:
        """Calculate clustering score for signal price"""
        try:
            zone_size = self.zone_params.get("zone_size_pips", 25)
            signal_zone = int(signal_price / zone_size)
            
            zones = zone_analysis.get("zones", {})
            max_per_zone = self.zone_params.get("max_positions_per_zone", 3)
            
            if signal_zone in zones:
                positions_in_zone = len(zones[signal_zone])
                if positions_in_zone >= max_per_zone:
                    return 0.0  # Would create clustering
                else:
                    return 1.0 - (positions_in_zone / max_per_zone)
            else:
                return 1.0  # Empty zone is good
                
        except Exception:
            return 0.5
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        try:
            if not self.circuit_breaker.get("enabled", True):
                return False
            
            if not self.circuit_breaker_open:
                return False
            
            # Check if timeout has passed
            if self.circuit_breaker_last_failure:
                timeout = self.circuit_breaker.get("timeout", 300)
                if (datetime.now() - self.circuit_breaker_last_failure).seconds > timeout:
                    self.circuit_breaker_open = False
                    logger.info("Circuit breaker reset - resuming normal operation")
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _create_safe_default_decision(self, signal: Any, reason: str) -> DecisionResult:
        """Create safe default decision for error cases"""
        return DecisionResult(
            action=DecisionAction.SKIP,
            lot_size=0.0,
            confidence=0.0,
            reasoning=reason,
            safety_score=0.0,
            portfolio_score=0.0,
            zone_score=0.0,
            balance_score=0.0,
            signal_score=0.0,
            weighted_score=0.0,
            conflicts_resolved=[],
            execution_time_ms=0.0
        )
    
    def _create_decision_result(self, action: DecisionAction, lot_size: float, 
                              reasoning: str, **kwargs) -> DecisionResult:
        """Helper to create decision result"""
        return DecisionResult(
            action=action,
            lot_size=lot_size,
            reasoning=reasoning,
            **kwargs
        )
    
    def _record_decision(self, decision: DecisionResult, signal: Any, state: Dict[str, Any]):
        """Record decision for statistics and learning"""
        try:
            self.decision_history.append({
                "timestamp": datetime.now(),
                "decision": decision,
                "signal": signal,
                "state_summary": {
                    "position_count": len(state.get("positions", [])),
                    "portfolio_health": state.get("portfolio_health", 100.0),
                    "buy_volume": state.get("buy_volume", 0.0),
                    "sell_volume": state.get("sell_volume", 0.0)
                }
            })
            
            # Keep only recent decisions (last 1000)
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-1000:]
            
            # Update performance tracking
            self.performance_tracker["total_decisions"] += 1
            self.performance_tracker["execution_times"].append(decision.execution_time_ms)
            self.performance_tracker["conflicts_resolved"] += len(decision.conflicts_resolved or [])
            
        except Exception as e:
            logger.error(f"Error recording decision: {str(e)}")
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get comprehensive decision statistics"""
        try:
            total_decisions = self.performance_tracker["total_decisions"]
            execution_times = self.performance_tracker["execution_times"]
            
            if not execution_times:
                avg_execution_time = 0.0
            else:
                avg_execution_time = sum(execution_times) / len(execution_times)
            
            # Analyze recent decisions
            recent_decisions = self.decision_history[-100:] if self.decision_history else []
            action_counts = {}
            
            for record in recent_decisions:
                action = record["decision"].action.value
                action_counts[action] = action_counts.get(action, 0) + 1
            
            return {
                "total_decisions": total_decisions,
                "avg_execution_time_ms": avg_execution_time,
                "conflicts_resolved": self.performance_tracker["conflicts_resolved"],
                "recent_action_distribution": action_counts,
                "circuit_breaker_open": self.circuit_breaker_open,
                "conflict_resolver_stats": self.conflict_resolver.get_conflict_statistics(),
                "cache_performance": self.performance.get_performance_stats()
            }
            
        except Exception as e:
            logger.error(f"Error getting decision statistics: {str(e)}")
            return {}
    
    def trigger_circuit_breaker(self, reason: str):
        """Manually trigger circuit breaker"""
        self.circuit_breaker_open = True
        self.circuit_breaker_last_failure = datetime.now()
        logger.warning(f"Circuit breaker triggered: {reason}")
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_breaker_open = False
        self.circuit_breaker_last_failure = None
        logger.info("Circuit breaker manually reset")