#!/usr/bin/env python3
"""
Test script for Warm Engine Pool Manager

This script tests the warm pooling strategy:
1. Checks for required Docker image
2. Creates warm engines
3. Tests world generation
4. Validates performance improvements
"""

import sys
import time
import logging
import argparse
from pathlib import Path
import docker

from warm_engine_pool_manager import WarmEnginePoolManager, EngineState
from orchestrator import WarmPoolOrchestrator


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_docker_image(image_name: str = "vwe-bepinex-gen1:latest") -> bool:
    """Check if the required Docker image exists"""
    logger.info(f"Checking for Docker image: {image_name}")

    try:
        client = docker.from_env()
        images = client.images.list(name=image_name)

        if images:
            logger.info(f"✓ Found image: {image_name}")
            logger.info(f"  Image ID: {images[0].short_id}")
            logger.info(f"  Created: {images[0].attrs.get('Created', 'unknown')}")
            return True
        else:
            logger.error(f"✗ Image not found: {image_name}")
            logger.error(f"")
            logger.error(f"To build the image, run:")
            logger.error(f"  cd etl/experimental/bepinex-gen1")
            logger.error(f"  bash docker/build.sh")
            return False

    except docker.errors.DockerException as e:
        logger.error(f"Docker error: {e}")
        logger.error(f"Make sure Docker is running")
        return False


def test_engine_creation():
    """Test creating a warm engine"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Warm Engine Creation")
    logger.info("="*80)

    manager = WarmEnginePoolManager()

    logger.info("Creating warm engine...")
    start_time = time.time()

    try:
        engine_id = manager.create_warm_engine()
        creation_time = time.time() - start_time

        logger.info(f"✓ Warm engine created in {creation_time:.1f}s: {engine_id}")

        # Get status
        status = manager.get_status()
        logger.info(f"\nPool status:")
        logger.info(f"  Pool size: {status['pool_size']}/{status['max_pool_size']}")

        for eid, info in status['engines'].items():
            logger.info(f"  Engine {eid}:")
            logger.info(f"    State: {info['state']}")
            logger.info(f"    Container: {info['container']}")
            logger.info(f"    Jobs processed: {info['jobs_processed']}")

        # Shutdown engine
        logger.info(f"\nShutting down engine...")
        manager.shutdown_engine(engine_id)
        logger.info(f"✓ Engine shut down")

        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        return False


def test_pool_initialization():
    """Test initializing a pool of warm engines"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Warm Pool Initialization")
    logger.info("="*80)

    orchestrator = WarmPoolOrchestrator()

    logger.info("Initializing pool with 2 engines...")
    start_time = time.time()

    try:
        orchestrator.initialize_pool(pool_size=2)
        init_time = time.time() - start_time

        logger.info(f"✓ Pool initialized in {init_time:.1f}s")

        # Get status
        status = orchestrator.get_pool_status()
        logger.info(f"\nPool status:")
        logger.info(f"  Active engines: {status['pool_size']}")

        # Shutdown
        logger.info(f"\nShutting down pool...")
        orchestrator.shutdown()
        logger.info(f"✓ Pool shut down")

        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        return False


