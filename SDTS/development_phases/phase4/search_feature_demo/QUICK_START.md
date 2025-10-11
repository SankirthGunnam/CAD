# Quick Start Guide - Search Feature Demo

## Prerequisites
- Python 3.7 or higher
- Virtual environment (recommended)

## Setup and Run

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
# or
pip install PySide6
```

### 3. Run the Demo
```bash
python search_demo.py
```

### 4. Alternative: Use the Launcher
```bash
python run_demo.py
```

## Testing
Run the test suite to verify functionality:
```bash
python test_search.py
```

## Features Demonstrated

### 🔍 **Unified Search Interface**
- Single search bar for all widgets
- Scope selection (Current Tab vs All Tabs)
- Navigation buttons (Previous/Next)
- Clear functionality

### 📋 **Widget Types**
1. **Tree Widget**: File system structure with hierarchical search
2. **Table Widget**: Device management table with cell search
3. **Text Edit Widget**: Code/documentation with text highlighting
4. **Complex Tab**: Multiple widgets in one tab (tree + table + text)

### 🎯 **Search Capabilities**
- **Tree**: Recursive search through all items
- **Table**: Search across all cells
- **Text**: Full-text search with highlighting
- **Complex Tab**: Search across multiple widget types simultaneously

## Usage Examples

### Basic Search
1. Enter search text (e.g., "python", "device", "project")
2. Select scope (Current Tab or All Tabs)
3. Click "Search" or press Enter
4. Use Previous/Next to navigate results

### Complex Tab Search
- Switch to "Complex Tab"
- Search for terms like "React", "Python", "Development"
- Results cycle through tree, table, and text widgets

### Sample Search Terms
- **Tree Tab**: "python", "documents", "images"
- **Table Tab**: "sensor", "active", "device"
- **Text Tab**: "function", "database", "error"
- **Complex Tab**: "react", "python", "development"

## Troubleshooting

### PySide6 Installation Issues
If you encounter installation problems:
```bash
# Try with --user flag
pip install --user PySide6

# Or use system package manager
sudo apt install python3-pyside6  # Ubuntu/Debian
```

### Display Issues (WSL/Linux)
If running in WSL or headless environment:
```bash
# Install X11 forwarding
sudo apt install x11-apps

# Run with display forwarding
export DISPLAY=:0
python search_demo.py
```

### Virtual Environment Issues
If virtual environment doesn't work:
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install PySide6
```

## File Structure
```
search_feature_demo/
├── search_demo.py          # Main demo application
├── test_search.py          # Test suite
├── run_demo.py            # Launcher script
├── requirements.txt       # Dependencies
├── README.md             # Detailed documentation
├── QUICK_START.md        # This file
└── venv/                 # Virtual environment (created)
```

## Integration Notes

The search functionality is designed to be easily integrated into existing applications:

1. **Extend Base Widgets**: Create searchable versions of your widgets
2. **Register with Manager**: Use TabSearchManager for tab coordination
3. **Customize Highlighting**: Modify colors and behavior as needed
4. **Add to Existing UI**: Integrate search controls into your layout

## Support

For issues or questions:
1. Check the main README.md for detailed documentation
2. Run the test suite to verify functionality
3. Review the code comments for implementation details
