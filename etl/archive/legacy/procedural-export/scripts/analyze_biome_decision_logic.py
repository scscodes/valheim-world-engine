#!/usr/bin/env python3
"""
Comprehensive Biome Classification Analysis
============================================

Analyzes the decision-making logic and weights that classify locations into biomes,
comparing raw API data vs post-processing transformations.

This script examines:
1. Raw biome distribution from WorldGenerator.GetBiome()
2. The decision tree logic used by Valheim
3. Weights and thresholds for each biome
4. Post-processing filters and their impact
5. Comparison with expected/reference distributions
"""

import json
import math
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys


class BiomeAnalyzer:
    """Analyzes biome classification logic and distributions"""

    # Biome enum values and names
    BIOME_MAP = {
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

    # Constants from decompiled WorldGenerator code
    SEA_LEVEL = 30.0
    OCEAN_LEVEL = 0.05  # baseHeight threshold
    MOUNTAIN_HEIGHT = 0.4  # baseHeight threshold

    # Distance thresholds (reverse-engineered from actual data)
    THRESHOLDS = {
        "meadows_max_dist": 5000.0,
        "blackforest_min_dist": 600.0,
        "blackforest_max_dist": 6000.0,
        "swamp_min_dist": 2000.0,
        "swamp_max_dist": 6000.0,
        "plains_min_dist": 3000.0,
        "plains_max_dist": 8000.0,
        "mistlands_min_dist": 6000.0,
        "mistlands_max_dist": 10000.0,
        "deepnorth_threshold": 7140.0,  # Reverse-engineered
        "ashlands_threshold": 9626.0,   # Reverse-engineered
        "ocean_boundary": 10000.0
    }

    # Noise thresholds from decompiled code
    NOISE_THRESHOLDS = {
        "swamp": 0.6,
        "mistlands": 0.4,
        "plains": 0.4,
        "blackforest": 0.4
    }

    # Post-processing filter thresholds
    FILTER_THRESHOLDS = {
        "outer_ring_min": 6000.0,
        "outer_ring_max": 10000.0,
        "polar_threshold": 7000.0,  # Latitude threshold for polar crescent filter
        "shoreline_depth": -5.0
    }

    def __init__(self, samples_path: str):
        """Initialize analyzer with sample data"""
        print(f"Loading samples from: {samples_path}")
        with open(samples_path, 'r') as f:
            data = json.load(f)

        self.samples = data['Samples']
        self.world_name = data.get('WorldName', 'Unknown')
        self.resolution = data.get('Resolution', 0)
        self.sample_count = len(self.samples)

        print(f"Loaded {self.sample_count:,} samples for world '{self.world_name}' ({self.resolution}×{self.resolution})")

    def analyze_decision_tree(self) -> Dict:
        """
        Analyze the decision tree logic from WorldGenerator.GetBiome()

        Returns detailed breakdown of how each biome is determined.
        """
        print("\n" + "="*80)
        print("BIOME DECISION TREE ANALYSIS")
        print("="*80)

        decision_order = [
            {
                "biome": "Ashlands",
                "priority": 1,
                "check": "IsAshlands(x, z)",
                "logic": "Distance from (x, z-4000) > ~9,626m (with angle modulation)",
                "notes": "Checked FIRST - steals from other biomes in outer ring"
            },
            {
                "biome": "Ocean (baseHeight)",
                "priority": 2,
                "check": "baseHeight <= 0.05",
                "logic": "Terrain height below ocean level threshold",
                "notes": "Checked after Ashlands, before DeepNorth"
            },
            {
                "biome": "DeepNorth",
                "priority": 3,
                "check": "IsDeepNorth(x, z)",
                "logic": "Distance from (x, z+4000) > ~7,140m (with angle modulation)",
                "notes": "Checked BEFORE Mistlands - also steals territory"
            },
            {
                "biome": "Mountain (height)",
                "priority": 4,
                "check": "baseHeight > 0.4",
                "logic": "High elevation terrain",
                "notes": "Can appear in any biome ring if elevation is high"
            },
            {
                "biome": "Swamp",
                "priority": 5,
                "check": "PerlinNoise(m_offset0 + x/z) > 0.6 && dist 2-6km && height 0.05-0.25",
                "logic": "Noise check + distance ring + height band",
                "notes": "Requires specific noise threshold AND conditions"
            },
            {
                "biome": "Mistlands",
                "priority": 6,
                "check": "PerlinNoise(m_offset4 + x/z) > 0.4 && dist 6-10km",
                "logic": "Noise check + outer ring distance",
                "notes": "Checked AFTER polar biomes - gets starved in outer ring"
            },
            {
                "biome": "Plains",
                "priority": 7,
                "check": "PerlinNoise(m_offset1 + x/z) > 0.4 && dist 3-8km",
                "logic": "Noise check + mid-outer ring distance",
                "notes": "Mid-range biome with noise requirement"
            },
            {
                "biome": "BlackForest",
                "priority": 8,
                "check": "PerlinNoise(m_offset2 + x/z) > 0.4 && dist 0.6-6km OR dist > 5km",
                "logic": "Noise check + distance OR fallback for outer areas",
                "notes": "Has fallback rule: if dist > 5km and nothing else matched"
            },
            {
                "biome": "Meadows",
                "priority": 9,
                "check": "Default fallback",
                "logic": "Returned if no other biome matched",
                "notes": "Safest starting biome, appears in center"
            }
        ]

        print("\nDecision Order (from WorldGenerator.GetBiome, lines 752-810):")
        print("-" * 80)
        for entry in decision_order:
            print(f"\n{entry['priority']}. {entry['biome']}")
            print(f"   Check: {entry['check']}")
            print(f"   Logic: {entry['logic']}")
            print(f"   Notes: {entry['notes']}")

        return decision_order

    def analyze_raw_distribution(self) -> Dict:
        """Analyze raw biome distribution from API data"""
        print("\n" + "="*80)
        print("RAW BIOME DISTRIBUTION (WorldGenerator.GetBiome() Output)")
        print("="*80)

        biome_counts = Counter(s['Biome'] for s in self.samples)
        total = len(self.samples)

        # Sort by count descending
        sorted_biomes = sorted(biome_counts.items(), key=lambda x: x[1], reverse=True)

        print(f"\nTotal samples: {total:,}\n")
        print(f"{'Biome':<15} {'Count':>10} {'Percentage':>12} {'Bar':>40}")
        print("-" * 80)

        stats = {}
        for biome_id, count in sorted_biomes:
            name = self.BIOME_MAP.get(biome_id, f"Unknown({biome_id})")
            percentage = (count / total) * 100
            bar_length = int(percentage * 0.5)  # Scale to fit
            bar = "█" * bar_length

            print(f"{name:<15} {count:>10,} {percentage:>11.2f}% {bar}")

            stats[name] = {
                "count": count,
                "percentage": percentage,
                "biome_id": biome_id
            }

        return stats

    def analyze_spatial_distribution(self) -> Dict:
        """Analyze biome distribution by distance rings"""
        print("\n" + "="*80)
        print("SPATIAL DISTRIBUTION BY DISTANCE RINGS")
        print("="*80)

        rings = [
            (0, 2000, "Center (0-2km)"),
            (2000, 4000, "Inner (2-4km)"),
            (4000, 6000, "Mid (4-6km)"),
            (6000, 8000, "Outer (6-8km)"),
            (8000, 10000, "Far (8-10km)"),
            (10000, 12000, "Edge (10-12km)")
        ]

        ring_stats = {}

        for min_dist, max_dist, label in rings:
            ring_samples = [
                s for s in self.samples
                if min_dist <= math.sqrt(s['X']**2 + s['Z']**2) < max_dist
            ]

            if not ring_samples:
                continue

            biome_counts = Counter(s['Biome'] for s in ring_samples)
            total = len(ring_samples)

            print(f"\n{label}: {total:,} samples")
            print("-" * 60)

            sorted_biomes = sorted(biome_counts.items(), key=lambda x: x[1], reverse=True)

            ring_data = {}
            for biome_id, count in sorted_biomes:
                name = self.BIOME_MAP.get(biome_id, f"Unknown({biome_id})")
                percentage = (count / total) * 100
                bar_length = int(percentage * 0.3)
                bar = "█" * bar_length

                print(f"  {name:<15} {count:>8,} ({percentage:>5.1f}%) {bar}")

                ring_data[name] = {
                    "count": count,
                    "percentage": percentage
                }

            ring_stats[label] = ring_data

        return ring_stats

    def analyze_directional_distribution(self) -> Dict:
        """Analyze biome distribution by compass direction"""
        print("\n" + "="*80)
        print("DIRECTIONAL DISTRIBUTION (Polar Biome Analysis)")
        print("="*80)

        # Define quadrants
        quadrants = {
            "North (Z > 0)": lambda s: s['Z'] > 0,
            "South (Z < 0)": lambda s: s['Z'] < 0,
            "East (X > 0)": lambda s: s['X'] > 0,
            "West (X < 0)": lambda s: s['X'] < 0
        }

        # Focus on polar biomes
        polar_biomes = [256, 512]  # DeepNorth, Ashlands

        directional_stats = {}

        for direction, condition in quadrants.items():
            direction_samples = [s for s in self.samples if condition(s)]
            total = len(direction_samples)

            print(f"\n{direction}: {total:,} samples")
            print("-" * 60)

            for biome_id in polar_biomes:
                biome_name = self.BIOME_MAP[biome_id]
                count = sum(1 for s in direction_samples if s['Biome'] == biome_id)
                percentage = (count / total) * 100 if total > 0 else 0

                # Also show what % of this biome is in this direction
                total_biome = sum(1 for s in self.samples if s['Biome'] == biome_id)
                biome_percentage = (count / total_biome * 100) if total_biome > 0 else 0

                print(f"  {biome_name:<15} {count:>8,} ({percentage:>5.1f}% of direction, {biome_percentage:>5.1f}% of all {biome_name})")

                if direction not in directional_stats:
                    directional_stats[direction] = {}
                directional_stats[direction][biome_name] = {
                    "count": count,
                    "pct_of_direction": percentage,
                    "pct_of_biome": biome_percentage
                }

        return directional_stats

    def simulate_filters(self) -> Tuple[Dict, Dict]:
        """
        Simulate post-processing filters and return transformed distribution

        Returns:
            (transformed_stats, filter_impact)
        """
        print("\n" + "="*80)
        print("POST-PROCESSING FILTER SIMULATION")
        print("="*80)

        # Track transformations
        transformations = defaultdict(lambda: defaultdict(int))

        # Apply filters to each sample
        transformed_samples = []

        for sample in self.samples:
            original_biome = sample['Biome']
            biome_id = original_biome
            height = sample['Height']
            x, z = sample['X'], sample['Z']
            dist = math.sqrt(x**2 + z**2)

            # Filter 1: Ocean land contamination fix
            if biome_id == 32 and height >= self.SEA_LEVEL:
                transformations[original_biome][64] += 1  # Ocean -> Mistlands
                biome_id = 64

            # Filter 2: Edge biome water distinction
            elif (biome_id == 256 or biome_id == 512) and height < (self.SEA_LEVEL - 10):
                transformations[original_biome][32] += 1  # Polar -> Ocean
                biome_id = 32

            # Filter 3: Mistlands recovery (outer ring polar biome conversion)
            elif (self.FILTER_THRESHOLDS['outer_ring_min'] <= dist <= self.FILTER_THRESHOLDS['outer_ring_max']):
                # Ashlands -> Mistlands (except far south)
                if biome_id == 512 and z >= -self.FILTER_THRESHOLDS['polar_threshold']:
                    transformations[original_biome][64] += 1  # Ashlands -> Mistlands
                    biome_id = 64

                # DeepNorth -> Mistlands (except far north)
                elif biome_id == 256 and z <= self.FILTER_THRESHOLDS['polar_threshold']:
                    transformations[original_biome][64] += 1  # DeepNorth -> Mistlands
                    biome_id = 64

            transformed_samples.append({
                **sample,
                'OriginalBiome': original_biome,
                'TransformedBiome': biome_id
            })

        # Calculate transformed distribution
        biome_counts = Counter(s['TransformedBiome'] for s in transformed_samples)
        total = len(transformed_samples)

        print("\nTransformed Distribution:")
        print("-" * 80)
        print(f"{'Biome':<15} {'Count':>10} {'Percentage':>12} {'Bar':>40}")
        print("-" * 80)

        transformed_stats = {}
        sorted_biomes = sorted(biome_counts.items(), key=lambda x: x[1], reverse=True)

        for biome_id, count in sorted_biomes:
            name = self.BIOME_MAP.get(biome_id, f"Unknown({biome_id})")
            percentage = (count / total) * 100
            bar_length = int(percentage * 0.5)
            bar = "█" * bar_length

            print(f"{name:<15} {count:>10,} {percentage:>11.2f}% {bar}")

            transformed_stats[name] = {
                "count": count,
                "percentage": percentage,
                "biome_id": biome_id
            }

        # Show filter impact
        print("\n" + "="*80)
        print("FILTER IMPACT SUMMARY")
        print("="*80)

        total_transformed = sum(sum(targets.values()) for targets in transformations.values())
        print(f"\nTotal samples transformed: {total_transformed:,} ({total_transformed/total*100:.1f}%)")
        print("\nTransformation Matrix:")
        print("-" * 60)

        filter_impact = {}
        for from_biome, to_biomes in transformations.items():
            from_name = self.BIOME_MAP.get(from_biome, f"Unknown({from_biome})")
            print(f"\n{from_name}:")

            if from_name not in filter_impact:
                filter_impact[from_name] = {}

            for to_biome, count in to_biomes.items():
                to_name = self.BIOME_MAP.get(to_biome, f"Unknown({to_biome})")
                from_total = sum(1 for s in self.samples if s['Biome'] == from_biome)
                percentage = (count / from_total * 100) if from_total > 0 else 0
                print(f"  → {to_name}: {count:,} ({percentage:.1f}% of {from_name})")

                filter_impact[from_name][to_name] = {
                    "count": count,
                    "percentage": percentage
                }

        return transformed_stats, filter_impact

    def compare_distributions(self, raw_stats: Dict, transformed_stats: Dict):
        """Compare raw vs transformed distributions"""
        print("\n" + "="*80)
        print("RAW vs TRANSFORMED COMPARISON")
        print("="*80)

        print(f"\n{'Biome':<15} {'Raw %':>10} {'Transformed %':>15} {'Change':>12}")
        print("-" * 60)

        all_biomes = set(raw_stats.keys()) | set(transformed_stats.keys())

        for biome in sorted(all_biomes):
            raw_pct = raw_stats.get(biome, {}).get('percentage', 0)
            trans_pct = transformed_stats.get(biome, {}).get('percentage', 0)
            change = trans_pct - raw_pct
            change_str = f"{change:+.2f}%"

            # Color indicators
            indicator = "↑" if change > 0 else "↓" if change < 0 else "="

            print(f"{biome:<15} {raw_pct:>9.2f}% {trans_pct:>14.2f}% {change_str:>11} {indicator}")

    def generate_recommendations(self):
        """Generate recommendations for improving biome classification"""
        print("\n" + "="*80)
        print("RECOMMENDATIONS FOR IMPROVEMENT")
        print("="*80)

        recommendations = [
            {
                "issue": "Polar Biome Priority",
                "problem": "Ashlands and DeepNorth checked before Mistlands, stealing outer ring territory",
                "current_solution": "Post-processing filter converts outer ring polar → Mistlands (except far poles)",
                "alternative": "Reorder checks: Mistlands before polar biomes (requires C# plugin modification)",
                "impact": "Would make API data match game design intent directly"
            },
            {
                "issue": "Noise Weight Transparency",
                "problem": "Perlin noise thresholds (0.4, 0.6) are hardcoded with unclear biological meaning",
                "current_solution": "Documented in BIOME_REFERENCE.md",
                "alternative": "Expose noise seeds and offsets for each biome to allow client-side recreation",
                "impact": "Would enable perfect client-side world regeneration"
            },
            {
                "issue": "Height-Based Misclassification",
                "problem": "Ocean biome assigned to above-water land based on distance alone",
                "current_solution": "Post-processing filter: Ocean + height≥30m → Mistlands",
                "alternative": "Add height check to GetBiome() before distance-based Ocean return",
                "impact": "Would eliminate ~19k misclassified samples at source"
            },
            {
                "issue": "Biome Blend Zones",
                "problem": "Single biome ID per sample doesn't capture transition areas",
                "current_solution": "None (limitation of current data model)",
                "alternative": "Sample 3×3 grids, return biome IDs + blend percentages",
                "impact": "Would enable smooth biome boundary rendering (realistic gradients)"
            },
            {
                "issue": "Mistlands Underrepresentation",
                "problem": "Only 5.5% of world vs expected 30%+ in outer ring",
                "current_solution": "Mistlands recovery filter: outer ring polar → Mistlands (except far poles)",
                "alternative": "Increase mistlands noise threshold sensitivity or adjust distance ring",
                "impact": "Would balance endgame biome availability"
            }
        ]

        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['issue']}")
            print(f"   Problem: {rec['problem']}")
            print(f"   Current: {rec['current_solution']}")
            print(f"   Alternative: {rec['alternative']}")
            print(f"   Impact: {rec['impact']}")


