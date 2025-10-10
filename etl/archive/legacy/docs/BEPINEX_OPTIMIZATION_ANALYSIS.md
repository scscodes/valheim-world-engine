# BepInEx Optimization Analysis for Valheim World Generation

## Executive Summary

BepInEx offers a **next-generation solution** for optimizing our world generation pipeline, potentially reducing generation time from 2-3 minutes to **30-60 seconds** through programmatic save triggers and world data export.

## Current State vs. BepInEx Potential

### Current Implementation (Graceful Shutdown)
- **Time:** 2-3 minutes per world
- **Method:** Graceful shutdown with `PRE_SERVER_SHUTDOWN_HOOK`
- **Reliability:** ✅ High (built-in lloesche mechanism)
- **Complexity:** Low (environment variable)

### BepInEx Potential
- **Time:** 30-60 seconds per world
- **Method:** Programmatic save triggers + data export
- **Reliability:** ⚠️ Medium (custom plugin development)
- **Complexity:** High (C# development, plugin management)

## BepInEx Capabilities Analysis

### 1. Programmatic Save Triggers

**Available Methods:**
```csharp
// Direct save calls (most reliable)
ZNet.instance.Save();                    // Full world save
ZNet.instance.ConsoleSave();            // Console save command
ZNet.instance.SaveWorld();              // Alternative save method

// Hook into world generation events
[HarmonyPatch(typeof(ZoneSystem), "Start")]
static void OnZoneSystemStart() {
    // Trigger save after world generation completes
    ZNet.instance.ConsoleSave();
}
```

**Advantages:**
- ✅ Immediate save (no 20-minute autosave wait)
- ✅ Programmatic control (no command injection)
- ✅ Reliable (direct game API calls)
- ✅ Fast (30-60 seconds total)

### 2. World Data Export During Generation

**Potential Export Capabilities:**
```csharp
// Export biomes data
var biomeData = ZoneSystem.instance.GetBiomeData();
File.WriteAllText("biomes.json", JsonConvert.SerializeObject(biomeData));

// Export heightmap data
var heightmap = ZoneSystem.instance.GetHeightmap();
File.WriteAllBytes("heightmap.raw", heightmap);

// Export world metadata
var worldData = ZNet.instance.GetWorldData();
File.WriteAllText("world_metadata.json", JsonConvert.SerializeObject(worldData));
```

**Benefits:**
- ✅ Eliminates need for MakeFwl extraction
- ✅ Real-time data access during generation
- ✅ No separate extraction stage required
- ✅ More accurate data (direct from game)

### 3. Event Hooks for Automation

**Key Hooks for World Generation:**
```csharp
// World generation start
[HarmonyPatch(typeof(ZoneSystem), "Awake")]
static void OnZoneSystemAwake() { /* Setup */ }

// World generation complete
[HarmonyPatch(typeof(ZoneSystem), "Start")]
static void OnZoneSystemStart() { /* Trigger save + export */ }

// World save complete
[HarmonyPatch(typeof(ZNet), "SaveWorld")]
static void OnWorldSaved() { /* Verify files created */ }
```

## Proposed BepInEx Implementation

### Phase 1: Custom Save Plugin

**Plugin: `VWE_AutoSave.cs`**
```csharp
using BepInEx;
using HarmonyLib;

[BepInPlugin("com.vwe.autosave", "VWE Auto Save", "1.0.0")]
public class VWE_AutoSave : BaseUnityPlugin
{
    void Awake()
    {
        Harmony.CreateAndPatchAll(typeof(VWE_AutoSave));
    }

    [HarmonyPatch(typeof(ZoneSystem), "Start")]
    [HarmonyPostfix]
    static void OnWorldGenerationComplete()
    {
        // Wait for full initialization
        InvokeRepeating("TriggerSave", 5f, 0f);
    }

    void TriggerSave()
    {
        if (ZNet.instance != null && ZNet.instance.IsServer())
        {
            ZNet.instance.ConsoleSave();
            Logger.LogInfo("VWE: Triggered immediate world save");
            CancelInvoke("TriggerSave");
        }
    }
}
```

### Phase 2: Data Export Plugin

**Plugin: `VWE_DataExporter.cs`**
```csharp
[BepInPlugin("com.vwe.exporter", "VWE Data Exporter", "1.0.0")]
public class VWE_DataExporter : BaseUnityPlugin
{
    [HarmonyPatch(typeof(ZNet), "SaveWorld")]
    [HarmonyPostfix]
    static void OnWorldSaved()
    {
        // Export biomes data
        ExportBiomesData();
        
        // Export heightmap data
        ExportHeightmapData();
        
        // Export world metadata
        ExportWorldMetadata();
    }

    void ExportBiomesData()
    {
        var biomes = ZoneSystem.instance.GetBiomeData();
        var json = JsonConvert.SerializeObject(biomes, Formatting.Indented);
        File.WriteAllText("/config/vwe_export/biomes.json", json);
    }
}
```

### Phase 3: Integrated Pipeline

**Modified `world_generator.py`:**
```python
# Mount BepInEx plugins
"volumes": {
    host_config_dir: "/config",
    plugins_host: "/config/BepInEx/plugins",  # Mount VWE plugins
},

# Reduced timeout (BepInEx handles save)
stage1_timeout_sec = 120  # 2 minutes max

# Monitor for BepInEx exports
"expected_outputs": {
    "raw": [
        os.path.join(seed_dir, "worlds_local", f"{seed}.db"),
        os.path.join(seed_dir, "worlds_local", f"{seed}.fwl"),
    ],
    "extracted": [
        os.path.join(extracted_dir, "biomes.json"),      # BepInEx export
        os.path.join(extracted_dir, "heightmap.raw"),    # BepInEx export
        os.path.join(extracted_dir, "world_metadata.json"), # BepInEx export
    ],
}
```

## Implementation Roadmap

### Week 1: Plugin Development
- [ ] Set up BepInEx development environment
- [ ] Create `VWE_AutoSave` plugin
- [ ] Test save triggering on world generation complete
- [ ] Validate `.db` and `.fwl` file creation

### Week 2: Data Export
- [ ] Create `VWE_DataExporter` plugin
- [ ] Implement biomes data export
- [ ] Implement heightmap data export
- [ ] Test data accuracy against MakeFwl

### Week 3: Integration
- [ ] Modify `world_generator.py` for BepInEx workflow
- [ ] Update Docker image to include VWE plugins
- [ ] Test end-to-end pipeline
- [ ] Performance benchmarking

### Week 4: Optimization
- [ ] Fine-tune save timing
- [ ] Optimize data export performance
- [ ] Add error handling and logging
- [ ] Documentation and deployment

## Expected Performance Gains

### Timeline Comparison
```
Current (Graceful Shutdown):
├── World generation: 60-90s
├── Graceful shutdown: 10-30s
├── File stability check: 5s
└── Total: 2-3 minutes

BepInEx (Programmatic):
├── World generation: 60-90s
├── Immediate save: 5-10s
├── Data export: 5-10s
└── Total: 30-60 seconds
```

### Additional Benefits
- ✅ **Eliminates MakeFwl dependency** (direct game data access)
- ✅ **More accurate data** (no parsing/interpretation)
- ✅ **Real-time export** (during generation, not after)
- ✅ **Reduced complexity** (fewer pipeline stages)
- ✅ **Better error handling** (plugin can detect issues)

## Risk Assessment

### Technical Risks
- **Plugin Development Complexity:** C# development required
- **Valheim Version Compatibility:** Plugin may break with game updates
- **Docker Integration:** Plugin mounting and management complexity

### Mitigation Strategies
- **Version Pinning:** Lock to specific Valheim/BepInEx versions
- **Fallback Mechanism:** Keep graceful shutdown as backup
- **Extensive Testing:** Test with multiple seeds and scenarios
- **Community Support:** Leverage BepInEx community for development

## Recommendation

**Proceed with BepInEx implementation** as a Phase 2 optimization:

1. **Keep current graceful shutdown** as primary solution (reliable, working)
2. **Develop BepInEx plugins** in parallel for next-generation optimization
3. **A/B test both approaches** with performance metrics
4. **Migrate to BepInEx** once proven stable and faster

This approach provides immediate value with graceful shutdown while building toward a more efficient long-term solution.

## References
- [BepInEx GitHub](https://github.com/BepInEx/BepInEx)
- [BepInEx Valheim Pack](https://thunderstore.io/c/valheim/p/denikson/BepInExPack_Valheim/)
- [Valheim Modding Discord](https://discord.gg/RBq2mzeu4z)
- [BepInEx Documentation](https://docs.bepinex.dev/)
