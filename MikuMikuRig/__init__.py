from .addons.MikuMikuRig import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": 'MikuMikuRig',
    "author": '小峰峰哥l',
    "blender": (4, 2, 0),
    "version": (1, 36),
    "description": 'MMD骨骼优化工具',
    "tracker_url": 'https://space.bilibili.com/2109816568?spm_id_from=333.1007.0.0',
    "support": 'COMMUNITY',
    "category": 'VIEW_3D'
}

def register():
    addon_register()

def unregister():
    addon_unregister()

    