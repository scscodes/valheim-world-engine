using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using BepInEx.Logging;
using UnityEngine;
using Newtonsoft.Json;

namespace VWE_DataExporter.DataExporters
{
    public class BiomeExporter
    {
        private readonly ManualLogSource _logger;
        private readonly int _resolution;

        public BiomeExporter(ManualLogSource logger, int resolution)
        {
            _logger = logger;
            _resolution = resolution;
        }

        public IEnumerator ExportBiomes(string exportPath, string format)
        {
            _logger.LogInfo($"VWE DataExporter: Starting biome export (resolution: {_resolution})");

            // Check WorldGenerator availability
            if (WorldGenerator.instance == null)
            {
                _logger.LogWarning("VWE DataExporter: WorldGenerator not available for biome export");
                yield break;
            }

            var biomeData = new Dictionary<string, object>();
            var biomeMap = new int[_resolution, _resolution];

            // Sample biome data across the world
            var worldSize = 10000f; // Valheim world size
            var stepSize = worldSize / _resolution;

            for (int x = 0; x < _resolution; x++)
            {
                for (int z = 0; z < _resolution; z++)
                {
                    var worldX = (x * stepSize) - (worldSize / 2);
                    var worldZ = (z * stepSize) - (worldSize / 2);

                    var biome = GetBiomeAtPosition(worldX, worldZ);
                    biomeMap[x, z] = (int)biome;

                    // Yield every 100 samples to prevent frame drops
                    if ((x * _resolution + z) % 100 == 0)
                    {
                        yield return null;
                    }
                }
            }

            // Prepare export data
            biomeData["resolution"] = _resolution;
            biomeData["world_size"] = worldSize;
            biomeData["biome_map"] = biomeMap;
            biomeData["biome_names"] = GetBiomeNames();
            biomeData["export_timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");

            // Export based on format (non-yielding methods)
            if (format == "json" || format == "both")
            {
                ExportBiomesJson(exportPath, biomeData);
            }

            if (format == "png" || format == "both")
            {
                ExportBiomesPng(exportPath, biomeMap);
            }

            _logger.LogInfo("VWE DataExporter: Biome export completed successfully");
        }

        private Heightmap.Biome GetBiomeAtPosition(float worldX, float worldZ)
        {
            if (WorldGenerator.instance == null)
                return Heightmap.Biome.Meadows;

            // Get biome using WorldGenerator
            return WorldGenerator.instance.GetBiome(worldX, worldZ);
        }

        private Dictionary<int, string> GetBiomeNames()
        {
            return new Dictionary<int, string>
            {
                { 0, "Meadows" },
                { 1, "BlackForest" },
                { 2, "Swamp" },
                { 3, "Mountain" },
                { 4, "Plains" },
                { 5, "Ocean" },
                { 6, "Mistlands" },
                { 7, "DeepNorth" },
                { 8, "Ashlands" }
            };
        }

        private void ExportBiomesJson(string exportPath, Dictionary<string, object> biomeData)
        {
            try
            {
                var jsonPath = Path.Combine(exportPath, "biomes.json");
                var json = JsonConvert.SerializeObject(biomeData, Formatting.Indented);
                File.WriteAllText(jsonPath, json);
                _logger.LogInfo($"VWE DataExporter: Biome JSON exported to {jsonPath}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Failed to export biome JSON: {ex.Message}");
            }
        }

        private void ExportBiomesPng(string exportPath, int[,] biomeMap)
        {
            try
            {
                var pngPath = Path.Combine(exportPath, "biomes.png");
                
                // Create texture from biome map
                var texture = new Texture2D(_resolution, _resolution, TextureFormat.RGB24, false);
                var pixels = new Color[_resolution * _resolution];

                for (int x = 0; x < _resolution; x++)
                {
                    for (int z = 0; z < _resolution; z++)
                    {
                        var biome = biomeMap[x, z];
                        var color = GetBiomeColor(biome);
                        pixels[x * _resolution + z] = color;
                    }
                }

                texture.SetPixels(pixels);
                texture.Apply();

                // Convert to PNG
                var pngData = texture.EncodeToPNG();
                File.WriteAllBytes(pngPath, pngData);

                // Clean up
                UnityEngine.Object.Destroy(texture);

                _logger.LogInfo($"VWE DataExporter: Biome PNG exported to {pngPath}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Failed to export biome PNG: {ex.Message}");
            }
        }

        private Color GetBiomeColor(int biome)
        {
            return biome switch
            {
                0 => new Color(0.4f, 0.8f, 0.4f), // Meadows - Green
                1 => new Color(0.2f, 0.4f, 0.2f), // BlackForest - Dark Green
                2 => new Color(0.3f, 0.3f, 0.1f), // Swamp - Brown
                3 => new Color(0.8f, 0.8f, 0.9f), // Mountain - White
                4 => new Color(0.8f, 0.7f, 0.4f), // Plains - Yellow
                5 => new Color(0.2f, 0.4f, 0.8f), // Ocean - Blue
                6 => new Color(0.6f, 0.4f, 0.8f), // Mistlands - Purple
                7 => new Color(0.9f, 0.9f, 0.9f), // DeepNorth - Light Gray
                8 => new Color(0.6f, 0.2f, 0.1f), // Ashlands - Red
                _ => new Color(0.5f, 0.5f, 0.5f)  // Unknown - Gray
            };
        }
    }
}
