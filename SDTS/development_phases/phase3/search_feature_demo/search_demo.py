#!/usr/bin/env python3
"""
Search Feature Demo using QTreeView and QTableView with Model-View Architecture
This demo follows the same pattern as legacy_bcf_manager.py with TreeItem and TreeModel classes.
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTreeView, QTableView, QTextEdit, QLineEdit,
    QPushButton, QLabel, QGroupBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, Signal, QObject,
    QAbstractTableModel, QSortFilterProxyModel
)
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor, QSyntaxHighlighter, QTextDocument


class TreeItem:
    """Internal class to represent tree items - following legacy_bcf_manager.py pattern"""
    
    def __init__(self, name, parent=None, data=None):
        self.name = name
        self.data = data or {}
        self.children = []
        self.parent = parent
        self.icon = None
        self.font = QFont()
        self.view_type = None
        
    def append_child(self, child):
        self.children.append(child)
        child.parent = self
        
    def child(self, row):
        return self.children[row] if 0 <= row < len(self.children) else None
        
    def child_count(self):
        return len(self.children)
        
    def row(self):
        return self.parent.children.index(self) if self.parent else 0


class TreeModel(QAbstractItemModel):
    """Model that creates a tree structure - following legacy_bcf_manager.py pattern"""
    
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.root = TreeItem("Root")
        if data:
            self._build_tree(self.root, data)
            
    def _build_tree(self, parent_node, tree_dict):
        """Build tree structure from dictionary"""
        for key, value in tree_dict.items():
            child_node = TreeItem(key, data=value)
            
            # Set view type based on the value
            if isinstance(value, dict):
                child_node.view_type = "table"
            else:
                child_node.view_type = value
                
            # Customize font and icon
            font = QFont()
            font.setBold(True if not parent_node.parent else False)
            child_node.font = font
            
            parent_node.append_child(child_node)
            
            if isinstance(value, dict):
                self._build_tree(child_node, value)
                
    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
            
        parent_node = self.get_node(parent)
        child_node = parent_node.child(row)
        if child_node:
            return self.createIndex(row, column, child_node)
        return QModelIndex()
        
    def parent(self, index):
        node = self.get_node(index)
        if not node or not node.parent or node.parent == self.root:
            return QModelIndex()
        return self.createIndex(node.parent.row(), 0, node.parent)
        
    def rowCount(self, parent=QModelIndex()):
        node = self.get_node(parent)
        return node.child_count()
        
    def columnCount(self, parent=QModelIndex()):
        return 1
        
    def data(self, index, role=Qt.DisplayRole):
        node = self.get_node(index)
        if not node:
            return None
            
        if role == Qt.DisplayRole:
            return node.name
        elif role == Qt.FontRole:
            return node.font
        elif role == Qt.DecorationRole:
            return node.icon
        elif role == Qt.UserRole:
            return node.view_type
        return None
        
    def get_node(self, index):
        return index.internalPointer() if index.isValid() else self.root


class TableModel(QAbstractTableModel):
    """Table model for QTableView"""
    
    def __init__(self, data=None, headers=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._headers = headers or ["Column 1", "Column 2", "Column 3", "Column 4"]
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
        
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if 0 <= row < len(self._data) and 0 <= col < len(self._headers):
                return str(self._data[row][col])
        return None
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None


class SearchHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for search results in QTextEdit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_format = QTextCharFormat()
        self.search_format.setBackground(QColor(255, 255, 0, 100))  # Yellow highlight
        self.search_format.setForeground(QColor(0, 0, 0))
        self.search_pattern = ""
        
    def highlightBlock(self, text):
        if self.search_pattern:
            import re
            pattern = re.escape(self.search_pattern)
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                self.setFormat(start, end - start, self.search_format)
                
    def set_search_pattern(self, pattern):
        self.search_pattern = pattern
        self.rehighlight()


class SearchableTreeView(QTreeView):
    """Searchable TreeView with search functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted_items = []
        self.current_highlight_index = -1
        self.search_term = ""
        
    def search(self, term):
        """Search for items in the tree"""
        self.search_term = term.lower()
        self.highlighted_items = []
        self.current_highlight_index = -1
        
        if not term:
            return
            
        model = self.model()
        if not model:
            return
            
        # Search through all items
        self._search_recursive(QModelIndex(), model)
        
        if self.highlighted_items:
            self.current_highlight_index = 0
            self._highlight_current_item()
            
    def _search_recursive(self, parent_index, model):
        """Recursively search through tree items"""
        for row in range(model.rowCount(parent_index)):
            index = model.index(row, 0, parent_index)
            item_text = model.data(index, Qt.DisplayRole)
            
            if item_text and self.search_term in item_text.lower():
                self.highlighted_items.append(index)
                
            # Search children
            if model.hasChildren(index):
                self._search_recursive(index, model)
                
    def _highlight_current_item(self):
        """Highlight the current search result"""
        if 0 <= self.current_highlight_index < len(self.highlighted_items):
            index = self.highlighted_items[self.current_highlight_index]
            self.setCurrentIndex(index)
            self.scrollTo(index, QAbstractItemView.PositionAtCenter)
            
    def next_search_result(self):
        """Move to next search result"""
        if self.highlighted_items:
            self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlighted_items)
            self._highlight_current_item()
            
    def previous_search_result(self):
        """Move to previous search result"""
        if self.highlighted_items:
            self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlighted_items)
            self._highlight_current_item()
            
    def clear_search(self):
        """Clear search highlighting"""
        self.highlighted_items = []
        self.current_highlight_index = -1
        self.search_term = ""


