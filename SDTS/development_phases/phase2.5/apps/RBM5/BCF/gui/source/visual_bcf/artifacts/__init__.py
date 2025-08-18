"""
Artifacts Package - Phase 2.5

This package contains the component artifacts: pins, chips, and connections.
"""

from .pin import ComponentPin
from .chip import ComponentWithPins
from .connection import Wire

__all__ = ['ComponentPin', 'ComponentWithPins', 'Wire']
