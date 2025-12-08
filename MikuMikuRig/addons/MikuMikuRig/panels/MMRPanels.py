import bpy

from MikuMikuRig.addons.MikuMikuRig.operators.MMRpresets import mmrmakepresetsOperator, mmrdesignatedOperator
from MikuMikuRig.addons.MikuMikuRig.operators.Physics import Add_Damping_Tracking, Remove_Damping_Tracking, Assign_Rigidbody, \
    Assign_armature_rigidbody, Open_MMD_Physics, Show_Rigidbody, Select_Collision_Group, Update_World, Select_By_Type
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import mmrexportvmdactionsOperator, MahyPdtOperator
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import mmrrigOperator
from MikuMikuRig.addons.MikuMikuRig.operators.RIG import polartargetOperator
from MikuMikuRig.addons.MikuMikuRig.operators.redirect import MMR_redirect, MMR_Import_VMD
from MikuMikuRig.addons.MikuMikuRig.operators.reload import MMR_OT_OpenPresetFolder
from MikuMikuRig.common.i18n.i18n import i18n

class MMD_Rig_Opt(bpy.types.Panel):
    bl_label = "Controller options"
    bl_idname = "SCENE_PT_MMR_Rig_0"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"

    def draw(self, context: bpy.types.Context):

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
                row.prop(mmr, "Import_presets", text=i18n("Import presets"), toggle=True)

                # 增加按钮大小并添加图标
                layout.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
                layout.operator(mmrrigOperator.bl_idname, text="Build a controller",icon="OUTLINER_DATA_ARMATURE")

                layout.operator(MahyPdtOperator.bl_idname, text="Add Mouth Panel",icon="MODIFIER")

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

                    layout.prop(mmr, "Preset_editor", text=i18n("MMR Preset Editor"))
            else:
                layout.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
                layout.prop(mmr, "json_txt")
                row = layout.row()
                row.operator(mmrdesignatedOperator.bl_idname, text="designated")
                row.operator(mmrmakepresetsOperator.bl_idname, text="Exit the designation")
        else:
            layout.label(text=i18n("Please choose a skeleton"), icon='ERROR')
# 骨骼重定向
class MMD_Rig_Opt_Polar(bpy.types.Panel):
    bl_label = "Bone retargeting"
    bl_idname = "SCENE_PT_MMR_Rig_1"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "MMR"
    bl_parent_id = "SCENE_PT_MMR_Rig_0"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        mmr = context.object.mmr
        layout.prop(mmr, "py_presets", text=i18n('presets'))
        layout.operator(MMR_redirect.bl_idname, icon='OUTLINER_DATA_ARMATURE')
        layout.operator(MMR_Import_VMD.bl_idname, icon='OUTLINER_OB_ARMATURE')
        layout.operator(mmrexportvmdactionsOperator.bl_idname, text="Export VMD actions", icon='ANIM')
        layout.operator(MMR_OT_OpenPresetFolder.bl_idname, icon='FILE_FOLDER')
        layout.prop(mmr, "boolean", text=i18n("Extras"), toggle=True,icon="PREFERENCES")
        if mmr.boolean:
            layout.prop(mmr, "Manually_adjust_FBX_movements", text=i18n("Manually adjust FBX movements"))
            layout.prop(mmr, "Manually_adjust_VMD_movements", text=i18n("Manually adjust VMD movements"))

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
    bl_parent_id = "SCENE_PT_MMR_Rig_0"

    def draw(self, context: bpy.types.Context):

        mmr = context.object.mmr

        # 从上往下排列
        layout = self.layout

        # 增加按钮大小并添加图标
        row = layout.row()
        row.scale_y = 1.2  # 这将使按钮的垂直尺寸加倍
        row.operator(polartargetOperator.bl_idname, text="Optimization MMD Armature", icon='BONE_DATA')

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
    bl_parent_id = "SCENE_PT_MMR_Rig_0"

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