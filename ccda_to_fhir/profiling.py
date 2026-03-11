"""Performance profiling utilities for C-CDA to FHIR conversion.

This module provides decorators and context managers for profiling
conversion performance in production environments.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import ParamSpec, TypedDict, TypeVar

from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import OperationStats

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class PerformanceMetrics:
    """Collects and reports performance metrics."""

    def __init__(self) -> None:
        """Initialize performance metrics collector."""
        self.metrics: dict[str, list[float]] = {}
        self.counts: dict[str, int] = {}

    def record(self, operation: str, duration: float) -> None:
        """Record a performance measurement.

        Args:
            operation: Name of the operation being measured
            duration: Duration in seconds
        """
        if operation not in self.metrics:
            self.metrics[operation] = []
            self.counts[operation] = 0

        self.metrics[operation].append(duration)
        self.counts[operation] += 1

    def get_stats(self, operation: str) -> OperationStats:
        """Get statistics for an operation.

        Args:
            operation: Name of the operation

        Returns:
            OperationStats (zero-valued if operation not found)
        """
        if operation not in self.metrics:
            return OperationStats()

        durations = self.metrics[operation]
        return OperationStats(
            count=self.counts[operation],
            total=sum(durations),
            avg=sum(durations) / len(durations) if durations else 0,
            min=min(durations) if durations else 0,
            max=max(durations) if durations else 0,
        )

    def get_all_stats(self) -> dict[str, OperationStats]:
        """Get statistics for all operations.

        Returns:
            Dictionary mapping operation names to their statistics
        """
        return {op: self.get_stats(op) for op in self.metrics}

    def report(self) -> None:
        """Log a summary of all performance metrics."""
        logger.info("=== Performance Metrics Summary ===")
        for operation, stats in self.get_all_stats().items():
            logger.info(
                f"{operation}: {stats.count} calls, "
                f"avg={stats.avg:.3f}s, "
                f"min={stats.min:.3f}s, "
                f"max={stats.max:.3f}s, "
                f"total={stats.total:.3f}s"
            )

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.counts.clear()


# Global metrics instance
_global_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """Get the global performance metrics instance.

    Returns:
        PerformanceMetrics instance
    """
    return _global_metrics


@contextmanager
def profile_operation(operation_name: str, log_result: bool = True) -> Generator[None, None, None]:
    """Context manager for profiling an operation.

    Args:
        operation_name: Name of the operation being profiled
        log_result: Whether to log the timing result

    Yields:
        None

    Example:
        with profile_operation("convert_document"):
            result = convert_document(xml)
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        _global_metrics.record(operation_name, duration)

        if log_result:
            logger.debug(f"{operation_name} completed in {duration:.3f}s")


def profile(
    operation_name: str | None = None, log_result: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for profiling a function.

    Args:
        operation_name: Optional name for the operation (defaults to function name)
        log_result: Whether to log each function call timing

    Returns:
        Decorated function

    Example:
        @profile("convert_patient")
        def convert_patient(data):
            # conversion logic
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        op_name = operation_name or func.__name__

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with profile_operation(op_name, log_result=log_result):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class ResourceStats(TypedDict):
    """Stats for a single resource type."""

    count: int
    total_time: float
    avg_time: float


class ProfilingReport(TypedDict):
    """Profiling report structure."""

    total_time: float
    stages: dict[str, float]
    resources: dict[str, ResourceStats]


class ConversionProfiler:
    """High-level profiler for C-CDA to FHIR conversion.

    This class provides detailed profiling for document conversion,
    breaking down timing by conversion stage and resource type.
    """

    def __init__(self) -> None:
        """Initialize the conversion profiler."""
        self.stage_times: dict[str, float] = {}
        self.resource_counts: dict[str, int] = {}
        self.resource_times: dict[str, float] = {}
        self.total_time: float = 0
        self.start_time: float | None = None

    def start(self) -> None:
        """Start profiling a conversion."""
        self.start_time = time.time()
        self.stage_times.clear()
        self.resource_counts.clear()
        self.resource_times.clear()

    def record_stage(self, stage_name: str, duration: float) -> None:
        """Record timing for a conversion stage.

        Args:
            stage_name: Name of the conversion stage
            duration: Duration in seconds
        """
        self.stage_times[stage_name] = duration

    def record_resource(self, resource_type: str, duration: float) -> None:
        """Record timing for a resource conversion.

        Args:
            resource_type: Type of FHIR resource (e.g., "Patient", "Observation")
            duration: Duration in seconds
        """
        if resource_type not in self.resource_times:
            self.resource_times[resource_type] = 0
            self.resource_counts[resource_type] = 0

        self.resource_times[resource_type] += duration
        self.resource_counts[resource_type] += 1

    def finish(self) -> float:
        """Finish profiling and calculate total time.

        Returns:
            Total conversion time in seconds
        """
        if self.start_time:
            self.total_time = time.time() - self.start_time
        return self.total_time

    def get_report(self) -> ProfilingReport:
        """Get a detailed profiling report.

        Returns:
            Typed profiling report with stages and resource stats.
        """
        return ProfilingReport(
            total_time=self.total_time,
            stages=self.stage_times.copy(),
            resources={
                resource_type: ResourceStats(
                    count=self.resource_counts[resource_type],
                    total_time=self.resource_times[resource_type],
                    avg_time=(
                        self.resource_times[resource_type] / self.resource_counts[resource_type]
                        if self.resource_counts[resource_type] > 0
                        else 0
                    ),
                )
                for resource_type in self.resource_times
            },
        )

    def log_report(self) -> None:
        """Log the profiling report."""
        report = self.get_report()

        logger.info("=== Conversion Profiling Report ===")
        logger.info(f"Total time: {report['total_time']:.3f}s")

        logger.info("Stages:")
        for stage, duration in report["stages"].items():
            percent = (duration / report["total_time"]) * 100 if report["total_time"] > 0 else 0
            logger.info(f"  {stage}: {duration:.3f}s ({percent:.1f}%)")

        logger.info("Resources:")
        for resource_type, stats in report["resources"].items():
            logger.info(
                f"  {resource_type}: {stats['count']} resources, "
                f"total={stats['total_time']:.3f}s, "
                f"avg={stats['avg_time']:.4f}s"
            )