def test_world_generation(seed: str = "WarmPoolTest"):
    """Test world generation with warm pool (DRY RUN - no actual generation)"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: World Generation Dry Run")
    logger.info("="*80)
    logger.info("Note: This is a dry run that creates the engine but doesn't")
    logger.info("      actually generate a world (would take ~3 minutes)")

    manager = WarmEnginePoolManager()

    try:
        # Create warm engine
        logger.info("Creating warm engine...")
        start_time = time.time()
        engine_id = manager.create_warm_engine()
        creation_time = time.time() - start_time
        logger.info(f"✓ Warm engine ready in {creation_time:.1f}s: {engine_id}")

        # Verify engine is ready
        status = manager.get_status()
        engine_info = status['engines'].get(engine_id)

        if engine_info and engine_info['state'] == 'ready':
            logger.info(f"✓ Engine is in READY state")
            logger.info(f"  Container: {engine_info['container']}")

            # In a real test, this would call:
            # result = manager.generate_world(seed, seed_hash, job_id, engine_id)
            logger.info(f"\n[DRY RUN] Would now generate world for seed: {seed}")
            logger.info(f"  Expected steps:")
            logger.info(f"    1. Send console command to load world")
            logger.info(f"    2. Wait for world generation (~60s)")
            logger.info(f"    3. Wait for BepInEx export (~20s)")
            logger.info(f"    4. Reset engine to ready state")
            logger.info(f"  Total expected time: ~1-1.5 minutes (vs 3 min traditional)")

        else:
            logger.error(f"✗ Engine not in ready state: {engine_info.get('state')}")
            return False

        # Shutdown
        logger.info(f"\nShutting down engine...")
        manager.shutdown_engine(engine_id)
        logger.info(f"✓ Engine shut down")

        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        # Cleanup
        try:
            manager.shutdown_all_engines()
        except:
            pass
        return False


def test_full_generation(seed: str = "QuickTest"):
    """
    Full integration test - actually generates a world
    WARNING: This takes ~3 minutes for first generation!
    """
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Full World Generation (LIVE TEST)")
    logger.info("="*80)
    logger.info(f"Seed: {seed}")
    logger.info("⚠ WARNING: This will take ~3 minutes!")
    logger.info("="*80)

    orchestrator = WarmPoolOrchestrator()

    try:
        # Initialize pool
        logger.info("\nInitializing warm pool...")
        pool_start = time.time()
        orchestrator.initialize_pool(pool_size=1)
        pool_init_time = time.time() - pool_start
        logger.info(f"✓ Pool initialized in {pool_init_time:.1f}s")

        # Generate world
        logger.info(f"\nGenerating world for seed: {seed}")
        gen_start = time.time()

        result = orchestrator.generate_world(seed)

        gen_time = time.time() - gen_start
        total_time = time.time() - pool_start

        if result['success']:
            logger.info(f"\n✓ World generation successful!")
            logger.info(f"  Pool initialization: {pool_init_time:.1f}s")
            logger.info(f"  World generation: {gen_time:.1f}s")
            logger.info(f"  Total time: {total_time:.1f}s")

            if not result.get('cached'):
                logger.info(f"  Generation time: {result.get('generation_time', 0):.1f}s")
                logger.info(f"  Export time: {result.get('export_time', 0):.1f}s")
                logger.info(f"  Engine ID: {result.get('engine_id', 'N/A')}")
            else:
                logger.info(f"  (Used cached data)")

            logger.info(f"  Data directory: {result.get('data_dir', 'N/A')}")
        else:
            logger.error(f"✗ World generation failed: {result.get('error', 'Unknown error')}")
            return False

        # Shutdown
        logger.info(f"\nShutting down pool...")
        orchestrator.shutdown()
        logger.info(f"✓ Pool shut down")

        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        # Cleanup
        try:
            orchestrator.shutdown()
        except:
            pass
        return False


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Test Warm Engine Pool Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test modes:
  quick    - Run quick tests (engine creation, pool init) [default]
  full     - Run full integration test (actually generates a world ~3 min)

Examples:
  # Run quick tests only
  python test_warm_pool.py

  # Run full integration test
  python test_warm_pool.py --mode full

  # Run with custom seed
  python test_warm_pool.py --mode full --seed "MyTestWorld"
        """
    )

    parser.add_argument(
        "--mode",
        choices=["quick", "full"],
        default="quick",
        help="Test mode (default: quick)"
    )

    parser.add_argument(
        "--seed",
        default="QuickTest",
        help="Seed for full test (default: QuickTest)"
    )

    parser.add_argument(
        "--skip-image-check",
        action="store_true",
        help="Skip Docker image check"
    )

    args = parser.parse_args()

    # Header
    logger.info("="*80)
    logger.info("WARM ENGINE POOL MANAGER - TEST SUITE")
    logger.info("="*80)

    # Check Docker image
    if not args.skip_image_check:
        if not check_docker_image():
            logger.error("\n✗ Docker image not available, exiting")
            sys.exit(1)

    # Run tests based on mode
    if args.mode == "quick":
        logger.info("\nRunning quick tests...")

        tests = [
            ("Engine Creation", test_engine_creation),
            ("Pool Initialization", test_pool_initialization),
            ("World Generation Dry Run", test_world_generation),
        ]

    else:  # full
        logger.info("\nRunning full integration tests...")
        logger.info("⚠ WARNING: Full test will take ~3 minutes!\n")

        # Confirm
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            logger.info("Test cancelled")
            sys.exit(0)

        tests = [
            ("Engine Creation", test_engine_creation),
            ("Pool Initialization", test_pool_initialization),
            ("Full World Generation", lambda: test_full_generation(args.seed)),
        ]

    # Run tests
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            logger.warning("\n\nTest interrupted by user")
            sys.exit(130)
        except Exception as e:
            logger.error(f"\n\nUnexpected error in {test_name}: {e}", exc_info=True)
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}  {test_name}")

    logger.info("="*80)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("="*80)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
