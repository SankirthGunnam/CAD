#!/usr/bin/env python3
"""
Search Feature Demo

This demo showcases search functionality across different widget types:
- Tab Widget (with nested widgets)
- Tree Widget
- Table Widget  
- Text Edit Widget

Each widget has its own search implementation that can be triggered
from a unified search bar or individual widget search buttons.
"""

import sys
import random
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QGroupBox,
    QSplitter, QScrollArea, QFrame, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QColor, QPalette, QTextCursor, QTextCharFormat


class SearchHighlighter:
    """Helper class for highlighting search results in text widgets."""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor(255, 255, 0, 100))  # Light yellow
        self.highlight_format.setForeground(QColor(0, 0, 0))
        
    def highlight_text(self, search_text: str):
        """Highlight all occurrences of search text."""
        if not search_text:
            return
            
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        # Clear previous highlights
        self.text_widget.document().setDefaultFont(self.text_widget.font())
        
        # Find and highlight all occurrences
        while not cursor.isNull() and not cursor.atEnd():
            cursor = self.text_widget.document().find(search_text, cursor)
            if not cursor.isNull():
                cursor.mergeCharFormat(self.highlight_format)


class SearchableTreeWidget(QTreeWidget):
    """Tree widget with search functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.current_highlight_index = -1
        self.highlighted_items = []
        
    def search(self, text: str):
        """Search for text in tree items and highlight results."""
        self.search_text = text.lower()
        self.current_highlight_index = -1
        self.highlighted_items = []
        
        if not text:
            self.clear_highlights()
            return
            
        # Find all matching items
        self._find_matching_items(self.invisibleRootItem())
        
        # Highlight first result
        if self.highlighted_items:
            self.current_highlight_index = 0
            self._highlight_current_item()
            
    def _find_matching_items(self, parent_item):
        """Recursively find items matching search text."""
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            
            # Check if item text matches
            if self.search_text in item.text(0).lower():
                self.highlighted_items.append(item)
                
            # Recursively search children
            if item.childCount() > 0:
                self._find_matching_items(item)
                
    def _highlight_current_item(self):
        """Highlight the current search result."""
        if 0 <= self.current_highlight_index < len(self.highlighted_items):
            item = self.highlighted_items[self.current_highlight_index]
            self.setCurrentItem(item)
            self.scrollToItem(item)
            
            # Visual highlight
            item.setBackground(0, QColor(255, 255, 0, 150))
            
    def clear_highlights(self):
        """Clear all search highlights."""
        for item in self.highlighted_items:
            item.setBackground(0, QColor(255, 255, 255, 0))
        self.highlighted_items = []
        self.current_highlight_index = -1
        
    def next_search_result(self):
        """Move to next search result."""
        if not self.highlighted_items:
            return
            
        # Clear previous highlight
        if 0 <= self.current_highlight_index < len(self.highlighted_items):
            self.highlighted_items[self.current_highlight_index].setBackground(0, QColor(255, 255, 0, 150))
            
        self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlighted_items)
        self._highlight_current_item()
        
    def previous_search_result(self):
        """Move to previous search result."""
        if not self.highlighted_items:
            return
            
        # Clear previous highlight
        if 0 <= self.current_highlight_index < len(self.highlighted_items):
            self.highlighted_items[self.current_highlight_index].setBackground(0, QColor(255, 255, 0, 150))
            
        self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlighted_items)
        self._highlight_current_item()


class SearchableTableWidget(QTableWidget):
    """Table widget with search functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.current_highlight_index = -1
        self.highlighted_cells = []
        
    def search(self, text: str):
        """Search for text in table cells and highlight results."""
        self.search_text = text.lower()
        self.current_highlight_index = -1
        self.highlighted_cells = []
        
        if not text:
            self.clear_highlights()
            return
            
        # Find all matching cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and self.search_text in item.text().lower():
                    self.highlighted_cells.append((row, col))
                    
        # Highlight first result
        if self.highlighted_cells:
            self.current_highlight_index = 0
            self._highlight_current_cell()
            
    def _highlight_current_cell(self):
        """Highlight the current search result cell."""
        if 0 <= self.current_highlight_index < len(self.highlighted_cells):
            row, col = self.highlighted_cells[self.current_highlight_index]
            self.setCurrentCell(row, col)
            self.scrollToItem(self.item(row, col))
            
            # Visual highlight
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 0, 150))
                
    def clear_highlights(self):
        """Clear all search highlights."""
        for row, col in self.highlighted_cells:
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 255, 0))
        self.highlighted_cells = []
        self.current_highlight_index = -1
        
    def next_search_result(self):
        """Move to next search result."""
        if not self.highlighted_cells:
            return
            
        # Clear previous highlight
        if 0 <= self.current_highlight_index < len(self.highlighted_cells):
            row, col = self.highlighted_cells[self.current_highlight_index]
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 0, 150))
                
        self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlighted_cells)
        self._highlight_current_cell()
        
    def previous_search_result(self):
        """Move to previous search result."""
        if not self.highlighted_cells:
            return
            
        # Clear previous highlight
        if 0 <= self.current_highlight_index < len(self.highlighted_cells):
            row, col = self.highlighted_cells[self.current_highlight_index]
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 0, 150))
                
        self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlighted_cells)
        self._highlight_current_cell()


