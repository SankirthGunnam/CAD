from typing import TYPE_CHECKING
import apps.RBM5.BCF.source.RDB.paths as paths
if TYPE_CHECKING:
    from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager

class AbstractModel:

    @property
    def current_revision(self):
        return self.rdb[paths.CURRENT_REVISION]
    
    def __init__(self, controller=None, rdb:"RDBManager"=None):
        self.controller = controller
        self.rdb = rdb

    def get_attribute(self, attr):
        try:
            return self.__getattribute__(attr)
        except AttributeError:
            return f'Attribute {attr} not found, returning default value.'

    def set_attribute(self, attr, value):
        try:
            self.__setattr__(attr, value)
        except AttributeError:
            return f'Attribute {attr} not found, setting default value.'