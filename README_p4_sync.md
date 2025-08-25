# Perforce Recursive Sync Script

A comprehensive Python script for recursively syncing files in Perforce with advanced features and error handling.

## Features

- **Recursive Directory Sync**: Sync entire directory trees from Perforce depot
- **Selective File Sync**: Sync specific files or file patterns
- **Preview Mode**: See what would be synced without actually syncing
- **Force Sync**: Overwrite local changes when needed
- **Client Management**: Work with specific Perforce clients
- **Status Checking**: View sync status of local files
- **Comprehensive Logging**: Detailed logging to both console and file
- **Error Handling**: Robust error handling and user feedback

## Prerequisites

- Python 3.6 or higher
- Perforce client (`p4`) installed and in your PATH
- Valid Perforce connection and client workspace

## Installation

1. Download the script files:
   - `p4_sync_recursive.py` - Main script
   - `requirements.txt` - Dependencies (none required)
   - `README_p4_sync.md` - This documentation

2. Make the script executable (Linux/Mac):
   ```bash
   chmod +x p4_sync_recursive.py
   ```

3. Ensure Perforce client is accessible:
   ```bash
   p4 info
   ```

## Usage

### Basic Commands

#### Sync Current Workspace
```bash
python p4_sync_recursive.py
```
This will sync all files in your current Perforce workspace.

#### Sync Specific Directory
```bash
python p4_sync_recursive.py --path //depot/main/project
```
Sync all files in the specified depot path recursively.

#### Preview Sync Operations
```bash
python p4_sync_recursive.py --path //depot/main/project --preview
```
See what files would be synced without actually syncing them.

#### Force Sync (Overwrite Local Changes)
```bash
python p4_sync_recursive.py --force
```
Force sync will overwrite any local changes.

#### Sync Specific Files
```bash
python p4_sync_recursive.py --files //depot/main/file1.txt //depot/main/file2.txt
```

#### Use Specific Client
```bash
python p4_sync_recursive.py --client my_client_name
```

#### Check Sync Status
```bash
python p4_sync_recursive.py --status
```
Shows which files are out of sync or not in the depot.

#### Verbose Logging
```bash
python p4_sync_recursive.py --verbose
```
Enable detailed debug logging.

### Advanced Usage Examples

#### Sync Multiple Paths
```bash
# Sync main project
python p4_sync_recursive.py --path //depot/main/project

# Then sync specific subdirectory
python p4_sync_recursive.py --path //depot/main/project/subdir
```

#### Batch Operations
```bash
# Create a script for regular syncs
#!/bin/bash
python p4_sync_recursive.py --path //depot/main/project --verbose
python p4_sync_recursive.py --path //depot/main/docs --preview
```

#### Integration with CI/CD
```bash
# In your build script
python p4_sync_recursive.py --path //depot/main/build --force
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--path` | Depot path to sync | `--path //depot/main/project` |
| `--files` | Specific files to sync | `--files file1.txt file2.txt` |
| `--client` | Perforce client name | `--client my_client` |
| `--force` | Force sync (overwrite local) | `--force` |
| `--preview` | Preview mode only | `--preview` |
| `--status` | Show sync status | `--status` |
| `--verbose` | Enable verbose logging | `--verbose` |
| `-h, --help` | Show help message | `--help` |

## Output and Logging

The script provides:
- **Console Output**: Real-time progress and status information
- **Log File**: Detailed logs saved to `p4_sync.log`
- **Progress Indicators**: File count and processing progress
- **Error Reporting**: Clear error messages and suggestions

### Log File Location
- Default: `p4_sync.log` in the current directory
- Contains timestamps, log levels, and detailed operation information

## Error Handling

The script handles common Perforce errors:
- Connection failures
- Authentication issues
- File permission problems
- Invalid depot paths
- Client workspace issues

## Best Practices

1. **Always use `--preview` first** for large syncs to understand the scope
2. **Use `--force` carefully** as it overwrites local changes
3. **Check sync status** before and after operations
4. **Monitor log files** for detailed operation history
5. **Use specific paths** rather than syncing entire workspaces when possible

## Troubleshooting

### Common Issues

#### "Perforce client not found"
- Ensure `p4` is in your PATH
- Install Perforce client if not present

#### "Perforce connection failed"
- Check your Perforce server connection
- Verify authentication (run `p4 login` if needed)
- Check network connectivity

#### "No files found in depot path"
- Verify the depot path exists
- Check your client mapping
- Ensure you have access to the specified path

#### "Permission denied"
- Check file permissions
- Verify your Perforce user has access to the files
- Run `p4 login` to refresh authentication

### Debug Mode
Use `--verbose` flag to get detailed debug information:
```bash
python p4_sync_recursive.py --path //depot/main/project --verbose
```

## Script Architecture

The script is organized into a `PerforceSync` class with methods for:
- **Command Execution**: Running Perforce commands safely
- **File Discovery**: Finding files in depot paths
- **Sync Operations**: Individual and batch file syncing
- **Status Checking**: Determining sync state of files
- **Logging**: Comprehensive operation logging

## Contributing

The script is designed to be extensible. You can:
- Add new sync strategies
- Implement additional Perforce operations
- Customize logging and output formats
- Add integration with other tools

## License

This script is provided as-is for educational and practical use. Modify as needed for your environment.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the log files for detailed error information
3. Use `--verbose` flag for debug output
4. Verify Perforce client configuration
