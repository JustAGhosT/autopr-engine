"""
Performance Optimization Module for AI Enhanced File Splitter

This module provides advanced performance optimizations including:
- Intelligent caching with TTL and LRU eviction
- Parallel processing for large files
- Memory-mapped file processing
- Performance profiling and monitoring
- Resource usage optimization
"""

from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
import functools
import gc
import hashlib
import logging
import mmap
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Any

import psutil


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata for intelligent eviction."""

    value: Any
    timestamp: float
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: int = 3600  # 1 hour default


class IntelligentCache:
    """Advanced caching system with TTL, LRU, and size-based eviction."""

    def __init__(
        self,
        max_size_mb: int = 100,
        max_entries: int = 1000,
        default_ttl_seconds: int = 3600,
        enable_compression: bool = True,
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.default_ttl_seconds = default_ttl_seconds
        self.enable_compression = enable_compression

        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size_bytes = 0
        self.lock = threading.RLock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a deterministic cache key."""
        key_parts = []

        for arg in args:
            if isinstance(arg, str | int | float | bool):
                key_parts.append(str(arg))
            elif isinstance(arg, Path):
                key_parts.append(str(arg.absolute()))
            else:
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}={value}")

        return hashlib.md5(":".join(key_parts).encode()).hexdigest()

    def _estimate_size(self, value: Any) -> int:
        """Estimate the size of a value in bytes."""
        try:
            if isinstance(value, str):
                return len(value.encode("utf-8"))
            elif isinstance(value, bytes):
                return len(value)
            elif isinstance(value, list | tuple):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v)
                    for k, v in value.items()
                )
            else:
                return len(str(value).encode("utf-8"))
        except Exception:
            return 1024  # Default estimate

    def _evict_if_needed(self) -> None:
        """Evict entries if cache is full."""
        while (
            len(self.cache) > self.max_entries
            or self.current_size_bytes > self.max_size_bytes
        ):
            # Remove oldest entry
            if self.cache:
                key, entry = self.cache.popitem(last=False)
                self.current_size_bytes -= entry.size_bytes
                self.evictions += 1
                logger.debug(f"Evicted cache entry: {key}")

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self.cache.items()
            if current_time - entry.timestamp > entry.ttl_seconds
        ]

        for key in expired_keys:
            entry = self.cache.pop(key)
            self.current_size_bytes -= entry.size_bytes
            logger.debug(f"Removed expired cache entry: {key}")

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        with self.lock:
            self._cleanup_expired()

            if key in self.cache:
                entry = self.cache[key]
                entry.access_count += 1
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return entry.value

            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Set a value in cache."""
        with self.lock:
            self._cleanup_expired()

            size_bytes = self._estimate_size(value)
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                size_bytes=size_bytes,
                ttl_seconds=ttl_seconds or self.default_ttl_seconds,
            )

            # Remove existing entry if present
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_size_bytes -= old_entry.size_bytes

            self.cache[key] = entry
            self.current_size_bytes += size_bytes

            self._evict_if_needed()

    def invalidate(self, pattern: str) -> int:
        """Invalidate entries matching a pattern."""
        with self.lock:
            keys_to_remove = [key for key in self.cache if pattern in key]

            for key in keys_to_remove:
                entry = self.cache.pop(key)
                self.current_size_bytes -= entry.size_bytes

            return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.current_size_bytes = 0
            logger.debug("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0

            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "evictions": self.evictions,
                "current_entries": len(self.cache),
                "current_size_mb": self.current_size_bytes / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "max_entries": self.max_entries,
            }


@dataclass
class PerformanceProfile:
    """Performance profile for optimization decisions."""

    file_size_bytes: int
    complexity_score: float
    processing_time_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float
    parallel_efficiency: float = 1.0


class MemoryMappedFileProcessor:
    """Process large files using memory mapping for efficiency."""

    def __init__(self, chunk_size_mb: int = 10):
        self.chunk_size = chunk_size_mb * 1024 * 1024

    def process_large_file(
        self, file_path: Path, processor_func: Callable[[bytes], Any]
    ) -> list[Any]:
        """Process a large file in chunks using memory mapping."""
        results = []

        try:
            with open(file_path, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    offset = 0
                    while offset < len(mm):
                        # Read chunk
                        chunk_end = min(offset + self.chunk_size, len(mm))
                        chunk = mm[offset:chunk_end]

                        # Process chunk
                        result = processor_func(chunk)
                        if result:
                            results.append(result)

                        offset = chunk_end

                        # Yield control to prevent blocking
                        if offset % (self.chunk_size * 4) == 0:
                            time.sleep(0.001)

        except Exception as e:
            logger.exception(f"Error processing large file {file_path}: {e}")
            raise

        return results


class ParallelProcessor:
    """Parallel processing utilities for file splitting operations."""

    def __init__(self, max_workers: int | None = None, use_process_pool: bool = False):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.use_process_pool = use_process_pool
        self.executor_class = (
            ProcessPoolExecutor if use_process_pool else ThreadPoolExecutor
        )

    def process_files_parallel(
        self,
        files: list[tuple[Path, str]],
        processor_func: Callable[[Path, str], Any],
        chunk_size: int = 10,
    ) -> list[Any]:
        """Process multiple files in parallel."""
        results = []

        with self.executor_class(max_workers=self.max_workers) as executor:
            # Submit tasks
            future_to_file = {
                executor.submit(processor_func, file_path, content): file_path
                for file_path, content in files
            }

            # Collect results
            for future in future_to_file:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    results.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    logger.exception(f"Error processing {file_path}: {e}")
                    results.append(None)

        return results

    def process_file_chunks_parallel(
        self,
        file_path: Path,
        content: str,
        chunk_processor: Callable[[str], Any],
        chunk_size: int = 1000,
    ) -> list[Any]:
        """Process a single file in parallel chunks."""
        lines = content.splitlines()
        chunks = [
            "\n".join(lines[i : i + chunk_size])
            for i in range(0, len(lines), chunk_size)
        ]

        with self.executor_class(max_workers=self.max_workers) as executor:
            futures = [executor.submit(chunk_processor, chunk) for chunk in chunks]

            results = []
            for future in futures:
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    logger.exception(f"Error processing chunk: {e}")
                    results.append(None)

        return results

    def process_parallel(
        self,
        items: list[Any],
        processor_func: Callable[[Any], Any],
        chunk_size: int = 10,
    ) -> list[Any]:
        """Process items in parallel using the specified processor function."""
        results = []

        with self.executor_class(max_workers=self.max_workers) as executor:
            # Submit tasks
            futures = [executor.submit(processor_func, item) for item in items]

            # Collect results
            for future in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    results.append(result)
                except Exception as e:
                    logger.exception(f"Error processing item: {e}")
                    results.append(None)

        return results


class PerformanceOptimizer:
    """Main performance optimization orchestrator."""

    def __init__(
        self,
        cache_size_mb: int = 100,
        max_workers: int | None = None,
        enable_memory_mapping: bool = True,
        enable_parallel_processing: bool = True,
    ):
        self.cache = IntelligentCache(max_size_mb=cache_size_mb)
        self.parallel_processor = ParallelProcessor(max_workers=max_workers)
        self.memory_mapper = MemoryMappedFileProcessor()

        self.enable_memory_mapping = enable_memory_mapping
        self.enable_parallel_processing = enable_parallel_processing

        # Performance tracking
        self.profiles: list[PerformanceProfile] = []
        self.session_start = time.time()

        # Add cache_manager attribute for compatibility with tests
        self.cache_manager = self.cache

    def optimize_file_processing(
        self, file_path: Path, content: str, processor_func: Callable[[Path, str], Any]
    ) -> Any:
        """Optimize file processing based on file characteristics."""
        file_size = len(content.encode("utf-8"))

        # Determine optimal processing strategy
        if file_size > 10 * 1024 * 1024:  # > 10MB
            return self._process_large_file(file_path, content, processor_func)
        elif file_size > 1024 * 1024:  # > 1MB
            return self._process_medium_file(file_path, content, processor_func)
        else:
            return self._process_small_file(file_path, content, processor_func)

    def _process_small_file(
        self, file_path: Path, content: str, processor_func: Callable[[Path, str], Any]
    ) -> Any:
        """Process small files with caching."""
        # Generate collision-resistant cache key using SHA-256 hash of entire content
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        content_length = len(content)
        cache_key = self.cache._generate_key(
            str(file_path), content_hash, content_length
        )

        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Process and cache
        start_time = time.time()
        result = processor_func(file_path, content)
        processing_time = time.time() - start_time

        # Cache result
        self.cache.set(cache_key, result, ttl_seconds=1800)  # 30 minutes

        # Record profile
        self._record_profile(file_path, len(content), 0, processing_time)

        return result

    def _process_medium_file(
        self, file_path: Path, content: str, processor_func: Callable[[Path, str], Any]
    ) -> Any:
        """Process medium files with parallel chunking."""
        if not self.enable_parallel_processing:
            return self._process_small_file(file_path, content, processor_func)

        start_time = time.time()

        # Process in parallel chunks
        def chunk_processor(chunk: str) -> Any:
            # Create secure unique temp file using NamedTemporaryFile
            temp_file = tempfile.NamedTemporaryFile(
                mode="w+", suffix=".chunk", delete=False, encoding="utf-8"
            )
            temp_path = Path(temp_file.name)
            try:
                temp_file.write(chunk)
                temp_file.flush()
                temp_file.close()
                return processor_func(temp_path, chunk)
            finally:
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove temp chunk file {temp_path}: {e}")

        results = self.parallel_processor.process_file_chunks_parallel(
            file_path, content, chunk_processor, chunk_size=500
        )

        processing_time = time.time() - start_time

        # Combine results
        combined_result = self._combine_chunk_results(results)

        # Record profile
        self._record_profile(file_path, len(content), 0, processing_time)

        return combined_result

    def _process_large_file(
        self, file_path: Path, content: str, processor_func: Callable[[Path, str], Any]
    ) -> Any:
        """Process large files with memory mapping."""
        if not self.enable_memory_mapping:
            return self._process_medium_file(file_path, content, processor_func)

        start_time = time.time()
        temp_path = None

        # Write content to a unique temp file for memory mapping
        temp_file = tempfile.NamedTemporaryFile(
            mode="w+", suffix=".mmap", delete=False, encoding="utf-8"
        )
        try:
            temp_file.write(content)
            temp_file.flush()
            temp_file.close()
            temp_path = Path(temp_file.name)

            def memory_mapped_processor(chunk: bytes) -> Any:
                chunk_str = chunk.decode("utf-8", errors="ignore")
                return processor_func(temp_path, chunk_str)

            results = self.memory_mapper.process_large_file(
                temp_path, memory_mapped_processor
            )

        finally:
            try:
                if temp_path is not None and temp_path.exists():
                    temp_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove mmap temp file {temp_path}: {e}")

        processing_time = time.time() - start_time

        # Combine results
        combined_result = self._combine_chunk_results(results)

        # Record profile
        self._record_profile(file_path, len(content), 0, processing_time)

        return combined_result

    def _combine_chunk_results(self, results: list[Any]) -> Any:
        """Combine results from parallel processing."""
        # Filter out None results
        valid_results = [r for r in results if r is not None]

        if not valid_results:
            return None

        # If all results are the same type, combine them
        if all(isinstance(r, dict) for r in valid_results):
            combined = {}
            for result in valid_results:
                combined.update(result)
            return combined
        elif all(isinstance(r, list) for r in valid_results):
            return [item for result in valid_results for item in result]
        else:
            # Return the first valid result
            return valid_results[0]

    def _record_profile(
        self,
        file_path: Path,
        file_size_bytes: int,
        complexity_score: float,
        processing_time_seconds: float,
    ) -> None:
        """Record performance profile for optimization."""
        memory_usage = psutil.Process().memory_info().rss / (1024 * 1024)
        cpu_usage = psutil.Process().cpu_percent()
        cache_stats = self.cache.get_stats()

        profile = PerformanceProfile(
            file_size_bytes=file_size_bytes,
            complexity_score=complexity_score,
            processing_time_seconds=processing_time_seconds,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            cache_hit_rate=cache_stats.get("hit_rate", 0.0),
        )

        self.profiles.append(profile)

    def get_optimization_recommendations(self) -> dict[str, Any]:
        """Get optimization recommendations based on performance profiles."""
        if not self.profiles:
            return {"message": "No performance data available"}

        avg_processing_time = sum(
            p.processing_time_seconds for p in self.profiles
        ) / len(self.profiles)
        avg_file_size = sum(p.file_size_bytes for p in self.profiles) / len(
            self.profiles
        )
        avg_cache_hit_rate = sum(p.cache_hit_rate for p in self.profiles) / len(
            self.profiles
        )

        suggestions: list[str] = []
        recommendations = {
            "average_processing_time_seconds": avg_processing_time,
            "average_file_size_mb": avg_file_size / (1024 * 1024),
            "average_cache_hit_rate": avg_cache_hit_rate,
            "total_files_processed": len(self.profiles),
            "session_duration_seconds": time.time() - self.session_start,
            "suggestions": suggestions,
        }

        # Generate recommendations
        if avg_processing_time > 5.0:
            suggestions.append(
                "Consider enabling parallel processing for faster file handling"
            )

        if avg_file_size > 5 * 1024 * 1024:  # > 5MB
            suggestions.append(
                "Large files detected - enable memory mapping for better performance"
            )

        if avg_cache_hit_rate < 0.3:
            suggestions.append(
                "Low cache hit rate - consider increasing cache size or TTL"
            )

        return recommendations

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics including CPU usage."""
        current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        current_cpu = psutil.Process().cpu_percent()
        cache_stats = self.cache.get_stats()

        return {
            "cpu_usage": current_cpu,
            "memory_usage_mb": current_memory,
            "cache_stats": cache_stats,
            "profiles_count": len(self.profiles),
            "session_duration_seconds": time.time() - self.session_start,
        }

    def cleanup(self) -> None:
        """Cleanup resources and perform final optimizations."""
        # Clear cache
        self.cache.clear()

        # Optimize memory usage
        self.optimize_memory_usage()

        # Clear performance profiles
        self.profiles.clear()

        logger.info("Performance optimizer cleanup completed")

    def optimize_memory_usage(self) -> None:
        """Optimize memory usage by garbage collection and cache cleanup."""
        # Force garbage collection
        gc.collect()

        # Clean up expired cache entries
        self.cache._cleanup_expired()

        # Log memory usage
        memory_usage = psutil.Process().memory_info().rss / (1024 * 1024)
        logger.info(f"Memory usage after optimization: {memory_usage:.2f} MB")


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


def optimize_performance(func: Callable) -> Callable:
    """Decorator to automatically optimize function performance."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we have file path and content in arguments
        file_path = None
        content = None

        for arg in args:
            if isinstance(arg, Path):
                file_path = arg
            elif isinstance(arg, str) and len(arg) > 100:
                content = arg

        for value in kwargs.values():
            if isinstance(value, Path):
                file_path = value
            elif isinstance(value, str) and len(value) > 100:
                content = value

        if file_path and content:
            # Use optimized processing
            return performance_optimizer.optimize_file_processing(
                file_path, content, func
            )
        else:
            # Fall back to normal processing
            return func(*args, **kwargs)

    return wrapper
