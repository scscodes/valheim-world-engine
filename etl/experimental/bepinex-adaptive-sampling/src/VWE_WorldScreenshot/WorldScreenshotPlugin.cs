using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using System;
using System.IO;
using UnityEngine;

namespace VWE.WorldScreenshot
{
    [BepInPlugin(PluginGUID, PluginName, PluginVersion)]
    public class WorldScreenshotPlugin : BaseUnityPlugin
    {
        public const string PluginGUID = "com.vwe.worldscreenshot";
        public const string PluginName = "VWE World Screenshot";
        public const string PluginVersion = "1.0.0";

        private static ManualLogSource _logger;
        private bool _screenshotCaptured = false;
        private float _checkTimer = 0f;
        private const float CHECK_INTERVAL = 5f;

        // Configuration
        private ConfigEntry<bool> _configEnabled;
        private ConfigEntry<int> _configResolution;
        private ConfigEntry<float> _configDelay;
        private ConfigEntry<string> _configExportPath;

        void Awake()
        {
            _logger = Logger;

            // Setup configuration
            _configEnabled = Config.Bind("General", "Enabled", true,
                "Enable automatic screenshot capture on world load");

            _configResolution = Config.Bind("General", "Resolution", 2048,
                "Screenshot resolution (0 = native minimap resolution)");

            _configDelay = Config.Bind("General", "CaptureDelay", 15f,
                "Seconds to wait after world load before capturing");

            _configExportPath = Config.Bind("General", "ExportPath", "/opt/valheim/world_data",
                "Export path for screenshots (absolute path)");

            if (!_configEnabled.Value)
            {
                _logger.LogInfo("WorldScreenshot plugin disabled in config");
                return;
            }

            _logger.LogInfo($"★★★ {PluginName} v{PluginVersion} loaded");
            _logger.LogInfo($"★★★ Export path: {_configExportPath.Value}");
            _logger.LogInfo($"★★★ Target resolution: {_configResolution.Value}");
        }

        void Update()
        {
            if (!_configEnabled.Value || _screenshotCaptured)
                return;

            _checkTimer += Time.deltaTime;

            if (_checkTimer < CHECK_INTERVAL)
                return;

            _checkTimer = 0f;

            // Check if we're ready to capture
            if (CanCapture())
            {
                _logger.LogInfo("★★★ WorldScreenshot: Conditions met, scheduling capture");
                Invoke(nameof(CaptureScreenshot), _configDelay.Value);
                _screenshotCaptured = true; // Mark as scheduled
            }
        }

        private bool CanCapture()
        {
            // Must be on dedicated server
            if (ZNet.instance == null || !ZNet.instance.IsServer())
            {
                _logger.LogDebug("Not a server, skipping");
                return false;
            }

            // World must be loaded
            if (ZoneSystem.instance == null)
            {
                _logger.LogDebug("ZoneSystem not ready");
                return false;
            }

            // Minimap must exist
            if (Minimap.instance == null)
            {
                _logger.LogDebug("Minimap instance not ready");
                return false;
            }

            _logger.LogInfo("★★★ WorldScreenshot: All conditions met!");
            return true;
        }

        private void CaptureScreenshot()
        {
            try
            {
                _logger.LogInfo("★★★ WorldScreenshot: Starting capture");

                // Get world name
                string worldName = ZNet.instance.GetWorldName();
                _logger.LogInfo($"★★★ WorldScreenshot: World name = {worldName}");

                // Reveal entire map (this is key for getting full world view)
                _logger.LogInfo("★★★ WorldScreenshot: Revealing entire map");
                Minimap.instance.ExploreAll();

                // Wait a frame for map to update
                StartCoroutine(CaptureAfterFrame(worldName));
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ WorldScreenshot ERROR: {ex.Message}");
                _logger.LogError($"Stack trace: {ex.StackTrace}");
            }
        }

