# World Screenshot Exporter Plugin

**Status:** Design Phase → Implementation
**Purpose:** Capture high-resolution, game-rendered world map directly from Valheim server
**Requirement:** Server-side only, no client mods required

---

## Overview

BepInEx plugin that captures the minimap texture directly from Valheim's game engine, providing the "artistic" rendering style that matches player exploration maps (like `biomes_hnLycKKCMI.png`).

**Why This Matters:**
- Current approach: Data-driven rendering (pure biome colors)
- Screenshot approach: Game-engine rendering (artistic, with lighting/blending)
- Gets you the "reference image" look automatically
- Perfect for visual validation and comparison

---

## Technical Approach

### Method 1: Minimap Texture Capture (Recommended)

Valheim's `Minimap` class maintains a rendered texture of the explored world. We can:
1. Programmatically reveal entire map
2. Force minimap rendering at high resolution
3. Capture the rendered texture
4. Export as PNG

**Advantages:**
- Uses Valheim's actual rendering pipeline
- Matches in-game aesthetic perfectly
- Includes terrain shading, colors, artistic effects
- Relatively simple implementation

**Code Concept:**
```csharp
[BepInPlugin("com.vwe.worldscreenshot", "World Screenshot Exporter", "1.0.0")]
public class WorldScreenshotExporter : BaseUnityPlugin
{
    void Awake()
    {
        // Wait for world to load, then capture
        InvokeRepeating(nameof(CheckAndCapture), 5f, 5f);
    }

    void CheckAndCapture()
    {
        if (ZoneSystem.instance == null || !ZoneSystem.instance.IsZoneLoaded())
            return;

        if (Minimap.instance == null)
            return;

        // Already captured?
        if (HasCaptured()) return;

        Logger.LogInfo("World loaded - capturing minimap screenshot");
        CaptureMinimapScreenshot();
        MarkCaptured();
    }

    void CaptureMinimapScreenshot()
    {
        // 1. Reveal entire map
        Minimap.instance.RevealAll();

        // 2. Get minimap texture
        Texture2D mapTexture = Minimap.instance.GetMapTexture();

        // 3. Export to PNG
        byte[] pngBytes = mapTexture.EncodeToPNG();
        string path = $"/config/world_data/minimap_screenshot_{WorldName}_{DateTime.Now:yyyyMMdd_HHmmss}.png";
        File.WriteAllBytes(path, pngBytes);

        Logger.LogInfo($"Screenshot saved: {path}");
    }
}
```

### Method 2: Custom High-Resolution Render

For even higher quality, we can render at custom resolution:

```csharp
void CaptureHighResScreenshot(int resolution = 4096)
{
    // Create high-res render texture
    RenderTexture rt = new RenderTexture(resolution, resolution, 24);
    RenderTexture previous = RenderTexture.active;
    RenderTexture.active = rt;

    // Render minimap to our texture at high resolution
    // (This requires accessing Minimap's rendering internals)
    Minimap.instance.RenderMap(rt, resolution);

    // Read pixels
    Texture2D screenshot = new Texture2D(resolution, resolution, TextureFormat.RGB24, false);
    screenshot.ReadPixels(new Rect(0, 0, resolution, resolution), 0, 0);
    screenshot.Apply();

    // Export
    byte[] pngBytes = screenshot.EncodeToPNG();
    File.WriteAllBytes(outputPath, pngBytes);

    // Cleanup
    RenderTexture.active = previous;
    Destroy(screenshot);
    rt.Release();
}
```

---

## Features

### Core Functionality

