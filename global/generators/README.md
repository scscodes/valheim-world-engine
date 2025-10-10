# VWE Code Generators

This directory contains code generators for the Valheim World Engine project. These generators create boilerplate code, project structures, and templates for different technologies used in the VWE ecosystem.

## Available Generators

### 1. C# Generator (`csharp_generator.py`)
Generates BepInEx plugin templates and project structures for Valheim modding.

**Features:**
- Complete BepInEx plugin structure
- Project files (.csproj) with proper dependencies
- Configuration files (.cfg) for BepInEx
- Build scripts and documentation
- Specialized templates for VWE plugins

**Usage:**
```python
from csharp_generator import CSharpGenerator

generator = CSharpGenerator()
files = generator.create_bepinex_plugin(
    plugin_name="VWE_MyPlugin",
    description="My custom VWE plugin",
    version="1.0.0",
    author="VWE"
)
```

**Generated Structure:**
```
VWE_MyPlugin/
├── VWE_MyPlugin.cs          # Main plugin class
├── VWE_MyPlugin.csproj      # Project file
├── VWE_MyPlugin.cfg         # Configuration template
├── build.sh                 # Build script
└── README.md                # Documentation
```

### 2. Python Generator (`python_generator.py`)
Generates FastAPI backend services and data processing components.

**Features:**
- Complete FastAPI application structure
- Service layer with dependency injection
- Pydantic models for data validation
- API routes with proper error handling
- Docker configuration and testing setup
- Specialized templates for VWE services

**Usage:**
```python
from python_generator import PythonGenerator

generator = PythonGenerator()
files = generator.create_fastapi_service(
    service_name="VWE_DataProcessor",
    description="Processes Valheim world data",
    version="1.0.0",
    author="VWE"
)
```

**Generated Structure:**
```
VWE_DataProcessor/
├── app/
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   └── config.py        # Configuration settings
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── services/            # Business logic
│   └── models/              # Data models
├── tests/                   # Test cases
├── requirements.txt         # Dependencies
├── Dockerfile              # Container config
└── README.md               # Documentation
```

### 3. TypeScript Generator (`typescript_generator.py`)
Generates Next.js frontend applications and React components.

**Features:**
- Complete Next.js 14 application with App Router
- TypeScript configuration and type definitions
- Tailwind CSS for styling
- Custom React hooks and utilities
- API client with Axios
- Testing setup with Jest and Testing Library
- Docker configuration for deployment

**Usage:**
```python
from typescript_generator import TypeScriptGenerator

generator = TypeScriptGenerator()
files = generator.create_nextjs_app(
    app_name="VWE_MapViewer",
    description="Interactive map viewer for Valheim worlds",
    version="1.0.0",
    author="VWE"
)
```

**Generated Structure:**
```
VWE_MapViewer/
├── src/
│   ├── app/                 # Next.js App Router
│   ├── components/          # React components
│   ├── hooks/              # Custom hooks
│   ├── lib/                # Library code
│   ├── types/              # TypeScript types
│   └── utils/              # Utility functions
├── public/                 # Static assets
├── styles/                 # Global styles
├── tests/                  # Test cases
├── package.json           # Dependencies
├── next.config.js         # Next.js config
├── tsconfig.json          # TypeScript config
├── Dockerfile             # Container config
└── README.md              # Documentation
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip or conda

### Installation
```bash
# Navigate to the generators directory
cd global/generators

# Install any required dependencies
pip install -r requirements.txt
```

### Basic Usage

#### Generate a BepInEx Plugin
```bash
python csharp_generator.py
```

#### Generate a FastAPI Service
```bash
python python_generator.py
```

#### Generate a Next.js Application
```bash
python typescript_generator.py
```

### Custom Generation

You can also use the generators programmatically:

```python
# C# Generator
from csharp_generator import CSharpGenerator
generator = CSharpGenerator()
files = generator.create_data_exporter_plugin("VWE_MyExporter")

# Python Generator
from python_generator import PythonGenerator
generator = PythonGenerator()
files = generator.create_data_processor("VWE_MyProcessor")

# TypeScript Generator
from typescript_generator import TypeScriptGenerator
generator = TypeScriptGenerator()
files = generator.create_map_viewer("VWE_MyViewer")
```

## Configuration

### Environment Variables
The generators respect the following environment variables:

- `VWE_GENERATOR_OUTPUT_DIR` - Output directory for generated files (default: `./output`)
- `VWE_GENERATOR_TEMPLATES_DIR` - Directory containing custom templates (default: `./templates`)

### Custom Templates
You can provide custom templates by creating a `templates/` directory structure:

```
templates/
├── csharp/
│   ├── plugin_class.template
│   ├── project_file.template
│   └── config_file.template
├── python/
│   ├── main_app.template
│   ├── service_class.template
│   └── models.template
└── typescript/
    ├── component.template
    ├── hook.template
    └── api_client.template
```

## Specialized Templates

### VWE-Specific Generators

#### C# - Data Exporter Plugin
```python
generator = CSharpGenerator()
files = generator.create_data_exporter_plugin("VWE_DataExporter")
```

#### C# - Auto Save Plugin
```python
generator = CSharpGenerator()
files = generator.create_autosave_plugin("VWE_AutoSave")
```

#### Python - Data Processor Service
```python
generator = PythonGenerator()
files = generator.create_data_processor("VWE_DataProcessor")
```

#### Python - Rendering Service
```python
generator = PythonGenerator()
files = generator.create_rendering_service("VWE_RenderingService")
```

#### TypeScript - Map Viewer
```python
generator = TypeScriptGenerator()
files = generator.create_map_viewer("VWE_MapViewer")
```

#### TypeScript - Dashboard
```python
generator = TypeScriptGenerator()
files = generator.create_dashboard("VWE_Dashboard")
```

## Generated Code Features

### C# (BepInEx Plugins)
- ✅ BepInEx 5.4.22+ compatibility
- ✅ HarmonyX integration for patching
- ✅ Configuration file generation
- ✅ Proper project file with dependencies
- ✅ Build scripts for easy compilation
- ✅ Comprehensive documentation

### Python (FastAPI Services)
- ✅ FastAPI 0.104+ with async support
- ✅ Pydantic models for data validation
- ✅ Dependency injection pattern
- ✅ Comprehensive error handling
- ✅ Docker configuration
- ✅ Test suite with pytest
- ✅ API documentation generation

### TypeScript (Next.js Applications)
- ✅ Next.js 14 with App Router
- ✅ TypeScript for type safety
- ✅ Tailwind CSS for styling
- ✅ Custom React hooks
- ✅ API client with Axios
- ✅ Testing with Jest and Testing Library
- ✅ Docker configuration
- ✅ Responsive design

## Integration with VWE

The generators are designed to work seamlessly with the Valheim World Engine project:

1. **Consistent Naming**: All generated code follows VWE naming conventions
2. **Configuration**: Generated services use VWE configuration patterns
3. **API Compatibility**: Generated APIs are compatible with VWE backend
4. **Docker Support**: All generated services include Docker configuration
5. **Testing**: Generated code includes comprehensive test suites

## Contributing

To add new generators or modify existing ones:

1. Create a new generator class following the existing patterns
2. Implement the required methods for your technology stack
3. Add specialized templates for VWE-specific use cases
4. Update this README with documentation
5. Add tests for your generator

## License

Generated code follows the same license as the Valheim World Engine project.

## Support

For issues or questions about the generators:
1. Check the generated README files for specific technology guidance
2. Review the example usage in each generator's `main()` function
3. Create an issue in the VWE project repository
