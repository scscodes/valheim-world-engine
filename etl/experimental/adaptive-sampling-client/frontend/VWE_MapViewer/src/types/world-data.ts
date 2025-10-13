/**
 * World Data Types for Valheim Map Viewer
 * TypeScript definitions for biome and heightmap data
 */

export interface BiomeMapData {
  resolution: number;
  world_radius: number;
  world_diameter: number;
  biome_map: number[][];
  metadata?: {
    sample_spacing_meters: number;
    biome_counts: Record<string, number>;
    generation_time?: string;
  };
}

export interface HeightmapData {
  resolution: number;
  world_radius: number;
  world_diameter: number;
  heightmap: number[][];
  metadata?: {
    min_height: number;
    max_height: number;
    sample_spacing_meters: number;
  };
}

export enum Biome {
  None = 0,
  Meadows = 1,
  BlackForest = 2,
  Swamp = 4,
  Mountain = 8,
  Plains = 16,
  Ocean = 32,
  Mistlands = 64,
  DeepNorth = 256,
  Ashlands = 512,
}

export const BiomeColors: Record<Biome, string> = {
  [Biome.None]: '#000000',
  [Biome.Meadows]: '#79B051',
  [Biome.Swamp]: '#625947',
  [Biome.Mountain]: '#D1E4ED',
  [Biome.BlackForest]: '#2D4228',
  [Biome.Plains]: '#F6DE91',
  [Biome.Ocean]: '#34618D',
  [Biome.Mistlands]: '#696978',
  [Biome.Ashlands]: '#784632',
  [Biome.DeepNorth]: '#F0F8FF',
};

// API response names (camelCase, matches backend)
export const BiomeNames: Record<Biome, string> = {
  [Biome.None]: 'None',
  [Biome.Meadows]: 'Meadows',
  [Biome.BlackForest]: 'BlackForest',
  [Biome.Swamp]: 'Swamp',
  [Biome.Mountain]: 'Mountain',
  [Biome.Plains]: 'Plains',
  [Biome.Ocean]: 'Ocean',
  [Biome.Mistlands]: 'Mistlands',
  [Biome.DeepNorth]: 'DeepNorth',
  [Biome.Ashlands]: 'Ashlands',
};

// Display names for UI (with proper spacing)
export const BiomeDisplayNames: Record<Biome, string> = {
  [Biome.None]: 'None',
  [Biome.Meadows]: 'Meadows',
  [Biome.BlackForest]: 'Black Forest',
  [Biome.Swamp]: 'Swamp',
  [Biome.Mountain]: 'Mountain',
  [Biome.Plains]: 'Plains',
  [Biome.Ocean]: 'Ocean',
  [Biome.Mistlands]: 'Mistlands',
  [Biome.DeepNorth]: 'Deep North',
  [Biome.Ashlands]: 'Ashlands',
};

export interface WorldDataInfo {
  seed: string;
  has_biomes: boolean;
  has_heightmap: boolean;
  has_structures: boolean;
  resolution?: number;
  file_sizes: Record<string, number>;
}

export interface ValidationCheck {
  check_name: string;
  status: 'passed' | 'failed' | 'warning';
  details: string;
  expected?: string;
  actual?: string;
}

export interface ValidationReport {
  seed: string;
  status: 'passed' | 'failed' | 'warning';
  checks: ValidationCheck[];
  summary: Record<string, any>;
  timestamp: string;
}

