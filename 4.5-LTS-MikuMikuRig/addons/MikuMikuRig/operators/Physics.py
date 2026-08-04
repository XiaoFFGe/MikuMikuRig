from math import radians

import bpy

# 添加阻尼跟踪
class Add_Damping_Tracking(bpy.types.Operator):
    '''Add_Damping_Tracking'''
    bl_idname = "mmr.add_damping_tracking"
    bl_label = "Add Damping Tracking"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):

        # 获取当前活动对象和骨骼
        obj = bpy.context.active_object

        # 获取选中骨骼列表
        selected_bones = [bone for bone in obj.pose.bones if bone.select]

        for bone in selected_bones:

            # 获取活动骨骼
            active_bone = obj.data.bones.get(bone.name)

            # 切换到编辑模式获取骨骼位置数据
            current_mode = bpy.context.object.mode

            # 获取MMR属性
            mmr = obj.mmr

            def get_bone_chain():

                if not obj or obj.type != 'ARMATURE':
                    return []

                if not active_bone:
                    return []

                bpy.ops.object.mode_set(mode='EDIT')

                try:
                    edit_bones = obj.data.edit_bones
                    bone_chain = []
                    current_bone = active_bone

                    while current_bone:  # 继续遍历直到没有下一个骨骼
                        # 添加当前骨骼到链
                        bone_chain.append(current_bone.name)

                        # 在编辑模式中获取当前骨骼对象
                        edit_bone = edit_bones[current_bone.name]
                        tail_pos = (round(edit_bone.tail[0], 4),
                                    round(edit_bone.tail[1], 4),
                                    round(edit_bone.tail[2], 4))

                        # 查找直接连接的下一个骨骼
                        next_bone = None
                        for child in current_bone.children:
                            child_edit = edit_bones[child.name]
                            head_pos = (round(child_edit.head[0], 4),
                                        round(child_edit.head[1], 4),
                                        round(child_edit.head[2], 4))

                            if head_pos == tail_pos:
                                next_bone = child
                                break  # 找到第一个连接的子骨骼

                        current_bone = next_bone  # 移动到下一个骨骼或结束循环

                    return bone_chain

                finally:
                    # 恢复原始模式
                    bpy.ops.object.mode_set(mode=current_mode)

            bone_chain = get_bone_chain()

            if bone_chain:
                # 检查是否有MMR-Target骨骼
                if not any(bone.endswith("_MMR-Target") for bone in bone_chain):
                    # 切换到编辑模式
                    bpy.ops.object.mode_set(mode='EDIT')
                    edit_bones = obj.data.edit_bones
                    bone = edit_bones.get(bone_chain[-1])
                    if bone:
                        # 新建一个骨骼
                        new_name = bone.name + "_MMR-Target"
                        new_bone = edit_bones.new(new_name)
                        new_bone.head = bone.tail
                        new_bone.tail.x = bone.tail.x
                        new_bone.tail.y = bone.tail.y
                        new_bone.tail.z = bone.tail.z + bone.length
                        new_bone.roll = bone.roll
                        new_bone.parent = bone
                        bone_chain.append(new_bone.name)
                        # 切换回原始模式
                        bpy.ops.object.mode_set(mode=current_mode)
                        new_bone = obj.data.bones.get(new_name)
                        new_bone.hide = True

            # 列表长度
            list_len = len(bone_chain)

            # 打印骨骼名称和索引
            added_count = 0  # 记录添加的约束数量
            for index, bone_name in enumerate(bone_chain):
                print(f"骨骼名称: {bone_name}, 索引: {index}")

                if index == list_len - 1:  # 检查是否是最后一个元素
                    continue  # 跳过最后一个骨骼

                # 获取骨骼
                current_bone = obj.pose.bones.get(bone_name)
                # 获取子骨骼
                children_bones = obj.pose.bones.get(bone_chain[index + 1])

                # 检查骨骼是否存在
                if not current_bone:
                    print(f"警告: 未找到骨骼 '{bone_name}'，跳过")
                    continue

                if not children_bones:
                    print(f"警告: 未找到子骨骼 '{bone_chain[index + 1]}'，跳过")
                    continue

                # 先删除旧的约束(只删除名为"MMR-阻尼追踪"的约束)
                constraint_to_remove = None
                for constraint in current_bone.constraints:
                    if constraint.name == "MMR-阻尼追踪":
                        constraint_to_remove = constraint
                        break

                if constraint_to_remove:
                    current_bone.constraints.remove(constraint_to_remove)

                # 添加阻尼追踪约束
                constraint = current_bone.constraints.new(type='DAMPED_TRACK')
                constraint.name = "MMR-阻尼追踪"
                constraint.target = obj
                constraint.subtarget = children_bones.name  # 子骨骼
                constraint.influence = mmr.Softness
                added_count += 1

            # 操作完成后给出提示
            if added_count > 0:
                print(f"成功添加 {added_count} 个阻尼追踪约束")

        return {'FINISHED'}

# 设置选择骨骼的阻尼追踪影响
class Set_Damping_Tracking_Influence(bpy.types.Operator):
    '''Set_Damping_Tracking_Influence'''
    bl_idname = "mmr.set_damping_tracking_influence"
    bl_label = "Set Damping Tracking Influence"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    @classmethod
    def poll(cls, context):
        """验证是否可以执行操作"""
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):
        # 获取当前活动对象和骨骼
        obj = bpy.context.active_object

        # 获取选中骨骼列表
        selected_bones = [bone for bone in obj.pose.bones if bone.select]

        # 检查是否有选中的骨骼
        if not selected_bones:
            self.report({'WARNING'}, "请选择骨骼")
            return {'CANCELLED'}

        modified_count = 0  # 记录修改的约束数量

        for bone in selected_bones:
            # 检查是否存在阻尼追踪约束
            if "MMR-阻尼追踪" not in bone.constraints.keys():
                continue

            constraint = bone.constraints.get("MMR-阻尼追踪")
            if not constraint:
                continue

            # 根据布尔值设置影响值
            if context.active_pose_bone.mmr_bone.Damping_Tracking_bool:
                # 启用约束
                if bone.mmr_bone.Damping_Tracking_influence != 0.0:
                    # 恢复之前保存的影响值
                    constraint.influence = bone.mmr_bone.Damping_Tracking_influence
                    modified_count += 1
            else:
                # 禁用约束
                if constraint.influence != 0.0:
                    # 存储当前影响值
                    bone.mmr_bone.Damping_Tracking_influence = constraint.influence
                    # 设置影响为0
                    constraint.influence = 0
                    modified_count += 1

        # 是否插入关键帧
        if context.active_pose_bone.mmr_bone.Insert_dt_keyframe:
            keyframe_count = 0
            for bone in selected_bones:
                if "MMR-阻尼追踪" in bone.constraints.keys():
                    constraint = bone.constraints["MMR-阻尼追踪"]
                    constraint.keyframe_insert(data_path="influence")
                    keyframe_count += 1

            if keyframe_count > 0:
                print(f"已插入 {keyframe_count} 个关键帧")
        else:
            if modified_count > 0:
                print(f"成功修改 {modified_count} 个阻尼追踪约束")
            else:
                print(f"没有需要修改的阻尼追踪约束")



        return {'FINISHED'}

