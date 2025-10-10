"""
VWE Code Generators Package
Valheim World Engine code generators for C#, Python, and TypeScript
"""

from .csharp_generator import CSharpGenerator
from .python_generator import PythonGenerator
from .typescript_generator import TypeScriptGenerator
from .generator_config import (
    GeneratorConfig,
    GeneratorType,
    GeneratorRegistry,
    VWETemplateManager,
    VWECodeStyle,
    GeneratorFactory,
    load_vwe_config,
    create_vwe_factory,
    generate_bepinex_plugin,
    generate_fastapi_service,
    generate_nextjs_app
)

__version__ = "1.0.0"
__author__ = "VWE"

__all__ = [
    # Generators
    "CSharpGenerator",
    "PythonGenerator", 
    "TypeScriptGenerator",
    
    # Configuration
    "GeneratorConfig",
    "GeneratorType",
    "GeneratorRegistry",
    "VWETemplateManager",
    "VWECodeStyle",
    "GeneratorFactory",
    
    # Convenience functions
    "load_vwe_config",
    "create_vwe_factory",
    "generate_bepinex_plugin",
    "generate_fastapi_service",
    "generate_nextjs_app",
]
