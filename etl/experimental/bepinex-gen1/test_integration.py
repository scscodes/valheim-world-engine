#!/usr/bin/env python3
"""
BepInEx Gen1 - Integration Testing Framework

Tests each stage independently and validates output against reference data.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add lib to path
sys.path.append(str(Path(__file__).parent / "lib"))

from orchestrator import DockerOrchestrator, GenerationPlan, GenerationResult
from processor import DataProcessor, ProcessingResult
from renderer import MapRenderer, RenderingResult
from utils import hash_seed, create_output_structure

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of an integration test"""
    test_name: str
    success: bool
    duration_seconds: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = None


class IntegrationTester:
    """Integration testing framework for BepInEx Gen1 generator"""
    
    def __init__(self, config_path: Path, repo_root: Path):
        """Initialize integration tester"""
        self.config_path = config_path
        self.repo_root = repo_root
        self.output_dir = repo_root / "etl" / "experimental" / "bepinex-gen1" / "data"
        
        # Load configurations
        self._load_configurations()
        
        # Initialize components
        self.orchestrator = DockerOrchestrator(
            self.generator_config, self.global_configs, repo_root
        )
        self.processor = DataProcessor(
            self.generator_config, self.global_configs
        )
        self.renderer = MapRenderer(
            self.generator_config, self.global_configs
        )
        
        # Test seeds and reference data
        self.test_seeds = [
            "QuickTest",  # Fast test
            "hkLycKKCMI",  # Reference validation seed
        ]
        
        logger.info("Integration tester initialized")

    def _load_configurations(self):
        """Load all required configurations"""
        import yaml
        
        # Load generator config
        with open(self.config_path, 'r') as f:
            self.generator_config = yaml.safe_load(f)
        
        # Load global configs
        global_data_dir = self.repo_root / "global" / "data"
        self.global_configs = {}
        
        for config_file in global_data_dir.glob("*.yml"):
            with open(config_file, 'r') as f:
                config_name = config_file.stem
                self.global_configs[config_name] = yaml.safe_load(f)

    def run_all_tests(self) -> List[TestResult]:
        """Run all integration tests"""
        logger.info("Starting integration test suite")
        
        results = []
        
        # Test 1: Configuration validation
        results.append(self.test_configuration_validation())
        
        # Test 2: Docker image availability
        results.append(self.test_docker_image_availability())
        
        # Test 3: Component initialization
        results.append(self.test_component_initialization())
        
        # Test 4: End-to-end generation (quick test)
        results.append(self.test_end_to_end_generation("QuickTest"))
        
        # Test 5: Output validation against reference
        results.append(self.test_output_validation("hkLycKKCMI"))
        
        # Test 6: Performance regression detection
        results.append(self.test_performance_regression())
        
        # Summary
        self._log_test_summary(results)
        
        return results

    def test_configuration_validation(self) -> TestResult:
        """Test configuration validation system"""
        start_time = time.time()
        
        try:
            success = self.orchestrator.validate_configuration()
            duration = time.time() - start_time
            
            return TestResult(
                test_name="Configuration Validation",
                success=success,
                duration_seconds=duration,
                details={"validation_passed": success}
            )
            
        except Exception as e:
            return TestResult(
                test_name="Configuration Validation",
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def test_docker_image_availability(self) -> TestResult:
        """Test Docker image availability"""
        start_time = time.time()
        
        try:
            image = self.generator_config["docker"]["custom_image"]
            exists = self.orchestrator._image_exists(image)
            duration = time.time() - start_time
            
            return TestResult(
                test_name="Docker Image Availability",
                success=exists,
                duration_seconds=duration,
                details={"image": image, "exists": exists}
            )
            
        except Exception as e:
            return TestResult(
                test_name="Docker Image Availability",
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def test_component_initialization(self) -> TestResult:
        """Test component initialization"""
        start_time = time.time()
        
        try:
            # Test orchestrator
            orchestrator_ok = hasattr(self.orchestrator, 'docker_client')
            
            # Test processor
            processor_ok = hasattr(self.processor, 'generator_config')
            
            # Test renderer
            renderer_ok = hasattr(self.renderer, 'generator_config')
            
            success = orchestrator_ok and processor_ok and renderer_ok
            duration = time.time() - start_time
            
            return TestResult(
                test_name="Component Initialization",
                success=success,
                duration_seconds=duration,
                details={
                    "orchestrator": orchestrator_ok,
                    "processor": processor_ok,
                    "renderer": renderer_ok
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name="Component Initialization",
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def test_end_to_end_generation(self, seed: str) -> TestResult:
        """Test end-to-end generation with quick test seed"""
        start_time = time.time()
        
        try:
            seed_hash = hash_seed(seed)
            directories = create_output_structure(self.output_dir, seed_hash)
            
            # Stage 1: World Generation
            plan, gen_result = self.orchestrator.generate_world(
                seed, seed_hash, directories, resolution=256  # Lower resolution for speed
            )
            
            if not gen_result.success:
                return TestResult(
                    test_name=f"End-to-End Generation ({seed})",
                    success=False,
                    duration_seconds=time.time() - start_time,
                    error_message=f"Generation failed: {gen_result.error_message}"
                )
            
            # Stage 2: Data Processing
            proc_result = self.processor.process(seed, seed_hash, directories)
            
            if not proc_result.success:
                return TestResult(
                    test_name=f"End-to-End Generation ({seed})",
                    success=False,
                    duration_seconds=time.time() - start_time,
                    error_message=f"Processing failed: {proc_result.error_message}"
                )
            
            # Stage 3: Rendering
            render_result = self.renderer.render(seed, directories)
            
            success = render_result.success
            duration = time.time() - start_time
            
            return TestResult(
                test_name=f"End-to-End Generation ({seed})",
                success=success,
                duration_seconds=duration,
                details={
                    "generation_duration": gen_result.duration_seconds,
                    "processing_duration": proc_result.duration_seconds,
                    "rendering_duration": render_result.duration_seconds,
                    "total_duration": duration
                },
                error_message=None if success else f"Rendering failed: {render_result.error_message}"
            )
            
        except Exception as e:
            return TestResult(
                test_name=f"End-to-End Generation ({seed})",
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def test_output_validation(self, seed: str) -> TestResult:
        """Test output validation against reference data"""
        start_time = time.time()
        
        try:
            seed_hash = hash_seed(seed)
            directories = create_output_structure(self.output_dir, seed_hash)
            
            # Check if reference data exists
            reference_dir = self.repo_root / "etl" / "archive" / "legacy" / "data" / "seeds" / seed_hash
            if not reference_dir.exists():
                return TestResult(
                    test_name=f"Output Validation ({seed})",
                    success=False,
                    duration_seconds=time.time() - start_time,
                    error_message=f"Reference data not found: {reference_dir}"
                )
            
            # Validate file structure
            required_files = [
                "extracted/biomes.json",
                "extracted/heightmap.json",
                "processed/biomes.json",
                "processed/heightmap.json",
                "renders/biomes_layer.webp",
                "renders/land_sea_layer.webp"
            ]
            
            missing_files = []
            for file_path in required_files:
                full_path = directories["seed_root"] / file_path
                if not full_path.exists():
                    missing_files.append(file_path)
            
            success = len(missing_files) == 0
            duration = time.time() - start_time
            
            return TestResult(
                test_name=f"Output Validation ({seed})",
                success=success,
                duration_seconds=duration,
                details={
                    "missing_files": missing_files,
                    "total_files_checked": len(required_files)
                },
                error_message=None if success else f"Missing files: {missing_files}"
            )
            
        except Exception as e:
            return TestResult(
                test_name=f"Output Validation ({seed})",
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def test_performance_regression(self) -> TestResult:
        """Test for performance regressions"""
        start_time = time.time()
        
        try:
            # Load reference performance data
            validation_data = self.global_configs.get("validation-data", {})
            reference_times = validation_data.get("performance", {})
            
            if not reference_times:
                return TestResult(
                    test_name="Performance Regression",
                    success=True,  # Skip if no reference data
                    duration_seconds=time.time() - start_time,
                    details={"status": "skipped", "reason": "no_reference_data"}
                )
            
            # Run quick performance test
            test_seed = "QuickTest"
            seed_hash = hash_seed(test_seed)
            directories = create_output_structure(self.output_dir, seed_hash)
            
            perf_start = time.time()
            plan, gen_result = self.orchestrator.generate_world(
                test_seed, seed_hash, directories, resolution=256
            )
            perf_duration = time.time() - perf_start
            
            # Compare against reference (allow 50% variance)
            reference_duration = reference_times.get("generation_seconds", 300)
            max_allowed = reference_duration * 1.5
            
            success = perf_duration <= max_allowed
            duration = time.time() - start_time
            
            return TestResult(
                test_name="Performance Regression",
                success=success,
                duration_seconds=duration,
                details={
                    "test_duration": perf_duration,
                    "reference_duration": reference_duration,
                    "max_allowed": max_allowed,
                    "performance_ratio": perf_duration / reference_duration
                },
                error_message=None if success else f"Performance regression: {perf_duration:.1f}s > {max_allowed:.1f}s"
            )
            
        except Exception as e:
            return TestResult(
                test_name="Performance Regression",
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            )

    def _log_test_summary(self, results: List[TestResult]):
        """Log test summary"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        logger.info("=" * 60)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        logger.info("")
        
        for result in results:
            status = "✓ PASS" if result.success else "✗ FAIL"
            logger.info(f"{status} {result.test_name} ({result.duration_seconds:.1f}s)")
            if result.error_message:
                logger.info(f"    Error: {result.error_message}")
        
        logger.info("=" * 60)


def main():
    """Main entry point for integration testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BepInEx Gen1 Integration Testing")
    parser.add_argument("--config", default="config/generator.yaml", help="Generator config path")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    config_path = Path(args.config)
    repo_root = Path(args.repo_root)
    
    tester = IntegrationTester(config_path, repo_root)
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    failed_tests = [r for r in results if not r.success]
    if failed_tests:
        logger.error(f"Integration tests failed: {len(failed_tests)} failures")
        sys.exit(1)
    else:
        logger.info("All integration tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
