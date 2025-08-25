#!/usr/bin/env python3
"""
Perforce Recursive Sync Script

This script provides functionality to recursively sync files in Perforce,
including options for force sync, preview mode, and selective syncing.
"""

import subprocess
import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import json


class PerforceSync:
    """Handles Perforce operations for recursive file syncing."""
    
    def __init__(self, client_name: Optional[str] = None, force: bool = False):
        """
        Initialize Perforce sync handler.
        
        Args:
            client_name: Optional Perforce client name
            force: Whether to force sync (overwrite local changes)
        """
        self.client_name = client_name
        self.force = force
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('p4_sync.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def run_p4_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Execute a Perforce command.
        
        Args:
            command: List of command arguments
            capture_output: Whether to capture command output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            if self.client_name:
                command.extend(['-c', self.client_name])
            
            self.logger.debug(f"Running command: {' '.join(command)}")
            
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(command, check=False)
                return result.returncode, "", ""
                
        except FileNotFoundError:
            self.logger.error("Perforce client (p4) not found in PATH")
            return 1, "", "Perforce client not found"
        except Exception as e:
            self.logger.error(f"Error running Perforce command: {e}")
            return 1, "", str(e)
    
    def check_p4_connection(self) -> bool:
        """Check if Perforce connection is working."""
        return_code, stdout, stderr = self.run_p4_command(['p4', 'info'])
        if return_code == 0:
            self.logger.info("Perforce connection successful")
            return True
        else:
            self.logger.error(f"Perforce connection failed: {stderr}")
            return False
    
    def get_client_info(self) -> Optional[str]:
        """Get current Perforce client information."""
        return_code, stdout, stderr = self.run_p4_command(['p4', 'client', '-o'])
        if return_code == 0:
            # Parse client name from output
            for line in stdout.split('\n'):
                if line.startswith('Client:'):
                    return line.split(':', 1)[1].strip()
        return None
    
    def get_depot_files(self, path: str) -> List[str]:
        """
        Get list of files in depot at specified path.
        
        Args:
            path: Depot path to search
            
        Returns:
            List of depot file paths
        """
        return_code, stdout, stderr = self.run_p4_command(['p4', 'files', path])
        if return_code == 0:
            files = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    # Extract file path from p4 files output
                    parts = line.split()
                    if len(parts) >= 1:
                        files.append(parts[0])
            return files
        else:
            self.logger.error(f"Failed to get depot files: {stderr}")
            return []
    
    def sync_file(self, depot_path: str, preview: bool = False) -> bool:
        """
        Sync a single file from depot.
        
        Args:
            depot_path: Depot path of the file
            preview: If True, only preview the sync operation
            
        Returns:
            True if successful, False otherwise
        """
        command = ['p4', 'sync']
        
        if preview:
            command.append('-n')  # Preview mode
        elif self.force:
            command.append('-f')  # Force sync
            
        command.append(depot_path)
        
        return_code, stdout, stderr = self.run_p4_command(command)
        
        if return_code == 0:
            if preview:
                self.logger.info(f"Preview sync for: {depot_path}")
                self.logger.info(stdout)
            else:
                self.logger.info(f"Synced: {depot_path}")
            return True
        else:
            self.logger.error(f"Failed to sync {depot_path}: {stderr}")
            return False
    
    def sync_directory_recursive(self, depot_path: str, preview: bool = False) -> Tuple[int, int]:
        """
        Recursively sync all files in a directory.
        
        Args:
            depot_path: Depot directory path
            preview: If True, only preview the sync operation
            
        Returns:
            Tuple of (successful_syncs, total_files)
        """
        self.logger.info(f"Starting recursive sync for: {depot_path}")
        
        # Get all files in the directory
        files = self.get_depot_files(f"{depot_path}/...")
        
        if not files:
            self.logger.warning(f"No files found in depot path: {depot_path}")
            return 0, 0
        
        self.logger.info(f"Found {len(files)} files to sync")
        
        successful = 0
        total = len(files)
        
        for i, file_path in enumerate(files, 1):
            self.logger.info(f"Processing file {i}/{total}: {file_path}")
            
            if self.sync_file(file_path, preview):
                successful += 1
            
            # Progress indicator
            if i % 10 == 0:
                self.logger.info(f"Progress: {i}/{total} files processed")
        
        return successful, total
    
    def sync_specific_files(self, file_list: List[str], preview: bool = False) -> Tuple[int, int]:
        """
        Sync a specific list of files.
        
        Args:
            file_list: List of depot file paths
            preview: If True, only preview the sync operation
            
        Returns:
            Tuple of (successful_syncs, total_files)
        """
        self.logger.info(f"Syncing {len(file_list)} specific files")
        
        successful = 0
        total = len(file_list)
        
        for i, file_path in enumerate(file_list, 1):
            self.logger.info(f"Processing file {i}/{total}: {file_path}")
            
            if self.sync_file(file_path, preview):
                successful += 1
        
        return successful, total
    
    def get_sync_status(self, local_path: str = ".") -> dict:
        """
        Get sync status for local files.
        
        Args:
            local_path: Local path to check
            
        Returns:
            Dictionary with sync status information
        """
        status = {
            'out_of_sync': [],
            'not_in_depot': [],
            'up_to_date': []
        }
        
        # Check for files that need sync
        return_code, stdout, stderr = self.run_p4_command(
            ['p4', 'sync', '-n', f"{local_path}/..."]
        )
        
        if return_code == 0:
            for line in stdout.split('\n'):
                if line.strip() and 'updating' in line:
                    # Extract file path from sync output
                    parts = line.split()
                    if len(parts) >= 2:
                        status['out_of_sync'].append(parts[1])
        
        # Check for files not in depot
        return_code, stdout, stderr = self.run_p4_command(
            ['p4', 'reconcile', '-n', f"{local_path}/..."]
        )
        
        if return_code == 0:
            for line in stdout.split('\n'):
                if line.strip() and 'add' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        status['not_in_depot'].append(parts[1])
        
        return status


def main():
    """Main function to handle command line arguments and execute sync operations."""
    parser = argparse.ArgumentParser(
        description="Recursively sync files in Perforce",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync entire workspace
  python p4_sync_recursive.py
  
  # Preview sync for specific directory
  python p4_sync_recursive.py --path //depot/main/project --preview
  
  # Force sync specific files
  python p4_sync_recursive.py --files file1.txt file2.txt --force
  
  # Sync with specific client
  python p4_sync_recursive.py --client my_client --path //depot/main
        """
    )
    
    parser.add_argument(
        '--path',
        help='Depot path to sync (e.g., //depot/main/project)'
    )
    
    parser.add_argument(
        '--files',
        nargs='+',
        help='Specific files to sync'
    )
    
    parser.add_argument(
        '--client',
        help='Perforce client name to use'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force sync (overwrite local changes)'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview sync operations without executing them'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show sync status for local files'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize Perforce sync handler
    p4_sync = PerforceSync(client_name=args.client, force=args.force)
    
    # Check Perforce connection
    if not p4_sync.check_p4_connection():
        sys.exit(1)
    
    # Show client info
    client_info = p4_sync.get_client_info()
    if client_info:
        print(f"Using Perforce client: {client_info}")
    
    try:
        if args.status:
            # Show sync status
            status = p4_sync.get_sync_status()
            print("\nSync Status:")
            print(f"Files out of sync: {len(status['out_of_sync'])}")
            print(f"Files not in depot: {len(status['not_in_depot'])}")
            
            if status['out_of_sync']:
                print("\nOut of sync files:")
                for file_path in status['out_of_sync'][:10]:  # Show first 10
                    print(f"  {file_path}")
                if len(status['out_of_sync']) > 10:
                    print(f"  ... and {len(status['out_of_sync']) - 10} more")
            
        elif args.files:
            # Sync specific files
            successful, total = p4_sync.sync_specific_files(args.files, args.preview)
            print(f"\nSync completed: {successful}/{total} files successful")
            
        elif args.path:
            # Sync directory recursively
            successful, total = p4_sync.sync_directory_recursive(args.path, args.preview)
            print(f"\nSync completed: {successful}/{total} files successful")
            
        else:
            # Default: sync current workspace
            current_dir = os.getcwd()
            print(f"Syncing current workspace: {current_dir}")
            
            # Get workspace root from Perforce
            return_code, stdout, stderr = p4_sync.run_p4_command(['p4', 'info'])
            if return_code == 0:
                for line in stdout.split('\n'):
                    if line.startswith('Client root:'):
                        client_root = line.split(':', 1)[1].strip()
                        print(f"Client root: {client_root}")
                        break
            
            successful, total = p4_sync.sync_directory_recursive(".", args.preview)
            print(f"\nSync completed: {successful}/{total} files successful")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during sync operation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