# 删除阻尼追踪约束
class Remove_Damping_Tracking(bpy.types.Operator):
    '''Remove_Damping_Tracking'''
    bl_idname = "mmr.remove_damping_tracking"
    bl_label = "Remove Damping Tracking"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):

        # 获取当前活动对象和骨骼
        obj = bpy.context.active_object

        # 获取选中骨骼列表
        selected_bones = [bone for bone in obj.pose.bones if bone.select]

        for bone in selected_bones:

            # 获取活动骨骼
            active_bone = obj.data.bones.get(bone.name)

            current_mode = bpy.context.object.mode

            # 获取MMR属性
            mmr = obj.mmr

            def get_bone_chain():

                if not obj or obj.type != 'ARMATURE':
                    return []

                if not active_bone:
                    return []

                bpy.ops.object.mode_set(mode='EDIT')

                try:
                    edit_bones = obj.data.edit_bones
                    bone_chain = []
                    current_bone = active_bone

                    while current_bone:  # 继续遍历直到没有下一个骨骼
                        # 添加当前骨骼到链
                        bone_chain.append(current_bone.name)

                        # 在编辑模式中获取当前骨骼对象
                        edit_bone = edit_bones[current_bone.name]
                        tail_pos = (round(edit_bone.tail[0], 4),
                                    round(edit_bone.tail[1], 4),
                                    round(edit_bone.tail[2], 4))

                        # 查找直接连接的下一个骨骼
                        next_bone = None
                        for child in current_bone.children:
                            child_edit = edit_bones[child.name]
                            head_pos = (round(child_edit.head[0], 4),
                                        round(child_edit.head[1], 4),
                                        round(child_edit.head[2], 4))

                            if head_pos == tail_pos:
                                next_bone = child
                                break  # 找到第一个连接的子骨骼

                        current_bone = next_bone  # 移动到下一个骨骼或结束循环

                    return bone_chain

                finally:
                    # 恢复原始模式
                    bpy.ops.object.mode_set(mode=current_mode)

            bone_chain = get_bone_chain()

            # 删除阻尼追踪约束
            removed_count = 0  # 记录删除的约束数量
            for bone_name in bone_chain:
                bone = obj.pose.bones.get(bone_name)
                if bone:
                    # 只删除名为"MMR-阻尼追踪"的约束
                    constraint_to_remove = None
                    for constraint in bone.constraints:
                        if constraint.name == "MMR-阻尼追踪":
                            constraint_to_remove = constraint
                            break

                    if constraint_to_remove:
                        bone.constraints.remove(constraint_to_remove)
                        removed_count += 1

            # 删除 _MMR-Target 辅助骨骼
            target_bones_to_remove = []
            for bone_name in bone_chain:
                if bone_name.endswith("_MMR-Target"):
                    target_bones_to_remove.append(bone_name)

            # 如果有辅助骨骼需要删除
            if target_bones_to_remove:
                # 切换到编辑模式删除骨骼
                bpy.ops.object.mode_set(mode='EDIT')
                try:
                    edit_bones = obj.data.edit_bones
                    removed_bones_count = 0

                    for target_bone_name in target_bones_to_remove:
                        # 检查编辑骨骼是否存在
                        if target_bone_name in edit_bones:
                            edit_bone = edit_bones[target_bone_name]
                            # 删除编辑骨骼
                            edit_bones.remove(edit_bone)
                            removed_bones_count += 1

                finally:
                    # 恢复原始模式
                    bpy.ops.object.mode_set(mode=current_mode)

                # 操作完成后给出提示
                if removed_count > 0 and removed_bones_count > 0:
                    print(f"成功删除 {removed_count} 个阻尼追踪约束和 {removed_bones_count} 个辅助骨骼")
                elif removed_count > 0:
                    print(f"成功删除 {removed_count} 个阻尼追踪约束")
                elif removed_bones_count > 0:
                    print(f"成功删除 {removed_bones_count} 个辅助骨骼")
            else:
                # 操作完成后给出提示
                if removed_count > 0:
                    print(f"成功删除 {removed_count} 个阻尼追踪约束")
                else:
                    print(f"未找到阻尼追踪约束")

        return {'FINISHED'}

# MMD刚体转换MMR刚体
class mmdrigidbody_to_mmrrigidbody(bpy.types.Operator):
    '''mmdrigidbody_to_mmrrigidbody'''
    bl_idname = "mmr.mmd_rigidbody_to_mmr_rigidbody"
    bl_label = "MMD Rigidbody to MMR Rigidbody"
    bl_description = "MMD刚体转MMR刚体"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):

        global joints_collection, armature, collection

        active_obj = bpy.context.active_object

        # 只能循环50次, 防止无限循环
        i = 50

        # 循环, 直到找到MMD根对象
        while active_obj.mmd_type != 'ROOT':
            # 循环次数减一
            i -= 1
            if i <= 0:
                self.report({'ERROR'}, f"未找到MMD根对象")
                return {'CANCELLED'}
            active_obj = active_obj.parent

        # 检查活动物体是否是MMD模型
        if active_obj.mmd_type != 'ROOT':
            self.report({'ERROR'}, "请选择MMD根对象")
            return {'CANCELLED'}

        root =  active_obj

        root.mmr_bone.mmr_type = "ROOT"

        for child in root.children:
            # 名称有"rigidbodies"
            if "rigidbodies" in child.name:
                collection = child
            # 名称有"joints"
            if "joints" in child.name:
                joints_collection = child
            # type是"armature"
            if child.type == 'ARMATURE':
                armature = child

        # 获取物体"rigidbodies"的子物体
        children_bones = collection.children
        if collection:
            # 遍历集合中的所有对象
            for obj in children_bones:
                if obj.type == 'MESH':  # 只处理网格对象
                    if obj.rigid_body:
                        obj.mmr_bone.collision_group_mask = obj.mmd_rigid.collision_group_mask
                        obj.mmr_bone.collision_group_index = obj.mmd_rigid.collision_group_number
                        obj.mmr_bone.bone = obj.mmd_rigid.bone
                        # 面板布尔值
                        obj.mmr_bone.panel_bool = True
                        obj.mmr_bone.rigidbody_type = obj.mmd_rigid.type
                        obj.mmr_bone.mmr_type = "RIGIDBODY"

        # 获取物体"joints"的子物体
        children_joints = joints_collection.children
        if joints_collection:
            # 遍历集合中的所有对象
            for obj in children_joints:
                if obj.type == 'EMPTY':
                    obj.mmr_bone.mmr_type = "JOINT"

        # 获取物体"armature"的子物体
        children_armature = armature.children
        armature.mmr_bone.mmr_type = "ARMATURE"
        if armature:
            # 遍历集合中的所有对象
            for obj in children_armature:
                if obj.type == 'MESH':  # 只处理网格对象
                    if obj.rigid_body:
                        obj.mmr_bone.collision_group_mask = obj.mmd_rigid.collision_group_mask
                        obj.mmr_bone.collision_group_index = obj.mmd_rigid.collision_group_number
                        obj.mmr_bone.bone = obj.mmd_rigid.bone
                        # 面板布尔值
                        obj.mmr_bone.panel_bool = True
                        obj.mmr_bone.rigidbody_type = obj.mmd_rigid.type
                        obj.mmr_bone.mmr_type = "RIGIDBODY"

        context.scene.mmr.mmd_rigid_panel_bool = True

        return {'FINISHED'}

