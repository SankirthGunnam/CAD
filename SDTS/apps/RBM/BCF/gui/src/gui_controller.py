from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QMessageBox,
    QMainWindow,
    QDockWidget,
    QLabel,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread, QMetaObject
from typing import Dict, Any, Callable, Optional
import threading
from queue import Queue

from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip
from apps.RBM.BCF.gui.src.visual_bcf.scene import RFScene
from apps.RBM.BCF.gui.src.visual_bcf.view import RFView
from apps.RBM.BCF.src.models.chip import ChipModel
from apps.RBM.BCF.src.RCC.core_controller import ToolState
from .visual_bcf.visual_bcf_manager import VisualBCFManager
from .legacy_bcf.legacy_bcf_manager import LegacyBCFManager


class GUIController(QMainWindow):
    """Main controller for RBM GUI that manages both visual and legacy BCF interfaces"""

    # Define GUI Events (blocking)
    EVENT_CREATE = "create"
    EVENT_LOAD = "load"
    EVENT_BUILD = "build"
    EVENT_SAVE = "save"
    EVENT_EXPORT = "export"

    # Define signals
    show_error_signal = Signal(str)
    show_success_signal = Signal(str)
    add_chip_signal = Signal(ChipModel)
    process_blocking_event_signal = Signal(str, dict)
    data_changed = Signal(dict)
    error_occurred = Signal(str)
    build_requested = Signal(dict)  # Signal when build is requested
    configure_requested = Signal(dict)  # Signal when configuration is requested
    export_requested = Signal(dict)  # Signal when export is requested

    def __init__(self, parent: Optional[QWidget] = None, rdb_manager=None):
        super().__init__(parent)
        self.setWindowTitle("RBM GUI Controller")
        self.setMinimumSize(1000, 800)
        
        # Store RDB manager reference
        self.rdb_manager = rdb_manager

        # Create stacked widget as central widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create and add both managers
        self.legacy_manager = LegacyBCFManager()
        # Pass RDB manager to Visual BCF Manager to enable MVC architecture
        self.visual_manager = VisualBCFManager(parent_controller=self, rdb_manager=self.rdb_manager)

        self.stacked_widget.addWidget(self.legacy_manager)
        self.stacked_widget.addWidget(self.visual_manager)

        # Set initial mode
        self.current_mode = "legacy"
        self.stacked_widget.setCurrentWidget(self.legacy_manager)

        # Create proper toolbar
        self.create_toolbar()

        # Create dock widgets
        self.setup_dock_widgets()

        # Connect signals
        self.legacy_manager.data_changed.connect(self._on_data_changed)
        self.visual_manager.data_changed.connect(self._on_data_changed)
        # NEW: Connect Visual BCF data changes to refresh Legacy BCF table 
        self.visual_manager.data_changed.connect(self.on_visual_data_changed_refresh_table)
        self.legacy_manager.error_occurred.connect(self._on_error)
        self.visual_manager.error_occurred.connect(self._on_error)

        # Event handling
        self.gui_event_callbacks: Dict[str, Callable] = {}  # For GUI events
        self.non_gui_event_callbacks: Dict[str, Callable] = {}  # For non-GUI events
        self.blocking_events: Dict[str, bool] = {
            self.EVENT_CREATE: True,
            self.EVENT_LOAD: True,
            self.EVENT_BUILD: True,
            self.EVENT_SAVE: True,
            self.EVENT_EXPORT: False,
        }
        self.event_queue = Queue()
        self.event_thread = None

        # Start event processing thread
        self.start_event_processor()

        # Register event callbacks
        self.register_gui_event(self.EVENT_CREATE, self.add_chip)

    def register_gui_event(self, event_name: str, callback: Callable):
        """Register a callback for a GUI event (blocking)"""
        self.gui_event_callbacks[event_name] = callback

    def register_non_gui_event(self, event_name: str, callback: Callable):
        """Register a callback for a non-GUI event (non-blocking)"""
        self.non_gui_event_callbacks[event_name] = callback

    def start_event_processor(self):
        """Start the event processing thread"""
        self.event_thread = threading.Thread(target=self._process_events, daemon=True)
        self.event_thread.start()

    def _process_events(self):
        """Process events from the queue"""
        while True:
            event = self.event_queue.get()
            event_name, data, is_blocking = event

            if is_blocking:
                # GUI events must be processed in main thread
                self.process_blocking_event_signal.emit(event_name, data)
            else:
                # Non-GUI events can be processed in worker thread
                if event_name in self.non_gui_event_callbacks:
                    self.non_gui_event_callbacks[event_name](data)
                else:
                    print(
                        f"Warning: No handler registered for non-GUI event: {event_name}"
                    )

    def _process_blocking_event(self, event_name: str, data: Dict[str, Any]):
        """Process a GUI event in the main thread"""
        try:
            if event_name in self.gui_event_callbacks:
                func = self.gui_event_callbacks[event_name]
                reply = func(data)
                self.handle_reply(event_name, reply)
            else:
                print(f"Warning: No handler registered for GUI event: {event_name}")
        except Exception as e:
            self.show_error(f"Error processing {event_name}: {str(e)}")

    def handle_reply(self, event_name: str, reply: Dict[str, Any]):
        """Handle replies from event processing"""
        if reply.get("status") == "success":
            self.show_success(f"{event_name} completed successfully")
        else:
            self.show_error(
                f"{event_name} failed: {reply.get('message', 'Unknown error')}"
            )

    def send_event(self, event_name: str, data: Dict[str, Any] = None):
        """Send an event to be processed"""
        if data is None:
            data = {}

        print("send event called")
        is_blocking = self.blocking_events.get(event_name, False)
        self.event_queue.put((event_name, data, is_blocking))

    def create_toolbar(self):
        """Create the main toolbar with mode switch and other actions"""
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        # Mode switch action
        self.mode_action = QAction("Switch to Visual Mode", self)
        self.mode_action.setCheckable(True)
        self.mode_action.triggered.connect(self._on_mode_toggle)
        self.toolbar.addAction(self.mode_action)

        # Add other actions
        actions = [
            ("Create", self._on_create),
            ("Load", self._on_load),
            ("Build", self._on_build),
            ("Save", self._on_save),
            ("Export", self._on_export),
        ]

        for name, callback in actions:
            action = QAction(name, self)
            action.triggered.connect(callback)
            self.toolbar.addAction(action)

    def show_error(self, message: str):
        """Show error message"""
        print(message)
        self.show_error_signal.emit(message)

    def _show_error_message(self, message: str):
        """Show error message in the main thread"""
        QMessageBox.critical(self, "Error", message)

    def show_success(self, message: str):
        """Show success message"""
        self.show_success_signal.emit(message)

    def _show_success_message(self, message: str):
        """Show success message in the main thread"""
        QMessageBox.information(self, "Success", message)

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the GUI controller"""
        return {
            "status": "running",
            "event_queue_size": self.event_queue.qsize(),
            "active_threads": threading.active_count(),
        }

    def recover(self):
        """Recover from error state"""
        # Clear event queue
        while not self.event_queue.empty():
            self.event_queue.get()

        # Restart event processor if needed
        if not self.event_thread or not self.event_thread.is_alive():
            self.start_event_processor()

    def add_chip(self, *args, **kwargs):
        print("add chip called", args, kwargs)
        """Add a new chip to the scene and database"""
        # Check if we can start building
        if self.core_controller.current_state != ToolState.IDLE:
            error_msg = f"Cannot add chip: Core controller is in {self.core_controller.current_state.name} state"
            print(error_msg)
            self.show_error(error_msg)
            return

        try:
            # Create the chip model in the current thread
            chip_model = ChipModel(name="Sample Chip", width=100, height=100)
            chip_model.add_pin(0, 50, "Input")
            chip_model.add_pin(100, 50, "Output")

            # Add to database
            # self.rdb_manager.add_chip(chip_model)

            # Emit signal to add chip to scene in main thread
            self.add_chip_signal.emit(chip_model)

            return {"status": "success", "message": "Chip added successfully"}

        except Exception as e:
            error_msg = f"Error adding chip: {e}"
            self.core_controller._set_error(str(e))
            print(error_msg)
            return {"status": "error", "message": error_msg}

    def _add_chip_to_scene(self, chip_model: ChipModel):
        """Add a chip widget to the scene in the main thread"""
        try:
            chip_widget = Chip(chip_model)
            self.scene.add_component(chip_widget)
        except Exception as e:
            print(f"Error adding chip widget: {e}")
            self.show_error_signal.emit(f"Error adding chip widget: {e}")

    def _on_mode_toggle(self, checked: bool):
        """Handle mode toggle button click"""
        try:
            if checked:
                self.current_mode = "visual"
                self.mode_action.setText("Switch to Legacy Mode")
                self.stacked_widget.setCurrentWidget(self.visual_manager)
                self.legacy_properties_dock.hide()
                self.visual_properties_dock.show()
                # Show RF toolbar only in visual mode
                self.visual_manager.show_rf_toolbar()
            else:
                self.current_mode = "legacy"
                self.mode_action.setText("Switch to Visual Mode")
                self.stacked_widget.setCurrentWidget(self.legacy_manager)
                self.visual_properties_dock.hide()
                self.legacy_properties_dock.show()
                # Hide RF toolbar when switching to legacy mode
                self.visual_manager.hide_rf_toolbar()
        except Exception as e:
            self.error_occurred.emit(f"Error switching modes: {str(e)}")
    

    def _on_data_changed(self, data: dict):
        """Handle data changes from either manager"""
        try:
            # To avoid recursion, only emit the signal without cross-updating managers
            # The managers should handle their own data consistency
            self.data_changed.emit(data)
            
            # Log the data change for debugging
            source = data.get('source', 'unknown')
            action = data.get('action', 'unknown')
            print(f"Data changed - Source: {source}, Action: {action}")
            
        except Exception as e:
            print(f"Error handling data change: {str(e)}")

    def _on_error(self, message: str):
        """Handle errors from either manager"""
        QMessageBox.critical(self, "Error", message)
        self.error_occurred.emit(message)
    
    def on_visual_data_changed_refresh_table(self, data: dict):
        """Refresh Legacy BCF device table when Visual BCF data changes (especially deletions)"""
        try:
            action = data.get('action', '')
            source = data.get('source', '')
            message = data.get('message', '')
            
            print(f"📊 Visual BCF data changed - Action: '{action}', Source: '{source}', Message: '{message}'")
            
            # Only handle specific Visual BCF actions that affect Legacy BCF
            if source in ['mvc', 'bidirectional_sync'] and action in [
                'user_deletion_synced', 'user_deletion_visual_only', 'delete_components',
                'remove_component', 'add_component', 'import_legacy', 'paste_components', 'paste'
            ]:
                print(f"🎯 Triggering Legacy BCF table refresh for action: {action}")
                
                # Refresh Legacy BCF table to reflect the changes
                if hasattr(self.legacy_manager, 'refresh_device_table'):
                    self.legacy_manager.refresh_device_table()
                    print(f"✅ Called legacy_manager.refresh_device_table()")
                elif hasattr(self.legacy_manager, 'update_table'):
                    # Trigger a table update with the Visual BCF data
                    self.legacy_manager.update_table(data)
                    print(f"✅ Called legacy_manager.update_table()")
                else:
                    print(f"❌ No refresh method found in legacy_manager")
                
                # Log the refresh action
                component_name = data.get('component_name', 'Unknown')
                print(f"🔄 Refreshed Legacy BCF table due to Visual BCF {action} of '{component_name}'")
            else:
                print(f"⏭️ Skipping refresh - Source: '{source}', Action: '{action}' not in handled actions")
                
        except Exception as e:
            print(f"❌ Error refreshing Legacy BCF table: {str(e)}")
            self.error_occurred.emit(f"Failed to refresh Legacy BCF table: {str(e)}")

    def update_data(self, data: dict):
        """Update both managers with new data"""
        try:
            self.legacy_manager.update_table(data)
            self.visual_manager.update_scene(data)
        except Exception as e:
            self.error_occurred.emit(f"Error updating data: {str(e)}")
    
    def update_state(self, state):
        """Update the GUI based on the current state"""
        try:
            # Update window title to show current state
            self.setWindowTitle(f"RBM GUI Controller - {state.name}")
            
            # Enable/disable actions based on state
            if hasattr(state, 'name'):
                state_name = state.name
                if state_name == "ERROR":
                    # Disable most actions in error state
                    for action in self.toolbar.actions():
                        if action.text() not in ["Switch to Visual Mode", "Switch to Legacy Mode"]:
                            action.setEnabled(False)
                elif state_name == "IDLE":
                    # Enable all actions in idle state
                    for action in self.toolbar.actions():
                        action.setEnabled(True)
                else:
                    # Disable some actions during processing
                    for action in self.toolbar.actions():
                        if action.text() in ["Build", "Export"]:
                            action.setEnabled(False)
                        else:
                            action.setEnabled(True)
        except Exception as e:
            print(f"Error updating state: {str(e)}")

    def setup_dock_widgets(self):
        """Setup dock widgets for both modes"""
        # Legacy mode docks
        self.legacy_properties_dock = QDockWidget("Properties", self)
        # self.legacy_properties_dock.setWidget(self.legacy_manager.control_dock.widget())
        self.addDockWidget(Qt.RightDockWidgetArea, self.legacy_properties_dock)

        # Visual mode docks
        self.visual_properties_dock = QDockWidget("Properties", self)
        # self.visual_properties_dock.setWidget(self.visual_manager.control_dock.widget())
        self.visual_properties_dock.hide()  # Initially hidden

        # Add visual docks
        self.addDockWidget(Qt.RightDockWidgetArea, self.visual_properties_dock)

    def showEvent(self, event):
        """Connect to database when window is shown"""
        super().showEvent(event)
        # Add any initialization code here

    def closeEvent(self, event):
        """Clean up when window is closed"""
        # Call cleanup on both managers
        if hasattr(self, 'legacy_manager'):
            self.legacy_manager.cleanup()
        if hasattr(self, 'visual_manager'):
            self.visual_manager.cleanup()
        super().closeEvent(event)
    
    def switch_mode(self, mode: str):
        """Switch between legacy and visual modes"""
        try:
            if mode == "visual":
                self.current_mode = "visual"
                self.mode_action.setText("Switch to Legacy Mode")
                self.mode_action.setChecked(True)
                self.stacked_widget.setCurrentWidget(self.visual_manager)
                if hasattr(self, 'legacy_properties_dock'):
                    self.legacy_properties_dock.hide()
                if hasattr(self, 'visual_properties_dock'):
                    self.visual_properties_dock.show()
                # Show RF toolbar only in visual mode
                self.visual_manager.show_rf_toolbar()
            elif mode == "legacy":
                self.current_mode = "legacy"
                self.mode_action.setText("Switch to Visual Mode")
                self.mode_action.setChecked(False)
                self.stacked_widget.setCurrentWidget(self.legacy_manager)
                if hasattr(self, 'visual_properties_dock'):
                    self.visual_properties_dock.hide()
                if hasattr(self, 'legacy_properties_dock'):
                    self.legacy_properties_dock.show()
                # Hide RF toolbar when switching to legacy mode
                self.visual_manager.hide_rf_toolbar()
        except Exception as e:
            self.error_occurred.emit(f"Error switching modes: {str(e)}")

    # Action handlers
    def _on_create(self):
        """Handle create action"""
        self.send_event(self.EVENT_CREATE, {})

    def _on_load(self):
        """Handle load action"""
        self.send_event(self.EVENT_LOAD, {})

    def _on_build(self):
        """Handle build action"""
        self.build_requested.emit({"mode": self.current_mode})

    def _on_save(self):
        """Handle save action"""
        self.send_event(self.EVENT_SAVE, {})

    def _on_export(self):
        """Handle export action"""
        self.export_requested.emit({"mode": self.current_mode})
    
    def show_status(self, message: str):
        """Show status message"""
        print(f"Status: {message}")
        # Could also use a status bar if we had one
    
    def show_warning(self, message: str):
        """Show warning message"""
        print(f"Warning: {message}")
        QMessageBox.warning(self, "Warning", message)
    
    def add_generated_file(self, file_path: str):
        """Add a generated file to the list"""
        print(f"Generated file: {file_path}")
        # Could update a file list widget if we had one
    
    def refresh_data(self):
        """Refresh data in both managers"""
        try:
            if hasattr(self.legacy_manager, 'refresh'):
                self.legacy_manager.refresh()
            if hasattr(self.visual_manager, 'refresh'):
                self.visual_manager.refresh()
        except Exception as e:
            print(f"Error refreshing data: {e}")
