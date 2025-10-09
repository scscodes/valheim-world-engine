# BepInEx Integration Example

**⚠️ NOTE:** This integration is **on hold** until BepInEx approach is fully validated.

This document outlines how the BepInEx solution **could** be integrated into the main Valheim World Engine project once it proves superior to the current graceful shutdown approach.

**Current Status:** BepInEx approach is isolated for testing. See `VALIDATION_GUIDE.md`.

## 1. Update world_generator.py

Add BepInEx support to the world generation service:

```python
# In backend/app/services/world_generator.py

def build_worldgen_plan(self, seed: str) -> Dict[str, Any]:
    # ... existing code ...
    
    # Check if BepInEx is enabled
    bepinex_enabled = os.getenv("BEPINEX_ENABLED", "false").lower() == "true"
    
    if bepinex_enabled:
        # Use BepInEx-enabled image
        image = "vwe/valheim-server-bepinex:latest"
        
        # Add BepInEx environment variables
        env_vars.update({
            "BEPINEX_ENABLED": "true",
            "BEPINEX_LOG_LEVEL": "Info",
            "VWE_AUTOSAVE_ENABLED": "true",
            "VWE_AUTOSAVE_DELAY": "2",
            "VWE_DATAEXPORT_ENABLED": "true",
            "VWE_DATAEXPORT_FORMAT": "both",
            "VWE_DATAEXPORT_DIR": "./world_data"
        })
        
        # Add exported data to expected outputs
        expected_outputs["exported"] = [
            os.path.join(seed_dir, "exported", "biomes.json"),
            os.path.join(seed_dir, "exported", "biomes.png"),
            os.path.join(seed_dir, "exported", "heightmap.json"),
            os.path.join(seed_dir, "exported", "heightmap.png"),
            os.path.join(seed_dir, "exported", "structures.json"),
            os.path.join(seed_dir, "exported", "structures.png")
        ]
    else:
        # Use standard image
        image = settings.valheim_image
    
    # ... rest of existing code ...
```

## 2. Use dedicated BepInEx compose file

Use the dedicated BepInEx compose file:

```bash
# Run from repo root
docker compose -f docker/bepinex/docker-compose.bepinex.yml --profile bepinex up -d
```

## 3. Update .env

Add BepInEx configuration to environment:

```bash
# In .env

# BepInEx Configuration
BEPINEX_ENABLED=true
BEPINEX_LOG_LEVEL=Info
VWE_AUTOSAVE_ENABLED=true
VWE_AUTOSAVE_DELAY=2
VWE_DATAEXPORT_ENABLED=true
VWE_DATAEXPORT_FORMAT=both
VWE_DATAEXPORT_DIR=./world_data

# Plugin directories
PLUGINS_HOST_DIR=/home/steve/projects/valheim-world-engine/bepinex/plugins
```

## 4. Update API endpoints

Add endpoints for exported data:

```python
# In backend/app/api/routes/seeds.py

@router.get("/{seed}/exported")
async def get_exported_data(seed: str):
    """Get exported world data (biomes, heightmaps, structures)"""
    seed_dir = os.path.join(settings.data_dir, "seeds", seed)
    exported_dir = os.path.join(seed_dir, "exported")
    
    if not os.path.exists(exported_dir):
        raise HTTPException(status_code=404, detail="Exported data not found")
    
    # Return list of available exported files
    files = []
    for file in os.listdir(exported_dir):
        if file.endswith(('.json', '.png')):
            files.append({
                "name": file,
                "type": "json" if file.endswith('.json') else "png",
                "size": os.path.getsize(os.path.join(exported_dir, file))
            })
    
    return {"files": files}

@router.get("/{seed}/exported/{filename}")
async def get_exported_file(seed: str, filename: str):
    """Download exported world data file"""
    seed_dir = os.path.join(settings.data_dir, "seeds", seed)
    file_path = os.path.join(seed_dir, "exported", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)
```

## 5. Update frontend

Add UI for exported data:

```typescript
// In frontend/components/ExportedDataViewer.tsx

interface ExportedDataViewerProps {
  seed: string;
}

export const ExportedDataViewer: React.FC<ExportedDataViewerProps> = ({ seed }) => {
  const [exportedFiles, setExportedFiles] = useState([]);
  
  useEffect(() => {
    // Fetch exported data files
    fetch(`/api/seeds/${seed}/exported`)
      .then(res => res.json())
      .then(data => setExportedFiles(data.files));
  }, [seed]);
  
  return (
    <div className="exported-data-viewer">
      <h3>Exported World Data</h3>
      <div className="file-grid">
        {exportedFiles.map(file => (
          <div key={file.name} className="file-item">
            <img 
              src={`/api/seeds/${seed}/exported/${file.name}`}
              alt={file.name}
              style={{ maxWidth: '200px', maxHeight: '200px' }}
            />
            <p>{file.name}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 6. Performance Benefits

With BepInEx integration:

- **Generation time**: 30-60 seconds (vs 2-3 minutes)
- **Data availability**: Real-time (vs post-generation)
- **Resource usage**: Lower (no 20-30 minute waits)
- **Reliability**: Higher (programmatic vs timing-based)

## 7. Deployment

1. **Build plugins**: `cd bepinex && make build`
2. **Build Docker image**: `cd bepinex && make docker-build`
3. **Update configuration**: Set `BEPINEX_ENABLED=true` in `.env`
4. **Deploy**: `docker compose -f docker/bepinex/docker-compose.bepinex.yml --profile bepinex up -d`

## 8. Monitoring

Monitor BepInEx logs:

```bash
# Check plugin loading
docker logs valheim-server 2>&1 | grep -E "(VWE|BepInEx)"

# Check exported data
docker exec valheim-server ls -la /valheim/world_data/

# Check plugin status
docker exec valheim-server ls -la /valheim/BepInEx/plugins/
```

This integration provides a complete BepInEx solution for optimized Valheim world generation and data export.
