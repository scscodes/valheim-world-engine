#!/usr/bin/env python3
"""
Reverse engineer actual biome thresholds from sample data
"""

import json
import math
from collections import defaultdict

def world_angle(x, y):
    return math.sin(math.atan2(x, y) * 20.0)

def analyze_thresholds(sample_file):
    with open(sample_file, 'r') as f:
        data = json.load(f)

    # Collect boundary samples
    deepnorth_distances = []
    ashlands_distances = []
    not_deepnorth_distances = []
    not_ashlands_distances = []

    for sample in data['Samples']:
        x, z = sample['X'], sample['Z']
        biome = sample['Biome']

        # DeepNorth analysis
        angle_mod = world_angle(x, z) * 100.0
        dn_dist = math.sqrt(x**2 + (z + 4000)**2)
        dn_threshold = dn_dist - angle_mod

        if biome == 256:  # DeepNorth
            deepnorth_distances.append((dn_dist, dn_threshold, x, z))
        elif biome != 8:  # Not Mountain (which can appear in DN zones)
            not_deepnorth_distances.append((dn_dist, dn_threshold, x, z))

        # Ashlands analysis
        ash_dist = math.sqrt(x**2 + (z - 4000)**2)
        ash_threshold = ash_dist - angle_mod

        if biome == 512:  # Ashlands
            ashlands_distances.append((ash_dist, ash_threshold, x, z))
        else:
            not_ashlands_distances.append((ash_dist, ash_threshold, x, z))

    print("=" * 80)
    print("REVERSE ENGINEERED BIOME THRESHOLDS")
    print("=" * 80)

    # Find minimum DeepNorth threshold
    if deepnorth_distances:
        min_dn = min(deepnorth_distances, key=lambda x: x[1])
        max_not_dn = max(not_deepnorth_distances, key=lambda x: x[1]) if not_deepnorth_distances else (0, 0, 0, 0)

        print(f"\n🔍 DEEPNORTH THRESHOLD:")
        print(f"   Decompiled constant: 12000.0")
        print(f"   Minimum DeepNorth sample: {min_dn[1]:.1f} at ({min_dn[2]:.0f}, {min_dn[3]:.0f})")
        print(f"   Maximum non-DeepNorth: {max_not_dn[1]:.1f} at ({max_not_dn[2]:.0f}, {max_not_dn[3]:.0f})")
        print(f"   **ACTUAL THRESHOLD appears to be: ~{(min_dn[1] + max_not_dn[1])/2:.0f}**")

    # Find minimum Ashlands threshold
    if ashlands_distances:
        min_ash = min(ashlands_distances, key=lambda x: x[1])
        max_not_ash = max(not_ashlands_distances, key=lambda x: x[1]) if not_ashlands_distances else (0, 0, 0, 0)

        print(f"\n🔍 ASHLANDS THRESHOLD:")
        print(f"   Decompiled constant: 12000.0")
        print(f"   Minimum Ashlands sample: {min_ash[1]:.1f} at ({min_ash[2]:.0f}, {min_ash[3]:.0f})")
        print(f"   Maximum non-Ashlands: {max_not_ash[1]:.1f} at ({max_not_ash[2]:.0f}, {max_not_ash[3]:.0f})")
        print(f"   **ACTUAL THRESHOLD appears to be: ~{(min_ash[1] + max_not_ash[1])/2:.0f}**")

    # Statistical analysis
    print(f"\n📊 STATISTICAL ANALYSIS:")
    dn_thresholds = [t[1] for t in deepnorth_distances]
    if dn_thresholds:
        print(f"   DeepNorth threshold range: {min(dn_thresholds):.1f} - {max(dn_thresholds):.1f}")
        print(f"   Mean: {sum(dn_thresholds)/len(dn_thresholds):.1f}")

    ash_thresholds = [t[1] for t in ashlands_distances]
    if ash_thresholds:
        print(f"   Ashlands threshold range: {min(ash_thresholds):.1f} - {max(ash_thresholds):.1f}")
        print(f"   Mean: {sum(ash_thresholds)/len(ash_thresholds):.1f}")

if __name__ == '__main__':
    analyze_thresholds('/home/steve/projects/valheim-world-engine/procedural-export/output/hnLycKKCMI-samples-1024.json')
