#!/usr/bin/env python3
"""
Compare two biome JSON files (before/after fix)
Shows improvement in distribution accuracy
"""

import json
import sys
from pathlib import Path
from collections import Counter

BIOME_NAMES = {
    1: "Meadows",
    2: "Swamp",
    4: "Mountain",
    8: "BlackForest",
    16: "Plains",
    32: "Ocean",
    64: "Mistlands",
    256: "DeepNorth",
    512: "Ashlands"
}

# Expected distributions for seed hkLycKKCMI (from reference)
EXPECTED = {
    "Ocean": 30.0,
    "DeepNorth": 15.0,
    "Meadows": 12.0,
    "BlackForest": 10.0,
    "Plains": 10.0,
    "Mountain": 8.0,
    "Swamp": 7.0,
    "Mistlands": 5.0,
    "Ashlands": 3.0
}


def analyze(json_path):
    """Analyze biome distribution from JSON file"""
    with open(json_path) as f:
        data = json.load(f)

    biome_map = data['biome_map']
    flat = [bid for row in biome_map for bid in row]
    counts = Counter(flat)
    total = len(flat)

    results = {}
    for biome_id in [1, 2, 4, 8, 16, 32, 64, 256, 512]:
        name = BIOME_NAMES[biome_id]
        count = counts.get(biome_id, 0)
        pct = (count / total) * 100
        expected = EXPECTED.get(name, 0)
        error = pct - expected
        results[name] = {
            'count': count,
            'pct': pct,
            'expected': expected,
            'error': error,
            'abs_error': abs(error)
        }

    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_biome_distributions.py <before.json> <after.json>")
        print("\nExample:")
        print("  python compare_biome_distributions.py before/biomes.json after/biomes.json")
        sys.exit(1)

    before_path = Path(sys.argv[1])
    after_path = Path(sys.argv[2])

    if not before_path.exists():
        print(f"ERROR: Before file not found: {before_path}")
        sys.exit(1)
    if not after_path.exists():
        print(f"ERROR: After file not found: {after_path}")
        sys.exit(1)

    print(f"\nAnalyzing distributions...")
    print(f"  Before: {before_path}")
    print(f"  After:  {after_path}")

    before_results = analyze(before_path)
    after_results = analyze(after_path)

    print(f"\n{'='*100}")
    print("BEFORE/AFTER DISTRIBUTION COMPARISON")
    print(f"{'='*100}\n")
    print(f"{'Biome':<15} {'Before %':<12} {'After %':<12} {'Expected %':<12} {'Before Err':<12} {'After Err':<12} {'Improvement':<15}")
    print("-" * 100)

    total_improvement = 0
    improvements = []

    for name in sorted(EXPECTED.keys(), key=lambda n: EXPECTED[n], reverse=True):
        before = before_results[name]
        after = after_results[name]
        improvement = before['abs_error'] - after['abs_error']
        total_improvement += improvement
        improvements.append((name, improvement, before, after))

        # Determine status
        if improvement > 1.0:
            flag = "✅"  # Significant improvement
        elif improvement > 0:
            flag = "→"   # Minor improvement
        elif improvement > -1.0:
            flag = "="   # No change
        else:
            flag = "❌"  # Regression

        print(f"{flag} {name:<15} {before['pct']:>6.2f}%      {after['pct']:>6.2f}%      "
              f"{before['expected']:>6.1f}%      {before['error']:>+6.2f}%      "
              f"{after['error']:>+6.2f}%      {improvement:>+6.2f}%")

    print("-" * 100)
    print(f"{'TOTAL ABSOLUTE ERROR REDUCTION:':<77} {total_improvement:>+6.2f}%\n")

    # Summary statistics
    before_total_error = sum(r['abs_error'] for r in before_results.values())
    after_total_error = sum(r['abs_error'] for r in after_results.values())

    before_max_error = max(r['abs_error'] for r in before_results.values())
    after_max_error = max(r['abs_error'] for r in after_results.values())

    before_worst = max(before_results.items(), key=lambda x: x[1]['abs_error'])
    after_worst = max(after_results.items(), key=lambda x: x[1]['abs_error'])

    print("="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    print(f"\nTotal Absolute Error:")
    print(f"  Before: {before_total_error:.2f}%")
    print(f"  After:  {after_total_error:.2f}%")
    print(f"  Improvement: {before_total_error - after_total_error:+.2f}%")
    print(f"  Reduction: {((before_total_error - after_total_error) / before_total_error * 100):.1f}%")

    print(f"\nWorst-Case Error:")
    print(f"  Before: {before_worst[0]} ({before_worst[1]['error']:+.2f}%)")
    print(f"  After:  {after_worst[0]} ({after_worst[1]['error']:+.2f}%)")
    print(f"  Improvement: {before_max_error - after_max_error:+.2f}%")

    print(f"\nBiomes Within ±5% Target:")
    before_within_5 = sum(1 for r in before_results.values() if r['abs_error'] <= 5.0)
    after_within_5 = sum(1 for r in after_results.values() if r['abs_error'] <= 5.0)
    print(f"  Before: {before_within_5}/9 biomes ({before_within_5/9*100:.0f}%)")
    print(f"  After:  {after_within_5}/9 biomes ({after_within_5/9*100:.0f}%)")

    print(f"\nBiomes Within ±8% Target:")
    before_within_8 = sum(1 for r in before_results.values() if r['abs_error'] <= 8.0)
    after_within_8 = sum(1 for r in after_results.values() if r['abs_error'] <= 8.0)
    print(f"  Before: {before_within_8}/9 biomes ({before_within_8/9*100:.0f}%)")
    print(f"  After:  {after_within_8}/9 biomes ({after_within_8/9*100:.0f}%)")

    # Overall assessment
    print(f"\n{'='*100}")
    print("ASSESSMENT")
    print(f"{'='*100}\n")

    success_criteria = {
        'total_error_reduction': total_improvement > 15.0,  # 25% reduction from 61%
        'total_error_target': after_total_error < 45.0,
        'max_error_target': after_max_error < 10.0,
        'majority_within_8': after_within_8 >= 7
    }

    for criterion, passed in success_criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        criterion_name = criterion.replace('_', ' ').title()
        print(f"  {status}: {criterion_name}")

    if all(success_criteria.values()):
        print(f"\n✅ SUCCESS: All validation criteria met")
        print(f"   The pixel-center sampling fix significantly improved distribution accuracy.")
    elif sum(success_criteria.values()) >= 2:
        print(f"\n→ PARTIAL SUCCESS: {sum(success_criteria.values())}/4 criteria met")
        print(f"   Further optimization may be needed (consider true adaptive sampling).")
    else:
        print(f"\n❌ NEEDS WORK: Only {sum(success_criteria.values())}/4 criteria met")
        print(f"   Consider implementing true adaptive sampling with boundary detection.")

    print(f"\n{'='*100}\n")

    # Top improvements
    print("Top 3 Improvements:")
    top_improvements = sorted(improvements, key=lambda x: x[1], reverse=True)[:3]
    for i, (name, improvement, before, after) in enumerate(top_improvements, 1):
        print(f"  {i}. {name}: {improvement:+.2f}% (from {before['error']:+.2f}% to {after['error']:+.2f}%)")

    # Top regressions
    regressions = [x for x in improvements if x[1] < 0]
    if regressions:
        print(f"\nRegressions:")
        for name, improvement, before, after in sorted(regressions, key=lambda x: x[1])[:3]:
            print(f"  - {name}: {improvement:+.2f}% (from {before['error']:+.2f}% to {after['error']:+.2f}%)")

    print()


if __name__ == '__main__':
    main()
