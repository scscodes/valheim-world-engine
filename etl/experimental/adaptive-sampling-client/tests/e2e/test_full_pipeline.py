"""
End-to-End Pipeline Tests
Tests the complete flow: BepInEx output → API → Frontend
"""

import pytest
import requests
from pathlib import Path
import json


class TestE2EPipeline:
    """Test full pipeline from data export to visualization"""
    
    API_BASE = "http://localhost:8000"
    DATA_ROOT = Path(__file__).parent.parent.parent / "bepinex-adaptive-sampling" / "output" / "world_data"
    
    def test_bepinex_output_exists(self):
        """Verify BepInEx adaptive sampling has generated output files"""
        assert self.DATA_ROOT.exists(), f"Data root not found: {self.DATA_ROOT}"
        
        biomes_file = self.DATA_ROOT / "biomes.json"
        heightmap_file = self.DATA_ROOT / "heightmap.json"
        
        assert biomes_file.exists(), "biomes.json not found"
        assert heightmap_file.exists(), "heightmap.json not found"
        
        # Validate JSON structure
        with open(biomes_file) as f:
            biome_data = json.load(f)
            assert "resolution" in biome_data
            assert "biome_map" in biome_data
            assert len(biome_data["biome_map"]) == biome_data["resolution"]
        
        with open(heightmap_file) as f:
            heightmap_data = json.load(f)
            assert "resolution" in heightmap_data
            assert "heightmap" in heightmap_data
            assert len(heightmap_data["heightmap"]) == heightmap_data["resolution"]
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{self.API_BASE}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_list_worlds(self):
        """Test listing available worlds"""
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/")
        assert response.status_code == 200
        worlds = response.json()
        assert isinstance(worlds, list)
        assert len(worlds) > 0
    
    def test_api_get_biome_json(self):
        """Test fetching biome data as JSON"""
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/biomes?format=json")
        assert response.status_code == 200
        data = response.json()
        
        assert "resolution" in data
        assert "biome_map" in data
        assert "metadata" in data
        
        # Verify metadata
        metadata = data["metadata"]
        assert "sample_spacing_meters" in metadata
        assert "biome_counts" in metadata
        
        # Verify biome counts
        biome_counts = metadata["biome_counts"]
        total_samples = sum(biome_counts.values())
        expected_samples = data["resolution"] ** 2
        assert total_samples == expected_samples
    
    def test_api_get_biome_png(self):
        """Test fetching biome data as PNG"""
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/biomes?format=png")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"
        assert len(response.content) > 0
    
    def test_api_get_heightmap_json(self):
        """Test fetching heightmap data as JSON"""
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/heightmap?format=json")
        assert response.status_code == 200
        data = response.json()
        
        assert "resolution" in data
        assert "heightmap" in data
        assert "metadata" in data
        
        # Verify metadata
        metadata = data["metadata"]
        assert "min_height" in metadata
        assert "max_height" in metadata
        assert metadata["min_height"] < metadata["max_height"]
    
    def test_api_get_heightmap_png(self):
        """Test fetching heightmap as PNG"""
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/heightmap?format=png")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"
        assert len(response.content) > 0
    
    def test_api_get_composite_image(self):
        """Test generating composite image"""
        response = requests.get(
            f"{self.API_BASE}/api/v1/worlds/default/composite?resolution=512&alpha=0.5"
        )
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"
        assert len(response.content) > 0
    
    def test_data_quality_resolution(self):
        """Test that data resolution matches expected value"""
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/biomes?format=json")
        data = response.json()
        
        # Adaptive sampling uses 256x256
        assert data["resolution"] == 256
        assert len(data["biome_map"]) == 256
        assert len(data["biome_map"][0]) == 256
    
    def test_data_quality_biome_ids(self):
        """Test that biome IDs are valid bit flags"""
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/biomes?format=json")
        data = response.json()
        
        valid_biomes = {0, 1, 2, 4, 8, 16, 32, 64, 128, 256}
        
        for row in data["biome_map"]:
            for biome_id in row:
                assert biome_id in valid_biomes, f"Invalid biome ID: {biome_id}"
    
    def test_performance_response_time(self):
        """Test that API responses are fast enough"""
        import time
        
        # Biome JSON should respond in < 2 seconds
        start = time.time()
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/biomes?format=json")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Biome JSON response too slow: {elapsed:.2f}s"
        
        # PNG generation should complete in < 5 seconds
        start = time.time()
        response = requests.get(f"{self.API_BASE}/api/v1/worlds/default/biomes?format=png")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0, f"PNG generation too slow: {elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