class SearchableTextEdit(QTextEdit):
    """Text edit widget with search functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = SearchHighlighter(self)
        self.search_text = ""
        self.current_highlight_index = -1
        self.highlighted_positions = []
        
    def search(self, text: str):
        """Search for text and highlight results."""
        self.search_text = text
        self.current_highlight_index = -1
        self.highlighted_positions = []
        
        if not text:
            self.highlighter.highlight_text("")
            return
            
        # Find all occurrences
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        while not cursor.isNull() and not cursor.atEnd():
            cursor = self.document().find(text, cursor)
            if not cursor.isNull():
                self.highlighted_positions.append(cursor.position())
                
        # Highlight all occurrences
        self.highlighter.highlight_text(text)
        
        # Move to first result
        if self.highlighted_positions:
            self.current_highlight_index = 0
            self._move_to_current_result()
            
    def _move_to_current_result(self):
        """Move cursor to current search result."""
        if 0 <= self.current_highlight_index < len(self.highlighted_positions):
            cursor = self.textCursor()
            cursor.setPosition(self.highlighted_positions[self.current_highlight_index])
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            
    def next_search_result(self):
        """Move to next search result."""
        if not self.highlighted_positions:
            return
            
        self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlighted_positions)
        self._move_to_current_result()
        
    def previous_search_result(self):
        """Move to previous search result."""
        if not self.highlighted_positions:
            return
            
        self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlighted_positions)
        self._move_to_current_result()


class TabSearchManager(QObject):
    """Manages search functionality across all widgets in tabs."""
    
    def __init__(self, tab_widget):
        super().__init__()
        self.tab_widget = tab_widget
        self.searchable_widgets = {}  # tab_index -> widget mapping
        
    def register_widget(self, tab_index: int, widget):
        """Register a searchable widget for a specific tab."""
        self.searchable_widgets[tab_index] = widget
        
    def search_in_current_tab(self, text: str):
        """Search in the currently active tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index in self.searchable_widgets:
            widget = self.searchable_widgets[current_index]
            if hasattr(widget, 'search'):
                widget.search(text)
                
    def search_in_all_tabs(self, text: str):
        """Search in all registered tabs."""
        for tab_index, widget in self.searchable_widgets.items():
            if hasattr(widget, 'search'):
                widget.search(text)
                
    def next_result_in_current_tab(self):
        """Move to next search result in current tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index in self.searchable_widgets:
            widget = self.searchable_widgets[current_index]
            if hasattr(widget, 'next_search_result'):
                widget.next_search_result()
                
    def previous_result_in_current_tab(self):
        """Move to previous search result in current tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index in self.searchable_widgets:
            widget = self.searchable_widgets[current_index]
            if hasattr(widget, 'previous_search_result'):
                widget.previous_search_result()


