import bpy

from MikuMikuRig.addons.MikuMikuRig.operators.MMRpresets import mmrmakepresetsOperator, mmrdesignatedOperator
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import mmdarmoptOperator, mmrexportvmdactionsOperator
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import mmrrigOperator
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import polartargetOperator
from MikuMikuRig.addons.MikuMikuRig.operators.redirect import MMR_redirect, MMR_Import_VMD
from MikuMikuRig.addons.MikuMikuRig.operators.reload import MMR_OT_OpenPresetFolder
from MikuMikuRig.common.i18n.i18n import i18n


class MMD_Rig_Opt(bpy.types.Panel):
    bl_label = "Controller options"
    bl_idname = "SCENE_PT_MMR_Rig_A"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"

    def draw(self, context: bpy.types.Context):

        # 从上往下排列
        layout = self.layout

        mmr = context.object.mmr

        if mmr.make_presets:
            if mmr.Import_presets:
                layout.prop(mmr,"json_filepath",text=i18n('presets'))
            else:
                layout.prop(mmr,"presets",text=i18n('presets'))

            row = layout.row()
            row.operator(mmrmakepresetsOperator.bl_idname, text="make presets")
            row.prop(mmr, "Import_presets", text=i18n("Import presets"), toggle=True)

            # 增加按钮大小并添加图标
            layout.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
            layout.operator(mmrrigOperator.bl_idname, text="Build a controller",icon="OUTLINER_DATA_ARMATURE")

            layout.prop(mmr, "extras_enabled", text=i18n("Extras"), toggle=True,icon="PREFERENCES")

            if mmr.extras_enabled:

                row = layout.row()
                row.prop(mmr, "Bend_the_bones", text=i18n("Bend the arm bones"))
                row.prop(mmr, "Bend_angle_arm", text=i18n("Bend angle"))

                row = layout.row()
                # 弯曲腿部骨骼
                row.prop(mmr, "Bend_the_leg_bones", text=i18n("Bend the leg bones"))
                row.prop(mmr, "Bend_angle_leg", text=i18n("Bend angle"))

                # 使用ITASC解算器
                layout.prop(mmr, "Use_ITASC_solver", text=i18n("Use ITASC solver"))
                # ORG模式
                layout.prop(mmr, "ORG_mode", text=i18n("ORG mode"))

                layout.prop(mmr, "Polar_target", text=i18n("Polar target"))

                layout.prop(mmr, "Shoulder_linkage", text=i18n("Shoulder linkage"))
                if mmr.Shoulder_linkage:
                    layout.label(text=i18n("This option has a serious bug and should not be enabled"), icon='ERROR')

                layout.prop(mmr, "Finger_options", text=i18n("Finger options"))

                if mmr.Finger_options:
                    layout.prop(mmr, "f_pin", text=i18n("Finger tip bone repair"))
                    layout.prop(mmr, "Thumb_twist_aligns_with_the_world_Z_axis", text=i18n("Thumb twist aligns with the world Z-axis"))

                layout.prop(mmr, "Upper_body_linkage", text=i18n("Upper body linkage"))

                # 隐藏骨架
                layout.prop(mmr, "Hide_mmd_skeleton", text=i18n("No Hide skeleton"))

                layout.prop(mmr, "Only_meta_bones_are_generated", text=i18n("Only meta bones are generated"))

                layout.prop(mmr, "Towards_the_dialog_box", text=i18n("Sets the default orientation"))
                layout.prop(mmr, "Reference_bones", text=i18n("Reference bones"))
                layout.prop(mmr, "Preset_editor", text=i18n("MMR Preset Editor"))
        else:
            layout.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
            layout.prop(mmr, "json_txt")
            row = layout.row()
            row.operator(mmrdesignatedOperator.bl_idname, text="designated")
            row.operator(mmrmakepresetsOperator.bl_idname, text="Exit the designation")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

# 骨骼重定向
class MMD_Rig_Opt_Polar(bpy.types.Panel):
    bl_label = "Bone retargeting"
    bl_idname = "SCENE_PT_MMR_Rig_B"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"
    bl_parent_id = "SCENE_PT_MMR_Rig_A"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mmr = context.object.mmr
        layout.prop(mmr, "py_presets", text=i18n('presets'))
        layout.operator(MMR_redirect.bl_idname, icon='OUTLINER_DATA_ARMATURE')
        layout.operator(MMR_Import_VMD.bl_idname, icon='OUTLINER_OB_ARMATURE')
        layout.operator(mmrexportvmdactionsOperator.bl_idname, text="Export VMD actions", icon='ANIM')
        layout.operator(MMR_OT_OpenPresetFolder.bl_idname, icon='FILE_FOLDER')
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

