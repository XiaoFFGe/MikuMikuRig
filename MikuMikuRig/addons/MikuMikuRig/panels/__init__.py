import os
import bpy
from bpy.props import *

from MikuMikuRig.addons.MikuMikuRig.config import __addon_name__

# 哇哦~文件缓存系统得了vmp！
file_cache = {
    ".json": {"mtime": 0, "files": [], "files_ic": []},
    ".py": {"mtime": 0, "files": [], "files_ic": []}
}

# 获取预设目录
def get_presets_directory():
    new_path = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(new_path, 'operators', 'presets')


TARGET_FOLDER = get_presets_directory()  # 预设目录


def get_file_list(extension):
    global file_cache

    try:
        # 获取当前扩展名的缓存
        cache = file_cache[extension]
        current_mtime = os.path.getmtime(TARGET_FOLDER)

        # 检查目录修改时间和缓存有效性
        if current_mtime == cache["mtime"] and cache["files"]:
            return cache["files"]

        valid_files = []
        valid_files_ic = []

        # 遍历目录并过滤文件
        for f in os.listdir(TARGET_FOLDER):
            file_path = os.path.join(TARGET_FOLDER, f)
            if os.path.isfile(file_path) and f.endswith(extension):
                # 提取基础文件名和生成描述
                base_name = os.path.splitext(f)[0]
                valid_files.append(base_name)
                valid_files_ic.append(f"选择文件：{base_name}")

        # 更新当前扩展名的缓存
        file_cache[extension] = {
            "mtime": current_mtime,
            "files": sorted(valid_files, key=str.lower),
            "files_ic": sorted(valid_files_ic, key=str.lower)
        }

        return file_cache[extension]["files"]

    except Exception as e:
        print(f"预设加载错误: {str(e)}")
        return []


def make_presets_enum(extension):
    def update_file_list(self, context):
        files = get_file_list(extension)  # 传入扩展名参数
        cache = file_cache[extension]

        items = []
        # 安全遍历：确保两个列表长度一致
        for idx in range(min(len(files), len(cache["files_ic"]))):
            items.append((
                files[idx],
                files[idx],
                cache["files_ic"][idx]
            ))

        # 处理空列表情况
        return items or [("NONE", "无可用文件", "空预设")]

    return update_file_list

class MMR_property(bpy.types.PropertyGroup):
    # 控制器预设（.json）
    presets: EnumProperty(
        name="Controller Presets",
        description="选择控制器预设配置",
        items=make_presets_enum('.json'),
    )

    # 重定向预设（.py）
    py_presets: EnumProperty(
        name="Retarget Presets",
        description="选择骨骼重定向预设配置",
        items=make_presets_enum('.py'),
    )

    filepath: StringProperty(
        name="",
        subtype='FILE_PATH'
    )

    number: IntProperty(
        name="Int Config",
        default=2,
    )

    Towards_the_dialog_box: BoolProperty(
        name="Sets the default orientation",
        default=False,
        description="如果模型的正面朝向-Y，就选择-Y"
    )

    boolean: BoolProperty(
        name="Boolean Config",
        default=False,
    )

    # 创建布尔属性作为极向目标开关
    Polar_target: BoolProperty(
        name="Polar target",
        default=False
    )

    extras_enabled: BoolProperty(
        name="Extras Enabled",
        default=False
    )

    Shoulder_linkage: BoolProperty(
        name="Shoulder linkage",
        default=False
    )

    json_filepath: StringProperty(
        name="",
        subtype='FILE_PATH',
        description="导入json字典预设"
    )

    Import_presets: BoolProperty(
        name="Import presets",
        default=False,
        description="导入json字典预设"
    )
    Bend_the_bones: BoolProperty(
        name="Bend the bones",
        default=False,
        description='弯曲手臂骨骼'
    )
    Only_meta_bones_are_generated: BoolProperty(
        name="Only meta bones are generated",
        default=False,
        description="仅生成元骨骼"
    )

    make_presets: BoolProperty(
        default=True,
    )

    number: IntProperty(
        default=0,
    )
    json_txt: StringProperty(
        name="",
        subtype='FILE_NAME',
    )
    designated: BoolProperty(
        default=True,
    )

    designated: BoolProperty(
        default=True,
    )
    Copy_the_file: BoolProperty(
        default=True,
    )
    Preset_editor: BoolProperty(
        default=False
    )
    Reference_bones: BoolProperty(
        default=False
    )
    f_pin: BoolProperty(
        default=True,
    )
    Finger_options: BoolProperty(
        default=False,
    )
    Upper_body_linkage: BoolProperty(
        default=False,
    )
    Thumb_twist_aligns_with_the_world_Z_axis: BoolProperty(
        default=False,
    )
    # 隐藏骨架
    Hide_mmd_skeleton: BoolProperty(
        default=False,
    )
    # 弯曲腿部骨骼
    Bend_the_leg_bones: BoolProperty(
        default=False,
        description="弯曲腿部骨骼"
    )
    # 弯曲角度（腿部）
    Bend_angle_leg: FloatProperty(
        default=2.5,
    )
    # 弯曲角度（手臂）
    Bend_angle_arm: FloatProperty(
        default=6,
    )
    # 使用ITASC解算器
    Use_ITASC_solver: BoolProperty(
        default=False,
        description="IK解算器使用ITASC算法,最精确,但要弯曲四肢骨骼"
    )
    # ORG模式
    ORG_mode: BoolProperty(
        default=False,
        description="使用 MMR 1.20版的约束算法"
    )
