/**
 * API Client for World Data
 * Fetches data from VWE World Data API
 */

import { BiomeMapData, HeightmapData, WorldDataInfo, ValidationReport } from '../types/world-data';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class WorldDataAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * List all available worlds
   */
  async listWorlds(): Promise<WorldDataInfo[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/worlds/`);
    if (!response.ok) {
      throw new Error(`Failed to list worlds: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get world info for a specific seed
   */
  async getWorldInfo(seed: string): Promise<WorldDataInfo> {
    const response = await fetch(`${this.baseUrl}/api/v1/worlds/${seed}/info`);
    if (!response.ok) {
      throw new Error(`Failed to get world info: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Fetch biome data as JSON
   */
  async fetchBiomeData(seed: string): Promise<BiomeMapData> {
    const response = await fetch(`${this.baseUrl}/api/v1/worlds/${seed}/biomes?format=json`);
    if (!response.ok) {
      throw new Error(`Failed to fetch biome data: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Fetch biome data as PNG URL
   */
  getBiomeImageUrl(seed: string): string {
    return `${this.baseUrl}/api/v1/worlds/${seed}/biomes?format=png`;
  }

  /**
   * Fetch heightmap data as JSON
   */
  async fetchHeightmapData(seed: string): Promise<HeightmapData> {
    const response = await fetch(`${this.baseUrl}/api/v1/worlds/${seed}/heightmap?format=json`);
    if (!response.ok) {
      throw new Error(`Failed to fetch heightmap data: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Fetch heightmap data as PNG URL
   */
  getHeightmapImageUrl(seed: string, colormap: 'terrain' | 'grayscale' = 'terrain'): string {
    return `${this.baseUrl}/api/v1/worlds/${seed}/heightmap?format=png&colormap=${colormap}`;
  }

  /**
   * Get composite image URL (biomes + heightmap)
   */
  getCompositeImageUrl(seed: string, resolution: number = 512, alpha: number = 0.5): string {
    return `${this.baseUrl}/api/v1/worlds/${seed}/composite?resolution=${resolution}&alpha=${alpha}`;
  }

  /**
   * Validate world data
   */
  async validateWorldData(seed: string): Promise<ValidationReport> {
    const response = await fetch(`${this.baseUrl}/api/v1/validate/${seed}`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to validate world data: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/worlds/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }
}

// Export singleton instance
export const worldDataAPI = new WorldDataAPI();

