"""RDB Models package"""

# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path

from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import RDBTableModel

__all__ = ["RDBTableModel", "ChipModel", "PinModel"]
