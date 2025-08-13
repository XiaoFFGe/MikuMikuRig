import bpy
from .config import __addon_name__
from .i18n.dictionary import dictionary
from .panels import MMR_property
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import load_dictionary

# Add-on info
bl_info = {
    "name": "MikuMikuRig",
    "author": "小峰峰哥l",
    "blender": (4, 2, 0),
    "version": (1, 36),
    "description": "MMD骨骼优化工具",
    "tracker_url": "https://space.bilibili.com/2109816568?spm_id_from=333.1007.0.0",
    "support": "COMMUNITY",
    "category": "VIEW_3D"
}

_addon_properties = {}

def register():
    print("正在注册")  # 打印正在注册的提示信息
    # 注册类
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)
    bpy.utils.register_class(MMR_property)
    bpy.types.Object.mmr = bpy.props.PointerProperty(type=MMR_property)

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

    print("{}插件已卸载。".format(bl_info["name"]))