# MMR刚体转换MMD刚体
class mmr_rigidbody_to_mmd_rigidbody(bpy.types.Operator):
    '''mmrrigidbody_to_mmdrigidbody'''
    bl_idname = "mmr.mmr_rigidbody_to_mmd_rigidbody"
    bl_label = "MMR Rigidbody to MMD Rigidbody"
    bl_description = "MMR刚体转MMD刚体"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    def execute(self, context):

        global joints_collection, armature, collection

        active_obj = bpy.context.active_object

        # 只能循环50次, 防止无限循环
        i = 50

        # 循环, 直到找到MMD根对象
        while active_obj.mmd_type != 'ROOT':
            # 循环次数减一
            i -= 1
            if i <= 0:
                self.report({'ERROR'}, f"未找到MMD根对象")
                return {'CANCELLED'}
            active_obj = active_obj.parent

        # 检查活动物体是否是MMD模型
        if active_obj.mmd_type != 'ROOT':
            self.report({'ERROR'}, "请选择MMD根对象")
            return {'CANCELLED'}

        root = active_obj

        root.mmr_bone.mmr_type = "ROOT"

        for child in root.children:
            # 名称有"rigidbodies"
            if "rigidbodies" in child.name:
                collection = child
            # 名称有"joints"
            if "joints" in child.name:
                joints_collection = child
            # type是"armature"
            if child.type == 'ARMATURE':
                armature = child

        # 获取物体"rigidbodies"的子物体
        children_bones = collection.children
        if collection:
            # 遍历集合中的所有对象
            for obj in children_bones:
                if obj.type == 'MESH':  # 只处理网格对象
                    if obj.rigid_body:
                        obj.mmd_rigid.collision_group_mask = obj.mmr_bone.collision_group_mask
                        obj.mmd_rigid.collision_group_number = obj.mmr_bone.collision_group_index
                        obj.mmd_rigid.bone = obj.mmr_bone.bone
                        obj.mmd_rigid.type = obj.mmr_bone.rigidbody_type
                        # 面板布尔值
                        obj.mmr_bone.panel_bool = False

        # 获取物体"armature"的子物体
        children_armature = armature.children
        if armature:
            # 遍历集合中的所有对象
            for obj in children_armature:
                if obj.type == 'MESH':  # 只处理网格对象
                    if obj.rigid_body:
                        obj.mmd_rigid.collision_group_mask = obj.mmr_bone.collision_group_mask
                        obj.mmd_rigid.collision_group_number = obj.mmr_bone.collision_group_index
                        obj.mmd_rigid.bone = obj.mmr_bone.bone
                        obj.mmd_rigid.type = obj.mmr_bone.rigidbody_type
                        # 面板布尔值
                        obj.mmr_bone.panel_bool = False

        context.scene.mmr.mmd_rigid_panel_bool = False

        return {'FINISHED'}

