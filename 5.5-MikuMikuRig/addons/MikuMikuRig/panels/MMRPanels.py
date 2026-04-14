import bpy
from numpy.f2py.capi_maps import depargs

from addons.MikuMikuRig.operators.MMRpresets import mmrmakepresetsOperator, mmrdesignatedOperator, MMR_OT_ImportPresets, \
    MMR_OT_Designated
from addons.MikuMikuRig.operators.Physics import Add_Damping_Tracking, Remove_Damping_Tracking, Assign_Rigidbody, \
    Show_Rigidbody, Select_Collision_Group, Update_World, Select_By_Type, \
    mmdrigidbody_to_mmrrigidbody, Remove_physics, Show_Joint, Select_Collision_Group_For_Joint, Select_By_Type_For_Joint
from addons.MikuMikuRig.operators.RIG import mmrexportvmdactionsOperator, MahyPdtOperator, \
    MMR_OT_Batch_Adjust_Shape_Key, MMR_OT_Insert_Keyframe, MMR_OT_Unselect_All_Key, \
    MMR_OT_Select_All_Key, MMR_OT_Select_Keyframe_Key, MMR_OT_Weight_Bone_Parent_Add, MMR_OT_Weight_Bone_Parent_Del, \
    MMR_OT_Import_Default_Weight_Bone_Parent, MMR_OT_Import_Default_Automatic_IK_Bone_Chain, \
    MMR_OT_Add_Automatic_IK_Bone_Chain, MMR_OT_Remove_Automatic_IK_Bone_Chain, \
    MMR_OT_Add_Automatic_IK_Bone_Chain_Separator, MMR_OT_Designated_Bone_Chain
from addons.MikuMikuRig.operators.RIG import mmrrigOperator
from addons.MikuMikuRig.operators.RIG import polartargetOperator
from addons.MikuMikuRig.operators.mmd_rig_physics import MMD_RIG_PHYSICS_BUILD
from addons.MikuMikuRig.operators.redirect import MMR_redirect, MMR_Import_VMD
from addons.MikuMikuRig.operators.reload import MMR_OT_OpenPresetFolder
from common.i18n.i18n import i18n
from ....common.types.framework import reg_order
from addons.MikuMikuRig.config import __addon_name__

