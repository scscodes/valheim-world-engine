# VWE World Screenshot Plugin

**Version:** 1.0.0 (Proof of Concept)
**Purpose:** Capture high-resolution minimap screenshots from Valheim dedicated server

## Overview

This BepInEx plugin automatically captures a screenshot of the entire world minimap when the server starts. The screenshot is taken from Valheim's actual game rendering engine, providing the artistic/aesthetic look that matches what players see in-game.

## Features

- ✅ Automatic capture on world load
- ✅ Full map reveal (no fog of war)
- ✅ Configurable resolution
- ✅ PNG export with metadata
- ✅ Server-side only (no client mods required)
- ✅ One-shot capture (doesn't repeat)

## How It Works

1. Plugin loads when server starts
2. Waits for world to fully initialize
3. Reveals entire minimap (`ExploreAll()`)
4. Captures the minimap texture
5. Exports as PNG to `world_data/` directory
6. Creates metadata JSON with capture info

## Configuration

Configuration file: `BepInEx/config/com.vwe.worldscreenshot.cfg`

```ini
[General]

## Enable automatic screenshot capture on world load
# Setting type: Boolean
# Default value: true
Enabled = true

## Screenshot resolution (0 = native minimap resolution)
# Setting type: Int32
# Default value: 2048
Resolution = 2048

## Seconds to wait after world load before capturing
# Setting type: Single
# Default value: 15
CaptureDelay = 15.0

## Export path for screenshots (absolute path)
# Setting type: String
# Default value: /opt/valheim/world_data
ExportPath = /opt/valheim/world_data
```

## Building

```bash
cd src/VWE_WorldScreenshot
dotnet build -c Release
```

Output: `bin/Release/net48/VWE_WorldScreenshot.dll`

## Installation

1. Copy `VWE_WorldScreenshot.dll` to `BepInEx/plugins/`
2. (Optional) Edit config file to customize settings
3. Start Valheim server
4. Screenshot will be saved to configured export path

## Output Files

```
world_data/
├── minimap_screenshot_<worldname>_<timestamp>.png
└── minimap_screenshot_<worldname>_<timestamp>_metadata.json
```

### Example

```
world_data/
├── minimap_screenshot_hnLycKKCMI_20251014_153045.png
└── minimap_screenshot_hnLycKKCMI_20251014_153045_metadata.json
```

### Metadata Format

```json
{
  "world_name": "hnLycKKCMI",
  "resolution": {
    "width": 2048,
    "height": 2048
  },
  "capture_timestamp": "2025-10-14T15:30:45.1234567Z",
  "plugin_version": "1.0.0",
  "world_radius": 10000.0,
  "world_diameter": 20000.0
}
```

## Logging

Plugin logs all actions with `★★★` prefix for easy filtering:

```
[Info   : VWE World Screenshot] ★★★ VWE World Screenshot v1.0.0 loaded
[Info   : VWE World Screenshot] ★★★ Export path: /opt/valheim/world_data
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Conditions met, scheduling capture
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Starting capture
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Revealing entire map
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Capturing minimap texture
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Got texture 2048x2048
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Encoding to PNG
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Writing to /opt/valheim/world_data/minimap_screenshot_hnLycKKCMI_20251014_153045.png
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: COMPLETE - Screenshot saved (2345KB)
```

## Troubleshooting

### Screenshot not captured

**Check logs:**
```bash
docker logs valheim-server | grep "WorldScreenshot"
```

**Common issues:**
- World not fully loaded → Increase `CaptureDelay`
- Minimap not initialized → Check for errors in logs
- Export path doesn't exist → Will be created automatically

### Screenshot is black/empty

- Increase `CaptureDelay` to 20-30 seconds
- Verify world loaded correctly
- Check console for errors

### Plugin not loading

- Verify BepInEx is installed correctly
- Check `BepInEx/LogOutput.log` for errors
- Ensure .NET 4.8 dependencies are present

## Integration with Adaptive Sampling Pipeline

This plugin complements the existing data exporters:

```
VWE_DataExporter    → biomes.json, heightmap.json  (data)
VWE_WorldScreenshot → minimap_screenshot.png        (visual)
```

Use the screenshot for:
- Visual validation of data renders
- User-facing world previews
- Marketing/aesthetic displays
- Comparison with procedurally generated renders

## Known Limitations

**Proof of Concept Status:**
- Single capture only (doesn't support re-capture)
- Resolution limited by Valheim's minimap texture
- No custom rendering options (uses default minimap style)
- Requires minimap to be generated (happens during world init)

**Future Enhancements:**
- Multi-resolution export
- Custom rendering passes
- Comparison with data renders
- Animated capture (timelapse)

## Dependencies

- BepInEx 5.x
- Valheim (dedicated server)
- .NET Framework 4.8
- Newtonsoft.Json

## License

Part of Valheim World Engine project

## Author

VWE Development Team

## Version History

- **1.0.0** (2025-10-14): Initial proof-of-concept release
  - Basic minimap capture
  - PNG export
  - Metadata generation
  - Configurable resolution