# 装配刚体
class Assign_Rigidbody(bpy.types.Operator):
    '''Assign_Rigidbody'''
    bl_idname = "mmr.assign_rigidbody"
    bl_label = "Assign physics"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    # 非碰撞距离缩放系数属性
    non_collision_distance_scale: bpy.props.FloatProperty(
        name="Non-Collision Distance Scale",  # 属性显示名称
        description="The distance scale for creating extra non-collision constraints while building physics",  # 属性描述
        min=0,  # 最小值
        soft_max=50,  # 软最大值
        default=1.6,  # 默认值
    )

    # 碰撞边距属性
    collision_margin: bpy.props.FloatProperty(
        name="Collision Margin",  # 属性显示名称
        description="The collision margin between rigid bodies. If 0, the default value for each shape is adopted.",  # 属性描述
        unit="LENGTH",  # 单位类型
        min=0,  # 最小值
        soft_max=10,  # 软最大值
        default=1e-06,  # 默认值
    )

    # 是否在播放动画
    @classmethod
    def poll(cls, context):
        # 如果正在播放动画，则禁止操作
        if context.screen and context.screen.is_animation_playing:
            return False
        return True

    def execute(self, context):

        # 获取当前活动对象
        active_obj = bpy.context.active_object

        context_frame = bpy.context.scene.frame_current  # 当前帧
        frame_start = bpy.context.scene.rigidbody_world.point_cache.frame_start  # 缓存开始帧

        if context_frame != frame_start:
            bpy.context.scene.frame_current = frame_start  # 设置当前帧为缓存开始帧
            self.report({'WARNING'}, f"当前帧{context_frame}与缓存开始帧{frame_start}不一致, 已自动调整为缓存开始帧, 请重新执行")
            return {'FINISHED'}

        bpy.context.scene.frame_set(frame_start)  # 更新场景帧
        bpy.context.view_layer.update()  # 更新视图层

        try:
            # 只能循环50次, 防止无限循环
            i = 50

            # 循环, 直到找到MMD根对象
            while active_obj.mmr_bone.mmr_type != 'ROOT':
                # 循环次数减一
                i -= 1
                if i <= 0:
                    self.report({'ERROR'}, f"未找到MMD根对象")
                    return {'CANCELLED'}

                active_obj = active_obj.parent
        except AttributeError:
            bpy.ops.mmr.mmd_rigidbody_to_mmr_rigidbody()
            self.report({'ERROR'}, f"已转换为MMR刚体,请再点一次")
            return {'CANCELLED'}

        # 获取MMD根对象
        root = active_obj

        if root.mmr.physics_bool:
            self.report({'INFO'}, "已开启物理")
            return {'CANCELLED'}

        root.mmr.physics_bool = True # 标记开启物理

        collection_name = F"{root.name}_mmr_temp_object"

        # 获取当前视图层
        view_layer = bpy.context.view_layer

        # 判断集合是否存在
        if collection_name not in bpy.data.collections:
            # 创建集合
            temp_object = bpy.data.collections.new(collection_name)
            # 链接到场景
            bpy.context.collection.children.link(temp_object)
        else:
            temp_object = bpy.data.collections[collection_name]

        collection = None
        temp_collection = None
        joints_collection = None
        armature = None

        # 处理过的刚体对
        Processed_Rigidbody = set()

        rigidbody_bone_names = []

        rigidbody_objects = []

        joints_objects = []

        for child in root.children:
            print(child.name)
            # 名称有"rigidbodies"
            if "rigidbodies" in child.name:
                collection = child
            # 名称有"temporary"
            if "temporary" in child.name:
                temp_collection = child
            # 名称有"joints"
            if "joints" in child.name:
                joints_collection = child
            # type是"armature"
            if child.type == 'ARMATURE':
                armature = child

        # 如果没有"temporary"，则创建一个
        if not temp_collection:
            temp_collection = bpy.data.objects.new("temporary", None)
            # 将空物体链接到场景
            temp_object.objects.link(temp_collection)

        temp_collection.hide_set(True) # 隐藏空物体

        if not collection or not joints_collection or not armature:
            self.report({'WARNING'}, "未找到'rigidbodies'或'joints'或'MMD Model_arm'对象")
            return {'CANCELLED'}

        # 预处理"joints"
        for joint in joints_collection.children:
            if joint.rigid_body_constraint: # 只处理有刚体约束的关节
                if joint.type == 'EMPTY': # 只处理空物体关节
                    constraint = joint.rigid_body_constraint
                    constraint.disable_collisions = True
                    obj1 = constraint.object1
                    obj2 = constraint.object2
                    pair = frozenset([obj1,obj2]) # 有序对
                    Processed_Rigidbody.add(pair) # 添加到处理过的刚体对中
                    joints_objects.append(joint)

        # 预处理"rigidbodies"
        for obj in collection.children:
            if obj.type == 'MESH': # 只处理网格对象
                obj.rigid_body.use_margin = True
                obj.rigid_body.collision_margin = self.collision_margin
                rigidbody_bone_names.append(obj.mmr_bone.bone)
                if obj.mmr_bone.panel_bool:
                    rigidbody_objects.append(obj)

                    # 删除刚体所有约束
                for constraint in obj.constraints:
                    if constraint:
                        obj.constraints.remove(constraint)

        # 新建空物体
        empty = bpy.data.objects.new(f"empty", None)
        # 将空物体链接到场景
        temp_object.objects.link(empty)
        # 空物体父物体设置为"temporary"
        empty.parent = temp_collection

        empty.hide_set(True) # 隐藏空物体

        # 创建空物体的刚体约束
        bpy.context.view_layer.objects.active = empty
        bpy.ops.rigidbody.constraint_add()

        idxs = 0

        def __getRigidRange(obj: bpy.types.Object) -> float:
            """计算刚体对象的最大尺寸范围"""
            x0, y0, z0 = obj.bound_box[0]  # 获取边界框的最小点
            x1, y1, z1 = obj.bound_box[6]  # 获取边界框的最大点
            return max(x1 - x0, y1 - y0, z1 - z0)  # 返回三个轴向的最大尺寸

        def add__rigidbody_constraint(rigidbody,other_rigidbody):
            # 复制空物体
            empty_copy = empty.copy()
            # 将复制的空物体链接到场景
            temp_object.objects.link(empty_copy)
            empty_copy.hide_set(True) # 隐藏空物体
            # 设置空物体的刚体约束
            constraint = empty_copy.rigid_body_constraint
            constraint.disable_collisions = True
            constraint.object1 = rigidbody
            constraint.object2 = other_rigidbody
            constraint.type = 'GENERIC'

        def Assemble_skeletal_rigidbody(rigidbody):

            i = 0
            for idx, other_rigidbody in enumerate(rigidbody_objects):
                if other_rigidbody.name == rigidbody.name:
                    i = idx

            print(f"刚体：{rigidbody.name}，{i}/{len(rigidbody_objects)}")

            # 获取骨骼
            bone = armature.data.bones.get(rigidbody.mmr_bone.bone)

            # 获取姿态骨骼
            pose_bone = armature.pose.bones.get(rigidbody.mmr_bone.bone)
            # 获取姿态骨骼矩阵
            pose_bone_matrix = pose_bone.matrix
            # 计算姿态骨骼的全局矩阵
            pose_bone_global_matrix = armature.matrix_world @ pose_bone_matrix

            # 获取骨骼矩阵
            bone_matrix = bone.matrix_local
            # 计算全局矩阵
            global_bone_matrix = armature.matrix_world @ bone_matrix

            # 刚体世界矩阵
            rigidbody_world_matrix = rigidbody.matrix_world
            # 计算相对变换,global_bone_matrix 到 rigidbody_world_matrix 的变换矩阵
            relative_transform = global_bone_matrix.inverted() @ rigidbody_world_matrix

            rigidbody.parent = armature
            rigidbody.parent_type = 'BONE'
            rigidbody.parent_bone = bone.name

            # 应用相对变换到刚体
            rigidbody.matrix_world = pose_bone_global_matrix @ relative_transform

        def Assemble_Physical_Rigidbody(bone, rigidbody, mode = '0'):
            print("骨骼：",bone.name, "刚体：",rigidbody.name)

            # 获取骨骼矩阵
            bone_matrix_local = bone.matrix_local
            bone_matrix_global = armature.matrix_world @ bone_matrix_local # 计算骨骼的全局矩阵 , 初始变换

            # 获取姿态骨骼
            pose_bone = armature.pose.bones.get(rigidbody.mmr_bone.bone)
            # 获取姿态骨骼矩阵
            pose_bone_matrix = pose_bone.matrix
            # 计算姿态骨骼的全局矩阵
            pose_bone_global_matrix = armature.matrix_world @ pose_bone_matrix

            # 刚体矩阵
            rigidbody_matrix_world = rigidbody.matrix_world

            # 计算相对变换,bone_matrix_global 到 rigidbody_matrix_world 的变换矩阵
            relative_transform = bone_matrix_global.inverted() @ rigidbody_matrix_world
            # 应用相对变换到刚体
            rigidbody.matrix_world =  pose_bone_global_matrix @ relative_transform

            # 复制空物体
            empty_1 = bpy.data.objects.new(f"empty_{rigidbody.name}_{joint.name}", None)
            # 将空物体链接到场景
            temp_object.objects.link(empty_1)
            # 显示大小
            empty_1.empty_display_size = 0.08 # 空物体显示大小
            # 空物体父物体设置为"temporary"
            empty_1.parent = temp_collection

            empty_1.hide_set(True) # 隐藏空物体

            # 子级
            constraint = empty_1.constraints.new(type='CHILD_OF')
            constraint.name = "mmr_physics"
            constraint.target = rigidbody

            empty_1.matrix_world = pose_bone_global_matrix # 空物体矩阵设置为姿态骨骼的全局矩阵

            if mode == '1':
                # 为骨骼加复制变换约束
                constraint = pose_bone.constraints.new(type='COPY_TRANSFORMS')
                constraint.name = "mmr_physics"
                constraint.target = empty_1

            if mode == '2':
                # 为骨骼加复制旋转约束
                constraint = pose_bone.constraints.new(type='COPY_ROTATION')
                constraint.name = "mmr_physics"
                constraint.target = empty_1

        def Assemble_Physical_Joint(joint, rigidbody):
            print("关节：",joint.name, "刚体：",rigidbody.name, "骨骼：",rigidbody.mmr_bone.bone)

            # 获取姿态骨骼
            pose_bone = armature.pose.bones.get(rigidbody.mmr_bone.bone)
            # 获取骨骼
            bone = armature.data.bones.get(rigidbody.mmr_bone.bone)

            # 检查骨骼是否存在
            if pose_bone is None or bone is None:
                print(f"警告：找不到骨骼 '{rigidbody.mmr_bone.bone}'，跳过关节装配")
                return

            # 获取姿态骨骼矩阵
            pose_bone_matrix = pose_bone.matrix
            # 计算姿态骨骼的全局矩阵
            pose_bone_global_matrix = armature.matrix_world @ pose_bone_matrix

            # 获取骨骼矩阵
            bone_matrix = bone.matrix_local
            # 计算全局矩阵
            global_bone_matrix = armature.matrix_world @ bone_matrix

            # joint矩阵
            joint_matrix_world = joint.matrix_world

            # 计算相对变换
            relative_transform = global_bone_matrix.inverted() @ joint_matrix_world

            # 应用相对变换到关节
            joint.matrix_world = pose_bone_global_matrix @ relative_transform

        for idx, rigidbody in enumerate(rigidbody_objects):
            if rigidbody.type == 'MESH': # 只处理网格对象
                # 遍历其他刚体
                for other_rigidbody in rigidbody_objects:
                    if other_rigidbody.type == 'MESH': # 只处理网格对象
                        if other_rigidbody != rigidbody: # 排除自身

                            # 存储碰撞组遮罩
                            u = []
                            for i, bit in enumerate(rigidbody.mmr_bone.collision_group_mask):
                                if bit:
                                    u.append([i, bit])

                            for i in u:
                                if i[0] == other_rigidbody.mmr_bone.collision_group_index:

                                    pair = frozenset([rigidbody, other_rigidbody]) # 有序对

                                    # 检查是否已处理过
                                    if pair not in Processed_Rigidbody:
                                        # 计算两个刚体之间的距离
                                        distance = (rigidbody.location - other_rigidbody.location).length
                                        # 如果距离小于阈值，创建非碰撞约束
                                        if distance < self.non_collision_distance_scale * ((__getRigidRange(rigidbody) + __getRigidRange(other_rigidbody)) * 0.45):
                                            print(f'<{(idx/len(rigidbody_objects))*100:.2f}%> {idx}/{len(rigidbody_objects)}',
                                                  rigidbody.name, "与", other_rigidbody.name, "禁用碰撞", f'距离：{distance:.2f}')
                                            # 添加刚体约束
                                            add__rigidbody_constraint(rigidbody,other_rigidbody)
                                            idxs += 1
                                            # 处理过的刚体添加到列表
                                            Processed_Rigidbody.add(pair)

        for rigidbody in rigidbody_objects:
            if rigidbody.mmr_bone.rigidbody_type == '0':
                # 装配骨骼刚体
                Assemble_skeletal_rigidbody(rigidbody)

        Processed_Rigidbody = set() # 已处理过的刚体列表

        for rigidbody in rigidbody_objects:
            if rigidbody.mmr_bone.rigidbody_type == '1':
                # 检查是否已处理过
                if rigidbody not in Processed_Rigidbody:
                    bone = armature.data.bones.get(rigidbody.mmr_bone.bone)
                    if bone is None:
                        continue
                    Assemble_Physical_Rigidbody(bone, rigidbody, mode = '1')
                    # 处理过的刚体添加到列表
                    Processed_Rigidbody.add(rigidbody)

        for rigidbody in rigidbody_objects:
            if rigidbody.mmr_bone.rigidbody_type == '2':
                # 检查是否已处理过
                if rigidbody not in Processed_Rigidbody:
                    bone = armature.data.bones.get(rigidbody.mmr_bone.bone)
                    if bone is None:
                        continue
                    Assemble_Physical_Rigidbody(bone, rigidbody, mode = '2')
                    # 处理过的刚体添加到列表
                    Processed_Rigidbody.add(rigidbody)

        Processed_Joints = set() # 已处理过的关节列表

        for joint in joints_objects:
            # 检查是否已处理过
            if joint not in Processed_Joints:

                rigidbody = joint.rigid_body_constraint.object2
                # 装配物理关节
                Assemble_Physical_Joint(joint, rigidbody)
                # 处理过的关节添加到列表
                Processed_Joints.add(joint)

        bpy.context.scene.frame_set(frame_start)  # 更新场景变化
        bpy.context.view_layer.update()  # 更新视图层

        bpy.context.scene.frame_current = context_frame  # 设置当前帧

        bpy.context.scene.rigidbody_world.enabled = True  # 启用物理模拟

        bpy.context.view_layer.objects.active = root  # 设置活动对象为根

        # 标记已构建
        root.mmr.mmr_root_is_built = True

        print('-' * 20)
        self.report({'INFO'}, f"共创建{idxs}个刚体约束")
        return {'FINISHED'}

