#!/usr/bin/env python3
"""
Visualize spatial distribution of biome samples
Generates heatmap showing sample coverage patterns
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys


def visualize_sample_density(json_path: Path, output_path: Path):
    print(f"Loading biome data from: {json_path}")
    with open(json_path) as f:
        data = json.load(f)

    biome_map = np.array(data['biome_map'])
    resolution = data['resolution']
    world_radius = data['world_radius']

    # Create coordinate grids (matching BiomeExporter logic)
    step_size = (2 * world_radius) / resolution

    # Current implementation (corner-aligned)
    x_coords_corner = np.arange(resolution) * step_size - world_radius
    z_coords_corner = np.arange(resolution) * step_size - world_radius

    # Fixed implementation (center-aligned)
    x_coords_center = (np.arange(resolution) + 0.5) * step_size - world_radius
    z_coords_center = (np.arange(resolution) + 0.5) * step_size - world_radius

    # Calculate distance from center for each sample
    X_corner, Z_corner = np.meshgrid(x_coords_corner, z_coords_corner)
    X_center, Z_center = np.meshgrid(x_coords_center, z_coords_center)

    distances_corner = np.sqrt(X_corner**2 + Z_corner**2)
    distances_center = np.sqrt(X_center**2 + Z_center**2)

    # Plot
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Sample Density Analysis - {resolution}x{resolution} resolution', fontsize=16)

    # Row 1: Current (corner-aligned) implementation
    axes[0, 0].scatter(X_corner.flatten()[::10], Z_corner.flatten()[::10],
                       s=1, alpha=0.3, c='blue', label='Sample points')
    axes[0, 0].add_patch(plt.Circle((0, 0), world_radius, fill=False,
                                     color='red', linestyle='--', label='World boundary'))
    axes[0, 0].set_title('Current: Corner-Aligned Samples')
    axes[0, 0].set_xlabel('World X (m)')
    axes[0, 0].set_ylabel('World Z (m)')
    axes[0, 0].set_aspect('equal')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()

    im0 = axes[0, 1].imshow(distances_corner, cmap='viridis', origin='lower',
                            extent=[-world_radius, world_radius, -world_radius, world_radius])
    axes[0, 1].set_title('Current: Distance from Center')
    axes[0, 1].set_xlabel('World X (m)')
    axes[0, 1].set_ylabel('World Z (m)')
    plt.colorbar(im0, ax=axes[0, 1], label='Distance (m)')

    radial_bins = np.linspace(0, world_radius, 20)
    counts_corner, _ = np.histogram(distances_corner.flatten(), bins=radial_bins)
    axes[0, 2].plot(radial_bins[:-1], counts_corner, 'o-', color='blue', label='Corner-aligned')
    axes[0, 2].set_title('Current: Radial Distribution')
    axes[0, 2].set_xlabel('Distance from Center (m)')
    axes[0, 2].set_ylabel('Number of Samples')
    axes[0, 2].grid(True, alpha=0.3)
    axes[0, 2].legend()

    # Row 2: Fixed (center-aligned) implementation
    axes[1, 0].scatter(X_center.flatten()[::10], Z_center.flatten()[::10],
                       s=1, alpha=0.3, c='green', label='Sample points')
    axes[1, 0].add_patch(plt.Circle((0, 0), world_radius, fill=False,
                                     color='red', linestyle='--', label='World boundary'))
    axes[1, 0].set_title('Fixed: Center-Aligned Samples')
    axes[1, 0].set_xlabel('World X (m)')
    axes[1, 0].set_ylabel('World Z (m)')
    axes[1, 0].set_aspect('equal')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()

    im1 = axes[1, 1].imshow(distances_center, cmap='viridis', origin='lower',
                            extent=[-world_radius, world_radius, -world_radius, world_radius])
    axes[1, 1].set_title('Fixed: Distance from Center')
    axes[1, 1].set_xlabel('World X (m)')
    axes[1, 1].set_ylabel('World Z (m)')
    plt.colorbar(im1, ax=axes[1, 1], label='Distance (m)')

    counts_center, _ = np.histogram(distances_center.flatten(), bins=radial_bins)
    axes[1, 2].plot(radial_bins[:-1], counts_center, 'o-', color='green', label='Center-aligned')
    axes[1, 2].set_title('Fixed: Radial Distribution')
    axes[1, 2].set_xlabel('Distance from Center (m)')
    axes[1, 2].set_ylabel('Number of Samples')
    axes[1, 2].grid(True, alpha=0.3)
    axes[1, 2].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nDensity visualization saved to: {output_path}")

    # Statistical summary
    print(f"\n{'='*80}")
    print("SAMPLE COVERAGE STATISTICS")
    print(f"{'='*80}\n")

    print("Configuration:")
    print(f"  Resolution: {resolution}x{resolution}")
    print(f"  Total samples: {resolution * resolution:,}")
    print(f"  Step size: {step_size:.2f}m")
    print(f"  World radius: {world_radius:.0f}m")

    print(f"\nCurrent (Corner-Aligned) Implementation:")
    print(f"  X range: [{x_coords_corner[0]:.1f}, {x_coords_corner[-1]:.1f}]")
    print(f"  Z range: [{z_coords_corner[0]:.1f}, {z_coords_corner[-1]:.1f}]")
    print(f"  Min distance from center: {distances_corner.min():.1f}m")
    print(f"  Max distance from center: {distances_corner.max():.1f}m")
    print(f"  Samples at exact boundary: {np.sum(distances_corner >= world_radius):,}")

    print(f"\nFixed (Center-Aligned) Implementation:")
    print(f"  X range: [{x_coords_center[0]:.1f}, {x_coords_center[-1]:.1f}]")
    print(f"  Z range: [{z_coords_center[0]:.1f}, {z_coords_center[-1]:.1f}]")
    print(f"  Min distance from center: {distances_center.min():.1f}m")
    print(f"  Max distance from center: {distances_center.max():.1f}m")
    print(f"  Samples at exact boundary: {np.sum(distances_center >= world_radius):,}")

    # Edge analysis
    edge_threshold_corner = np.percentile(distances_corner.flatten(), 90)
    edge_threshold_center = np.percentile(distances_center.flatten(), 90)

    print(f"\nEdge Bias Analysis (outer 10% of samples):")
    print(f"  Corner-aligned edge threshold: {edge_threshold_corner:.1f}m")
    print(f"  Center-aligned edge threshold: {edge_threshold_center:.1f}m")
    print(f"  Improvement: {edge_threshold_corner - edge_threshold_center:.1f}m reduction")

    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python visualize_sample_density.py <biomes.json> [output.png]")
        print("\nExample:")
        print("  python visualize_sample_density.py etl/experimental/bepinex-adaptive-sampling/output/world_data/biomes.json sample_density.png")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('sample_density.png')

    if not json_path.exists():
        print(f"ERROR: File not found: {json_path}")
        sys.exit(1)

    visualize_sample_density(json_path, output_path)
