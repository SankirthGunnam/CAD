#!/usr/bin/env python3
"""
Test script for search functionality

This script tests the search classes without requiring a GUI,
allowing for automated testing of the search logic.
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor

# Import our search classes
from search_demo import (
    SearchableTreeWidget,
    SearchableTableWidget,
    SearchableTextEdit,
    SearchHighlighter,
    TabSearchManager
)


class TestSearchHighlighter(unittest.TestCase):
    """Test the SearchHighlighter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.text_widget = Mock()
        self.text_widget.font.return_value = Mock()
        self.text_widget.textCursor.return_value = Mock()
        self.text_widget.document.return_value = Mock()

        self.highlighter = SearchHighlighter(self.text_widget)

    def test_highlight_text_empty(self):
        """Test highlighting with empty text."""
        self.highlighter.highlight_text("")
        # Should not raise any exceptions

    def test_highlight_format_creation(self):
        """Test that highlight format is created correctly."""
        self.assertIsNotNone(self.highlighter.highlight_format)
        self.assertEqual(self.highlighter.highlight_format.background().color(), QColor(255, 255, 0, 100))


class TestSearchableTreeWidget(unittest.TestCase):
    """Test the SearchableTreeWidget class."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.tree = SearchableTreeWidget()

    def test_initial_state(self):
        """Test initial state of the tree widget."""
        self.assertEqual(self.tree.search_text, "")
        self.assertEqual(self.tree.current_highlight_index, -1)
        self.assertEqual(len(self.tree.highlighted_items), 0)

    def test_search_empty_text(self):
        """Test search with empty text."""
        self.tree.search("")
        self.assertEqual(len(self.tree.highlighted_items), 0)
        self.assertEqual(self.tree.current_highlight_index, -1)

    def test_clear_highlights(self):
        """Test clearing highlights."""
        # Add some mock highlighted items
        mock_item = Mock()
        mock_item.setBackground = Mock()
        self.tree.highlighted_items = [mock_item]
        self.tree.current_highlight_index = 0

        self.tree.clear_highlights()

        self.assertEqual(len(self.tree.highlighted_items), 0)
        self.assertEqual(self.tree.current_highlight_index, -1)
        mock_item.setBackground.assert_called_once()


class TestSearchableTableWidget(unittest.TestCase):
    """Test the SearchableTableWidget class."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.table = SearchableTableWidget()
        self.table.setRowCount(2)
        self.table.setColumnCount(2)

    def test_initial_state(self):
        """Test initial state of the table widget."""
        self.assertEqual(self.table.search_text, "")
        self.assertEqual(self.table.current_highlight_index, -1)
        self.assertEqual(len(self.table.highlighted_cells), 0)

    def test_search_empty_text(self):
        """Test search with empty text."""
        self.table.search("")
        self.assertEqual(len(self.table.highlighted_cells), 0)
        self.assertEqual(self.table.current_highlight_index, -1)

    def test_clear_highlights(self):
        """Test clearing highlights."""
        # Add some mock highlighted cells
        self.table.highlighted_cells = [(0, 0), (1, 1)]
        self.table.current_highlight_index = 0

        # Mock table items
        mock_item = Mock()
        mock_item.setBackground = Mock()
        self.table.item = Mock(return_value=mock_item)

        self.table.clear_highlights()

        self.assertEqual(len(self.table.highlighted_cells), 0)
        self.assertEqual(self.table.current_highlight_index, -1)


class TestSearchableTextEdit(unittest.TestCase):
    """Test the SearchableTextEdit class."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.text_edit = SearchableTextEdit()

    def test_initial_state(self):
        """Test initial state of the text edit widget."""
        self.assertEqual(self.text_edit.search_text, "")
        self.assertEqual(self.text_edit.current_highlight_index, -1)
        self.assertEqual(len(self.text_edit.highlighted_positions), 0)

    def test_search_empty_text(self):
        """Test search with empty text."""
        self.text_edit.search("")
        self.assertEqual(len(self.text_edit.highlighted_positions), 0)
        self.assertEqual(self.text_edit.current_highlight_index, -1)


class TestTabSearchManager(unittest.TestCase):
    """Test the TabSearchManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        self.tab_widget = Mock()
        self.manager = TabSearchManager(self.tab_widget)

    def test_initial_state(self):
        """Test initial state of the search manager."""
        self.assertEqual(self.manager.tab_widget, self.tab_widget)
        self.assertEqual(len(self.manager.searchable_widgets), 0)

    def test_register_widget(self):
        """Test registering a widget."""
        mock_widget = Mock()
        self.manager.register_widget(0, mock_widget)

        self.assertIn(0, self.manager.searchable_widgets)
        self.assertEqual(self.manager.searchable_widgets[0], mock_widget)

    def test_search_in_current_tab(self):
        """Test searching in current tab."""
        mock_widget = Mock()
        mock_widget.search = Mock()
        self.manager.register_widget(0, mock_widget)

        self.tab_widget.currentIndex.return_value = 0
        self.manager.search_in_current_tab("test")

        mock_widget.search.assert_called_once_with("test")

    def test_search_in_all_tabs(self):
        """Test searching in all tabs."""
        mock_widget1 = Mock()
        mock_widget1.search = Mock()
        mock_widget2 = Mock()
        mock_widget2.search = Mock()

        self.manager.register_widget(0, mock_widget1)
        self.manager.register_widget(1, mock_widget2)

        self.manager.search_in_all_tabs("test")

        mock_widget1.search.assert_called_once_with("test")
        mock_widget2.search.assert_called_once_with("test")


def run_tests():
    """Run all tests."""
    print("Running Search Feature Tests...")
    print("=" * 50)

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_classes = [
        TestSearchHighlighter,
        TestSearchableTreeWidget,
        TestSearchableTableWidget,
        TestSearchableTextEdit,
        TestTabSearchManager
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")

    return len(result.failures) + len(result.errors) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
