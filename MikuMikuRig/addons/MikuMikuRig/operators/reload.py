import os
import sys
import subprocess
import bpy
import json
from bpy.props import (
    StringProperty,
    CollectionProperty,
    IntProperty,BoolProperty,IntVectorProperty
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
    UIList,
)
from MikuMikuRig.addons.MikuMikuRig.panels import get_presets_directory


def open_system_folder(path):
    """跨平台打开文件夹"""
    try:
        # 检查路径是否存在
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        # 根据操作系统执行不同命令
        if sys.platform == "win32":
            os.startfile(os.path.normpath(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception as e:
        print(f"无法打开文件夹: {str(e)}")
        return False


class MMR_OT_OpenPresetFolder(Operator):
    bl_idname = "mmr.open_preset_folder"
    bl_label = "Open the presets folder"
    bl_description = "在文件浏览器中打开预设目录, 以便可以查看和编辑预设文件。"

    def execute(self, context):
        target_folder = get_presets_directory()

        # 尝试打开文件夹
        if open_system_folder(target_folder):
            self.report({'INFO'}, f"已打开文件夹: {target_folder}")
        else:
            self.report({'ERROR'}, "无法打开文件夹，请检查控制台日志")

        return {'FINISHED'}

# 定义键值对数据结构
class MMR_JSON_Item(PropertyGroup):
    key: StringProperty(name="Key", default="")
    value: StringProperty(name="Value", default="")
    is_selected: BoolProperty(name="Selected", default=False)  # 选中状态属性



# UI列表类
class MMR_UL_JsonList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):

        row = layout.row(align=True)
        # 多选复选框
        row.prop(
            item,
            "is_selected",
            text="",
            icon='CHECKBOX_HLT' if item.is_selected else 'CHECKBOX_DEHLT',
            emboss=False
        )

        # 左侧键输入
        row.prop(item, "key", text="", emboss=True)

        # 箭头分隔符 占10的宽度
        row2 = layout.row(align=True)
        # 文字居中
        row2.alignment = 'CENTER'
        row2.label(text="",icon='FORWARD')

        # 右侧值输入
        row1 = layout.row(align=True)
        row1.prop(item, "value", text="", emboss=True)

        # 处理多选逻辑
        def filter_items(self, context, data, propname):
            items = getattr(data, propname)
            selected_indices = [i for i, item in enumerate(items) if item.is_selected]

            return [], []  # 返回空列表禁用默认过滤

# 操作类
class MMR_OT_AddJsonItem(Operator):  # 添加键值对
    bl_idname = "mmr.add_json_item"
    bl_label = "Add Item"

    def execute(self, context):
        context.scene.mmr_json.add()
        return {'FINISHED'}

class MMR_OT_RemoveJsonItem(Operator):  # 移除选中的键值对
    bl_idname = "mmr.remove_json_item"
    bl_label = "Remove Selected Items"

    index: IntProperty()

    def execute(self, context):
        items = context.scene.mmr_json
        selected_indices = sorted(
            [i for i, item in enumerate(items) if item.is_selected],
            reverse=True  # 必须逆序删除避免索引错位
        )

        for idx in selected_indices:
            items.remove(idx)

        context.scene.mmr_json.remove(self.index)

        return {'FINISHED'}

# 全选
class MMR_OT_SelectAllItems(Operator):
    bl_idname = "mmr.select_all_items"
    bl_label = "Select All"

    def execute(self, context):
        for item in context.scene.mmr_json:
            item.is_selected = True
        return {'FINISHED'}

# 取消全选
class MMR_OT_DeselectAllItems(Operator):
    bl_idname = "mmr.deselect_all_items"
    bl_label = "Deselect All"

    def execute(self, context):
        for item in context.scene.mmr_json:
            item.is_selected = False
        return {'FINISHED'}

class MMR_OT_ImportJson(Operator):  # 导入JSON文件
    bl_idname = "mmr.import_json"
    bl_label = "Import presets"

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    def execute(self, context):
        with open(self.filepath, 'r', encoding='utf - 8') as f:
            data = json.load(f)

        items = context.scene.mmr_json
        items.clear()

        for k, v in data.items():
            item = items.add()
            item.key = k
            item.value = str(v)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MMR_OT_ExportJson(Operator):  # 导出JSON文件
    bl_idname = "mmr.export_json"
    bl_label = "Export presets"

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    def execute(self, context):
        data = {}
        for item in context.scene.mmr_json:
            data[item.key] = item.value
            # 文件名去掉后缀
            file_name = os.path.splitext(self.filepath)[0]
        with open(file_name + '.json', 'w',encoding='utf - 8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# 主面板
class MMR_PT_JsonEditor(Panel):
    bl_label = "MMR Preset Editor"
    bl_idname = "SCENE_PT_MMR_Rig_Fpt_Editor"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = "MMR"
    bl_parent_id = "SCENE_PT_MMR_Rig_A"

    def draw(self, context):
        layout = self.layout
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
        col.operator("mmr.select_all_items", icon='CHECKBOX_HLT',text="")
        col.operator("mmr.deselect_all_items",icon='CHECKBOX_DEHLT', text="")

        # 导入导出按钮
        row = layout.row()
        row.operator("mmr.import_json", icon='IMPORT')
        row.operator("mmr.export_json", icon='EXPORT')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.object is None:
            return False
        mmr = context.object.mmr
        return mmr.Preset_editor


def register():
    bpy.types.Scene.mmr_json = CollectionProperty(type=MMR_JSON_Item)
    bpy.types.Scene.mmr_json_index = IntProperty()

def unregister():
    del bpy.types.Scene.mmr_json
    del bpy.types.Scene.mmr_json_index
