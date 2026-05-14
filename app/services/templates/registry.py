"""Template registry for managing render templates."""

from typing import Dict

from app.core.exceptions import ValidationError
from app.services.templates.base import RenderTemplate
from app.services.templates.shorts_blur import ShortsBlurTemplate
from app.services.templates.shorts_fit import ShortsFitTemplate
from app.services.templates.square import SquareTemplate


class TemplateRegistry:
    """
    Registry for managing render templates.
    
    Provides built-in templates and supports custom template registration.
    """
    
    _templates: Dict[str, RenderTemplate] = {}
    _initialized: bool = False
    
    @classmethod
    def _initialize_builtin_templates(cls) -> None:
        """Initialize built-in template definitions."""
        if cls._initialized:
            return
        
        builtin_templates = [
            ShortsFitTemplate(),
            ShortsBlurTemplate(),
            SquareTemplate(),
        ]
        
        for template in builtin_templates:
            cls._templates[template.name] = template
        
        cls._initialized = True
    
    @classmethod
    def get(cls, name: str) -> RenderTemplate:
        """
        Get template by name.
        
        Args:
            name: Template identifier
            
        Returns:
            RenderTemplate instance
            
        Raises:
            ValidationError: If template not found
        """
        cls._initialize_builtin_templates()
        
        if name not in cls._templates:
            raise ValidationError(
                f"Template '{name}' not found. Available: {', '.join(cls.list_templates())}"
            )
        
        return cls._templates[name]
    
    @classmethod
    def register(cls, template: RenderTemplate) -> None:
        """
        Register a custom template.
        
        Args:
            template: RenderTemplate instance to register
        """
        cls._initialize_builtin_templates()
        cls._templates[template.name] = template
    
    @classmethod
    def list_templates(cls) -> list[str]:
        """
        List all available template names.
        
        Returns:
            List of template identifiers
        """
        cls._initialize_builtin_templates()
        return list(cls._templates.keys())
    
    @classmethod
    def get_all(cls) -> Dict[str, RenderTemplate]:
        """
        Get all registered templates.
        
        Returns:
            Dictionary of template name to RenderTemplate
        """
        cls._initialize_builtin_templates()
        return cls._templates.copy()
    
    @classmethod
    def get_for_format(cls, format_name: str) -> list[RenderTemplate]:
        """
        Get all templates that support a given format.
        
        Args:
            format_name: Format identifier
            
        Returns:
            List of compatible templates
        """
        cls._initialize_builtin_templates()
        return [
            template
            for template in cls._templates.values()
            if template.supports_format(format_name)
        ]