# 解除物理
class Remove_physics(bpy.types.Operator):
    '''Remove_physics'''

    bl_idname = "mmr.remove_physics"
    bl_label = "Remove physics"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能


    # 是否在播放动画
    @classmethod
    def poll(cls, context):
        # 如果正在播放动画，则禁止操作
        if context.screen and context.screen.is_animation_playing:
            return False
        return True

    def execute(self, context):

        context_frame = bpy.context.scene.frame_current  # 当前帧
        frame_start = bpy.context.scene.rigidbody_world.point_cache.frame_start  # 缓存开始帧

        if context_frame != frame_start:
            bpy.context.scene.frame_current = frame_start  # 设置当前帧为缓存开始帧
            self.report({'WARNING'}, f"当前帧{context_frame}与缓存开始帧{frame_start}不一致, 已自动调整为缓存开始帧, 请重新执行")
            return {'FINISHED'}

        bpy.context.scene.frame_set(frame_start)  # 更新场景帧
        bpy.context.view_layer.update()  # 更新视图层

        # 获取当前活动对象
        global armature, collection, joints_collection
        active_obj = bpy.context.active_object

        # 只能循环50次, 防止无限循环
        i = 50

        # 循环, 直到找到MMD根对象
        while active_obj.mmr_bone.mmr_type != 'ROOT':
            # 循环次数减一
            i -= 1
            if i <= 0:
                self.report({'ERROR'}, f"未找到MMD根对象")
                return {'CANCELLED'}
            active_obj = active_obj.parent

        # 获取MMD根对象
        root = active_obj

        if not root.mmr.physics_bool:
            self.report({'INFO'}, "未开启物理")
            return {'CANCELLED'}

        root.mmr.physics_bool = False # 标记关闭物理

        collection_name = F"{root.name}_mmr_temp_object"

        # 判断集合是否存在
        if collection_name in bpy.data.collections:
            temp_object = bpy.data.collections[collection_name]
        else:
            self.report({'ERROR'}, f"未找到{collection_name}集合")
            return {'CANCELLED'}

        def setRigidBodyWorldEnabled(enable: bool) -> bool:
            """启用或禁用刚体世界"""
            if bpy.ops.rigidbody.world_add.poll():
                bpy.ops.rigidbody.world_add()  # 如果不存在刚体世界则创建
            rigidbody_world = bpy.context.scene.rigidbody_world
            enabled = rigidbody_world.enabled  # 保存当前状态
            rigidbody_world.enabled = enable  # 设置新状态
            return enabled

        for child in root.children:
             # type是"armature"
            if child.type == 'ARMATURE':
                armature = child

            # 名称有"rigidbodies"
            if "rigidbodies" in child.name:
                collection = child

            # 名称有"joints"
            if "joints" in child.name:
                joints_collection = child

        context_frame = bpy.context.scene.frame_current # 当前帧
        frame_start = bpy.context.scene.rigidbody_world.point_cache.frame_start # 缓存开始帧
        bpy.context.scene.frame_current = frame_start # 设置当前帧为缓存开始帧
        bpy.context.scene.frame_set(frame_start) # 更新场景变化
        bpy.context.view_layer.update() # 更新视图层

        bpy.ops.screen.animation_cancel() # 取消动画

        # 临时禁用刚体世界并保存当前启用状态
        rigidbody_world_enabled = setRigidBodyWorldEnabled(False)


        bpy.ops.object.select_all(action='DESELECT')

        # 找到"temporary"
        for obj in temp_object.objects:
            if obj is None:
                continue
            print(obj.name)
            # 类型是"empty"
            if obj.type == 'EMPTY':
                # 名称有"temporary"
                if "temporary" in obj.name:

                    # 取捎隐藏
                    obj.hide_set(False)
                    # 选中物体
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj

                    for child in obj.children:
                        print(child.name)
                        # 取捎隐藏
                        child.hide_set(False)
                        # 选中物体
                        child.select_set(True)
                        bpy.context.view_layer.objects.active = child

        bpy.ops.object.delete(use_global=False, confirm=False) # 删除选中物体

        def Recovery_matrix(rigidbody, bone_name=None):

            if bone_name is None:
                # 指定的骨骼名称
                bone_name = rigidbody.mmr_bone.bone

            # 检查bone_name是否为空字符串
            if not bone_name:
                print(f"警告：骨骼名称为空，跳过恢复矩阵")
                return

            if rigidbody.mmr_bone.mmr_type == 'RIGIDBODY':

                # 刚体全局矩阵
                rigidbody_matrix_world = rigidbody.matrix_world
                # 获取姿态骨骼
                pose_bone = armature.pose.bones[bone_name]

                # 检查姿态骨骼是否存在
                if pose_bone is None:
                    print(f"警告：找不到姿态骨骼 '{bone_name}'，跳过关节装配")
                    return

                # 获取姿态骨骼矩阵
                pose_bone_matrix = pose_bone.matrix
                # 计算姿态骨骼的全局矩阵
                pose_bone_global_matrix = armature.matrix_world @ pose_bone_matrix

                # 获取数据骨骼
                data_bone = armature.data.bones[bone_name]
                # 获取数据骨骼矩阵
                data_bone_matrix = data_bone.matrix_local
                # 计算数据骨骼的全局矩阵
                data_bone_global_matrix = armature.matrix_world @ data_bone_matrix

                # 计算相对变换矩阵
                relative_matrix = pose_bone_global_matrix.inverted() @ rigidbody_matrix_world

                rigidbody.parent = collection # 恢复父物体

                # 应用相对变换矩阵到刚体
                rigidbody.matrix_world = data_bone_global_matrix @ relative_matrix

            if rigidbody.mmr_bone.mmr_type == 'JOINT':
                joint = rigidbody
                # 获取关节的全局矩阵
                joint_matrix_world = joint.matrix_world

                # 获取姿态骨骼
                pose_bone = armature.pose.bones[bone_name]
                # 获取姿态骨骼矩阵
                pose_bone_matrix = pose_bone.matrix
                # 计算姿态骨骼的全局矩阵
                pose_bone_global_matrix = armature.matrix_world @ pose_bone_matrix

                # 获取数据骨骼
                data_bone = armature.data.bones[bone_name]
                # 获取数据骨骼矩阵
                data_bone_matrix = data_bone.matrix_local
                # 计算数据骨骼的全局矩阵
                data_bone_global_matrix = armature.matrix_world @ data_bone_matrix

                # 计算相对变换矩阵
                relative_matrix = pose_bone_global_matrix.inverted() @ joint_matrix_world

                # 应用相对变换矩阵到关节
                joint.matrix_world = data_bone_global_matrix @ relative_matrix

        Processed_Rigidbody = set() # 已处理过的刚体列表

        for child in armature.children:
            if child.mmr_bone.mmr_type == 'RIGIDBODY':
                # 检查是否已处理过
                if child not in Processed_Rigidbody:
                    # 恢复矩阵
                    Recovery_matrix(child)
                    # 处理过的刚体添加到列表
                    Processed_Rigidbody.add(child)

        for child in collection.children:
            if child.mmr_bone.mmr_type == 'RIGIDBODY':
                # 检查是否已处理过
                if child not in Processed_Rigidbody:
                    # 恢复矩阵
                    Recovery_matrix(child)
                    # 处理过的刚体添加到列表
                    Processed_Rigidbody.add(child)

        for joint in joints_collection.children:
            if joint.mmr_bone.mmr_type == 'JOINT':
                # 检查是否已处理过
                if joint not in Processed_Rigidbody:
                    # 获取刚体约束
                    rigidbody_constraint = joint.rigid_body_constraint
                    if rigidbody_constraint:
                        obj2 = rigidbody_constraint.object2 # 约束的刚体
                        bone_name1 = obj2.mmr_bone.bone # 骨骼名称
                        # 恢复矩阵
                        Recovery_matrix(joint, bone_name=bone_name1)
                        # 处理过的刚体添加到列表
                        Processed_Rigidbody.add(joint)

        # 名称包含'mmr_physics'的骨骼约束
        for bone in armature.pose.bones:
            constraints = bone.constraints
            for constraint in constraints:
                if constraint.name.startswith('mmr_physics'):
                    constraints.remove(constraint)

        bpy.context.scene.frame_set(frame_start) # 更新场景变化
        bpy.context.view_layer.update() # 更新视图层

        bpy.context.scene.frame_current = context_frame # 设置当前帧

        # 恢复刚体世界的原始启用状态
        setRigidBodyWorldEnabled(rigidbody_world_enabled)

        bpy.context.view_layer.objects.active = root  # 设置活动对象为根

        # 删除temp_object集合
        # 从父集合中移除
        for parent_coll in bpy.data.collections:
            if temp_object.name in parent_coll.children:
                parent_coll.children.unlink(temp_object)
                break

        # 删除集合本身
        bpy.data.collections.remove(temp_object)

        # 标记未构建
        root.mmr.mmr_root_is_built = False

        return {'FINISHED'}

