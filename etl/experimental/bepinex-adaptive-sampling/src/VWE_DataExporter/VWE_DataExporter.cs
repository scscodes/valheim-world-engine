using System;
using System.Collections;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;
using VWE_DataExporter.DataExporters;

namespace VWE_DataExporter
{
    [BepInPlugin(PluginGUID, PluginName, PluginVersion)]
    public class VWE_DataExporterPlugin : BaseUnityPlugin
    {
        public const string PluginGUID = "com.valheimworldengine.dataexporter";
        public const string PluginName = "VWE DataExporter";
        public const string PluginVersion = "1.0.0";

        private static ConfigEntry<bool>? _enabled;
        private static ConfigEntry<string>? _exportFormat;
        private static ConfigEntry<float>? _exportInterval;
        private static ConfigEntry<string>? _exportDir;
        private static ConfigEntry<bool>? _logExports;
        private static ConfigEntry<bool>? _logDebug;

        private static ConfigEntry<bool>? _biomeExportEnabled;
        private static ConfigEntry<int>? _biomeResolution;
        private static ConfigEntry<bool>? _heightmapExportEnabled;
        private static ConfigEntry<int>? _heightmapResolution;
        private static ConfigEntry<bool>? _structureExportEnabled;

        // Dynamic yield configuration (global for all exporters)
        private static ConfigEntry<bool>? _useDynamicYield;
        private static ConfigEntry<int>? _yieldIntervalMs;

        private static ManualLogSource? _logger;

        private static bool _worldGenerationComplete = false;
        private static bool _exportTriggered = false;
        private static Coroutine? _exportCoroutine;

        private void Awake()
        {
            // Store logger for static access
            _logger = Logger;
            
            // Main configuration
            _enabled = Config.Bind("DataExporter", "enabled", true, "Enable/disable data export");
            _exportFormat = Config.Bind("DataExporter", "export_format", "both", "Export format: json, png, both");
            _exportInterval = Config.Bind("DataExporter", "export_interval", 0f, "Export interval (seconds, 0 = on-demand)");
            _exportDir = Config.Bind("DataExporter", "export_dir", "./world_data", "Export directory (relative to Valheim root)");
            _logExports = Config.Bind("DataExporter", "log_exports", true, "Log export events");
            _logDebug = Config.Bind("DataExporter", "log_debug", false, "Enable debug logging");

            // Biome export configuration
            _biomeExportEnabled = Config.Bind("BiomeExport", "enabled", true, "Export biome data");
            _biomeResolution = Config.Bind("BiomeExport", "resolution", 512, "Resolution for biome maps");

            // Heightmap export configuration
            _heightmapExportEnabled = Config.Bind("HeightmapExport", "enabled", true, "Export heightmap data");
            _heightmapResolution = Config.Bind("HeightmapExport", "resolution", 512, "Resolution for heightmaps");

            // Structure export configuration
            _structureExportEnabled = Config.Bind("StructureExport", "enabled", true, "Export structure data");

            // Dynamic yield configuration (global for all exporters)
            _useDynamicYield = Config.Bind("Performance", "use_dynamic_yield", false, "Use time-based yielding instead of sample-based (experimental)");
            _yieldIntervalMs = Config.Bind("Performance", "yield_interval_ms", 100, "Yield interval in milliseconds for time-based yielding");

            if (_enabled.Value)
            {
                Logger.LogInfo("VWE DataExporter plugin loaded and enabled");
                
                // Apply Harmony patches
                var harmony = new Harmony(PluginGUID);
                harmony.PatchAll();
                
                Logger.LogInfo("VWE DataExporter patches applied");
            }
            else
            {
                Logger.LogInfo("VWE DataExporter plugin loaded but disabled");
            }
        }

        private void Start()
        {
            if (!_enabled.Value) return;

            // Create export directory
            CreateExportDirectory();

            // Start monitoring for world generation completion
            StartCoroutine(MonitorWorldGeneration());
        }

