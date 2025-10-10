#!/usr/bin/env python3
"""
C# Generator for Valheim World Engine
Generates BepInEx plugin templates and project structures
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add global logging to path
sys.path.append(str(Path(__file__).parent.parent / "logging"))
from generator_logging import GeneratorLogManager


class CSharpGenerator:
    """Generator for C# BepInEx plugins and project structures"""
    
    # Standardized VWE plugin versions - DO NOT MODIFY WITHOUT UPDATING ALL PLUGINS
    VWE_STANDARD_VERSIONS = {
        "BepInEx": "5.4.22",
        "HarmonyX": "2.10.1", 
        "Valheim": "0.217.46",
        "UnityEngine.CoreModule": "5.6.3",
        "UnityEngine.PhysicsModule": "5.6.3",
        "UnityEngine.TextRenderingModule": "5.6.3",
        "UnityEngine.UI": "1.0.0",
        "Newtonsoft.Json": "13.0.3"
    }
    
    def __init__(self, base_path: str = ".", override_versions: Optional[Dict[str, str]] = None):
        self.base_path = Path(base_path)
        self.templates_dir = self.base_path / "templates" / "csharp"
        self.output_dir = self.base_path / "output" / "csharp"
        
        # Setup enhanced logging
        self.log_manager = GeneratorLogManager("csharp-generator")
        self.logger = self.log_manager.logger
        
        # Handle version overrides with clear logging
        self.versions = self.VWE_STANDARD_VERSIONS.copy()
        if override_versions:
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  VERSION OVERRIDES DETECTED - NON-STANDARD CONFIGURATION")
            self.logger.warning("=" * 60)
            for package, version in override_versions.items():
                if package in self.versions:
                    old_version = self.versions[package]
                    self.versions[package] = version
                    self.logger.warning(f"OVERRIDE: {package} {old_version} → {version}")
                else:
                    self.versions[package] = version
                    self.logger.warning(f"ADDED: {package} {version}")
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  USING OVERRIDDEN VERSIONS - MAY CAUSE COMPATIBILITY ISSUES")
            self.logger.warning("=" * 60)
        
    def create_bepinex_plugin(self, plugin_name: str, description: str = "", 
                            version: str = "1.0.0", author: str = "VWE") -> Dict[str, str]:
        """Generate a complete BepInEx plugin structure"""
        
        operation_id = f"create-plugin-{plugin_name}-{int(datetime.utcnow().timestamp())}"
        
        # Start operation tracking
        self.log_manager.start_operation(operation_id, "create_bepinex_plugin", {
            "plugin_name": plugin_name,
            "description": description,
            "author": author,
            "version": version
        })
        
        try:
            self.logger.info(f"Creating BepInEx plugin: {plugin_name} v{version}")
            self.logger.info(f"Using VWE standardized dependency versions")
            
            # Create plugin directory structure
            plugin_dir = self.output_dir / plugin_name
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            self.log_manager.update_progress(operation_id, 10, "Created plugin directory")
        
            # Generate files
            files_created = {}
            
            # 1. Main plugin class
            plugin_class = self._generate_plugin_class(plugin_name, description, version, author)
            plugin_file = plugin_dir / f"{plugin_name}.cs"
            plugin_file.write_text(plugin_class)
            files_created["plugin_class"] = str(plugin_file)
            self.log_manager.update_progress(operation_id, 30, "Generated plugin class")
            
            # 2. Project file
            project_content = self._generate_project_file(plugin_name, version)
            project_file = plugin_dir / f"{plugin_name}.csproj"
            project_file.write_text(project_content)
            files_created["project_file"] = str(project_file)
            self.log_manager.update_progress(operation_id, 50, "Generated project file")
            
            # 3. Configuration file
            config_content = self._generate_config_file(plugin_name)
            config_file = plugin_dir / f"{plugin_name}.cfg"
            config_file.write_text(config_content)
            files_created["config_file"] = str(config_file)
            self.log_manager.update_progress(operation_id, 70, "Generated configuration file")
            
            # 4. README
            readme_content = self._generate_readme(plugin_name, description, version, author)
            readme_file = plugin_dir / "README.md"
            readme_file.write_text(readme_content)
            files_created["readme"] = str(readme_file)
            self.log_manager.update_progress(operation_id, 85, "Generated documentation")
            
            # 5. Build script
            build_script = self._generate_build_script(plugin_name)
            build_file = plugin_dir / "build.sh"
            build_file.write_text(build_script)
            build_file.chmod(0o755)
            files_created["build_script"] = str(build_file)
            self.log_manager.update_progress(operation_id, 95, "Generated build script")
            
            # Log file creation
            for file_type, file_path in files_created.items():
                self.log_manager.log_file_created(operation_id, file_path, file_type)
            
            # Complete operation
            self.log_manager.complete_operation(operation_id, True, {
                "files_created": len(files_created),
                "plugin_name": plugin_name,
                "version": version
            })
            
            return files_created
            
        except Exception as e:
            self.log_manager.log_error(operation_id, str(e), "generation_error")
            self.log_manager.complete_operation(operation_id, False, {"error": str(e)})
            raise
    
    def _generate_plugin_class(self, plugin_name: str, description: str, 
                              version: str, author: str) -> str:
        """Generate the main BepInEx plugin class"""
        return f'''using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace {plugin_name}
{{
    [BepInPlugin(PluginInfo.PLUGIN_GUID, PluginInfo.PLUGIN_NAME, PluginInfo.PLUGIN_VERSION)]
    public class {plugin_name} : BaseUnityPlugin
    {{
        private const string PluginGUID = "{plugin_name}";
        private const string PluginName = "{plugin_name}";
        private const string PluginVersion = "{version}";
        
        private static ConfigFile Config {{ get; set; }}
        private static ConfigEntry<bool> ModEnabled {{ get; set; }}
        private static ConfigEntry<float> SomeSetting {{ get; set; }}
        
        private static readonly Harmony Harmony = new Harmony(PluginGUID);
        private static new ManualLogSource Logger {{ get; set; }}
        
        private void Awake()
        {{
            Logger = base.Logger;
            Config = base.Config;
            
            // Load configuration
            ModEnabled = Config.Bind("General", "Enabled", true, "Enable/disable the mod");
            SomeSetting = Config.Bind("General", "SomeSetting", 1.0f, "Some configurable setting");
            
            if (ModEnabled.Value)
            {{
                Logger.LogInfo($"{{PluginName}} v{{PluginVersion}} loaded successfully!");
                Harmony.PatchAll();
            }}
            else
            {{
                Logger.LogInfo($"{{PluginName}} is disabled in configuration.");
            }}
        }}
        
        private void OnDestroy()
        {{
            Harmony?.UnpatchSelf();
        }}
        
        // Example Harmony patch
        [HarmonyPatch(typeof(Player), nameof(Player.Update))]
        static class Player_Update_Patch
        {{
            static void Postfix(Player __instance)
            {{
                // Your custom logic here
                if (__instance.IsPlayer())
                {{
                    // Example: Log player position every 60 frames
                    if (Time.frameCount % 60 == 0)
                    {{
                        Logger.LogInfo($"Player position: {{__instance.transform.position}}");
                    }}
                }}
            }}
        }}
    }}
    
    public static class PluginInfo
    {{
        public const string PLUGIN_GUID = "{plugin_name}";
        public const string PLUGIN_NAME = "{plugin_name}";
        public const string PLUGIN_VERSION = "{version}";
    }}
}}'''
    
    def _generate_project_file(self, plugin_name: str, version: str) -> str:
        """Generate .csproj file for the plugin using VWE standardized versions"""
        self.logger.info(f"Generating project file with VWE standardized versions")
        
        # Log version usage
        self.logger.info(f"Using BepInEx {self.versions['BepInEx']}, HarmonyX {self.versions['HarmonyX']}, Valheim {self.versions['Valheim']}")
        
        return f'''<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net48</TargetFramework>
    <AssemblyName>{plugin_name}</AssemblyName>
    <RootNamespace>{plugin_name}</RootNamespace>
    <AssemblyVersion>{version}</AssemblyVersion>
    <FileVersion>{version}</FileVersion>
    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
    <AppendTargetFrameworkToOutputPath>false</AppendTargetFrameworkToOutputPath>
    <OutputPath>../../plugins/</OutputPath>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BepInEx.Core" Version="{self.versions['BepInEx']}" />
    <PackageReference Include="BepInEx.PluginInfoProps" Version="1.1.0" />
    <PackageReference Include="HarmonyX" Version="{self.versions['HarmonyX']}" />
    <PackageReference Include="UnityEngine.CoreModule" Version="{self.versions['UnityEngine.CoreModule']}" />
    <PackageReference Include="UnityEngine.PhysicsModule" Version="{self.versions['UnityEngine.PhysicsModule']}" />
    <PackageReference Include="UnityEngine.TextRenderingModule" Version="{self.versions['UnityEngine.TextRenderingModule']}" />
    <PackageReference Include="UnityEngine.UI" Version="{self.versions['UnityEngine.UI']}" />
    <PackageReference Include="Valheim" Version="{self.versions['Valheim']}" />
    <PackageReference Include="Newtonsoft.Json" Version="{self.versions['Newtonsoft.Json']}" />
  </ItemGroup>

  <ItemGroup>
    <Reference Include="Assembly-CSharp">
      <HintPath>../../references/Assembly-CSharp.dll</HintPath>
      <Private>false</Private>
    </Reference>
  </ItemGroup>

</Project>'''
    
    def _generate_config_file(self, plugin_name: str) -> str:
        """Generate BepInEx configuration file"""
        return f'''[General]

## Enable/disable the mod
# Setting type: Boolean
# Default value: true
Enabled = true

## Some configurable setting
# Setting type: Single
# Default value: 1.0
# Acceptable value range: 0.1 to 10.0
SomeSetting = 1.0

[Debug]

## Enable debug logging
# Setting type: Boolean
# Default value: false
DebugMode = false

## Log level verbosity
# Setting type: String
# Default value: Info
# Acceptable values: Trace, Debug, Info, Warning, Error, Fatal
LogLevel = Info'''
    
    def _generate_readme(self, plugin_name: str, description: str, 
                        version: str, author: str) -> str:
        """Generate README for the plugin"""
        return f'''# {plugin_name}

{description or f"A BepInEx plugin for Valheim World Engine"}

## Version
{version}

## Author
{author}

## Description
This plugin was generated using the Valheim World Engine C# generator.

## Installation
1. Install BepInEx for Valheim
2. Place the `{plugin_name}.dll` file in your `BepInEx/plugins/` folder
3. Start the game

## Configuration
The plugin creates a configuration file at `BepInEx/config/{plugin_name}.cfg` where you can adjust settings.

## Building
Run the included build script:
```bash
./build.sh
```

## Dependencies
- BepInEx 5.4.22+
- Valheim 0.217.46+
- HarmonyX 2.10.1+

## Generated Files
- `{plugin_name}.cs` - Main plugin class
- `{plugin_name}.csproj` - Project file
- `{plugin_name}.cfg` - Configuration template
- `build.sh` - Build script
- `README.md` - This file

## Development
This plugin uses HarmonyX for patching Valheim's game code. The main plugin class inherits from `BaseUnityPlugin` and provides hooks for game events.

## License
Generated by Valheim World Engine - See project license for details.
'''
    
    def _generate_build_script(self, plugin_name: str) -> str:
        """Generate build script for the plugin"""
        return f'''#!/bin/bash
# Build script for {plugin_name}

set -e

echo "Building {plugin_name}..."

# Check if dotnet is available
if ! command -v dotnet &> /dev/null; then
    echo "Error: dotnet is not installed or not in PATH"
    echo "Please install .NET SDK 6.0 or later"
    exit 1
fi

# Restore packages
echo "Restoring NuGet packages..."
dotnet restore

# Build the project
echo "Building project..."
dotnet build --configuration Release

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build successful! Plugin should be in ../../plugins/{plugin_name}.dll"
else
    echo "Build failed!"
    exit 1
fi

echo "Build complete!"
'''
    
    def create_data_exporter_plugin(self, plugin_name: str = "VWE_DataExporter") -> Dict[str, str]:
        """Generate a specialized data exporter plugin template"""
        return self.create_bepinex_plugin(
            plugin_name=plugin_name,
            description="Exports Valheim world data for VWE processing",
            version="1.0.0",
            author="VWE"
        )
    
    def create_autosave_plugin(self, plugin_name: str = "VWE_AutoSave") -> Dict[str, str]:
        """Generate a specialized autosave plugin template"""
        return self.create_bepinex_plugin(
            plugin_name=plugin_name,
            description="Triggers world save after generation for VWE",
            version="1.0.0",
            author="VWE"
        )
    
    def create_plugin_suite(self, suite_name: str, plugins: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """Generate a complete plugin suite with multiple related plugins"""
        self.logger.info(f"Creating VWE plugin suite: {suite_name}")
        self.logger.info(f"Suite will contain {len(plugins)} plugins")
        
        suite_results = {}
        
        for plugin_config in plugins:
            plugin_name = plugin_config.get("name", f"VWE_{suite_name}_Plugin")
            description = plugin_config.get("description", f"Plugin for {suite_name} suite")
            version = plugin_config.get("version", "1.0.0")
            author = plugin_config.get("author", "VWE")
            
            self.logger.info(f"  Generating plugin: {plugin_name}")
            files = self.create_bepinex_plugin(plugin_name, description, version, author)
            suite_results[plugin_name] = files
        
        self.logger.info(f"Plugin suite '{suite_name}' generation complete")
        return suite_results
    
    def create_vwe_core_plugins(self) -> Dict[str, Dict[str, str]]:
        """Generate the core VWE plugin suite"""
        core_plugins = [
            {
                "name": "VWE_DataExporter",
                "description": "Exports Valheim world data for VWE processing",
                "version": "1.0.0"
            },
            {
                "name": "VWE_AutoSave", 
                "description": "Triggers world save after generation for VWE",
                "version": "1.0.0"
            },
            {
                "name": "VWE_WorldProcessor",
                "description": "Processes world data during generation",
                "version": "1.0.0"
            },
            {
                "name": "VWE_ConfigManager",
                "description": "Manages VWE-specific configuration",
                "version": "1.0.0"
            }
        ]
        
        return self.create_plugin_suite("VWE_Core", core_plugins)


def main():
    """Example usage of the C# generator"""
    generator = CSharpGenerator()
    
    # Generate a basic plugin
    print("Generating basic BepInEx plugin...")
    files = generator.create_bepinex_plugin(
        plugin_name="VWE_ExamplePlugin",
        description="Example plugin generated by VWE C# generator",
        version="1.0.0",
        author="VWE"
    )
    
    print("Generated files:")
    for file_type, file_path in files.items():
        print(f"  {file_type}: {file_path}")
    
    # Generate specialized plugins
    print("\\nGenerating data exporter plugin...")
    generator.create_data_exporter_plugin()
    
    print("\\nGenerating autosave plugin...")
    generator.create_autosave_plugin()
    
    print("\\nC# generator example complete!")


if __name__ == "__main__":
    main()
