using System;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;
using Newtonsoft.Json;

namespace VWE_ProceduralMetadata
{
    [BepInPlugin(PluginGUID, PluginName, PluginVersion)]
    public class VWE_ProceduralMetadataPlugin : BaseUnityPlugin
    {
        public const string PluginGUID = "com.valheimworldengine.proceduralmetadata";
        public const string PluginName = "VWE Procedural Metadata";
        public const string PluginVersion = "1.0.0";

        private static ConfigEntry<bool>? _enabled;
        private static ConfigEntry<string>? _exportDir;
        private static ConfigEntry<bool>? _enableOptimalSampling;
        private static ConfigEntry<int>? _optimalResolution;
        private static ManualLogSource? _logger;
        private static bool _exportTriggered = false;
        private static UnityEngine.Coroutine? _samplingCoroutine;

        private void Awake()
        {
            _logger = Logger;

            // Configuration
            _enabled = Config.Bind("General", "enabled", true, "Enable/disable metadata export");
            _exportDir = Config.Bind("General", "export_dir", "./procedural_metadata", "Export directory");
            _enableOptimalSampling = Config.Bind("OptimalSampling", "enabled", true, "Enable 1024x1024 optimal sampling for validation");
            _optimalResolution = Config.Bind("OptimalSampling", "resolution", 1024, "Sample resolution (1024 for full Valheim world)");

            if (_enabled.Value)
            {
                Logger.LogInfo($"{PluginName} v{PluginVersion} loaded and enabled");

                // Apply Harmony patches
                var harmony = new Harmony(PluginGUID);
                harmony.PatchAll();

                Logger.LogInfo($"{PluginName} patches applied");
            }
            else
            {
                Logger.LogInfo($"{PluginName} loaded but disabled");
            }
        }

        private void Start()
        {
            if (!_enabled.Value) return;

            // Create export directory
            CreateExportDirectory();
        }

        private void CreateExportDirectory()
        {
            try
            {
                var exportPath = Path.Combine(UnityEngine.Application.dataPath, "..", _exportDir.Value);
                exportPath = Path.GetFullPath(exportPath);

                if (!Directory.Exists(exportPath))
                {
                    Directory.CreateDirectory(exportPath);
                    Logger.LogInfo($"Created export directory: {exportPath}");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError($"Failed to create export directory: {ex.Message}");
            }
        }

        private static void ExportProceduralMetadata()
        {
            if (_exportTriggered || _logger == null) return;

            try
            {
                _logger.LogInfo("★★★ ProceduralMetadata: Triggering metadata export");
                _exportTriggered = true;

                // Use reflection to extract WorldGenerator parameters
                var reflector = new WorldGeneratorReflector(_logger);
                var metadata = reflector.ExtractMetadata();

                // Export to JSON
                var exportPath = Path.Combine(UnityEngine.Application.dataPath, "..", _exportDir?.Value ?? "./procedural_metadata");
                exportPath = Path.GetFullPath(exportPath);

                var jsonPath = Path.Combine(exportPath, $"{metadata.WorldName}-procedural.json");
                var json = JsonConvert.SerializeObject(metadata, Formatting.Indented);
                File.WriteAllText(jsonPath, json);

                var fileSize = new FileInfo(jsonPath).Length;
                _logger.LogInfo($"★★★ ProceduralMetadata: Exported to {jsonPath} ({fileSize} bytes)");

                // Start optimal sampling if enabled
                if (_enableOptimalSampling?.Value == true && !string.IsNullOrEmpty(metadata.WorldName))
                {
                    _logger.LogInfo($"★★★ ProceduralMetadata: Starting optimal sampling at {_optimalResolution?.Value ?? 1024}x{_optimalResolution?.Value ?? 1024}");
                    var sampler = new OptimalSampler(_logger, _optimalResolution?.Value ?? 1024);

                    // Find MonoBehaviour to start coroutine
                    var plugin = UnityEngine.Object.FindObjectOfType<VWE_ProceduralMetadataPlugin>();
                    if (plugin != null)
                    {
                        _samplingCoroutine = plugin.StartCoroutine(sampler.SampleWorld(exportPath, metadata.WorldName));
                    }
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError($"★★★ ProceduralMetadata: Export failed: {ex.GetType().Name} - {ex.Message}\nStack: {ex.StackTrace}");
            }
        }

        // Harmony patch: Trigger after world generation
        [HarmonyPatch(typeof(ZoneSystem), "Start")]
        public static class ZoneSystemStartPatch
        {
            public static void Postfix(ZoneSystem __instance)
            {
                if (_enabled?.Value != true) return;

                _logger?.LogInfo("★★★ ProceduralMetadata: ZoneSystem.Start detected - triggering export");
                ExportProceduralMetadata();
            }
        }
    }
}
