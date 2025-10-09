# Valheim Map Viewer - Client

Simple HTML5/Canvas visualization of 512×512 Valheim world samples.

## Features

- **Biome Map:** Color-coded biome visualization
- **Height Map:** Grayscale elevation visualization
- **Scalable:** Render at 512px (native) up to 2048px (4x upscaled)
- **Smoothing Options:**
  - Pixelated (sharp, retro look)
  - Bicubic (smooth, production-ready)
- **Interactive:** Mouse hover shows coordinates, biome, and height
- **Export:** Download rendered map as PNG

## Quick Start

### 1. Start Development Server

```bash
cd procedural-export/client
python3 serve.py
```

Server runs at: http://localhost:8080/client/

### 2. Open in Browser

Navigate to http://localhost:8080/client/ and click "Load Map Data"

## Files

- `index.html` - Main UI and layout
- `renderer.js` - Canvas rendering logic
- `serve.py` - Simple HTTP server with CORS

## Configuration

### Render Modes

- **Biomes:** Display color-coded biome map (default)
- **Height Map:** Grayscale elevation map

### Canvas Sizes

- **512×512** - Native resolution (pixelated)
- **768×768** - 1.5x upscaled
- **1024×1024** - 2x upscaled (recommended) ✓
- **1536×1536** - 3x upscaled
- **2048×2048** - 4x upscaled (smooth)

### Smoothing

- **Pixelated (Sharp):** CSS `image-rendering: pixelated` - Retro Minecraft-like look
- **Smooth (Bicubic):** CSS `image-rendering: auto` - Browser applies bicubic interpolation

## Data Format

Expects samples JSON at: `../output/samples/hkLycKKCMI-samples-512.json`

```json
{
  "WorldName": "hkLycKKCMI",
  "Resolution": 512,
  "SampleCount": 262144,
  "Samples": [
    {"X": -5000.0, "Z": -5000.0, "Biome": 512, "Height": 80.5},
    ...
  ]
}
```

## Biome Colors

| Biome | Color (RGB) | Enum |
|-------|-------------|------|
| Meadows | (121, 179, 85) | 1 |
| BlackForest | (64, 81, 50) | 2 |
| Swamp | (119, 108, 82) | 4 |
| Mountain | (220, 225, 238) | 8 |
| Plains | (193, 181, 122) | 16 |
| Ocean | (59, 103, 163) | 32 |
| Mistlands | (78, 93, 107) | 64 |
| DeepNorth | (210, 230, 255) | 256 |
| Ashlands | (155, 75, 60) | 512 |

## Performance

- **Load time:** ~500ms for 26MB JSON
- **Render time:** ~100-300ms depending on canvas size
- **Total:** <1 second from click to display

## Browser Compatibility

- Chrome/Edge: ✓ Full support
- Firefox: ✓ Full support
- Safari: ✓ Full support (iOS may struggle with 2048px)

## Future Enhancements

- [ ] Zoom/pan controls
- [ ] Coordinate search
- [ ] Biome statistics
- [ ] Compare multiple worlds
- [ ] 3D terrain view
- [ ] Structure overlay
- [ ] Distance measurements