class MMD_Arm_Opt(bpy.types.Panel):
    bl_label = "MMD tool"
    bl_idname = "SCENE_PT_MMR_Rig_C"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"
    bl_parent_id = "SCENE_PT_MMR_Rig_A"

    def draw(self, context: bpy.types.Context):

        mmr = context.object.mmr

        # 从上往下排列
        layout = self.layout

        if mmr.boolean:
            # 增加按钮大小并添加图标
            row = layout.row()
            row.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
            row.operator(polartargetOperator.bl_idname, text="Optimization MMD Armature", icon='BONE_DATA')
            col = layout.column_flow(columns=2)

        else:
            # 增加按钮大小并添加图标
            row = layout.row()
            row.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
            row.operator(mmdarmoptOperator.bl_idname, text="Optimization MMD Armature", icon='BONE_DATA')

        row1 = layout.row()
        row1.prop(mmr, "boolean", text=i18n('Polar target'))

        col = layout.column_flow(columns=2)
        col.scale_y = 1.2

        obj = context.active_object
        if obj:
            # 第五个骨骼和约束组合
            bone_name_1 = "ひじ.L"
            constraint_name_1 = "【IK】L"
            obj = bpy.context.object
            if obj and obj.type == 'ARMATURE':
                bone_1 = obj.pose.bones.get(bone_name_1)
                if bone_1:
                    constraint_1 = bone_1.constraints.get(constraint_name_1)
                    if constraint_1:
                        if mmr.boolean:
                            col.prop(constraint_1, "pole_angle", text="手IK.L(极向角度)")

            # 第二个骨骼和约束组合
            bone_name_2 = "手首.L"
            constraint_name_2 = "【复制旋转】.L"
            if obj and obj.type == 'ARMATURE':
                bone_2 = obj.pose.bones.get(bone_name_2)
                if bone_2:
                    constraint_2 = bone_2.constraints.get(constraint_name_2)
                    if constraint_2:
                        col.prop(constraint_2, "influence",text="手IK.L(旋转)")

            # 第一个骨骼和约束组合
            bone_name_1 = "ひじ.L"
            constraint_name_1 = "【IK】L"
            obj = bpy.context.object
            if obj and obj.type == 'ARMATURE':
                bone_1 = obj.pose.bones.get(bone_name_1)
                if bone_1:
                    constraint_1 = bone_1.constraints.get(constraint_name_1)
                    if constraint_1:
                        col.prop(constraint_1, "influence",text="手IK.L(位置)")

            # 第六个骨骼和约束组合
            bone_name_1 = "ひじ.R"
            constraint_name_1 = "【IK】R"
            obj = bpy.context.object
            if obj and obj.type == 'ARMATURE':
                bone_1 = obj.pose.bones.get(bone_name_1)
                if bone_1:
                    constraint_1 = bone_1.constraints.get(constraint_name_1)
                    if constraint_1:
                        if mmr.boolean:
                            col.prop(constraint_1, "pole_angle", text="手IK.R(极向角度)")

            # 第三个骨骼和约束组合
            bone_name_1 = "ひじ.R"
            constraint_name_1 = "【IK】R"
            obj = bpy.context.object
            if obj and obj.type == 'ARMATURE':
                bone_1 = obj.pose.bones.get(bone_name_1)
                if bone_1:
                    constraint_1 = bone_1.constraints.get(constraint_name_1)
                    if constraint_1:
                        col.prop(constraint_1, "influence", text="手IK.R(位置)")

            # 第四个骨骼和约束组合
            bone_name_2 = "手首.R"
            constraint_name_2 = "【复制旋转】.R"
            if obj and obj.type == 'ARMATURE':
                bone_2 = obj.pose.bones.get(bone_name_2)
                if bone_2:
                    constraint_2 = bone_2.constraints.get(constraint_name_2)
                    if constraint_2:
                        col.prop(constraint_2, "influence", text="手IK.R(旋转)")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