        private System.Collections.IEnumerator CaptureAfterFrame(string worldName)
        {
            yield return new WaitForEndOfFrame();

            try
            {
                _logger.LogInfo("★★★ WorldScreenshot: Capturing minimap texture");

                // Get the minimap texture
                Texture2D mapTexture = GetMinimapTexture();

                if (mapTexture == null)
                {
                    _logger.LogError("★★★ WorldScreenshot: Failed to get minimap texture");
                    yield break;
                }

                _logger.LogInfo($"★★★ WorldScreenshot: Got texture {mapTexture.width}x{mapTexture.height}");

                // Optional: Resize if custom resolution specified
                Texture2D finalTexture = mapTexture;
                if (_configResolution.Value > 0 && _configResolution.Value != mapTexture.width)
                {
                    _logger.LogInfo($"★★★ WorldScreenshot: Resizing to {_configResolution.Value}x{_configResolution.Value}");
                    finalTexture = ResizeTexture(mapTexture, _configResolution.Value, _configResolution.Value);
                }

                // Encode to PNG
                _logger.LogInfo("★★★ WorldScreenshot: Encoding to PNG");
                byte[] pngBytes = finalTexture.EncodeToPNG();

                // Ensure export directory exists
                string exportDir = _configExportPath.Value;
                if (!Directory.Exists(exportDir))
                {
                    _logger.LogInfo($"★★★ WorldScreenshot: Creating directory {exportDir}");
                    Directory.CreateDirectory(exportDir);
                }

                // Generate filename
                string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string filename = $"minimap_screenshot_{worldName}_{timestamp}.png";
                string fullPath = Path.Combine(exportDir, filename);

                // Write to file
                _logger.LogInfo($"★★★ WorldScreenshot: Writing to {fullPath}");
                File.WriteAllBytes(fullPath, pngBytes);

                _logger.LogInfo($"★★★ WorldScreenshot: COMPLETE - Screenshot saved ({pngBytes.Length / 1024}KB)");
                _logger.LogInfo($"★★★ WorldScreenshot: Path: {fullPath}");

                // Also create metadata JSON
                CreateMetadata(worldName, fullPath, finalTexture.width, finalTexture.height);

                // Cleanup
                if (finalTexture != mapTexture)
                {
                    Destroy(finalTexture);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ WorldScreenshot CAPTURE ERROR: {ex.Message}");
                _logger.LogError($"Stack trace: {ex.StackTrace}");
            }
        }

        private Texture2D GetMinimapTexture()
        {
            try
            {
                // Access the minimap texture
                // This gets the actual rendered map texture from Valheim
                var mapTextureField = typeof(Minimap).GetField("m_mapTexture",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);

                if (mapTextureField != null)
                {
                    Texture2D texture = mapTextureField.GetValue(Minimap.instance) as Texture2D;
                    if (texture != null)
                    {
                        // Make it readable
                        return DuplicateTexture(texture);
                    }
                }

                _logger.LogWarning("★★★ WorldScreenshot: Could not access m_mapTexture, trying alternative");

                // Alternative: Try to get the texture from the minimap UI
                var mapImageField = typeof(Minimap).GetField("m_mapImageLarge",
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);

                if (mapImageField != null)
                {
                    var mapImage = mapImageField.GetValue(Minimap.instance) as UnityEngine.UI.RawImage;
                    if (mapImage != null && mapImage.texture != null)
                    {
                        return DuplicateTexture(mapImage.texture as Texture2D);
                    }
                }

                _logger.LogError("★★★ WorldScreenshot: Could not access minimap texture");
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError($"★★★ WorldScreenshot GetMinimapTexture ERROR: {ex.Message}");
                return null;
            }
        }

        private Texture2D DuplicateTexture(Texture2D source)
        {
            // Create a readable copy of the texture
            RenderTexture renderTex = RenderTexture.GetTemporary(
                source.width, source.height, 0,
                RenderTextureFormat.Default, RenderTextureReadWrite.Linear);

            Graphics.Blit(source, renderTex);
            RenderTexture previous = RenderTexture.active;
            RenderTexture.active = renderTex;

            Texture2D readableTexture = new Texture2D(source.width, source.height);
            readableTexture.ReadPixels(new Rect(0, 0, renderTex.width, renderTex.height), 0, 0);
            readableTexture.Apply();

            RenderTexture.active = previous;
            RenderTexture.ReleaseTemporary(renderTex);

            return readableTexture;
        }

        private Texture2D ResizeTexture(Texture2D source, int newWidth, int newHeight)
        {
            RenderTexture rt = RenderTexture.GetTemporary(newWidth, newHeight);
            rt.filterMode = FilterMode.Bilinear;

            RenderTexture.active = rt;
            Graphics.Blit(source, rt);

            Texture2D result = new Texture2D(newWidth, newHeight, TextureFormat.RGB24, false);
            result.ReadPixels(new Rect(0, 0, newWidth, newHeight), 0, 0);
            result.Apply();

            RenderTexture.active = null;
            RenderTexture.ReleaseTemporary(rt);

            return result;
        }

        private void CreateMetadata(string worldName, string screenshotPath, int width, int height)
        {
            try
            {
                string metadataPath = screenshotPath.Replace(".png", "_metadata.json");

                var metadata = new
                {
                    world_name = worldName,
                    resolution = new { width, height },
                    capture_timestamp = DateTime.UtcNow.ToString("o"),
                    plugin_version = PluginVersion,
                    world_radius = 10000.0,
                    world_diameter = 20000.0
                };

                string json = Newtonsoft.Json.JsonConvert.SerializeObject(metadata, Newtonsoft.Json.Formatting.Indented);
                File.WriteAllText(metadataPath, json);

                _logger.LogInfo($"★★★ WorldScreenshot: Metadata saved to {metadataPath}");
            }
            catch (Exception ex)
            {
                _logger.LogWarning($"★★★ WorldScreenshot: Could not save metadata: {ex.Message}");
            }
        }
    }
}
