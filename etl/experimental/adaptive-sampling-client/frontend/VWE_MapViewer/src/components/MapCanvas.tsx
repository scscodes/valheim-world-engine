'use client';

import React, { useRef, useEffect, useState } from 'react';
import { BiomeMapData, HeightmapData, BiomeColors, Biome } from '../types/world-data';

interface MapCanvasProps {
  biomeData?: BiomeMapData;
  heightmapData?: HeightmapData;
  width?: number;
  height?: number;
  showBiomes?: boolean;
  showHeightmap?: boolean;
  heightmapAlpha?: number;
}

export default function MapCanvas({
  biomeData,
  heightmapData,
  width = 512,
  height = 512,
  showBiomes = true,
  showHeightmap = false,
  heightmapAlpha = 0.5,
}: MapCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isRendering, setIsRendering] = useState(false);

  useEffect(() => {
    if (!canvasRef.current) return;
    if (!biomeData && !heightmapData) return;

    setIsRendering(true);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Render biomes
    if (showBiomes && biomeData) {
      renderBiomes(ctx, biomeData, width, height);
    }

    // Render heightmap overlay
    if (showHeightmap && heightmapData) {
      renderHeightmap(ctx, heightmapData, width, height, heightmapAlpha);
    }

    setIsRendering(false);
  }, [biomeData, heightmapData, width, height, showBiomes, showHeightmap, heightmapAlpha]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="border border-gray-300 rounded"
      />
      {isRendering && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded">
          <div className="text-white">Rendering...</div>
        </div>
      )}
    </div>
  );
}

function renderBiomes(
  ctx: CanvasRenderingContext2D,
  biomeData: BiomeMapData,
  targetWidth: number,
  targetHeight: number
) {
  const { biome_map, resolution } = biomeData;
  const pixelSize = targetWidth / resolution;

  for (let y = 0; y < resolution; y++) {
    for (let x = 0; x < resolution; x++) {
      const biomeId = biome_map[y][x] as Biome;
      const color = BiomeColors[biomeId] || BiomeColors[Biome.None];
      
      ctx.fillStyle = color;
      ctx.fillRect(
        x * pixelSize,
        y * pixelSize,
        Math.ceil(pixelSize),
        Math.ceil(pixelSize)
      );
    }
  }
}

function renderHeightmap(
  ctx: CanvasRenderingContext2D,
  heightmapData: HeightmapData,
  targetWidth: number,
  targetHeight: number,
  alpha: number
) {
  const { heightmap, resolution, metadata } = heightmapData;
  const pixelSize = targetWidth / resolution;

  // Find min/max for normalization
  let minHeight = metadata?.min_height ?? Infinity;
  let maxHeight = metadata?.max_height ?? -Infinity;

  if (!metadata) {
    for (const row of heightmap) {
      for (const h of row) {
        if (h < minHeight) minHeight = h;
        if (h > maxHeight) maxHeight = h;
      }
    }
  }

  const heightRange = maxHeight - minHeight;

  ctx.globalAlpha = alpha;

  for (let y = 0; y < resolution; y++) {
    for (let x = 0; x < resolution; x++) {
      const height = heightmap[y][x];
      const normalized = heightRange > 0 ? (height - minHeight) / heightRange : 0;
      const intensity = Math.floor(normalized * 255);
      
      ctx.fillStyle = `rgb(${intensity}, ${intensity}, ${intensity})`;
      ctx.fillRect(
        x * pixelSize,
        y * pixelSize,
        Math.ceil(pixelSize),
        Math.ceil(pixelSize)
      );
    }
  }

  ctx.globalAlpha = 1.0;
}

