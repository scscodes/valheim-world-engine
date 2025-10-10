#!/usr/bin/env python3
"""
VWE Log Management Script
Centralized script for managing VWE logs across all components
"""

import sys
import argparse
from pathlib import Path

# Add global logging to path
sys.path.append(str(Path(__file__).parent.parent / "global" / "logging"))

from vwe_logger import VWELogger, LogLevel, LogFormat, setup_vwe_logging
from docker_logging import DockerLogManager
from generator_logging import GeneratorLogManager
from log_rotation import LogRotationManager
from log_monitoring import LogMonitor


def main():
    parser = argparse.ArgumentParser(description="VWE Log Management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup VWE logging")
    setup_parser.add_argument("--level", choices=["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"], 
                             default="INFO", help="Log level")
    setup_parser.add_argument("--format", choices=["json", "text", "compact"], 
                             default="json", help="Log format")
    setup_parser.add_argument("--output-dir", default="/var/log/vwe", 
                             help="Log output directory")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor logs")
    monitor_parser.add_argument("--start", action="store_true", help="Start monitoring")
    monitor_parser.add_argument("--stop", action="store_true", help="Stop monitoring")
    monitor_parser.add_argument("--status", action="store_true", help="Show monitoring status")
    monitor_parser.add_argument("--health", action="store_true", help="Show log health")
    
    # Rotate command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate logs")
    rotate_parser.add_argument("--file", help="Specific file to rotate")
    rotate_parser.add_argument("--directory", help="Directory to rotate logs in")
    rotate_parser.add_argument("--force", action="store_true", help="Force rotation")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old logs")
    cleanup_parser.add_argument("--directory", help="Directory to cleanup")
    cleanup_parser.add_argument("--days", type=int, default=30, help="Retention days")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search logs")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--directory", help="Directory to search")
    search_parser.add_argument("--hours", type=int, default=24, help="Hours to look back")
    search_parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show log statistics")
    stats_parser.add_argument("--directory", help="Directory to analyze")
    stats_parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_vwe_logging(
        LogLevel[args.level] if hasattr(args, 'level') else LogLevel.INFO,
        LogFormat[args.format] if hasattr(args, 'format') else LogFormat.JSON,
        args.output_dir if hasattr(args, 'output_dir') else "/var/log/vwe"
    )
    
    logger = VWELogger("log-manager")
    
    try:
        if args.command == "setup":
            logger.info("VWE logging setup completed", 
                       level=args.level, 
                       format=args.format, 
                       output_dir=args.output_dir)
            print(f"✅ VWE logging setup completed")
            print(f"   Level: {args.level}")
            print(f"   Format: {args.format}")
            print(f"   Output: {args.output_dir}")
        
        elif args.command == "monitor":
            monitor = LogMonitor()
            
            if args.start:
                monitor.start_monitoring()
                print("✅ Log monitoring started")
            elif args.stop:
                monitor.stop_monitoring()
                print("✅ Log monitoring stopped")
            elif args.status:
                status = monitor.get_logging_status()
                print(f"📊 Monitoring status: {status}")
            elif args.health:
                health = monitor.get_log_health_status()
                print(f"🏥 Log health: {health['status']}")
                for rec in health.get('recommendations', []):
                    print(f"   💡 {rec}")
        
        elif args.command == "rotate":
            rotation_manager = LogRotationManager()
            
            if args.file:
                success = rotation_manager.rotate_log_file(args.file)
                if success:
                    print(f"✅ Rotated log file: {args.file}")
                else:
                    print(f"❌ Failed to rotate log file: {args.file}")
            elif args.directory:
                # Rotate all files in directory
                log_dir = Path(args.directory)
                rotated_count = 0
                for log_file in log_dir.rglob("*.log"):
                    if rotation_manager.rotate_log_file(str(log_file)):
                        rotated_count += 1
                print(f"✅ Rotated {rotated_count} log files in {args.directory}")
            else:
                print("❌ Please specify --file or --directory")
        
        elif args.command == "cleanup":
            rotation_manager = LogRotationManager()
            
            if args.directory:
                if args.dry_run:
                    stats = rotation_manager.get_log_statistics(args.directory)
                    print(f"📊 Log statistics for {args.directory}:")
                    print(f"   Total files: {stats.get('total_files', 0)}")
                    print(f"   Total size: {stats.get('total_size_mb', 0)} MB")
                    print(f"   Compressed: {stats.get('compressed_files', 0)}")
                    print(f"   Uncompressed: {stats.get('uncompressed_files', 0)}")
                else:
                    stats = rotation_manager.cleanup_old_logs(args.directory)
                    print(f"✅ Cleanup completed:")
                    print(f"   Files removed: {stats.get('files_removed', 0)}")
                    print(f"   Files archived: {stats.get('files_archived', 0)}")
                    print(f"   Size freed: {stats.get('size_freed', 0)} bytes")
            else:
                print("❌ Please specify --directory")
        
        elif args.command == "search":
            monitor = LogMonitor()
            
            results = monitor.search_logs(
                args.query,
                [args.directory] if args.directory else None,
                args.hours
            )
            
            if args.format == "json":
                import json
                print(json.dumps(results, indent=2))
            else:
                print(f"🔍 Found {len(results)} matches for '{args.query}':")
                for result in results[:10]:  # Show first 10 results
                    print(f"   {result['file']}:{result['line']} - {result['content'][:100]}...")
                if len(results) > 10:
                    print(f"   ... and {len(results) - 10} more results")
        
        elif args.command == "stats":
            rotation_manager = LogRotationManager()
            
            directory = args.directory or "/var/log/vwe"
            stats = rotation_manager.get_log_statistics(directory)
            
            if args.format == "json":
                import json
                print(json.dumps(stats, indent=2))
            else:
                print(f"📊 Log statistics for {directory}:")
                print(f"   Total files: {stats.get('total_files', 0)}")
                print(f"   Total size: {stats.get('total_size_mb', 0)} MB ({stats.get('total_size_gb', 0)} GB)")
                print(f"   Compressed files: {stats.get('compressed_files', 0)}")
                print(f"   Uncompressed files: {stats.get('uncompressed_files', 0)}")
                print(f"   Oldest file: {stats.get('oldest_file', 'N/A')}")
                print(f"   Newest file: {stats.get('newest_file', 'N/A')}")
    
    except Exception as e:
        logger.error("Command failed", command=args.command, error=str(e))
        print(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
