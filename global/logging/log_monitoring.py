#!/usr/bin/env python3
"""
Log Monitoring for Valheim World Engine
Monitors logs for errors, patterns, and provides management utilities
"""

import os
import json
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Pattern
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from .vwe_logger import VWELogger, LogLevel


@dataclass
class MonitoringConfig:
    """Log monitoring configuration"""
    log_directories: List[str] = None
    error_patterns: List[str] = None
    warning_patterns: List[str] = None
    success_patterns: List[str] = None
    alert_thresholds: Dict[str, int] = None
    monitoring_interval: int = 60  # seconds
    max_log_lines: int = 1000


class LogMonitor:
    """Monitors logs for patterns, errors, and provides management utilities"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        
        # Setup VWE logger
        self.logger = VWELogger("log-monitor", context={
            "component": "log-monitoring",
            "config": asdict(self.config)
        })
        
        # Default patterns
        self.error_patterns = self.config.error_patterns or [
            r"ERROR",
            r"CRITICAL",
            r"Exception",
            r"Traceback",
            r"Failed",
            r"Error:",
            r"FATAL"
        ]
        
        self.warning_patterns = self.config.warning_patterns or [
            r"WARN",
            r"WARNING",
            r"Deprecated",
            r"Timeout",
            r"Retry"
        ]
        
        self.success_patterns = self.config.success_patterns or [
            r"SUCCESS",
            r"Completed",
            r"Finished",
            r"Ready",
            r"Started"
        ]
        
        # Compile patterns
        self.compiled_error_patterns = [re.compile(p, re.IGNORECASE) for p in self.error_patterns]
        self.compiled_warning_patterns = [re.compile(p, re.IGNORECASE) for p in self.warning_patterns]
        self.compiled_success_patterns = [re.compile(p, re.IGNORECASE) for p in self.success_patterns]
        
        # Monitoring state
        self.monitoring_active = False
        self.last_check_time = None
        self.alert_counts = defaultdict(int)
        self.pattern_matches = defaultdict(list)
    
    def start_monitoring(self):
        """Start continuous log monitoring"""
        self.monitoring_active = True
        self.logger.info("Started log monitoring")
        
        import threading
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous log monitoring"""
        self.monitoring_active = False
        self.logger.info("Stopped log monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self.check_logs()
                time.sleep(self.config.monitoring_interval)
            except Exception as e:
                self.logger.error("Error in monitoring loop", error=str(e))
                time.sleep(60)  # Wait before retrying
    
    def check_logs(self) -> Dict[str, Any]:
        """Check logs for patterns and issues"""
        try:
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "errors": [],
                "warnings": [],
                "successes": [],
                "patterns_found": {},
                "summary": {}
            }
            
            # Check each log directory
            for log_dir in self.config.log_directories or ["/var/log/vwe"]:
                if not Path(log_dir).exists():
                    continue
                
                # Find recent log files
                log_files = self._get_recent_log_files(log_dir)
                
                for log_file in log_files:
                    try:
                        file_results = self._analyze_log_file(log_file)
                        results["errors"].extend(file_results["errors"])
                        results["warnings"].extend(file_results["warnings"])
                        results["successes"].extend(file_results["successes"])
                        
                    except Exception as e:
                        self.logger.warn("Failed to analyze log file", 
                                       file_path=str(log_file),
                                       error=str(e))
            
            # Update pattern matches
            self._update_pattern_matches(results)
            
            # Check alert thresholds
            self._check_alert_thresholds(results)
            
            # Generate summary
            results["summary"] = self._generate_summary(results)
            
            self.last_check_time = datetime.utcnow()
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to check logs", error=str(e))
            return {"error": str(e)}
    
    def _get_recent_log_files(self, log_dir: str, hours: int = 24) -> List[Path]:
        """Get recent log files from directory"""
        try:
            log_path = Path(log_dir)
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            recent_files = []
            for log_file in log_path.rglob("*.log"):
                try:
                    if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff_time:
                        recent_files.append(log_file)
                except OSError:
                    continue
            
            return recent_files
            
        except Exception as e:
            self.logger.error("Failed to get recent log files", 
                            directory=log_dir,
                            error=str(e))
            return []
    
    def _analyze_log_file(self, log_file: Path) -> Dict[str, Any]:
        """Analyze a single log file for patterns"""
        try:
            results = {
                "file": str(log_file),
                "errors": [],
                "warnings": [],
                "successes": []
            }
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                # Limit lines for performance
                if len(lines) > self.config.max_log_lines:
                    lines = lines[-self.config.max_log_lines:]
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for errors
                    for pattern in self.compiled_error_patterns:
                        if pattern.search(line):
                            results["errors"].append({
                                "file": str(log_file),
                                "line": line_num,
                                "content": line,
                                "pattern": pattern.pattern,
                                "timestamp": self._extract_timestamp(line)
                            })
                    
                    # Check for warnings
                    for pattern in self.compiled_warning_patterns:
                        if pattern.search(line):
                            results["warnings"].append({
                                "file": str(log_file),
                                "line": line_num,
                                "content": line,
                                "pattern": pattern.pattern,
                                "timestamp": self._extract_timestamp(line)
                            })
                    
                    # Check for successes
                    for pattern in self.compiled_success_patterns:
                        if pattern.search(line):
                            results["successes"].append({
                                "file": str(log_file),
                                "line": line_num,
                                "content": line,
                                "pattern": pattern.pattern,
                                "timestamp": self._extract_timestamp(line)
                            })
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to analyze log file", 
                            file_path=str(log_file),
                            error=str(e))
            return {"file": str(log_file), "errors": [], "warnings": [], "successes": []}
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        try:
            # Common timestamp formats
            timestamp_patterns = [
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
                r'(\d{2}:\d{2}:\d{2})'
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _update_pattern_matches(self, results: Dict[str, Any]):
        """Update pattern match tracking"""
        for error in results["errors"]:
            pattern = error["pattern"]
            self.pattern_matches[pattern].append({
                "timestamp": error["timestamp"],
                "file": error["file"],
                "content": error["content"]
            })
    
    def _check_alert_thresholds(self, results: Dict[str, Any]):
        """Check if alert thresholds are exceeded"""
        if not self.config.alert_thresholds:
            return
        
        for threshold_name, threshold_value in self.config.alert_thresholds.items():
            if threshold_name == "errors_per_hour":
                error_count = len(results["errors"])
                if error_count > threshold_value:
                    self.alert_counts[threshold_name] += 1
                    self.logger.warn("Alert threshold exceeded", 
                                   threshold=threshold_name,
                                   value=error_count,
                                   limit=threshold_value)
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of monitoring results"""
        return {
            "total_errors": len(results["errors"]),
            "total_warnings": len(results["warnings"]),
            "total_successes": len(results["successes"]),
            "files_checked": len(set(e["file"] for e in results["errors"] + results["warnings"] + results["successes"])),
            "most_common_error_patterns": self._get_most_common_patterns("error"),
            "most_common_warning_patterns": self._get_most_common_patterns("warning"),
            "alert_counts": dict(self.alert_counts)
        }
    
    def _get_most_common_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Get most common patterns of a specific type"""
        pattern_counts = Counter()
        
        for pattern, matches in self.pattern_matches.items():
            if pattern_type == "error" and any(p.search(pattern) for p in self.compiled_error_patterns):
                pattern_counts[pattern] = len(matches)
            elif pattern_type == "warning" and any(p.search(pattern) for p in self.compiled_warning_patterns):
                pattern_counts[pattern] = len(matches)
        
        return [{"pattern": pattern, "count": count} for pattern, count in pattern_counts.most_common(5)]
    
    def get_log_health_status(self) -> Dict[str, Any]:
        """Get overall log health status"""
        try:
            recent_results = self.check_logs()
            
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "summary": recent_results.get("summary", {}),
                "alerts": dict(self.alert_counts),
                "recommendations": []
            }
            
            # Determine health status
            error_count = recent_results.get("summary", {}).get("total_errors", 0)
            warning_count = recent_results.get("summary", {}).get("total_warnings", 0)
            
            if error_count > 10:
                health_status["status"] = "critical"
                health_status["recommendations"].append("High error count detected - investigate immediately")
            elif error_count > 5:
                health_status["status"] = "warning"
                health_status["recommendations"].append("Elevated error count - monitor closely")
            elif warning_count > 20:
                health_status["status"] = "warning"
                health_status["recommendations"].append("High warning count - review configuration")
            
            if not health_status["recommendations"]:
                health_status["recommendations"].append("Logs appear healthy")
            
            return health_status
            
        except Exception as e:
            self.logger.error("Failed to get log health status", error=str(e))
            return {"status": "error", "error": str(e)}
    
    def search_logs(self, query: str, log_directories: List[str] = None, 
                   hours: int = 24) -> List[Dict[str, Any]]:
        """Search logs for specific query"""
        try:
            results = []
            search_pattern = re.compile(query, re.IGNORECASE)
            
            directories = log_directories or self.config.log_directories or ["/var/log/vwe"]
            
            for log_dir in directories:
                if not Path(log_dir).exists():
                    continue
                
                log_files = self._get_recent_log_files(log_dir, hours)
                
                for log_file in log_files:
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if search_pattern.search(line):
                                    results.append({
                                        "file": str(log_file),
                                        "line": line_num,
                                        "content": line.strip(),
                                        "timestamp": self._extract_timestamp(line)
                                    })
                    except Exception as e:
                        self.logger.warn("Failed to search log file", 
                                       file_path=str(log_file),
                                       error=str(e))
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to search logs", 
                            query=query,
                            error=str(e))
            return []


def main():
    """Example usage of log monitor"""
    
    # Create log monitor
    config = MonitoringConfig(
        log_directories=["/var/log/vwe"],
        alert_thresholds={"errors_per_hour": 5}
    )
    monitor = LogMonitor(config)
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Wait a bit
    time.sleep(5)
    
    # Get health status
    health = monitor.get_log_health_status()
    print(f"Log health: {health}")
    
    # Search logs
    search_results = monitor.search_logs("ERROR", hours=1)
    print(f"Error search results: {len(search_results)} matches")
    
    # Stop monitoring
    monitor.stop_monitoring()


if __name__ == "__main__":
    main()
