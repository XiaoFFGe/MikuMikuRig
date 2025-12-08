import re

import bpy
import os
import logging
import json
from math import radians
import json
import logging
import os
from math import radians
import numpy as np

from MikuMikuRig.common.class_loader.auto_load import blender_version


class polartargetOperator(bpy.types.Operator):
    '''Optimization MMD Armature'''
    bl_idname = "object.mmd_polars_target"
    bl_label = "Optimization MMD Armature"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.type == 'ARMATURE':
                return True
        return False

    def execute(self, context: bpy.types.Context):

        self.report({'INFO'}, '正在重构此功能，敬请期待！')
        mmd_arm = context.view_layer.objects.active

        print(mmd_arm.data.bones.items())


        return {'FINISHED'}

class mmrrigOperator(bpy.types.Operator):
    '''Build a controller'''
    bl_idname = "object.mmr_rig"
    bl_label = "Build a controller"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.type == 'ARMATURE':
                return True
        return False

    Towards: bpy.props.EnumProperty(
        name="",
        items=[('X', 'X', 'X'),('Y', 'Y', 'Y'),
               ('-X', '-X', '-X'),('-Y', '-Y', '-Y')],
        default='-Y',
        description = "如果模型的正面朝向-Y，就选择-Y"
    )

    def execute(self, context: bpy.types.Context):

        mmr = context.object.mmr

        # 获取当前运行的Py文件的路径
        current_file_path = __file__
        # 获取当前Py文件所在的文件夹路径
        new_path = os.path.dirname(current_file_path)
        # 将当前文件夹路径和文件名组合成完整的文件路径
        file = mmr.presets + '.json'
        new_file_path = os.path.join(new_path, 'presets', file)
        blend_file_path = os.path.join(new_path, 'MMR_Rig.blend')

        # 设置追加参数
        filepath = os.path.join(blend_file_path, "Object", "MMR_Rig_relative")
        directory = os.path.join(blend_file_path, "Object")
        filename = "MMR_Rig_relative"

        # 执行追加操作
        if bpy.data.objects.get('MMR_Rig_relative') is None:
            bpy.ops.wm.append(
                filepath=filepath,
                directory=directory,
                filename=filename,
            )

        if mmr.Import_presets:
            new_file_path = mmr.json_filepath

        # 读取json文件
        with open(new_file_path) as f:
            config = json.load(f)

        # 检测是否开启rigify
        if 'rigify' not in bpy.context.preferences.addons.keys():
            logging.info("检测到未开启rigify，已自动开启")
            bpy.ops.preferences.addon_enable(module="rigify")

        # 切换物体模式
        bpy.ops.object.mode_set(mode='OBJECT')
        # 当前活动物体名称
        mmd_arm = bpy.context.active_object
        print("当前活动骨骼名称:", mmd_arm.name)

        # 记住变换
        mmd_arm_matrix = mmd_arm.matrix_world.copy()

        # 清除旋转
        mmd_arm.rotation_euler = (0, 0, 0)

        Arm_Towards = {'X': -90, 'Y': 180, '-X': 90, '-Y': 0}
        for key, value in Arm_Towards.items():
            if key == self.Towards:
                mmd_arm.rotation_euler.z = value * (3.1415926 / 180)

            # 确保物体数据是唯一的
            if mmd_arm.data.users > 1:
                mmd_arm.data = mmd_arm.data.copy()

            # 激活物体
            bpy.context.view_layer.objects.active = mmd_arm
            mmd_arm.select_set(True)

            # 应用旋转变换
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        RIG = bpy.data.objects.get("MMR_Rig_relative")

        def check_keywords(target_string: str) -> bool:
            """
            检查目标字符串是否包含指定关键词列表中的任意一个
            :param target_string: 待检查的目标字符串
            :return: 若包含任意关键词返回True，否则返回False
            """
            keywords = {"thumb", "index", "middle", "ring", "pinky"}
            for keyword in keywords:
                if keyword in target_string:
                    return True
            return False

        # 判断字符串的左(L)右(R)
        def determine_side(s):
            parts = s.split('.')
            if len(parts) < 1:
                return None
            suffix = parts[-1].strip().upper()  # 统一转大写并去除首尾空格
            if suffix == 'L':
                return True
            elif suffix == 'R':
                return False
            else:
                return None

        def get_bone_world_rotation(armature_obj, bone_name):
            # 获取骨骼对象
            bone = armature_obj.pose.bones.get(bone_name)
            if bone is None:
                print(f"骨骼 {bone_name} 未找到。")
                return None

            # 获取骨骼的矩阵
            bone_matrix = armature_obj.matrix_world @ bone.matrix

            # 获取旋转部分(四元数)
            rotation = bone_matrix.to_quaternion()

            # 将四元数转换为欧拉角(弧度)
            euler_rotation = rotation.to_euler()

            return euler_rotation

        # 对齐骨骼roll
        def align_bones_roll(A, D, B, C):
            # A骨骼(D骨架),B骨骼(C骨架)
            # 获取 D 骨架和 C 骨架对象
            D_armature_obj = bpy.data.objects.get(D)
            C_armature_obj = bpy.data.objects.get(C)

            if not D_armature_obj or not C_armature_obj:
                print("未找到 D 骨架或 C 骨架对象，请检查名称。")
                return

            if D_armature_obj.type != 'ARMATURE' or C_armature_obj.type != 'ARMATURE':
                print("D 或 C 对象不是骨架类型，请检查。")
                return

            # 进入 D 骨架的编辑模式
            bpy.context.view_layer.objects.active = D_armature_obj
            bpy.ops.object.mode_set(mode='EDIT')
            D_edit_bones = D_armature_obj.data.edit_bones

            # 进入 C 骨架的编辑模式
            bpy.context.view_layer.objects.active = C_armature_obj
            bpy.ops.object.mode_set(mode='EDIT')
            C_edit_bones = C_armature_obj.data.edit_bones

            # 获取 A 骨骼和 B 骨骼
            A_bone = D_edit_bones.get(A)
            B_bone = C_edit_bones.get(B)

            if not A_bone or not B_bone:
                print(f"未找到 {A} 骨骼或 {B} 骨骼，请检查名称。")
                bpy.ops.object.mode_set(mode='OBJECT')
                return

            B_bone.roll = A_bone.roll

        # 对齐骨骼
        def align_bones(A, D, B, C, Compare_Boolean=False, count = False):
            # A骨骼(D骨架),B骨骼(C骨架)
            # 获取 D 骨架和 C 骨架对象
            D_armature_obj = bpy.data.objects.get(D)
            C_armature_obj = bpy.data.objects.get(C)

            if not D_armature_obj or not C_armature_obj:
                print("未找到 D 骨架或 C 骨架对象，请检查名称。")
                return

            if D_armature_obj.type != 'ARMATURE' or C_armature_obj.type != 'ARMATURE':
                print("D 或 C 对象不是骨架类型，请检查。")
                return

            # 进入 D 骨架的编辑模式
            bpy.context.view_layer.objects.active = D_armature_obj
            bpy.ops.object.mode_set(mode='EDIT')
            D_edit_bones = D_armature_obj.data.edit_bones

            # 进入 C 骨架的编辑模式
            bpy.context.view_layer.objects.active = C_armature_obj
            bpy.ops.object.mode_set(mode='EDIT')
            C_edit_bones = C_armature_obj.data.edit_bones

            # 获取 A 骨骼和 B 骨骼
            A_bone = D_edit_bones.get(A)
            B_bone = C_edit_bones.get(B)

            if not A_bone or not B_bone:
                print(f"未找到 {A} 骨骼或 {B} 骨骼，请检查名称。")
                bpy.ops.object.mode_set(mode='OBJECT')
                return False
            else:
                if count:
                    return True

            # 转换 B 骨骼的头和尾坐标到世界空间
            world_matrix_C = C_armature_obj.matrix_world
            world_head_B = world_matrix_C @ B_bone.head
            world_tail_B = world_matrix_C @ B_bone.tail

            # 转换世界空间坐标到 D 骨架的局部空间
            world_matrix_D = D_armature_obj.matrix_world
            local_matrix_D = world_matrix_D.inverted()
            local_head_B = local_matrix_D @ world_head_B
            local_tail_B = local_matrix_D @ world_tail_B

            if Compare_Boolean:
                if local_head_B[2] < local_tail_B[2]:
                    return False
                else:
                    return True

            # 设置 A 骨骼的头和尾
            if A == 'spine':
                if local_head_B[2] < local_tail_B[2]:
                    A_bone.head = local_head_B
                    A_bone.tail = local_tail_B
                else:
                    A_bone.head = local_tail_B
                    A_bone.tail = local_head_B
            else:
                A_bone.head = local_head_B
                A_bone.tail = local_tail_B

            # 退出编辑模式
            bpy.ops.object.mode_set(mode='OBJECT')

        def move_bone_a_to_b(d_armature_name, c_armature_name, bone_a_name, bone_b_name, A_bone_Z_location = False):

            # 获取 D 骨架和 C 骨架对象
            d_armature_obj = bpy.data.objects.get(d_armature_name)
            c_armature_obj = bpy.data.objects.get(c_armature_name)

            if d_armature_obj and c_armature_obj:
                # 确保 D 骨架和 C 骨架处于姿态模式
                for obj in [d_armature_obj, c_armature_obj]:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.mode_set(mode='POSE')

                # 获取 A 骨骼和 B 骨骼
                bone_A = d_armature_obj.pose.bones.get(bone_a_name)
                bone_B = c_armature_obj.pose.bones.get(bone_b_name)

                if bone_A and bone_B:
                    # 下面的注释是Ai写的,不能全信
                    # 使用矩阵操作（如需同时处理位置和旋转）
                    # 1. 计算骨骼 B 的世界矩阵（包含位置、旋转、缩放）
                    world_matrix_b = c_armature_obj.matrix_world @ bone_B.matrix  # 补充此处定义

                    # 2. 分解骨骼 A 的原有旋转、Z位置和缩放（避免被覆盖）
                    original_rot = bone_A.rotation_quaternion.copy()
                    original_scale = bone_A.scale.copy()
                    A_bone_Z = bone_A.location.z

                    # 3. 设置骨骼 A 的局部矩阵（世界矩阵反转为局部空间）
                    bone_A.matrix = d_armature_obj.matrix_world.inverted() @ world_matrix_b

                    # 4. 恢复骨骼 A 的原有旋转和缩放（仅保留目标位置）
                    bone_A.rotation_quaternion = original_rot
                    bone_A.scale = original_scale

                    if A_bone_Z_location:
                        bone_A.location.z = A_bone_Z

                    # 更新场景以反映更改
                    bpy.context.view_layer.update()
                else:
                    print("未找到指定的骨骼。")
            else:
                print("未找到指定的骨架对象。")

        def Size_settings(A, B):
            obj_a = A
            obj_b = B

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

        def Move_location(A,B):
            object_a = A
            object_b = B

            if object_a and object_b:
                object_a_copy = object_a.copy()  # 复制物体 A data

                # 获取物体 B 的世界矩阵
                world_matrix_b = object_b.matrix_world

                # 计算物体 A 的世界矩阵
                world_matrix_a = object_a.matrix_world

                # 计算新的局部变换矩阵
                new_world_matrix = world_matrix_b @ world_matrix_a.inverted()

                # 应用新的局部变换矩阵到物体 A
                object_a.matrix_local = new_world_matrix
                object_a.scale = object_a_copy.scale  # 保留原始缩放
                # 更新场景
                bpy.context.view_layer.update()

            else:
                print("未找到指定的物体")

        def rotate_bone_x(armature_object, bone_name, angle_deg=10, armature_apply=True):

            bpy.ops.object.mode_set(mode='POSE')

            # 获取姿态骨骼
            pose_bone = armature_object.pose.bones.get(bone_name)

            # 欧拉旋转
            pose_bone.rotation_mode = 'XYZ'

            # 转换为弧度并应用旋转
            angle_rad = radians(angle_deg)
            pose_bone.rotation_euler.x += angle_rad
            if armature_apply:
                bpy.ops.pose.armature_apply(selected=False)

        def match_bone_transforms(arm, hand_ik, hand_fk):

            # 获取对象
            armature_obj = arm

            # 确保对象是骨骼对象
            if armature_obj.type == 'ARMATURE':
                # 进入姿态模式
                bpy.ops.object.mode_set(mode='POSE')

                # 获取骨骼数据
                pose_bones = armature_obj.pose.bones

                # 获取 hand_ik 和 hand_fk 骨骼
                hand_ik_bone = pose_bones.get(hand_ik)
                hand_fk_bone = pose_bones.get(hand_fk)

                if hand_ik_bone and hand_fk_bone:

                    # 获取 hand_fk 骨骼的世界空间矩阵
                    hand_fk_matrix_world = armature_obj.matrix_world @ hand_fk_bone.matrix

                    # 计算 hand_ik 骨骼的本地空间矩阵
                    hand_ik_matrix_local = armature_obj.matrix_world.inverted() @ hand_fk_matrix_world

                    # 将 hand_ik 骨骼的本地空间矩阵设置为计算得到的矩阵
                    hand_ik_bone.matrix = hand_ik_matrix_local

        def calculate_tail_coordinates(bone_name, bone_name2, arm_obj_name, scale = True, distance = False, lengths = False):

            arm = bpy.data.objects.get(arm_obj_name)

            bpy.context.view_layer.objects.active = arm
            bpy.ops.object.mode_set(mode='EDIT')  # 切到编辑模式

            # 确保骨骼存在
            if bone_name not in arm.data.edit_bones or bone_name2 not in arm.data.edit_bones:
                print(f"骨骼 {bone_name} 或 {bone_name2} 不存在于骨架 {arm_obj_name} 中")
                return

            bone1 = arm.data.edit_bones.get(bone_name)
            bone2 = arm.data.edit_bones.get(bone_name2)

            bone1_head = bone1.head # 头坐标
            bone1_tail = bone1.tail # 尾坐标
            bone2_length = bone2.length # 长度
            bone1_length = bone1.length # 长度

            if distance:
                head1 = np.array([bone1_head.x, bone1_head.y, bone1_head.z])
                tail1 = np.array([bone1_tail.x, bone1_tail.y, bone1_tail.z])

                # 计算方向向量和缩放因子
                direction = tail1 - head1
                length = np.linalg.norm(direction)
                if lengths:
                    k = bone1_length / length  # 缩放因子
                else:
                    k = bone2_length / length  # 缩放因子


                # 生成两种方向的尾坐标
                scaled_dir1 = direction * k  # 原方向
                scaled_dir2 = -direction * k  # 反方向
                tail2_case1 = tail1 + scaled_dir1
                tail2_case2 = tail1 + scaled_dir2

                # 计算到 head1 的距离
                distance_case1 = np.linalg.norm(head1 - tail2_case1)
                distance_case2 = np.linalg.norm(head1 - tail2_case2)

                if distance_case1 > distance_case2:  # 选择距离更长的
                    bone2.tail = tail2_case1
                    print(f"Case 1 尾坐标: {np.round(tail2_case1, 4)}, 距离: {np.round(distance_case1, 4)}")
                else:
                    bone2.tail = tail2_case2
                    print(f"Case 2 尾坐标: {np.round(tail2_case2, 4)}, 距离: {np.round(distance_case2, 4)}")

            if not distance:
                bone2.tail = bone1_head
                if scale:
                    bone2.length = bone2_length

        def Calculate_intersection_angle(Arm, a_bone, b_bone):

            bpy.ops.object.mode_set(mode='EDIT')

            A_bone = Arm.data.edit_bones.get(a_bone)
            B_bone = Arm.data.edit_bones.get(b_bone)

            # 定义点坐标
            A = np.array([A_bone.head.x, A_bone.head.y, A_bone.head.z])  # 起点
            B = np.array([B_bone.head.x, B_bone.head.y, B_bone.head.z])  # 交点
            C = np.array([B_bone.tail.x, B_bone.tail.y, B_bone.tail.z])  # 终点

            # 计算从交点B出发的向量
            BA = A - B  # 向量BA
            BC = C - B  # 向量BC

            # 计算点积
            dot_product = np.dot(BA, BC)

            # 计算向量模长
            norm_BA = np.linalg.norm(BA)
            norm_BC = np.linalg.norm(BC)

            # 计算夹角余弦值
            cos_theta = dot_product / (norm_BA * norm_BC)

            # 计算夹角（弧度）
            theta_rad = np.arccos(np.clip(cos_theta, -1.0, 1.0))

            # 转换为角度
            theta_deg = np.degrees(theta_rad)

            # 输出结果
            print('骨骼: ', a_bone, b_bone)
            print(f"向量 BA: {BA}")
            print(f"向量 BC: {BC}")
            print(f"点积: {dot_product}")
            print(f"向量 BA 模长: {norm_BA:.6f}")
            print(f"向量 BC 模长: {norm_BC:.6f}")
            print(f"余弦值: {cos_theta:.6f}")
            print(f"角度(弧度): {theta_rad:.6f}")
            print(f"角度(度数): {theta_deg:.6f}")
            print('------------------')

            return theta_deg

        # 获取某个骨骼的世界空间z轴坐标
        def get_bone_world_z(bone_name, armature_obj):
            # 切换到姿势模式
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='POSE')

            # 获取骨骼
            pose_bone = armature_obj.pose.bones.get(bone_name)
            if not pose_bone:
                print(f"骨骼 {bone_name} 不存在")
                return

            # 获取骨骼z轴坐标
            z_coordinate = pose_bone.matrix.translation.z
            return z_coordinate

        # 设置骨骼的世界空间z轴坐标(在姿势模式)
        def set_bone_world_z(bone_name, armature_obj, z_value):
            # 切换到姿势模式
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='POSE')

            # 获取骨骼
            pose_bone = armature_obj.pose.bones.get(bone_name)
            if not pose_bone:
                print(f"骨骼 {bone_name} 不存在")
                return

            # 设置骨骼z轴坐标
            pose_bone.matrix.translation.z = z_value

            # 应用变换
            bpy.ops.pose.armature_apply(selected=False)

        # 版本比较
        def compare_version(version1, version2):
            parts1 = []
            parts2 = []
            for part in re.split('[.-]', version1):
                try:
                    num = int(part)
                except ValueError:
                    num = 0
                parts1.append(num)
            for part in re.split('[.-]', version2):
                try:
                    num = int(part)
                except ValueError:
                    num = 0
                parts2.append(num)
            min_length = min(len(parts1), len(parts2))
            for i in range(min_length):
                if parts1[i] < parts2[i]:
                    return True
                elif parts1[i] > parts2[i]:
                    return False
            return len(parts1) < len(parts2)

        # 变换
        Move_location(mmd_arm,RIG)
        # 缩放
        Size_settings(RIG,mmd_arm)

        finger_bone = []

        arm_number = 0
        arm_not_bone = []

        # 遍历字典的键值对并打印
        for key, value in config.items():
            print(f"键名: {key}, 值: {value}")

            if check_keywords(value):
                finger_bone.append(value)

            if value == "spine":
                # 调用函数
                align_bones(value, RIG.name, key, mmd_arm.name)
            else:
                # 调用函数
                align_bones(value, RIG.name, key, mmd_arm.name)

            if value == "spine.006":
                # 移动到正确位置
                move_bone_a_to_b(RIG.name, mmd_arm.name, "face", key)
                # 遍历字典的键值
                for key, value in config.items():
                    # 眼睛
                    if value == "eye.L" or value == "eye.R":
                        move_bone_a_to_b(RIG.name, mmd_arm.name, value, key)

            if align_bones(value, RIG.name, key, mmd_arm.name, count=True):
                arm_number += 1
                # 激活物体
                bpy.context.view_layer.objects.active = RIG
                # 选择物体
                RIG.select_set(True)
                # 应用
                bpy.ops.object.mode_set(mode='POSE')
                bpy.ops.pose.armature_apply(selected=False)

        for key, value in config.items():
            if 'hand' in value:
                if determine_side(value):
                    calculate_tail_coordinates('f_middle.01.L', 'hand.L', RIG.name)
                else:
                    calculate_tail_coordinates('f_middle.01.R', 'hand.R', RIG.name)


            if value == 'spine.003':
                calculate_tail_coordinates('spine.004', 'spine.003', RIG.name, scale=False)

            if 'foot' in value:
                if determine_side(value):
                    move_bone_a_to_b(RIG.name, RIG.name, "heel.02.L", value, A_bone_Z_location=True)
                else:
                    move_bone_a_to_b(RIG.name, RIG.name, "heel.02.R", value, A_bone_Z_location=True)

            bpy.ops.object.mode_set(mode='POSE')  # 切到pose模式
            bpy.ops.pose.armature_apply(selected=False)  # 应用

        finger_bone_L = []
        finger_bone_R = []

        for v in finger_bone:
            if determine_side(v):
                finger_bone_L.append(v)
            else:
                finger_bone_R.append(v)

        bpy.context.view_layer.objects.active = RIG
        bpy.ops.object.mode_set(mode='EDIT')  # 切到编辑模式

        if mmr.f_pin:
            for key, value in config.items():
                if '03' in value:
                    f_pin = ['thumb', 'index', 'middle', 'ring', 'pinky']
                    for f in f_pin:
                        if f in value:
                            v_bone = RIG.data.edit_bones.get(value)
                            if format(v_bone.head.x, '.4f') == format(v_bone.tail.x, '.4f'):
                                if format(v_bone.head.y, '.4f') == format(v_bone.tail.y, '.4f'):
                                    pinky_parent = v_bone.parent.name
                                    calculate_tail_coordinates(pinky_parent, value, RIG.name, distance=True, lengths=True)

        for bone in RIG.data.edit_bones:  # 遍历所有骨骼
            bone.select = bone.name in finger_bone_R  # True=选中，False=不选
        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z') # 原本想设x的,看到0.56 MMR这样用的,就这样吧
        bpy.ops.armature.select_all(action='DESELECT') # 取消所有选择

        for bone in RIG.data.edit_bones:
            bone.select = bone.name in finger_bone_L
        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
        bpy.ops.armature.select_all(action='DESELECT')

        roll_thumb = 'GLOBAL_NEG_Y'

        if mmr.Thumb_twist_aligns_with_the_world_Z_axis:
            roll_thumb = 'GLOBAL_POS_Z'

        for bone in RIG.data.edit_bones:
            if bone.name in finger_bone_R:
                if 'thumb' in bone.name:
                    bone.select = True
                    bpy.ops.armature.calculate_roll(type=roll_thumb)
                    bpy.ops.armature.select_all(action='DESELECT')
            else:
                if bone.name in finger_bone_L:
                    if 'thumb' in bone.name:
                        bone.select = True
                        bpy.ops.armature.calculate_roll(type=roll_thumb)
                        bpy.ops.armature.select_all(action='DESELECT')

        bjiy_1 = ['thigh.L', 'shin.L',
                  'thigh.R', 'shin.R']

        bjiy_2 = ['spine', 'spine.001',
                  'spine.002', 'spine.003',
                  'spine.004', 'spine.006',
                  'upper_arm.L', 'forearm.L',
                  'hand.L', 'upper_arm.R',
                  'forearm.R', 'hand.R']

        bjiy_3 = ['thigh.L', 'shin.L', 'foot.L', 'toe.L', 'thigh.R', 'shin.R', 'foot.R', 'toe.R']

        bjiy_4 = {'foot.L': 'toe.L', 'foot.R': 'toe.R'}

        bjiy_5 = ['shoulder.L', 'shoulder.R']

        for bone in RIG.data.edit_bones:
            bone.select = bone.name in bjiy_2
        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Y')
        bpy.ops.armature.select_all(action='DESELECT')

        for bone in RIG.data.edit_bones:
            bone.select = bone.name in bjiy_2
        bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Y')
        bpy.ops.armature.select_all(action='DESELECT')

        for bone in RIG.data.edit_bones:
            bone.select = bone.name in bjiy_3
        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Y')
        bpy.ops.armature.select_all(action='DESELECT')

        for k, v in bjiy_4.items():
            for bone in RIG.data.edit_bones:
                if bone.name == k:
                    bone.select = True
                    bpy.ops.armature.calculate_roll(type='GLOBAL_NEG_Z')
                    bpy.ops.armature.select_all(action='DESELECT')
                if bone.name == v:
                    bone.select = True
                    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
                    bpy.ops.armature.select_all(action='DESELECT')

        for bone in RIG.data.edit_bones:
            bone.select = bone.name in bjiy_5
        bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
        bpy.ops.armature.select_all(action='DESELECT')

        # 设置父子级
        for key, value in config.items():
            # 进入RIG的编辑模式
            bpy.context.view_layer.objects.active = RIG
            bpy.ops.object.mode_set(mode='EDIT')
            # 进入mmd_arm的编辑模式
            bpy.context.view_layer.objects.active = mmd_arm
            bpy.ops.object.mode_set(mode='EDIT')

            mmd_edit_bones = mmd_arm.data.edit_bones
            RIG_edit_bones = RIG.data.edit_bones

            if 'eye' in value:
                continue

            # 检查骨骼是否存在
            if key in mmd_edit_bones and value in RIG_edit_bones:
                # 获取骨骼对象
                mmd_bone = mmd_edit_bones[key]
                RIG_bone = RIG_edit_bones[value]
                # 新建骨骼
                new_bone = RIG_edit_bones.new(name=value + '_parent')
                new_bone.head = mmd_bone.head  # 复制头位置
                new_bone.tail = mmd_bone.tail  # 复制尾位置
                new_bone.roll = mmd_bone.roll  # 复制旋转
                new_bone.parent = RIG_bone  # 设置父级
            else:
                print(f"骨骼 {key} 或 {value} 不存在于骨架中")

        Wrist_twist = {'A':mmr.Left_lower_arm_twist, 'B':mmr.Right_lower_arm_twist, 'C':mmr.Left_upper_arm_twist, 'D':mmr.Right_upper_arm_twist}

        Twist_bones = [{'forearm.L':Wrist_twist['A'], 'forearm.R':Wrist_twist['B'], 'upper_arm.L':Wrist_twist['C'], 'upper_arm.R':Wrist_twist['D']},
                       {'DEF-forearm.L.001':Wrist_twist['A'], 'DEF-forearm.R.001':Wrist_twist['B'], 'DEF-upper_arm.L.001':Wrist_twist['C'], 'DEF-upper_arm.R.001':Wrist_twist['D']}]

        for key, value in Twist_bones[0].items():

            # 进入RIG的编辑模式
            bpy.context.view_layer.objects.active = RIG
            bpy.ops.object.mode_set(mode='EDIT')
            # 进入mmd_arm的编辑模式
            bpy.context.view_layer.objects.active = mmd_arm
            bpy.ops.object.mode_set(mode='EDIT')

            mmd_edit_bones = mmd_arm.data.edit_bones
            RIG_edit_bones = RIG.data.edit_bones

            if value in mmd_edit_bones:
                # 获取骨骼对象
                mmd_bone = mmd_edit_bones.get(value)
                RIG_bone = RIG_edit_bones.get(key)

                if not mmd_bone or not RIG_bone:
                    continue

                # 新建骨骼
                new_bone = RIG_edit_bones.new(name=value + '_parent')
                new_bone.head = mmd_bone.head  # 复制头位置
                new_bone.tail = mmd_bone.tail  # 复制尾位置
                new_bone.roll = mmd_bone.roll  # 复制旋转
                new_bone.parent = RIG_bone

        # 激活骨架
        bpy.context.view_layer.objects.active = RIG
        RIG.select_set(True)

        if mmr.Only_meta_bones_are_generated:
            mmr.Only_meta_bones_are_generated = False
            return {'FINISHED'}

        foot_L_world_z = get_bone_world_z('foot.L',RIG)
        foot_R_world_z = get_bone_world_z('foot.R',RIG)

        heel_bones = ['heel.02.L', 'heel.02.R']

        heel_L_world_z = get_bone_world_z('heel.02.L',RIG)
        heel_R_world_z = get_bone_world_z('heel.02.R',RIG)

        heel_world_z = (heel_L_world_z + heel_R_world_z) / 2

        # 角度
        v = mmr.Bend_angle_leg
        v1 = mmr.Bend_angle_arm

        # 弯曲骨骼(必须要，不然就会出bug)
        if mmr.Bend_the_bones:
            if Calculate_intersection_angle(RIG, 'upper_arm.L', 'forearm.L') > 165:
                rotate_bone_x(RIG,'upper_arm.L',angle_deg=-v1)
                rotate_bone_x(RIG,'forearm.L',angle_deg=v1*2)

            if Calculate_intersection_angle(RIG, 'upper_arm.R', 'forearm.R') > 165:
                rotate_bone_x(RIG,'upper_arm.R',angle_deg=-v1)
                rotate_bone_x(RIG,'forearm.R',angle_deg=v1*2)

        # 弯曲腿部骨骼
        if mmr.Bend_the_leg_bones:

            print('heel_world_z: ', heel_world_z)

            if Calculate_intersection_angle(RIG, 'thigh.L', 'shin.L') > 165:
                rotate_bone_x(RIG, 'thigh.L',angle_deg=-v)
                rotate_bone_x(RIG, 'shin.L',angle_deg=v*2)
                rotate_bone_x(RIG, 'foot.L',angle_deg=-v)

            if Calculate_intersection_angle(RIG, 'thigh.R', 'shin.R') > 165:
                rotate_bone_x(RIG, 'thigh.R',angle_deg=-v)
                rotate_bone_x(RIG, 'shin.R',angle_deg=v*2)
                rotate_bone_x(RIG, 'foot.R',angle_deg=-v)

            foot_L_world_z_1 = get_bone_world_z('foot.L', RIG)
            foot_R_world_z_1 = get_bone_world_z('foot.R', RIG)

            foot_L_world_z_difference = foot_L_world_z_1 - foot_L_world_z
            foot_R_world_z_difference = foot_R_world_z_1 - foot_R_world_z

            foot_world_z_difference = (foot_L_world_z_difference + foot_R_world_z_difference) / 2

            print('foot_world_z 差异: ', foot_world_z_difference)

            spine_world_z = get_bone_world_z('spine',RIG)
            print('spine_world_z: ', spine_world_z)

            spine_world_z_1 = spine_world_z - foot_world_z_difference
            print('spine_world_z 坐标: ', spine_world_z_1)

            set_bone_world_z('spine',RIG,spine_world_z_1)

            for bone in heel_bones:
                set_bone_world_z(bone,RIG,heel_world_z)

        u = "WGTS_" + RIG.name
        if u in bpy.data.collections:
            bpy.context.object.data.rigify_widgets_collection = bpy.data.collections["WGTS_" + RIG.name]

        RIG.name = 'MMR-' + mmd_arm.name

        # 生成
        bpy.ops.pose.rigify_generate()

        rigify = bpy.context.active_object
        rigify.name = 'RIG-' + mmd_arm.name

        if not mmr.ORG_mode:
            for key, value in config.items():
                if 'eye' in value:
                    continue

                value1 = 'ORG-' + value + '_parent'

                # 进入编辑模式
                bpy.context.view_layer.objects.active = rigify
                bpy.ops.object.mode_set(mode='EDIT')

                bone = rigify.data.edit_bones.get(value1)

                if value1 in rigify.data.edit_bones:
                    # 父级
                    bone.parent = rigify.data.edit_bones['DEF-' + value]

        eye_pt = ['eye.L', 'eye.R']

        for n in eye_pt:
            for k , v in config.items():
                if v == n:
                    n = 'ORG-' + v
                    # 进入编辑模式
                    bpy.context.view_layer.objects.active = rigify
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.context.view_layer.objects.active = mmd_arm
                    bpy.ops.object.mode_set(mode='EDIT')

                    edit_bones = rigify.data.edit_bones
                    mmd_edit_bones = mmd_arm.data.edit_bones

                    s_bone = edit_bones[n]
                    m_bone = mmd_edit_bones[k]

                    # 复制骨骼（新建骨骼并复制属性）
                    new_bone = edit_bones.new(name = n +'_parent')
                    # 位置
                    new_bone.head = m_bone.head
                    new_bone.tail = m_bone.tail
                    # 扭转
                    new_bone.roll = m_bone.roll

        bpy.context.view_layer.objects.active = rigify
        rigify.select_set(True)
        bpy.ops.object.mode_set(mode='POSE')
        # 应用姿态
        bpy.ops.pose.armature_apply(selected=False)

        for k in eye_pt:
            # 进入编辑模式
            bpy.ops.object.mode_set(mode='EDIT')

            edit_bones = rigify.data.edit_bones

            s_bone = edit_bones['ORG-' + k + '_parent']
            e_bone = edit_bones['ORG-' + k]

            # 父级
            s_bone.parent = e_bone
            # 加入集合
            bpy.ops.object.mode_set(mode='POSE')
            data_bones = rigify.pose.bones
            t_bone = data_bones.get('ORG-' + k + '_parent')
            t_bone.select = True # 活动骨骼
            bpy.ops.armature.collection_assign(name='ORG')
            bpy.ops.pose.select_all(action='DESELECT')

        # 捩骨约束
        for key, value in Twist_bones[-1].items():
            value1 = 'ORG-' + value + '_parent'
            # 进入编辑模式
            bpy.ops.object.mode_set(mode='EDIT')
            edit_bones = rigify.data.edit_bones

            bone1 = edit_bones.get(key)
            bone2 = edit_bones.get(value1)

            if key in edit_bones and value1 in edit_bones:
                bone2.parent = bone1

            bpy.context.view_layer.objects.active = mmd_arm
            mmd_arm.select_set(True)
            bpy.ops.object.mode_set(mode='POSE')

            bone = mmd_arm.pose.bones.get(value)  # 获取骨骼

            # 检查骨骼是否存在
            if bone is None:
                print(f"警告: 未找到名为 {value} 的骨骼，跳过约束操作")
                continue  # 跳过后续约束

            # 删除所有约束
            for constraint in list(bone.constraints):
                if constraint.name == 'MMR_复制旋转':
                    bone.constraints.remove(constraint)

            # 添加复制旋转约束
            constraint = bone.constraints.new(type='COPY_ROTATION')  # 复制旋转
            constraint.name = 'MMR_复制旋转'
            constraint.target = rigify
            constraint.subtarget = value1

        # 添加约束
        for key, value in config.items():

            value = 'ORG-' + value + '_parent'

            print(f"键名: {key}, 值: {value}")

            bpy.context.view_layer.objects.active = mmd_arm
            mmd_arm.select_set(True)
            bpy.ops.object.mode_set(mode='POSE')

            bone = mmd_arm.pose.bones.get(key)  # 获取骨骼

            # 检查骨骼是否存在
            if bone is None:
                print(f"警告: 未找到名为 {key} 的骨骼，跳过约束操作")
                continue  # 跳过后续约束

            # 删除所有约束
            for constraint in list(bone.constraints):
                if constraint.name == 'MMR_复制变换':
                    bone.constraints.remove(constraint)

            # 添加复制变换约束
            if 'ORG-toe' in value:
                constraint = bone.constraints.new(type='COPY_ROTATION')  # 复制旋转
            else:
                constraint = bone.constraints.new(type='COPY_TRANSFORMS')
            constraint.name = 'MMR_复制变换'
            constraint.target = rigify
            constraint.subtarget = value

        subtarget = ['つま先ＩＫ.L', 'つま先ＩＫ.R', '足ＩＫ.R', '足ＩＫ.L']

        mmd_arms = True # 是否是mmd的armature

        # 遍历骨骼
        for bone in mmd_arm.pose.bones:
            # 遍历骨骼约束
            for constraint in bone.constraints:
                # 类型是否为IK
                if constraint.type == 'IK':
                    for s in subtarget:
                        if constraint.subtarget == s:
                            # 设置影响值为0
                            constraint.influence = 0.0
                            print(f"已将骨骼 '{bone.name}' 的IK约束影响值设置为0")
                            mmd_arms = False
        if mmd_arms:
            # 遍历骨骼
            for bone in mmd_arm.pose.bones:
                # 遍历骨骼约束
                for constraint in bone.constraints:
                    # 类型是否为IK
                    if constraint.type == 'IK':
                        # 设置影响值为0
                        constraint.influence = 0.0
                        print(f"已将骨骼 '{bone.name}' 的IK约束影响值设置为0")

        bpy.context.view_layer.objects.active = rigify
        rigify.select_set(True)
        # 进入编辑模式
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones = rigify.data.edit_bones

        e_bone = edit_bones['thigh_ik.R']
        c_bone = edit_bones['torso']
        root_bone = edit_bones['root']
        L_bone = edit_bones['hand_ik.L']
        R_bone = edit_bones['hand_ik.R']

        # 复制骨骼（新建骨骼并复制属性）
        new_bone = edit_bones.new(name='torso_root')
        # 位置
        new_bone.head.x = c_bone.head.copy().x
        new_bone.head.y = c_bone.head.copy().y
        new_bone.head.z = e_bone.tail.copy().z
        new_bone.tail.x = c_bone.tail.copy().x
        new_bone.tail.y = c_bone.tail.copy().y
        new_bone.tail.z = e_bone.tail.copy().z
        # 父级
        new_bone.parent = root_bone
        c_bone.parent = new_bone
        R_bone.parent = new_bone
        L_bone.parent = new_bone
        # 形状
        bpy.ops.object.mode_set(mode='POSE')
        pose_bones = rigify.pose.bones
        t_bone = pose_bones.get('torso_root')
        t_bone.color.palette = 'THEME09'
        t_bone.custom_shape = bpy.data.objects["WGT-RIG-" + RIG.name + "_root"]
        # 加入集合
        data_bones = rigify.pose.bones
        t_bone = data_bones.get('torso_root')
        t_bone.select = True
        bpy.ops.armature.collection_assign(name='Torso')
        bpy.ops.pose.select_all(action='DESELECT')

        rigify.show_in_front = True # 在前面

        if mmr.Upper_body_linkage:
            rigify.pose.bones["torso"]["neck_follow"] = 0
            rigify.pose.bones["torso"]["head_follow"] = 0
        else:
            rigify.pose.bones["torso"]["neck_follow"] = 1
            rigify.pose.bones["torso"]["head_follow"] = 1

        is_gto = ['Face (Primary)', 'Face (Secondary)', 'Torso (Tweak)', 'Fingers (Detail)', 'Arm.L (FK)', 'Arm.R (FK)',
                  'Arm.L (Tweak)', 'Arm.R (Tweak)', 'Leg.L (FK)', 'Leg.R (FK)', 'Leg.L (Tweak)', 'Leg.R (Tweak)']

        # 隐藏骨骼集合
        for n in is_gto:
            rigify.data.collections_all[n].is_visible = False

        not_bone = ['ear.L', 'ear.R', 'jaw_master', 'teeth.B', 'tongue_master', 'teeth.T', 'nose_master']

        blender_version = bpy.app.version_string

        if compare_version(blender_version, "4.9.9"):
            # 隐藏骨骼
            for n in not_bone:
                bone = rigify.data.bones.get(n)
                bone.hide = True
        else:
            # 隐藏骨骼
            for n in not_bone:
                bone = rigify.pose.bones.get(n)
                bone.hide = True

        ik_stretch = ["upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.R","thigh_parent.L" ]

        # 关闭ik拉伸
        for i in ik_stretch:
            rigify.pose.bones[i]["IK_Stretch"] = 0

        # 极向目标
        if mmr.Polar_target:
            for i in ik_stretch:
                bone = rigify.pose.bones.get(i)
                bone["pole_vector"] = True

        if mmr.Use_ITASC_solver:
            rigify.pose.ik_solver = 'ITASC' # 设置IK解算器

        bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS' # 各自的原点

        bpy.ops.object.mode_set(mode='OBJECT')

        del_obj = [RIG.name]

        # 删除临时对象
        for y in del_obj:
            bpy.ops.object.select_all(action='DESELECT')
            del_object = bpy.data.objects.get(y)
            del_object.select_set(True)
            bpy.context.view_layer.objects.active = del_object
            bpy.ops.object.delete(use_global=False)

        if not mmr.Hide_mmd_skeleton:
            mmd_arm.hide_set(True) # 隐藏mmd骨架
        else:
            mmd_arm.select_set(True) # 选中mmd骨架

        mmd_arm.matrix_world = mmd_arm_matrix # 还原位置

        rigify.matrix_world = mmd_arm_matrix # 吸附位置

        # 激活并选择最终生成的Rigify骨架
        rigify.select_set(True)
        bpy.context.view_layer.objects.active = rigify

        self.report({'INFO'}, f"生成成功, 匹配骨骼数: {arm_number}")

        return {'FINISHED'}

    def invoke(self, context, event):
        mmr = context.object.mmr
        if mmr.Towards_the_dialog_box:
            return context.window_manager.invoke_props_dialog(self, width=200)
        else:
            return self.execute(context)  # 直接执行

    def draw(self, context):
        layout = self.layout
        layout.label(text='模型默认朝向')
        layout.prop(self,"Towards")