# 显示刚体
class Show_Rigidbody(bpy.types.Operator):
    bl_idname = "mmr.show_rigidbody"
    bl_label = "Show Rigidbody"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        # 循环, 直到找到MMD根对象
        while obj.mmd_type != 'ROOT':
            obj = obj.parent

        obj_parent = obj

        if obj.mmr.show_rigid_bodies:
            # 隐藏
            for child in obj_parent.children:
                if "rigidbodies" in child.name:
                    for rigidbody in child.children:
                        rigidbody.hide_set(True)

                if child.type == 'ARMATURE':
                    for rigidbody in child.children:
                        if rigidbody.rigid_body:
                            rigidbody.hide_set(True)

            obj.mmr.show_rigid_bodies = False
        else:
            # 显示
            for child in obj_parent.children:
                if "rigidbodies" in child.name:
                    for rigidbody in child.children:
                        rigidbody.hide_set(False)

                if child.type  == 'ARMATURE':
                    for rigidbody in child.children:
                        if rigidbody.rigid_body:
                            rigidbody.hide_set(False)
            obj.mmr.show_rigid_bodies = True

        return {'FINISHED'}

# 显示关节
class Show_Joint(bpy.types.Operator):
    bl_idname = "mmr.show_joint"
    bl_label = "Show Joint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        obj = context.active_object

        # 循环, 直到找到MMD根对象
        while obj.mmd_type != 'ROOT':
            obj = obj.parent

        obj_parent = obj

        if obj.mmr.joint_show:
            # 隐藏
            for child in obj_parent.children:
                if "joints" in child.name:
                    for joint in child.children:
                        if joint.rigid_body_constraint:
                            joint.hide_set(True)
            obj.mmr.joint_show = False
        else:
            # 显示
            for child in obj_parent.children:
                if "joints" in child.name:
                    for joint in child.children:
                        if joint.rigid_body_constraint:
                            joint.hide_set(False)
            obj.mmr.joint_show = True

        return {'FINISHED'}

