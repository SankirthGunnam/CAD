#!/usr/bin/env python3
"""
RDB TableModel Test Script

This script tests the actual TableModel with RDBManager to identify
where the segfault occurs in the real implementation.
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
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

# Add the current project to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import TableModel


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


class RDBTableTest(QMainWindow):
    """Main window for testing the RDB TableModel"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RDB TableModel Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("RDB TableModel Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Create RDBManager
        print("🧪 Creating RDBManager...")
        try:
            self.rdb_manager = RDBManager()
            print(f"✓ RDBManager created: {self.rdb_manager}")
        except Exception as e:
            print(f"❌ Error creating RDBManager: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test table access
        print("🧪 Testing table access...")
        try:
            table_data = self.rdb_manager.get_table("all_devices")
            print(f"✓ Table data retrieved: {len(table_data)} rows")
            if table_data:
                print(f"✓ Sample data: {table_data[0] if table_data else 'Empty'}")
        except Exception as e:
            print(f"❌ Error accessing table: {e}")
            import traceback
            traceback.print_exc()
        
        # Create TableModel
        print("🧪 Creating TableModel...")
        try:
            columns = [
                {"key": "device_id", "title": "Device ID"},
                {"key": "device_name", "title": "Device Name"},
                {"key": "control_type", "title": "Control Type"},
                {"key": "module", "title": "Module"},
            ]
            
            self.table_model = TableModel(
                db=self.rdb_manager,
                table_path="all_devices",
                columns=columns
            )
            print(f"✓ TableModel created: {self.table_model}")
            
            # Test model methods
            row_count = self.table_model.rowCount()
            col_count = self.table_model.columnCount()
            print(f"✓ Model has {row_count} rows and {col_count} columns")
            
        except Exception as e:
            print(f"❌ Error creating TableModel: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Create TableView
        print("🧪 Creating CustomTableView...")
        try:
            self.table_view = CustomTableView()
            print(f"✓ CustomTableView created: {self.table_view}")
        except Exception as e:
            print(f"❌ Error creating CustomTableView: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Set model on table view - THIS IS WHERE THE SEGFAULT MIGHT OCCUR
        print("🧪 Setting model on table view...")
        try:
            self.table_view.setModel(self.table_model)
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
        
        print("✅ RDBTableTest window initialized successfully")
    
    def test_table_functionality(self):
        """Test various table functionality"""
        try:
            self.status_label.setText("Testing table functionality...")
            
            # Test model data access
            row_count = self.table_model.rowCount()
            col_count = self.table_model.columnCount()
            self.status_label.setText(f"Table has {row_count} rows and {col_count} columns")
            
            # Test getting data from first cell
            if row_count > 0:
                index = self.table_model.index(0, 0)
                data = self.table_model.data(index)
                self.status_label.setText(f"First cell data: {data}")
            else:
                self.status_label.setText("Table is empty")
            
            print("✅ Table functionality test completed successfully")
            
        except Exception as e:
            print(f"❌ Error in table functionality test: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error: {e}")


def main():
    print("🚀 Starting RDB TableModel Test...")
    
    app = QApplication(sys.argv)
    
    try:
        window = RDBTableTest()
        window.show()
        
        print("✅ Window created and shown successfully")
        print("🎬 RDB TableModel Test Started!")
        print("==================================================")
        print("• You should see a window with an RDB table")
        print("• The table shows data from the RDBManager")
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
