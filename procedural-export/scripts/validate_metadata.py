#!/usr/bin/env python3
"""
Validation Script: Compare metadata-regenerated world data vs actual Valheim samples

This script:
1. Loads procedural metadata (seed, noise params, thresholds)
2. Implements Valheim's GetBiome and GetBaseHeight algorithms
3. Regenerates biome/height values for sample coordinates
4. Compares regenerated vs actual samples
5. Reports accuracy metrics and discrepancies
"""

import json
import math
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class NoiseParams:
    """Perlin noise parameters"""
    seed: int
    frequency: float
    amplitude: float
    octaves: int
    lacunarity: float
    persistence: float


@dataclass
class BiomeThresholds:
    """Biome detection thresholds"""
    swamp_noise_threshold: float
    mistlands_noise_threshold: float
    plains_noise_threshold: float
    blackforest_noise_threshold: float
    swamp_min_dist: float
    swamp_max_dist: float
    blackforest_min_dist: float
    blackforest_max_dist: float
    plains_min_dist: float
    plains_max_dist: float
    mistlands_min_dist: float
    mistlands_max_dist: float
    blackforest_fallback_dist: float
    ocean_level: float
    mountain_height: float
    swamp_min_height: float
    swamp_max_height: float
    min_mountain_distance: float


class PerlinNoise:
    """Simple Perlin noise implementation (matches Valheim's DUtils.PerlinNoise)"""

    @staticmethod
    def noise(x: float, y: float) -> float:
        """
        Basic Perlin noise using Python's math library
        Note: This is a simplified version - Valheim uses Unity's Mathf.PerlinNoise
        which has specific implementation details. We'll need to verify accuracy.
        """
        # Simple implementation using sine waves
        # This is a placeholder - may need to match Unity's exact implementation
        xi = int(math.floor(x))
        yi = int(math.floor(y))

        xf = x - xi
        yf = y - yi

        # Smooth interpolation
        u = xf * xf * (3.0 - 2.0 * xf)
        v = yf * yf * (3.0 - 2.0 * yf)

        # Hash coordinates
        def hash2d(x: int, y: int) -> float:
            n = x + y * 57
            n = (n << 13) ^ n
            return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)

        # Interpolate
        a = hash2d(xi, yi)
        b = hash2d(xi + 1, yi)
        c = hash2d(xi, yi + 1)
        d = hash2d(xi + 1, yi + 1)

        x1 = a + u * (b - a)
        x2 = c + u * (d - c)

        return (x1 + v * (x2 - x1) + 1.0) / 2.0


