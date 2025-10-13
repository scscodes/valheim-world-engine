#!/usr/bin/env python3
"""
Generate Adaptive Sampling Client Services
Uses VWE generators to create backend API and frontend app
"""

import sys
from pathlib import Path

# Add generators to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "global" / "generators"))

from python_generator import PythonGenerator
from typescript_generator import TypeScriptGenerator

def main():
    """Generate backend and frontend services"""
    
    print("=" * 80)
    print("Adaptive Sampling Client - Service Generation")
    print("=" * 80)
    print()
    
    # Configure output paths
    base_dir = Path(__file__).parent
    
    print("[1/2] Generating FastAPI Backend Service...")
    print()
    
    # Generate Python FastAPI backend
    python_gen = PythonGenerator(base_path=base_dir)
    python_gen.output_dir = base_dir / "backend"
    
    backend_files = python_gen.create_fastapi_service(
        service_name="VWE_WorldDataAPI",
        description="World data processing API for adaptive sampling client",
        version="1.0.0",
        author="VWE"
    )
    
    print(f"✓ Generated {len(backend_files)} backend files")
    for name, path in backend_files.items():
        print(f"  - {name}: {path}")
    print()
    
    print("[2/2] Generating Next.js Frontend Application...")
    print()
    
    # Generate TypeScript Next.js frontend
    ts_gen = TypeScriptGenerator(base_path=base_dir)
    ts_gen.output_dir = base_dir / "frontend"
    
    # Create the app/api directory structure first (generator bug workaround)
    app_api_dir = base_dir / "frontend" / "VWE_MapViewer" / "src" / "app" / "api"
    app_api_dir.mkdir(parents=True, exist_ok=True)
    
    frontend_files = ts_gen.create_nextjs_app(
        app_name="VWE_MapViewer",
        description="Interactive map viewer for Valheim world data",
        version="1.0.0",
        author="VWE"
    )
    
    print(f"✓ Generated {len(frontend_files)} frontend files")
    for name, path in frontend_files.items():
        print(f"  - {name}: {path}")
    print()
    
    print("=" * 80)
    print("✓ Service Generation Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. cd backend/VWE_WorldDataAPI && pip install -r requirements.txt")
    print("  2. cd frontend/VWE_MapViewer && npm install")
    print("  3. Review generated code and customize for world data processing")
    print()

if __name__ == "__main__":
    main()