# 选择碰撞组
class Select_Collision_Group(bpy.types.Operator):
    bl_idname = "mmr.select_collision_group"
    bl_label = "Select Collision Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        obj_parent = obj.parent

        for child in obj_parent.children:
            if child.mmd_rigid.collision_group_number == obj.mmd_rigid.collision_group_number:
                child.select_set(True)

        return {'FINISHED'}

# 更新世界
class Update_World(bpy.types.Operator):
    bl_idname = "mmr.update_world"
    bl_label = "Update World"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        rigidbody_world = context.scene.rigidbody_world

        point_cache = rigidbody_world.point_cache

        scene.rigidbody_world.time_scale = 0.75

        scene.rigidbody_world.substeps_per_frame = 3
        scene.rigidbody_world.solver_iterations = 6

        point_cache.frame_end = scene.frame_end
        return {'FINISHED'}

# 按类型选择
class Select_By_Type(bpy.types.Operator):
    bl_idname = "mmr.select_by_type"
    bl_label = "Select By Type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        obj_parent = obj.parent

        for child in obj_parent.children:
            if child.mmd_rigid.type == obj.mmd_rigid.type:
                child.select_set(True)

        return {'FINISHED'}


# 选择碰撞组（关节）
class Select_Collision_Group_For_Joint(bpy.types.Operator):
    bl_idname = "mmr.select_collision_group_for_joint"
    bl_label = "Select Collision Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        obj_parent = obj.parent

        constraint = obj.rigid_body_constraint

        object2 = constraint.object2
        joint_index = object2.mmd_rigid.collision_group_number

        for child in obj_parent.children:
            child_constraint = child.rigid_body_constraint
            if child_constraint.object2.mmd_rigid.collision_group_number == joint_index:
                child.select_set(True)

        return {'FINISHED'}

# 按类型选择（关节）
class Select_By_Type_For_Joint(bpy.types.Operator):
    bl_idname = "mmr.select_by_type_for_joint"
    bl_label = "Select By Type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        obj_parent = obj.parent

        constraint = obj.rigid_body_constraint

        object2 = constraint.object2
        joint_type = object2.mmd_rigid.type

        for child in obj_parent.children:
            child_constraint = child.rigid_body_constraint
            if child_constraint.object2.mmd_rigid.type == joint_type:
                child.select_set(True)

        return {'FINISHED'}

