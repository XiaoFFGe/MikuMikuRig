import bpy

from . import preset
from . import rig
from . import retarget
from . import physics
from . import extra


def register():
    """auto_load 分别调用各子模块 register，此处无需递归"""
    pass


def unregister():
    """auto_load 分别调用各子模块 unregister，此处无需递归"""
    pass