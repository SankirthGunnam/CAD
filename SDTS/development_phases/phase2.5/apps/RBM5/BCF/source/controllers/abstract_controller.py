"""
Abstract Controller Base Class for Visual BCF MVC Pattern

This module provides the base AbstractController class that all controllers
in the Visual BCF application should inherit from. It follows the MVC pattern
and provides common functionality and interfaces.
"""

import typing
from abc import ABC, abstractmethod
from PySide6.QtCore import QObject, Signal, QModelIndex
from PySide6.QtCore import QMetaObject


class QObjectABCMeta(type(QObject), type(ABC)):
    """Metaclass that combines QObject and ABC metaclasses."""
    pass


class AbstractController(QObject, ABC, metaclass=QObjectABCMeta):
    """
    Abstract base controller class for MVC pattern implementation.

    All controllers in the Visual BCF application should inherit from this class.
    It provides common signals, properties, and abstract methods that need to be
    implemented by child classes.
    """

    # Signals
    gui_event = Signal(str, object)  # event_name, event_data
    data_changed = Signal(QModelIndex, object)  # index, new_data

    def __init__(self, parent=None):
        """
        Initialize the abstract controller.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._view = None
        self._model = None

    @property
    def view(self):
        """Get the view component."""
        return self._view

    @property
    def model(self):
        """Get the model component."""
        return self._model

    def init_signals(self):
        """
        Initialize and connect signals.
        This method should be called after view and model are set up.
        """
        if self._model:
            # Connect model data changes to controller handler
            if hasattr(self._model, 'dataChanged'):
                self._model.dataChanged.connect(self._on_data_changed)

        # Connect controller signals
        self.data_changed.connect(self._on_data_changed)

    @abstractmethod
    def init_tab(self, revision: int):
        """
        Initialize the tab with specified revision.

        This method should be implemented by child classes to set up
        their specific UI and data structures.

        Args:
            revision (int): The revision number for initialization
        """
        pass

    @abstractmethod
    def set_data(self, widget: str, index: typing.Union[QModelIndex, int], data: typing.Any):
        """
        Set data for a specific widget at given index.

        This method should be implemented by child classes to handle
        setting data in their specific widgets.

        Args:
            widget (str): Widget identifier
            index (Union[QModelIndex, int]): Index to set data at
            data (Any): Data to set
        """
        pass

    def _on_data_changed(self, index: QModelIndex):
        """
        Handle data change events.

        This is called when the model data changes and can be overridden
        by child classes for specific handling.

        Args:
            index (QModelIndex): Index of changed data
        """
        # Default implementation - can be overridden by child classes
        self.gui_event.emit("data_changed", {"index": index})

    def set_view(self, view):
        """Set the view component."""
        self._view = view

    def set_model(self, model):
        """Set the model component."""
        self._model = model

    def get_data(self) -> typing.Dict[str, typing.Any]:
        """
        Get current controller data.

        Returns:
            Dict containing current controller data
        """
        return {
            "controller_type": self.__class__.__name__,
            "model_data": self._model.get_data() if self._model and hasattr(self._model, 'get_data') else None,
            "view_state": self._view.get_state() if self._view and hasattr(self._view, 'get_state') else None
        }

    def refresh(self):
        """
        Refresh the controller data and view.

        This method can be overridden by child classes for specific refresh logic.
        """
        if self._model and hasattr(self._model, 'refresh'):
            self._model.refresh()
        if self._view and hasattr(self._view, 'refresh'):
            self._view.refresh()
