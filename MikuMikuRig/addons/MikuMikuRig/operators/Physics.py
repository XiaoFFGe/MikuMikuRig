import bpy

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

        # 获取活动骨骼
        active_bone = obj.data.bones.active

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
        for index, bone_name in enumerate(bone_chain):
            print(f"骨骼名称: {bone_name}, 索引: {index}")

            if index == list_len - 1:  # 检查是否是最后一个元素
                continue  # 跳过最后一个骨骼

            # 获取骨骼
            current_bone = obj.pose.bones.get(bone_name)
            # 获取子骨骼
            children_bones = obj.pose.bones.get(bone_chain[index + 1])

            # 先删除旧的约束
            if current_bone:
                for constraint in current_bone.constraints:
                    if constraint.name == "MMR-阻尼追踪":
                        current_bone.constraints.remove(constraint)
                        break
                    # 没有找到旧的约束，删除阻尼追踪类型的约束
                    if constraint.type == 'DAMPED_TRACK':
                        current_bone.constraints.remove(constraint)
                        break

            if current_bone:
                # 加阻尼追踪约束
                constraint = current_bone.constraints.new(type='DAMPED_TRACK')
                constraint.name = "MMR-阻尼追踪"
                constraint.target = obj
                constraint.subtarget = children_bones.name  # 子骨骼
                constraint.influence = mmr.Softness

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

        # 获取活动骨骼
        active_bone = obj.data.bones.active

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
        for bone_name in bone_chain:
            bone = obj.pose.bones.get(bone_name)
            if bone:
                for constraint in bone.constraints:
                    bone.constraints.remove(constraint)
                    break

        return {'FINISHED'}

# 装配刚体
class Assign_Rigidbody(bpy.types.Operator):
    '''Assign_Rigidbody'''
    bl_idname = "mmr.assign_rigidbody"
    bl_label = "Assign Rigidbody"
    bl_options = {'REGISTER', 'UNDO'}  # 启用撤销功能

    # 验证物体是不是骨骼
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def execute(self, context):

        # 获取当前活动对象和骨骼
        obj = bpy.context.active_object

        # 获取活动骨骼
        active_bone = obj.data.bones.active

        current_mode = bpy.context.object.mode

        obj_parent = obj.parent

        mmr_bone = context.active_pose_bone.mmr_bone

        # 判断集合是否存在
        if "temp_object" not in bpy.data.collections:
            # 创建集合
            temp_object = bpy.data.collections.new("temp_object")
            # 链接到场景
            bpy.context.scene.collection.children.link(temp_object)
        else:
            temp_object = bpy.data.collections["temp_object"]

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

        def get_rigidbody(bone):
            active_bone = obj.data.bones.get(bone)

            for child in obj_parent.children:
                if "rigidbodies" in child.name:

                    rigidbodies = child # 获取刚体列表

                    for rigidbody in child.children:
                        rigidbody_bone = rigidbody.mmd_rigid.bone
                        if rigidbody_bone == active_bone.name:

                            rigidbody.rigid_body.linear_damping = mmr_bone.damping
                            rigidbody.rigid_body.angular_damping = mmr_bone.damping

                            # 获取骨骼的局部矩阵
                            bone_matrix = active_bone.matrix_local
                            # 计算全局矩阵：骨架的世界矩阵 × 骨骼的局部矩阵
                            global_matrix = obj.matrix_world @ bone_matrix

                            bpy.ops.object.mode_set(mode='OBJECT')

                            # 创建空物体
                            empty = bpy.data.objects.new("empty_" + rigidbody.name, None)
                            # 设置空物体的世界矩阵
                            empty.matrix_world = global_matrix
                            # 链接到集合
                            temp_object.objects.link(empty)
                            # 显示形状
                            empty.empty_display_type = 'ARROWS'

                            empty.scale = (0.05, 0.05, 0.05)

                            # 激活空物体
                            bpy.context.view_layer.objects.active = empty
                            empty.select_set(True)

                            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

                            rigidbody_matrix = rigidbody.matrix_world.copy()  # 复制刚体矩阵

                            # 父级
                            rigidbody.parent = empty

                            rigidbody.matrix_world = rigidbody_matrix  # 复原

                            joint_obj1 = None
                            joints = None

                            for child in obj_parent.children:
                                if "joints" in child.name:
                                    for joint in child.children:
                                        joint_obj = joint.mmd_joint.name_j
                                        if rigidbody.mmd_rigid.name_j == joint_obj:
                                            # 复制矩阵
                                            joint_matrix = joint.matrix_world.copy()

                                            # 父级
                                            joint.parent = empty

                                            # 矩阵
                                            joint.matrix_world = joint_matrix

                                            joint.rigid_body_constraint.disable_collisions = True

                                            joint_obj1 = joint
                                            joints = child

                                            break

                            # 获取姿势骨骼
                            pose_bone = obj.pose.bones[bone]

                            # 计算骨骼的世界变换矩阵
                            bone_matrix = obj.matrix_world @ pose_bone.matrix

                            # 设置刚体的世界变换矩阵
                            empty.matrix_world = bone_matrix

                            # 更新场景
                            bpy.context.view_layer.update()

                            joint_obj1_matrix = joint_obj1.matrix_world.copy()

                            # 父级
                            joint_obj1.parent = joints

                            # 矩阵
                            joint_obj1.matrix_world = joint_obj1_matrix

                            rigidbody_matrix = rigidbody.matrix_world.copy()

                            # 父级
                            rigidbody.parent = rigidbodies

                            # 矩阵
                            rigidbody.matrix_world = rigidbody_matrix

                            empty_matrix = empty.matrix_world.copy()

                            # 父级
                            empty.parent = rigidbody

                            # 矩阵
                            empty.matrix_world = empty_matrix

                            # 为骨骼加复制变换约束
                            constraint = pose_bone.constraints.new(type='COPY_TRANSFORMS')
                            constraint.name = "mmr_physics"
                            constraint.target = empty

        bone_chain = get_bone_chain()

        for bone in bone_chain:
            get_rigidbody(bone)

        return {'FINISHED'}

