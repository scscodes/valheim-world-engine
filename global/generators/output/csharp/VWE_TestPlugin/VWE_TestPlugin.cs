using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace VWE_TestPlugin
{
    [BepInPlugin(PluginInfo.PLUGIN_GUID, PluginInfo.PLUGIN_NAME, PluginInfo.PLUGIN_VERSION)]
    public class VWE_TestPlugin : BaseUnityPlugin
    {
        private const string PluginGUID = "VWE_TestPlugin";
        private const string PluginName = "VWE_TestPlugin";
        private const string PluginVersion = "1.0.0";
        
        private static ConfigFile Config { get; set; }
        private static ConfigEntry<bool> ModEnabled { get; set; }
        private static ConfigEntry<float> SomeSetting { get; set; }
        
        private static readonly Harmony Harmony = new Harmony(PluginGUID);
        private static new ManualLogSource Logger { get; set; }
        
        private void Awake()
        {
            Logger = base.Logger;
            Config = base.Config;
            
            // Load configuration
            ModEnabled = Config.Bind("General", "Enabled", true, "Enable/disable the mod");
            SomeSetting = Config.Bind("General", "SomeSetting", 1.0f, "Some configurable setting");
            
            if (ModEnabled.Value)
            {
                Logger.LogInfo($"{PluginName} v{PluginVersion} loaded successfully!");
                Harmony.PatchAll();
            }
            else
            {
                Logger.LogInfo($"{PluginName} is disabled in configuration.");
            }
        }
        
        private void OnDestroy()
        {
            Harmony?.UnpatchSelf();
        }
        
        // Example Harmony patch
        [HarmonyPatch(typeof(Player), nameof(Player.Update))]
        static class Player_Update_Patch
        {
            static void Postfix(Player __instance)
            {
                // Your custom logic here
                if (__instance.IsPlayer())
                {
                    // Example: Log player position every 60 frames
                    if (Time.frameCount % 60 == 0)
                    {
                        Logger.LogInfo($"Player position: {__instance.transform.position}");
                    }
                }
            }
        }
    }
    
    public static class PluginInfo
    {
        public const string PLUGIN_GUID = "VWE_TestPlugin";
        public const string PLUGIN_NAME = "VWE_TestPlugin";
        public const string PLUGIN_VERSION = "1.0.0";
    }
}