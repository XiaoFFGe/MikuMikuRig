import bpy
from bpy.app.handlers import persistent

from .config import __addon_name__
from .i18n.dictionary import dictionary
from .operators import has_keyframes_for_property
from .panels import MMR_property, MMR_bone_property, MMR_Scene_Property, MMR_key_property
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary

# Add-on info
bl_info = {
    "name": "MikuMikuRig",
    "author": "小峰峰哥l",
    "blender": (4, 2, 0),
    "version": (1, 76),
    "description": "MMD骨骼优化工具",
    "tracker_url": "https://space.bilibili.com/2109816568?spm_id_from=333.1007.0.0",
    "support": "COMMUNITY",
    "category": "VIEW_3D"
}

_addon_properties = {}

@ persistent
def sync_mmr_key_values(scene,depsgraph):

    # 获取目标对象
    obj = bpy.context.active_object

    if not obj:
        return

    # 获取批量调整值
    current_value1 = obj.mmr.Batch_adjust_shape_key

    # 如果值没有改变, 则不进行处理
    if current_value1 == obj.mmr.last_batch_adjust_value:
        return

    # 更新存储的值
    obj.mmr.last_batch_adjust_value = current_value1

    for idx, key in enumerate(obj.mmr_key):
        if key.select:

            meshkey = key.meshkey

            if not obj.mmr.register_handler:
                if not obj.mmr.direct_operation_shape_key:
                    # 同步到值
                    key.value = current_value1
                else:
                    if meshkey:
                        meshkey.key_blocks[key.meshkey_index].value = current_value1

                # 是否插入关键帧
                if bpy.context.scene.tool_settings.use_keyframe_insert_auto:

                    if not obj.mmr.direct_operation_shape_key:

                        if obj.mmr.insert_keyframe: # 选中的有关键帧的才会插入关键帧
                            if has_keyframes_for_property(obj, "mmr_key[%d].value" % idx):
                                obj.keyframe_insert(data_path="mmr_key[%d].value" % idx,frame=bpy.context.scene.frame_current)

                        if obj.mmr.use_keyframe_insert_auto: # 自动插入关键帧
                            obj.keyframe_insert(data_path="mmr_key[%d].value" % idx, frame=bpy.context.scene.frame_current)
                    else:
                        if meshkey:

                            if obj.mmr.insert_keyframe:  # 选中的有关键帧的才会插入关键帧
                                if has_keyframes_for_property(meshkey, f"key_blocks['{str(key.name)}'].value"):
                                    meshkey.key_blocks[key.meshkey_index].keyframe_insert(data_path="value", frame=bpy.context.scene.frame_current)

                            if obj.mmr.use_keyframe_insert_auto:  # 自动插入关键帧
                                meshkey.key_blocks[key.meshkey_index].keyframe_insert(data_path="value", frame=bpy.context.scene.frame_current)

def register():
    print("正在注册")  # 打印正在注册的提示信息
    # 注册类
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)
    bpy.utils.register_class(MMR_property)
    bpy.types.Object.mmr = bpy.props.PointerProperty(type=MMR_property)
    bpy.utils.register_class(MMR_bone_property)
    bpy.types.Object.mmr_bone = bpy.props.PointerProperty(type=MMR_bone_property)
    bpy.utils.register_class(MMR_Scene_Property)
    bpy.types.Scene.mmr = bpy.props.PointerProperty(type=MMR_Scene_Property)
    bpy.utils.register_class(MMR_key_property)
    bpy.types.Object.mmr_key = bpy.props.CollectionProperty(type=MMR_key_property)

    # 注册事件处理函数, 当场景的属性更新时调用 sync_mmr_key_values 函数
    bpy.app.handlers.depsgraph_update_pre.append(sync_mmr_key_values)

    # 国际化（多语言支持相关操作）
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)
    print("{}插件已安装。".format(bl_info["name"]))

def unregister():
    # 国际化（多语言支持相关操作）
    bpy.app.translations.unregister(__addon_name__)
    # 注销类
    auto_load.unregister()
    remove_properties(_addon_properties)
    del bpy.types.Object.mmr
    bpy.utils.unregister_class(MMR_property)
    del bpy.types.Object.mmr_bone
    bpy.utils.unregister_class(MMR_Scene_Property)
    del bpy.types.Scene.mmr
    bpy.utils.unregister_class(MMR_key_property)
    del bpy.types.Object.mmr_key

    # 注销事件处理函数
    bpy.app.handlers.depsgraph_update_pre.remove(sync_mmr_key_values)

    bpy.utils.unregister_class(MMR_bone_property)
    print("{}插件已卸载。".format(bl_info["name"]))