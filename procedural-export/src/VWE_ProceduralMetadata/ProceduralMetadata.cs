using System;

namespace VWE_ProceduralMetadata
{
    /// <summary>
    /// Data structure containing Valheim's procedural world generation parameters
    /// </summary>
    [Serializable]
    public class ProceduralMetadata
    {
        public string WorldName { get; set; }
        public string Seed { get; set; }
        public long SeedHash { get; set; }
        public float WorldSize { get; set; }

        // Noise offsets (critical for reproduction)
        public NoiseOffsets Offsets { get; set; }

        // Noise generation parameters
        public NoiseParameters BaseNoise { get; set; }
        public NoiseParameters BiomeNoise { get; set; }

        // Biome configuration
        public BiomeThresholds Thresholds { get; set; }

        // Heightmap parameters
        public HeightmapParameters Heightmap { get; set; }

        public string ExportTimestamp { get; set; }
        public string ValheimVersion { get; set; }
    }

    [Serializable]
    public class NoiseOffsets
    {
        public float Offset0 { get; set; }  // m_offset0 - base height/swamp noise
        public float Offset1 { get; set; }  // m_offset1 - plains noise
        public float Offset2 { get; set; }  // m_offset2 - blackforest noise
        public float Offset3 { get; set; }  // m_offset3 - unused?
        public float Offset4 { get; set; }  // m_offset4 - mistlands noise
    }

    [Serializable]
    public class NoiseParameters
    {
        public int Octaves { get; set; }
        public float Frequency { get; set; }
        public float Amplitude { get; set; }
        public float Lacunarity { get; set; }
        public float Persistence { get; set; }
        public int Seed { get; set; }
    }

    [Serializable]
    public class BiomeThresholds
    {
        // Noise thresholds for biome detection
        public float SwampNoiseThreshold { get; set; }          // 0.6
        public float MistlandsNoiseThreshold { get; set; }      // minDarklandNoise
        public float PlainsNoiseThreshold { get; set; }         // 0.4
        public float BlackForestNoiseThreshold { get; set; }    // 0.4

        // Distance rings from world center
        public float SwampMinDist { get; set; }                 // 2000
        public float SwampMaxDist { get; set; }                 // maxMarshDistance
        public float BlackForestMinDist { get; set; }           // 600
        public float BlackForestMaxDist { get; set; }           // 6000
        public float PlainsMinDist { get; set; }                // 3000
        public float PlainsMaxDist { get; set; }                // 8000
        public float MistlandsMinDist { get; set; }             // 6000
        public float MistlandsMaxDist { get; set; }             // 10000
        public float BlackForestFallbackDist { get; set; }      // 5000

        // Height-based thresholds
        public float OceanLevel { get; set; }                   // 0.02
        public float MountainHeight { get; set; }               // 0.4
        public float SwampMinHeight { get; set; }               // 0.05
        public float SwampMaxHeight { get; set; }               // 0.25
        public float MinMountainDistance { get; set; }          // m_minMountainDistance
    }

    [Serializable]
    public class HeightmapParameters
    {
        public float BaseHeight { get; set; }
        public float MountainHeight { get; set; }
        public float OceanDepth { get; set; }
        public float HeightScale { get; set; }
    }
}
