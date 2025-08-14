#!/usr/bin/env python3
"""
Test Runner Script for SDTS Project - TDD Workflow Support

This script provides a comprehensive test running interface that supports
Test-Driven Development (TDD) workflow with various test execution modes.

Usage:
    python run_tests.py [options]
    
Examples:
    python run_tests.py --unit                    # Run only unit tests
    python run_tests.py --integration             # Run only integration tests
    python run_tests.py --fast                    # Run fast tests (exclude slow)
    python run_tests.py --coverage                # Run with coverage report
    python run_tests.py --watch                   # Watch mode for TDD
    python run_tests.py --file test_main.py       # Run specific test file
    python run_tests.py --smoke                   # Run smoke tests
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Optional

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


class TestRunner:
    """Main test runner class for SDTS project"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "htmlcov"
        
    def print_banner(self, title: str):
        """Print a formatted banner"""
        print(f"\n{Color.CYAN}{Color.BOLD}{'='*60}{Color.END}")
        print(f"{Color.CYAN}{Color.BOLD}{title.center(60)}{Color.END}")
        print(f"{Color.CYAN}{Color.BOLD}{'='*60}{Color.END}\n")
        
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Color.GREEN}✓ {message}{Color.END}")
        
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Color.RED}✗ {message}{Color.END}")
        
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Color.YELLOW}⚠ {message}{Color.END}")
        
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Color.BLUE}ℹ {message}{Color.END}")
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        self.print_info("Checking dependencies...")
        
        required_packages = ["pytest", "pytest-qt", "pytest-cov", "PySide6"]
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == "pytest-qt":
                    __import__("pytestqt")
                else:
                    __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.print_error(f"Missing required packages: {', '.join(missing_packages)}")
            self.print_info("Install them with: pip install " + " ".join(missing_packages))
            return False
        
        self.print_success("All dependencies are available")
        return True
    
    def build_pytest_command(self, args: argparse.Namespace) -> List[str]:
        """Build pytest command based on arguments"""
        cmd = ["python", "-m", "pytest"]
        
        # Add test directory
        if args.file:
            test_path = self.test_dir / args.file
            if not test_path.exists():
                # Try finding the file in subdirectories
                found_files = list(self.test_dir.rglob(args.file))
                if found_files:
                    test_path = found_files[0]
                else:
                    self.print_error(f"Test file not found: {args.file}")
                    return None
            cmd.append(str(test_path))
        else:
            cmd.append(str(self.test_dir))
        
        # Add markers for test filtering
        markers = []
        if args.unit:
            markers.append("unit")
        if args.integration:
            markers.append("integration")
        if args.smoke:
            markers.append("smoke")
        if args.fast:
            markers.append("not slow")
        if args.gui:
            markers.append("gui")
        if args.performance:
            markers.append("performance")
            
        if markers:
            cmd.extend(["-m", " and ".join(markers)])
        
        # Coverage options
        if args.coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=html",
                "--cov-report=term-missing",
                f"--cov-fail-under={args.coverage_threshold}"
            ])
        
        # Verbosity
        if args.verbose:
            cmd.append("-v")
        elif args.quiet:
            cmd.append("-q")
        
        # Additional options
        if args.parallel:
            cmd.extend(["-n", "auto"])
        
        if args.fail_fast:
            cmd.append("-x")
            
        if args.last_failed:
            cmd.append("--lf")
            
        if args.collect_only:
            cmd.append("--collect-only")
        
        # Custom pytest arguments
        if args.pytest_args:
            cmd.extend(args.pytest_args.split())
        
        return cmd
    
    def run_tests(self, args: argparse.Namespace) -> int:
        """Run tests with specified arguments"""
        if not self.check_dependencies():
            return 1
            
        cmd = self.build_pytest_command(args)
        if not cmd:
            return 1
        
        self.print_banner("Running Tests")
        self.print_info(f"Command: {' '.join(cmd)}")
        self.print_info(f"Working directory: {self.project_root}")
        
        # Set environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)
        env["SDTS_TEST_MODE"] = "1"
        
        if args.headless:
            env["QT_QPA_PLATFORM"] = "offscreen"
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, env=env)
            
            if result.returncode == 0:
                self.print_success("All tests passed!")
                
                if args.coverage and (self.coverage_dir / "index.html").exists():
                    self.print_info(f"Coverage report: {self.coverage_dir / 'index.html'}")
            else:
                self.print_error("Some tests failed!")
            
            return result.returncode
            
        except KeyboardInterrupt:
            self.print_warning("Tests interrupted by user")
            return 1
        except Exception as e:
            self.print_error(f"Error running tests: {e}")
            return 1
    
    def watch_tests(self, args: argparse.Namespace):
        """Watch for file changes and re-run tests (TDD mode)"""
        self.print_banner("TDD Watch Mode")
        self.print_info("Watching for file changes...")
        self.print_info("Press Ctrl+C to exit")
        
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            self.print_error("watchdog package required for watch mode")
            self.print_info("Install with: pip install watchdog")
            return 1
        
        class TestHandler(FileSystemEventHandler):
            def __init__(self, runner, args):
                self.runner = runner
                self.args = args
                self.last_run = 0
                
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                # Only watch Python files
                if not event.src_path.endswith('.py'):
                    return
                
                # Debounce rapid file changes
                now = time.time()
                if now - self.last_run < 1:
                    return
                self.last_run = now
                
                print(f"\n{Color.YELLOW}File changed: {event.src_path}{Color.END}")
                self.runner.run_tests(self.args)
                print(f"\n{Color.CYAN}Waiting for changes...{Color.END}")
        
        # Initial test run
        self.run_tests(args)
        
        # Set up file watcher
        event_handler = TestHandler(self, args)
        observer = Observer()
        
        # Watch source directories
        observer.schedule(event_handler, str(self.project_root / "apps"), recursive=True)
        observer.schedule(event_handler, str(self.project_root / "gui"), recursive=True)
        observer.schedule(event_handler, str(self.test_dir), recursive=True)
        observer.schedule(event_handler, str(self.project_root / "main.py"))
        
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            self.print_info("Watch mode stopped")
        
        observer.join()
        return 0
    
    def show_test_structure(self):
        """Show the current test structure"""
        self.print_banner("Test Structure")
        
        if not self.test_dir.exists():
            self.print_error("Tests directory not found!")
            return
        
        def print_tree(path: Path, prefix: str = ""):
            items = sorted(path.iterdir())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and not item.name.startswith('.'):
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(item, next_prefix)
        
        print(f"📁 {self.test_dir.name}/")
        print_tree(self.test_dir)
    
    def clean_artifacts(self):
        """Clean test artifacts"""
        self.print_banner("Cleaning Test Artifacts")
        
        artifacts = [
            ".pytest_cache",
            "__pycache__",
            "htmlcov",
            "coverage.xml",
            ".coverage",
            "tests.log"
        ]
        
        for artifact in artifacts:
            artifact_path = self.project_root / artifact
            if artifact_path.exists():
                if artifact_path.is_dir():
                    import shutil
                    shutil.rmtree(artifact_path)
                    self.print_success(f"Removed directory: {artifact}")
                else:
                    artifact_path.unlink()
                    self.print_success(f"Removed file: {artifact}")
            else:
                self.print_info(f"Not found: {artifact}")


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="SDTS Test Runner - TDD Workflow Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --unit                    # Run unit tests only
  %(prog)s --integration             # Run integration tests only
  %(prog)s --fast                    # Run fast tests (exclude slow)
  %(prog)s --coverage                # Run with coverage report
  %(prog)s --watch                   # TDD watch mode
  %(prog)s --file test_main.py       # Run specific test file
  %(prog)s --smoke                   # Run smoke tests
  %(prog)s --clean                   # Clean test artifacts
        """
    )
    
    # Test selection
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--fast", action="store_true", help="Run fast tests (exclude slow)")
    parser.add_argument("--gui", action="store_true", help="Run GUI tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--file", help="Run specific test file")
    
    # Test execution
    parser.add_argument("--watch", action="store_true", help="Watch mode for TDD")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--last-failed", action="store_true", help="Run only last failed tests")
    parser.add_argument("--collect-only", action="store_true", help="Collect tests without running")
    
    # Coverage
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--coverage-threshold", type=int, default=80, help="Coverage threshold (default: 80)")
    
    # Output
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--headless", action="store_true", help="Run GUI tests headlessly")
    
    # Utilities
    parser.add_argument("--structure", action="store_true", help="Show test structure")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--pytest-args", help="Additional pytest arguments")
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Handle utility commands
    if args.clean:
        runner.clean_artifacts()
        return 0
    
    if args.structure:
        runner.show_test_structure()
        return 0
    
    # Handle test execution
    if args.watch:
        return runner.watch_tests(args)
    else:
        return runner.run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