class mmrexportvmdactionsOperator(bpy.types.Operator):
    '''Export VMD actions'''
    bl_idname = "object.mmr_export_vmd"
    bl_label = "Export VMD actions"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.type == 'ARMATURE':
                return True
        return False

    def execute(self, context: bpy.types.Context):

        # 获取名称
        obj = context.object.name
        obj = obj.removeprefix('RIG-')
        print(obj)
        bpy.ops.object.mode_set(mode="OBJECT")
        # 选择物体
        bpy.data.objects[obj].select_set(True)
        # 设为活动物体
        bpy.context.view_layer.objects.active = bpy.data.objects[obj]
        # 取消隐藏物体
        bpy.data.objects[obj].hide_set(False)
        # 姿态模式
        bpy.ops.object.mode_set(mode="POSE")

        # 检查所有的骨骼，如果有名称为"MMR_复制变换"的骨骼约束，则选中
        armature = context.object
        for bone in armature.pose.bones:
            for constraint in bone.constraints:
                if constraint.name == "MMR_复制变换":
                    bone.select = True
                    break

        start = bpy.context.scene.frame_start
        end = bpy.context.scene.frame_end

        bpy.ops.nla.bake(frame_start=start, frame_end=end, visual_keying=True, bake_types={'POSE'})

        bpy.ops.mmd_tools.export_vmd("INVOKE_DEFAULT")

        return {'FINISHED'}

