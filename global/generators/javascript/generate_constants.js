#!/usr/bin/env node
/**
 * Generate JavaScript constants from YAML configuration
 */

const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');

function loadYamlConfig() {
    const configPath = path.join(__dirname, '..', '..', 'data', 'valheim-world.yml');
    const yamlContent = fs.readFileSync(configPath, 'utf8');
    return yaml.load(yamlContent);
}

function loadValidationData() {
    const validationPath = path.join(__dirname, '..', '..', 'data', 'validation-data.yml');
    const yamlContent = fs.readFileSync(validationPath, 'utf8');
    return yaml.load(yamlContent);
}

function loadRenderingConfig() {
    const renderingPath = path.join(__dirname, '..', '..', 'data', 'rendering-config.yml');
    const yamlContent = fs.readFileSync(renderingPath, 'utf8');
    return yaml.load(yamlContent);
}

function mergeBiomeDefaults(biomes, defaults) {
    const merged = {};
    for (const [name, biome] of Object.entries(biomes)) {
        if (name === 'defaults') continue;
        
        // Start with defaults
        const mergedBiome = { ...defaults };
        
        // Override with biome-specific properties
        Object.assign(mergedBiome, biome);
        
        merged[name] = mergedBiome;
    }
    return merged;
}

function generateJavaScriptConstants() {
    const config = loadYamlConfig();
    const validation = loadValidationData();
    const rendering = loadRenderingConfig();
    
    // Extract constants
    const world = config.world;
    const coordinates = config.coordinates;
    const height = config.height;
    const biomes = mergeBiomeDefaults(config.biomes, config.biomes.defaults);
    
    // Generate JavaScript file
    const outputPath = path.join(__dirname, '..', '..', '..', 'procedural-export', 'client', 'valheim-constants.js');
    
    let content = '';
    
    // Header
    content += '// Generated Valheim Constants\n';
    content += '// ===========================\n';
    content += '// DO NOT EDIT - Generated from global/data/*.yml\n';
    content += `// Generated: ${config.metadata.last_updated}\n\n`;
    
    // World constants
    content += 'export const VALHEIM_WORLD = {\n';
    content += '    // World dimensions\n';
    content += `    RADIUS: ${world.radius},\n`;
    content += `    DIAMETER: ${world.diameter},\n`;
    content += `    WATER_EDGE: ${world.water_edge},\n\n`;
    
    // Coordinate system
    content += '    // Coordinate system\n';
    content += `    COORDINATE_ORIGIN: [${coordinates.origin[0]}, ${coordinates.origin[1]}],\n`;
    content += `    COORDINATE_UNIT: "${coordinates.unit}",\n`;
    content += '    COORDINATE_AXES: {\n';
    content += `        x: "${coordinates.axes.x}",\n`;
    content += `        y: "${coordinates.axes.y}",\n`;
    content += `        z: "${coordinates.axes.z}"\n`;
    content += '    },\n\n';
    
    // Height system
    content += '    // Height system\n';
    content += `    SEA_LEVEL: ${height.sea_level},\n`;
    content += `    HEIGHT_MULTIPLIER: ${height.multiplier},\n`;
    content += `    HEIGHT_RANGE: [${height.range[0]}, ${height.range[1]}],\n`;
    content += `    OCEAN_THRESHOLD: ${height.ocean_threshold},\n`;
    content += `    MOUNTAIN_THRESHOLD: ${height.mountain_threshold}\n`;
    content += '};\n\n';
    
    // Biome constants
    content += 'export const BIOMES = {\n';
    for (const [name, biome] of Object.entries(biomes)) {
        content += `    ${name}: {\n`;
        content += `        id: ${biome.id},\n`;
        content += `        rgb: [${biome.rgb[0]}, ${biome.rgb[1]}, ${biome.rgb[2]}],\n`;
        content += `        hex: "${biome.hex}",\n`;
        content += `        heightRange: [${biome.height_range[0]}, ${biome.height_range[1]}],\n`;
        content += `        distanceRange: [${biome.distance_range[0]}, ${biome.distance_range[1]}],\n`;
        content += `        noiseThreshold: ${biome.noise_threshold},\n`;
        content += `        polarOffset: ${biome.polar_offset},\n`;
        content += `        fallbackDistance: ${biome.fallback_distance},\n`;
        content += `        minMountainDistance: ${biome.min_mountain_distance}\n`;
        content += '    },\n';
    }
    content += '};\n\n';
    
    // Convenience lookups
    content += '// Convenience lookups\n';
    content += 'export const BIOME_IDS = Object.fromEntries(\n';
    content += '    Object.entries(BIOMES).map(([name, data]) => [name, data.id])\n';
    content += ');\n\n';
    
    content += 'export const BIOME_COLORS_RGB = Object.fromEntries(\n';
    content += '    Object.values(BIOMES).map(data => [data.id, data.rgb])\n';
    content += ');\n\n';
    
    content += 'export const BIOME_COLORS_HEX = Object.fromEntries(\n';
    content += '    Object.values(BIOMES).map(data => [data.id, data.hex])\n';
    content += ');\n\n';
    
    content += 'export const BIOME_NAMES = Object.fromEntries(\n';
    content += '    Object.entries(BIOMES).map(([name, data]) => [data.id, name])\n';
    content += ');\n\n';
    
    // Utility functions
    content += '// Utility functions\n';
    content += 'export function getBiomeName(biomeId) {\n';
    content += '    return BIOME_NAMES[biomeId] || `Unknown(${biomeId})`;\n';
    content += '}\n\n';
    
    content += 'export function getBiomeColorRgb(biomeId) {\n';
    content += '    return BIOME_COLORS_RGB[biomeId] || [255, 0, 255]; // Magenta for unknown\n';
    content += '}\n\n';
    
    content += 'export function getBiomeColorHex(biomeId) {\n';
    content += '    return BIOME_COLORS_HEX[biomeId] || "#FF00FF"; // Magenta for unknown\n';
    content += '}\n\n';
    
    content += 'export function isWithinWorldBounds(x, z) {\n';
    content += '    return Math.abs(x) <= VALHEIM_WORLD.RADIUS && Math.abs(z) <= VALHEIM_WORLD.RADIUS;\n';
    content += '}\n\n';
    
    content += 'export function distanceFromCenter(x, z) {\n';
    content += '    return Math.sqrt(x * x + z * z);\n';
    content += '}\n\n';
    
    content += 'export function worldToPixel(worldX, worldZ, resolution) {\n';
    content += '    const pixelX = Math.floor((worldX + VALHEIM_WORLD.RADIUS) * resolution / VALHEIM_WORLD.DIAMETER);\n';
    content += '    const pixelZ = Math.floor((worldZ + VALHEIM_WORLD.RADIUS) * resolution / VALHEIM_WORLD.DIAMETER);\n';
    content += '    return [pixelX, pixelZ];\n';
    content += '}\n\n';
    
    content += 'export function pixelToWorld(pixelX, pixelZ, resolution) {\n';
    content += '    const worldX = (pixelX * VALHEIM_WORLD.DIAMETER / resolution) - VALHEIM_WORLD.RADIUS;\n';
    content += '    const worldZ = (pixelZ * VALHEIM_WORLD.DIAMETER / resolution) - VALHEIM_WORLD.RADIUS;\n';
    content += '    return [worldX, worldZ];\n';
    content += '}\n';
    
    // Write file
    fs.writeFileSync(outputPath, content);
    console.log('JavaScript constants generated successfully!');
}

if (require.main === module) {
    generateJavaScriptConstants();
}

module.exports = { generateJavaScriptConstants };
