"""
Factory pattern for creating ISTAT converters.
Provides a centralized way to instantiate converters for different targets.
"""

try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

from .base_converter import BaseIstatConverter

logger = get_logger(__name__)


class ConverterFactory:
    """Factory for creating ISTAT data converters."""

    _converters: dict[str, type[BaseIstatConverter]] = {}

    @classmethod
    def register_converter(cls, target: str, converter_class: type[BaseIstatConverter]):
        """Register a converter class for a specific target."""
        cls._converters[target.lower()] = converter_class
        logger.info(f"Registered converter for target: {target}")

    @classmethod
    def create_converter(cls, target: str) -> BaseIstatConverter:
        """Create a converter instance for the specified target."""
        target_lower = target.lower()

        if target_lower not in cls._converters:
            # Lazy import to avoid circular dependencies
            cls._register_default_converters()

        if target_lower not in cls._converters:
            raise ValueError(f"No converter registered for target: {target}")

        converter_class = cls._converters[target_lower]
        logger.info(f"Creating converter for target: {target}")
        return converter_class()

    @classmethod
    def _register_default_converters(cls):
        """Register default converters on first use."""
        logger.info(
            "No default converters configured for MVP - use universal export formats"
        )

    @classmethod
    def get_available_targets(cls) -> list[str]:
        """Get list of available converter targets."""
        if not cls._converters:
            cls._register_default_converters()
        return list(cls._converters.keys())

    @classmethod
    def is_target_supported(cls, target: str) -> bool:
        """Check if a target is supported."""
        target_lower = target.lower()
        if target_lower not in cls._converters:
            cls._register_default_converters()
        return target_lower in cls._converters


# Convenience functions for common usage patterns
def get_converter_for_target(target: str) -> BaseIstatConverter:
    """Get converter instance for specified target."""
    return ConverterFactory.create_converter(target)
