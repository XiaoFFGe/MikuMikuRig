import os
import bpy
from mathutils import Matrix
from mathutils import Vector

class MMR_redirect(bpy.types.Operator):
    """ Import FBX actions """
    bl_idname = 'object.mmr_redirect'
    bl_label = 'Import FBX actions'
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    # 文件路径属性
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={'HIDDEN'}
    )

    def execute(self, context):

        mmr = context.object.mmr

        # 获取当前运行的Py文件的路径
        current_file_path = __file__
        # 获取当前Py文件所在的文件夹路径
        new_path = os.path.dirname(current_file_path)

        # 获取当前活动对象
        arm = bpy.context.active_object
        # 检查是否为骨架
        if arm.type != 'ARMATURE':
            self.report({'ERROR'}, '请选择一个骨架')
            return {'CANCELLED'}

        # 记住开始帧
        start_frame1 = bpy.context.scene.frame_start
        # 记住结束帧
        end_frame1 = bpy.context.scene.frame_end
        # 记住当前帧
        current_frame1 = bpy.context.scene.frame_current

        bpy.ops.object.mode_set(mode='POSE')  # 进入姿态模式

        ik_fk = ["upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.R","thigh_parent.L" ]

        for i in ik_fk:
            arm.pose.bones[i]["IK_FK"] = 1  # 设置IK_FK属性为1

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False  # 禁用自动插帧

        # 记住arm的变换
        arm_matrix_world = arm.matrix_world.copy()

        # 获取'torso_root'骨骼变换
        torso_root = arm.pose.bones['torso_root']
        # 复制'torso_root'的变换信息
        torso_root_copy = {
            "location": torso_root.location.copy(),
            "rotation_quaternion": torso_root.rotation_quaternion.copy(),
            "rotation_euler": torso_root.rotation_euler.copy(),
            "scale": torso_root.scale.copy()
        }

        # 获取'root'骨骼变换
        root = arm.pose.bones['root']
        # 复制'root'的变换信息
        root_copy = {
            "location": root.location.copy(),
            "rotation_quaternion": root.rotation_quaternion.copy(),
            "rotation_euler": root.rotation_euler.copy(),
            "scale": root.scale.copy()
        }

        # 清空变换
        torso_root.location = (0, 0, 0)
        torso_root.rotation_quaternion = (1, 0, 0, 0)
        torso_root.rotation_euler = (0, 0, 0)
        torso_root.scale = (1, 1, 1)

        root.location = (0, 0, 0)
        root.rotation_quaternion = (1, 0, 0, 0)
        root.rotation_euler = (0, 0, 0)
        root.scale = (1, 1, 1)

        # 清空arm的旋转
        arm.rotation_euler = (0, 0, 0)
        arm.rotation_quaternion = (1, 0, 0, 0)

        # 編輯模式
        bpy.ops.object.mode_set(mode='EDIT')

        # 获取'torso'骨骼父级
        torso_parent_copy = arm.data.edit_bones['torso'].parent
        if torso_parent_copy is None:
            print("'torso'骨骼没有父级")
        else:
            torso_parent_copy = torso_parent_copy.name  # 获取父级的名称

        # 获取'root'骨骼父级
        root_parent_copy = arm.data.edit_bones['root'].parent
        if root_parent_copy is None:
            print("'root'骨骼没有父级")
        else:
            root_parent_copy = root_parent_copy.name  # 获取父级的名称

        # 清空骨骼父级
        arm.data.edit_bones['torso'].parent = None
        arm.data.edit_bones['root'].parent = None

        # 导入FBX文件
        bpy.ops.import_scene.fbx(filepath=self.filepath)
        # 获取FBX文件名称
        fbx_name = os.path.basename(self.filepath)
        # 移除扩展名
        fbx_name = os.path.splitext(fbx_name)[0]

        # 从当前选择的东西获取骨架
        for obj in bpy.context.selected_objects:
            # 删掉除了骨架之外的物体
            if obj.type == 'ARMATURE':
                fbx_arm = obj
            else:
                bpy.data.objects.remove(obj)  # 删除非骨架物体

        # fbx_arm 移动到 arm 的位置
        fbx_arm.matrix_world.translation = arm.matrix_world.translation

        # fbx_arm 的骨骼动画帧范围
        start_frame = fbx_arm.animation_data.action.frame_range[0]
        end_frame = fbx_arm.animation_data.action.frame_range[1]

        print('帧范围：',start_frame, '///', end_frame)

        # 取消选择所有物体
        for obj in bpy.context.selected_objects:
            obj.select_set(False)

        # 激活 arm
        bpy.context.view_layer.objects.active = arm
        arm.select_set(True)

        bpy.context.scene.mmr_kumopult_bac_owner = arm  # 选择目标骨架
        arm.data.mmr_kumopult_bac.selected_target = fbx_arm  # 选择要复制的骨架

        target_script = os.path.join(new_path, 'presets', mmr.py_presets + '.py')  # 目标脚本路径

        bpy.ops.script.python_file_run(filepath=target_script)  # 运行脚本

        bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式
        # 设置骨骼父级
        arm.data.edit_bones['root'].parent = arm.data.edit_bones.get('torso')
        # 不要继承父级的变换
        arm.data.edit_bones['root'].use_inherit_rotation = False
        arm.data.edit_bones['root'].inherit_scale = 'NONE'

        bpy.ops.object.mode_set(mode="POSE")  # 进入姿态模式
        # 记住root骨骼的世界变换
        root_world_matrix_copy = arm.pose.bones['root'].matrix.copy()

        bpy.ops.object.mode_set(mode="EDIT")  # 进入编辑模式
        # 恢复root骨骼的父级
        if root_parent_copy is None:
            arm.data.edit_bones['root'].parent = None
        else:
            arm.data.edit_bones['root'].parent = arm.data.edit_bones.get(root_parent_copy)
        # 恢复torso骨骼的父级
        if torso_parent_copy is None:
            arm.data.edit_bones['torso'].parent = None
        else:
            arm.data.edit_bones['torso'].parent = arm.data.edit_bones.get(torso_parent_copy)

        bpy.ops.object.mode_set(mode="POSE")  # 进入姿态模式
        arm.pose.bones['root'].matrix = root_world_matrix_copy  # 恢复root骨骼的世界变换

        # 配置参数
        ARMATURE_NAME = arm.name  # 骨架名称
        BONE_NAMES = [ 'head', 'torso', 'chest', "ORG-heel.02.R", "ORG-heel.02.L",'ORG-hand.R', 'ORG-hand.L',
                      'ORG-forearm.R','ORG-forearm.L','ORG-shin.R','ORG-shin.L','ORG-toe.R','ORG-toe.L']  # 需要监控的骨骼名称
        START_FRAME = int(start_frame)  # 起始帧
        END_FRAME = int(end_frame)  # 结束帧
        SCAN_PHASES = [100, 50, 25, 10, 5, 2, 1]  # 多级扫描相位

        # 获取骨架对象
        armature = bpy.data.objects.get(ARMATURE_NAME)
        if not armature or armature.type != 'ARMATURE':
            raise Exception(f"未找到骨架: {ARMATURE_NAME}")

        # 验证骨骼存在性
        bones = []
        for name in BONE_NAMES:
            bone = armature.pose.bones.get(name)
            if not bone:
                raise Exception(f"骨骼不存在: {name}")
            bones.append(bone)

        # 初始化跟踪数据
        global_min_z = float('inf')
        global_min_frame = None
        global_min_bones = []

        # 多级扫描流程
        current_start = START_FRAME
        current_end = END_FRAME

        for phase, step in enumerate(SCAN_PHASES, 1):
            # 生成当前相位扫描范围
            scan_frames = []
            frame = current_start
            while frame <= current_end:
                scan_frames.append(frame)
                frame += step

            # 确保包含端点
            if scan_frames and scan_frames[-1] != current_end:
                scan_frames.append(current_end)

            print(f"\n=== 相位 {phase} (步长 {step}) ===")
            print(f"扫描范围: {current_start}-{current_end}")
            print(f"检测帧: {scan_frames}")

            # 遍历当前相位的所有帧
            for frame in scan_frames:
                bpy.context.scene.frame_set(frame)
                bpy.context.view_layer.update()

                # 获取双骨骼位置数据
                frame_data = []
                for bone in bones:
                    world_matrix = armature.matrix_world @ bone.matrix
                    z_pos = world_matrix.translation.z
                    frame_data.append(z_pos)

                # 计算本帧最低值
                current_min_z = min(frame_data)
                current_min_bones = [BONE_NAMES[i] for i, z in enumerate(frame_data) if z == current_min_z]

                # 更新全局记录
                update_flag = False
                if current_min_z < global_min_z:
                    update_flag = True
                elif current_min_z == global_min_z and frame < global_min_frame:
                    update_flag = True  # 相同Z值时取更早的帧

                if update_flag:
                    global_min_z = current_min_z
                    global_min_frame = frame
                    global_min_bones = current_min_bones
                    print(f"帧 {frame:3d}: 新最低 Z={global_min_z:.4f} ({', '.join(global_min_bones)})")

            # 更新下一相位范围
            if global_min_frame is not None:
                new_start = max(START_FRAME, global_min_frame - step)
                new_end = min(END_FRAME, global_min_frame + step)
                current_start, current_end = new_start, new_end

        # 最终精确扫描 (步长1)
        if current_start < current_end:
            print("\n=== 最终精确扫描 ===")
            for frame in range(current_start, current_end + 1):
                bpy.context.scene.frame_set(frame)
                bpy.context.view_layer.update()

                frame_data = []
                for bone in bones:
                    world_matrix = armature.matrix_world @ bone.matrix
                    z_pos = world_matrix.translation.z
                    frame_data.append(z_pos)
                    print(f"帧 {frame}: {bone.name} Z={z_pos:.4f}")

                current_min_z = min(frame_data)
                current_min_bones = [BONE_NAMES[i] for i, z in enumerate(frame_data) if z == current_min_z]

                if current_min_z < global_min_z or (current_min_z == global_min_z and frame < global_min_frame):
                    global_min_z = current_min_z
                    global_min_frame = frame
                    global_min_bones = current_min_bones
                    print(f"精确扫描帧 {frame}: Z={global_min_z:.4f}")

        # 输出结果
        if global_min_frame:
            print(f"\n===== 最终结果 =====")
            print(f"最低位置帧 : {global_min_frame}")
            print(f"Z轴坐标     : {global_min_z:.6f}")
            print(f"涉及骨骼    : {', '.join(global_min_bones)}")
            bpy.context.scene.frame_set(global_min_frame)  # 跳转到关键帧
        else:
            print("未找到有效数据")

        # 配置参数
        ARMATURE_NAME = arm.name  # 骨架名称
        BONE_NAMES = global_min_bones  # 涉及骨骼
        START_FRAME = int(start_frame)  # 起始帧
        END_FRAME = int(end_frame)  # 结束帧
        ERROR = 0.05  # 允许的误差范围

        z_values = []

        # 获取骨架对象
        arm_obj = bpy.data.objects.get(ARMATURE_NAME)
        if not arm_obj:
            raise ValueError(f"Armature '{ARMATURE_NAME}' not found")

        # 确保在对象模式下更新骨骼矩阵
        original_mode = bpy.context.object.mode
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 遍历每一帧
        for frame in range(START_FRAME, END_FRAME + 1):
            # 设置当前帧
            bpy.context.scene.frame_set(frame)
            # 更新视图层以确保骨骼矩阵正确
            bpy.context.view_layer.update()

            # 遍历每个骨骼名称
            for bone_name in BONE_NAMES:
                pose_bone = arm_obj.pose.bones.get(bone_name)
                if not pose_bone:
                    print(f"Bone '{bone_name}' not found in armature")
                    continue

                # 计算骨骼的世界空间位置
                bone_global_matrix = arm_obj.matrix_world @ pose_bone.matrix
                global_z = bone_global_matrix.translation.z
                z_values.append(global_z)

        # 恢复原始模式
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=original_mode)

        if not z_values:
            print("No Z values collected")
            return 0.0

        # --- 分桶统计法 ---
        bucket_width = ERROR * 2  # 桶宽度为误差的两倍（覆盖全区间）
        min_z = min(z_values)
        max_z = max(z_values)

        # 初始化分桶字典：键为桶编号，值为(点数总和, 点数)
        buckets = {}
        for z in z_values:
            # 计算当前Z值所属的桶编号
            bucket_key = int((z - min_z) // bucket_width)
            if bucket_key not in buckets:
                buckets[bucket_key] = [0.0, 0]  # [总和, 数量]
            buckets[bucket_key][0] += z
            buckets[bucket_key][1] += 1

        # 找到点数最多的桶
        max_count = 0
        best_z = min_z  # 默认取最小值
        for key in buckets:
            total_z, count = buckets[key]
            if count > max_count or (count == max_count and abs(total_z / count) < abs(best_z)):
                max_count = count
                # 计算该桶的平均高度
                best_z = total_z / count

        print(f"最佳Z值: {best_z:.6f}")
        print(f"点数最多的桶: {max_count}")

        root.matrix.translation.z = best_z  # 设置root的Z轴位置

        # 烘培动画
        bpy.ops.pose.select_all(action='DESELECT')  # 取消选择所有骨骼

        # 检查所有的骨骼，如果有名称为"BAC_ROT_COPY"的骨骼约束，则选中
        armature = arm
        for bone in armature.pose.bones:
            for constraint in bone.constraints:
                if constraint.name == "BAC_ROT_COPY":
                    bone.bone.select = True
                    break

        bpy.ops.nla.bake(frame_start=int(start_frame), frame_end=int(end_frame), visual_keying=True, bake_types={'POSE'})

        # 清空root变换
        root.location = (0, 0, 0)
        root.rotation_quaternion = (1, 0, 0, 0)
        root.rotation_euler = (0, 0, 0)
        root.scale = (1, 1, 1)

        # 删除列表中的约束
        del_constraints = ['BAC_ROT_COPY', 'BAC_ROT_ROLL', 'BAC_LOC_COPY', 'BAC_IK']
        for bone in armature.pose.bones:
            for constraint in bone.constraints:
                if constraint.name in del_constraints:
                    bone.constraints.remove(constraint)

        # 获取烘焙后的动作
        if armature.animation_data:
            baked_action = armature.animation_data.action
            if baked_action:
                baked_action.name = fbx_name  # 重命名动作
                # 取消关联动作
                armature.animation_data.action = None
                print("已烘焙动作:", baked_action.name)

        area_type = context.area.type  # 保存当前区域类型

        # 临时切换到非线性动画
        context.area.type = 'NLA_EDITOR'
        # 新建一个NLA轨道
        nla_track = context.object.animation_data.nla_tracks.new()
        nla_track.name = baked_action.name  # 重命名轨道
        # 在NLA轨道上添加动作
        nla_strip = nla_track.strips.new(nla_track.name, int(start_frame), baked_action)
        nla_strip.extrapolation = 'NOTHING'
        nla_strip.blend_type = 'REPLACE'

        # 恢复原来ui界面
        context.area.type = area_type

        bpy.data.objects.remove(fbx_arm)  # 删除

        # 恢复'torso_root'的变换
        torso_root.location = torso_root_copy["location"]
        torso_root.rotation_quaternion = torso_root_copy["rotation_quaternion"]
        torso_root.rotation_euler = torso_root_copy["rotation_euler"]
        torso_root.scale = torso_root_copy["scale"]
        # 恢复'root'的变换
        root.location = root_copy["location"]
        root.rotation_quaternion = root_copy["rotation_quaternion"]
        root.rotation_euler = root_copy["rotation_euler"]
        root.scale = root_copy["scale"]

        # 恢复arm的变换
        arm.matrix_world = arm_matrix_world.copy()

        bpy.context.scene.mmr_kumopult_bac_owner = None

        # 恢复开始帧
        bpy.context.scene.frame_start = int(start_frame1)
        # 恢复结束帧
        bpy.context.scene.frame_end = int(end_frame1)
        # 恢复当前帧
        bpy.context.scene.frame_current = int(current_frame1)

        return {'FINISHED'}

    def invoke(self, context, event):
        # 弹出文件选择对话框
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MMR_Import_VMD(bpy.types.Operator):
    """ Import VMD actions """
    bl_idname = 'object.mmr_import_vmd'
    bl_label = 'Import VMD actions'
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    # 文件路径属性
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(
        default="*.vmd",
        options={'HIDDEN'}
    )

    def execute(self, context):

        def Size_settings(A, B):
            obj_a = A
            obj_b = B

            bpy.ops.object.mode_set(mode='OBJECT')  # 进入物体模式

            if obj_a and obj_b:
                # 获取目标Z轴尺寸和当前Z轴尺寸
                target_z = obj_b.dimensions.z
                current_z = obj_a.dimensions.z

                # 避免除以零错误
                if current_z == 0:
                    print("Error: 物体A的Z轴尺寸为0，无法缩放")
                    return

                if target_z == current_z:
                    print('尺寸相同，无法缩放')
                    return

                # 直接计算缩放因子
                scale_factor = target_z / current_z

                # 应用缩放因子到所有轴向（保持比例）
                obj_a.scale *= scale_factor

                # 更新视图层以确保尺寸计算准确
                bpy.context.view_layer.update()

                # 应用缩放变换
                bpy.ops.object.select_all(action='DESELECT')
                obj_a.select_set(True)
                bpy.context.view_layer.objects.active = obj_a
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        mmr = context.object.mmr

        # 获取当前运行的Py文件的路径
        current_file_path = __file__
        # 获取当前Py文件所在的文件夹路径
        new_path = os.path.dirname(current_file_path)

        # 获取当前活动对象
        arm = bpy.context.active_object
        # 检查是否为骨架
        if arm.type != 'ARMATURE':
            self.report({'ERROR'}, '请选择一个骨架')
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')  # 进入物体模式

        blend_file_path = os.path.join(new_path, 'MMR_Leb.blend')

        # 记住开始帧
        start_frame1 = bpy.context.scene.frame_start
        # 记住结束帧
        end_frame1 = bpy.context.scene.frame_end
        # 记住当前帧
        current_frame1 = bpy.context.scene.frame_current

        # 设置追加参数
        filepath = os.path.join(blend_file_path, "Object", "MMR_leg_VMD_arm")
        directory = os.path.join(blend_file_path, "Object")
        filename = "MMR_leg_VMD_arm"

        # 执行追加操作
        if bpy.data.objects.get('MMR_leg_VMD_arm') is None:
            bpy.ops.wm.append(
                filepath=filepath,
                directory=directory,
                filename=filename,
            )

        fbx_arm = bpy.data.objects['MMR_leg_VMD_arm']

        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False  # 禁用自动插帧

        # 记住arm的变换
        arm_matrix_world = arm.matrix_world.copy()

        # 获取'torso_root'骨骼变换
        torso_root = arm.pose.bones['torso_root']
        # 复制'torso_root'的变换信息
        torso_root_copy = {
            "location": torso_root.location.copy(),
            "rotation_quaternion": torso_root.rotation_quaternion.copy(),
            "rotation_euler": torso_root.rotation_euler.copy(),
            "scale": torso_root.scale.copy()
        }

        # 获取'root'骨骼变换
        root = arm.pose.bones['root']
        # 复制'root'的变换信息
        root_copy = {
            "location": root.location.copy(),
            "rotation_quaternion": root.rotation_quaternion.copy(),
            "rotation_euler": root.rotation_euler.copy(),
            "scale": root.scale.copy()
        }

        # 清空变换
        torso_root.location = (0, 0, 0)
        torso_root.rotation_quaternion = (1, 0, 0, 0)
        torso_root.rotation_euler = (0, 0, 0)
        torso_root.scale = (1, 1, 1)

        root.location = (0, 0, 0)
        root.rotation_quaternion = (1, 0, 0, 0)
        root.rotation_euler = (0, 0, 0)
        root.scale = (1, 1, 1)

        # 清空arm的旋转
        arm.rotation_euler = (0, 0, 0)
        arm.rotation_quaternion = (1, 0, 0, 0)

        bpy.ops.object.mode_set(mode='POSE')  # 进入姿态模式

        # 清空arm骨架变换
        bpy.context.view_layer.objects.active = arm
        arm.select_set(True)
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()

        # 缩放
        Size_settings(fbx_arm,arm)

        bpy.ops.object.mode_set(mode='POSE')

        foot_bones = {'foot_fk.L': '足首.L', 'foot_fk.R': '足首.R', 'toe.L': '足先EX.L', 'toe.R': '足先EX.R'}

        for key, value in foot_bones.items():
            print(f"键名: {key}, 值: {value}")
            bpy.context.view_layer.update()  # 更新视图层
            # 获取骨骼
            bone_a = fbx_arm.pose.bones.get(value)
            bone_b = arm.pose.bones.get(key)

            if bone_a and bone_b:

                bone_b_location = bone_a.location.copy()  # 复制位置
                bone_b_scale = bone_a.scale.copy()  # 复制缩放

                bone_a.matrix = bone_b.matrix.copy()

                bone_a.location = bone_b_location  # 恢复位置
                bone_a.scale = bone_b_scale  # 恢复缩放
                bpy.ops.pose.armature_apply(selected=False)

        bpy.context.view_layer.objects.active = arm
        arm.select_set(True)

        ik_fk = ["upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.R","thigh_parent.L" ]

        for i in ik_fk:
            arm.pose.bones[i]["IK_FK"] = 1  # 设置IK_FK属性为1

        # 編輯模式
        bpy.ops.object.mode_set(mode='EDIT')

        # 获取'torso'骨骼父级
        torso_parent_copy = arm.data.edit_bones['torso'].parent
        if torso_parent_copy is None:
            print("'torso'骨骼没有父级")
        else:
            torso_parent_copy = torso_parent_copy.name  # 获取父级的名称

        # 获取'root'骨骼父级
        root_parent_copy = arm.data.edit_bones['root'].parent
        if root_parent_copy is None:
            print("'root'骨骼没有父级")
        else:
            root_parent_copy = root_parent_copy.name  # 获取父级的名称

        # 清空骨骼父级
        arm.data.edit_bones['torso'].parent = None
        arm.data.edit_bones['root'].parent = None

        # 获取FBX文件名称
        fbx_name = os.path.basename(self.filepath)
        # 移除扩展名
        fbx_name = os.path.splitext(fbx_name)[0]

        bpy.context.view_layer.objects.active = fbx_arm  # 激活目标对象
        fbx_arm.select_set(True)

        # 导入VMD文件
        file_path = str(self.filepath)
        file_name = os.path.basename(file_path)
        new_path1 = os.path.dirname(file_path)

        bpy.ops.mmd_tools.import_vmd(filepath=file_path,
                                         files=[{"name": file_name, "name": file_name}],
                                         directory=new_path1)

        # fbx_arm 移动到 arm 的位置
        fbx_arm.matrix_world.translation = arm.matrix_world.translation

        # fbx_arm 的骨骼动画帧范围
        start_frame = fbx_arm.animation_data.action.frame_range[0]
        end_frame = fbx_arm.animation_data.action.frame_range[1]

        print('帧范围：',start_frame, '///', end_frame)

        # 取消选择所有物体
        for obj in bpy.context.selected_objects:
            obj.select_set(False)

        # 激活 arm
        bpy.context.view_layer.objects.active = arm
        arm.select_set(True)

        bpy.context.scene.mmr_kumopult_bac_owner = arm  # 选择目标骨架
        arm.data.mmr_kumopult_bac.selected_target = fbx_arm  # 选择要复制的骨架

        target_script = os.path.join(new_path, 'MMR_OP_Presets', 'MMR_VMD.py')  # 目标脚本路径

        bpy.ops.script.python_file_run(filepath=target_script)  # 运行脚本

        bpy.ops.object.mode_set(mode='EDIT')  # 进入编辑模式
        # 设置骨骼父级
        arm.data.edit_bones['root'].parent = arm.data.edit_bones.get('torso')
        # 不要继承父级的变换
        arm.data.edit_bones['root'].use_inherit_rotation = False
        arm.data.edit_bones['root'].inherit_scale = 'NONE'

        bpy.ops.object.mode_set(mode="POSE")  # 进入姿态模式
        # 记住root骨骼的世界变换
        root_world_matrix_copy = arm.pose.bones['root'].matrix.copy()

        bpy.ops.object.mode_set(mode="EDIT")  # 进入编辑模式
        # 恢复root骨骼的父级
        if root_parent_copy is None:
            arm.data.edit_bones['root'].parent = None
        else:
            arm.data.edit_bones['root'].parent = arm.data.edit_bones.get(root_parent_copy)
        # 恢复torso骨骼的父级
        if torso_parent_copy is None:
            arm.data.edit_bones['torso'].parent = None
        else:
            arm.data.edit_bones['torso'].parent = arm.data.edit_bones.get(torso_parent_copy)

        bpy.ops.object.mode_set(mode="POSE")  # 进入姿态模式
        arm.pose.bones['root'].matrix = root_world_matrix_copy  # 恢复root骨骼的世界变换

        # 配置参数
        ARMATURE_NAME = arm.name  # 骨架名称
        BONE_NAMES = [ 'head', 'torso', 'chest', "ORG-heel.02.R", "ORG-heel.02.L",'ORG-hand.R', 'ORG-hand.L',
                      'ORG-forearm.R','ORG-forearm.L','ORG-shin.R','ORG-shin.L','ORG-toe.R','ORG-toe.L']  # 需要监控的骨骼名称
        START_FRAME = int(start_frame)  # 起始帧
        END_FRAME = int(end_frame)  # 结束帧
        SCAN_PHASES = [100, 50, 25, 10, 5, 2, 1]  # 多级扫描相位

        # 获取骨架对象
        armature = bpy.data.objects.get(ARMATURE_NAME)
        if not armature or armature.type != 'ARMATURE':
            raise Exception(f"未找到骨架: {ARMATURE_NAME}")

        # 验证骨骼存在性
        bones = []
        for name in BONE_NAMES:
            bone = armature.pose.bones.get(name)
            if not bone:
                raise Exception(f"骨骼不存在: {name}")
            bones.append(bone)

        # 初始化跟踪数据
        global_min_z = float('inf')
        global_min_frame = None
        global_min_bones = []

        # 多级扫描流程
        current_start = START_FRAME
        current_end = END_FRAME

        for phase, step in enumerate(SCAN_PHASES, 1):
            # 生成当前相位扫描范围
            scan_frames = []
            frame = current_start
            while frame <= current_end:
                scan_frames.append(frame)
                frame += step

            # 确保包含端点
            if scan_frames and scan_frames[-1] != current_end:
                scan_frames.append(current_end)

            print(f"\n=== 相位 {phase} (步长 {step}) ===")
            print(f"扫描范围: {current_start}-{current_end}")
            print(f"检测帧: {scan_frames}")

            # 遍历当前相位的所有帧
            for frame in scan_frames:
                bpy.context.scene.frame_set(frame)
                bpy.context.view_layer.update()

                # 获取双骨骼位置数据
                frame_data = []
                for bone in bones:
                    world_matrix = armature.matrix_world @ bone.matrix
                    z_pos = world_matrix.translation.z
                    frame_data.append(z_pos)

                # 计算本帧最低值
                current_min_z = min(frame_data)
                current_min_bones = [BONE_NAMES[i] for i, z in enumerate(frame_data) if z == current_min_z]

                # 更新全局记录
                update_flag = False
                if current_min_z < global_min_z:
                    update_flag = True
                elif current_min_z == global_min_z and frame < global_min_frame:
                    update_flag = True  # 相同Z值时取更早的帧

                if update_flag:
                    global_min_z = current_min_z
                    global_min_frame = frame
                    global_min_bones = current_min_bones
                    print(f"帧 {frame:3d}: 新最低 Z={global_min_z:.4f} ({', '.join(global_min_bones)})")

            # 更新下一相位范围
            if global_min_frame is not None:
                new_start = max(START_FRAME, global_min_frame - step)
                new_end = min(END_FRAME, global_min_frame + step)
                current_start, current_end = new_start, new_end

        # 最终精确扫描 (步长1)
        if current_start < current_end:
            print("\n=== 最终精确扫描 ===")
            for frame in range(current_start, current_end + 1):
                bpy.context.scene.frame_set(frame)
                bpy.context.view_layer.update()

                frame_data = []
                for bone in bones:
                    world_matrix = armature.matrix_world @ bone.matrix
                    z_pos = world_matrix.translation.z
                    frame_data.append(z_pos)
                    print(f"帧 {frame}: {bone.name} Z={z_pos:.4f}")

                current_min_z = min(frame_data)
                current_min_bones = [BONE_NAMES[i] for i, z in enumerate(frame_data) if z == current_min_z]

                if current_min_z < global_min_z or (current_min_z == global_min_z and frame < global_min_frame):
                    global_min_z = current_min_z
                    global_min_frame = frame
                    global_min_bones = current_min_bones
                    print(f"精确扫描帧 {frame}: Z={global_min_z:.4f}")

        # 输出结果
        if global_min_frame:
            print(f"\n===== 最终结果 =====")
            print(f"最低位置帧 : {global_min_frame}")
            print(f"Z轴坐标     : {global_min_z:.6f}")
            print(f"涉及骨骼    : {', '.join(global_min_bones)}")
            bpy.context.scene.frame_set(global_min_frame)  # 跳转到关键帧
        else:
            print("未找到有效数据")

        # 配置参数
        ARMATURE_NAME = arm.name  # 骨架名称
        BONE_NAMES = global_min_bones   # 涉及骨骼
        START_FRAME = int(start_frame)  # 起始帧
        END_FRAME = int(end_frame)  # 结束帧
        ERROR = 0.05  # 允许的误差范围

        z_values = []

        # 获取骨架对象
        arm_obj = bpy.data.objects.get(ARMATURE_NAME)
        if not arm_obj:
            raise ValueError(f"Armature '{ARMATURE_NAME}' not found")

        # 确保在对象模式下更新骨骼矩阵
        original_mode = bpy.context.object.mode
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 遍历每一帧
        for frame in range(START_FRAME, END_FRAME + 1):
            # 设置当前帧
            bpy.context.scene.frame_set(frame)
            # 更新视图层以确保骨骼矩阵正确
            bpy.context.view_layer.update()

            # 遍历每个骨骼名称
            for bone_name in BONE_NAMES:
                pose_bone = arm_obj.pose.bones.get(bone_name)
                if not pose_bone:
                    print(f"Bone '{bone_name}' not found in armature")
                    continue

                # 计算骨骼的世界空间位置
                bone_global_matrix = arm_obj.matrix_world @ pose_bone.matrix
                global_z = bone_global_matrix.translation.z
                z_values.append(global_z)

        # 恢复原始模式
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=original_mode)

        if not z_values:
            print("No Z values collected")
            return 0.0

        # --- 分桶统计法 ---
        bucket_width = ERROR * 2  # 桶宽度为误差的两倍（覆盖全区间）
        min_z = min(z_values)
        max_z = max(z_values)

        # 初始化分桶字典：键为桶编号，值为(点数总和, 点数)
        buckets = {}
        for z in z_values:
            # 计算当前Z值所属的桶编号
            bucket_key = int((z - min_z) // bucket_width)
            if bucket_key not in buckets:
                buckets[bucket_key] = [0.0, 0]  # [总和, 数量]
            buckets[bucket_key][0] += z
            buckets[bucket_key][1] += 1

        # 找到点数最多的桶
        max_count = 0
        best_z = min_z  # 默认取最小值
        for key in buckets:
            total_z, count = buckets[key]
            if count > max_count or (count == max_count and abs(total_z / count) < abs(best_z)):
                max_count = count
                # 计算该桶的平均高度
                best_z = total_z / count

        print(f"最佳Z值: {best_z:.6f}")
        print(f"点数最多的桶: {max_count}")

        root.matrix.translation.z = best_z  # 设置root的Z轴位置

        # 烘培动画
        bpy.ops.pose.select_all(action='DESELECT')  # 取消选择所有骨骼

        # 检查所有的骨骼，如果有名称为"BAC_ROT_COPY"的骨骼约束，则选中
        armature = arm
        for bone in armature.pose.bones:
            for constraint in bone.constraints:
                if constraint.name == "BAC_ROT_COPY":
                    bone.bone.select = True
                    break

        bpy.ops.nla.bake(frame_start=int(start_frame), frame_end=int(end_frame), visual_keying=True, bake_types={'POSE'})

        # 清空root变换
        root.location = (0, 0, 0)
        root.rotation_quaternion = (1, 0, 0, 0)
        root.rotation_euler = (0, 0, 0)
        root.scale = (1, 1, 1)

        # 删除列表中的约束
        del_constraints = ['BAC_ROT_COPY', 'BAC_ROT_ROLL', 'BAC_LOC_COPY', 'BAC_IK']
        for bone in armature.pose.bones:
            for constraint in bone.constraints:
                if constraint.name in del_constraints:
                    bone.constraints.remove(constraint)

        # 获取烘焙后的动作
        if armature.animation_data:
            baked_action = armature.animation_data.action
            if baked_action:
                baked_action.name = fbx_name  # 重命名动作
                # 取消关联动作
                armature.animation_data.action = None
                print("已烘焙动作:", baked_action.name)

        area_type = context.area.type  # 保存当前区域类型

        # 临时切换到非线性动画
        context.area.type = 'NLA_EDITOR'
        # 新建一个NLA轨道
        nla_track = context.object.animation_data.nla_tracks.new()
        nla_track.name = baked_action.name  # 重命名轨道
        # 在NLA轨道上添加动作
        nla_strip = nla_track.strips.new(nla_track.name, int(start_frame), baked_action)
        nla_strip.extrapolation = 'NOTHING'
        nla_strip.blend_type = 'REPLACE'

        # 恢复原来ui界面
        context.area.type = area_type

        bpy.data.objects.remove(fbx_arm)  # 删除

        # 恢复'torso_root'的变换
        torso_root.location = torso_root_copy["location"]
        torso_root.rotation_quaternion = torso_root_copy["rotation_quaternion"]
        torso_root.rotation_euler = torso_root_copy["rotation_euler"]
        torso_root.scale = torso_root_copy["scale"]
        # 恢复'root'的变换
        root.location = root_copy["location"]
        root.rotation_quaternion = root_copy["rotation_quaternion"]
        root.rotation_euler = root_copy["rotation_euler"]
        root.scale = root_copy["scale"]

        # 恢复arm的变换
        arm.matrix_world = arm_matrix_world.copy()

        bpy.context.scene.mmr_kumopult_bac_owner = None  # 取消选择目标骨架

        # 恢复开始帧
        bpy.context.scene.frame_start = int(start_frame1)
        # 恢复结束帧
        bpy.context.scene.frame_end = int(end_frame1)
        # 恢复当前帧
        bpy.context.scene.frame_current = int(current_frame1)

        return {'FINISHED'}

    def invoke(self, context, event):
        # 弹出文件选择对话框
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}