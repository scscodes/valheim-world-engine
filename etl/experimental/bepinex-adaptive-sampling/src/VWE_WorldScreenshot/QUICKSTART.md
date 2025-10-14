# Quick Start - VWE World Screenshot Plugin

## Build

```bash
cd etl/experimental/bepinex-adaptive-sampling/src/VWE_WorldScreenshot
./build.sh
```

## Deploy

```bash
# Copy DLL to plugins directory
cp bin/Release/net48/VWE_WorldScreenshot.dll ../../plugins/
```

## Test

```bash
# Run with test seed
cd ../..
python tests/validate_performance.py --seed "hnLycKKCMI"

# Check for screenshot
ls -lh output/world_data/minimap_screenshot*.png
```

## Logs

```bash
# Watch for screenshot capture in logs
docker logs -f vwe-adaptive-sampling-test | grep "WorldScreenshot"
```

## Expected Output

```
[Info   : VWE World Screenshot] ★★★ VWE World Screenshot v1.0.0 loaded
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Conditions met, scheduling capture
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: Starting capture
[Info   : VWE World Screenshot] ★★★ WorldScreenshot: COMPLETE - Screenshot saved (2345KB)
```

## Output Files

```
output/world_data/
├── minimap_screenshot_hnLycKKCMI_<timestamp>.png
└── minimap_screenshot_hnLycKKCMI_<timestamp>_metadata.json
```

## Configuration

Edit `BepInEx/config/com.vwe.worldscreenshot.cfg` to customize:
- Resolution
- Capture delay
- Export path

## Troubleshooting

**No screenshot generated:**
- Check logs for errors
- Increase CaptureDelay in config
- Verify export path exists

**Black/empty screenshot:**
- Increase CaptureDelay to 20-30 seconds
- Check if minimap is initialized

See README.md for full documentation.