class SearchableTableView(QTableView):
    """Searchable TableView with search functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted_cells = []
        self.current_highlight_index = -1
        self.search_term = ""
        
    def search(self, term):
        """Search for items in the table"""
        self.search_term = term.lower()
        self.highlighted_cells = []
        self.current_highlight_index = -1
        
        if not term:
            return
            
        model = self.model()
        if not model:
            return
            
        # Search through all cells
        for row in range(model.rowCount()):
            for col in range(model.columnCount()):
                index = model.index(row, col)
                cell_text = model.data(index, Qt.DisplayRole)
                
                if cell_text and self.search_term in cell_text.lower():
                    self.highlighted_cells.append(index)
                    
        if self.highlighted_cells:
            self.current_highlight_index = 0
            self._highlight_current_cell()
            
    def _highlight_current_cell(self):
        """Highlight the current search result"""
        if 0 <= self.current_highlight_index < len(self.highlighted_cells):
            index = self.highlighted_cells[self.current_highlight_index]
            self.setCurrentIndex(index)
            self.scrollTo(index, QAbstractItemView.PositionAtCenter)
            
    def next_search_result(self):
        """Move to next search result"""
        if self.highlighted_cells:
            self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlighted_cells)
            self._highlight_current_cell()
            
    def previous_search_result(self):
        """Move to previous search result"""
        if self.highlighted_cells:
            self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlighted_cells)
            self._highlight_current_cell()
            
    def clear_search(self):
        """Clear search highlighting"""
        self.highlighted_cells = []
        self.current_highlight_index = -1
        self.search_term = ""


class SearchableTextEdit(QTextEdit):
    """Searchable TextEdit with search functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = SearchHighlighter(self.document())
        self.highlighted_positions = []
        self.current_highlight_index = -1
        self.search_term = ""
        
    def search(self, term):
        """Search for text in the document"""
        self.search_term = term
        self.highlighted_positions = []
        self.current_highlight_index = -1
        
        if not term:
            self.highlighter.set_search_pattern("")
            return
            
        # Find all occurrences
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        while True:
            cursor = self.document().find(term, cursor)
            if cursor.isNull():
                break
            self.highlighted_positions.append(cursor.position())
            
        if self.highlighted_positions:
            self.current_highlight_index = 0
            self._highlight_current_position()
            
        self.highlighter.set_search_pattern(term)
        
    def _highlight_current_position(self):
        """Highlight the current search result"""
        if 0 <= self.current_highlight_index < len(self.highlighted_positions):
            position = self.highlighted_positions[self.current_highlight_index]
            cursor = self.textCursor()
            cursor.setPosition(position)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            
    def next_search_result(self):
        """Move to next search result"""
        if self.highlighted_positions:
            self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlighted_positions)
            self._highlight_current_position()
            
    def previous_search_result(self):
        """Move to previous search result"""
        if self.highlighted_positions:
            self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlighted_positions)
            self._highlight_current_position()
            
    def clear_search(self):
        """Clear search highlighting"""
        self.highlighted_positions = []
        self.current_highlight_index = -1
        self.search_term = ""
        self.highlighter.set_search_pattern("")


