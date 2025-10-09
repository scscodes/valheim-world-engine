using System;
using System.Collections;
using System.Collections.Generic;
using BepInEx.Logging;
using Newtonsoft.Json;

namespace VWE_ProceduralMetadata
{
    /// <summary>
    /// Samples world data at optimal 512x512 resolution for best UX
    /// 88 seconds vs 1400 seconds for 2048x2048 (16x faster)
    /// </summary>
    public class OptimalSampler
    {
        private readonly ManualLogSource _logger;
        private readonly int _resolution;

        public OptimalSampler(ManualLogSource logger, int resolution = 512)
        {
            _logger = logger;
            _resolution = resolution;
        }

        public IEnumerator SampleWorld(string exportPath, string worldName)
        {
            var startTime = DateTime.Now;
            _logger.LogInfo($"★★★ OptimalSampler: START - resolution={_resolution}, world={worldName}");

            if (WorldGenerator.instance == null)
            {
                _logger.LogError("★★★ OptimalSampler: WorldGenerator.instance is NULL");
                yield break;
            }

            var samples = new OptimalWorldSamples
            {
                WorldName = worldName,
                Resolution = _resolution,
                WorldSize = 20000f,
                Samples = new List<WorldSample>()
            };

            var worldSize = 20000f;
            var stepSize = worldSize / _resolution;
            var totalSamples = _resolution * _resolution;
            var samplesProcessed = 0;
            var lastLoggedPercent = 0;
            var yieldCount = 0;

            _logger.LogInfo($"★★★ OptimalSampler: Sampling {totalSamples} points, stepSize={stepSize:F2}");

            for (int x = 0; x < _resolution; x++)
            {
                for (int z = 0; z < _resolution; z++)
                {
                    try
                    {
                        var worldX = (x * stepSize) - (worldSize / 2);
                        var worldZ = (z * stepSize) - (worldSize / 2);

                        var biome = WorldGenerator.instance.GetBiome(worldX, worldZ);
                        var height = WorldGenerator.instance.GetHeight(worldX, worldZ);

                        samples.Samples.Add(new WorldSample
                        {
                            X = worldX,
                            Z = worldZ,
                            Biome = (int)biome,
                            Height = height
                        });

                        samplesProcessed++;

                        // Log progress every 10%
                        var percentComplete = (samplesProcessed * 100) / totalSamples;
                        if (percentComplete >= lastLoggedPercent + 10)
                        {
                            var elapsed = (DateTime.Now - startTime).TotalSeconds;
                            var samplesPerSec = samplesProcessed / elapsed;
                            var biomeName = GetBiomeName(biome);
                            _logger.LogInfo($"★★★ OptimalSampler: {percentComplete}% complete ({samplesProcessed}/{totalSamples}, {elapsed:F1}s, {samplesPerSec:F0} samples/sec) | Last: ({worldX:F0}, {worldZ:F0}), {biomeName}, {height:F1}m");
                            lastLoggedPercent = percentComplete;
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"★★★ OptimalSampler: Error at x={x}, z={z}: {ex.Message}");
                    }

                    // Yield every 100 samples
                    if (samplesProcessed % 100 == 0)
                    {
                        yieldCount++;
                        yield return null;
                    }
                }
            }

            _logger.LogInfo($"★★★ OptimalSampler: Sampling complete - {samplesProcessed} samples, {yieldCount} yields");

            // Export to JSON
            try
            {
                var jsonPath = System.IO.Path.Combine(exportPath, $"{worldName}-samples-{_resolution}.json");
                samples.ExportTimestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
                samples.SampleCount = samples.Samples.Count;

                var json = JsonConvert.SerializeObject(samples, Formatting.Indented);
                System.IO.File.WriteAllText(jsonPath, json);

                var fileSize = new System.IO.FileInfo(jsonPath).Length;
                var totalTime = (DateTime.Now - startTime).TotalSeconds;
                _logger.LogInfo($"★★★ OptimalSampler: COMPLETE - {totalTime:F1}s, exported to {jsonPath} ({fileSize / 1024}KB)");
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ OptimalSampler: Export failed: {ex.Message}");
            }
        }

        private string GetBiomeName(Heightmap.Biome biome)
        {
            return biome switch
            {
                Heightmap.Biome.Meadows => "Meadows",
                Heightmap.Biome.BlackForest => "BlackForest",
                Heightmap.Biome.Swamp => "Swamp",
                Heightmap.Biome.Mountain => "Mountain",
                Heightmap.Biome.Plains => "Plains",
                Heightmap.Biome.Ocean => "Ocean",
                Heightmap.Biome.Mistlands => "Mistlands",
                Heightmap.Biome.DeepNorth => "DeepNorth",
                Heightmap.Biome.AshLands => "Ashlands",
                _ => "Unknown"
            };
        }
    }

    [Serializable]
    public class OptimalWorldSamples
    {
        public string WorldName { get; set; }
        public int Resolution { get; set; }
        public float WorldSize { get; set; }
        public int SampleCount { get; set; }
        public string ExportTimestamp { get; set; }
        public List<WorldSample> Samples { get; set; }
    }

    [Serializable]
    public class WorldSample
    {
        public float X { get; set; }
        public float Z { get; set; }
        public int Biome { get; set; }
        public float Height { get; set; }
    }
}
