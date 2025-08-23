import bpy

from MikuMikuRig.addons.MikuMikuRig.operators.MMRpresets import mmrmakepresetsOperator, mmrdesignatedOperator
from MikuMikuRig.addons.MikuMikuRig.operators.Physics import Add_Damping_Tracking, Remove_Damping_Tracking, Assign_Rigidbody, \
    Assign_armature_rigidbody, Open_MMD_Physics, Show_Rigidbody, Select_Collision_Group, Update_World, Select_By_Type
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import mmdarmoptOperator, mmrexportvmdactionsOperator
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import mmrrigOperator
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import polartargetOperator
from MikuMikuRig.addons.MikuMikuRig.operators.redirect import MMR_redirect, MMR_Import_VMD
from MikuMikuRig.addons.MikuMikuRig.operators.reload import MMR_OT_OpenPresetFolder
from MikuMikuRig.addons.Miku_Miku_Rig.mmr_operators.preset import mmr_bone_property_set
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
    bl_idname = "SCENE_PT_MMR_Rig_1"
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
    bl_idname = "SCENE_PT_MMR_Rig_2"
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

# 物理面板
class Physics_Panel(bpy.types.Panel):
    bl_label = "Physics options"
    bl_idname = "SCENE_PT_MMR_Rig_3"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = "MMR"
    bl_parent_id = "SCENE_PT_MMR_Rig_A"

    __RIGID_SIZE_MAP = {
        "SPHERE": ("Radius",),
        "BOX": ("X", "Y", "Z"),
        "CAPSULE": ("Radius", "Height"),
    }

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mmr = context.object.mmr

        layout.label(text=i18n("Damping Tracking"))
        layout.prop(mmr, "Softness", text=i18n("Softness"))
        row = layout.row(align=True)
        row.operator(Add_Damping_Tracking.bl_idname, text="Add Damping Tracking")
        row.operator(Remove_Damping_Tracking.bl_idname, text="", icon='TRASH')

        layout.separator()
        layout.label(text=i18n("MMD Rigidbody"))


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

        if mmr.physics_bool:
            row.operator(Open_MMD_Physics.bl_idname, text="Physics", icon="PHYSICS", depress=True)
        else:
            row.operator(Open_MMD_Physics.bl_idname, text="Physics", icon="PHYSICS", depress=False)

        row.operator(Show_Rigidbody.bl_idname, text="Show Rigidbody", icon="RIGID_BODY")

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

            col = layout.column(align=True)
            col.label(text=i18n("collision collections:"))
            c = col.row(align=True)
            for i in range(10):
                c.prop(obj.rigid_body, "collision_collections", index=i, text=str(i), toggle=True)
            c = col.row(align=True)
            for i in range(10, 20):
                c.prop(obj.rigid_body, "collision_collections", index=i, text=str(i), toggle=True)

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

        if context.active_pose_bone:
            # 废弃功能
            layout.prop(mmr, "Discarded_function", text=i18n("Discarded function"))
            if mmr.Discarded_function:

                mmr_bone = context.active_pose_bone.mmr_bone

                row = layout.row()
                row.prop(mmr_bone, "collision_group_index", text="Collision Group")
                row.prop(mmr_bone, "damping", text="Damping")

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

                # 装配刚体
                layout.operator(Assign_Rigidbody.bl_idname)

                # 装配骨架刚体
                layout.operator(Assign_armature_rigidbody.bl_idname)


    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None