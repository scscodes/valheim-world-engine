#!/usr/bin/env python3
"""
Example usage of VWE Code Generators
Demonstrates how to use the generators to create VWE components
"""

import os
import sys
from pathlib import Path

# Add the generators directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from generator_config import create_vwe_factory, GeneratorConfig


def main():
    """Demonstrate VWE code generators"""
    print("VWE Code Generators - Example Usage")
    print("=" * 50)
    
    # Create VWE factory with configuration
    factory = create_vwe_factory()
    
    # Example 1: Generate a BepInEx data exporter plugin
    print("\n1. Generating BepInEx Data Exporter Plugin...")
    csharp_gen = factory.create_csharp_generator()
    files = csharp_gen.create_data_exporter_plugin("VWE_DataExporter")
    print(f"   Generated {len(files)} files:")
    for file_type, file_path in files.items():
        print(f"   - {file_type}: {file_path}")
    
    # Example 2: Generate a FastAPI data processor service
    print("\n2. Generating FastAPI Data Processor Service...")
    python_gen = factory.create_python_generator()
    files = python_gen.create_data_processor("VWE_DataProcessor")
    print(f"   Generated {len(files)} files:")
    for file_type, file_path in files.items():
        print(f"   - {file_type}: {file_path}")
    
    # Example 3: Generate a Next.js map viewer application
    print("\n3. Generating Next.js Map Viewer Application...")
    ts_gen = factory.create_typescript_generator()
    files = ts_gen.create_map_viewer("VWE_MapViewer")
    print(f"   Generated {len(files)} files:")
    for file_type, file_path in files.items():
        print(f"   - {file_type}: {file_path}")
    
    # Example 4: Generate a custom BepInEx plugin
    print("\n4. Generating Custom BepInEx Plugin...")
    files = csharp_gen.create_bepinex_plugin(
        plugin_name="VWE_CustomPlugin",
        description="A custom VWE plugin for specific functionality",
        version="2.0.0",
        author="VWE Team"
    )
    print(f"   Generated {len(files)} files:")
    for file_type, file_path in files.items():
        print(f"   - {file_type}: {file_path}")
    
    # Example 5: Generate a custom FastAPI service
    print("\n5. Generating Custom FastAPI Service...")
    files = python_gen.create_fastapi_service(
        service_name="VWE_CustomService",
        description="A custom VWE service for specialized processing",
        version="2.0.0",
        author="VWE Team"
    )
    print(f"   Generated {len(files)} files:")
    for file_type, file_path in files.items():
        print(f"   - {file_type}: {file_path}")
    
    # Example 6: Generate a custom Next.js application
    print("\n6. Generating Custom Next.js Application...")
    files = ts_gen.create_nextjs_app(
        app_name="VWE_CustomApp",
        description="A custom VWE application for specialized functionality",
        version="2.0.0",
        author="VWE Team"
    )
    print(f"   Generated {len(files)} files:")
    for file_type, file_path in files.items():
        print(f"   - {file_type}: {file_path}")
    
    print("\n" + "=" * 50)
    print("VWE Code Generators example complete!")
    print("\nGenerated files are located in the 'output' directory.")
    print("You can now:")
    print("- Build and test the generated code")
    print("- Customize the generated templates")
    print("- Integrate with your VWE project")
    print("\nFor more information, see README.md")


if __name__ == "__main__":
    main()
