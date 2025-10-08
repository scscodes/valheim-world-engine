using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using BepInEx.Logging;
using UnityEngine;
using Newtonsoft.Json;

namespace VWE_DataExporter.DataExporters
{
    public class StructureExporter
    {
        private readonly ManualLogSource _logger;

        public StructureExporter(ManualLogSource logger)
        {
            _logger = logger;
        }

        public IEnumerator ExportStructures(string exportPath, string format)
        {
            try
            {
                _logger.LogInfo("VWE DataExporter: Starting structure export");

                // Get structure data from ZoneSystem
                var zoneSystem = ZoneSystem.instance;
                if (zoneSystem == null)
                {
                    _logger.LogWarning("VWE DataExporter: ZoneSystem not available for structure export");
                    yield break;
                }

                var structureData = new Dictionary<string, object>();
                var structures = new List<Dictionary<string, object>>();

                // Find all structures in the world
                var allStructures = FindAllStructures();
                
                foreach (var structure in allStructures)
                {
                    var structureInfo = new Dictionary<string, object>
                    {
                        ["name"] = structure.name,
                        ["position"] = new
                        {
                            x = structure.transform.position.x,
                            y = structure.transform.position.y,
                            z = structure.transform.position.z
                        },
                        ["rotation"] = new
                        {
                            x = structure.transform.rotation.x,
                            y = structure.transform.rotation.y,
                            z = structure.transform.rotation.z,
                            w = structure.transform.rotation.w
                        },
                        ["scale"] = new
                        {
                            x = structure.transform.localScale.x,
                            y = structure.transform.localScale.y,
                            z = structure.transform.localScale.z
                        },
                        ["tag"] = structure.tag,
                        ["layer"] = structure.layer
                    };

                    // Add biome information
                    var biome = GetBiomeAtPosition(structure.transform.position);
                    structureInfo["biome"] = biome.ToString();

                    // Add height information
                    var height = GetHeightAtPosition(structure.transform.position);
                    structureInfo["height"] = height;

                    structures.Add(structureInfo);

                    // Yield every 10 structures to prevent frame drops
                    if (structures.Count % 10 == 0)
                    {
                        yield return null;
                    }
                }

                // Prepare export data
                structureData["structure_count"] = structures.Count;
                structureData["structures"] = structures;
                structureData["export_timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");

                // Export based on format
                if (format == "json" || format == "both")
                {
                    ExportStructuresJson(exportPath, structureData);
                }

                if (format == "png" || format == "both")
                {
                    yield return StartCoroutine(ExportStructuresPng(exportPath, structures));
                }

                _logger.LogInfo($"VWE DataExporter: Structure export completed successfully ({structures.Count} structures)");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Structure export failed: {ex.Message}");
            }
        }

        private List<GameObject> FindAllStructures()
        {
            var structures = new List<GameObject>();
            
            try
            {
                // Find all GameObjects with specific tags that indicate structures
                var structureTags = new[] { "piece", "structure", "building", "dungeon" };
                
                foreach (var tag in structureTags)
                {
                    var objects = GameObject.FindGameObjectsWithTag(tag);
                    structures.AddRange(objects);
                }

                // Also find objects by component types that indicate structures
                var structureComponents = new[] { typeof(Piece), typeof(PrivateArea), typeof(DungeonGenerator) };
                
                foreach (var componentType in structureComponents)
                {
                    var objects = UnityEngine.Object.FindObjectsOfType(componentType);
                    foreach (var obj in objects)
                    {
                        if (obj is Component component && component.gameObject != null)
                        {
                            structures.Add(component.gameObject);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"VWE DataExporter: Error finding structures: {ex.Message}");
            }

            return structures;
        }

        private Heightmap.Biome GetBiomeAtPosition(Vector3 worldPos)
        {
            try
            {
                var zoneSystem = ZoneSystem.instance;
                if (zoneSystem == null) return Heightmap.Biome.Meadows;

                var biome = zoneSystem.GetBiome(worldPos);
                return biome;
            }
            catch
            {
                return Heightmap.Biome.Meadows;
            }
        }

        private float GetHeightAtPosition(Vector3 worldPos)
        {
            try
            {
                var zoneSystem = ZoneSystem.instance;
                if (zoneSystem == null) return 0f;

                var height = zoneSystem.GetGroundHeight(worldPos);
                return height;
            }
            catch
            {
                return 0f;
            }
        }

        private void ExportStructuresJson(string exportPath, Dictionary<string, object> structureData)
        {
            try
            {
                var jsonPath = Path.Combine(exportPath, "structures.json");
                var json = JsonConvert.SerializeObject(structureData, Formatting.Indented);
                File.WriteAllText(jsonPath, json);
                _logger.LogInfo($"VWE DataExporter: Structure JSON exported to {jsonPath}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Failed to export structure JSON: {ex.Message}");
            }
        }

        private IEnumerator ExportStructuresPng(string exportPath, List<Dictionary<string, object>> structures)
        {
            try
            {
                var pngPath = Path.Combine(exportPath, "structures.png");
                
                // Create a map showing structure locations
                var resolution = 2048;
                var worldSize = 10000f;
                var texture = new Texture2D(resolution, resolution, TextureFormat.RGB24, false);
                var pixels = new Color[resolution * resolution];

                // Initialize with transparent background
                for (int i = 0; i < pixels.Length; i++)
                {
                    pixels[i] = new Color(0, 0, 0, 0);
                }

                // Draw structures on the map
                foreach (var structure in structures)
                {
                    var position = (Dictionary<string, object>)structure["position"];
                    var x = (float)position["x"];
                    var z = (float)position["z"];

                    // Convert world coordinates to texture coordinates
                    var texX = (int)((x + worldSize / 2) / worldSize * resolution);
                    var texZ = (int)((z + worldSize / 2) / worldSize * resolution);

                    if (texX >= 0 && texX < resolution && texZ >= 0 && texZ < resolution)
                    {
                        // Draw structure as a colored dot
                        var color = GetStructureColor(structure);
                        pixels[texZ * resolution + texX] = color;
                    }
                }

                texture.SetPixels(pixels);
                texture.Apply();

                // Convert to PNG
                var pngData = texture.EncodeToPNG();
                File.WriteAllBytes(pngPath, pngData);

                // Clean up
                UnityEngine.Object.Destroy(texture);

                _logger.LogInfo($"VWE DataExporter: Structure PNG exported to {pngPath}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"VWE DataExporter: Failed to export structure PNG: {ex.Message}");
            }
        }

        private Color GetStructureColor(Dictionary<string, object> structure)
        {
            var name = structure["name"].ToString().ToLower();
            
            return name switch
            {
                var n when n.Contains("dungeon") => new Color(1f, 0f, 0f), // Red for dungeons
                var n when n.Contains("tower") => new Color(0f, 0f, 1f), // Blue for towers
                var n when n.Contains("ruin") => new Color(0.5f, 0.5f, 0.5f), // Gray for ruins
                var n when n.Contains("crypt") => new Color(0.5f, 0f, 0.5f), // Purple for crypts
                var n when n.Contains("village") => new Color(0f, 1f, 0f), // Green for villages
                var n when n.Contains("ship") => new Color(1f, 1f, 0f), // Yellow for ships
                _ => new Color(1f, 1f, 1f) // White for other structures
            };
        }
    }
}
