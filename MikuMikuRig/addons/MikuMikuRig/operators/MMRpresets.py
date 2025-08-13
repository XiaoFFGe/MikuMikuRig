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
        else:
            mmr.make_presets = True

        return {'FINISHED'}

    def invoke(self, context, event):
        mmr = context.object.mmr
        if mmr.make_presets:
            if not mmr.Reference_bones:
                context.window_manager.fileselect_add(self)
            else:
                return self.execute(context)  # 直接执行
        else:
            return self.execute(context)
        return {'RUNNING_MODAL'}

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

                for bone in mmd_arm.data.bones:  # 遍历所有骨骼
                    if bone.name == fourth_key.removeprefix('p-'):
                        bone.select =True
                        mmd_arm.data.bones.active = bone

                print(mmr.number, fourth_key)

                mmr.designated = False
                return {'FINISHED'}
            else:
                # 源文件路径
                src_file = new_file_path
                # 文件路径
                dst_file = mmr.filepath
                # 目录获取
                desktop_paths = os.path.dirname(dst_file)
                # 文件名获取
                file_name = os.path.basename(dst_file)
                # 文件名去掉后缀
                file_name = os.path.splitext(file_name)[0]
                # 加后缀 .json
                file_name = file_name + '.json'
                # 目录路径 文件名
                dst_file = os.path.join(desktop_paths, file_name)

                # 复制文件
                if mmr.Copy_the_file:
                    shutil.copy(src_file, dst_file)
                    mmr.Copy_the_file = False

                json_path = os.path.join(desktop_paths, file_name)
                # 读取json文件
                with open(json_path) as f:
                    config = json.load(f)

                # 获取当前选中的骨骼
                selected_bones = bpy.context.active_bone.name
                print("当前选中的骨骼名称:", selected_bones)

                value = config.pop(fourth_key)  # 删除旧键并获取值

                config[selected_bones] = value

                items = context.scene.mmr_json
                item = items.add()
                item.key = selected_bones
                item.value = value

                # 写入json文件
                try:
                    with open(json_path, 'w', encoding='utf - 8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    self.report({'INFO'}, selected_bones + '写入成功!')
                except Exception as e:
                    print(f"写入失败, 错误原因: {e}")

                if mmr.number != len(json_keys) - 1:
                    # 更新提示
                    mmr.json_txt = 'OK! 下一个'
                    # 完成指定后将数组加 1
                    mmr.number = mmr.number + 1
                    mmr.designated = True
                else:
                    # 更新提示
                    self.report({'INFO'}, '文件位于:' + json_path)
                    mmr.json_txt = '文件位于:' + json_path
                    mmr.number = mmr.number + 1

        return {'FINISHED'}