1. **Automatic Capture on World Load**
   - Detects when world is fully initialized
   - Captures screenshot automatically
   - One-shot operation (doesn't repeat)

2. **Configurable Resolution**
   - Default: Native minimap resolution (~2048x2048)
   - Optional: Custom high-res (4096x4096, 8192x8192)
   - Balances quality vs file size

3. **Export Formats**
   - PNG (primary)
   - Optional: WebP for smaller size
   - Metadata JSON (world name, seed, resolution, timestamp)

4. **Integration with Existing Pipeline**
   - Exports to same `world_data/` directory as BepInEx data exporters
   - Compatible with adaptive-sampling workflow
   - Naming convention matches other exports

### Configuration Options

```ini
[WorldScreenshot]
# Enable automatic screenshot capture
Enabled = true

# Resolution (0 = native minimap resolution, or specify custom)
Resolution = 4096

# Export format
Format = PNG

# Export path (relative to config dir)
ExportPath = world_data

# Capture delay after world load (seconds)
CaptureDelay = 10.0

# Include metadata JSON
ExportMetadata = true
```

---

## Implementation Plan

### File Structure

```
etl/experimental/bepinex-adaptive-sampling/
├── src/
│   ├── VWE_WorldScreenshot/
│   │   ├── VWE_WorldScreenshot.csproj
│   │   ├── WorldScreenshotPlugin.cs
│   │   ├── MinimapCapture.cs
│   │   └── ScreenshotConfig.cs
├── plugins/
│   └── VWE_WorldScreenshot.dll  (compiled output)
├── config/
│   └── VWE_WorldScreenshot.cfg
└── README.md
```

### Dependencies

```xml
<!-- VWE_WorldScreenshot.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net48</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
    <!-- BepInEx -->
    <PackageReference Include="BepInEx.Core" Version="5.4.23.2" />
    <PackageReference Include="BepInEx.PluginInfoProps" Version="2.1.0" />

    <!-- Valheim assemblies (from game install) -->
    <Reference Include="assembly_valheim">
      <HintPath>$(ValheimInstall)\valheim_Data\Managed\assembly_valheim.dll</HintPath>
    </Reference>
    <Reference Include="UnityEngine">
      <HintPath>$(ValheimInstall)\unstripped_corlib\UnityEngine.dll</HintPath>
    </Reference>
    <Reference Include="UnityEngine.CoreModule">
      <HintPath>$(ValheimInstall)\unstripped_corlib\UnityEngine.CoreModule.dll</HintPath>
    </Reference>
  </ItemGroup>
</Project>
```

---

## Integration with Adaptive Sampling Pipeline

### Workflow Enhancement

**Current Pipeline:**
```
1. Start Valheim server with BepInEx
2. Export biome data (VWE_DataExporter)
3. Export heightmap data (VWE_DataExporter)
4. Generate renders from data (Python backend)
```

**Enhanced Pipeline:**
```
1. Start Valheim server with BepInEx
2. Export biome data (VWE_DataExporter)
3. Export heightmap data (VWE_DataExporter)
4. Capture minimap screenshot (VWE_WorldScreenshot) ← NEW
5. Generate renders from data (Python backend)
6. Compare data renders vs screenshot ← NEW VALIDATION
```

### Output Structure

```
data/seeds/{seed_hash}/
├── world_data/
│   ├── biomes.json              (existing)
│   ├── biomes.png               (existing - data visualization)
│   ├── heightmap.json           (existing)
│   ├── heightmap.png            (existing - data visualization)
│   ├── minimap_screenshot.png   (NEW - game-rendered)
│   └── minimap_metadata.json    (NEW - screenshot info)
```

### Metadata Format

```json
{
  "world_name": "hnLycKKCMI",
  "seed": "hnLycKKCMI",
  "resolution": 4096,
  "capture_timestamp": "2025-10-14T15:30:00Z",
  "valheim_version": "0.217.38",
  "bepinex_version": "5.4.23.2",
  "plugin_version": "1.0.0",
  "world_bounds": {
    "radius": 10000.0,
    "diameter": 20000.0
  }
}
```

---

## Usage Examples

### Standalone Export

```bash
# Run server with screenshot plugin
docker-compose up -d valheim

# Wait for world load and screenshot capture (~30 seconds)
# Check logs
docker logs valheim-server | grep "Screenshot saved"

# Screenshot will be in:
# ./valheim_data/world_data/minimap_screenshot_hnLycKKCMI_20251014.png
```

### With Validation Script

```python
# scripts/validate_with_screenshot.py
def compare_renders():
    # Load data-driven render
    client_render = Image.open("biomes_height_aware_wl25.png")

    # Load game-rendered screenshot
    game_screenshot = Image.open("minimap_screenshot.png")

    # Visual comparison
    compare_images(client_render, game_screenshot)

    # SSIM, histogram comparison, etc.
    metrics = calculate_similarity(client_render, game_screenshot)

    return metrics
```

---

## Advanced Features (Future)

### 1. Multi-Resolution Export
Export at multiple resolutions automatically:
- 1024x1024 (preview)
- 2048x2048 (standard)
- 4096x4096 (high quality)
- 8192x8192 (ultra quality)

### 2. Explored vs Full Map
- Capture with exploration fog (realistic player experience)
- Capture with full reveal (complete world view)
- Both exported for comparison

### 3. Layered Export
- Terrain only
- Terrain + fog
- Terrain + fog + pins/markers
- Separate layers for compositing

### 4. Animated GIF
- Capture minimap during world generation
- Create timelapse of world reveal
- Show progression of exploration

### 5. Comparison View
- Side-by-side: data render vs game screenshot
- Difference map highlighting discrepancies
- Automatic quality report

---

## Performance Considerations

### Capture Time
- Native resolution: ~1-2 seconds
- 4096x4096: ~3-5 seconds
- 8192x8192: ~10-15 seconds

### Memory Usage
- 2048x2048 PNG: ~5-10 MB
- 4096x4096 PNG: ~20-40 MB
- 8192x8192 PNG: ~80-150 MB

### Server Impact
- Capture happens once during startup
- No ongoing performance impact
- Can be disabled after capture

---

## Troubleshooting

### Screenshot is Black/Empty
**Cause:** Minimap not fully rendered yet
**Solution:** Increase `CaptureDelay` in config

### Screenshot Shows Only Partial Map
**Cause:** World not fully loaded
**Solution:** Ensure all zones are generated first

### Plugin Not Loading
**Cause:** Missing dependencies
**Solution:** Verify BepInEx installation, check console logs

### Screenshot Quality Issues
**Cause:** Texture compression
**Solution:** Use higher resolution, check Unity texture import settings

---

## Comparison: Data Render vs Screenshot

| Feature | Data Render | Game Screenshot |
|---------|-------------|-----------------|
| **Colors** | Pure biome colors | Artistic blending |
| **Resolution** | Any (upscaled) | Native + custom |
| **Accuracy** | 100% data fidelity | Visual representation |
| **Style** | Cartographic | Aesthetic |
| **Generation** | Fast (seconds) | Requires world load |
| **Use Case** | Analysis, validation | Visual preview, marketing |

**Recommendation:** Generate both!
- Data render: For technical validation and debugging
- Screenshot: For user-facing displays and visual appeal

---

## Next Steps

1. **Implement Basic Plugin** (2-3 hours)
   - Core screenshot capture
   - PNG export
   - Basic configuration

2. **Test with hnLycKKCMI Seed** (1 hour)
   - Run with current test seed
   - Compare with existing reference
   - Verify visual quality

3. **Integrate with Pipeline** (1-2 hours)
   - Update docker-compose
   - Add to validation scripts
   - Documentation

4. **Advanced Features** (Future)
   - High-res rendering
   - Multi-format export
   - Comparison tooling

---

## References

- [Valheim Minimap Class](https://github.com/Valheim-Modding/Jotunn/blob/dev/JotunnLib/Managers/MinimapManager.cs)
- [Unity RenderTexture](https://docs.unity3d.com/ScriptReference/RenderTexture.html)
- [BepInEx Plugin Tutorial](https://docs.bepinex.dev/articles/dev_guide/plugin_tutorial/)

---

**Status:** Ready for implementation
**Estimated Time:** 4-6 hours for MVP
**Priority:** High (directly supports world generation validation)

**Last Updated:** 2025-10-14
**Author:** Claude Code
**Related:** `docs/SERVER_SIDE_TELEMETRY.md`
