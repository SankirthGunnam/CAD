#!/usr/bin/env python3
"""
Simple TableModel and TableView Test Script

This script demonstrates the correct usage of TableModel and TableView
to help identify and fix the segfault issue.
"""

import sys
import os
from pathlib import Path

# Set DISPLAY to current system display (usually :0)
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QTableView, 
    QVBoxLayout, 
    QWidget,
    QPushButton,
    QLabel
)
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QTimer

# Add the current project to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager


class SimpleTableModel(QAbstractTableModel):
    """A simple table model for testing purposes"""
    
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or [
            {"device_id": "1", "device_name": "Device 1", "control_type": "MIPI", "module": "Module 1"},
            {"device_id": "2", "device_name": "Device 2", "control_type": "GPIO", "module": "Module 2"},
            {"device_id": "3", "device_name": "Device 3", "control_type": "MIPI", "module": "Module 3"},
        ]
        self._headers = ["Device ID", "Device Name", "Control Type", "Module"]
        
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
                row_data = self._data[row]
                if col == 0:
                    return row_data.get("device_id", "")
                elif col == 1:
                    return row_data.get("device_name", "")
                elif col == 2:
                    return row_data.get("control_type", "")
                elif col == 3:
                    return row_data.get("module", "")
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None


class CustomTableView(QTableView):
    """A custom table view extending QTableView"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomTableView")
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setMinimumHeight(200)
        print("✓ CustomTableView initialized successfully")


class SimpleTableTest(QMainWindow):
    """Main window for testing the table components"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Table Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Simple TableModel and TableView Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Create and setup table model
        print("🧪 Creating SimpleTableModel...")
        try:
            self.model = SimpleTableModel()
            print(f"✓ SimpleTableModel created: {self.model}")
        except Exception as e:
            print(f"❌ Error creating SimpleTableModel: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Create and setup table view
        print("🧪 Creating CustomTableView...")
        try:
            self.table_view = CustomTableView()
            print(f"✓ CustomTableView created: {self.table_view}")
        except Exception as e:
            print(f"❌ Error creating CustomTableView: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Set model on table view
        print("🧪 Setting model on table view...")
        try:
            self.table_view.setModel(self.model)
            print("✓ Model set on table view successfully")
        except Exception as e:
            print(f"❌ Error setting model on table view: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Add table view to layout
        layout.addWidget(self.table_view)
        
        # Add test button
        test_button = QPushButton("Test Table Functionality")
        test_button.clicked.connect(self.test_table_functionality)
        layout.addWidget(test_button)
        
        # Add status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        print("✅ SimpleTableTest window initialized successfully")
    
    def test_table_functionality(self):
        """Test various table functionality"""
        try:
            self.status_label.setText("Testing table functionality...")
            
            # Test model data access
            row_count = self.model.rowCount()
            col_count = self.model.columnCount()
            self.status_label.setText(f"Table has {row_count} rows and {col_count} columns")
            
            # Test getting data from first cell
            if row_count > 0:
                index = self.model.index(0, 0)
                data = self.model.data(index)
                self.status_label.setText(f"First cell data: {data}")
            
            print("✅ Table functionality test completed successfully")
            
        except Exception as e:
            print(f"❌ Error in table functionality test: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error: {e}")


def main():
    print("🚀 Starting Simple Table Test...")
    
    app = QApplication(sys.argv)
    
    try:
        window = SimpleTableTest()
        window.show()
        
        print("✅ Window created and shown successfully")
        print("🎬 Simple Table Test Started!")
        print("==================================================")
        print("• You should see a window with a simple table")
        print("• The table shows device data in rows and columns")
        print("• Try the 'Test Table Functionality' button")
        print("• Check the status label for feedback")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
