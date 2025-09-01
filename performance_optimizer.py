"""
Performance Optimizer for AI Gold Grid Trading System v3.0
Smart caching, memory management, and performance monitoring
"""

import time
import threading
import logging
import gc
import psutil
import os
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
import hashlib
import pickle

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    cache_tier: str = "cold"  # hot, warm, cold
    expires_at: Optional[datetime] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    cache_hits: int = 0
    cache_misses: int = 0
    avg_access_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_operations: int = 0
    total_operations: int = 0
    error_count: int = 0
    last_cleanup: datetime = field(default_factory=datetime.now)

class PerformanceOptimizer:
    """Smart caching and performance optimization system"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_lock = threading.RLock()
        
        # Performance settings
        self.settings = config_manager.get_performance_settings()
        self.max_cache_size = self.settings.get("max_cache_size", 1000)
        self.hot_threshold = self.settings.get("cache_hot_threshold", 10)
        self.warm_threshold = self.settings.get("cache_warm_threshold", 60)
        self.cleanup_interval = self.settings.get("cleanup_interval", 300)
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.operation_times: List[float] = []
        self.background_tasks: Dict[str, threading.Thread] = {}
        
        # Tiered cache sizes
        self.tier_limits = {
            "hot": int(self.max_cache_size * 0.3),   # 30% for hot data
            "warm": int(self.max_cache_size * 0.5),  # 50% for warm data
            "cold": int(self.max_cache_size * 0.2),  # 20% for cold data
        }
        
        # Memory monitoring
        self.memory_threshold_mb = 100  # Alert threshold
        self.memory_critical_mb = 200   # Critical threshold
        
        # Start background monitoring
        self._start_background_monitor()
        self._start_cleanup_scheduler()
        
        logger.info("PerformanceOptimizer initialized with smart caching")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with smart tier management"""
        start_time = time.time()
        
        try:
            with self.cache_lock:
                if key in self.cache:
                    entry = self.cache[key]
                    
                    # Check expiration
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        del self.cache[key]
                        self.metrics.cache_misses += 1
                        return default
                    
                    # Update access patterns
                    entry.last_accessed = datetime.now()
                    entry.access_count += 1
                    
                    # Update cache tier based on access patterns
                    self._update_cache_tier(entry)
                    
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    
                    self.metrics.cache_hits += 1
                    
                    access_time = time.time() - start_time
                    self._update_access_time(access_time)
                    
                    return entry.value
                else:
                    self.metrics.cache_misses += 1
                    return default
                    
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            self.metrics.error_count += 1
            return default
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            force_tier: Optional[str] = None) -> bool:
        """Set value in cache with smart tier assignment"""
        try:
            with self.cache_lock:
                now = datetime.now()
                expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None
                
                # Calculate size estimate
                size_bytes = self._estimate_size(value)
                
                # Determine cache tier
                cache_tier = force_tier or self._determine_initial_tier(key, value)
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=now,
                    last_accessed=now,
                    access_count=1,
                    size_bytes=size_bytes,
                    cache_tier=cache_tier,
                    expires_at=expires_at
                )
                
                # Check if we need to evict entries
                if len(self.cache) >= self.max_cache_size:
                    self._evict_entries()
                
                # Add to cache
                self.cache[key] = entry
                
                logger.debug(f"Cached {key} in {cache_tier} tier ({size_bytes} bytes)")
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            self.metrics.error_count += 1
            return False
    
    def invalidate(self, key: str) -> bool:
        """Remove specific key from cache"""
        try:
            with self.cache_lock:
                if key in self.cache:
                    del self.cache[key]
                    logger.debug(f"Invalidated cache key: {key}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Cache invalidation error for key {key}: {str(e)}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Remove all keys matching pattern"""
        try:
            invalidated = 0
            with self.cache_lock:
                keys_to_remove = [key for key in self.cache.keys() if pattern in key]
                for key in keys_to_remove:
                    del self.cache[key]
                    invalidated += 1
            
            logger.debug(f"Invalidated {invalidated} cache keys matching pattern: {pattern}")
            return invalidated
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {str(e)}")
            return 0
    
    def cache_function(self, ttl_seconds: int = 300, key_prefix: str = "func"):
        """Decorator for function result caching"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                cache_key = self._create_function_cache_key(func, args, kwargs, key_prefix)
                
                # Try to get from cache first
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Cache the result
                    self.set(cache_key, result, ttl_seconds)
                    
                    # Track performance
                    self._track_operation_time(execution_time)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Function execution error {func.__name__}: {str(e)}")
                    raise
                    
            return wrapper
        return decorator
    
    def background_task(self, task_name: str, target_function: Callable, 
                       args: Tuple = (), interval: int = 60) -> bool:
        """Schedule background task for non-critical operations"""
        try:
            if task_name in self.background_tasks:
                logger.warning(f"Background task {task_name} already exists")
                return False
            
            def task_runner():
                while True:
                    try:
                        target_function(*args)
                        time.sleep(interval)
                    except Exception as e:
                        logger.error(f"Background task {task_name} error: {str(e)}")
                        time.sleep(interval)  # Continue running even on error
            
            thread = threading.Thread(target=task_runner, daemon=True, name=task_name)
            thread.start()
            
            self.background_tasks[task_name] = thread
            logger.info(f"Started background task: {task_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting background task {task_name}: {str(e)}")
            return False
    
    def _update_cache_tier(self, entry: CacheEntry):
        """Update cache tier based on access patterns"""
        try:
            age_minutes = (datetime.now() - entry.created_at).seconds / 60
            access_frequency = entry.access_count / max(age_minutes, 1)
            
            if access_frequency >= self.hot_threshold:
                entry.cache_tier = "hot"
            elif access_frequency >= self.warm_threshold / 60:  # Convert to per-minute
                entry.cache_tier = "warm"
            else:
                entry.cache_tier = "cold"
                
        except Exception as e:
            logger.error(f"Error updating cache tier: {str(e)}")
    
    def _determine_initial_tier(self, key: str, value: Any) -> str:
        """Determine initial cache tier for new entries"""
        try:
            # Zone analysis is frequently accessed
            if "zone_analysis" in key:
                return "warm"
            
            # Position data is hot
            if "position" in key or "balance" in key:
                return "hot"
            
            # Configuration is warm
            if "config" in key:
                return "warm"
            
            # Default to cold
            return "cold"
            
        except:
            return "cold"
    
    def _evict_entries(self):
        """Evict cache entries using intelligent LRU + tier strategy"""
        try:
            entries_by_tier = defaultdict(list)
            
            # Group entries by tier
            for key, entry in self.cache.items():
                entries_by_tier[entry.cache_tier].append((key, entry))
            
            # Evict from cold tier first, then warm, then hot
            for tier in ["cold", "warm", "hot"]:
                tier_entries = entries_by_tier[tier]
                if tier_entries:
                    # Sort by last accessed time (oldest first)
                    tier_entries.sort(key=lambda x: x[1].last_accessed)
                    
                    # Remove oldest entry from this tier
                    key_to_remove = tier_entries[0][0]
                    del self.cache[key_to_remove]
                    logger.debug(f"Evicted cache entry: {key_to_remove} from {tier} tier")
                    return
            
        except Exception as e:
            logger.error(f"Cache eviction error: {str(e)}")
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of cached value"""
        try:
            return len(pickle.dumps(value))
        except:
            # Fallback estimation
            if isinstance(value, str):
                return len(value) * 2  # Unicode overhead
            elif isinstance(value, (list, tuple)):
                return len(value) * 8  # Pointer overhead
            elif isinstance(value, dict):
                return len(value) * 16  # Key-value overhead
            else:
                return 64  # Default estimate
    
    def _create_function_cache_key(self, func: Callable, args: Tuple, 
                                  kwargs: Dict[str, Any], prefix: str) -> str:
        """Create cache key for function calls"""
        try:
            # Create hash from function name and arguments
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
            return f"{prefix}:{func.__name__}:{key_hash}"
        except:
            # Fallback to simple key
            return f"{prefix}:{func.__name__}:{time.time()}"
    
    def _track_operation_time(self, execution_time: float):
        """Track operation execution times"""
        try:
            self.operation_times.append(execution_time)
            
            # Keep only recent times (last 1000 operations)
            if len(self.operation_times) > 1000:
                self.operation_times = self.operation_times[-1000:]
            
            # Update average
            if self.operation_times:
                self.metrics.avg_access_time = sum(self.operation_times) / len(self.operation_times)
                
        except Exception as e:
            logger.error(f"Error tracking operation time: {str(e)}")
    
    def _update_access_time(self, access_time: float):
        """Update average access time"""
        try:
            # Simple moving average
            alpha = 0.1  # Smoothing factor
            self.metrics.avg_access_time = (
                alpha * access_time + 
                (1 - alpha) * self.metrics.avg_access_time
            )
        except:
            self.metrics.avg_access_time = access_time
    
    def _start_background_monitor(self):
        """Start background performance monitoring"""
        def monitor():
            while True:
                try:
                    # Update memory usage
                    process = psutil.Process(os.getpid())
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    self.metrics.memory_usage_mb = memory_mb
                    
                    # Update CPU usage
                    self.metrics.cpu_usage_percent = process.cpu_percent()
                    
                    # Check memory thresholds
                    if memory_mb > self.memory_critical_mb:
                        logger.warning(f"Critical memory usage: {memory_mb:.1f}MB")
                        self._emergency_cleanup()
                    elif memory_mb > self.memory_threshold_mb:
                        logger.warning(f"High memory usage: {memory_mb:.1f}MB")
                    
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Performance monitor error: {str(e)}")
                    time.sleep(60)  # Longer sleep on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True, name="performance_monitor")
        monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def _start_cleanup_scheduler(self):
        """Start scheduled cache cleanup"""
        def cleanup_scheduler():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self.cleanup_cache()
                except Exception as e:
                    logger.error(f"Cleanup scheduler error: {str(e)}")
        
        cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True, name="cache_cleanup")
        cleanup_thread.start()
        logger.info("Cache cleanup scheduler started")
    
    def cleanup_cache(self):
        """Perform cache cleanup and garbage collection"""
        try:
            with self.cache_lock:
                now = datetime.now()
                removed_count = 0
                
                # Remove expired entries
                keys_to_remove = []
                for key, entry in self.cache.items():
                    if entry.expires_at and now > entry.expires_at:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.cache[key]
                    removed_count += 1
                
                # Cleanup old cold entries (older than 1 hour)
                hour_ago = now - timedelta(hours=1)
                cold_keys_to_remove = []
                for key, entry in self.cache.items():
                    if (entry.cache_tier == "cold" and 
                        entry.last_accessed < hour_ago and 
                        entry.access_count <= 1):
                        cold_keys_to_remove.append(key)
                
                # Remove up to 10% of old cold entries
                max_cold_removals = max(1, len(cold_keys_to_remove) // 10)
                for key in cold_keys_to_remove[:max_cold_removals]:
                    del self.cache[key]
                    removed_count += 1
                
                self.metrics.last_cleanup = now
                
                if removed_count > 0:
                    logger.info(f"Cache cleanup removed {removed_count} entries")
                
                # Force garbage collection
                gc.collect()
                
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")
    
    def _emergency_cleanup(self):
        """Emergency memory cleanup when usage is critical"""
        try:
            logger.warning("Performing emergency memory cleanup")
            
            with self.cache_lock:
                # Remove 50% of cold entries
                cold_entries = [(k, v) for k, v in self.cache.items() if v.cache_tier == "cold"]
                cold_entries.sort(key=lambda x: x[1].last_accessed)
                
                removal_count = len(cold_entries) // 2
                for key, _ in cold_entries[:removal_count]:
                    del self.cache[key]
                
                logger.warning(f"Emergency cleanup removed {removal_count} cold entries")
            
            # Force aggressive garbage collection
            gc.collect()
            
        except Exception as e:
            logger.error(f"Emergency cleanup error: {str(e)}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            with self.cache_lock:
                cache_size = len(self.cache)
                
                # Calculate tier distribution
                tier_counts = defaultdict(int)
                tier_sizes = defaultdict(int)
                total_size = 0
                
                for entry in self.cache.values():
                    tier_counts[entry.cache_tier] += 1
                    tier_sizes[entry.cache_tier] += entry.size_bytes
                    total_size += entry.size_bytes
                
                # Calculate hit rate
                total_requests = self.metrics.cache_hits + self.metrics.cache_misses
                hit_rate = (self.metrics.cache_hits / total_requests * 100) if total_requests > 0 else 0.0
                
                return {
                    "cache_stats": {
                        "total_entries": cache_size,
                        "total_size_mb": total_size / 1024 / 1024,
                        "hit_rate_percent": hit_rate,
                        "hits": self.metrics.cache_hits,
                        "misses": self.metrics.cache_misses,
                        "tier_distribution": dict(tier_counts),
                        "tier_sizes_mb": {k: v / 1024 / 1024 for k, v in tier_sizes.items()}
                    },
                    "performance": {
                        "avg_access_time_ms": self.metrics.avg_access_time * 1000,
                        "memory_usage_mb": self.metrics.memory_usage_mb,
                        "cpu_usage_percent": self.metrics.cpu_usage_percent,
                        "active_operations": self.metrics.active_operations,
                        "total_operations": self.metrics.total_operations,
                        "error_count": self.metrics.error_count
                    },
                    "background_tasks": {
                        "active_tasks": len(self.background_tasks),
                        "task_names": list(self.background_tasks.keys())
                    },
                    "last_cleanup": self.metrics.last_cleanup.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting performance stats: {str(e)}")
            return {}
    
    def optimize_for_trading_session(self):
        """Optimize cache and performance for active trading session"""
        try:
            logger.info("Optimizing for trading session")
            
            # Increase hot tier allocation
            self.tier_limits["hot"] = int(self.max_cache_size * 0.5)  # 50% for hot
            self.tier_limits["warm"] = int(self.max_cache_size * 0.4)  # 40% for warm
            self.tier_limits["cold"] = int(self.max_cache_size * 0.1)  # 10% for cold
            
            # More aggressive cleanup
            self.cleanup_interval = 120  # 2 minutes
            
            # Pre-warm critical caches if possible
            # This could be expanded to pre-load common zone analysis etc.
            
            logger.info("Trading session optimization complete")
            
        except Exception as e:
            logger.error(f"Trading session optimization error: {str(e)}")
    
    def shutdown(self):
        """Clean shutdown of performance optimizer"""
        try:
            logger.info("Shutting down PerformanceOptimizer")
            
            # Stop background tasks
            # Note: daemon threads will stop automatically
            
            # Final cleanup
            self.cleanup_cache()
            
            # Clear cache
            with self.cache_lock:
                self.cache.clear()
            
            logger.info("PerformanceOptimizer shutdown complete")
            
        except Exception as e:
            logger.error(f"PerformanceOptimizer shutdown error: {str(e)}")