# 装配骨骼刚体
class Assign_armature_rigidbody(bpy.types.Operator):
    bl_idname = "mmr.assign_armature_rigidbody"
    bl_label = "Assign armature Rigidbody"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择一个骨架对象")
            return {'CANCELLED'}

        obj_parent = obj.parent

        obj_bone = obj.data.bones

        # 判断集合是否存在
        if "temp_object" not in bpy.data.collections:
            # 创建集合
            temp_object = bpy.data.collections.new("temp_object")
            # 链接到场景
            bpy.context.scene.collection.children.link(temp_object)
        else:
            temp_object = bpy.data.collections["temp_object"]

        for bone in obj_bone:
            for child in obj_parent.children:
                if "rigidbodies" in child.name:
                    rigidbodies = child  # 获取刚体列表
                    for rigidbody in child.children:
                        rigidbody_bone = rigidbody.mmd_rigid.bone
                        if rigidbody_bone == bone.name:

                            if rigidbody.mmd_rigid.type == '0':
                                # 获取骨骼的局部矩阵
                                bone_matrix = bone.matrix_local
                                # 计算全局矩阵：骨架的世界矩阵 × 骨骼的局部矩阵
                                global_matrix = obj.matrix_world @ bone_matrix

                                # 创建空物体
                                empty = bpy.data.objects.new("empty_" + rigidbody.name, None)
                                # 设置空物体的世界矩阵
                                empty.matrix_world = global_matrix
                                # 链接到集合
                                temp_object.objects.link(empty)
                                # 显示形状
                                empty.empty_display_type = 'ARROWS'

                                empty.scale = (0.05, 0.05, 0.05)

                                # 激活空物体
                                bpy.context.view_layer.objects.active = empty
                                empty.select_set(True)

                                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

                                rigidbody_matrix = rigidbody.matrix_world.copy()  # 复制刚体矩阵
                                # 父级
                                rigidbody.parent = empty
                                rigidbody.matrix_world = rigidbody_matrix  # 复原

                                # 获取姿势骨骼
                                pose_bone = obj.pose.bones[bone.name]
                                # 计算骨骼的世界变换矩阵
                                bone_matrix = obj.matrix_world @ pose_bone.matrix
                                # 设置刚体的世界变换矩阵
                                empty.matrix_world = bone_matrix

                                # 更新场景
                                bpy.context.view_layer.update()

                                rigidbody_matrix = rigidbody.matrix_world.copy()  # 复制刚体矩阵
                                # 父级
                                rigidbody.parent = obj
                                rigidbody.parent_type = 'BONE'
                                rigidbody.parent_bone = bone.name
                                rigidbody.matrix_world = rigidbody_matrix  # 复原

                                # 删除空物体
                                bpy.data.objects.remove(empty)

        return {'FINISHED'}

# 打开MMD物理
class Open_MMD_Physics(bpy.types.Operator):
    bl_idname = "mmr.open_mmd_physics"
    bl_label = "Open MMD Physics"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        obj = bpy.data.objects.get(obj.name)

        mmr = obj.mmr

        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择一个骨架对象")
            return {'CANCELLED'}

        # 开启物理
        if mmr.physics_bool:
            bpy.ops.mmd_tools.clean_rig()
            mmr.physics_bool = False
        else:
            bpy.ops.mmd_tools.build_rig()
            mmr.physics_bool = True

        return {'FINISHED'}

# 显示刚体
class Show_Rigidbody(bpy.types.Operator):
    bl_idname = "mmr.show_rigidbody"
    bl_label = "Show Rigidbody"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, "请选择一个骨架对象")
            return {'CANCELLED'}

        obj_parent = obj.parent

        if obj.mmd_root.show_rigid_bodies:
            # 隐藏
            for child in obj_parent.children:
                if "rigidbodies" in child.name:
                    for rigidbody in child.children:
                        rigidbody.hide_set(True)
            obj.mmd_root.show_rigid_bodies = False
        else:
            # 显示
            for child in obj_parent.children:
                if "rigidbodies" in child.name:
                    for rigidbody in child.children:
                        rigidbody.hide_set(False)
            obj.mmd_root.show_rigid_bodies = True

        return {'FINISHED'}

# 选择碰撞组
class Select_Collision_Group(bpy.types.Operator):
    bl_idname = "mmr.select_collision_group"
    bl_label = "Select Collision Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        # 至少选择一个物体
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "请选择一个物体")
            return {'CANCELLED'}

        bpy.ops.mmd_tools.rigid_body_select(properties={'collision_group_number'})

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

        scene.rigidbody_world.substeps_per_frame = 3
        scene.rigidbody_world.solver_iterations = 8

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