class SearchDemoWindow(QMainWindow):
    """Main window demonstrating search functionality across different widgets."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Search Feature Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.tab_widget = None
        self.tree_widget = None
        self.table_widget = None
        self.text_edit = None
        self.search_manager = None
        
        # Setup UI
        self._setup_ui()
        self._populate_data()
        self._setup_search_functionality()
        
    def _setup_ui(self):
        """Setup the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Search Feature Demo")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Search controls
        self._setup_search_controls(main_layout)
        
        # Tab widget
        self._setup_tab_widget(main_layout)
        
    def _setup_search_controls(self, parent_layout):
        """Setup the search control panel."""
        search_group = QGroupBox("Search Controls")
        search_layout = QHBoxLayout(search_group)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search text...")
        self.search_input.setMinimumWidth(300)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        # Search scope
        self.search_scope = QComboBox()
        self.search_scope.addItems(["Current Tab", "All Tabs"])
        search_layout.addWidget(QLabel("Scope:"))
        search_layout.addWidget(self.search_scope)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._perform_search)
        search_layout.addWidget(self.search_button)
        
        # Navigation buttons
        self.prev_button = QPushButton("← Previous")
        self.prev_button.clicked.connect(self._previous_result)
        search_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self._next_result)
        search_layout.addWidget(self.next_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_search)
        search_layout.addWidget(self.clear_button)
        
        search_layout.addStretch()
        parent_layout.addWidget(search_group)
        
    def _setup_tab_widget(self, parent_layout):
        """Setup the tab widget with different widget types."""
        self.tab_widget = QTabWidget()
        
        # Tab 1: Tree Widget
        self._setup_tree_tab()
        
        # Tab 2: Table Widget
        self._setup_table_tab()
        
        # Tab 3: Text Edit Widget
        self._setup_text_edit_tab()
        
        # Tab 4: Complex Tab (with nested widgets)
        self._setup_complex_tab()
        
        parent_layout.addWidget(self.tab_widget)
        
    def _setup_tree_tab(self):
        """Setup the tree widget tab."""
        tree_widget = QWidget()
        layout = QVBoxLayout(tree_widget)
        
        # Title
        title = QLabel("Tree Widget Search Demo")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        layout.addWidget(title)
        
        # Tree widget
        self.tree_widget = SearchableTreeWidget()
        self.tree_widget.setHeaderLabel("File System Tree")
        layout.addWidget(self.tree_widget)
        
        self.tab_widget.addTab(tree_widget, "Tree Widget")
        
    def _setup_table_tab(self):
        """Setup the table widget tab."""
        table_widget = QWidget()
        layout = QVBoxLayout(table_widget)
        
        # Title
        title = QLabel("Table Widget Search Demo")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        layout.addWidget(title)
        
        # Table widget
        self.table_widget = SearchableTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Name", "Type", "Status", "Description"])
        layout.addWidget(self.table_widget)
        
        self.tab_widget.addTab(table_widget, "Table Widget")
        
    def _setup_text_edit_tab(self):
        """Setup the text edit widget tab."""
        text_widget = QWidget()
        layout = QVBoxLayout(text_widget)
        
        # Title
        title = QLabel("Text Edit Widget Search Demo")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        layout.addWidget(title)
        
        # Text edit widget
        self.text_edit = SearchableTextEdit()
        self.text_edit.setFont(QFont("Courier", 10))
        layout.addWidget(self.text_edit)
        
        self.tab_widget.addTab(text_widget, "Text Edit Widget")
        
    def _setup_complex_tab(self):
        """Setup a complex tab with multiple widget types."""
        complex_widget = QWidget()
        layout = QVBoxLayout(complex_widget)
        
        # Title
        title = QLabel("Complex Tab - Multiple Widget Types")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e;")
        layout.addWidget(title)
        
        # Splitter for multiple widgets
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Tree widget
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Project Structure:"))
        
        self.complex_tree = SearchableTreeWidget()
        self.complex_tree.setHeaderLabel("Projects")
        left_layout.addWidget(self.complex_tree)
        
        splitter.addWidget(left_widget)
        
        # Right side: Table widget
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Project Details:"))
        
        self.complex_table = SearchableTableWidget()
        self.complex_table.setColumnCount(3)
        self.complex_table.setHorizontalHeaderLabels(["Project", "Language", "Status"])
        right_layout.addWidget(self.complex_table)
        
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        
        # Bottom: Text area
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("Project Description:"))
        
        self.complex_text = SearchableTextEdit()
        self.complex_text.setMaximumHeight(150)
        bottom_layout.addWidget(self.complex_text)
        
        # Search status label
        self.complex_search_status_label = QLabel("Search results will appear here")
        self.complex_search_status_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 5px;")
        self.complex_search_status_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(self.complex_search_status_label)
        
        layout.addWidget(bottom_widget)
        
        self.tab_widget.addTab(complex_widget, "Complex Tab")
        
    def _populate_data(self):
        """Populate all widgets with sample data."""
        self._populate_tree()
        self._populate_table()
        self._populate_text_edit()
        self._populate_complex_tab()
        
    def _populate_tree(self):
        """Populate the tree widget with sample data."""
        # File system structure
        root = QTreeWidgetItem(self.tree_widget, ["Root Directory"])
        
        # Documents
        docs = QTreeWidgetItem(root, ["Documents"])
        QTreeWidgetItem(docs, ["report.pdf"])
        QTreeWidgetItem(docs, ["presentation.pptx"])
        QTreeWidgetItem(docs, ["data.xlsx"])
        
        # Images
        images = QTreeWidgetItem(root, ["Images"])
        QTreeWidgetItem(images, ["photo1.jpg"])
        QTreeWidgetItem(images, ["photo2.png"])
        QTreeWidgetItem(images, ["screenshot.png"])
        
        # Code
        code = QTreeWidgetItem(root, ["Code"])
        python = QTreeWidgetItem(code, ["Python"])
        QTreeWidgetItem(python, ["main.py"])
        QTreeWidgetItem(python, ["utils.py"])
        QTreeWidgetItem(python, ["config.py"])
        
        js = QTreeWidgetItem(code, ["JavaScript"])
        QTreeWidgetItem(js, ["app.js"])
        QTreeWidgetItem(js, ["style.css"])
        QTreeWidgetItem(js, ["index.html"])
        
        self.tree_widget.expandAll()
        
    def _populate_table(self):
        """Populate the table widget with sample data."""
        sample_data = [
            ["Device A", "Sensor", "Active", "Temperature sensor with high accuracy"],
            ["Device B", "Actuator", "Inactive", "Motor controller for robotic arm"],
            ["Device C", "Display", "Active", "LCD screen for user interface"],
            ["Device D", "Processor", "Active", "Main CPU for system control"],
            ["Device E", "Memory", "Active", "RAM module for data storage"],
            ["Device F", "Network", "Inactive", "WiFi module for connectivity"],
            ["Device G", "Storage", "Active", "SSD for persistent storage"],
            ["Device H", "Camera", "Active", "HD camera for image capture"]
        ]
        
        self.table_widget.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                self.table_widget.setItem(row, col, item)
                
        self.table_widget.resizeColumnsToContents()
        
    def _populate_text_edit(self):
        """Populate the text edit widget with sample data."""
        sample_text = """
# Sample Code and Documentation

## Python Example
def search_function(text, data):
    \"\"\"Search for text in data structure.\"\"\"
    results = []
    for item in data:
        if text.lower() in item.lower():
            results.append(item)
    return results

## Configuration Example
[Database]
host = localhost
port = 5432
database = myapp
username = admin
password = secret123

## Log Entries
2024-01-15 10:30:15 INFO: Application started
2024-01-15 10:30:16 DEBUG: Database connection established
2024-01-15 10:30:17 INFO: User authentication successful
2024-01-15 10:30:18 WARN: High memory usage detected
2024-01-15 10:30:19 ERROR: Failed to connect to external service

## Notes
- Remember to backup data regularly
- Check system logs for errors
- Monitor resource usage
- Update dependencies monthly
        """
        self.text_edit.setPlainText(sample_text.strip())
        
    def _populate_complex_tab(self):
        """Populate the complex tab with sample data."""
        # Populate complex tree
        root = QTreeWidgetItem(self.complex_tree, ["Projects"])
        
        web_projects = QTreeWidgetItem(root, ["Web Projects"])
        QTreeWidgetItem(web_projects, ["E-commerce Platform"])
        QTreeWidgetItem(web_projects, ["Blog System"])
        QTreeWidgetItem(web_projects, ["Dashboard"])
        
        mobile_projects = QTreeWidgetItem(root, ["Mobile Apps"])
        QTreeWidgetItem(mobile_projects, ["Fitness Tracker"])
        QTreeWidgetItem(mobile_projects, ["Weather App"])
        QTreeWidgetItem(mobile_projects, ["Task Manager"])
        
        desktop_projects = QTreeWidgetItem(root, ["Desktop Applications"])
        QTreeWidgetItem(desktop_projects, ["Image Editor"])
        QTreeWidgetItem(desktop_projects, ["Text Editor"])
        QTreeWidgetItem(desktop_projects, ["File Manager"])
        
        self.complex_tree.expandAll()
        
        # Populate complex table
        project_data = [
            ["E-commerce Platform", "React/Node.js", "In Development"],
            ["Blog System", "Django/Python", "Completed"],
            ["Dashboard", "Vue.js/Express", "Testing"],
            ["Fitness Tracker", "React Native", "In Development"],
            ["Weather App", "Flutter", "Completed"],
            ["Task Manager", "Swift", "Planning"],
            ["Image Editor", "C++/Qt", "In Development"],
            ["Text Editor", "Python/Tkinter", "Completed"],
            ["File Manager", "Java/Swing", "Testing"]
        ]
        
        self.complex_table.setRowCount(len(project_data))
        for row, data in enumerate(project_data):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                self.complex_table.setItem(row, col, item)
                
        self.complex_table.resizeColumnsToContents()
        
        # Populate complex text
        complex_text_content = """
# Project Management Overview

## Active Projects
- E-commerce Platform: React frontend with Node.js backend
- Fitness Tracker: Cross-platform mobile app using React Native
- Image Editor: Desktop application built with C++ and Qt

## Completed Projects
- Blog System: Django-based content management system
- Weather App: Flutter mobile application with real-time data
- Text Editor: Simple Python-based text editor

## Upcoming Projects
- Task Manager: iOS application using Swift
- File Manager: Java-based desktop file browser

## Development Guidelines
- Use version control for all projects
- Follow coding standards and best practices
- Implement comprehensive testing
- Document all APIs and user interfaces
        """
        self.complex_text.setPlainText(complex_text_content.strip())
        
    def _setup_search_functionality(self):
        """Setup the search functionality."""
        self.search_manager = TabSearchManager(self.tab_widget)
        
        # Register searchable widgets
        self.search_manager.register_widget(0, self.tree_widget)
        self.search_manager.register_widget(1, self.table_widget)
        self.search_manager.register_widget(2, self.text_edit)
        
        # For complex tab, we'll search in all its widgets
        # This is handled specially in the search methods
        
        # Connect search input to search functionality
        self.search_input.returnPressed.connect(self._perform_search)
        
    def _perform_search(self):
        """Perform search based on current scope."""
        search_text = self.search_input.text()
        scope = self.search_scope.currentText()
        
        if scope == "Current Tab":
            self.search_manager.search_in_current_tab(search_text)
        else:  # All Tabs
            self.search_manager.search_in_all_tabs(search_text)
            
        # Special handling for complex tab
        if self.tab_widget.currentIndex() == 3:  # Complex tab
            self._search_in_complex_tab(search_text)
            
    def _search_in_complex_tab(self, text: str):
        """Search in all widgets of the complex tab."""
        if hasattr(self, 'complex_tree'):
            self.complex_tree.search(text)
        if hasattr(self, 'complex_table'):
            self.complex_table.search(text)
        if hasattr(self, 'complex_text'):
            self.complex_text.search(text)
            
        # Update the search status display
        self._update_complex_tab_search_status()
        
        # Initialize navigation to first widget with results
        self._initialize_complex_tab_navigation()
        
    def _initialize_complex_tab_navigation(self):
        """Initialize navigation to the first widget with results."""
        first_widget = self._get_first_widget_with_results()
        if first_widget:
            # Set the first widget as active and highlight first result
            first_widget.current_highlight_index = 0
            if hasattr(first_widget, '_highlight_current_item'):
                first_widget._highlight_current_item()
            elif hasattr(first_widget, '_highlight_current_cell'):
                first_widget._highlight_current_cell()
            elif hasattr(first_widget, '_move_to_current_result'):
                first_widget._move_to_current_result()
            self._highlight_active_complex_widget(first_widget)
        
    def _update_complex_tab_search_status(self):
        """Update the search status display for complex tab."""
        if not hasattr(self, 'complex_search_status_label'):
            return
            
        total_results = 0
        widget_results = {}
        
        if hasattr(self, 'complex_tree') and self.complex_tree.highlighted_items:
            tree_count = len(self.complex_tree.highlighted_items)
            total_results += tree_count
            widget_results['Tree'] = tree_count
            
        if hasattr(self, 'complex_table') and self.complex_table.highlighted_cells:
            table_count = len(self.complex_table.highlighted_cells)
            total_results += table_count
            widget_results['Table'] = table_count
            
        if hasattr(self, 'complex_text') and self.complex_text.highlighted_positions:
            text_count = len(self.complex_text.highlighted_positions)
            total_results += text_count
            widget_results['Text'] = text_count
            
        if total_results > 0:
            status_text = f"Found {total_results} results: "
            status_text += ", ".join([f"{widget}: {count}" for widget, count in widget_results.items()])
            self.complex_search_status_label.setText(status_text)
            self.complex_search_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.complex_search_status_label.setText("No results found")
            self.complex_search_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
    def _next_result(self):
        """Move to next search result."""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 3:  # Complex tab
            self._next_result_complex_tab()
        else:
            self.search_manager.next_result_in_current_tab()
            
    def _previous_result(self):
        """Move to previous search result."""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 3:  # Complex tab
            self._previous_result_complex_tab()
        else:
            self.search_manager.previous_result_in_current_tab()
            
    def _next_result_complex_tab(self):
        """Move to next search result across all widgets in complex tab."""
        # Get current widget and result index
        current_widget, current_index = self._get_current_complex_widget_state()
        
        if current_widget is None:
            return
            
        # Check if we're at the last result in current widget
        is_at_last_result = False
        
        if hasattr(current_widget, 'highlighted_items') and current_widget.highlighted_items:
            is_at_last_result = (current_widget.current_highlight_index >= len(current_widget.highlighted_items) - 1)
        elif hasattr(current_widget, 'highlighted_cells') and current_widget.highlighted_cells:
            is_at_last_result = (current_widget.current_highlight_index >= len(current_widget.highlighted_cells) - 1)
        elif hasattr(current_widget, 'highlighted_positions') and current_widget.highlighted_positions:
            is_at_last_result = (current_widget.current_highlight_index >= len(current_widget.highlighted_positions) - 1)
            
        # If we're at the last result, move to next widget
        if is_at_last_result:
            next_widget = self._get_next_complex_widget(current_widget)
            if next_widget and hasattr(next_widget, 'highlighted_items') and next_widget.highlighted_items:
                # Move to first result in next widget
                next_widget.current_highlight_index = 0
                next_widget._highlight_current_item()
                self._highlight_active_complex_widget(next_widget)
            elif next_widget and hasattr(next_widget, 'highlighted_cells') and next_widget.highlighted_cells:
                # Move to first result in next widget
                next_widget.current_highlight_index = 0
                next_widget._highlight_current_cell()
                self._highlight_active_complex_widget(next_widget)
            elif next_widget and hasattr(next_widget, 'highlighted_positions') and next_widget.highlighted_positions:
                # Move to first result in next widget
                next_widget.current_highlight_index = 0
                next_widget._move_to_current_result()
                self._highlight_active_complex_widget(next_widget)
        else:
            # Move to next result within current widget
            if hasattr(current_widget, 'next_search_result'):
                current_widget.next_search_result()
                self._highlight_active_complex_widget(current_widget)
            
    def _previous_result_complex_tab(self):
        """Move to previous search result across all widgets in complex tab."""
        # Get current widget and result index
        current_widget, current_index = self._get_current_complex_widget_state()
        
        if current_widget is None:
            return
            
        # Check if we're at the first result in current widget
        is_at_first_result = False
        
        if hasattr(current_widget, 'highlighted_items') and current_widget.highlighted_items:
            is_at_first_result = (current_widget.current_highlight_index <= 0)
        elif hasattr(current_widget, 'highlighted_cells') and current_widget.highlighted_cells:
            is_at_first_result = (current_widget.current_highlight_index <= 0)
        elif hasattr(current_widget, 'highlighted_positions') and current_widget.highlighted_positions:
            is_at_first_result = (current_widget.current_highlight_index <= 0)
            
        # If we're at the first result, move to previous widget
        if is_at_first_result:
            prev_widget = self._get_previous_complex_widget(current_widget)
            if prev_widget and hasattr(prev_widget, 'highlighted_items') and prev_widget.highlighted_items:
                # Move to last result in previous widget
                prev_widget.current_highlight_index = len(prev_widget.highlighted_items) - 1
                prev_widget._highlight_current_item()
                self._highlight_active_complex_widget(prev_widget)
            elif prev_widget and hasattr(prev_widget, 'highlighted_cells') and prev_widget.highlighted_cells:
                # Move to last result in previous widget
                prev_widget.current_highlight_index = len(prev_widget.highlighted_cells) - 1
                prev_widget._highlight_current_cell()
                self._highlight_active_complex_widget(prev_widget)
            elif prev_widget and hasattr(prev_widget, 'highlighted_positions') and prev_widget.highlighted_positions:
                # Move to last result in previous widget
                prev_widget.current_highlight_index = len(prev_widget.highlighted_positions) - 1
                prev_widget._move_to_current_result()
                self._highlight_active_complex_widget(prev_widget)
        else:
            # Move to previous result within current widget
            if hasattr(current_widget, 'previous_search_result'):
                current_widget.previous_search_result()
                self._highlight_active_complex_widget(current_widget)
            
    def _get_current_complex_widget_state(self):
        """Get the current active widget and its state in the complex tab."""
        # Check which widget currently has focus or active search results
        if hasattr(self, 'complex_tree') and self.complex_tree.highlighted_items:
            return self.complex_tree, self.complex_tree.current_highlight_index
        elif hasattr(self, 'complex_table') and self.complex_table.highlighted_cells:
            return self.complex_table, self.complex_table.current_highlight_index
        elif hasattr(self, 'complex_text') and self.complex_text.highlighted_positions:
            return self.complex_text, self.complex_text.current_highlight_index
        else:
            # Default to first widget with results
            if hasattr(self, 'complex_tree') and self.complex_tree.highlighted_items:
                return self.complex_tree, 0
            elif hasattr(self, 'complex_table') and self.complex_table.highlighted_cells:
                return self.complex_table, 0
            elif hasattr(self, 'complex_text') and self.complex_text.highlighted_positions:
                return self.complex_text, 0
        return None, -1
        
    def _get_next_complex_widget(self, current_widget):
        """Get the next widget in the complex tab cycle with proper circular navigation."""
        # Define the widget order for circular navigation
        widget_order = ['complex_tree', 'complex_table', 'complex_text']
        
        # Find current widget index
        current_index = -1
        for i, widget_name in enumerate(widget_order):
            if getattr(self, widget_name) == current_widget:
                current_index = i
                break
        
        if current_index == -1:
            return None
            
        # Try to find next widget with results, starting from next position
        for offset in range(1, len(widget_order) + 1):
            next_index = (current_index + offset) % len(widget_order)
            next_widget_name = widget_order[next_index]
            next_widget = getattr(self, next_widget_name)
            
            # Check if next widget has results
            if hasattr(next_widget, 'highlighted_items') and next_widget.highlighted_items:
                return next_widget
            elif hasattr(next_widget, 'highlighted_cells') and next_widget.highlighted_cells:
                return next_widget
            elif hasattr(next_widget, 'highlighted_positions') and next_widget.highlighted_positions:
                return next_widget
                
        # If no other widget has results, return current widget (fallback)
        return current_widget
        
    def _highlight_active_complex_widget(self, active_widget):
        """Highlight the currently active widget in the complex tab."""
        # Reset all widget borders
        if hasattr(self, 'complex_tree'):
            self.complex_tree.setStyleSheet("")
        if hasattr(self, 'complex_table'):
            self.complex_table.setStyleSheet("")
        if hasattr(self, 'complex_text'):
            self.complex_text.setStyleSheet("")
            
        # Highlight the active widget
        if active_widget == self.complex_tree:
            self.complex_tree.setStyleSheet("border: 3px solid #3498db; border-radius: 5px;")
        elif active_widget == self.complex_table:
            self.complex_table.setStyleSheet("border: 3px solid #3498db; border-radius: 5px;")
        elif active_widget == self.complex_text:
            self.complex_text.setStyleSheet("border: 3px solid #3498db; border-radius: 5px;")
        
    def _get_previous_complex_widget(self, current_widget):
        """Get the previous widget in the complex tab cycle with proper circular navigation."""
        # Define the widget order for circular navigation (reverse order for previous)
        widget_order = ['complex_tree', 'complex_table', 'complex_text']
        
        # Find current widget index
        current_index = -1
        for i, widget_name in enumerate(widget_order):
            if getattr(self, widget_name) == current_widget:
                current_index = i
                break
        
        if current_index == -1:
            return None
            
        # Try to find previous widget with results, starting from previous position
        for offset in range(1, len(widget_order) + 1):
            prev_index = (current_index - offset) % len(widget_order)
            prev_widget_name = widget_order[prev_index]
            prev_widget = getattr(self, prev_widget_name)
            
            # Check if previous widget has results
            if hasattr(prev_widget, 'highlighted_items') and prev_widget.highlighted_items:
                return prev_widget
            elif hasattr(prev_widget, 'highlighted_cells') and prev_widget.highlighted_cells:
                return prev_widget
            elif hasattr(prev_widget, 'highlighted_positions') and prev_widget.highlighted_positions:
                return prev_widget
                
        # If no other widget has results, return current widget (fallback)
        return current_widget
        
    def _get_first_widget_with_results(self):
        """Get the first widget that has search results."""
        widget_order = ['complex_tree', 'complex_table', 'complex_text']
        
        for widget_name in widget_order:
            widget = getattr(self, widget_name)
            if hasattr(widget, 'highlighted_items') and widget.highlighted_items:
                return widget
            elif hasattr(widget, 'highlighted_cells') and widget.highlighted_cells:
                return widget
            elif hasattr(widget, 'highlighted_positions') and widget.highlighted_positions:
                return widget
        return None
            
    def _clear_search(self):
        """Clear all search results and highlights."""
        self.search_input.clear()
        
        # Clear highlights in all widgets
        if hasattr(self, 'tree_widget'):
            self.tree_widget.clear_highlights()
        if hasattr(self, 'table_widget'):
            self.table_widget.clear_highlights()
        if hasattr(self, 'text_edit'):
            self.text_edit.search("")
        if hasattr(self, 'complex_tree'):
            self.complex_tree.clear_highlights()
        if hasattr(self, 'complex_table'):
            self.complex_table.clear_highlights()
        if hasattr(self, 'complex_text'):
            self.complex_text.search("")


def main():
    """Main function to run the search demo."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = SearchDemoWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
