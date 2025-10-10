using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using YamlDotNet.Serialization;

namespace ValheimWorldEngine.Generators
{
    public class ValheimConstantsGenerator
    {
        public static void GenerateConstants()
        {
            // Load YAML configuration
            var config = LoadYamlConfig();
            var validation = LoadValidationData();
            var rendering = LoadRenderingConfig();
            
            // Generate C# constants
            GenerateCSharpConstants(config, validation, rendering);
            
            Console.WriteLine("C# constants generated successfully!");
        }
        
        private static Dictionary<string, object> LoadYamlConfig()
        {
            var configPath = Path.Combine("..", "..", "data", "valheim-world.yml");
            var yamlContent = File.ReadAllText(configPath);
            var deserializer = new DeserializerBuilder().Build();
            return deserializer.Deserialize<Dictionary<string, object>>(yamlContent);
        }
        
        private static Dictionary<string, object> LoadValidationData()
        {
            var validationPath = Path.Combine("..", "..", "data", "validation-data.yml");
            var yamlContent = File.ReadAllText(validationPath);
            var deserializer = new DeserializerBuilder().Build();
            return deserializer.Deserialize<Dictionary<string, object>>(yamlContent);
        }
        
        private static Dictionary<string, object> LoadRenderingConfig()
        {
            var renderingPath = Path.Combine("..", "..", "data", "rendering-config.yml");
            var yamlContent = File.ReadAllText(renderingPath);
            var deserializer = new DeserializerBuilder().Build();
            return deserializer.Deserialize<Dictionary<string, object>>(yamlContent);
        }
        
