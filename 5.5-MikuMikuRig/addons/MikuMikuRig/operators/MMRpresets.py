import shutil
import subprocess
import bpy
import json
import os

class mmrmakepresetsOperator(bpy.types.Operator):
    '''make presets'''
    bl_idname = "object.mmr_make_presets"
    bl_label = "make presets"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    #打开文件选择器
    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'HIDDEN'}
    )
    filter_folder: bpy.props.BoolProperty(
        default=True,
        options={'HIDDEN'}
    )
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.type == 'ARMATURE':
                return True
        return False

    def execute(self, context: bpy.types.Context):

        mmr = context.object.mmr

        # 获取当前运行的Py文件的路径
        current_file_path = __file__
        # 获取当前Py文件所在的文件夹路径
        new_path = os.path.dirname(current_file_path)

        if mmr.Reference_bones:
            blend_file_path = os.path.join(new_path, 'MMR_Rig.blend')
            # 设置追加参数
            filepath = os.path.join(blend_file_path, "Object", "MMR_Rig_relative")
            directory = os.path.join(blend_file_path, "Object")
            filename = "MMR_Rig_relative"
            # 执行追加操作
            bpy.ops.wm.append(
                filepath=filepath,
                directory=directory,
                filename=filename,
            )
            mmr.Reference_bones = False
            return {'FINISHED'}

        if mmr.make_presets:
            # 初始化
            mmr.filepath = self.filepath
            mmr.make_presets = False
            mmr.number = 0
            mmr.json_txt = '按下"指定"以指定骨骼'
            mmr.designated = True
            mmr.Copy_the_file = True
            bpy.ops.mmr.import_json(filepath=os.path.join(new_path, 'MMR_Presets.json'))
        else:
            mmr.make_presets = True
            # 更新窗口
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        return {'FINISHED'}

    def invoke(self, context, event):
        mmr = context.object.mmr

        if mmr.Reference_bones:
            return self.execute(context)  # 直接执行

        if mmr.make_presets:
            if not mmr.Reference_bones:
                context.window_manager.fileselect_add(self)
        else:
            context.window_manager.invoke_props_dialog(self, width=200)

        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        mmr = context.object.mmr
        if not mmr.make_presets:
            layout.label(text='确定要退出吗？')

class mmrdesignatedOperator(bpy.types.Operator):
    '''designated presets'''
    bl_idname = "object.mmr_designated"
    bl_label = "designated"

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.type == 'ARMATURE':
                return True
        return False

    def execute(self, context: bpy.types.Context):

        mmr = context.object.mmr
        mmd_arm = bpy.context.active_object
        # 进入姿态模式
        bpy.ops.object.mode_set(mode='POSE')

        # 获取当前运行的Py文件的路径
        current_file_path = __file__
        # 获取当前Py文件所在的文件夹路径
        new_path = os.path.dirname(current_file_path)
        # 将当前文件夹路径和文件名组合成完整的文件路径
        file = 'MMR_Presets.json'
        new_file_path = os.path.join(new_path,file)
        # 读取json文件
        with open(new_file_path) as f:
            config = json.load(f)


        # 将字典config的键转换为列表
        json_keys = list(config.keys())

        if mmr.number < len(json_keys):
            # 传入数组
            fourth_key = json_keys[mmr.number]

            if mmr.designated:
                # 更新提示
                mmr.json_txt = "请选择: " + fourth_key.removeprefix('p-') + '--' + config[fourth_key]

                # 选择骨骼
                for Bone in mmd_arm.pose.bones:
                    if Bone.name == fourth_key.removeprefix('p-'):
                        mmd_arm.data.bones.active = mmd_arm.data.bones.get(fourth_key.removeprefix('p-'))
                        Bone.select = True
                        break

                print(mmr.number, fourth_key)

                mmr.designated = False

            else:
                config = {}
                # 读取json
                for item in context.scene.mmr_json:
                    config[item.key] = item.value

                # 获取当前选中的骨骼
                selected_bones = bpy.context.active_bone.name
                print("当前选中的骨骼名称:", selected_bones)

                value = config.pop(fourth_key)  # 删除旧键并获取值

                config[selected_bones] = value

                items = context.scene.mmr_json

                # 删除旧项
                for i, item in enumerate(items):
                    if item.key == fourth_key:
                        items.remove(i)
                        break

                item = items.add()
                item.key = selected_bones
                item.value = value

                context.scene.mmr_json_index = len(items) - 1 if len(items) > 0 else -1

                if mmr.number != len(json_keys) - 1:
                    # 完成指定后将数组加 1
                    mmr.number = mmr.number + 1
                    mmr.designated = True
                    bpy.ops.object.mmr_designated() # 递归调用
                else:
                    # 更新提示
                    self.report({'INFO'}, '预设位于：MMR预设编辑器/' + mmr.filepath)
                    mmr.json_txt = '预设位于：MMR预设编辑器/' + mmr.filepath
                    mmr.number = mmr.number + 1
                    mmr.designated = False
                    bpy.ops.mmr.export_json(filepath=mmr.filepath) # 导出json文件

        return {'FINISHED'}

# 导入预设
class MMR_OT_ImportPresets(bpy.types.Operator):
    '''导入json字典预设'''

    bl_idname = "mmr.import_presets"
    bl_label = "Import presets"
    bl_options = {'REGISTER', 'UNDO'}

    #打开文件选择器
    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'HIDDEN'}
    )
    filter_folder: bpy.props.BoolProperty(
        default=True,
        options={'HIDDEN'}
    )
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.type == 'ARMATURE':
                return True
        return False
    def execute(self, context):
        mmr = context.object.mmr
        if not mmr.Import_presets:
            # 导入预设
            mmr.Import_presets = True
            # 导入文件路径
            mmr.json_filepath = self.filepath
        else:
            mmr.Import_presets = False
        return {'FINISHED'}

    def invoke(self, context, event):
        mmr = context.object.mmr
        if not mmr.Import_presets:
            context.window_manager.fileselect_add(self)
        else:
            mmr.Import_presets = False
        return {'RUNNING_MODAL'}

# 重新指定骨骼
class MMR_OT_Designated(bpy.types.Operator):
    '''从MMR预设编辑器当前项，重新指定骨骼'''

    bl_idname = "mmr.designated"
    bl_label = "Designated"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.type == 'ARMATURE':
                return True
        return False

    def execute(self, context):
        mmr_json = context.scene.mmr_json
        mmr_json_index = context.scene.mmr_json_index

        item = mmr_json[mmr_json_index]

        selected_bone = bpy.context.active_bone

        item.key = selected_bone.name

        return {'FINISHED'}