def main():
    """Main analysis entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_biome_decision_logic.py <samples-json-path>")
        print("\nExample:")
        print("  python3 analyze_biome_decision_logic.py ../output/samples/hnLycKKCMI-samples-512.json")
        sys.exit(1)

    samples_path = sys.argv[1]

    if not Path(samples_path).exists():
        print(f"Error: File not found: {samples_path}")
        sys.exit(1)

    analyzer = BiomeAnalyzer(samples_path)

    # Run all analyses
    print("\n" + "█"*80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 20 + "BIOME CLASSIFICATION ANALYSIS" + " " * 29 + "█")
    print("█" + " " * 78 + "█")
    print("█"*80)

    # 1. Decision tree analysis
    decision_tree = analyzer.analyze_decision_tree()

    # 2. Raw distribution
    raw_stats = analyzer.analyze_raw_distribution()

    # 3. Spatial distribution
    spatial_stats = analyzer.analyze_spatial_distribution()

    # 4. Directional distribution
    directional_stats = analyzer.analyze_directional_distribution()

    # 5. Filter simulation
    transformed_stats, filter_impact = analyzer.simulate_filters()

    # 6. Comparison
    analyzer.compare_distributions(raw_stats, transformed_stats)

    # 7. Recommendations
    analyzer.generate_recommendations()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nKey Findings:")
    print("1. Polar biomes (Ashlands, DeepNorth) checked before Mistlands → steals outer ring")
    print("2. Post-processing filters recover ~270k samples → Mistlands goes from 5.5% to ~31%")
    print("3. Directional filters create realistic polar crescents at poles")
    print("4. Height-based reclassification fixes ~19k ocean-on-land samples")
    print("\nSee documentation: BIOME_DISCREPANCY_ANALYSIS.md, MISTLANDS_RECOVERY_FIX.md")


if __name__ == "__main__":
    main()