        private void CreateExportDirectory()
        {
            try
            {
                var exportPath = Path.Combine(Application.dataPath, "..", _exportDir.Value);
                exportPath = Path.GetFullPath(exportPath);
                
                if (!Directory.Exists(exportPath))
                {
                    Directory.CreateDirectory(exportPath);
                    Logger.LogInfo($"VWE DataExporter: Created export directory: {exportPath}");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError($"VWE DataExporter: Failed to create export directory: {ex.Message}");
            }
        }

        private IEnumerator MonitorWorldGeneration()
        {
            while (true)
            {
                if (_worldGenerationComplete && !_exportTriggered)
                {
                    yield return new WaitForSeconds(2f); // Wait 2 seconds after world generation
                    TriggerDataExport();
                }
                
                yield return new WaitForSeconds(1f);
            }
        }

        private void TriggerDataExport()
        {
            if (_exportTriggered) return;

            try
            {
                Logger.LogInfo("★★★ VWE_DataExporter: TriggerDataExport called");

                _exportTriggered = true;

                Logger.LogInfo("★★★ VWE_DataExporter: Starting ExportWorldData coroutine");
                _exportCoroutine = StartCoroutine(ExportWorldData());
                Logger.LogInfo("★★★ VWE_DataExporter: ExportWorldData coroutine started successfully");
            }
            catch (Exception ex)
            {
                Logger.LogError($"★★★ VWE_DataExporter: FATAL - Failed to start export coroutine: {ex.GetType().Name} - {ex.Message}\nStack: {ex.StackTrace}");
            }
        }

        private IEnumerator ExportWorldData()
        {
            var startTime = DateTime.Now;
            Logger.LogInfo("★★★ VWE_DataExporter: ExportWorldData coroutine ENTERED");

            string exportPath;
            try
            {
                exportPath = Path.Combine(Application.dataPath, "..", _exportDir?.Value ?? "./world_data");
                exportPath = Path.GetFullPath(exportPath);
                Logger.LogInfo($"★★★ VWE_DataExporter: Export path resolved: {exportPath}");

                // Verify directory exists
                if (!Directory.Exists(exportPath))
                {
                    Logger.LogWarning($"★★★ VWE_DataExporter: Export directory doesn't exist, creating: {exportPath}");
                    Directory.CreateDirectory(exportPath);
                }
                Logger.LogInfo($"★★★ VWE_DataExporter: Export directory verified");
            }
            catch (Exception ex)
            {
                Logger.LogError($"★★★ VWE_DataExporter: FATAL - Error resolving export path: {ex.GetType().Name} - {ex.Message}");
                yield break;
            }

            // Export biome data
            if (_biomeExportEnabled?.Value == true)
            {
                Logger.LogInfo("★★★ VWE_DataExporter: Starting biome export phase");
                yield return ExportBiomeData(exportPath);
                Logger.LogInfo("★★★ VWE_DataExporter: Biome export phase completed");
            }
            else
            {
                Logger.LogInfo("★★★ VWE_DataExporter: Biome export SKIPPED (disabled)");
            }

            // Export heightmap data
            if (_heightmapExportEnabled?.Value == true)
            {
                Logger.LogInfo("★★★ VWE_DataExporter: Starting heightmap export phase");
                yield return ExportHeightmapData(exportPath);
                Logger.LogInfo("★★★ VWE_DataExporter: Heightmap export phase completed");
            }
            else
            {
                Logger.LogInfo("★★★ VWE_DataExporter: Heightmap export SKIPPED (disabled)");
            }

            // Export structure data
            if (_structureExportEnabled?.Value == true)
            {
                Logger.LogInfo("★★★ VWE_DataExporter: Starting structure export phase");
                yield return ExportStructureData(exportPath);
                Logger.LogInfo("★★★ VWE_DataExporter: Structure export phase completed");
            }
            else
            {
                Logger.LogInfo("★★★ VWE_DataExporter: Structure export SKIPPED (disabled)");
            }

            var totalTime = (DateTime.Now - startTime).TotalSeconds;
            Logger.LogInfo($"★★★ VWE_DataExporter: ALL EXPORTS COMPLETE - Total time: {totalTime:F1}s");
        }

        private IEnumerator ExportBiomeData(string exportPath)
        {
            Logger.LogInfo("★★★ VWE_DataExporter: Creating BiomeExporter instance");
            var biomeExporter = new BiomeExporter(
                Logger,
                _biomeResolution?.Value ?? 512,
                _useDynamicYield?.Value ?? false,
                _yieldIntervalMs?.Value ?? 100
            );
            Logger.LogInfo("★★★ VWE_DataExporter: Calling BiomeExporter.ExportBiomes");
            yield return biomeExporter.ExportBiomes(exportPath, _exportFormat?.Value ?? "both");
            Logger.LogInfo("★★★ VWE_DataExporter: BiomeExporter.ExportBiomes returned");
        }

        private IEnumerator ExportHeightmapData(string exportPath)
        {
            Logger.LogInfo("★★★ VWE_DataExporter: Creating HeightmapExporter instance");
            var heightmapExporter = new HeightmapExporter(
                Logger,
                _heightmapResolution?.Value ?? 512,
                _useDynamicYield?.Value ?? false,
                _yieldIntervalMs?.Value ?? 100
            );
            Logger.LogInfo("★★★ VWE_DataExporter: Calling HeightmapExporter.ExportHeightmap");
            yield return heightmapExporter.ExportHeightmap(exportPath, _exportFormat?.Value ?? "both");
            Logger.LogInfo("★★★ VWE_DataExporter: HeightmapExporter.ExportHeightmap returned");
        }

        private IEnumerator ExportStructureData(string exportPath)
        {
            Logger.LogInfo("★★★ VWE_DataExporter: Creating StructureExporter instance");
            var structureExporter = new StructureExporter(Logger);
            Logger.LogInfo("★★★ VWE_DataExporter: Calling StructureExporter.ExportStructures");
            yield return structureExporter.ExportStructures(exportPath, _exportFormat?.Value ?? "both");
            Logger.LogInfo("★★★ VWE_DataExporter: StructureExporter.ExportStructures returned");
        }

        // Harmony patch to detect world generation completion
        [HarmonyPatch(typeof(ZoneSystem), "Start")]
        public static class ZoneSystemStartPatch
        {
            public static void Postfix(ZoneSystem __instance)
            {
                if (_enabled?.Value != true) return;

                // ★★★ PROMINENT DEBUG LOGGING ★★★
                _logger?.LogInfo("★★★ VWE DataExporter: HOOK EXECUTED - ZoneSystem.Start detected ★★★");

                if (_logDebug?.Value == true)
                {
                    _logger?.LogInfo("VWE DataExporter: ZoneSystem.Start detected");
                }

                // Mark world generation as complete
                _worldGenerationComplete = true;

                if (_logExports?.Value == true)
                {
                    _logger?.LogInfo("VWE DataExporter: World generation complete, data export will be triggered");
                }
            }
        }

        // Harmony patch to detect when world is ready for data export
        [HarmonyPatch(typeof(ZNet), "OnNewConnection")]
        public static class ZNetOnNewConnectionPatch
        {
            public static void Postfix(ZNet __instance, ZNetPeer peer)
            {
                if (_enabled?.Value != true) return;

                if (_logDebug?.Value == true)
                {
                    _logger?.LogInfo("VWE DataExporter: New connection detected, checking world status");
                }

                // Check if world is ready for data export
                if (__instance.IsServer() && __instance.IsDedicated() && !_worldGenerationComplete)
                {
                    // Give some time for world generation to complete
                    __instance.StartCoroutine(CheckWorldGenerationStatus());
                }
            }
        }

        private static IEnumerator CheckWorldGenerationStatus()
        {
            yield return new WaitForSeconds(10f); // Wait 10 seconds after server start
            
            if (!_worldGenerationComplete)
            {
                _worldGenerationComplete = true;
                
                if (_logExports?.Value == true)
                {
                    _logger?.LogInfo("VWE DataExporter: World generation assumed complete (timeout), data export will be triggered");
                }
            }
        }
    }
}
