# Search Feature Demo

This demo showcases comprehensive search functionality across different Qt widget types, including the complex scenario of searching within tab widgets that contain multiple nested widgets.

## Features

### 1. **Unified Search Interface**
- Single search bar that works across all widget types
- Search scope selection (Current Tab vs All Tabs)
- Navigation buttons (Previous/Next) to cycle through results
- Clear button to reset all highlights

### 2. **Widget-Specific Search Implementations**

#### **Tree Widget Search**
- Recursive search through all tree items
- Visual highlighting of matching items
- Navigation through search results
- Maintains tree structure visibility

#### **Table Widget Search**
- Searches across all cells in the table
- Highlights matching cells with background color
- Navigation through search results
- Automatic scrolling to highlighted cells

#### **Text Edit Widget Search**
- Full-text search with syntax highlighting
- Highlights all occurrences of search text
- Cursor positioning to search results
- Support for case-sensitive and case-insensitive search

#### **Complex Tab Widget Search**
- Handles tabs containing multiple widget types
- Searches across all nested widgets simultaneously
- **Cross-widget navigation**: Next/Previous buttons cycle through different widget types
- **Circular navigation**: After last item in last widget, loops back to first item in first widget
- Visual feedback showing which widget is currently active (blue border)
- Search status display showing result counts for each widget type
- Maintains context when switching between tabs

## Widget Types Demonstrated

### 1. **Tree Widget Tab**
- File system structure simulation
- Hierarchical data with expandable nodes
- Search through folder and file names

### 2. **Table Widget Tab**
- Device management table
- Multiple columns with different data types
- Search across all columns simultaneously

### 3. **Text Edit Widget Tab**
- Code and documentation example
- Mixed content (code, config, logs, notes)
- Syntax-aware search highlighting

### 4. **Complex Tab**
- **Left Panel**: Project structure tree
- **Right Panel**: Project details table
- **Bottom Panel**: Project description text
- Demonstrates search across multiple widget types in a single tab

## Search Functionality Details

### **Search Methods**
- **Current Tab**: Searches only in the currently active tab
- **All Tabs**: Searches across all registered tabs simultaneously

### **Navigation**
- **Next (→)**: Move to the next search result
- **Previous (←)**: Move to the previous search result
- **Clear**: Remove all search highlights and reset
- **Complex Tab**: Navigation cycles through different widget types (Tree → Table → Text)
- **Circular**: After last item in last widget, loops back to first item in first widget

### **Visual Feedback**
- **Yellow highlighting**: Search results are highlighted in light yellow
- **Current result**: The currently selected result is highlighted more prominently
- **Active widget indicator**: Blue border around the currently active widget in complex tab
- **Search status display**: Shows result counts for each widget type in complex tab
- **Auto-scroll**: Widgets automatically scroll to show search results

## Technical Implementation

### **Core Classes**

#### `SearchableTreeWidget`
- Extends `QTreeWidget` with search capabilities
- Recursive search through tree hierarchy
- Visual highlighting and navigation

#### `SearchableTableWidget`
- Extends `QTableWidget` with search capabilities
- Cell-by-cell search with highlighting
- Result navigation with visual feedback

#### `SearchableTextEdit`
- Extends `QTextEdit` with search capabilities
- Text highlighting using `QTextCharFormat`
- Cursor positioning to search results

#### `TabSearchManager`
- Manages search functionality across tabs
- Widget registration and search coordination
- Scope-based search execution

#### `SearchHighlighter`
- Helper class for text highlighting
- Manages highlight formatting and application

### **Key Features**

1. **Extensible Design**: Easy to add search functionality to new widget types
2. **Unified Interface**: Single search bar controls all widgets
3. **Context Preservation**: Maintains widget state during search operations
4. **Performance Optimized**: Efficient search algorithms for large datasets
5. **User-Friendly**: Intuitive navigation and visual feedback

## Usage Instructions

### **Running the Demo**
```bash
cd search_feature_demo
python search_demo.py
```

### **Basic Search**
1. Enter search text in the search input field
2. Select search scope (Current Tab or All Tabs)
3. Click "Search" or press Enter
4. Use Previous/Next buttons to navigate results

### **Advanced Features**
- **Tab-specific search**: Switch tabs and search within specific widget types
- **Complex tab navigation**: In the complex tab, search results cycle through tree, table, and text widgets
- **Clear functionality**: Use the Clear button to reset all highlights

## Sample Data

The demo includes realistic sample data to demonstrate search capabilities:

### **Tree Widget**
- File system structure with documents, images, and code folders
- Nested hierarchy with multiple levels

### **Table Widget**
- Device management data with names, types, status, and descriptions
- Various device types (sensors, actuators, displays, etc.)

### **Text Edit Widget**
- Mixed content including Python code, configuration files, log entries, and notes
- Demonstrates search across different content types

### **Complex Tab**
- Project management data with structure tree, details table, and descriptions
- Shows how search works across multiple widget types simultaneously

## Integration Guidelines

### **Adding Search to Existing Widgets**
1. Create a searchable widget class extending the base widget
2. Implement the `search()`, `next_search_result()`, and `previous_search_result()` methods
3. Register the widget with the `TabSearchManager`
4. Add visual highlighting and navigation logic

### **Customizing Search Behavior**
- Modify highlight colors in the `SearchHighlighter` class
- Adjust search algorithms for specific data types
- Customize navigation behavior for complex widgets

### **Performance Considerations**
- For large datasets, consider implementing incremental search
- Use background threads for search operations in complex scenarios
- Implement search result caching for frequently searched content

## Recent Fixes

### **Complex Tab Navigation Issue (Fixed ✅)**
- **Problem**: Next/Previous buttons were stuck within individual widgets instead of jumping between widget types
- **Solution**: Implemented boundary detection to automatically jump to next/previous widget when reaching the last/first result
- **Behavior**: 
  - **Next**: Jumps to next widget when at last result in current widget
  - **Previous**: Jumps to previous widget when at first result in current widget
  - **Within**: Stays in current widget when not at boundary
- **Navigation Flow**: Tree → Table → Text → Tree (with proper cycling)

## Future Enhancements

1. **Regex Search**: Add support for regular expression search
2. **Case Sensitivity**: Add toggle for case-sensitive search
3. **Search History**: Maintain search history for quick access
4. **Advanced Filters**: Add filtering options for specific data types
5. **Export Results**: Allow exporting search results to external formats
6. **Search Statistics**: Display count of search results
7. **Keyboard Shortcuts**: Add keyboard shortcuts for search operations

## Dependencies

- **PySide6**: Qt bindings for Python
- **Python 3.7+**: Required for type hints and modern features

## License

This demo is provided as a reference implementation for search functionality in Qt applications. Feel free to adapt and extend it for your specific needs.
