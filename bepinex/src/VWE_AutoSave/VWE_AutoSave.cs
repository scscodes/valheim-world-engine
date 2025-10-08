using System;
using System.Collections;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace VWE_AutoSave
{
    [BepInPlugin(PluginGUID, PluginName, PluginVersion)]
    public class VWE_AutoSavePlugin : BaseUnityPlugin
    {
        public const string PluginGUID = "com.valheimworldengine.autosave";
        public const string PluginName = "VWE AutoSave";
        public const string PluginVersion = "1.0.0";

        private static ConfigEntry<bool>? _enabled;
        private static ConfigEntry<float>? _saveDelay;
        private static ConfigEntry<bool>? _logSaves;
        private static ConfigEntry<bool>? _logDebug;
        private static ManualLogSource? _logger;

        private static bool _worldGenerationComplete = false;
        private static bool _saveTriggered = false;

        private void Awake()
        {
            // Store logger for static access
            _logger = Logger;
            
            // Configuration
            _enabled = Config.Bind("AutoSave", "enabled", true, "Enable/disable auto-save functionality");
            _saveDelay = Config.Bind("AutoSave", "save_delay", 2f, "Delay before triggering save (seconds)");
            _logSaves = Config.Bind("AutoSave", "log_saves", true, "Log save events");
            _logDebug = Config.Bind("AutoSave", "log_debug", false, "Enable debug logging");

            if (_enabled.Value)
            {
                Logger.LogInfo("VWE AutoSave plugin loaded and enabled");
                
                // Apply Harmony patches
                var harmony = new Harmony(PluginGUID);
                harmony.PatchAll();
                
                Logger.LogInfo("VWE AutoSave patches applied");
            }
            else
            {
                Logger.LogInfo("VWE AutoSave plugin loaded but disabled");
            }
        }

        private void Start()
        {
            if (!_enabled.Value) return;

            // Start monitoring for world generation completion
            StartCoroutine(MonitorWorldGeneration());
        }

        private IEnumerator MonitorWorldGeneration()
        {
            while (true)
            {
                if (_worldGenerationComplete && !_saveTriggered)
                {
                    yield return new WaitForSeconds(_saveDelay.Value);
                    TriggerWorldSave();
                }
                
                yield return new WaitForSeconds(1f);
            }
        }

        private void TriggerWorldSave()
        {
            if (_saveTriggered) return;

            try
            {
                if (_logSaves.Value)
                {
                    Logger.LogInfo("VWE AutoSave: Triggering world save...");
                }

                // Trigger save via Save method
                if (ZNet.instance != null)
                {
                    ZNet.instance.Save(true);  // true = sync save
                    _saveTriggered = true;
                    
                    if (_logSaves?.Value == true)
                    {
                        Logger.LogInfo("VWE AutoSave: World save triggered successfully");
                    }
                }
                else
                {
                    Logger.LogWarning("VWE AutoSave: ZNet.instance is null, cannot trigger save");
                }
            }
            catch (Exception ex)
            {
                Logger.LogError($"VWE AutoSave: Failed to trigger save: {ex.Message}");
            }
        }

        // Harmony patch to detect world generation completion
        [HarmonyPatch(typeof(ZoneSystem), "Start")]
        public static class ZoneSystemStartPatch
        {
            public static void Postfix(ZoneSystem __instance)
            {
                if (_enabled?.Value != true) return;

                // ★★★ PROMINENT DEBUG LOGGING ★★★
                _logger?.LogInfo("★★★ VWE AutoSave: HOOK EXECUTED - ZoneSystem.Start detected ★★★");

                if (_logDebug?.Value == true)
                {
                    _logger?.LogInfo("VWE AutoSave: ZoneSystem.Start detected");
                }

                // Mark world generation as complete
                _worldGenerationComplete = true;

                if (_logSaves?.Value == true)
                {
                    _logger?.LogInfo("VWE AutoSave: World generation complete, save will be triggered");
                }
            }
        }

        // Harmony patch to detect when world is ready for saving
        [HarmonyPatch(typeof(ZNet), "OnNewConnection")]
        public static class ZNetOnNewConnectionPatch
        {
            public static void Postfix(ZNet __instance, ZNetPeer peer)
            {
                if (_enabled?.Value != true) return;

                if (_logDebug?.Value == true)
                {
                    _logger?.LogInfo("VWE AutoSave: New connection detected, checking world status");
                }

                // Check if world is ready for saving
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
                
                if (_logSaves?.Value == true)
                {
                    _logger?.LogInfo("VWE AutoSave: World generation assumed complete (timeout), save will be triggered");
                }
            }
        }
    }
}
