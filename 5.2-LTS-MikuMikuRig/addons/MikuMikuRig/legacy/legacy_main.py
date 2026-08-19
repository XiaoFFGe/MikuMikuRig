bl_info = {
    "name": "MikuMikuRig (Legacy 0.56)",
    "author": "LaoBro",
    "version": (0, 5, 6, 0),
    "blender": (4, 5, 0),
    "location": "3DView > Tools",
    "description": "快速为各种人形模型生成rigify控制器,一键套mixamo动作",
    "support": 'COMMUNITY',
    "category": "Rigging",
}
import bpy
import bpy_extras
from bpy.types import Operator
from . import translation
from . import mmr_operators
from bpy.props import BoolProperty
from bpy.props import IntProperty
from bpy.props import FloatProperty
from bpy.props import EnumProperty

class MMR_LEGACY_property(bpy.types.PropertyGroup):
    """Legacy 版本的场景属性（使用 mmr_legacy_property 避免与主版本冲突）"""
    upper_body_controller: BoolProperty(default=True, description="上半身控制器")
    wrist_rotation_follow: BoolProperty(default=False, description="手腕旋转跟随手臂")
    solid_rig: BoolProperty(default=False, description="实心控制器")
    min_ik_loop: IntProperty(default=10, description="最小IK迭代次数", min=1)
    lock_location: BoolProperty(default=False, description="锁定动画位置")
    fade_in_out: IntProperty(default=0, description="淡入淡出长度", min=0)
    action_scale: FloatProperty(default=1, description="动作缩放", min=0)
    auto_action_scale: BoolProperty(default=True, description="自动动作缩放")
    subdivide: IntProperty(default=0, description="细分级别", min=0, max=5)
    auto_select_mesh: BoolProperty(default=True, description="自动选择模型")
    auto_select_rigid_body: BoolProperty(default=True, description="自动选择刚体")
    extend_ribbon: BoolProperty(default=True, description="延展飘带区域")
    debug: BoolProperty(default=False, description="debug")
    rig_preset_name: EnumProperty(
        items=mmr_operators.preset.get_rig_preset_item,
        description=('Choose the preset you want to use'),
    )
    retarget_preset_name: EnumProperty(
        items=mmr_operators.preset.get_retarget_preset_item,
        description=('Choose the preset you want to use'),
    )
    IKFK_list = [
        ('None', 'None', ''),
        ('IK', 'IK', ''),
        ('FK', "FK", ''),
    ]
    IKFK_arm: EnumProperty(
        items=IKFK_list,
        description=('retarget mod'),
        default='FK',
    )
    IKFK_leg: EnumProperty(
        items=IKFK_list,
        description=('retarget mod'),
        default='IK',
    )
    cloth_convert_mod: EnumProperty(
        items=[
            ('Auto', 'Auto', ''),
            ('Bone Constrain', 'Bone Constrain', ''),
            ('Surface Deform', 'Surface Deform', '')
        ],
        description=('retarget mod'),
        default='Auto',
    )
    use_itasc_solver: BoolProperty(default=False, description="使用ITASC解算器")
    hide_mmd_skeleton: BoolProperty(default=True, description="隐藏MMD骨架")
    quick_assign_index: IntProperty(default=1, description="快速指定序号", min=1)
    quick_assign_mod: BoolProperty(default=False, description="快速指定模式")
    extra_options1: BoolProperty(default=False, description="高级选项")
    preferences: BoolProperty(default=False, description="偏好设置")
    extra_options2: BoolProperty(default=False, description="高级选项")
    mass_multiply_rate: FloatProperty(default=12.5, description="刚体质量倍率", min=0)
    import_as_NLA_strip: BoolProperty(
        name='Import as NLA strip',
        description="Import as NLA strip",
        default=True
    )


def alert_error(title, message):
    def draw(self, context):
        self.layout.label(text=str(message))
    bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')


# ---- 面板基类 ----

