#!/usr/bin/env python3
"""
Analyze biome classification issues in the generated world data
"""

import json
import math
from collections import defaultdict, Counter

def world_angle(x, y):
    """Valheim's WorldAngle function"""
    return math.sin(math.atan2(x, y) * 20.0)

def is_deepnorth_valheim(x, y):
    """Valheim's IsDeepnorth check"""
    angle_modifier = world_angle(x, y) * 100.0
    distance = math.sqrt(x**2 + (y + 4000)**2)
    threshold = 12000.0 + angle_modifier
    return distance > threshold

def is_ashlands_valheim(x, y):
    """Valheim's IsAshlands check"""
    angle_modifier = world_angle(x, y) * 100.0
    distance = math.sqrt(x**2 + (y - 4000)**2)
    threshold = 12000.0 + angle_modifier
    return distance > threshold

def analyze_samples(sample_file):
    print("=" * 80)
    print("BIOME CLASSIFICATION ANALYSIS")
    print("=" * 80)

    with open(sample_file, 'r') as f:
        data = json.load(f)

    biome_names = {
        1: 'Meadows', 2: 'BlackForest', 4: 'Swamp', 8: 'Mountain',
        16: 'Plains', 32: 'Ocean', 64: 'Mistlands', 256: 'DeepNorth', 512: 'Ashlands'
    }

    # Issue tracking
    issues = {
        'deepnorth_wrong': [],
        'ashlands_wrong': [],
        'deepnorth_center': [],
        'ashlands_center': []
    }

    for sample in data['Samples']:
        x, z = sample['X'], sample['Z']
        actual_biome = sample['Biome']
        dist_from_center = math.sqrt(x**2 + z**2)

        # Check DeepNorth
        should_be_deepnorth = is_deepnorth_valheim(x, z)
        is_deepnorth = (actual_biome == 256)

        if should_be_deepnorth != is_deepnorth:
            issues['deepnorth_wrong'].append({
                'pos': (x, z),
                'actual': biome_names.get(actual_biome, f'Unknown({actual_biome})'),
                'expected': 'DeepNorth' if should_be_deepnorth else 'Not DeepNorth',
                'dist': dist_from_center
            })

        if is_deepnorth and dist_from_center < 5000:
            issues['deepnorth_center'].append((x, z, dist_from_center))

        # Check Ashlands
        should_be_ashlands = is_ashlands_valheim(x, z)
        is_ashlands = (actual_biome == 512)

        if should_be_ashlands != is_ashlands:
            issues['ashlands_wrong'].append({
                'pos': (x, z),
                'actual': biome_names.get(actual_biome, f'Unknown({actual_biome})'),
                'expected': 'Ashlands' if should_be_ashlands else 'Not Ashlands',
                'dist': dist_from_center
            })

        if is_ashlands and dist_from_center < 8000:
            issues['ashlands_center'].append((x, z, dist_from_center))

    # Report findings
    print(f"\n🔍 ISSUE #1: DeepNorth Misclassification")
    print(f"   - Samples wrongly classified: {len(issues['deepnorth_wrong']):,}")
    print(f"   - DeepNorth within 5km of center: {len(issues['deepnorth_center']):,}")
    if issues['deepnorth_center']:
        closest = min(issues['deepnorth_center'], key=lambda x: x[2])
        print(f"   - Closest to center: ({closest[0]:.0f}, {closest[1]:.0f}) at {closest[2]:.0f}m")

    print(f"\n🔍 ISSUE #2: Ashlands Misclassification")
    print(f"   - Samples wrongly classified: {len(issues['ashlands_wrong']):,}")
    print(f"   - Ashlands within 8km of center: {len(issues['ashlands_center']):,}")
    if issues['ashlands_center']:
        closest = min(issues['ashlands_center'], key=lambda x: x[2])
        print(f"   - Closest to center: ({closest[0]:.0f}, {closest[1]:.0f}) at {closest[2]:.0f}m")

    # Show examples of misclassified samples
    if issues['deepnorth_wrong'][:5]:
        print(f"\n   Example DeepNorth mismatches:")
        for issue in issues['deepnorth_wrong'][:5]:
            print(f"     ({issue['pos'][0]:6.0f}, {issue['pos'][1]:6.0f}) "
                  f"actual={issue['actual']:12} expected={issue['expected']:12} "
                  f"dist={issue['dist']:6.0f}m")

    return issues

if __name__ == '__main__':
    analyze_samples('/home/steve/projects/valheim-world-engine/procedural-export/output/hnLycKKCMI-samples-1024.json')