# 清除碰撞组遮罩
class Clear_Collision_Group_Mask(bpy.types.Operator):
    bl_idname = "mmr.clear_collision_group_mask"
    bl_label = "Clear Collision Group Mask"
    bl_description = "清除碰撞组遮罩"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        set_objects = [obj for obj in context.selected_objects]

        for obj in set_objects:
            if obj.rigid_body:
                for index, group_mask in enumerate(obj.mmr_bone.collision_group_mask):
                    if obj.mmr_bone.collision_group_index != index:
                        obj.mmr_bone.collision_group_mask[index] = False

        return {'FINISHED'}

# 烘焙物理到骨骼
class Bake_Physics_To_Bone(bpy.types.Operator):

    bl_idname = "mmr.bake_physics_to_bone"
    bl_label = "Bake Physics To Bone"
    bl_description = "烘焙物理到骨骼"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'ARMATURE'

    def execute(self, context):

        arm = context.active_object

        bpy.ops.object.mode_set(mode='POSE')

        bpy.ops.pose.select_all(action='DESELECT')

        constraint_names = ['mmd_tools_rigid_track', 'mmr_physics']

        for constraint_name in constraint_names:
            for bone in arm.pose.bones:
                for constraint in bone.constraints:
                    if constraint.name == constraint_name:
                        bone.select = True

        start = bpy.context.scene.frame_start
        end = bpy.context.scene.frame_end

        bpy.ops.nla.bake(frame_start=start, frame_end=end, step=arm.mmr.Physics_frame_step, only_selected=True, visual_keying=True, clear_constraints=True,
                         use_current_action=True, clean_curves=True, bake_types={'POSE'})

        return {'FINISHED'}


# 选择所有刚体
class Select_All_Rigid_Bodies(bpy.types.Operator):
    bl_idname = "mmr.select_all_rigid_bodies"
    bl_label = "Select All"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "选择所有刚体"

    def execute(self, context):

        global joints_collection, armature, collection

        active_obj = bpy.context.active_object

        # 只能循环50次, 防止无限循环
        i = 50

        # 循环, 直到找到MMD根对象
        while active_obj.mmd_type != 'ROOT':
            # 循环次数减一
            i -= 1
            if i <= 0:
                self.report({'ERROR'}, f"未找到MMD根对象")
                return {'CANCELLED'}
            active_obj = active_obj.parent

        # 检查活动物体是否是MMD模型
        if active_obj.mmd_type != 'ROOT':
            self.report({'ERROR'}, "请选择MMD根对象")
            return {'CANCELLED'}

        root = active_obj

        root.mmr_bone.mmr_type = "ROOT"

        for child in root.children:
            # 名称有"rigidbodies"
            if "rigidbodies" in child.name:
                collection = child
            # 名称有"joints"
            if "joints" in child.name:
                joints_collection = child
            # type是"armature"
            if child.type == 'ARMATURE':
                armature = child

        # 获取物体"rigidbodies"的子物体
        children_bones = collection.children
        if children_bones:
            # 遍历集合中的所有对象
            for obj in children_bones:
                if obj.type == 'MESH':  # 只处理网格对象
                    if obj.rigid_body:

                        obj.select_set(True)

        # 获取物体"armature"的子物体
        children_armature = armature.children
        armature.mmr_bone.mmr_type = "ARMATURE"
        if armature:
            # 遍历集合中的所有对象
            for obj in children_armature:
                if obj.type == 'MESH':  # 只处理网格对象
                    if obj.rigid_body:

                        obj.select_set(True)

        return {'FINISHED'}

# 设置选择骨骼的约束影响
class Set_Constraint_Influence(bpy.types.Operator):
    bl_idname = "mmr.set_constraint_influence"
    bl_label = "Set Constraint Influence"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "设置选择骨骼的约束影响"

    def _get_constraint_name(self, context):
        """根据枚举值获取约束名称"""
        mmr_obj = context.object.mmr
        if mmr_obj.constraintswitchtool_name_enum == "0":
            return mmr_obj.constraintswitchtool_name
        elif mmr_obj.constraintswitchtool_name_enum == "1":
            return "mmr_physics"
        elif mmr_obj.constraintswitchtool_name_enum == "2":
            return "mmd_tools_rigid_track"
        elif mmr_obj.constraintswitchtool_name_enum == "3":
            return "MMR-阻尼追踪"
        return ""

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            return {'CANCELLED'}

        # 获取约束名称
        constraint_name = self._get_constraint_name(context)
        if not constraint_name:
            self.report({'ERROR'}, "未指定约束名称")
            return {'CANCELLED'}

        # 获取选中骨骼列表
        selected_bones = [bone for bone in obj.pose.bones if bone.select]

        # 检查是否有选中的骨骼
        if not selected_bones:
            self.report({'ERROR'}, "请选择骨骼")
            return {'CANCELLED'}

        modified_count = 0  # 记录修改的约束数量
        active_bone = context.active_pose_bone
        enable = active_bone.mmr_bone.Constraint_bool if active_bone else False

        for bone in selected_bones:
            # 检查是否存在目标约束
            constraint = bone.constraints.get(constraint_name)
            if not constraint:
                continue

            if enable:
                # 启用约束：获取影响值
                if active_bone and active_bone.mmr_bone.Use_manual_influence:
                    # 手动模式：使用活动骨骼的设置值，统一应用到所有骨骼
                    target_influence = active_bone.mmr_bone.Constraint_influence
                else:
                    # 每骨骼模式：恢复各自之前保存的影响值
                    target_influence = bone.mmr_bone.Constraint_influence

                if target_influence != 0.0 and constraint.influence != target_influence:
                    constraint.influence = target_influence
                    modified_count += 1
            else:
                # 禁用约束：存储当前影响值并设为0
                if constraint.influence != 0.0:
                    # 如果需要保持变换，先记录骨骼当前视觉矩阵
                    if active_bone and active_bone.mmr_bone.Disable_keep_transform:
                        saved_matrix = bone.matrix.copy()
                    bone.mmr_bone.Constraint_influence = constraint.influence
                    constraint.influence = 0.0
                    # 烘焙约束效果到骨骼姿态
                    if active_bone and active_bone.mmr_bone.Disable_keep_transform:
                        bone.matrix = saved_matrix
                    modified_count += 1

        # 是否插入关键帧
        if active_bone and active_bone.mmr_bone.Insert_constraint_keyframe:
            keyframe_count = 0
            for bone in selected_bones:
                constraint = bone.constraints.get(constraint_name)
                if constraint:
                    constraint.keyframe_insert(data_path="influence")
                    keyframe_count += 1

            if keyframe_count > 0:
                print(f"已插入 {keyframe_count} 个关键帧")
        else:
            if modified_count > 0:
                print(f"成功修改 {modified_count} 个约束")
            else:
                print(f"没有需要修改的约束")

        return {'FINISHED'}
