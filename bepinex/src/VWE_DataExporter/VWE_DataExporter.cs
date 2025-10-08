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
            _biomeResolution = Config.Bind("BiomeExport", "resolution", 2048, "Resolution for biome maps");

            // Heightmap export configuration
            _heightmapExportEnabled = Config.Bind("HeightmapExport", "enabled", true, "Export heightmap data");
            _heightmapResolution = Config.Bind("HeightmapExport", "resolution", 2048, "Resolution for heightmaps");

            // Structure export configuration
            _structureExportEnabled = Config.Bind("StructureExport", "enabled", true, "Export structure data");

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
                if (_logExports.Value)
                {
                    Logger.LogInfo("VWE DataExporter: Triggering data export...");
                }

                _exportTriggered = true;
                _exportCoroutine = StartCoroutine(ExportWorldData());
            }
            catch (Exception ex)
            {
                Logger.LogError($"VWE DataExporter: Failed to trigger export: {ex.Message}");
            }
        }

        private IEnumerator ExportWorldData()
        {
            var exportPath = Path.Combine(Application.dataPath, "..", _exportDir?.Value ?? "./world_data");
            exportPath = Path.GetFullPath(exportPath);

            // Export biome data
            if (_biomeExportEnabled?.Value == true)
            {
                yield return ExportBiomeData(exportPath);
            }

            // Export heightmap data
            if (_heightmapExportEnabled?.Value == true)
            {
                yield return ExportHeightmapData(exportPath);
            }

            // Export structure data
            if (_structureExportEnabled?.Value == true)
            {
                yield return ExportStructureData(exportPath);
            }

            if (_logExports?.Value == true)
            {
                Logger.LogInfo("VWE DataExporter: Data export completed successfully");
            }
        }

        private IEnumerator ExportBiomeData(string exportPath)
        {
            var biomeExporter = new BiomeExporter(Logger, _biomeResolution?.Value ?? 2048);
            yield return biomeExporter.ExportBiomes(exportPath, _exportFormat?.Value ?? "both");
        }

        private IEnumerator ExportHeightmapData(string exportPath)
        {
            var heightmapExporter = new HeightmapExporter(Logger, _heightmapResolution?.Value ?? 2048);
            yield return heightmapExporter.ExportHeightmap(exportPath, _exportFormat?.Value ?? "both");
        }

        private IEnumerator ExportStructureData(string exportPath)
        {
            var structureExporter = new StructureExporter(Logger);
            yield return structureExporter.ExportStructures(exportPath, _exportFormat?.Value ?? "both");
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
