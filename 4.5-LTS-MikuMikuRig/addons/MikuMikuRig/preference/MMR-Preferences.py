from bpy.props import *
import bpy
from requests.utils import from_key_val_list

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
    # 控制器线框宽度
    controller_wireframe_width: FloatProperty(
        default=1.8,
        description="控制器线框宽度"
    )
    # 左手ik-fk偏好
    left_ik_fk_preference: BoolProperty(
        default=True,
        description="左手ik-fk偏好"
    )
    # 右手ik-fk偏好
    right_ik_fk_preference: BoolProperty(
        default=True,
        description="右手ik-fk偏好"
    )
    # 左腿ik-fk偏好
    left_leg_ik_fk_preference: BoolProperty(
        default=True,
        description="左腿ik-fk偏好"
    )
    # 右腿ik-fk偏好
    right_leg_ik_fk_preference: BoolProperty(
        default=True,
        description="右腿ik-fk偏好"
    )
    # 双眼跟随
    both_eye_follow: BoolProperty(
        default=True,
        description="双眼跟随"
    )
    # 脖子跟随
    neck_follow: BoolProperty(
        default=True,
        description="脖子跟随"
    )
    # 头部跟随
    head_follow: BoolProperty(
        default=True,
        description="头部跟随"
    )
    # 人物四肢跟随
    arm_to_leg_following: BoolProperty(
        default=False,
        description="人物四肢跟随"
    )

