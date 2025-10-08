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
            try
            {
                _logger.LogInfo($"VWE DataExporter: Starting heightmap export (resolution: {_resolution})");

                // Get heightmap data from ZoneSystem
                var zoneSystem = ZoneSystem.instance;
                if (zoneSystem == null)
                {
                    _logger.LogWarning("VWE DataExporter: ZoneSystem not available for heightmap export");
                    yield break;
                }

                var heightmapData = new Dictionary<string, object>();
                var heightMap = new float[_resolution, _resolution];

                // Sample height data across the world
                var worldSize = 10000f; // Valheim world size
                var stepSize = worldSize / _resolution;

                for (int x = 0; x < _resolution; x++)
                {
                    for (int z = 0; z < _resolution; z++)
                    {
                        var worldPos = new Vector3(
                            (x * stepSize) - (worldSize / 2),
                            0,
                            (z * stepSize) - (worldSize / 2)
                        );

                        var height = GetHeightAtPosition(worldPos);
                        heightMap[x, z] = height;

                        // Yield every 100 samples to prevent frame drops
                        if ((x * _resolution + z) % 100 == 0)
                        {
                            yield return null;
                        }
                    }
                }

                // Calculate height statistics
                var minHeight = float.MaxValue;
                var maxHeight = float.MinValue;
                var avgHeight = 0f;

                foreach (var height in heightMap)
                {
                    if (height < minHeight) minHeight = height;
                    if (height > maxHeight) maxHeight = height;
                    avgHeight += height;
                }
                avgHeight /= (_resolution * _resolution);

                // Prepare export data
                heightmapData["resolution"] = _resolution;
                heightmapData["world_size"] = worldSize;
                heightmapData["height_map"] = heightMap;
                heightmapData["min_height"] = minHeight;
                heightmapData["max_height"] = maxHeight;
                heightmapData["avg_height"] = avgHeight;
                heightmapData["export_timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");

                // Export based on format
                if (format == "json" || format == "both")
                {
                    ExportHeightmapJson(exportPath, heightmapData);
                }

                if (format == "png" || format == "both")
                {
                    yield return StartCoroutine(ExportHeightmapPng(exportPath, heightMap, minHeight, maxHeight));
                }

                _logger.LogInfo("VWE DataExporter: Heightmap export completed successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Heightmap export failed: {ex.Message}");
            }
        }

        private float GetHeightAtPosition(Vector3 worldPos)
        {
            try
            {
                var zoneSystem = ZoneSystem.instance;
                if (zoneSystem == null) return 0f;

                // Get height using ZoneSystem's method
                var height = zoneSystem.GetGroundHeight(worldPos);
                return height;
            }
            catch
            {
                return 0f;
            }
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

        private IEnumerator ExportHeightmapPng(string exportPath, float[,] heightMap, float minHeight, float maxHeight)
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