class ValheimWorldGenerator:
    """Reimplementation of Valheim's WorldGenerator algorithms"""

    def __init__(self, metadata: Dict):
        self.world_name = metadata['WorldName']
        self.seed = metadata['Seed']
        self.seed_hash = metadata['SeedHash']

        # Noise offsets (m_offset0, m_offset1, etc.)
        self.m_offset0 = float(metadata['BaseNoise']['Seed'])
        self.m_offset1 = float(metadata['BiomeNoise']['Seed'])
        self.m_offset2 = self.m_offset0 + 100.0  # Approximation for m_offset2
        self.m_offset4 = self.m_offset1 + 200.0  # Approximation for m_offset4

        # Thresholds
        t = metadata['Thresholds']
        self.thresholds = BiomeThresholds(
            swamp_noise_threshold=t['SwampNoiseThreshold'],
            mistlands_noise_threshold=t['MistlandsNoiseThreshold'],
            plains_noise_threshold=t['PlainsNoiseThreshold'],
            blackforest_noise_threshold=t['BlackForestNoiseThreshold'],
            swamp_min_dist=t['SwampMinDist'],
            swamp_max_dist=t['SwampMaxDist'],
            blackforest_min_dist=t['BlackForestMinDist'],
            blackforest_max_dist=t['BlackForestMaxDist'],
            plains_min_dist=t['PlainsMinDist'],
            plains_max_dist=t['PlainsMaxDist'],
            mistlands_min_dist=t['MistlandsMinDist'],
            mistlands_max_dist=t['MistlandsMaxDist'],
            blackforest_fallback_dist=t['BlackForestFallbackDist'],
            ocean_level=t['OceanLevel'],
            mountain_height=t['MountainHeight'],
            swamp_min_height=t['SwampMinHeight'],
            swamp_max_height=t['SwampMaxHeight'],
            min_mountain_distance=t['MinMountainDistance']
        )

        # Heightmap params
        h = metadata['Heightmap']
        self.base_height = h['BaseHeight']
        self.mountain_height = h['MountainHeight']
        self.ocean_depth = h['OceanDepth']

    def get_base_height(self, wx: float, wy: float) -> float:
        """
        Reimplementation of WorldGenerator.GetBaseHeight
        Based on decompiled source (lines 817-865)
        """
        distance = math.sqrt(wx * wx + wy * wy)

        # Offset coordinates
        x = wx + 100000.0 + self.m_offset0
        y = wy + 100000.0 + self.m_offset1

        # Layer 1: Large scale
        noise1 = PerlinNoise.noise(x * 0.001, y * 0.001)
        noise2 = PerlinNoise.noise(x * 0.0015, y * 0.0015)
        height = noise1 * noise2 * 1.0

        # Layer 2: Medium scale (self-modulating)
        noise3 = PerlinNoise.noise(x * 0.002, y * 0.002)
        noise4 = PerlinNoise.noise(x * 0.003, y * 0.003)
        height += noise3 * noise4 * height * 0.9

        # Layer 3: Fine scale (self-modulating)
        noise5 = PerlinNoise.noise(x * 0.005, y * 0.005)
        noise6 = PerlinNoise.noise(x * 0.01, y * 0.01)
        height += noise5 * noise6 * 0.5 * height

        # Baseline offset
        height -= 0.07

        # TODO: River cutting, edge dampening, mountain distance clamping
        # (Skipping for now - requires additional parameters)

        return height

    def get_biome(self, wx: float, wy: float) -> int:
        """
        Reimplementation of WorldGenerator.GetBiome
        Based on decompiled source (lines 752-810)

        Returns biome enum value:
        1=Meadows, 2=BlackForest, 4=Swamp, 8=Mountain, 16=Plains,
        32=Ocean, 64=Mistlands, 256=DeepNorth, 512=Ashlands
        """
        distance = math.sqrt(wx * wx + wy * wy)
        base_height = self.get_base_height(wx, wy)
        angle = math.atan2(wy, wx)
        angle_offset = angle * 100.0

        # Ocean check
        if base_height <= self.thresholds.ocean_level:
            return 32  # Ocean

        # Mountain check
        if base_height > self.thresholds.mountain_height:
            return 8  # Mountain

        # Swamp: noise + distance ring + height range
        swamp_noise = PerlinNoise.noise((self.m_offset0 + wx) * 0.001,
                                       (self.m_offset0 + wy) * 0.001)
        if (swamp_noise > self.thresholds.swamp_noise_threshold and
            distance > self.thresholds.swamp_min_dist and
            distance < self.thresholds.swamp_max_dist and
            base_height > self.thresholds.swamp_min_height and
            base_height < self.thresholds.swamp_max_height):
            return 4  # Swamp

        # Mistlands: m_offset4 noise + outer ring
        mistlands_noise = PerlinNoise.noise((self.m_offset4 + wx) * 0.001,
                                           (self.m_offset4 + wy) * 0.001)
        if (mistlands_noise > self.thresholds.mistlands_noise_threshold and
            distance > (self.thresholds.mistlands_min_dist + angle_offset) and
            distance < self.thresholds.mistlands_max_dist):
            return 64  # Mistlands

        # Plains: m_offset1 noise + mid-outer ring
        plains_noise = PerlinNoise.noise((self.m_offset1 + wx) * 0.001,
                                        (self.m_offset1 + wy) * 0.001)
        if (plains_noise > self.thresholds.plains_noise_threshold and
            distance > (self.thresholds.plains_min_dist + angle_offset) and
            distance < self.thresholds.plains_max_dist):
            return 16  # Plains

        # BlackForest: m_offset2 noise + mid ring
        blackforest_noise = PerlinNoise.noise((self.m_offset2 + wx) * 0.001,
                                             (self.m_offset2 + wy) * 0.001)
        if (blackforest_noise > self.thresholds.blackforest_noise_threshold and
            distance > (self.thresholds.blackforest_min_dist + angle_offset) and
            distance < self.thresholds.blackforest_max_dist):
            return 2  # BlackForest

        # BlackForest fallback for distant areas
        if distance > (self.thresholds.blackforest_fallback_dist + angle_offset):
            return 2  # BlackForest

        # Default
        return 1  # Meadows


def get_biome_name(biome_id: int) -> str:
    """Convert biome enum value to name"""
    biome_names = {
        1: "Meadows",
        2: "BlackForest",
        4: "Swamp",
        8: "Mountain",
        16: "Plains",
        32: "Ocean",
        64: "Mistlands",
        256: "DeepNorth",
        512: "Ashlands"
    }
    return biome_names.get(biome_id, f"Unknown({biome_id})")


