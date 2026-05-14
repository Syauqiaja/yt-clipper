"""Base template interface for render templates."""

from abc import ABC, abstractmethod

from app.services.composition.models import CompositionPlan
from app.services.formats.models import OutputFormat


class RenderTemplate(ABC):
    """
    Base class for render templates.
    
    Templates generate composition plans and provide rendering configuration
    for specific output formats and styles.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Template identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable template description."""
        pass
    
    @abstractmethod
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """
        Generate composition plan for this template.
        
        Args:
            video_width: Source video width
            video_height: Source video height
            output_format: Target output format
            
        Returns:
            CompositionPlan instance
        """
        pass
    
    @abstractmethod
    def supports_format(self, format_name: str) -> bool:
        """
        Check if template supports given format.
        
        Args:
            format_name: Format identifier
            
        Returns:
            True if supported
        """
        pass
