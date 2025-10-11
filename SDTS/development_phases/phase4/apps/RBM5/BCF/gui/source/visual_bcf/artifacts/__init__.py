"""
Artifacts Package - Phase 2.5

This package contains the component artifacts: pins, chips, and connections.
"""

# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path

from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.chip import ComponentWithPins
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire

__all__ = ['ComponentPin', 'ComponentWithPins', 'Wire']
