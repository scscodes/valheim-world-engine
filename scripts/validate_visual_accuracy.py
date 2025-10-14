#!/usr/bin/env python3
"""
Visual Accuracy Validator - Biome Map Renderer Quality Assessment

Compares client-rendered biome maps against reference high-resolution images.
Uses multiple metrics to assess visual fidelity:
  - Structural Similarity (SSIM): Perceptual similarity
  - Edge Alignment (RMSE): Boundary position accuracy
  - Biome Distribution Error: Statistical color distribution match
  - Pixel Agreement: Exact color match percentage

Usage:
  python validate_visual_accuracy.py <client_render.png> <reference.png> [--output metrics.json]
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, Tuple
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from scipy.ndimage import sobel

# Valid biome colors from global/data (Valheim canonical colors)
BIOME_COLORS = {
    (121, 176, 81): "Meadows",      # Green
    (119, 108, 92): "Swamp",        # Muddy brown
    (209, 228, 237): "Mountain",    # Light gray/white
    (88, 129, 59): "BlackForest",   # Dark green
    (229, 215, 150): "Plains",      # Tan/yellow
    (52, 97, 141): "Ocean",         # Blue
    (88, 90, 92): "Mistlands",      # Dark gray
    (255, 255, 255): "DeepNorth",   # White
    (139, 37, 28): "Ashlands"       # Dark red
}


def load_and_normalize_images(
    client_path: Path,
    reference_path: Path
) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
    """
    Load both images and ensure they're the same resolution for comparison.
    Uses NEAREST neighbor to preserve exact biome boundaries when resizing.

    Returns:
        (client_array, reference_array, original_client_shape)
    """
    print(f"Loading images...")
    print(f"  Client:    {client_path}")
    print(f"  Reference: {reference_path}")

    client_img = Image.open(client_path).convert('RGB')
    reference_img = Image.open(reference_path).convert('RGB')

    original_client_shape = client_img.size

    print(f"\nOriginal resolutions:")
    print(f"  Client:    {client_img.size[0]}×{client_img.size[1]}")
    print(f"  Reference: {reference_img.size[0]}×{reference_img.size[1]}")

    # Resize to match reference resolution for fair comparison
    if client_img.size != reference_img.size:
        print(f"\nResizing client to match reference ({reference_img.size[0]}×{reference_img.size[1]})...")
        client_img = client_img.resize(reference_img.size, Image.Resampling.NEAREST)

    client_array = np.array(client_img)
    reference_array = np.array(reference_img)

    return client_array, reference_array, original_client_shape


def calculate_pixel_agreement(client: np.ndarray, reference: np.ndarray) -> Dict:
    """
    Calculate exact pixel-wise color agreement.

    Returns percentage of pixels with exact RGB match.
    """
    print(f"\n{'='*80}")
    print("METRIC 1: Pixel-Wise Agreement")
    print(f"{'='*80}")

    exact_matches = np.all(client == reference, axis=-1)
    agreement_pct = np.mean(exact_matches) * 100

    total_pixels = client.shape[0] * client.shape[1]
    matching_pixels = int(np.sum(exact_matches))

    print(f"Exact pixel matches: {matching_pixels:,} / {total_pixels:,}")
    print(f"Agreement: {agreement_pct:.2f}%")

    return {
        'agreement_percentage': round(agreement_pct, 2),
        'matching_pixels': matching_pixels,
        'total_pixels': total_pixels
    }


def calculate_edge_alignment(client: np.ndarray, reference: np.ndarray) -> Dict:
    """
    Calculate edge alignment using Sobel edge detection.
    Measures how well biome boundaries align between client and reference.

    Lower RMSE = better boundary alignment.
    """
    print(f"\n{'='*80}")
    print("METRIC 2: Edge Alignment (Boundary Position Accuracy)")
    print(f"{'='*80}")

    # Convert to grayscale for edge detection
    client_gray = np.mean(client, axis=2)
    reference_gray = np.mean(reference, axis=2)

    # Sobel edge detection
    client_edges = sobel(client_gray)
    reference_edges = sobel(reference_gray)

    # Calculate RMSE of edge maps
    edge_rmse = np.sqrt(np.mean((client_edges - reference_edges) ** 2))

    # Normalize RMSE to 0-100 scale for interpretability
    max_possible_rmse = np.sqrt(np.mean(reference_edges ** 2) * 2)
    normalized_rmse = (edge_rmse / max_possible_rmse) * 100 if max_possible_rmse > 0 else 0

    # Edge detection statistics
    client_edge_pixels = np.sum(client_edges > client_edges.mean())
    reference_edge_pixels = np.sum(reference_edges > reference_edges.mean())

    print(f"Edge detection:")
    print(f"  Client edges:    {client_edge_pixels:,} pixels")
    print(f"  Reference edges: {reference_edge_pixels:,} pixels")
    print(f"  Edge RMSE:       {edge_rmse:.2f}")
    print(f"  Normalized RMSE: {normalized_rmse:.2f}% (lower is better)")

    return {
        'edge_rmse': round(edge_rmse, 2),
        'normalized_rmse': round(normalized_rmse, 2),
        'client_edge_pixels': int(client_edge_pixels),
        'reference_edge_pixels': int(reference_edge_pixels)
    }


def calculate_ssim(client: np.ndarray, reference: np.ndarray) -> Dict:
    """
    Calculate Structural Similarity Index (SSIM).
    Measures perceptual similarity between images.

    SSIM ranges from -1 to 1, where 1 = perfect match.
    """
    print(f"\n{'='*80}")
    print("METRIC 3: Structural Similarity (SSIM)")
    print(f"{'='*80}")

    # Calculate SSIM across all RGB channels
    ssim_score = ssim(client, reference, channel_axis=2, data_range=255)
    ssim_pct = ssim_score * 100

    print(f"SSIM Score: {ssim_score:.4f}")
    print(f"Similarity: {ssim_pct:.2f}%")

    # Interpretation
    if ssim_score >= 0.95:
        interpretation = "Excellent - Near-identical"
    elif ssim_score >= 0.85:
        interpretation = "Good - Minor visual differences"
    elif ssim_score >= 0.70:
        interpretation = "Fair - Noticeable differences"
    else:
        interpretation = "Poor - Significant differences"

    print(f"Interpretation: {interpretation}")

    return {
        'ssim_score': round(ssim_score, 4),
        'ssim_percentage': round(ssim_pct, 2),
        'interpretation': interpretation
    }


def calculate_biome_distribution_error(client: np.ndarray, reference: np.ndarray) -> Dict:
    """
    Calculate biome distribution error by comparing color histograms.
    Measures how well the client preserves the statistical distribution of biomes.
    """
    print(f"\n{'='*80}")
    print("METRIC 4: Biome Distribution Error")
    print(f"{'='*80}")

    # Flatten to color lists
    client_pixels = client.reshape(-1, 3)
    reference_pixels = reference.reshape(-1, 3)

    # Count color frequencies
    client_colors = Counter(tuple(pixel) for pixel in client_pixels)
    reference_colors = Counter(tuple(pixel) for pixel in reference_pixels)

    total_pixels = len(client_pixels)

    # Calculate distribution for known biome colors
    print(f"\n{'Biome':<15} {'Client %':<12} {'Reference %':<12} {'Diff':<12}")
    print("-" * 60)

    biome_errors = {}
    total_error = 0

    for color, biome_name in BIOME_COLORS.items():
        client_count = client_colors.get(color, 0)
        reference_count = reference_colors.get(color, 0)

        client_pct = (client_count / total_pixels) * 100
        reference_pct = (reference_count / total_pixels) * 100
        diff = client_pct - reference_pct

        biome_errors[biome_name] = {
            'client_percentage': round(client_pct, 2),
            'reference_percentage': round(reference_pct, 2),
            'difference': round(diff, 2),
            'abs_difference': round(abs(diff), 2)
        }

        total_error += abs(diff)

        flag = "⚠️ " if abs(diff) > 5.0 else "  "
        print(f"{flag}{biome_name:<15} {client_pct:>6.2f}%      {reference_pct:>6.2f}%      {diff:>+6.2f}%")

    # Handle unknown/interpolated colors
    all_colors = set(client_colors.keys()) | set(reference_colors.keys())
    unknown_colors = all_colors - set(BIOME_COLORS.keys())

    unknown_client_count = sum(client_colors.get(c, 0) for c in unknown_colors)
    unknown_reference_count = sum(reference_colors.get(c, 0) for c in unknown_colors)

    unknown_client_pct = (unknown_client_count / total_pixels) * 100
    unknown_reference_pct = (unknown_reference_count / total_pixels) * 100

    if unknown_client_count > 0 or unknown_reference_count > 0:
        print(f"\n{'Unknown/Interp.':<15} {unknown_client_pct:>6.2f}%      {unknown_reference_pct:>6.2f}%")
        print(f"  (Indicates interpolation artifacts or non-standard colors)")

    print(f"\nTotal Absolute Error: {total_error:.2f}%")
    print(f"Average Error per Biome: {total_error / len(BIOME_COLORS):.2f}%")

    return {
        'total_absolute_error': round(total_error, 2),
        'average_error_per_biome': round(total_error / len(BIOME_COLORS), 2),
        'biome_errors': biome_errors,
        'unknown_colors': {
            'client_percentage': round(unknown_client_pct, 2),
            'reference_percentage': round(unknown_reference_pct, 2),
            'count': len(unknown_colors)
        }
    }


def generate_summary(results: Dict) -> Dict:
    """Generate overall quality assessment and recommendations."""
    print(f"\n{'='*80}")
    print("OVERALL ASSESSMENT")
    print(f"{'='*80}")

    # Define quality criteria
    criteria = {
        'pixel_agreement': {
            'value': results['pixel_agreement']['agreement_percentage'],
            'threshold': 80.0,
            'name': 'Pixel Agreement',
            'unit': '%'
        },
        'ssim': {
            'value': results['ssim']['ssim_percentage'],
            'threshold': 85.0,
            'name': 'Structural Similarity',
            'unit': '%'
        },
        'edge_alignment': {
            'value': 100 - results['edge_alignment']['normalized_rmse'],
            'threshold': 85.0,
            'name': 'Edge Alignment',
            'unit': '%'
        },
        'distribution': {
            'value': 100 - results['biome_distribution']['total_absolute_error'],
            'threshold': 90.0,
            'name': 'Distribution Accuracy',
            'unit': '%'
        }
    }

    print()
    passed_count = 0
    for criterion, data in criteria.items():
        passed = data['value'] >= data['threshold']
        passed_count += int(passed)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {data['name']:<30} {data['value']:>6.2f}{data['unit']} (target: ≥{data['threshold']}{data['unit']})")

    overall_score = (sum(c['value'] for c in criteria.values()) / len(criteria))

    print(f"\nOverall Quality Score: {overall_score:.2f}%")
    print(f"Criteria Passed: {passed_count}/{len(criteria)}")

    # Determine grade
    if overall_score >= 95:
        grade = "A+ (Excellent)"
    elif overall_score >= 90:
        grade = "A (Very Good)"
    elif overall_score >= 85:
        grade = "B (Good)"
    elif overall_score >= 75:
        grade = "C (Acceptable)"
    elif overall_score >= 60:
        grade = "D (Needs Improvement)"
    else:
        grade = "F (Poor)"

    print(f"Grade: {grade}")

    # Recommendations
    print(f"\nRecommendations:")
    if results['pixel_agreement']['agreement_percentage'] < 80:
        print("  • Low pixel agreement suggests significant rendering differences")
        print("    → Consider higher resolution sampling or smoother interpolation")

    if results['ssim']['ssim_score'] < 0.85:
        print("  • Low SSIM indicates perceptual quality issues")
        print("    → Implement distance-field or Voronoi-based rendering")

    if results['edge_alignment']['normalized_rmse'] > 15:
        print("  • High edge RMSE indicates boundary misalignment")
        print("    → Use adaptive sampling near biome boundaries")

    if results['biome_distribution']['total_absolute_error'] > 10:
        print("  • High distribution error indicates statistical inaccuracy")
        print("    → Verify sampling density and rendering algorithm")

    if results['biome_distribution']['unknown_colors']['client_percentage'] > 5:
        print("  • High unknown color percentage indicates interpolation artifacts")
        print("    → Use NEAREST neighbor upscaling or pure biome colors")

    if passed_count == len(criteria):
        print("  ✅ All criteria met - excellent visual accuracy!")

    return {
        'overall_score': round(overall_score, 2),
        'grade': grade,
        'criteria_passed': passed_count,
        'criteria_total': len(criteria),
        'criteria_details': criteria
    }


def save_results(results: Dict, output_path: Path):
    """Save validation results to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate visual accuracy of biome map renders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison
  python validate_visual_accuracy.py client_render.png reference.png

  # Save metrics to JSON
  python validate_visual_accuracy.py client_render.png reference.png --output metrics.json

  # Compare adaptive-sampling-client output against reference
  python validate_visual_accuracy.py \\
    data/seeds/hkLycKKCMI/world_data/biomes.png \\
    docs/biomes_hnLycKKCMI.png \\
    --output etl/experimental/adaptive-sampling-client/validation_baseline.json
        """
    )

    parser.add_argument('client', type=Path, help='Client-rendered biome map PNG')
    parser.add_argument('reference', type=Path, help='Reference biome map PNG')
    parser.add_argument('--output', '-o', type=Path, help='Output JSON file for metrics')

    args = parser.parse_args()

    # Validate inputs
    if not args.client.exists():
        print(f"❌ ERROR: Client file not found: {args.client}")
        sys.exit(1)

    if not args.reference.exists():
        print(f"❌ ERROR: Reference file not found: {args.reference}")
        sys.exit(1)

    print(f"{'='*80}")
    print("Visual Accuracy Validation - Biome Map Renderer Quality Assessment")
    print(f"{'='*80}")

    # Load images
    client, reference, original_shape = load_and_normalize_images(args.client, args.reference)

    # Calculate all metrics
    results = {
        'metadata': {
            'client_path': str(args.client),
            'reference_path': str(args.reference),
            'client_original_resolution': f"{original_shape[0]}×{original_shape[1]}",
            'comparison_resolution': f"{reference.shape[1]}×{reference.shape[0]}",
        },
        'pixel_agreement': calculate_pixel_agreement(client, reference),
        'edge_alignment': calculate_edge_alignment(client, reference),
        'ssim': calculate_ssim(client, reference),
        'biome_distribution': calculate_biome_distribution_error(client, reference),
    }

    # Generate summary
    results['summary'] = generate_summary(results)

    # Save if requested
    if args.output:
        save_results(results, args.output)

    print(f"\n{'='*80}\n")

    # Exit code based on quality
    if results['summary']['criteria_passed'] >= 3:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Needs improvement


if __name__ == '__main__':
    main()
