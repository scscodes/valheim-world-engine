using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using BepInEx.Logging;
using UnityEngine;
using Newtonsoft.Json;

namespace VWE_DataExporter.DataExporters
{
    public class HeightmapExporter
    {
        private readonly ManualLogSource _logger;
        private readonly int _resolution;

        public HeightmapExporter(ManualLogSource logger, int resolution)
        {
            _logger = logger;
            _resolution = resolution;
        }

        public IEnumerator ExportHeightmap(string exportPath, string format)
        {
            var startTime = DateTime.Now;
            _logger.LogInfo($"★★★ HeightmapExporter: START - resolution={_resolution}, format={format}, path={exportPath}");

            // Check WorldGenerator availability
            if (WorldGenerator.instance == null)
            {
                _logger.LogError("★★★ HeightmapExporter: FATAL - WorldGenerator.instance is NULL");
                yield break;
            }

            _logger.LogInfo($"★★★ HeightmapExporter: WorldGenerator.instance verified, starting sampling");

            var heightmapData = new Dictionary<string, object>();
            var heightMap = new float[_resolution, _resolution];

            // Sample height data across the world
            // FIX: Use world diameter, not radius for full coverage
            var worldRadius = 10000f; // Valheim world radius
            var worldDiameter = worldRadius * 2; // 20000m total diameter
            var stepSize = worldDiameter / _resolution;
            var totalSamples = _resolution * _resolution;
            var samplesProcessed = 0;
            var lastLoggedPercent = 0;
            var yieldCount = 0;
            var invalidHeightCount = 0;

            _logger.LogInfo($"★★★ HeightmapExporter: Starting sampling loop - {totalSamples} total samples, stepSize={stepSize}");
            _logger.LogInfo($"★★★ HeightmapExporter: Full world coverage - worldRadius={worldRadius}, worldDiameter={worldDiameter}");
            _logger.LogInfo($"★★★ HeightmapExporter: Coverage range - X=[{-worldRadius} to {worldRadius}], Z=[{-worldRadius} to {worldRadius}]");

            for (int x = 0; x < _resolution; x++)
            {
                for (int z = 0; z < _resolution; z++)
                {
                    float worldX = 0f;
                    float worldZ = 0f;

                    try
                    {
                        // FIX: Calculate world coordinates to cover full ±10km range
                        worldX = (x * stepSize) - worldRadius;
                        worldZ = (z * stepSize) - worldRadius;

                        var height = GetHeightAtPosition(worldX, worldZ);

                        // Validate height value
                        if (float.IsNaN(height) || float.IsInfinity(height))
                        {
                            _logger.LogWarning($"★★★ HeightmapExporter: Invalid height at ({worldX:F1}, {worldZ:F1}): {height}");
                            height = 0f;
                            invalidHeightCount++;
                        }

                        heightMap[x, z] = height;
                        samplesProcessed++;

                        // Log first and last samples to verify full world coverage
                        if (samplesProcessed == 1 || samplesProcessed == totalSamples)
                        {
                            _logger.LogInfo($"★★★ HeightmapExporter: Sample #{samplesProcessed}/{totalSamples} - pos=({worldX:F2}, {worldZ:F2}), height={height:F1}m");
                        }

                        // Log progress every 10%
                        var percentComplete = (samplesProcessed * 100) / totalSamples;
                        if (percentComplete >= lastLoggedPercent + 10)
                        {
                            var elapsed = (DateTime.Now - startTime).TotalSeconds;
                            var samplesPerSec = samplesProcessed / elapsed;
                            _logger.LogInfo($"★★★ HeightmapExporter: {percentComplete}% complete ({samplesProcessed}/{totalSamples} samples, {elapsed:F1}s elapsed, {samplesPerSec:F0} samples/sec, {yieldCount} yields) | Last: pos=({worldX:F0}, {worldZ:F0}), height={height:F1}m");
                            lastLoggedPercent = percentComplete;
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"★★★ HeightmapExporter: Error sampling at x={x}, z={z}, worldPos=({worldX:F1}, {worldZ:F1}): {ex.GetType().Name} - {ex.Message}");
                        heightMap[x, z] = 0f; // Default to sea level
                        samplesProcessed++;
                    }

                    // Yield every 100 samples to prevent frame drops (outside try-catch)
                    if (samplesProcessed % 100 == 0)
                    {
                        yieldCount++;
                        yield return null;
                    }
                }
            }

            _logger.LogInfo($"★★★ HeightmapExporter: Sampling complete - {samplesProcessed} samples processed, {yieldCount} yields executed, {invalidHeightCount} invalid values");

            // Calculate height statistics
            _logger.LogInfo($"★★★ HeightmapExporter: Calculating statistics");
            var minHeight = float.MaxValue;
            var maxHeight = float.MinValue;
            var avgHeight = 0f;

            try
            {
                foreach (var height in heightMap)
                {
                    if (height < minHeight) minHeight = height;
                    if (height > maxHeight) maxHeight = height;
                    avgHeight += height;
                }
                avgHeight /= (_resolution * _resolution);
                _logger.LogInfo($"★★★ HeightmapExporter: Stats - min={minHeight:F1}, max={maxHeight:F1}, avg={avgHeight:F1}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ HeightmapExporter: Error calculating statistics: {ex.GetType().Name} - {ex.Message}");
                yield break;
            }

            // Prepare export data
            _logger.LogInfo($"★★★ HeightmapExporter: Preparing export data");
            try
            {
                heightmapData["resolution"] = _resolution;
                heightmapData["world_radius"] = worldRadius;
                heightmapData["world_diameter"] = worldDiameter;
                heightmapData["height_map"] = heightMap;
                heightmapData["min_height"] = minHeight;
                heightmapData["max_height"] = maxHeight;
                heightmapData["avg_height"] = avgHeight;
                heightmapData["export_timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
                _logger.LogInfo($"★★★ HeightmapExporter: Export data prepared successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ HeightmapExporter: Error preparing export data: {ex.GetType().Name} - {ex.Message}");
                yield break;
            }

            // Export based on format (non-yielding methods)
            if (format == "json" || format == "both")
            {
                _logger.LogInfo($"★★★ HeightmapExporter: Starting JSON export");
                ExportHeightmapJson(exportPath, heightmapData);
            }

            if (format == "png" || format == "both")
            {
                _logger.LogInfo($"★★★ HeightmapExporter: Starting PNG export");
                ExportHeightmapPng(exportPath, heightMap, minHeight, maxHeight);
            }

            var totalTime = (DateTime.Now - startTime).TotalSeconds;
            _logger.LogInfo($"★★★ HeightmapExporter: COMPLETE - Total time: {totalTime:F1}s");
        }

        private float GetHeightAtPosition(float worldX, float worldZ)
        {
            if (WorldGenerator.instance == null)
                return 0f;

            // Get height using WorldGenerator - returns height directly
            return WorldGenerator.instance.GetHeight(worldX, worldZ);
        }

        private void ExportHeightmapJson(string exportPath, Dictionary<string, object> heightmapData)
        {
            try
            {
                var jsonPath = Path.Combine(exportPath, "heightmap.json");
                var json = JsonConvert.SerializeObject(heightmapData, Formatting.Indented);
                File.WriteAllText(jsonPath, json);
                _logger.LogInfo($"VWE DataExporter: Heightmap JSON exported to {jsonPath}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Failed to export heightmap JSON: {ex.Message}");
            }
        }

        private void ExportHeightmapPng(string exportPath, float[,] heightMap, float minHeight, float maxHeight)
        {
            try
            {
                var pngPath = Path.Combine(exportPath, "heightmap.png");
                
                // Create texture from height map
                var texture = new Texture2D(_resolution, _resolution, TextureFormat.RGB24, false);
                var pixels = new Color[_resolution * _resolution];

                var heightRange = maxHeight - minHeight;
                if (heightRange <= 0) heightRange = 1f;

                for (int x = 0; x < _resolution; x++)
                {
                    for (int z = 0; z < _resolution; z++)
                    {
                        var height = heightMap[x, z];
                        var normalizedHeight = (height - minHeight) / heightRange;
                        
                        // Create grayscale color based on height
                        var color = new Color(normalizedHeight, normalizedHeight, normalizedHeight);
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

                _logger.LogInfo($"VWE DataExporter: Heightmap PNG exported to {pngPath}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Failed to export heightmap PNG: {ex.Message}");
            }
        }
    }
}