class Mmr_Panel_Base:
    """Legacy 面板基类（不继承 Panel，避免被 auto_load 误注册）"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MMR"
    bl_context = "objectmode"


def _legacy_poll(cls, context):
    """Legacy 面板通用 poll：检查 use_legacy_mode 偏好设置"""
    prefs = context.preferences.addons.get("MikuMikuRig")
    return prefs is not None and getattr(prefs.preferences, 'use_legacy_mode', False)


class MikuMikuRig_1(Mmr_Panel_Base, bpy.types.Panel):
    bl_idname = "MMR_PT_LEGACY_panel_1"
    bl_label = "Auto MMD rig"

    @classmethod
    def poll(cls, context):
        return _legacy_poll(cls, context)

    def draw(self, context):
        prefs = context.preferences.addons["MikuMikuRig"].preferences
        scene = context.scene
        mmr_property = scene.mmr_legacy_property
        layout = self.layout
        layout.label(text="Select MMD armature then press the button")
        layout.operator("mmr_legacy.generate_rig", text="Generate MMD rig")
        layout.prop(mmr_property, 'upper_body_controller', text="Upper body controller")
        layout.prop(prefs, 'bent_IK_bone', text="Bent IK bone")
        layout.prop(mmr_property, 'wrist_rotation_follow', text="Wrist rotation follow arm")
        layout.prop(prefs, 'auto_shoulder', text="Shoulder IK")
        layout.prop(mmr_property, 'solid_rig', text="Replace the controller")
        layout.prop(prefs, 'pole_target', text="Use pole target")


class MikuMikuRig_2(Mmr_Panel_Base, bpy.types.Panel):
    bl_idname = "MMR_PT_LEGACY_panel_2"
    bl_label = "Extra"

    @classmethod
    def poll(cls, context):
        return _legacy_poll(cls, context)

    def draw(self, context):
        prefs = context.preferences
        view = prefs.view
        scene = context.scene
        mmr_property = scene.mmr_legacy_property
        layout = self.layout
        layout.prop(mmr_property, 'min_ik_loop', text="Min IK loop")
        layout.operator("mmr.set_min_ik_loop", text="Set min IK loop")
        layout.prop(mmr_property, 'mass_multiply_rate', text="Multiply Rate")
        layout.operator("mmr.rigid_body_mass_multiply", text="Rigid Body Mass Multiply")
        layout.operator("mmr.hide_skirt", text="Hide Skirt By Rigid Body")
        layout.operator("mmr.decorate_mmd_arm", text="Decorate MMD Arm")


class MikuMikuRig_3(Mmr_Panel_Base, bpy.types.Panel):
    bl_idname = "MMR_PT_LEGACY_panel_3"
    bl_label = "Auto animation import"

    @classmethod
    def poll(cls, context):
        return _legacy_poll(cls, context)

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_legacy_property
        layout = self.layout
        layout.label(text="Select rigify controller then press the button")
        layout.prop(mmr_property, 'fade_in_out', text="Fade in out")
        layout.prop(mmr_property, 'action_scale', text="Animation scale")
        layout.prop(mmr_property, 'auto_action_scale', text="Auto mixamo animation scale", toggle=True)
        layout.prop(mmr_property, 'lock_location', text="Lock mixamo animation location", toggle=True)
        row = layout.row()
        row.label(text='Arm:', translate=False)
        row.prop(mmr_property, 'IKFK_arm', expand=True)
        row = layout.row()
        row.label(text='Leg:', translate=False)
        row.prop(mmr_property, 'IKFK_leg', expand=True)
        layout.operator("mmr.import_mixamo", text="Import mixamo animation as NLA")
        layout.operator("mmr.import_vmd", text="Import VMD animation as NLA")
        layout.operator("mmr.export_vmd", text="Bake and export VMD animation")

class MikuMikuRig_4(Mmr_Panel_Base, bpy.types.Panel):
    bl_idname = "MMR_PT_LEGACY_panel_4"
    bl_label = "Auto cloth(experimental)"

    @classmethod
    def poll(cls, context):
        return _legacy_poll(cls, context)

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_legacy_property
        layout = self.layout
        layout.label(text="Select mesh and rigidbody then press the button")
        layout.operator("mmr.convert_rigid_body_to_cloth", text="Convert rigid body to cloth")
        layout.prop(mmr_property, 'subdivide', text="Subdivide level")
        layout.label(text='Convert Mod:')
        layout.props_enum(mmr_property, 'cloth_convert_mod')
        layout.label(text='Options:')
        layout.prop(mmr_property, 'auto_select_mesh', text="Auto select mesh", toggle=True)
        layout.prop(mmr_property, 'auto_select_rigid_body', text="Auto select rigid body", toggle=True)
        layout.prop(mmr_property, 'extend_ribbon', text="Extend ribbon area", toggle=True)
        layout.label(text="This feature is developed in cooperation with")
        layout.label(text="UuuNyaa")


class MikuMikuRig_5(Mmr_Panel_Base, bpy.types.Panel):
    bl_idname = "MMR_PT_LEGACY_panel_5"
    bl_label = "About"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return _legacy_poll(cls, context)

    def draw(self, context):
        scene = context.scene
        mmr_property = scene.mmr_legacy_property
        layout = self.layout
        layout.label(text="MikuMikuRig (Legacy 0.56)")
        layout.label(text="版本号:" + str(bl_info["version"]))
        layout.label(text="作者:小威廉伯爵")
        layout.prop(mmr_property, 'debug', text="Debug")


# ---- 缺失的 generate_rig 操作符 ----

class OT_Generate_Rig_Legacy(Operator):
    """Legacy 版本的生成骨骼操作符"""
    bl_idname = "mmr_legacy.generate_rig"
    bl_label = "Generate MMD Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons.get("MikuMikuRig")
        return prefs and getattr(prefs.preferences, 'use_legacy_mode', False)

    def execute(self, context):
        from .mmr_operators import rig, preset
        scene = context.scene
        mmr_property = scene.mmr_legacy_property
        if rig.check_arm() == False:
            return {'CANCELLED'}
        obj = context.object
        pose = obj.pose
        preset_name = mmr_property.rig_preset_name
        if preset_name and preset_name != 'None':
            rig_preset = preset.preset_dict_dict['rig'].get(preset_name)
            if rig_preset:
                preset.set_bone_type(pose, rig_preset)
        result = rig.RIG2(context)
        if result:
            return {'FINISHED'}
        return {'CANCELLED'}


# ---- 注册/注销 ----

def register():
    """注册 legacy 版本（属性由各子模块 register 处理，auto_load 负责调用）"""
    print('[MikuMikuRig Legacy] registered')


def unregister():
    """注销 legacy 版本"""
    print('[MikuMikuRig Legacy] unregistered')