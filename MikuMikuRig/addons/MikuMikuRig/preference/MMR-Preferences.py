from bpy.props import IntProperty
from bpy.types import AddonPreferences

from MikuMikuRig.addons.MikuMikuRig.config import __addon_name__


class MikuMikuRigPreferences(AddonPreferences):

    bl_idname = __addon_name__

    number: IntProperty(
        name="Int Config",
        default=2,
    )
