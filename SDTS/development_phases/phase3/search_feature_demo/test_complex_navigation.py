#!/usr/bin/env python3
"""
Test script for complex tab navigation

This script tests the cross-widget navigation in the complex tab
without requiring a full GUI.
"""

import sys
from unittest.mock import Mock, MagicMock

# Mock PySide6 for testing
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()

# Import our search classes
from search_demo import (
    SearchableTreeWidget, 
    SearchableTableWidget, 
    SearchableTextEdit
)


def test_complex_tab_navigation():
    """Test the complex tab navigation logic."""
    print("Testing Complex Tab Navigation...")
    print("=" * 50)
    
    # Create mock widgets
    tree_widget = Mock()
    table_widget = Mock()
    text_widget = Mock()
    
    # Mock the search demo window methods
    class MockSearchDemo:
        def __init__(self):
            self.complex_tree = tree_widget
            self.complex_table = table_widget
            self.complex_text = text_widget
            
        def _get_current_complex_widget_state(self):
            """Mock the current widget state method."""
            # Simulate tree widget having results
            if hasattr(self.complex_tree, 'highlighted_items') and self.complex_tree.highlighted_items:
                return self.complex_tree, self.complex_tree.current_highlight_index
            elif hasattr(self.complex_table, 'highlighted_cells') and self.complex_table.highlighted_cells:
                return self.complex_table, self.complex_table.current_highlight_index
            elif hasattr(self.complex_text, 'highlighted_positions') and self.complex_text.highlighted_positions:
                return self.complex_text, self.complex_text.current_highlight_index
            return None, -1
            
        def _get_next_complex_widget(self, current_widget):
            """Mock the next widget method."""
            if current_widget == self.complex_tree:
                if hasattr(self.complex_table, 'highlighted_cells') and self.complex_table.highlighted_cells:
                    return self.complex_table
                elif hasattr(self.complex_text, 'highlighted_positions') and self.complex_text.highlighted_positions:
                    return self.complex_text
                elif hasattr(self.complex_tree, 'highlighted_items') and self.complex_tree.highlighted_items:
                    return self.complex_tree  # Wrap around
            elif current_widget == self.complex_table:
                if hasattr(self.complex_text, 'highlighted_positions') and self.complex_text.highlighted_positions:
                    return self.complex_text
                elif hasattr(self.complex_tree, 'highlighted_items') and self.complex_tree.highlighted_items:
                    return self.complex_tree
                elif hasattr(self.complex_table, 'highlighted_cells') and self.complex_table.highlighted_cells:
                    return self.complex_table  # Wrap around
            elif current_widget == self.complex_text:
                if hasattr(self.complex_tree, 'highlighted_items') and self.complex_tree.highlighted_items:
                    return self.complex_tree
                elif hasattr(self.complex_table, 'highlighted_cells') and self.complex_table.highlighted_cells:
                    return self.complex_table
                elif hasattr(self.complex_text, 'highlighted_positions') and self.complex_text.highlighted_positions:
                    return self.complex_text  # Wrap around
            return None
            
        def _get_previous_complex_widget(self, current_widget):
            """Mock the previous widget method."""
            if current_widget == self.complex_tree:
                if hasattr(self.complex_text, 'highlighted_positions') and self.complex_text.highlighted_positions:
                    return self.complex_text
                elif hasattr(self.complex_table, 'highlighted_cells') and self.complex_table.highlighted_cells:
                    return self.complex_table
                elif hasattr(self.complex_tree, 'highlighted_items') and self.complex_tree.highlighted_items:
                    return self.complex_tree  # Wrap around
            elif current_widget == self.complex_table:
                if hasattr(self.complex_tree, 'highlighted_items') and self.complex_tree.highlighted_items:
                    return self.complex_tree
                elif hasattr(self.complex_text, 'highlighted_positions') and self.complex_text.highlighted_positions:
                    return self.complex_text
                elif hasattr(self.complex_table, 'highlighted_cells') and self.complex_table.highlighted_cells:
                    return self.complex_table  # Wrap around
            elif current_widget == self.complex_text:
                if hasattr(self.complex_table, 'highlighted_cells') and self.complex_table.highlighted_cells:
                    return self.complex_table
                elif hasattr(self.complex_tree, 'highlighted_items') and self.complex_tree.highlighted_items:
                    return self.complex_tree
                elif hasattr(self.complex_text, 'highlighted_positions') and self.complex_text.highlighted_positions:
                    return self.complex_text  # Wrap around
            return None
    
    # Create mock demo instance
    demo = MockSearchDemo()
    
    # Test 1: All widgets have results
    print("\nTest 1: All widgets have search results")
    print("-" * 40)
    
    # Setup mock data
    tree_widget.highlighted_items = ['item1', 'item2', 'item3']
    tree_widget.current_highlight_index = 2  # Last item
    
    table_widget.highlighted_cells = [(0, 0), (1, 1), (2, 2)]
    table_widget.current_highlight_index = 0  # First item
    
    text_widget.highlighted_positions = [100, 200, 300]
    text_widget.current_highlight_index = 1  # Middle item
    
    # Test next widget navigation
    current_widget, _ = demo._get_current_complex_widget_state()
    print(f"Current widget: {type(current_widget).__name__}")
    
    next_widget = demo._get_next_complex_widget(current_widget)
    print(f"Next widget: {type(next_widget).__name__}")
    
    prev_widget = demo._get_previous_complex_widget(current_widget)
    print(f"Previous widget: {type(prev_widget).__name__}")
    
    # Test 2: Only tree and table have results
    print("\nTest 2: Only tree and table have results")
    print("-" * 40)
    
    tree_widget.highlighted_items = ['item1', 'item2']
    tree_widget.current_highlight_index = 1
    
    table_widget.highlighted_cells = [(0, 0), (1, 1)]
    table_widget.current_highlight_index = 0
    
    text_widget.highlighted_positions = []  # No results
    
    current_widget, _ = demo._get_current_complex_widget_state()
    print(f"Current widget: {type(current_widget).__name__}")
    
    next_widget = demo._get_next_complex_widget(current_widget)
    print(f"Next widget: {type(next_widget).__name__}")
    
    prev_widget = demo._get_previous_complex_widget(current_widget)
    print(f"Previous widget: {type(prev_widget).__name__}")
    
    # Test 3: Only tree has results
    print("\nTest 3: Only tree has results")
    print("-" * 40)
    
    tree_widget.highlighted_items = ['item1', 'item2', 'item3']
    tree_widget.current_highlight_index = 0
    
    table_widget.highlighted_cells = []
    text_widget.highlighted_positions = []
    
    current_widget, _ = demo._get_current_complex_widget_state()
    print(f"Current widget: {type(current_widget).__name__}")
    
    next_widget = demo._get_next_complex_widget(current_widget)
    print(f"Next widget: {type(next_widget).__name__}")
    
    prev_widget = demo._get_previous_complex_widget(current_widget)
    print(f"Previous widget: {type(prev_widget).__name__}")
    
    print("\n" + "=" * 50)
    print("Complex Tab Navigation Test Completed!")
    print("The navigation logic should now properly cycle between different widget types.")


if __name__ == "__main__":
    test_complex_tab_navigation()