# UL类
class MMR_UL_key(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        obj = context.active_object

        if item.bool_value:
            layout.prop(item, "select", text="")
        layout.label(text=item.name)
        if item.bool_value:
            if not obj.mmr.direct_operation_shape_key:
                layout.prop(item, "value", text="")
            else:
                meshkey = item.meshkey
                if meshkey:
                    layout.prop(meshkey.key_blocks[item.meshkey_index], "value", text="")

class MMR_UL_weight_bone_parent_fix(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        row = layout.row(align=True)

        # 左侧键输入
        row.prop(item, "key", text="", emboss=True)

        # 箭头分隔符
        row2 = layout.row(align=True)
        row2.label(text="",icon='FORWARD')

        # 右侧值输入
        row1 = layout.row(align=True)
        row1.prop(item, "value", text="", emboss=True)

class MMR_UL_automatic_ik_bone_chain(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        row = layout.row(align=True)
        if item.separator:
            row.label(text=item.name)
        else:
            row.label(text="", icon='SORT_ASC')
            row.prop(item, "name", text="", emboss=True)


class MMR_key_Options(bpy.types.Panel):

    bl_label = "MMR Key Options"
    bl_idname = "SCENE_PT_MMR_Key_Options_0"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "Tool"

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        obj = context.active_object

        layout.prop(obj.mmr, "key_obj", text="Mesh")

        if obj.mmr:
            # UL
            layout.template_list("MMR_UL_key", "", obj, "mmr_key", obj.mmr, "key_idx")

            row = layout.row()
            row.operator(MMR_OT_Batch_Adjust_Shape_Key.bl_idname, icon="MODIFIER", text="",depress=False if obj.mmr.register_handler else True)
            row.prop(obj.mmr, "insert_keyframe", text='',icon='ZOOM_ALL')
            row.operator(MMR_OT_Unselect_All_Key.bl_idname, icon="CANCEL", text="")
            row.operator(MMR_OT_Select_All_Key.bl_idname, icon="CHECKBOX_HLT", text="")
            row.operator(MMR_OT_Select_Keyframe_Key.bl_idname, icon="AUTOMERGE_ON", text="")

            row = layout.row()
            row.prop(obj.mmr, "Batch_adjust_shape_key", text=i18n('Batch Adjustment'))
            row.operator(MMR_OT_Insert_Keyframe.bl_idname, icon="LAYER_ACTIVE", text="")
            row.prop(obj.mmr, "use_keyframe_insert_auto", text='',icon='KEYFRAME')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

# IK-FK
class IK_FK_fxer(bpy.types.Panel):
    bl_label = "MMR IK-FK"
    bl_idname = "Q_PT_MMR_IK_FK_0"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "Item"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        # 检查是否有活动对象
        if context.active_object is not None:
            # 检查type是否为ARMATURE
            if context.active_object.type == 'ARMATURE':
                # 检查名称是否以"RIG"开头
                if context.active_object.name.startswith("RIG"):
                    return True
        return False

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        cx_obj = context.active_object

        if cx_obj.pose.bones.get("upper_arm_parent.L") and cx_obj.pose.bones.get("upper_arm_parent.R"):
            row = layout.row()

        for bone in cx_obj.pose.bones:
            if bone.name == "upper_arm_parent.L":
                row.prop(bone, '["IK_FK"]', text=i18n('Arm.L'))

        for bone in cx_obj.pose.bones:
            if bone.name == "upper_arm_parent.R":
                row.prop(bone, '["IK_FK"]', text=i18n('Arm.R'))

        if cx_obj.pose.bones.get("thigh_parent.L") and cx_obj.pose.bones.get("thigh_parent.R"):
            row = layout.row()

        for bone in cx_obj.pose.bones:
            if bone.name == "thigh_parent.L":
                row.prop(bone, '["IK_FK"]', text=i18n('Leg.L'))

        for bone in cx_obj.pose.bones:
            if bone.name == "thigh_parent.R":
                row.prop(bone, '["IK_FK"]', text=i18n('Leg.R'))

# 手指 FK-IK
class Finger_IK_FK_fxer(bpy.types.Panel):
    bl_label = "MMR Finger FK-IK"
    bl_idname = "Q_PT_MMR_Finger_FK_IK_0"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "Item"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        # 检查是否有活动对象
        if context.active_object is not None:
            # 检查type是否为ARMATURE
            if context.active_object.type == 'ARMATURE':
                # 检查名称是否以"RIG"开头
                if context.active_object.name.startswith("RIG"):
                    if bpy.context.active_pose_bone is not None:
                        if bpy.context.active_pose_bone.name.startswith("f_"):
                            return True
                        if bpy.context.active_pose_bone.name.startswith("thumb"):
                            return True
        return False

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        cx_obj = context.active_object

        if cx_obj.pose.bones.get("thumb.01_ik.L") and cx_obj.pose.bones.get("thumb.01_ik.R"):
            layout.row()
            row = layout.row()

        for bone in cx_obj.pose.bones:
            if bone.name == "thumb.01_ik.L":
                row.prop(bone, '["FK_IK"]', text=i18n('thumb')+'.L')

        for bone in cx_obj.pose.bones:
            if bone.name == "thumb.01_ik.R":
                row.prop(bone, '["FK_IK"]', text=i18n('thumb')+'.R')

        if cx_obj.pose.bones.get("f_index.01_ik.L") and cx_obj.pose.bones.get("f_index.01_ik.R"):
            row = layout.row()

        for bone in cx_obj.pose.bones:
            if bone.name == "f_index.01_ik.L":
                row.prop(bone, '["FK_IK"]', text=i18n('index')+'.L')

        for bone in cx_obj.pose.bones:
            if bone.name == "f_index.01_ik.R":
                row.prop(bone, '["FK_IK"]', text=i18n('index')+'.R')

        if cx_obj.pose.bones.get("f_middle.01_ik.L") and cx_obj.pose.bones.get("f_middle.01_ik.R"):
            row = layout.row()

        for bone in cx_obj.pose.bones:
            if bone.name == "f_middle.01_ik.L":
                row.prop(bone, '["FK_IK"]', text=i18n('middle')+'.L')

        for bone in cx_obj.pose.bones:
            if bone.name == "f_middle.01_ik.R":
                row.prop(bone, '["FK_IK"]', text=i18n('middle')+'.R')

        if cx_obj.pose.bones.get("f_ring.01_ik.L") and cx_obj.pose.bones.get("f_ring.01_ik.R"):
            row = layout.row()

        for bone in cx_obj.pose.bones:
            if bone.name == "f_ring.01_ik.L":
                row.prop(bone, '["FK_IK"]', text=i18n('ring')+'.L')

        for bone in cx_obj.pose.bones:
            if bone.name == "f_ring.01_ik.R":
                row.prop(bone, '["FK_IK"]', text=i18n('ring')+'.R')

        if cx_obj.pose.bones.get("f_pinky.01_ik.L") and cx_obj.pose.bones.get("f_pinky.01_ik.R"):
            row = layout.row()

        for bone in cx_obj.pose.bones:
            if bone.name == "f_pinky.01_ik.L":
                row.prop(bone, '["FK_IK"]', text=i18n('pinky')+'.L')

        for bone in cx_obj.pose.bones:
            if bone.name == "f_pinky.01_ik.R":
                row.prop(bone, '["FK_IK"]', text=i18n('pinky')+'.R')



# 控制器选项面板
@reg_order(0)
class MMD_Rig_Opt(bpy.types.Panel):
    bl_label = "Controller options"
    bl_idname = "SCENE_PT_MMR_Rig_0"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"

    def draw(self, context: bpy.types.Context):

        prefs = context.preferences.addons[__addon_name__].preferences

        # 从上往下排列
        layout = self.layout

        if context.active_object is not None:
            mmr = context.object.mmr

            if mmr.make_presets:
                if mmr.Import_presets:
                    layout.prop(mmr,"json_filepath",text=i18n('presets'))
                else:
                    layout.prop(mmr,"presets",text=i18n('presets'))

                row = layout.row()
                row.operator(mmrmakepresetsOperator.bl_idname, text="make presets")
                row.operator(MMR_OT_ImportPresets.bl_idname, text=i18n('Import presets') if not mmr.Import_presets else i18n('return'), depress=mmr.Import_presets)

                # 增加按钮大小并添加图标
                layout.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
                layout.operator(mmrrigOperator.bl_idname, text="Build a controller",icon="OUTLINER_DATA_ARMATURE")

                layout.operator(MahyPdtOperator.bl_idname, icon="MODIFIER")

                layout.prop(mmr, "extras_enabled", text=i18n("Extras"), toggle=True,icon="PREFERENCES")

                if mmr.extras_enabled:

                    row = layout.row()
                    row.prop(mmr, "Bend_the_bones", text=i18n("Bend the arm bones"))
                    row.prop(mmr, "Bend_angle_arm", text=i18n("Bend angle"))

                    row = layout.row()
                    # 弯曲腿部骨骼
                    row.prop(mmr, "Bend_the_leg_bones", text=i18n("Bend the leg bones"))
                    row.prop(mmr, "Bend_angle_leg", text=i18n("Bend angle"))
                    # 禁用手掌修正
                    layout.prop(mmr, "Disable_hand_fix", text=i18n("Disable hand fix"))
                    # 权重骨骼父级修正
                    layout.prop(mmr, "Weight_bone_parent_fix", text=i18n("Weight bone parent fix"))
                    if mmr.Weight_bone_parent_fix:
                        # 列表显示区域
                        row = layout.row()
                        row.template_list("MMR_UL_weight_bone_parent_fix", "",
                                        context.active_object, "mmr_weight_bone_parent_fix",
                                        context.active_object, "mmr_weight_bone_parent_fix_index",
                                        rows=6)

                        col = row.column(align=True)
                        # 添加按钮
                        col.operator(MMR_OT_Weight_Bone_Parent_Add.bl_idname, text='', icon="ADD")
                        # 删除按钮
                        col.operator(MMR_OT_Weight_Bone_Parent_Del.bl_idname, text='', icon="REMOVE")

                        col = col.column()
                        # 导入默认项
                        col.operator(MMR_OT_Import_Default_Weight_Bone_Parent.bl_idname, text='', icon="FILE_REFRESH")

                    # 禁用脚趾位置约束
                    layout.prop(mmr, "Disable_toe_position_constraint", text=i18n("Disable toe position constraint"))
                    # 手指选项
                    layout.prop(mmr, "Finger_options", text=i18n("Finger options"))
                    if mmr.Finger_options:
                        # 修复手指尖端骨骼
                        layout.prop(mmr, "f_pin", text=i18n("Finger tip bone repair"))
                        # 启用手指IK
                        layout.prop(mmr, "Enable_finger_IK", text=i18n("Enable Finger IK"))
                        # 拇指旋转与世界Z轴对齐
                        layout.prop(mmr, "Thumb_twist_aligns_with_the_world_Z_axis",
                                    text=i18n("Thumb twist aligns with the world Z-axis"))

                    # 使用ITASC解算器
                    layout.prop(mmr, "Use_ITASC_solver", text=i18n("Use ITASC solver"))
                    # ORG模式
                    layout.prop(mmr, "ORG_mode", text=i18n("ORG mode"))
                    # 极性目标
                    layout.prop(mmr, "Polar_target", text=i18n("Polar target"))
                    # 肩膀链接
                    layout.prop(mmr, "Shoulder_linkage", text=i18n("Shoulder linkage"))
                    if mmr.Shoulder_linkage:
                        layout.label(text=i18n("This option has a serious bug and should not be enabled"), icon='ERROR')

                    layout.prop(mmr, "Upper_body_linkage", text=i18n("Upper body linkage"))

                    # 隐藏骨架
                    layout.prop(mmr, "Hide_mmd_skeleton", text=i18n("No Hide skeleton"))

                    layout.prop(mmr, "Only_meta_bones_are_generated", text=i18n("Only meta bones are generated"))

                    layout.prop(mmr, "Towards_the_dialog_box", text=i18n("Sets the default orientation"))
                    layout.prop(mmr, "Reference_bones", text=i18n("Reference bones"))

                    layout.prop(mmr, "Wrist_twist_preset", text=i18n("Wrist twist preset"))
                    if mmr.Wrist_twist_preset:
                        box = layout.box()
                        box.prop(mmr, "Left_upper_arm_twist", text=i18n("Left upper arm twist"))
                        box.prop(mmr, "Right_upper_arm_twist", text=i18n("Right upper arm twist"))
                        box.prop(mmr, "Left_lower_arm_twist", text=i18n("Left lower arm twist"))
                        box.prop(mmr, "Right_lower_arm_twist", text=i18n("Right lower arm twist"))

                    layout.prop(mmr, "panel_preset", text=i18n("Customize the panel preset"))
                    if mmr.panel_preset:
                        # 背景变黑
                        box = layout.box()
                        box.prop(mmr, "panel_preset_bone", text=i18n("Constraint Bone"))
                        box.prop(mmr, "panel_preset_A", text=i18n("A"))
                        box.prop(mmr, "panel_preset_I", text=i18n("I"))
                        box.prop(mmr, "panel_preset_U", text=i18n("U"))
                        box.prop(mmr, "panel_preset_E", text=i18n("E"))
                        box.prop(mmr, "panel_preset_O", text=i18n("O"))
                    layout.prop(mmr, "direct_operation_shape_key", text=i18n("Direct operation shape key"))
                    # 不使用MMR刚体
                    layout.prop(prefs, "no_mmr_rigidbody", text=i18n("No MMD Rigidbody"))
                    layout.prop(mmr, "Preset_editor", text=i18n("MMR Preset Editor"))
            else:
                layout.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
                layout.prop(mmr, "json_txt")
                scene = context.scene
                # 列表显示区域
                row = layout.row()
                row.template_list(
                    "MMR_UL_JsonList",
                    "",
                    scene,
                    "mmr_json",
                    scene,
                    "mmr_json_index",
                    rows=4
                )
                # 右侧操作按钮列
                col = row.column(align=True)
                col.operator("mmr.add_json_item", icon='ADD', text="")
                col.operator("mmr.remove_json_item", icon='REMOVE', text="")
                row = layout.row()
                row.operator(mmrdesignatedOperator.bl_idname, text="designated")
                bone_name = scene.mmr_json[scene.mmr_json_index].value
                row.operator(MMR_OT_Designated.bl_idname, text=i18n("Re designated")+f"({bone_name})")
                row = layout.row()
                row.operator(mmrmakepresetsOperator.bl_idname, text="Exit the designation")
        else:
            layout.label(text=i18n("Please choose a skeleton"), icon='ERROR')

# 设置约束
class Set_constraints(bpy.types.Panel):
    bl_idname = "BONE_PT_mmr_constraints_bone"
    bl_label = "MMR Bone constraints"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        if context.active_bone is None:
            return False
        else:
            if bpy.context.mode == 'POSE':
                if context.active_object.mmr.MMR_Arm:
                    return True

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        mmr_bone = bpy.context.active_pose_bone.mmr_bone

        layout.label(text=i18n('Set constraint type:'))
        names = [i18n('Copy Rotation'), i18n('Copy Location'), i18n('Copy Scale')]

        row = layout.row(align=True)
        for i in range(0, 3):
            row.prop(mmr_bone, "Set_constraints", index=i, text=str(names[i]), toggle=True)

# 骨骼重定向
@reg_order(1)
class MMD_Rig_Opt_Polar(bpy.types.Panel):
    bl_label = "Bone retargeting"
    bl_idname = "SCENE_PT_MMR_Rig_1"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mmr = context.object.mmr
        layout.prop(mmr, "py_presets", text=i18n('presets'))
        layout.prop(mmr, "frame_step", text=i18n('Bake Frame Step'))
        layout.operator(MMR_redirect.bl_idname, icon='OUTLINER_DATA_ARMATURE')
        layout.operator(MMR_Import_VMD.bl_idname, icon='OUTLINER_OB_ARMATURE')
        layout.operator(mmrexportvmdactionsOperator.bl_idname, text="Export VMD actions", icon='ANIM')
        layout.operator(MMR_OT_OpenPresetFolder.bl_idname, icon='FILE_FOLDER')
        layout.prop(mmr, "boolean", text=i18n("Extras"), toggle=True,icon="PREFERENCES")
        if mmr.boolean:
            layout.prop(mmr, "Manually_adjust_FBX_movements", text=i18n("Manually adjust FBX movements"))
            layout.prop(mmr, "Manually_adjust_VMD_movements", text=i18n("Manually adjust VMD movements"))
            layout.prop(mmr, "IK_import_bool", text=i18n("Enable VMD IK import（Mandatory）"))

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

@reg_order(2)
class MMD_Arm_Opt(bpy.types.Panel):
    bl_label = "MMD tool"
    bl_idname = "SCENE_PT_MMR_Rig_2"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"

    def draw(self, context: bpy.types.Context):

        mmr = context.object.mmr

        # 从上往下排列
        layout = self.layout

        # 增加按钮大小并添加图标
        row = layout.row()
        row.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
        row.operator(polartargetOperator.bl_idname, text="Optimization MMD Armature", icon='BONE_DATA')
        layout.prop(mmr, "mmd_tool_extras", text=i18n("Extras"), toggle=True,icon="PREFERENCES")

        if mmr.mmd_tool_extras:

            layout.label(text=i18n("Automatic IK bone chain:"))

            row = layout.row()
            row.template_list("MMR_UL_automatic_ik_bone_chain", "",
                                 context.object, "mmr_automatic_ik_bone_chain",
                                 context.object, "mmr_automatic_ik_bone_chain_index",
                                 rows=5)

            col = row.column()
            col.operator(MMR_OT_Add_Automatic_IK_Bone_Chain.bl_idname,icon="ADD")
            col.operator(MMR_OT_Remove_Automatic_IK_Bone_Chain.bl_idname,icon="REMOVE")
            col.operator(MMR_OT_Import_Default_Automatic_IK_Bone_Chain.bl_idname,icon="FILE_REFRESH")
            col.operator(MMR_OT_Add_Automatic_IK_Bone_Chain_Separator.bl_idname,icon="DRIVER_DISTANCE")
            col.operator(MMR_OT_Designated_Bone_Chain.bl_idname,icon="GROUP_BONE")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

# 物理面板
@reg_order(3)
class Physics_Panel(bpy.types.Panel):
    bl_label = "Physics options"
    bl_idname = "SCENE_PT_MMR_Rig_3"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = "MMR"

    __RIGID_SIZE_MAP = {
        "SPHERE": ("Radius",),
        "BOX": ("X", "Y", "Z"),
        "CAPSULE": ("Radius", "Height"),
    }

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mmr = context.object.mmr
        prefs = context.preferences.addons[__addon_name__].preferences

        layout.label(text=i18n("Damping Tracking"))
        layout.prop(mmr, "Softness", text=i18n("Softness"))
        row = layout.row(align=True)
        row.operator(Add_Damping_Tracking.bl_idname, text="Add Damping Tracking")
        row.operator(Remove_Damping_Tracking.bl_idname, text="", icon='TRASH')

        layout.separator()

        obj = context.active_object

        layout.use_property_split = True

        scene = context.scene
        rbw = scene.rigidbody_world

        if rbw:
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

            col = flow.column()
            col.active = rbw.enabled

            col = col.column()
            col.prop(rbw, "time_scale", text="Speed")

            col = flow.column()
            col.active = rbw.enabled
            col.prop(rbw, "use_split_impulse")

            col = col.column()
            col.prop(rbw, "substeps_per_frame",text="Substeps")
            col.prop(rbw, "solver_iterations", text="Iterations")

            rigidbody_world = context.scene.rigidbody_world

            point_cache = rigidbody_world.point_cache

            col = layout.column(align=True)
            row = col.row(align=True)
            row.enabled = not point_cache.is_baked
            row.prop(point_cache, "frame_start")
            row.prop(point_cache, "frame_end")

            layout.use_property_split = False

            layout.prop(rbw, "enabled", text=i18n('Global Rigidbody physical'))

            row = layout.row(align=True)
            row.label(text="Rigid Body Physics:", icon="PHYSICS")
            row.operator(Update_World.bl_idname, text="Update World", icon="ERROR")

            row = layout.row(align=True)
            if point_cache.is_baked is True:
                row.operator("mmd_tools.ptcache_rigid_body_delete_bake", text="Delete Bake")
            else:
                row.operator("mmd_tools.ptcache_rigid_body_bake", text="Bake")

        layout.use_property_split = False

        row = layout.row()
        row.label(text=i18n("MMD Rigidbody"))
        row.prop(context.scene.mmr, "mmd_rigid_panel_bool", text=i18n("Hide MMD Rigidbody"))

        row = layout.row(align=True)

        # 查找MMD根对象
        active_obj = bpy.context.active_object

        # 只能循环50次, 防止无限循环
        i = 50

        # 循环, 直到找到MMD根对象
        while active_obj and active_obj.mmd_type != 'ROOT' and i > 0:
            i -= 1 # 循环次数减一
            active_obj = active_obj.parent # 上一级对象

        # 检查活动物体是否是MMD模型
        if active_obj and (active_obj.mmd_type or active_obj.mmd_type == 'ROOT'):

            if active_obj and not active_obj.mmd_root.is_built:
                row.operator(MMD_RIG_PHYSICS_BUILD.bl_idname, text="Physics", icon="PHYSICS", depress=False)
            else:
                row.operator(MMD_RIG_PHYSICS_BUILD.bl_idname, text="Physics", icon="PHYSICS", depress=True)

        row.operator(Show_Rigidbody.bl_idname, text="Show Rigidbody", icon="RIGID_BODY")
        row.operator(Show_Joint.bl_idname, text="Show Joint", icon="RIGID_BODY_CONSTRAINT")

        if not context.scene.mmr.mmd_rigid_panel_bool:
            if obj is not None and obj.mmd_type == "RIGID_BODY":

                c = layout.column()
                c.prop(obj.mmd_rigid, "name_j")
                c.prop(obj.mmd_rigid, "name_e")

                c = layout.column(align=True)
                row = c.row(align=True)
                row.prop(obj.mmd_rigid, "type", expand=True)

                row = c.row(align=True)
                row.prop(obj.mmd_rigid, "bone", icon="BONE_DATA", text="")

                c = layout.column(align=True)
                c.enabled = obj.mode == "OBJECT"
                c.row(align=True).prop(obj.mmd_rigid, "shape", expand=True)

                col = c.column(align=True)
                for i, name in enumerate(self.__RIGID_SIZE_MAP[obj.mmd_rigid.shape]):
                    col.prop(obj.mmd_rigid, "size", text=name, index=i)

                row = c.row(align=True)
                c = row.column()
                c.prop(obj.rigid_body, "mass")
                c.prop(obj.mmd_rigid, "collision_group_number")
                c = row.column()
                c.prop(obj.rigid_body, "restitution")
                c.prop(obj.rigid_body, "friction")

                c = layout.column()
                col = c.column(align=True)
                col.label(text="Collision Group Mask:")
                row = col.row(align=True)
                for i in range(8):
                    row.prop(obj.mmd_rigid, "collision_group_mask", index=i, text=str(i), toggle=True)
                row = col.row(align=True)
                for i in range(8, 16):
                    row.prop(obj.mmd_rigid, "collision_group_mask", index=i, text=str(i), toggle=True)

                c = layout.column()
                c.label(text="Damping")
                row = c.row()
                row.prop(obj.rigid_body, "linear_damping")
                row.prop(obj.rigid_body, "angular_damping")

        row = layout.row()
        # 选择碰撞组
        row.operator(Select_Collision_Group.bl_idname)
        row.operator(Select_By_Type.bl_idname)

        if not prefs.no_mmr_rigidbody:

            layout.label(text=i18n("MMR Rigidbody"))

            row = layout.row()
            # MMR刚体
            row.operator(Assign_Rigidbody.bl_idname)
            # 解除物理
            row.operator(Remove_physics.bl_idname)
            # MMD刚体转换MMR刚体
            layout.operator(mmdrigidbody_to_mmrrigidbody.bl_idname)

            mmr_bone = context.active_object.mmr_bone

            if mmr_bone.panel_bool:

                mmr_bone = context.active_object.mmr_bone

                row = layout.row(align=True)
                row.prop(obj.rigid_body, "mass")
                row.prop(obj.rigid_body, "restitution")

                row = layout.row(align=True)
                row.prop(mmr_bone, "collision_group_index", text="Collision Group")
                row.prop(obj.rigid_body, "friction")

                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(mmr_bone, "rigidbody_type", text="Rigidbody Type", expand = True)
                row = col.row(align=True)
                row.prop(mmr_bone, "bone", icon="BONE_DATA")


                col = layout.column(align=True)
                col.label(text=i18n("collision collections:"))
                c = col.row(align=True)
                for i in range(10):
                    c.prop(obj.rigid_body, "collision_collections", index=i, text=str(i), toggle=True)
                c = col.row(align=True)
                for i in range(10, 20):
                    c.prop(obj.rigid_body, "collision_collections", index=i, text=str(i), toggle=True)

                # 碰撞组掩码部分
                col = layout.column(align=True)
                col.label(text=i18n("Collision Group Mask:"))

                # 第一行显示 0-7 组
                row = col.row(align=True)
                for i in range(0, 8):
                    row.prop(mmr_bone, "collision_group_mask", index=i, text=str(i), toggle=True)

                # 第二行显示 8-15 组
                row = col.row(align=True)
                for i in range(8, 16):
                    row.prop(mmr_bone, "collision_group_mask", index=i, text=str(i), toggle=True)

                c = layout.column()
                c.label(text="Damping")
                row = c.row()
                row.prop(obj.rigid_body, "linear_damping")
                row.prop(obj.rigid_body, "angular_damping")

            obj = context.active_object
            rbc = obj.rigid_body_constraint
            constraint = obj.rigid_body_constraint

            if constraint:
                if constraint.type == "GENERIC_SPRING":
                    layout.label(text=i18n("Rigidbody Constraint"))

                    c = layout.column()
                    c.prop(rbc, "object1")
                    c.prop(rbc, "object2")

                    layout.label(text=i18n("Limit(Location)"))
                    row = layout.row(align=True)
                    col = row.column(align=True)
                    row = col.row(align=True)
                    row.prop(rbc, "limit_lin_x_lower")
                    row.prop(rbc, "limit_lin_x_upper")
                    row = col.row(align=True)
                    row.prop(rbc, "limit_lin_y_lower")
                    row.prop(rbc, "limit_lin_y_upper")
                    row = col.row(align=True)
                    row.prop(rbc, "limit_lin_z_lower")
                    row.prop(rbc, "limit_lin_z_upper")

                    layout.label(text=i18n("Limit(Angle)"))
                    row = layout.row(align=True)
                    col = row.column(align=True)
                    row = col.row(align=True)
                    row.prop(rbc, "limit_ang_x_lower")
                    row.prop(rbc, "limit_ang_x_upper")
                    row = col.row(align=True)
                    row.prop(rbc, "limit_ang_y_lower")
                    row.prop(rbc, "limit_ang_y_upper")
                    row = col.row(align=True)
                    row.prop(rbc, "limit_ang_z_lower")
                    row.prop(rbc, "limit_ang_z_upper")

                    ob = context.object
                    rbc = ob.rigid_body_constraint
                    row = layout.row()

                    col = row.column(align=True)
                    col.label(text=i18n("Spring(Location)"))
                    col.prop(rbc, "spring_stiffness_x", text="X Stiffness")
                    col.prop(rbc, "spring_stiffness_y", text="Y Stiffness")
                    col.prop(rbc, "spring_stiffness_z", text="Z Stiffness")

                    col = row.column(align=True)
                    col.label(text=i18n("Spring(Angle)"))
                    col.prop(rbc, "spring_stiffness_ang_x", text="X Stiffness")
                    col.prop(rbc, "spring_stiffness_ang_y", text="Y Stiffness")
                    col.prop(rbc, "spring_stiffness_ang_z", text="Z Stiffness")

                    row = layout.row()
                    # 选择碰撞组
                    row.operator(Select_Collision_Group_For_Joint.bl_idname)
                    # 按类型选择
                    row.operator(Select_By_Type_For_Joint.bl_idname)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

# 刚体选择
class MMRSelect_PT_Rigidbody(bpy.types.Panel):
    bl_idname = "MMR_PT_Select_Rigidbody"
    bl_label = "Rigidbody Select"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        # 选择碰撞组
        row.operator(Select_Collision_Group.bl_idname)
        # 按类型选择
        row.operator(Select_By_Type.bl_idname)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object.rigid_body is not None

# 刚体约束选择
class MMR_PT_Select_Constructability(bpy.types.Panel):
    bl_idname = "MMR_PT_Select_Constructability"
    bl_label = "Rigidbody Constraint Select"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        # 选择碰撞组
        row.operator(Select_Collision_Group_For_Joint.bl_idname)
        # 按类型选择
        row.operator(Select_By_Type_For_Joint.bl_idname)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object.rigid_body_constraint is not None
