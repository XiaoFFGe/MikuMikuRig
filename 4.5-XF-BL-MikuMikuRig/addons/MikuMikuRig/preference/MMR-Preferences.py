from bpy.props import IntProperty, BoolProperty
import bpy

from addons.MikuMikuRig.config import __addon_name__

class MikuMikuRigPreferences(bpy.types.AddonPreferences):

    bl_idname = __addon_name__

    number: IntProperty(
        name="Int Config",
        default=2,
    )
    # 不使用MMR刚体
    no_mmr_rigidbody: BoolProperty(
        default=False,
        description="不使用MMR刚体"
    )
