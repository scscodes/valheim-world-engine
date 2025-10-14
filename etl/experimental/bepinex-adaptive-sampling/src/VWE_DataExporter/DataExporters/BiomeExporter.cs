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
        private readonly bool _useDynamicYield;
        private readonly int _yieldIntervalMs;

        public BiomeExporter(ManualLogSource logger, int resolution, bool useDynamicYield = false, int yieldIntervalMs = 100)
        {
            _logger = logger;
            _resolution = resolution;
            _useDynamicYield = useDynamicYield;
            _yieldIntervalMs = yieldIntervalMs;
        }

        public IEnumerator ExportBiomes(string exportPath, string format)
        {
            var startTime = DateTime.Now;
            var yieldStrategy = _useDynamicYield ? "TIME-BASED" : "SAMPLE-BASED";
            _logger.LogInfo($"★★★ BiomeExporter: START - resolution={_resolution}, format={format}, yield={yieldStrategy}, interval={_yieldIntervalMs}ms, path={exportPath}");

            // Check WorldGenerator availability
            if (WorldGenerator.instance == null)
            {
                _logger.LogError("★★★ BiomeExporter: FATAL - WorldGenerator.instance is NULL");
                yield break;
            }

            _logger.LogInfo($"★★★ BiomeExporter: WorldGenerator.instance verified, starting sampling");

            var biomeData = new Dictionary<string, object>();
            var biomeMap = new int[_resolution, _resolution];

            // Sample biome data across the world
            // FIX: Use world diameter, not radius for full coverage
            var worldRadius = 10000f; // Valheim world radius
            var worldDiameter = worldRadius * 2; // 20000m total diameter
            var stepSize = worldDiameter / _resolution;
            var totalSamples = _resolution * _resolution;
            var samplesProcessed = 0;
            var lastLoggedPercent = 0;
            var yieldCount = 0;
            var lastYieldTime = DateTime.Now;

            _logger.LogInfo($"★★★ BiomeExporter: Starting sampling loop - {totalSamples} total samples, stepSize={stepSize}");
            _logger.LogInfo($"★★★ BiomeExporter: Full world coverage - worldRadius={worldRadius}, worldDiameter={worldDiameter}");
            _logger.LogInfo($"★★★ BiomeExporter: Coverage range - X=[{-worldRadius} to {worldRadius}], Z=[{-worldRadius} to {worldRadius}]");

            for (int x = 0; x < _resolution; x++)
            {
                for (int z = 0; z < _resolution; z++)
                {
                    try
                    {
                        // FIX: Sample pixel centers (standard GIS practice) to reduce edge bias
                        var worldX = ((x + 0.5f) * stepSize) - worldRadius;
                        var worldZ = ((z + 0.5f) * stepSize) - worldRadius;

                        var biome = GetBiomeAtPosition(worldX, worldZ);
                        biomeMap[x, z] = (int)biome;

                        samplesProcessed++;

                        // Log first and last samples to verify full world coverage
                        if (samplesProcessed == 1 || samplesProcessed == totalSamples)
                        {
                            var biomeName = GetBiomeNames().ContainsKey((int)biome) ? GetBiomeNames()[(int)biome] : $"Unknown({(int)biome})";
                            _logger.LogInfo($"★★★ BiomeExporter: Sample #{samplesProcessed}/{totalSamples} - pos=({worldX:F2}, {worldZ:F2}), biome={biomeName}");
                        }

                        // Log progress every 10%
                        var percentComplete = (samplesProcessed * 100) / totalSamples;
                        if (percentComplete >= lastLoggedPercent + 10)
                        {
                            var elapsed = (DateTime.Now - startTime).TotalSeconds;
                            var samplesPerSec = samplesProcessed / elapsed;
                            var biomeName = GetBiomeNames().ContainsKey((int)biome) ? GetBiomeNames()[(int)biome] : $"Unknown({(int)biome})";
                            _logger.LogInfo($"★★★ BiomeExporter: {percentComplete}% complete ({samplesProcessed}/{totalSamples} samples, {elapsed:F1}s elapsed, {samplesPerSec:F0} samples/sec, {yieldCount} yields) | Last: pos=({worldX:F0}, {worldZ:F0}), biome={biomeName}");
                            lastLoggedPercent = percentComplete;
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"★★★ BiomeExporter: Error sampling at x={x}, z={z}: {ex.GetType().Name} - {ex.Message}");
                        // Continue sampling despite error
                        biomeMap[x, z] = 0; // Default to Meadows
                    }

                    // Yield based on strategy
                    bool shouldYield = false;
                    if (_useDynamicYield)
                    {
                        // Time-based yielding: Yield every N milliseconds
                        var timeSinceLastYield = (DateTime.Now - lastYieldTime).TotalMilliseconds;
                        if (timeSinceLastYield >= _yieldIntervalMs)
                        {
                            shouldYield = true;
                            lastYieldTime = DateTime.Now;
                        }
                    }
                    else
                    {
                        // Sample-based yielding: Yield every 100 samples
                        if (samplesProcessed % 100 == 0)
                        {
                            shouldYield = true;
                        }
                    }

                    if (shouldYield)
                    {
                        yieldCount++;
                        yield return null;
                    }
                }
            }

            _logger.LogInfo($"★★★ BiomeExporter: Sampling complete - {samplesProcessed} samples processed, {yieldCount} yields executed");

            // Prepare export data
            _logger.LogInfo($"★★★ BiomeExporter: Preparing export data");
            try
            {
                biomeData["resolution"] = _resolution;
                biomeData["world_radius"] = worldRadius;
                biomeData["world_diameter"] = worldDiameter;
                biomeData["biome_map"] = biomeMap;
                biomeData["biome_names"] = GetBiomeNames();
                biomeData["export_timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
                _logger.LogInfo($"★★★ BiomeExporter: Export data prepared successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ BiomeExporter: Error preparing export data: {ex.GetType().Name} - {ex.Message}");
                yield break;
            }

            // Export based on format (non-yielding methods)
            if (format == "json" || format == "both")
            {
                _logger.LogInfo($"★★★ BiomeExporter: Starting JSON export");
                ExportBiomesJson(exportPath, biomeData);
            }

            if (format == "png" || format == "both")
            {
                _logger.LogInfo($"★★★ BiomeExporter: Starting PNG export");
                ExportBiomesPng(exportPath, biomeMap);
            }

            var totalTime = (DateTime.Now - startTime).TotalSeconds;
            _logger.LogInfo($"★★★ BiomeExporter: COMPLETE - Total time: {totalTime:F1}s");
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
            // FIX: Use Valheim's actual bit flag enum values, not sequential indices
            // Valheim uses powers of 2 for biome flags
            return new Dictionary<int, string>
            {
                { 1, "Meadows" },      // Heightmap.Biome.Meadows = 1
                { 2, "BlackForest" },  // Heightmap.Biome.BlackForest = 2
                { 4, "Swamp" },        // Heightmap.Biome.Swamp = 4
                { 8, "Mountain" },     // Heightmap.Biome.Mountain = 8
                { 16, "Plains" },      // Heightmap.Biome.Plains = 16
                { 32, "Ocean" },       // Heightmap.Biome.Ocean = 32
                { 64, "Mistlands" },   // Heightmap.Biome.Mistlands = 64
                { 256, "DeepNorth" },  // Heightmap.Biome.DeepNorth = 256
                { 512, "Ashlands" }    // Heightmap.Biome.Ashlands = 512
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
