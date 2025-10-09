using System;
using System.Reflection;
using BepInEx.Logging;

namespace VWE_ProceduralMetadata
{
    /// <summary>
    /// Uses C# reflection to extract Valheim's WorldGenerator internal parameters
    /// </summary>
    public class WorldGeneratorReflector
    {
        private readonly ManualLogSource _logger;
        private readonly WorldGenerator _worldGenerator;

        public WorldGeneratorReflector(ManualLogSource logger)
        {
            _logger = logger;
            _worldGenerator = WorldGenerator.instance;

            if (_worldGenerator == null)
            {
                throw new InvalidOperationException("WorldGenerator.instance is null - world not initialized yet");
            }
        }

        public ProceduralMetadata ExtractMetadata()
        {
            _logger.LogInfo("★★★ ProceduralMetadata: Starting WorldGenerator reflection");

            var metadata = new ProceduralMetadata
            {
                WorldName = GetWorldName(),
                Seed = GetSeed(),
                SeedHash = GetSeedHash(),
                WorldSize = 20000f, // Valheim actual world size (20km diameter)
                ExportTimestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                ValheimVersion = GetValheimVersion()
            };

            _logger.LogInfo($"★★★ ProceduralMetadata: Seed={metadata.Seed}, Hash={metadata.SeedHash}");

            // Extract noise offsets (CRITICAL for exact reproduction)
            metadata.Offsets = ExtractNoiseOffsets();

            // Extract noise parameters via reflection
            metadata.BaseNoise = ExtractNoiseParameters("m_offset0");
            metadata.BiomeNoise = ExtractNoiseParameters("m_offset1");

            // Extract biome thresholds
            metadata.Thresholds = ExtractBiomeThresholds();

            // Extract heightmap parameters
            metadata.Heightmap = ExtractHeightmapParameters();

            _logger.LogInfo("★★★ ProceduralMetadata: Extraction complete");
            return metadata;
        }

        private string GetWorldName()
        {
            try
            {
                var world = GetPrivateField<World>(_worldGenerator, "m_world");
                return world?.m_name ?? "Unknown";
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"Could not extract world name: {ex.Message}");
                return "Unknown";
            }
        }

        private string GetSeed()
        {
            try
            {
                var world = GetPrivateField<World>(_worldGenerator, "m_world");
                return world?.m_seedName ?? "";
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"Could not extract seed: {ex.Message}");
                return "";
            }
        }

        private long GetSeedHash()
        {
            try
            {
                var world = GetPrivateField<World>(_worldGenerator, "m_world");
                return world?.m_seed ?? 0;
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"Could not extract seed hash: {ex.Message}");
                return 0;
            }
        }

        private string GetValheimVersion()
        {
            // Version class is internal/private in Valheim assemblies
            return "Unknown";
        }

        private NoiseOffsets ExtractNoiseOffsets()
        {
            try
            {
                var offsets = new NoiseOffsets
                {
                    Offset0 = GetPrivateField<float>(_worldGenerator, "m_offset0"),
                    Offset1 = GetPrivateField<float>(_worldGenerator, "m_offset1"),
                    Offset2 = GetPrivateField<float>(_worldGenerator, "m_offset2"),
                    Offset3 = GetPrivateField<float>(_worldGenerator, "m_offset3"),
                    Offset4 = GetPrivateField<float>(_worldGenerator, "m_offset4")
                };

                _logger.LogInfo($"★★★ ProceduralMetadata: Extracted offsets - " +
                    $"m_offset0={offsets.Offset0:F1}, " +
                    $"m_offset1={offsets.Offset1:F1}, " +
                    $"m_offset2={offsets.Offset2:F1}, " +
                    $"m_offset3={offsets.Offset3:F1}, " +
                    $"m_offset4={offsets.Offset4:F1}");

                return offsets;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Could not extract noise offsets: {ex.Message}");
                return new NoiseOffsets();
            }
        }

        private NoiseParameters ExtractNoiseParameters(string offsetFieldName)
        {
            try
            {
                var offset = GetPrivateField<float>(_worldGenerator, offsetFieldName);

                // Attempt to find noise-related fields
                // Note: These may not exist as direct fields - WorldGenerator might use
                // methods/formulas instead. This is exploratory.

                return new NoiseParameters
                {
                    Seed = (int)offset,
                    Octaves = TryGetPrivateField<int>(_worldGenerator, "m_octaves", 4), // Default fallback
                    Frequency = TryGetPrivateField<float>(_worldGenerator, "m_frequency", 0.01f),
                    Amplitude = TryGetPrivateField<float>(_worldGenerator, "m_amplitude", 1.0f),
                    Lacunarity = 2.0f, // Common default
                    Persistence = 0.5f  // Common default
                };
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"Could not extract noise parameters for {offsetFieldName}: {ex.Message}");
                return new NoiseParameters { Seed = 0 };
            }
        }

        private BiomeThresholds ExtractBiomeThresholds()
        {
            _logger.LogInfo("★★★ ProceduralMetadata: Extracting biome thresholds from WorldGenerator fields");

            return new BiomeThresholds
            {
                // Noise thresholds (hardcoded in GetBiome)
                SwampNoiseThreshold = 0.6f,
                MistlandsNoiseThreshold = TryGetPrivateField(_worldGenerator, "minDarklandNoise", 0.4f),
                PlainsNoiseThreshold = 0.4f,
                BlackForestNoiseThreshold = 0.4f,

                // Distance rings
                SwampMinDist = 2000f,
                SwampMaxDist = TryGetPrivateField(_worldGenerator, "maxMarshDistance", 6000f),
                BlackForestMinDist = 600f,
                BlackForestMaxDist = 6000f,
                PlainsMinDist = 3000f,
                PlainsMaxDist = 8000f,
                MistlandsMinDist = 6000f,
                MistlandsMaxDist = 10000f,
                BlackForestFallbackDist = 5000f,

                // Height thresholds
                OceanLevel = 0.02f,
                MountainHeight = 0.4f,
                SwampMinHeight = 0.05f,
                SwampMaxHeight = 0.25f,
                MinMountainDistance = TryGetPrivateField(_worldGenerator, "m_minMountainDistance", 1000f)
            };
        }

        private HeightmapParameters ExtractHeightmapParameters()
        {
            return new HeightmapParameters
            {
                BaseHeight = TryGetPrivateField<float>(_worldGenerator, "m_baseHeight", 30.0f),
                MountainHeight = TryGetPrivateField<float>(_worldGenerator, "m_mountainHeight", 200.0f),
                OceanDepth = TryGetPrivateField<float>(_worldGenerator, "m_oceanDepth", 50.0f),
                HeightScale = 1.0f
            };
        }

        // Helper: Get private field with exception handling
        private T GetPrivateField<T>(object obj, string fieldName)
        {
            var type = obj.GetType();
            var field = type.GetField(fieldName, BindingFlags.NonPublic | BindingFlags.Instance);

            if (field == null)
                throw new FieldAccessException($"Field '{fieldName}' not found in {type.Name}");

            return (T)field.GetValue(obj);
        }

        // Helper: Try get private field with default fallback
        private T TryGetPrivateField<T>(object obj, string fieldName, T defaultValue)
        {
            try
            {
                return GetPrivateField<T>(obj, fieldName);
            }
            catch
            {
                return defaultValue;
            }
        }
    }
}