class TabSearchManager(QObject):
    """Manages search across different tabs and widgets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_widget = None
        self.search_widgets = {}
        
    def set_tab_widget(self, tab_widget):
        """Set the tab widget to manage"""
        self.tab_widget = tab_widget
        
    def register_widget(self, tab_index, widget):
        """Register a searchable widget for a tab"""
        self.search_widgets[tab_index] = widget
        
    def search_all_tabs(self, term):
        """Search across all registered widgets"""
        for tab_index, widget in self.search_widgets.items():
            if hasattr(widget, 'search'):
                widget.search(term)
                
    def clear_all_searches(self):
        """Clear search in all registered widgets"""
        for widget in self.search_widgets.values():
            if hasattr(widget, 'clear_search'):
                widget.clear_search()


class SearchDemoWindow(QMainWindow):
    """Main window demonstrating search functionality with QTreeView and QTableView"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Search Feature Demo - TreeView & TableView")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize search manager
        self.search_manager = TabSearchManager()
        
        self._setup_ui()
        self._setup_search_controls()
        self._setup_tab_widget()
        self._populate_data()
        self._setup_search_functionality()
        
    def _setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        
    def _setup_search_controls(self):
        """Setup search controls"""
        search_group = QGroupBox("Search Controls")
        search_layout = QHBoxLayout(search_group)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        # Search buttons
        self.search_button = QPushButton("Search")
        self.next_button = QPushButton("Next")
        self.previous_button = QPushButton("Previous")
        self.clear_button = QPushButton("Clear")
        
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.previous_button)
        search_layout.addWidget(self.next_button)
        search_layout.addWidget(self.clear_button)
        
        # Search status
        self.search_status_label = QLabel("No search performed")
        search_layout.addWidget(self.search_status_label)
        
        self.main_layout.addWidget(search_group)
        
    def _setup_tab_widget(self):
        """Setup the tab widget with different views"""
        self.tab_widget = QTabWidget()
        self.search_manager.set_tab_widget(self.tab_widget)
        
        # Tree View Tab
        self._setup_tree_tab()
        
        # Table View Tab
        self._setup_table_tab()
        
        # Text Edit Tab
        self._setup_text_edit_tab()
        
        # Complex Tab (TreeView + TableView + TextEdit)
        self._setup_complex_tab()
        
        self.main_layout.addWidget(self.tab_widget)
        
    def _setup_tree_tab(self):
        """Setup tree view tab"""
        tree_widget = QWidget()
        layout = QVBoxLayout(tree_widget)
        
        self.tree_view = SearchableTreeView()
        layout.addWidget(self.tree_view)
        
        self.tab_widget.addTab(tree_widget, "Tree View")
        self.search_manager.register_widget(0, self.tree_view)
        
    def _setup_table_tab(self):
        """Setup table view tab"""
        table_widget = QWidget()
        layout = QVBoxLayout(table_widget)
        
        self.table_view = SearchableTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_view)
        
        self.tab_widget.addTab(table_widget, "Table View")
        self.search_manager.register_widget(1, self.table_view)
        
    def _setup_text_edit_tab(self):
        """Setup text edit tab"""
        text_widget = QWidget()
        layout = QVBoxLayout(text_widget)
        
        self.text_edit = SearchableTextEdit()
        layout.addWidget(self.text_edit)
        
        self.tab_widget.addTab(text_widget, "Text Edit")
        self.search_manager.register_widget(2, self.text_edit)
        
    def _setup_complex_tab(self):
        """Setup complex tab with multiple widgets"""
        complex_widget = QWidget()
        layout = QVBoxLayout(complex_widget)
        
        # Create horizontal layout for tree and table
        top_layout = QHBoxLayout()
        
        # Tree view
        self.complex_tree = SearchableTreeView()
        self.complex_tree.setObjectName("complex_tree")
        top_layout.addWidget(self.complex_tree, 1)
        
        # Table view
        self.complex_table = SearchableTableView()
        self.complex_table.setObjectName("complex_table")
        self.complex_table.setAlternatingRowColors(True)
        top_layout.addWidget(self.complex_table, 1)
        
        layout.addLayout(top_layout)
        
        # Text edit
        self.complex_text = SearchableTextEdit()
        self.complex_text.setObjectName("complex_text")
        layout.addWidget(self.complex_text)
        
        # Status label for complex tab
        self.complex_search_status_label = QLabel("No search performed")
        layout.addWidget(self.complex_search_status_label)
        
        self.tab_widget.addTab(complex_widget, "Complex View")
        
        # Register widgets for complex tab
        self.search_manager.register_widget(3, self.complex_tree)
        self.search_manager.register_widget(3, self.complex_table)
        self.search_manager.register_widget(3, self.complex_text)
        
    def _populate_data(self):
        """Populate all widgets with sample data"""
        self._populate_tree()
        self._populate_table()
        self._populate_text_edit()
        self._populate_complex_tab()
        
    def _populate_tree(self):
        """Populate tree view with sample data"""
        tree_data = {
            "Components": {
                "Bands": {
                    "Band 1": "table",
                    "Band 2": "table",
                    "Band 3": "table",
                },
                "Boards": {
                    "Board 1": "table",
                    "Board 2": "table",
                    "Board 3": "table",
                },
                "RCCs": {
                    "RCC 1": "table",
                    "RCC 2": "table",
                    "RCC 3": "table",
                },
            },
            "Devices": {
                "Input Devices": {
                    "Sensor 1": "input",
                    "Sensor 2": "input",
                    "Button 1": "input",
                },
                "Output Devices": {
                    "LED 1": "output",
                    "Motor 1": "output",
                    "Display 1": "output",
                },
            },
            "Settings": {
                "General": "settings",
                "Advanced": "settings",
                "Network": "settings",
            }
        }
        
        model = TreeModel(tree_data)
        self.tree_view.setModel(model)
        
    def _populate_table(self):
        """Populate table view with sample data"""
        headers = ["Name", "Type", "Status", "Value", "Description"]
        data = [
            ["Device 1", "Input", "Active", "100", "Primary input device"],
            ["Device 2", "Output", "Inactive", "0", "Secondary output device"],
            ["Device 3", "Sensor", "Active", "75", "Temperature sensor"],
            ["Device 4", "Motor", "Active", "50", "Stepper motor"],
            ["Device 5", "LED", "Inactive", "0", "Status indicator"],
            ["Device 6", "Button", "Active", "1", "User input button"],
            ["Device 7", "Display", "Active", "100", "LCD display"],
            ["Device 8", "Relay", "Inactive", "0", "Switching relay"],
        ]
        
        model = TableModel(data, headers)
        self.table_view.setModel(model)
        
    def _populate_text_edit(self):
        """Populate text edit with sample content"""
        content = """
System Configuration Report
==========================

Device Status Summary:
- Total Devices: 8
- Active Devices: 5
- Inactive Devices: 3

Device Details:
1. Device 1 (Input) - Status: Active, Value: 100
   Description: Primary input device for user interaction
   
2. Device 2 (Output) - Status: Inactive, Value: 0
   Description: Secondary output device for system feedback
   
3. Device 3 (Sensor) - Status: Active, Value: 75
   Description: Temperature sensor monitoring system heat
   
4. Device 4 (Motor) - Status: Active, Value: 50
   Description: Stepper motor for mechanical operations
   
5. Device 5 (LED) - Status: Inactive, Value: 0
   Description: Status indicator for system state
   
6. Device 6 (Button) - Status: Active, Value: 1
   Description: User input button for manual control
   
7. Device 7 (Display) - Status: Active, Value: 100
   Description: LCD display for system information
   
8. Device 8 (Relay) - Status: Inactive, Value: 0
   Description: Switching relay for power control

System Performance:
- CPU Usage: 45%
- Memory Usage: 60%
- Network Status: Connected
- Storage Available: 2.5 GB

Configuration Notes:
- All devices are properly configured
- Network settings are optimized
- Security protocols are active
- Backup systems are operational
        """
        
        self.text_edit.setPlainText(content.strip())
        
    def _populate_complex_tab(self):
        """Populate complex tab with sample data"""
        # Tree data
        complex_tree_data = {
            "System Components": {
                "Hardware": {
                    "CPU": "hardware",
                    "Memory": "hardware",
                    "Storage": "hardware",
                },
                "Software": {
                    "OS": "software",
                    "Applications": "software",
                    "Drivers": "software",
                },
            }
        }
        
        tree_model = TreeModel(complex_tree_data)
        self.complex_tree.setModel(tree_model)
        
        # Table data
        table_headers = ["Component", "Type", "Status", "Version"]
        table_data = [
            ["CPU", "Hardware", "Active", "v2.1"],
            ["Memory", "Hardware", "Active", "v1.0"],
            ["Storage", "Hardware", "Active", "v3.2"],
            ["OS", "Software", "Active", "v5.1"],
            ["Applications", "Software", "Active", "v2.3"],
            ["Drivers", "Software", "Active", "v1.8"],
        ]
        
        table_model = TableModel(table_data, table_headers)
        self.complex_table.setModel(table_model)
        
        # Text content
        text_content = """
Complex System Overview
======================

This complex view demonstrates search functionality across multiple widget types:
- TreeView: Hierarchical component structure
- TableView: Tabular component data
- TextEdit: Detailed system information

Search Features:
- Cross-widget navigation
- Highlighted results
- Next/Previous navigation
- Real-time search status

System Architecture:
- Modular design
- Scalable components
- Real-time monitoring
- Automated management
        """
        
        self.complex_text.setPlainText(text_content.strip())
        
    def _setup_search_functionality(self):
        """Setup search functionality"""
        self.search_input.returnPressed.connect(self._perform_search)
        self.search_button.clicked.connect(self._perform_search)
        self.next_button.clicked.connect(self._next_result)
        self.previous_button.clicked.connect(self._previous_result)
        self.clear_button.clicked.connect(self._clear_search)
        
    def _perform_search(self):
        """Perform search across all tabs"""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            self._clear_search()
            return
            
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 3:  # Complex tab
            self._search_in_complex_tab(search_term)
        else:
            # Search in current tab
            widget = self.search_manager.search_widgets.get(current_tab)
            if widget and hasattr(widget, 'search'):
                widget.search(search_term)
                self._update_search_status(widget, search_term)
                
    def _search_in_complex_tab(self, search_term):
        """Search in complex tab across all widgets"""
        total_results = 0
        
        # Search in tree
        self.complex_tree.search(search_term)
        tree_results = len(self.complex_tree.highlighted_items)
        total_results += tree_results
        
        # Search in table
        self.complex_table.search(search_term)
        table_results = len(self.complex_table.highlighted_cells)
        total_results += table_results
        
        # Search in text
        self.complex_text.search(search_term)
        text_results = len(self.complex_text.highlighted_positions)
        total_results += text_results
        
        # Update status
        status_text = f"Found {total_results} results: Tree({tree_results}), Table({table_results}), Text({text_results})"
        self.complex_search_status_label.setText(status_text)
        
        # Initialize navigation to first result
        self._initialize_complex_tab_navigation()
        
    def _initialize_complex_tab_navigation(self):
        """Initialize navigation to first available result in complex tab"""
        first_widget = self._get_first_widget_with_results()
        if first_widget:
            self._highlight_active_complex_widget(first_widget)
            
    def _get_first_widget_with_results(self):
        """Get the first widget that has search results"""
        if self.complex_tree.highlighted_items:
            return self.complex_tree
        elif self.complex_table.highlighted_cells:
            return self.complex_table
        elif self.complex_text.highlighted_positions:
            return self.complex_text
        return None
        
    def _highlight_active_complex_widget(self, widget):
        """Highlight the currently active widget in complex tab"""
        # Remove previous highlighting
        for w in [self.complex_tree, self.complex_table, self.complex_text]:
            w.setStyleSheet("")
            
        # Highlight current widget
        widget.setStyleSheet("border: 2px solid blue;")
        
    def _next_result(self):
        """Move to next search result"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 3:  # Complex tab
            self._next_result_complex_tab()
        else:
            widget = self.search_manager.search_widgets.get(current_tab)
            if widget and hasattr(widget, 'next_search_result'):
                widget.next_search_result()
                self._update_search_status(widget, widget.search_term)
                
    def _previous_result(self):
        """Move to previous search result"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 3:  # Complex tab
            self._previous_result_complex_tab()
        else:
            widget = self.search_manager.search_widgets.get(current_tab)
            if widget and hasattr(widget, 'previous_search_result'):
                widget.previous_search_result()
                self._update_search_status(widget, widget.search_term)
                
    def _next_result_complex_tab(self):
        """Move to next result in complex tab"""
        current_widget = self._get_current_complex_widget_state()
        if not current_widget:
            return
            
        # Check if we're at the last result in current widget
        is_at_last_result = False
        
        if current_widget == self.complex_tree:
            is_at_last_result = (self.complex_tree.current_highlight_index == 
                               len(self.complex_tree.highlighted_items) - 1)
        elif current_widget == self.complex_table:
            is_at_last_result = (self.complex_table.current_highlight_index == 
                               len(self.complex_table.highlighted_cells) - 1)
        elif current_widget == self.complex_text:
            is_at_last_result = (self.complex_text.current_highlight_index == 
                               len(self.complex_text.highlighted_positions) - 1)
                               
        if is_at_last_result:
            # Move to first result in next widget
            next_widget = self._get_next_complex_widget(current_widget)
            if next_widget:
                if hasattr(next_widget, 'current_highlight_index'):
                    next_widget.current_highlight_index = 0
                if hasattr(next_widget, 'next_search_result'):
                    next_widget.next_search_result()
                self._highlight_active_complex_widget(next_widget)
        else:
            # Move to next result within current widget
            if hasattr(current_widget, 'next_search_result'):
                current_widget.next_search_result()
                self._highlight_active_complex_widget(current_widget)
                
    def _previous_result_complex_tab(self):
        """Move to previous result in complex tab"""
        current_widget = self._get_current_complex_widget_state()
        if not current_widget:
            return
            
        # Check if we're at the first result in current widget
        is_at_first_result = False
        
        if current_widget == self.complex_tree:
            is_at_first_result = (self.complex_tree.current_highlight_index == 0)
        elif current_widget == self.complex_table:
            is_at_first_result = (self.complex_table.current_highlight_index == 0)
        elif current_widget == self.complex_text:
            is_at_first_result = (self.complex_text.current_highlight_index == 0)
            
        if is_at_first_result:
            # Move to last result in previous widget
            prev_widget = self._get_previous_complex_widget(current_widget)
            if prev_widget:
                if hasattr(prev_widget, 'current_highlight_index'):
                    if prev_widget == self.complex_tree:
                        prev_widget.current_highlight_index = len(self.complex_tree.highlighted_items) - 1
                    elif prev_widget == self.complex_table:
                        prev_widget.current_highlight_index = len(self.complex_table.highlighted_cells) - 1
                    elif prev_widget == self.complex_text:
                        prev_widget.current_highlight_index = len(self.complex_text.highlighted_positions) - 1
                if hasattr(prev_widget, 'previous_search_result'):
                    prev_widget.previous_search_result()
                self._highlight_active_complex_widget(prev_widget)
        else:
            # Move to previous result within current widget
            if hasattr(current_widget, 'previous_search_result'):
                current_widget.previous_search_result()
                self._highlight_active_complex_widget(current_widget)
                
    def _get_current_complex_widget_state(self):
        """Get the currently active widget in complex tab"""
        if self.complex_tree.current_highlight_index >= 0:
            return self.complex_tree
        elif self.complex_table.current_highlight_index >= 0:
            return self.complex_table
        elif self.complex_text.current_highlight_index >= 0:
            return self.complex_text
        return None
        
    def _get_next_complex_widget(self, current_widget):
        """Get the next widget in complex tab with results"""
        widget_order = ['complex_tree', 'complex_table', 'complex_text']
        current_index = 0
        
        # Find current widget in order
        for i, widget_name in enumerate(widget_order):
            if getattr(self, widget_name) == current_widget:
                current_index = i
                break
                
        # Look for next widget with results
        for offset in range(1, len(widget_order) + 1):
            next_index = (current_index + offset) % len(widget_order)
            next_widget_name = widget_order[next_index]
            next_widget = getattr(self, next_widget_name)
            
            if next_widget_name == 'complex_tree' and next_widget.highlighted_items:
                return next_widget
            elif next_widget_name == 'complex_table' and next_widget.highlighted_cells:
                return next_widget
            elif next_widget_name == 'complex_text' and next_widget.highlighted_positions:
                return next_widget
                
        return None
        
    def _get_previous_complex_widget(self, current_widget):
        """Get the previous widget in complex tab with results"""
        widget_order = ['complex_tree', 'complex_table', 'complex_text']
        current_index = 0
        
        # Find current widget in order
        for i, widget_name in enumerate(widget_order):
            if getattr(self, widget_name) == current_widget:
                current_index = i
                break
                
        # Look for previous widget with results
        for offset in range(1, len(widget_order) + 1):
            prev_index = (current_index - offset) % len(widget_order)
            prev_widget_name = widget_order[prev_index]
            prev_widget = getattr(self, prev_widget_name)
            
            if prev_widget_name == 'complex_tree' and prev_widget.highlighted_items:
                return prev_widget
            elif prev_widget_name == 'complex_table' and prev_widget.highlighted_cells:
                return prev_widget
            elif prev_widget_name == 'complex_text' and prev_widget.highlighted_positions:
                return prev_widget
                
        return None
        
    def _update_search_status(self, widget, search_term):
        """Update search status label"""
        if hasattr(widget, 'highlighted_items'):
            count = len(widget.highlighted_items)
        elif hasattr(widget, 'highlighted_cells'):
            count = len(widget.highlighted_cells)
        elif hasattr(widget, 'highlighted_positions'):
            count = len(widget.highlighted_positions)
        else:
            count = 0
            
        if count > 0:
            current_index = getattr(widget, 'current_highlight_index', 0) + 1
            self.search_status_label.setText(f"Found {count} results for '{search_term}' - {current_index}/{count}")
        else:
            self.search_status_label.setText(f"No results found for '{search_term}'")
            
    def _clear_search(self):
        """Clear all search results"""
        self.search_input.clear()
        self.search_status_label.setText("No search performed")
        self.complex_search_status_label.setText("No search performed")
        
        # Clear search in all widgets
        for widget in self.search_manager.search_widgets.values():
            if hasattr(widget, 'clear_search'):
                widget.clear_search()
                
        # Remove highlighting from complex tab widgets
        for widget in [self.complex_tree, self.complex_table, self.complex_text]:
            widget.setStyleSheet("")


def main():
    """Main function to run the demo"""
    app = QApplication(sys.argv)
    
    window = SearchDemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