        private static void GenerateCSharpConstants(Dictionary<string, object> config, 
                                                   Dictionary<string, object> validation, 
                                                   Dictionary<string, object> rendering)
        {
            var outputPath = Path.Combine("..", "..", "..", "bepinex", "src", "VWE_DataExporter", "ValheimConstants.cs");
            
            using var writer = new StreamWriter(outputPath);
            
            writer.WriteLine("// Generated Valheim Constants");
            writer.WriteLine("// ===========================");
            writer.WriteLine("// DO NOT EDIT - Generated from global/data/*.yml");
            writer.WriteLine($"// Generated: {DateTime.Now:yyyy-MM-dd}");
            writer.WriteLine();
            writer.WriteLine("using System.Collections.Generic;");
            writer.WriteLine();
            writer.WriteLine("namespace VWE_DataExporter");
            writer.WriteLine("{");
            writer.WriteLine("    public static class ValheimConstants");
            writer.WriteLine("    {");
            
            // World constants
            var world = (Dictionary<string, object>)config["world"];
            writer.WriteLine("        // World dimensions");
            writer.WriteLine($"        public const float WORLD_RADIUS = {world["radius"]}f;");
            writer.WriteLine($"        public const float WORLD_DIAMETER = {world["diameter"]}f;");
            writer.WriteLine($"        public const float WATER_EDGE = {world["water_edge"]}f;");
            writer.WriteLine();
            
            // Coordinate system
            var coordinates = (Dictionary<string, object>)config["coordinates"];
            var origin = (List<object>)coordinates["origin"];
            writer.WriteLine("        // Coordinate system");
            writer.WriteLine($"        public const float COORDINATE_ORIGIN_X = {origin[0]}f;");
            writer.WriteLine($"        public const float COORDINATE_ORIGIN_Z = {origin[1]}f;");
            writer.WriteLine($"        public const string COORDINATE_UNIT = \"{coordinates["unit"]}\";");
            writer.WriteLine();
            
            // Height system
            var height = (Dictionary<string, object>)config["height"];
            writer.WriteLine("        // Height system");
            writer.WriteLine($"        public const float SEA_LEVEL = {height["sea_level"]}f;");
            writer.WriteLine($"        public const float HEIGHT_MULTIPLIER = {height["multiplier"]}f;");
            writer.WriteLine($"        public const float OCEAN_THRESHOLD = {height["ocean_threshold"]}f;");
            writer.WriteLine($"        public const float MOUNTAIN_THRESHOLD = {height["mountain_threshold"]}f;");
            writer.WriteLine();
            
            // Biome constants
            var biomes = (Dictionary<string, object>)config["biomes"];
            var defaults = (Dictionary<string, object>)biomes["defaults"];
            
            writer.WriteLine("        // Biome IDs");
            writer.WriteLine("        public const int BIOME_MEADOWS = 1;");
            writer.WriteLine("        public const int BIOME_BLACKFOREST = 2;");
            writer.WriteLine("        public const int BIOME_SWAMP = 4;");
            writer.WriteLine("        public const int BIOME_MOUNTAIN = 8;");
            writer.WriteLine("        public const int BIOME_PLAINS = 16;");
            writer.WriteLine("        public const int BIOME_OCEAN = 32;");
            writer.WriteLine("        public const int BIOME_MISTLANDS = 64;");
            writer.WriteLine("        public const int BIOME_DEEPNORTH = 256;");
            writer.WriteLine("        public const int BIOME_ASHLANDS = 512;");
            writer.WriteLine();
            
            // Generate biome data
            writer.WriteLine("        // Biome data");
            writer.WriteLine("        public static readonly Dictionary<string, BiomeData> BIOMES = new()");
            writer.WriteLine("        {");
            
            foreach (var kvp in biomes)
            {
                if (kvp.Key == "defaults") continue;
                
                var biome = (Dictionary<string, object>)kvp.Value;
                var name = kvp.Key;
                var id = biome["id"];
                var rgb = (List<object>)biome["rgb"];
                var hex = biome["hex"];
                
                // Merge with defaults
                var heightRange = biome.ContainsKey("height_range") ? 
                    (List<object>)biome["height_range"] : 
                    (List<object>)defaults["height_range"];
                var distanceRange = biome.ContainsKey("distance_range") ? 
                    (List<object>)biome["distance_range"] : 
                    (List<object>)defaults["distance_range"];
                var noiseThreshold = biome.ContainsKey("noise_threshold") ? 
                    biome["noise_threshold"] : 
                    defaults["noise_threshold"];
                var polarOffset = biome.ContainsKey("polar_offset") ? 
                    biome["polar_offset"] : 
                    defaults["polar_offset"];
                var fallbackDistance = biome.ContainsKey("fallback_distance") ? 
                    biome["fallback_distance"] : 
                    defaults["fallback_distance"];
                var minMountainDistance = biome.ContainsKey("min_mountain_distance") ? 
                    biome["min_mountain_distance"] : 
                    defaults["min_mountain_distance"];
                
                writer.WriteLine($"            [\"{name}\"] = new BiomeData");
                writer.WriteLine("            {");
                writer.WriteLine($"                Id = {id},");
                writer.WriteLine($"                Rgb = ({rgb[0]}, {rgb[1]}, {rgb[2]}),");
                writer.WriteLine($"                Hex = \"{hex}\",");
                writer.WriteLine($"                HeightRange = ({heightRange[0]}, {heightRange[1]}),");
                writer.WriteLine($"                DistanceRange = ({distanceRange[0]}, {distanceRange[1]}),");
                writer.WriteLine($"                NoiseThreshold = {noiseThreshold}f,");
                writer.WriteLine($"                PolarOffset = {polarOffset},");
                writer.WriteLine($"                FallbackDistance = {fallbackDistance},");
                writer.WriteLine($"                MinMountainDistance = {minMountainDistance}");
                writer.WriteLine("            },");
            }
            
            writer.WriteLine("        };");
            writer.WriteLine("    }");
            writer.WriteLine();
            writer.WriteLine("    public class BiomeData");
            writer.WriteLine("    {");
            writer.WriteLine("        public int Id { get; set; }");
            writer.WriteLine("        public (int, int, int) Rgb { get; set; }");
            writer.WriteLine("        public string Hex { get; set; }");
            writer.WriteLine("        public (int, int) HeightRange { get; set; }");
            writer.WriteLine("        public (int, int) DistanceRange { get; set; }");
            writer.WriteLine("        public float NoiseThreshold { get; set; }");
            writer.WriteLine("        public int PolarOffset { get; set; }");
            writer.WriteLine("        public float? FallbackDistance { get; set; }");
            writer.WriteLine("        public int? MinMountainDistance { get; set; }");
            writer.WriteLine("    }");
            writer.WriteLine("}");
        }
    }
}