class MahyPdtOperator(bpy.types.Operator):
    bl_idname = "object.mdtsu_ops"
    bl_label = "Add Mouth Panel"
    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tyu = None
        # 获取当前活动的物体
        active_object = context.view_layer.objects.active

        mmr = context.object.mmr

        # 自定义面板预设
        panel_preset = {'bone':mmr.panel_preset_bone, 'A':mmr.panel_preset_A, 'I':mmr.panel_preset_I, 'U':mmr.panel_preset_U, 'E':mmr.panel_preset_E, 'O':mmr.panel_preset_O}
        # 骨骼约束切换自定义
        bone_air = mmr.panel_preset

        # 检查是否有活动物体，如果存在则打印名称
        if active_object:
            print("当前活动的物体：", active_object.name)
            Model = active_object.name

            # 获取所有选中的物体
            selected_objects = bpy.context.selected_objects

            # 验证是否至少有两个物体被选中：一个活动的和至少一个非活动的
            if len(selected_objects) > 1:
                # 打印除了活动物体之外的所有选中物体的名称
                for obj1 in selected_objects:
                    if obj1 != active_object:
                        tyu = obj1.name
                        print("不活动物体的名称：", tyu)
            else:
                print("需要选中模型和骨骼！")
                self.report({'WARNING'}, f"需要选中模型和骨骼！")
                return {'FINISHED'}

            # 检查是否至少有两个物体被选中
            if len(selected_objects) != 2:
                print("只能选中模型和骨骼！")
                self.report({'WARNING'}, "只能选中模型和骨骼！")
                return {'FINISHED'}

            # 确保一个是网格模型，另一个是骨骼
            model_and_armature_selected = False
            for obj in selected_objects:
                if obj.type == 'MESH':
                    model = obj
                elif obj.type == 'ARMATURE':
                    armature = obj
            if 'model' in locals() and 'armature' in locals():
                model_and_armature_selected = True

            if not model_and_armature_selected:
                print("只能选中模型和骨骼！")
                self.report({'WARNING'}, "只能选中模型和骨骼！")
                return {'FINISHED'}
        else:
            print("没有活动物体被选中！")
            self.report({'WARNING'}, f"没有活动物体被选中！")
            return {'FINISHED'}

        def check_collection_exists(name, collections=None):
            if collections is None:
                collections = bpy.data.collections
            for coll in collections:
                if coll.name == name:
                    return True
                # 递归检查子集合
                if check_collection_exists(name, coll.children):
                    return True
            return False

        # 调用函数检查
        exists = check_collection_exists("Mouth_Rigvitfy")
        print("集合存在" if exists else "集合不存在")

        if exists == False:
            # 获取目录路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"当前目录路径：{current_dir}")
            # 路径拼接
            file_path = os.path.join(current_dir, "Mouth_Rig.blend")
            # 标准化路径（处理双斜杠等问题）
            normalized_path = os.path.normpath(file_path)
            print(f"blend文件路径：{normalized_path}")

            # 配置目标集合名称
            target_collection = "Mouth_Rigtion"

            # 构造Blender内部路径格式
            internal_dir = str(normalized_path) + "/Collection/"
            internal_path = str(normalized_path) + "/Collection/" + target_collection

            # 执行追加操作
            bpy.ops.wm.append(
                filepath=internal_path,
                directory=internal_dir,
                filename=target_collection,
            )

            def delete_collection_and_move_to_parent(collection_name):
                target_coll = bpy.data.collections.get(collection_name)
                if not target_coll:
                    print(f"集合 '{collection_name}' 不存在")
                    return
                # 查找目标集合的所有父集合
                parent_collections = []
                for coll in bpy.data.collections:
                    if target_coll.name in coll.children:
                        parent_collections.append(coll)
                # 如果目标集合没有父集合，默认转移到场景主集合
                if not parent_collections:
                    parent_collections = [bpy.context.scene.collection]
                # 将对象和子集合转移到每个父集合
                for parent_coll in parent_collections:
                    # 转移对象
                    for obj in target_coll.objects[:]:  # 遍历副本避免修改问题
                        if obj.name not in parent_coll.objects:
                            parent_coll.objects.link(obj)
                        target_coll.objects.unlink(obj)
                    # 转移子集合
                    for child_coll in target_coll.children[:]:
                        if child_coll.name not in parent_coll.children:
                            parent_coll.children.link(child_coll)
                        target_coll.children.unlink(child_coll)
                # 解除目标集合的所有父级引用
                for coll in bpy.data.collections:
                    if target_coll.name in coll.children:
                        coll.children.unlink(target_coll)
                # 删除目标集合
                bpy.data.collections.remove(target_coll)

            # 执行操作
            delete_collection_and_move_to_parent('Mouth_Rigtion')

            # 检查集合是否存在
            if "Mouth_Rigvitfy" not in bpy.data.collections:
                print("集合不存在")
            else:
                # 获取当前视图层
                view_layer = bpy.context.view_layer

                # 递归遍历 LayerCollection 树
                def exclude_collection(layer_coll, target_name):
                    if layer_coll.name == target_name:
                        layer_coll.exclude = True
                        return True
                    for child in layer_coll.children:
                        if exclude_collection(child, target_name):
                            return True
                    return False

                # 调用函数排除集合
                if exclude_collection(view_layer.layer_collection, "Mouth_Rigvitfy"):
                    print("集合已排除")
                else:
                    print("集合未找到")
        else:
            # 获取目录路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"当前目录路径：{current_dir}")
            # 路径拼接
            file_path = os.path.join(current_dir, "Mouth_Rig.blend")
            # 标准化路径（处理双斜杠等问题）
            normalized_path = os.path.normpath(file_path)
            print(f"blend文件路径：{normalized_path}")

            # 设置追加参数
            filepath = os.path.join(normalized_path, "Object", "Mouth_Rig_001")
            directory = os.path.join(normalized_path, "Object")
            filename = "Mouth_Rig_001"

            # 执行追加操作
            bpy.ops.wm.append(
                filepath=filepath,
                directory=directory,
                filename=filename,
            )
            bpy.data.objects.get("Mouth_Rig_001").name = "Mouth_Rig"

        def Add_a_lip_panel_driver(A, B, C, D):
            # 获取当前选中的物体
            obj = bpy.context.object
            if not obj or obj.type != 'MESH':
                raise Exception("请选择一个网格物体")

            # 检查形态键
            if not obj.data.shape_keys:
                raise Exception("该物体没有形态键")
            key_blocks = obj.data.shape_keys.key_blocks
            kb = key_blocks.get(A)
            if not kb:
                raise Exception("找不到形态键：",A)

            # 获取驱动骨架
            arm = bpy.data.objects.get(B)
            if not arm or arm.type != 'ARMATURE':
                raise Exception("骨架不存在")

            # 验证目标骨骼
            if "qws_F2" not in arm.pose.bones:
                raise Exception("骨架中不存在骨骼'qws_F2'")

            # 添加驱动器
            fcurve = kb.driver_add("value")
            driver = fcurve.driver
            driver.type = 'SCRIPTED'  # 明确设置驱动类型

            # 清除旧变量
            while driver.variables:
                driver.variables.remove(driver.variables[0])

            # 创建新变量
            var = driver.variables.new()
            var.name = "var"
            var.type = 'TRANSFORMS'

            # 配置变量目标
            target = var.targets[0]
            target.id = arm
            if A != panel_preset['A']:
                target.bone_target = "qws_F2"
            else:
                target.bone_target = "qws_F3"
            target.transform_type = C
            target.transform_space = 'LOCAL_SPACE'  # 局部空间

            # 设置驱动表达式
            driver.expression = D

            print("形态键驱动器已成功添加")

            # 确保存在F曲线
            if not fcurve.keyframe_points:
                print("警告：F曲线不存在，正在创建关键帧")

            # 清除旧关键帧（避免重复）
            fcurve.keyframe_points.clear()

            # 添加关键帧 (X位置对应变量值，Y位置对应形态键值)
            fcurve.keyframe_points.insert(0.0, 0.0)  # 输入0 → 输出0
            if A != panel_preset['A']:
                fcurve.keyframe_points.insert(0.106, 1.0)  # 输入0.106 → 输出1
            else:
                fcurve.keyframe_points.insert(0.192, 1.0)  # 输入0.192 → 输出1

            # 设置插值模式为线性
            for kp in fcurve.keyframe_points:
                kp.interpolation = 'LINEAR'

            # 强制更新曲线数据
            fcurve.update()

            print("关键帧添加完成")

            # 确保存在F曲线
            if not hasattr(fcurve, 'modifiers'):
                raise Exception("当前F曲线不支持修改器")

            # 删除所有修改器
            if fcurve.modifiers:
                print(f"正在移除 {len(fcurve.modifiers)} 个修改器...")
                # 反向遍历避免索引错位
                for i in range(len(fcurve.modifiers) - 1, -1, -1):
                    fcurve.modifiers.remove(fcurve.modifiers[i])

                fcurve.update()
                print("所有修改器已清除")
            else:
                print("该F曲线没有需要删除的修改器")

            # 验证结果
            print("剩余修改器数量:", len(fcurve.modifiers))

            # 设置外插模式
            fcurve.extrapolation = 'LINEAR'  # 设置为线性外插

            # 可选：验证设置结果
            print("当前外插模式：", fcurve.extrapolation)

            # 强制更新曲线数据
            fcurve.update()

            print("外插模式已设置为线性")

        Add_a_lip_panel_driver(panel_preset['U'],"Mouth_Rig",'LOC_X',"-var + 0.0")
        Add_a_lip_panel_driver(panel_preset['I'],"Mouth_Rig",'LOC_X',"var + 0.0")
        Add_a_lip_panel_driver(panel_preset['O'],"Mouth_Rig",'LOC_Z',"-var + 0.0")
        Add_a_lip_panel_driver(panel_preset['E'],"Mouth_Rig",'LOC_Z',"var + 0.0")
        Add_a_lip_panel_driver(panel_preset['A'],"Mouth_Rig",'LOC_X',"var + 0.0")

        # 获取需要添加约束的物体和目标物体
        obj = bpy.data.objects['Mouth_Rig']  # 被施加约束的物体
        target_obj = bpy.data.objects[tyu]  # 目标物体

        # 添加复制变换约束
        constraint = obj.constraints.new(type='COPY_TRANSFORMS')
        constraint.target = target_obj  # 设置目标物体
        constraint.mix_mode = 'REPLACE'
        constraint.target_space = 'WORLD'
        constraint.owner_space = 'WORLD'

        # 取消所有物体的选中状态
        bpy.ops.object.select_all(action='DESELECT')

        # 通过名称获取物体
        obj1 = bpy.data.objects.get(tyu)
        obj2 = bpy.data.objects.get('Mouth_Rig')

        # 检查物体是否存在
        if not obj1:
            raise Exception("未找到名称为'1'的物体")
        if not obj2:
            raise Exception("未找到名称为'2'的物体")

        # 选中两个物体
        obj1.select_set(True)
        obj2.select_set(True)

        # 将物体1设为激活状态
        bpy.context.view_layer.objects.active = obj1
        # 合并骨架
        bpy.ops.object.join()
        # 姿态模式
        bpy.ops.object.mode_set(mode="POSE")
        # 获取目标骨骼
        target_bone = bpy.context.active_object.pose.bones.get("qws_F1")
        subtarget_bone = bpy.context.active_object.pose.bones.get("頭")
        if not target_bone:
            raise KeyError("未找到名为 qws_F1 的骨骼")

        # 添加子级约束
        constraint = target_bone.constraints.new(type='CHILD_OF')
        constraint.name = "MMD_Emoji_Manager"

        # 设置约束目标
        armature = bpy.context.active_object
        constraint.target = bpy.data.objects.get(tyu)

        if bone_air:
            constraint.subtarget = panel_preset['bone']
        else:
            if subtarget_bone:
                constraint.subtarget = "頭"
            else:
                constraint.subtarget = "head"

        bpy.ops.pose.select_all(action='DESELECT')
        # 选中并激活骨骼
        bpy.ops.pose.select_all(action='DESELECT')  # 取消所有骨骼选择
        armature.data.bones.active = target_bone.bone  # 设置活动骨骼
        target_bone.select = True  # 选中骨骼
        # 反向
        bpy.ops.constraint.childof_set_inverse(constraint="MMD_Emoji_Manager", owner='BONE')
        bpy.ops.constraint.childof_clear_inverse(constraint="MMD_Emoji_Manager", owner='BONE')
        # 设置变换
        target_bone.rotation_mode = 'XYZ'
        target_bone.rotation_euler[0] = -1.5708 # X旋转
        target_bone.location[1] = -0.05 # Y位置
        target_bone.location[0] = 0.25 # X位置
        target_bone.scale[0] = 0.6
        target_bone.scale[1] = 0.6
        target_bone.scale[2] = 0.6
        # 骨骼形状
        target_bone.custom_shape = bpy.data.objects["rew_G2"]
        bpy.context.active_object.pose.bones.get("qws_F3").custom_shape = bpy.data.objects["rew_G3"]
        bpy.context.active_object.pose.bones.get("qws_F2").custom_shape = bpy.data.objects["rew_G1"]

        return {'FINISHED'}