def validate(metadata_path: str, samples_path: str, max_samples: int = 1000):
    """
    Validate metadata accuracy by comparing against actual samples

    Args:
        metadata_path: Path to procedural metadata JSON
        samples_path: Path to 512x512 samples JSON
        max_samples: Maximum number of samples to validate (for performance)
    """
    print("=" * 80)
    print("VALHEIM PROCEDURAL METADATA VALIDATION")
    print("=" * 80)

    # Load metadata
    print(f"\n[1/4] Loading metadata: {metadata_path}")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    print(f"  World: {metadata['WorldName']}")
    print(f"  Seed: {metadata['Seed']} (hash={metadata['SeedHash']})")

    # Load samples
    print(f"\n[2/4] Loading samples: {samples_path}")
    with open(samples_path, 'r') as f:
        samples_data = json.load(f)

    samples = samples_data['Samples']
    total_samples = len(samples)
    print(f"  Total samples: {total_samples:,}")
    print(f"  Resolution: {samples_data['Resolution']}x{samples_data['Resolution']}")

    # Limit samples for validation
    if max_samples < total_samples:
        print(f"  Validating first {max_samples:,} samples (for performance)")
        samples = samples[:max_samples]

    # Initialize world generator
    print(f"\n[3/4] Initializing world generator from metadata")
    wg = ValheimWorldGenerator(metadata)

    # Validate samples
    print(f"\n[4/4] Validating {len(samples):,} samples...")

    biome_matches = 0
    biome_mismatches = 0
    height_errors = []
    discrepancies = []

    progress_interval = max(1, len(samples) // 10)

    for i, sample in enumerate(samples):
        wx = sample['X']
        wz = sample['Z']
        actual_biome = sample['Biome']
        actual_height = sample['Height']

        # Regenerate from metadata
        regen_biome = wg.get_biome(wx, wz)
        regen_height = wg.get_base_height(wx, wz)

        # Compare biome
        if regen_biome == actual_biome:
            biome_matches += 1
        else:
            biome_mismatches += 1
            if len(discrepancies) < 20:  # Only store first 20
                discrepancies.append({
                    'x': wx,
                    'z': wz,
                    'actual_biome': get_biome_name(actual_biome),
                    'regen_biome': get_biome_name(regen_biome)
                })

        # Compare height (allow some error due to floating point)
        height_error = abs(regen_height - actual_height)
        height_errors.append(height_error)

        # Progress
        if (i + 1) % progress_interval == 0:
            percent = ((i + 1) / len(samples)) * 100
            print(f"  {percent:5.1f}% complete ({i+1:,}/{len(samples):,}) | "
                  f"Last: ({wx:.0f}, {wz:.0f}), "
                  f"actual={get_biome_name(actual_biome)}, "
                  f"regen={get_biome_name(regen_biome)}, "
                  f"Δh={height_error:.2f}m")

    # Results
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    biome_accuracy = (biome_matches / len(samples)) * 100
    avg_height_error = sum(height_errors) / len(height_errors)
    max_height_error = max(height_errors)

    print(f"\nBiome Accuracy:")
    print(f"  Matches:     {biome_matches:,} ({biome_accuracy:.2f}%)")
    print(f"  Mismatches:  {biome_mismatches:,} ({100-biome_accuracy:.2f}%)")

    print(f"\nHeight Error:")
    print(f"  Average:     {avg_height_error:.2f}m")
    print(f"  Maximum:     {max_height_error:.2f}m")

    if discrepancies:
        print(f"\nFirst {len(discrepancies)} Biome Discrepancies:")
        for d in discrepancies[:10]:
            print(f"  ({d['x']:.0f}, {d['z']:.0f}): "
                  f"actual={d['actual_biome']}, regen={d['regen_biome']}")

    # Assessment
    print("\n" + "=" * 80)
    if biome_accuracy >= 99.9:
        print("✓ EXCELLENT: Metadata accuracy ≥99.9% - ready for production")
    elif biome_accuracy >= 99.0:
        print("✓ GOOD: Metadata accuracy ≥99% - acceptable for most use cases")
    elif biome_accuracy >= 95.0:
        print("⚠ FAIR: Metadata accuracy ≥95% - needs refinement")
    else:
        print("✗ POOR: Metadata accuracy <95% - requires investigation")
        print("\nLikely issues:")
        print("  - Perlin noise implementation doesn't match Unity's Mathf.PerlinNoise")
        print("  - Missing offset parameters (m_offset2, m_offset4)")
        print("  - Incomplete algorithm implementation (rivers, edge dampening)")
    print("=" * 80)

    return {
        'biome_accuracy': biome_accuracy,
        'avg_height_error': avg_height_error,
        'max_height_error': max_height_error
    }


if __name__ == '__main__':
    metadata_path = 'output/metadata/hkLycKKCMI-procedural-v2.json'
    samples_path = 'output/samples/hkLycKKCMI-samples-512.json'

    if len(sys.argv) > 1:
        metadata_path = sys.argv[1]
    if len(sys.argv) > 2:
        samples_path = sys.argv[2]

    validate(metadata_path, samples_path, max_samples=10000)
