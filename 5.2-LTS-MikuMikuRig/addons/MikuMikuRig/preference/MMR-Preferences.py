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
        default=True,
        description="人物四肢跟随"
    )
    # 使用 Legacy 版本（William的0.56版本）
    use_legacy_mode: BoolProperty(
        default=False,
        description="启用LaoBro的0.56版本功能"
    )
    # 弯曲IK骨骼
    bent_IK_bone: BoolProperty(
        default=False,
        description="弯曲IK骨骼"
    )
    # 肩膀联动
    auto_shoulder: BoolProperty(
        default=False,
        description="肩膀联动"
    )
    # 极向目标
    pole_target: BoolProperty(
        default=False,
        description="极向目标"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "no_mmr_rigidbody")
        layout.prop(self, "controller_wireframe_width")
        layout.prop(self, "left_ik_fk_preference")
        layout.prop(self, "right_ik_fk_preference")
        layout.prop(self, "left_leg_ik_fk_preference")
        layout.prop(self, "right_leg_ik_fk_preference")
        layout.prop(self, "both_eye_follow")
        layout.prop(self, "neck_follow")
        layout.prop(self, "head_follow")
        layout.prop(self, "arm_to_leg_following")
        layout.prop(self, "use_legacy_mode")

