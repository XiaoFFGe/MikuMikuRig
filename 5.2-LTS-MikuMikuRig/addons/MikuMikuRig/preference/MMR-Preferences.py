from bpy.props import *
import bpy
from requests.utils import from_key_val_list

from addons.MikuMikuRig.config import __addon_name__
from common.i18n.i18n import i18n

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
    # 开启MMR形态键
    enable_mmr_shape_key: BoolProperty(
        default=False,
        description="开启MMR形态键"
    )
    # 是否直接操作形态键
    direct_operation_shape_key: BoolProperty(
        default=True,
        description="是否直接操作形态键"
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()

        box.label(text=i18n("IK/FK Preference"), icon='CON_KINEMATIC')

        box.prop(self, "left_ik_fk_preference",
                 text=i18n("Left Arm IK" if self.left_ik_fk_preference else "Left Arm FK"))
        box.prop(self, "right_ik_fk_preference",
                 text=i18n("Right Arm IK" if self.right_ik_fk_preference else "Right Arm FK"))

        box.prop(self, "left_leg_ik_fk_preference",
                 text=i18n("Left Leg IK" if self.left_leg_ik_fk_preference else "Left Leg FK"))
        box.prop(self, "right_leg_ik_fk_preference",
                 text=i18n("Right Leg IK" if self.right_leg_ik_fk_preference else "Right Leg FK"))

        box.label(text=i18n("Follow Settings"), icon='CON_SPLINEIK')
        box.prop(self, "both_eye_follow", text=i18n("Eyes"))
        box.prop(self, "head_follow", text=i18n("Head"))
        box.prop(self, "neck_follow", text=i18n("Neck"))
        box.prop(self, "arm_to_leg_following", text=i18n("Arm to leg"))

        box.label(text=i18n("Other Settings"), icon='BRUSHES_ALL')
        # 不使用MMR刚体
        box.prop(self, "no_mmr_rigidbody", text=i18n("No MMR Rigidbody"))
        # 启用 Legacy 0.56 版本功能
        box.prop(self, "use_legacy_mode", text=i18n("Enable Legacy 0.56 Version"))
        # 开启MMR形态键
        box.prop(self, "enable_mmr_shape_key", text=i18n("Enable MMR Shape Key"))
        # 是否直接操作形态键
        box.prop(self, "direct_operation_shape_key", text=i18n("Direct operation shape key"))

        # 控制器线框宽度
        row = box.row()
        row.prop(self, "controller_wireframe_width", text=i18n("Controller Wireframe Width"))

