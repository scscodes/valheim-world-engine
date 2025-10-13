'use client';

import { useState, useEffect } from 'react';
import MapCanvas from '../components/MapCanvas';
import { worldDataAPI } from '../lib/api-client';
import { BiomeMapData, HeightmapData, BiomeNames, BiomeDisplayNames, Biome, BiomeColors } from '../types/world-data';

export default function Home() {
  const [biomeData, setBiomeData] = useState<BiomeMapData | null>(null);
  const [heightmapData, setHeightmapData] = useState<HeightmapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBiomes, setShowBiomes] = useState(true);
  const [showHeightmap, setShowHeightmap] = useState(false);
  const [heightmapAlpha, setHeightmapAlpha] = useState(0.5);

  useEffect(() => {
    loadWorldData();
  }, []);

  async function loadWorldData() {
    setLoading(true);
    setError(null);

    try {
      // Load biome and heightmap data
      const [biomes, heightmap] = await Promise.all([
        worldDataAPI.fetchBiomeData('default').catch(() => null),
        worldDataAPI.fetchHeightmapData('default').catch(() => null),
      ]);

      setBiomeData(biomes);
      setHeightmapData(heightmap);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load world data');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Valheim World Map Viewer</h1>
        <p className="text-gray-600 mb-8">
          Interactive visualization of Valheim world data from adaptive sampling
        </p>

        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg">Loading world data...</div>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Map Canvas */}
            <div className="lg:col-span-2">
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h2 className="text-2xl font-semibold mb-4">World Map</h2>
                
                {biomeData || heightmapData ? (
                  <MapCanvas
                    biomeData={biomeData || undefined}
                    heightmapData={heightmapData || undefined}
                    width={512}
                    height={512}
                    showBiomes={showBiomes}
                    showHeightmap={showHeightmap}
                    heightmapAlpha={heightmapAlpha}
                  />
                ) : (
                  <div className="flex items-center justify-center h-96 bg-gray-100 rounded">
                    <p className="text-gray-500">No world data available</p>
                  </div>
                )}

                {/* Map Info */}
                {biomeData && (
                  <div className="mt-4 text-sm text-gray-600">
                    <p><strong>Resolution:</strong> {biomeData.resolution}×{biomeData.resolution}</p>
                    <p><strong>World Diameter:</strong> {biomeData.world_diameter.toLocaleString()}m</p>
                    {biomeData.metadata && (
                      <p><strong>Sample Spacing:</strong> {biomeData.metadata.sample_spacing_meters.toFixed(1)}m</p>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Controls & Legend */}
            <div className="space-y-6">
              {/* Layer Controls */}
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-4">Layer Controls</h3>
                
                <div className="space-y-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={showBiomes}
                      onChange={(e) => setShowBiomes(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span>Show Biomes</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={showHeightmap}
                      onChange={(e) => setShowHeightmap(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span>Show Heightmap</span>
                  </label>

                  {showHeightmap && (
                    <div>
                      <label className="block text-sm mb-1">
                        Heightmap Opacity: {(heightmapAlpha * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={heightmapAlpha}
                        onChange={(e) => setHeightmapAlpha(parseFloat(e.target.value))}
                        className="w-full"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Biome Legend */}
              {showBiomes && biomeData && (
                <div className="bg-white p-6 rounded-lg shadow-md">
                  <h3 className="text-xl font-semibold mb-4">Biome Legend</h3>
                  
                  <div className="space-y-2">
                    {Object.entries(BiomeNames).map(([id, apiName]) => {
                      const biomeId = parseInt(id) as Biome;
                      const count = biomeData.metadata?.biome_counts?.[apiName] || 0;
                      const percentage = biomeData.metadata?.biome_counts
                        ? ((count / (biomeData.resolution * biomeData.resolution)) * 100).toFixed(1)
                        : '0';

                      if (count === 0) return null;

                      const displayName = BiomeDisplayNames[biomeId];

                      return (
                        <div key={id} className="flex items-center space-x-2 text-sm">
                          <div
                            className="w-6 h-6 rounded border border-gray-300"
                            style={{ backgroundColor: BiomeColors[biomeId] }}
                          />
                          <span className="flex-1">{displayName}</span>
                          <span className="text-gray-500">{percentage}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Image Export */}
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-4">Export</h3>
                
                <div className="space-y-2">
                  <a
                    href={worldDataAPI.getBiomeImageUrl('default')}
                    download="biomes.png"
                    className="block w-full text-center bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
                  >
                    Download Biome Map
                  </a>
                  <a
                    href={worldDataAPI.getHeightmapImageUrl('default')}
                    download="heightmap.png"
                    className="block w-full text-center bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600"
                  >
                    Download Heightmap
                  </a>
                  <a
                    href={worldDataAPI.getCompositeImageUrl('default', 1024, 0.5)}
                    download="composite.png"
                    className="block w-full text-center bg-purple-500 text-white py-2 px-4 rounded hover:bg-purple-600"
                  >
                    Download Composite (1024px)
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
