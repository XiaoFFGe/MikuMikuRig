import contextlib
import logging
import time
from typing import List, Optional, Iterator, Generator

import bpy
from mathutils import Vector, Euler

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 物理属性常量
# 碰撞形状类型
SHAPE_SPHERE = 0      # 球体形状
SHAPE_BOX = 1         # 立方体形状
SHAPE_CAPSULE = 2     # 胶囊体形状

# 刚体动力学模式
MODE_STATIC = 0              # 静态模式（固定不动）
MODE_DYNAMIC = 1             # 动态模式（完全受物理影响）
MODE_DYNAMIC_BONE = 2        # 动态骨骼模式（部分受物理影响）

# 形状类型转换函数
def shapeType(collision_shape):
    """将字符串类型的碰撞形状转换为整数索引
    
    Args:
        collision_shape: 字符串形式的碰撞形状名称（SPHERE, BOX, CAPSULE）
        
    Returns:
        对应形状的整数索引
    """
    return ("SPHERE", "BOX", "CAPSULE").index(collision_shape)


def collisionShape(shape_type):
    """将整数索引转换为字符串类型的碰撞形状
    
    Args:
        shape_type: 形状类型的整数索引
        
    Returns:
        对应形状的字符串名称
    """
    return ("SPHERE", "BOX", "CAPSULE")[shape_type]

# 属性名映射（处理Blender API变化）
# 用于在不同Blender版本间保持兼容性的属性名映射类
class Props:
    show_in_front = "show_in_front"             # 显示在前面
    display_type = "display_type"               # 显示类型
    display_size = "display_size"               # 显示大小
    empty_display_type = "empty_display_type"   # 空对象显示类型
    empty_display_size = "empty_display_size"   # 空对象显示大小

# 上下文工具类
# 提供Blender上下文管理和对象操作的工具方法
class FnContext:
    @staticmethod
    def ensure_context(target_scene=None) -> bpy.types.Context:
        """确保获取有效的Blender上下文
        
        Args:
            target_scene: 目标场景，如果为None则使用当前上下文
            
        Returns:
            有效的Blender上下文对象
            
        Raises:
            ValueError: 无法找到3D视图区域创建上下文时抛出
        """
        if target_scene is None:
            context = bpy.context
        else:
            # 创建一个临时上下文，用于在特定场景中执行操作
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if area.type == 'VIEW_3D':  # 找到3D视图区域
                        # 创建上下文字典
                        context = {'window': window, 'screen': screen, 'area': area}
                        context['scene'] = target_scene
                        context['view_layer'] = target_scene.view_layers[0]
                        return context
            raise ValueError("Could not find a 3D view area to create context")
        return context

    @staticmethod
    def new_and_link_object(context: bpy.types.Context, name: str, object_data) -> bpy.types.Object:
        """创建新对象并将其链接到当前上下文的集合中
        
        Args:
            context: Blender上下文
            name: 新对象的名称
            object_data: 对象的数据（如网格、曲线等），None表示空对象
            
        Returns:
            创建并链接的新对象
        """
        obj = bpy.data.objects.new(name=name, object_data=object_data)
        context.collection.objects.link(obj)
        return obj

    @staticmethod
    def link_object(context: bpy.types.Context, obj: bpy.types.Object):
        """将对象链接到当前上下文的集合中
        
        Args:
            context: Blender上下文
            obj: 要链接的对象
        """
        context.collection.objects.link(obj)

    @staticmethod
    def select_object(context: bpy.types.Context, obj: bpy.types.Object):
        """选择指定的对象
        
        Args:
            context: Blender上下文
            obj: 要选择的对象
        """
        obj.select_set(True)

    @staticmethod
    def set_active_object(context: bpy.types.Context, obj: bpy.types.Object):
        """将指定对象设置为当前活动对象
        
        Args:
            context: Blender上下文
            obj: 要设置为活动的对象
        """
        context.view_layer.objects.active = obj

    @staticmethod
    def duplicate_object(context: bpy.types.Context, obj: bpy.types.Object, count: int) -> List[bpy.types.Object]:
        objects = []
        for _ in range(count):
            new_obj = obj.copy()
            if obj.data:
                new_obj.data = obj.data.copy()
            context.collection.objects.link(new_obj)
            objects.append(new_obj)
        return objects

    @staticmethod
    def find_user_layer_collection_by_object(context: bpy.types.Context, target_object: bpy.types.Object) -> Optional[bpy.types.LayerCollection]:
        """
        查找包含指定目标对象的图层集合

        Args:
            context: Blender上下文
            target_object: 要查找图层集合的目标对象

        Returns:
            包含目标对象的图层集合，如果未找到则返回None
        """
        scene_layer_collection: bpy.types.LayerCollection = context.view_layer.layer_collection

        def find_layer_collection_by_name(layer_collection: bpy.types.LayerCollection, name: str) -> Optional[bpy.types.LayerCollection]:
            """递归查找指定名称的图层集合"""
            if layer_collection.name == name:
                return layer_collection

            child_layer_collection: bpy.types.LayerCollection
            for child_layer_collection in layer_collection.children:
                found = find_layer_collection_by_name(child_layer_collection, name)
                if found is not None:
                    return found

            return None

        user_collection: bpy.types.Collection
        for user_collection in target_object.users_collection:
            found = find_layer_collection_by_name(scene_layer_collection, user_collection.name)
            if found is not None:
                return found

        return None

    @staticmethod
    @contextlib.contextmanager
    def temp_override_active_layer_collection(context: bpy.types.Context, target_object: bpy.types.Object) -> Generator[bpy.types.Context, None, None]:
        """
        临时覆盖包含目标对象的活动图层集合的上下文管理器

        此上下文管理器允许临时将给定上下文中的active_layer_collection更改为包含目标对象的图层集合。
        它确保在退出上下文后恢复原始的active_layer_collection。

        Args:
            context: 将在其中覆盖active_layer_collection的上下文
            target_object: 其图层集合将被设置为active_layer_collection的目标对象

        Yields:
            已修改active_layer_collection的上下文

        Example:
            with FnContext.temp_override_active_layer_collection(context, target_object):
                # 使用修改后的上下文执行操作
                bpy.ops.object.select_all(action='DESELECT')
                target_object.select_set(True)
                bpy.ops.object.delete()

        """
        original_layer_collection = context.view_layer.active_layer_collection
        target_layer_collection = FnContext.find_user_layer_collection_by_object(context, target_object)
        if target_layer_collection is not None:
            context.view_layer.active_layer_collection = target_layer_collection
        try:
            yield context
        finally:
            if context.view_layer.active_layer_collection.name != original_layer_collection.name:
                context.view_layer.active_layer_collection = original_layer_collection

# 模型查找工具类
# 提供MMD模型对象的查找和遍历工具方法
class FnModel:
    @staticmethod
    def find_root_object(obj: bpy.types.Object) -> Optional[bpy.types.Object]:
        """查找对象所在的MMD根对象
        
        Args:
            obj: 要查找根对象的Blender对象
            
        Returns:
            MMD根对象，如果未找到则返回None
        """
        if obj.mmd_type == "ROOT":
            return obj
        for parent in obj.parent_recursive:
            if parent.mmd_type == "ROOT":
                return parent
        return None

    @staticmethod
    def find_armature_object(root_obj: bpy.types.Object) -> Optional[bpy.types.Object]:
        """查找MMD模型的骨架对象
        
        Args:
            root_obj: MMD根对象
            
        Returns:
            骨架对象，如果未找到则返回None
        """
        for obj in root_obj.children:
            if obj.type == "ARMATURE":
                return obj
        return None

    @staticmethod
    def find_rigid_group_object(root_obj: bpy.types.Object) -> Optional[bpy.types.Object]:
        """查找刚体组对象
        
        Args:
            root_obj: MMD根对象
            
        Returns:
            刚体组对象，如果未找到则返回None
        """
        for obj in root_obj.children:
            if obj.mmd_type == "RIGID_GRP_OBJ":
                return obj
        return None

    @staticmethod
    def find_joint_group_object(root_obj: bpy.types.Object) -> Optional[bpy.types.Object]:
        """查找关节组对象
        
        Args:
            root_obj: MMD根对象
            
        Returns:
            关节组对象，如果未找到则返回None
        """
        for obj in root_obj.children:
            if obj.mmd_type == "JOINT_GRP_OBJ":
                return obj
        return None

    @staticmethod
    def find_temporary_group_object(root_obj: bpy.types.Object) -> Optional[bpy.types.Object]:
        """查找临时对象组
        
        Args:
            root_obj: MMD根对象
            
        Returns:
            临时对象组，如果未找到则返回None
        """
        for obj in root_obj.children:
            if obj.mmd_type == "TEMPORARY_GRP_OBJ":
                return obj
        return None

    @staticmethod
    def iterate_child_objects(obj: bpy.types.Object) -> Iterator[bpy.types.Object]:
        """递归遍历对象的所有子对象
        
        Args:
            obj: 要遍历的父对象
            
        Yields:
            对象的所有子对象（递归）
        """
        for child in obj.children:
            yield child
            yield from FnModel.iterate_child_objects(child)

    @staticmethod
    def iterate_mesh_objects(root_obj: bpy.types.Object) -> Iterator[bpy.types.Object]:
        """遍历模型中的所有网格对象
        
        Args:
            root_obj: MMD根对象
            
        Yields:
            所有类型为MESH的对象
        """
        for obj in FnModel.iterate_child_objects(root_obj):
            if obj.type == "MESH":
                yield obj

    @staticmethod
    def iterate_rigid_body_objects(root_obj: bpy.types.Object) -> Iterator[bpy.types.Object]:
        """遍历模型中的所有刚体对象
        
        Args:
            root_obj: MMD根对象
            
        Yields:
            所有类型为RIGID_BODY的对象
        """
        for obj in FnModel.iterate_child_objects(root_obj):
            if obj.mmd_type == "RIGID_BODY":
                yield obj

    @staticmethod
    def iterate_joint_objects(root_obj: bpy.types.Object) -> Iterator[bpy.types.Object]:
        """遍历模型中的所有关节对象
        
        Args:
            root_obj: MMD根对象
            
        Yields:
            所有类型为JOINT的对象
        """
        for obj in FnModel.iterate_child_objects(root_obj):
            if obj.mmd_type == "JOINT":
                yield obj

    @staticmethod
    def iterate_temporary_objects(root_obj: bpy.types.Object, rigid_track_only=False) -> Iterator[bpy.types.Object]:
        """遍历模型中的所有临时对象
        
        Args:
            root_obj: MMD根对象
            rigid_track_only: 是否只返回TRACK_TARGET类型的临时对象
            
        Yields:
            所有临时对象（TRACK_TARGET和可选的NON_COLLISION_CONSTRAINT）
        """
        for obj in FnModel.iterate_child_objects(root_obj):
            if obj.mmd_type == "TRACK_TARGET":
                yield obj
            elif not rigid_track_only and obj.mmd_type == "NON_COLLISION_CONSTRAINT":
                yield obj

# 刚体工具类
# 提供刚体世界管理的工具方法
class rigid_body:
    @staticmethod
    def setRigidBodyWorldEnabled(enable: bool) -> bool:
        """启用或禁用刚体世界
        
        Args:
            enable: 是否启用刚体世界
            
        Returns:
            操作前的刚体世界启用状态
        """
        if bpy.ops.rigidbody.world_add.poll():
            bpy.ops.rigidbody.world_add()  # 如果不存在刚体世界则创建
        rigidbody_world = bpy.context.scene.rigidbody_world
        enabled = rigidbody_world.enabled  # 保存当前状态
        rigidbody_world.enabled = enable   # 设置新状态
        return enabled

# 刚体材质类
# 为刚体对象提供颜色材质管理
class RigidBodyMaterial:
    COLORS = [
        0x7FDDD4, 0xF0E68C, 0xEE82EE, 0xFFE4E1,
        0x8FEEEE, 0xADFF2F, 0xFA8072, 0x9370DB,
        0x40E0D0, 0x96514D, 0x5A964E, 0xE6BFAB,
        0xD3381C, 0x165E83, 0x701682, 0x828216,
    ]

    @classmethod
    def getMaterial(cls, number: int):
        """获取或创建指定编号的刚体材质
        
        Args:
            number: 材质编号（0-15）
            
        Returns:
            创建或获取的材质对象
        """
        number = int(number)
        material_name = f"mmd_tools_rigid_{number}"
        if material_name not in bpy.data.materials:
            # 创建新材质
            mat = bpy.data.materials.new(material_name)
            color = cls.COLORS[number]  # 获取颜色
            # 解析RGB颜色值
            mat.diffuse_color[:3] = [
                ((0xFF0000 & color) >> 16) / 255.0,  # 红色分量
                ((0x00FF00 & color) >> 8) / 255.0,   # 绿色分量
                (0x0000FF & color) / 255.0           # 蓝色分量
            ]
            mat.specular_intensity = 0  # 无高光
            if len(mat.diffuse_color) > 3:
                mat.diffuse_color[3] = 0.5  # 设置透明度
            mat.blend_method = "BLEND"  # 启用混合模式
            if hasattr(mat, "shadow_method"):
                mat.shadow_method = "NONE"  # 不产生阴影
            mat.use_backface_culling = True  # 启用背面剔除
            mat.show_transparent_back = False  # 不显示透明背面
            
            # 设置节点材质
            mat.use_nodes = True
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            nodes.clear()  # 清除默认节点
            
            # 添加背景节点和输出节点
            node_color = nodes.new("ShaderNodeBackground")
            node_color.inputs["Color"].default_value = mat.diffuse_color
            node_output = nodes.new("ShaderNodeOutputMaterial")
            links.new(node_color.outputs[0], node_output.inputs["Surface"])
        else:
            # 使用已存在的材质
            mat = bpy.data.materials[material_name]
        return mat

# 刚体操作类
# 提供刚体和关节对象的创建和设置工具方法
class FnRigidBody:
    @staticmethod
    def new_rigid_body_object(context: bpy.types.Context, parent_object: bpy.types.Object) -> bpy.types.Object:
        """创建新的刚体对象
        
        Args:
            context: Blender上下文
            parent_object: 刚体对象的父对象
            
        Returns:
            创建的刚体对象
        """
        # 创建新的网格对象作为刚体的载体
        mesh = bpy.data.meshes.new(name="Rigidbody")  # 创建空网格数据
        obj = FnContext.new_and_link_object(context, name="Rigidbody", object_data=mesh)  # 创建对象并链接到场景
        
        # 设置对象基本属性
        obj.parent = parent_object  # 设置父对象，通常是刚体组对象
        obj.mmd_type = "RIGID_BODY"  # 设置MMD类型标识为刚体
        obj.rotation_mode = "YXZ"     # 设置旋转模式为YXZ（与MMD兼容）
        setattr(obj, Props.display_type, "SOLID")  # 设置显示类型为实体
        obj.show_transparent = True  # 启用透明显示，便于在3D视图中观察
        obj.hide_render = True       # 渲染时隐藏，避免影响最终渲染结果
        obj.display.show_shadows = False  # 不显示阴影，提高视图性能

        # 添加Blender刚体属性
        # 保存当前选择和活动对象状态，以便后续恢复
        original_active_obj = context.view_layer.objects.active
        original_selected_objs = context.selected_objects
        
        # 清除当前选择并设置新刚体对象为活动对象
        bpy.ops.object.select_all(action='DESELECT')  # 取消所有选择
        FnContext.set_active_object(context, obj)  # 设置新对象为活动对象
        obj.select_set(True)  # 选中新对象
        
        # 确保对象没有已存在的刚体属性，然后添加新的活动刚体属性
        obj.rigid_body = None  # 清除可能存在的刚体属性
        bpy.ops.rigidbody.object_add(type="ACTIVE")  # 添加活动类型的刚体属性
        
        # 恢复之前的选择和活动对象状态
        bpy.ops.object.select_all(action='DESELECT')  # 取消所有选择
        # 恢复原始活动对象
        if original_active_obj:
            original_active_obj.select_set(True)
            FnContext.set_active_object(context, original_active_obj)
        # 恢复原始选中对象
        for original_obj in original_selected_objs:
            original_obj.select_set(True)

        return obj

    @staticmethod
    def setup_rigid_body_object(
        obj: bpy.types.Object,
        shape_type: str,
        location: Vector,
        rotation: Euler,
        size: Vector,
        dynamics_type: str,
        collision_group_number: Optional[int] = None,
        collision_group_mask: Optional[List[bool]] = None,
        name: Optional[str] = None,
        name_e: Optional[str] = None,
        bone: Optional[str] = None,
        friction: Optional[float] = None,
        mass: Optional[float] = None,
        angular_damping: Optional[float] = None,
        linear_damping: Optional[float] = None,
        bounce: Optional[float] = None,
    ) -> bpy.types.Object:
        """设置刚体对象的属性
        
        Args:
            obj: 要设置的刚体对象
            shape_type: 碰撞形状类型（SPHERE, BOX, CAPSULE）
            location: 刚体位置
            rotation: 刚体旋转
            size: 刚体大小
            dynamics_type: 动力学类型（0=静态, 1=动态, 2=动态骨骼）
            collision_group_number: 碰撞组编号
            collision_group_mask: 碰撞组掩码
            name: 刚体名称（日文）
            name_e: 刚体名称（英文）
            bone: 关联的骨骼名称
            friction: 摩擦系数
            mass: 质量
            angular_damping: 角阻尼
            linear_damping: 线性阻尼
            bounce: 弹性系数
            
        Returns:
            设置完成的刚体对象
        """
        # 设置位置和旋转
        obj.location = location
        obj.rotation_euler = rotation

        # 设置MMD刚体属性
        obj.mmd_rigid.shape = shape_type  # 碰撞形状
        obj.mmd_rigid.size = size         # 形状大小
        # 确保动力学类型在有效范围内
        obj.mmd_rigid.type = str(dynamics_type) if dynamics_type in range(3) else "1"

        # 设置碰撞组
        if collision_group_number is not None:
            obj.mmd_rigid.collision_group_number = collision_group_number

        if collision_group_mask is not None:
            obj.mmd_rigid.collision_group_mask = collision_group_mask

        # 设置名称
        if name is not None:
            obj.name = name
            obj.mmd_rigid.name_j = name  # 日文名称
            obj.data.name = name

        if name_e is not None:
            obj.mmd_rigid.name_e = name_e  # 英文名称

        # 设置关联骨骼
        if bone is not None:
            obj.mmd_rigid.bone = bone
        else:
            obj.mmd_rigid.bone = ""

        # 设置物理属性
        rb = obj.rigid_body
        if friction is not None:
            rb.friction = friction        # 摩擦系数
        if mass is not None:
            rb.mass = mass                # 质量
        if angular_damping is not None:
            rb.angular_damping = angular_damping  # 角阻尼
        if linear_damping is not None:
            rb.linear_damping = linear_damping    # 线性阻尼
        if bounce is not None:
            rb.restitution = bounce       # 弹性系数（恢复系数）

        return obj

    @staticmethod
    def new_joint_object(context: bpy.types.Context, parent_object: bpy.types.Object, empty_display_size: float) -> bpy.types.Object:
        """创建新的关节对象
        
        Args:
            context: Blender上下文
            parent_object: 关节对象的父对象
            empty_display_size: 空对象的显示大小
            
        Returns:
            创建的关节对象
        """
        obj = FnContext.new_and_link_object(context, name="Joint", object_data=None)
        obj.parent = parent_object
        obj.mmd_type = "JOINT"
        obj.rotation_mode = "YXZ"
        setattr(obj, Props.empty_display_type, "ARROWS")
        setattr(obj, Props.empty_display_size, 0.1 * empty_display_size)
        obj.hide_render = True

        # 保存当前选择和活动对象
        original_active_obj = context.view_layer.objects.active
        original_selected_objs = context.selected_objects
        
        # 设置新对象为活动对象并选择
        bpy.ops.object.select_all(action='DESELECT')
        FnContext.set_active_object(context, obj)
        obj.select_set(True)
        
        # 添加刚体约束
        bpy.ops.rigidbody.constraint_add(type="GENERIC_SPRING")

        # 配置约束属性
        rigid_body_constraint = obj.rigid_body_constraint
        if rigid_body_constraint is not None:
            rigid_body_constraint.disable_collisions = False
            rigid_body_constraint.use_limit_ang_x = True
            rigid_body_constraint.use_limit_ang_y = True
            rigid_body_constraint.use_limit_ang_z = True
            rigid_body_constraint.use_limit_lin_x = True
            rigid_body_constraint.use_limit_lin_y = True
            rigid_body_constraint.use_limit_lin_z = True
            rigid_body_constraint.use_spring_x = True
            rigid_body_constraint.use_spring_y = True
            rigid_body_constraint.use_spring_z = True
            rigid_body_constraint.use_spring_ang_x = True
            rigid_body_constraint.use_spring_ang_y = True
            rigid_body_constraint.use_spring_ang_z = True
        
        # 恢复之前的选择和活动对象
        bpy.ops.object.select_all(action='DESELECT')
        if original_active_obj:
            original_active_obj.select_set(True)
            FnContext.set_active_object(context, original_active_obj)
        for original_obj in original_selected_objs:
            original_obj.select_set(True)

        return obj

    @staticmethod
    def setup_joint_object(
        obj: bpy.types.Object,
        location: Vector,
        rotation: Euler,
        rigid_a: bpy.types.Object,
        rigid_b: bpy.types.Object,
        maximum_location: Vector,
        minimum_location: Vector,
        maximum_rotation: Euler,
        minimum_rotation: Euler,
        spring_angular: Vector,
        spring_linear: Vector,
        name: str,
        name_e: Optional[str] = None,
    ) -> bpy.types.Object:
        """设置关节对象的属性和约束
        
        Args:
            obj: 要设置的关节对象
            location: 关节位置
            rotation: 关节旋转
            rigid_a: 关节连接的第一个刚体
            rigid_b: 关节连接的第二个刚体
            maximum_location: 最大位置限制
            minimum_location: 最小位置限制
            maximum_rotation: 最大旋转限制
            minimum_rotation: 最小旋转限制
            spring_angular: 角弹簧参数
            spring_linear: 线性弹簧参数
            name: 关节名称（日文）
            name_e: 关节名称（英文）
            
        Returns:
            设置完成的关节对象
        """
        obj.name = f"J.{name}"
        obj.location = location
        obj.rotation_euler = rotation

        rigid_body_constraint = obj.rigid_body_constraint
        if rigid_body_constraint is not None:
            rigid_body_constraint.object1 = rigid_a
            rigid_body_constraint.object2 = rigid_b
            # 设置位置限制
            rigid_body_constraint.limit_lin_x_upper = maximum_location.x
            rigid_body_constraint.limit_lin_y_upper = maximum_location.y
            rigid_body_constraint.limit_lin_z_upper = maximum_location.z
            rigid_body_constraint.limit_lin_x_lower = minimum_location.x
            rigid_body_constraint.limit_lin_y_lower = minimum_location.y
            rigid_body_constraint.limit_lin_z_lower = minimum_location.z
            # 设置旋转限制
            rigid_body_constraint.limit_ang_x_upper = maximum_rotation.x
            rigid_body_constraint.limit_ang_y_upper = maximum_rotation.y
            rigid_body_constraint.limit_ang_z_upper = maximum_rotation.z
            rigid_body_constraint.limit_ang_x_lower = minimum_rotation.x
            rigid_body_constraint.limit_ang_y_lower = minimum_rotation.y
            rigid_body_constraint.limit_ang_z_lower = minimum_rotation.z
            # 设置弹簧参数
            rigid_body_constraint.spring_stiffness_x = spring_linear.x
            rigid_body_constraint.spring_stiffness_y = spring_linear.y
            rigid_body_constraint.spring_stiffness_z = spring_linear.z
            rigid_body_constraint.spring_stiffness_ang_x = spring_angular.x
            rigid_body_constraint.spring_stiffness_ang_y = spring_angular.y
            rigid_body_constraint.spring_stiffness_ang_z = spring_angular.z

        obj.mmd_joint.name_j = name
        if name_e is not None:
            obj.mmd_joint.name_e = name_e
        obj.mmd_joint.spring_linear = spring_linear
        obj.mmd_joint.spring_angular = spring_angular

        return obj

# 模型类
# MMD模型的主要操作类，负责协调物理构建、刚体和关节管理
class Model:
    def __init__(self, root_obj: bpy.types.Object):
        """初始化Model对象
        
        Args:
            root_obj: MMD根对象
            
        Raises:
            ValueError: 如果root_obj为None或不是MMD ROOT类型对象
        """
        if root_obj is None:
            raise ValueError("must be MMD ROOT type object")
        if root_obj.mmd_type != "ROOT":
            raise ValueError("must be MMD ROOT type object")
        self.__root: bpy.types.Object = getattr(root_obj, "original", root_obj)
        self.__arm: Optional[bpy.types.Object] = None
        self.__rigid_grp: Optional[bpy.types.Object] = None
        self.__joint_grp: Optional[bpy.types.Object] = None
        self.__temporary_grp: Optional[bpy.types.Object] = None
        
        # 内部状态
        self.__fake_parent_map = {}  # 虚拟父对象映射
        self.__rigid_body_matrix_map = {}  # 刚体矩阵映射
        self.__empty_parent_map = {}  # 空对象父对象映射

    def rootObject(self) -> bpy.types.Object:
        """获取MMD根对象
        
        Returns:
            MMD根对象
        """
        return self.__root

    def armature(self) -> bpy.types.Object:
        """获取模型的骨架对象
        
        Returns:
            骨架对象
            
        Raises:
            ValueError: 如果找不到骨架对象
        """
        if self.__arm is None:
            self.__arm = FnModel.find_armature_object(self.__root)
            if self.__arm is None:
                raise ValueError("Could not find armature object")
        return self.__arm

    def rigidGroupObject(self) -> bpy.types.Object:
        """获取或创建刚体组对象
        
        Returns:
            刚体组对象
        """
        if self.__rigid_grp is None:
            self.__rigid_grp = FnModel.find_rigid_group_object(self.__root)
            if self.__rigid_grp is None:
                context = FnContext.ensure_context()
                rigids = bpy.data.objects.new(name="rigidbodies", object_data=None)
                FnContext.link_object(context, rigids)
                rigids.mmd_type = "RIGID_GRP_OBJ"
                rigids.parent = self.__root
                rigids.hide_set(True)
                rigids.hide_select = True
                rigids.lock_rotation = rigids.lock_location = rigids.lock_scale = [True, True, True]
                self.__rigid_grp = rigids
        return self.__rigid_grp

    def jointGroupObject(self) -> bpy.types.Object:
        """获取或创建关节组对象
        
        Returns:
            关节组对象
        """
        if self.__joint_grp is None:
            self.__joint_grp = FnModel.find_joint_group_object(self.__root)
            if self.__joint_grp is None:
                context = FnContext.ensure_context()
                joints = bpy.data.objects.new(name="joints", object_data=None)
                FnContext.link_object(context, joints)
                joints.mmd_type = "JOINT_GRP_OBJ"
                joints.parent = self.__root
                joints.hide_set(True)
                joints.hide_select = True
                joints.lock_rotation = joints.lock_location = joints.lock_scale = [True, True, True]
                self.__joint_grp = joints
        return self.__joint_grp

    def temporaryGroupObject(self) -> bpy.types.Object:
        """获取或创建临时对象组
        
        Returns:
            临时对象组
        """
        if self.__temporary_grp is None:
            self.__temporary_grp = FnModel.find_temporary_group_object(self.__root)
            if self.__temporary_grp is None:
                context = FnContext.ensure_context()
                temporarys = bpy.data.objects.new(name="temporary", object_data=None)
                FnContext.link_object(context, temporarys)
                temporarys.mmd_type = "TEMPORARY_GRP_OBJ"
                temporarys.parent = self.__root
                temporarys.hide_set(True)
                temporarys.hide_select = True
                temporarys.lock_rotation = temporarys.lock_location = temporarys.lock_scale = [True, True, True]
                self.__temporary_grp = temporarys
        return self.__temporary_grp

    def rigidBodies(self) -> Iterator[bpy.types.Object]:
        """获取所有刚体对象的迭代器
        
        Returns:
            所有刚体对象的迭代器
        """
        return FnModel.iterate_rigid_body_objects(self.__root)

    def joints(self) -> Iterator[bpy.types.Object]:
        """获取所有关节对象的迭代器
        
        Returns:
            所有关节对象的迭代器
        """
        return FnModel.iterate_joint_objects(self.__root)

    def temporaryObjects(self, rigid_track_only=False) -> Iterator[bpy.types.Object]:
        """获取所有临时对象的迭代器
        
        Args:
            rigid_track_only: 是否只返回TRACK_TARGET类型的临时对象
            
        Returns:
            所有临时对象的迭代器
        """
        return FnModel.iterate_temporary_objects(self.__root, rigid_track_only)

    def __backupTransforms(self, obj: bpy.types.Object):
        """备份对象的变换属性（位置和旋转）
        
        Args:
            obj: 要备份变换属性的对象
        """
        for attr in ("location", "rotation_euler"):
            attr_name = f"__backup_{attr}__"
            if attr_name in obj:
                continue
            obj[attr_name] = getattr(obj, attr, None)

    def __restoreTransforms(self, obj: bpy.types.Object):
        """恢复对象的变换属性（位置和旋转）
        
        Args:
            obj: 要恢复变换属性的对象
        """
        for attr in ("location", "rotation_euler"):
            attr_name = f"__backup_{attr}__"
            val = obj.get(attr_name, None)
            if val is not None:
                setattr(obj, attr, val)
                del obj[attr_name]

    def __preBuild(self):
        """在构建物理系统之前进行准备工作
        
        这个方法主要完成以下工作：
        1. 重置内部状态映射
        2. 备份所有刚体对象的变换
        3. 禁用刚体的约束和相关骨骼的IK约束
        4. 更新骨骼约束变化
        5. 处理没有父对象的刚体，建立虚拟父对象关系
        """
        self.__fake_parent_map = {}
        self.__rigid_body_matrix_map = {}
        self.__empty_parent_map = {}

        no_parents = []  # 没有父对象的刚体列表
        for i in self.rigidBodies():
            self.__backupTransforms(i)  # 备份当前变换
            # 禁用约束
            if "mmd_tools_rigid_parent" in i.constraints:
                relation = i.constraints["mmd_tools_rigid_parent"]
                relation.mute = True  # 禁用约束
                # 禁用IK
                rigid_type = int(i.mmd_rigid.type)
                if rigid_type in {MODE_DYNAMIC, MODE_DYNAMIC_BONE}:
                    arm = relation.target
                    bone_name = relation.subtarget
                    if arm is not None and bone_name != "":
                        for c in arm.pose.bones[bone_name].constraints:
                            if c.type == "IK":  # 禁用IK约束
                                c.mute = True
                                c.influence = c.influence  # 触发更新
                    else:
                        no_parents.append(i)  # 记录没有父对象的刚体
        # 更新骨骼约束变化
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)

        parented = []  # 已处理的刚体列表
        for i in self.joints():
            self.__backupTransforms(i)  # 备份关节变换
            rbc = i.rigid_body_constraint
            if rbc is None:
                continue
            obj1, obj2 = rbc.object1, rbc.object2
            # 处理没有父对象的刚体，建立虚拟父对象关系
            if obj2 in no_parents:
                if obj1 not in no_parents and obj2 not in parented:
                    self.__fake_parent_map.setdefault(obj1, []).append(obj2)
                    parented.append(obj2)
            elif obj1 in no_parents:
                if obj1 not in parented:
                    self.__fake_parent_map.setdefault(obj2, []).append(obj1)
                    parented.append(obj1)

    def __postBuild(self):
        """在构建物理系统之后进行清理和收尾工作
        
        这个方法主要完成以下工作：
        1. 清理内部状态映射
        2. 更新场景变化
        3. 批量设置空对象的父对象以提高性能
        4. 启用骨骼上的刚体跟踪约束
        """
        self.__fake_parent_map = None  # 清理虚拟父对象映射
        self.__rigid_body_matrix_map = None  # 清理刚体矩阵映射

        # 更新场景变化
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)

        # 批量设置空对象的父对象以提高性能
        for empty, rigid_obj in self.__empty_parent_map.items():
            matrix_world = empty.matrix_world  # 保存当前世界矩阵
            empty.parent = rigid_obj  # 设置父对象
            empty.matrix_world = matrix_world  # 恢复世界矩阵
        self.__empty_parent_map = None  # 清理空对象父对象映射

        arm = self.armature()  # 获取骨架对象
        if arm:
            for p_bone in arm.pose.bones:
                c = p_bone.constraints.get("mmd_tools_rigid_track", None)
                if c:
                    c.mute = False  # 启用刚体跟踪约束

    def __getRigidRange(self, obj: bpy.types.Object) -> float:
        """计算刚体对象的最大尺寸范围
        
        Args:
            obj: 刚体对象
            
        Returns:
            刚体在X、Y、Z三个轴向上的最大尺寸
        """
        x0, y0, z0 = obj.bound_box[0]  # 获取边界框的最小点
        x1, y1, z1 = obj.bound_box[6]  # 获取边界框的最大点
        return max(x1 - x0, y1 - y0, z1 - z0)  # 返回三个轴向的最大尺寸

    def __createNonCollisionConstraint(self, nonCollisionJointTable: List[tuple]):
        """创建非碰撞约束
        
        Args:
            nonCollisionJointTable: 非碰撞约束对列表，每个元素是两个刚体对象的元组
        """
        total_len = len(nonCollisionJointTable)
        if total_len < 1:
            return  # 没有需要创建的约束，直接返回

        logging.debug("-" * 60)
        logging.debug(" creating ncc, counts: %d", total_len)
        start_time = time.time()

        context = FnContext.ensure_context()
        # 创建非碰撞约束对象
        ncc_obj = FnContext.new_and_link_object(context, name="ncc", object_data=None)
        ncc_obj.location = [0, 0, 0]
        setattr(ncc_obj, Props.empty_display_type, "ARROWS")
        setattr(ncc_obj, Props.empty_display_size, 0.5 * getattr(self.__root, Props.empty_display_size))
        ncc_obj.mmd_type = "NON_COLLISION_CONSTRAINT"
        ncc_obj.hide_render = True
        ncc_obj.parent = self.temporaryGroupObject()

        # 保存当前选择和活动对象
        original_active_obj = context.view_layer.objects.active
        original_selected_objs = context.selected_objects
        
        # 设置新对象为活动对象并选择
        bpy.ops.object.select_all(action='DESELECT')
        FnContext.set_active_object(context, ncc_obj)
        ncc_obj.select_set(True)
        
        # 添加刚体约束
        bpy.ops.rigidbody.constraint_add(type="GENERIC")
        rb = ncc_obj.rigid_body_constraint
        if rb is not None:
            rb.disable_collisions = True  # 设置为非碰撞约束
        
        # 恢复之前的选择和活动对象
        bpy.ops.object.select_all(action='DESELECT')
        if original_active_obj:
            original_active_obj.select_set(True)
            FnContext.set_active_object(context, original_active_obj)
        for original_obj in original_selected_objs:
            original_obj.select_set(True)

        # 复制约束对象
        ncc_objs = FnContext.duplicate_object(context, ncc_obj, total_len)
        logging.debug(" created %d ncc.", len(ncc_objs))

        # 为每个约束设置对应的刚体对象对
        for ncc_obj, pair in zip(ncc_objs, nonCollisionJointTable):
            rbc = ncc_obj.rigid_body_constraint
            if rbc is not None:
                rbc.object1, rbc.object2 = pair  # 设置约束连接的两个刚体
            ncc_obj.hide_set(True)  # 隐藏约束对象
            ncc_obj.hide_select = True  # 不可选择
        logging.debug(" finish in %f seconds.", time.time() - start_time)
        logging.debug("-" * 60)

    def updateRigid(self, rigid_obj: bpy.types.Object, collision_margin: float):
        """更新刚体对象的属性和约束
        
        Args:
            rigid_obj: 要更新的刚体对象
            collision_margin: 碰撞边距值
        """
        assert rigid_obj.mmd_type == "RIGID_BODY"
        rb = rigid_obj.rigid_body
        if rb is None:
            return

        rigid = rigid_obj.mmd_rigid
        rigid_type = int(rigid.type)  # 获取刚体类型
        relation = rigid_obj.constraints["mmd_tools_rigid_parent"]  # 获取父约束

        if relation.target is None:
            relation.target = self.armature()  # 设置目标为骨架

        arm = relation.target
        if relation.subtarget not in arm.pose.bones:
            bone_name = ""
        else:
            bone_name = relation.subtarget  # 获取关联的骨骼名称

        # 设置刚体是否为运动学
        if rigid_type == MODE_STATIC:
            rb.kinematic = True  # 静态刚体设置为运动学
        else:
            rb.kinematic = False  # 动态刚体设置为非运动学

        # 设置碰撞边距
        if collision_margin == 0.0:
            rb.use_margin = False  # 无边距
        else:
            rb.use_margin = True  # 有边距
            rb.collision_margin = collision_margin  # 设置边距值

        if arm is not None and bone_name != "":
            target_bone = arm.pose.bones[bone_name]  # 获取目标骨骼

            if rigid_type == MODE_STATIC:
                # 处理静态刚体
                m = target_bone.matrix @ target_bone.bone.matrix_local.inverted()
                self.__rigid_body_matrix_map[rigid_obj] = m
                orig_scale = rigid_obj.scale.copy()  # 保存原始缩放
                to_matrix_world = rigid_obj.matrix_world @ rigid_obj.matrix_local.inverted()
                matrix_world = to_matrix_world @ (m @ rigid_obj.matrix_local)
                rigid_obj.parent = arm  # 设置父对象为骨架
                rigid_obj.parent_type = "BONE"  # 设置父类型为骨骼
                rigid_obj.parent_bone = bone_name  # 设置父骨骼名称
                rigid_obj.matrix_world = matrix_world  # 设置世界矩阵
                rigid_obj.scale = orig_scale  # 恢复原始缩放
                
                # 处理虚拟子对象
                fake_children = self.__fake_parent_map.get(rigid_obj, None)
                if fake_children:
                    for fake_child in fake_children:
                        logging.debug("          - fake_child: %s", fake_child.name)
                        t, r, s = (m @ fake_child.matrix_local).decompose()
                        fake_child.location = t
                        fake_child.rotation_euler = r.to_euler(fake_child.rotation_mode)

            elif rigid_type in {MODE_DYNAMIC, MODE_DYNAMIC_BONE}:
                # 处理动态刚体
                m = target_bone.matrix @ target_bone.bone.matrix_local.inverted()
                self.__rigid_body_matrix_map[rigid_obj] = m
                t, r, s = (m @ rigid_obj.matrix_local).decompose()
                rigid_obj.location = t
                rigid_obj.rotation_euler = r.to_euler(rigid_obj.rotation_mode)
                
                # 处理虚拟子对象
                fake_children = self.__fake_parent_map.get(rigid_obj, None)
                if fake_children:
                    for fake_child in fake_children:
                        logging.debug("          - fake_child: %s", fake_child.name)
                        t, r, s = (m @ fake_child.matrix_local).decompose()
                        fake_child.location = t
                        fake_child.rotation_euler = r.to_euler(fake_child.rotation_mode)

                if "mmd_tools_rigid_track" not in target_bone.constraints:
                    # 创建刚体跟踪约束
                    context = FnContext.ensure_context()
                    empty = FnContext.new_and_link_object(context, name="mmd_bonetrack", object_data=None)
                    empty.matrix_world = target_bone.matrix
                    setattr(empty, Props.empty_display_type, "ARROWS")
                    setattr(empty, Props.empty_display_size, 0.1 * getattr(self.__root, Props.empty_display_size))
                    empty.mmd_type = "TRACK_TARGET"
                    empty.hide_set(True)
                    empty.parent = self.temporaryGroupObject()

                    rigid_obj.mmd_rigid.bone = bone_name
                    rigid_obj.constraints.remove(relation)  # 移除父约束

                    self.__empty_parent_map[empty] = rigid_obj  # 记录空对象和刚体的映射

                    # 根据刚体类型选择约束类型
                    const_type = ("COPY_TRANSFORMS", "COPY_ROTATION")[rigid_type - 1]
                    const = target_bone.constraints.new(const_type)
                    const.mute = True
                    const.name = "mmd_tools_rigid_track"
                    const.target = empty
                else:
                    # 更新现有的跟踪约束
                    empty = target_bone.constraints["mmd_tools_rigid_track"].target
                    if empty in self.__empty_parent_map:
                        ori_rigid_obj = self.__empty_parent_map[empty]
                        ori_rb = ori_rigid_obj.rigid_body
                        if ori_rb and rb.mass > ori_rb.mass:
                            logging.debug("        * Bone (%s): change target from [%s] to [%s]", target_bone.name, ori_rigid_obj.name, rigid_obj.name)
                            # 重新设置父对象
                            rigid_obj.mmd_rigid.bone = bone_name
                            rigid_obj.constraints.remove(relation)
                            self.__empty_parent_map[empty] = rigid_obj
                            # 恢复变化
                            ori_rigid_obj.mmd_rigid.bone = bone_name

        rb.collision_shape = rigid.shape  # 设置碰撞形状

    def buildRigids(self, non_collision_distance_scale: float, collision_margin: float) -> List[bpy.types.Object]:
        """构建刚体系统的主要方法
        
        该方法执行以下操作：
        1. 将刚体按碰撞组分组
        2. 创建关节映射表
        3. 分析并创建非碰撞约束
        4. 更新所有刚体对象的属性
        5. 创建额外的非碰撞约束
        
        Args:
            non_collision_distance_scale: 非碰撞距离缩放系数
            collision_margin: 碰撞边距值
            
        Returns:
            处理完成的所有刚体对象列表
        """
        logging.debug("--------------------------------")
        logging.debug(" Build riggings of rigid bodies")
        logging.debug("--------------------------------")
        rigid_objects = list(self.rigidBodies())
        
        # 将刚体按碰撞组分组（共16组）
        rigid_object_groups = [[] for _ in range(16)]
        for i in rigid_objects:
            rigid_object_groups[i.mmd_rigid.collision_group_number].append(i)

        # 创建关节映射表，用于快速查找两个刚体之间的关节
        jointMap = {}
        for joint in self.joints():
            rbc = joint.rigid_body_constraint
            if rbc is None:
                continue
            # 确保关联的刚体不为None
            if rbc.object1 is None or rbc.object2 is None:
                continue
            rbc.disable_collisions = False  # 初始设置为允许碰撞
            # 使用frozenset作为键，确保顺序不影响查找
            jointMap[frozenset((rbc.object1, rbc.object2))] = joint

        logging.info("Creating non collision constraints")
        # 创建非碰撞约束表和已处理的约束对集合
        nonCollisionJointTable = []
        non_collision_pairs = set()
        rigid_object_cnt = len(rigid_objects)
        
        # 遍历所有刚体，分析碰撞组掩码并创建非碰撞约束
        for obj_a in rigid_objects:
            # 遍历碰撞组掩码（共16个）
            for n, ignore in enumerate(obj_a.mmd_rigid.collision_group_mask):
                if not ignore:
                    continue  # 如果不忽略该组碰撞，则跳过
                    
                # 遍历与当前组相关的所有刚体
                for obj_b in rigid_object_groups[n]:
                    if obj_a == obj_b:
                        continue  # 跳过自身
                        
                    pair = frozenset((obj_a, obj_b))  # 创建刚体对
                    if pair in non_collision_pairs:
                        continue  # 已处理过的对，跳过
                    
                    # 检查是否已有关节连接这两个刚体
                    if pair in jointMap:
                        joint = jointMap[pair]
                        # 如果有关节，设置为非碰撞
                        if joint.rigid_body_constraint is not None:
                            joint.rigid_body_constraint.disable_collisions = True
                    else:
                        # 计算两个刚体之间的距离
                        distance = (obj_a.location - obj_b.location).length
                        # 如果距离小于阈值，创建非碰撞约束
                        if distance < non_collision_distance_scale * (self.__getRigidRange(obj_a) + self.__getRigidRange(obj_b)) * 0.5:
                            nonCollisionJointTable.append((obj_a, obj_b))
                    
                    non_collision_pairs.add(pair)  # 标记为已处理
        
        # 更新所有刚体对象
        for cnt, i in enumerate(rigid_objects):
            logging.info("%3d/%3d: Updating rigid body %s", cnt + 1, rigid_object_cnt, i.name)
            self.updateRigid(i, collision_margin)
        
        # 创建非碰撞约束
        self.__createNonCollisionConstraint(nonCollisionJointTable)
        return rigid_objects

    def buildJoints(self):
        """构建和更新所有关节对象的位置和旋转
        
        该方法遍历所有关节对象，根据关联的刚体变换矩阵更新关节的位置和旋转。
        这确保了关节在物理模拟中的正确位置和方向。
        """
        for i in self.joints():
            rbc = i.rigid_body_constraint
            if rbc is None:
                continue  # 如果没有刚体约束，跳过
                
            # 获取关联刚体的变换矩阵
            m = self.__rigid_body_matrix_map.get(rbc.object1, None)
            if m is None:
                # 如果第一个刚体没有变换矩阵，尝试第二个
                m = self.__rigid_body_matrix_map.get(rbc.object2, None)
                if m is None:
                    continue  # 如果都没有，跳过
                    
            # 计算并设置关节的位置和旋转
            t, r, s = (m @ i.matrix_local).decompose()
            i.location = t  # 设置位置
            i.rotation_euler = r.to_euler(i.rotation_mode)  # 设置旋转

    def clean(self):
        """清理物理构建过程中创建的所有约束和临时对象，并恢复原始状态
        
        该方法执行以下操作：
        1. 临时禁用刚体世界
        2. 移除骨骼上的刚体跟踪约束
        3. 为刚体创建或恢复父约束
        4. 恢复刚体和关节的原始变换
        5. 删除临时对象
        6. 更新场景状态
        7. 恢复刚体世界的原始启用状态
        """
        # 临时禁用刚体世界并保存当前启用状态
        rigidbody_world_enabled = rigid_body.setRigidBodyWorldEnabled(False)
        logging.info("****************************************")
        logging.info(" Clean rig")
        logging.info("****************************************")
        start_time = time.time()

        # 获取骨架对象的姿势骨骼
        pose_bones = []
        arm = self.armature()
        if arm is not None:
            pose_bones = arm.pose.bones
            
        # 移除所有骨骼上的刚体跟踪约束
        for i in pose_bones:
            if "mmd_tools_rigid_track" in i.constraints:
                const = i.constraints["mmd_tools_rigid_track"]
                i.constraints.remove(const)

        rigid_track_counts = 0
        # 处理所有刚体对象
        for i in self.rigidBodies():
            rigid_type = int(i.mmd_rigid.type)
            
            # 如果没有父约束，创建一个
            if "mmd_tools_rigid_parent" not in i.constraints:
                rigid_track_counts += 1
                logging.info('%3d# Create a "CHILD_OF" constraint for %s', rigid_track_counts, i.name)
                i.mmd_rigid.bone = i.mmd_rigid.bone  # 触发约束创建
            
            # 获取父约束
            relation = i.constraints["mmd_tools_rigid_parent"]
            relation.mute = True  # 禁用约束
            
            # 根据刚体类型设置父对象
            if rigid_type == MODE_STATIC:
                i.parent_type = "OBJECT"
                i.parent = self.rigidGroupObject()  # 设置父对象为刚体组
            elif rigid_type in {MODE_DYNAMIC, MODE_DYNAMIC_BONE}:
                arm = relation.target
                bone_name = relation.subtarget
                if arm is not None and bone_name != "":
                    # 启用IK约束
                    for c in arm.pose.bones[bone_name].constraints:
                        if c.type == "IK":
                            c.mute = False
            
            # 恢复刚体的原始变换
            self.__restoreTransforms(i)

        # 恢复所有关节的原始变换
        for i in self.joints():
            self.__restoreTransforms(i)

        # 删除所有临时对象
        temporary_objects = list(self.temporaryObjects())
        if temporary_objects:
            context = FnContext.ensure_context()
            # 保存当前选择和活动对象
            original_active_obj = context.view_layer.objects.active
            original_selected_objs = context.selected_objects
            
            # 选择要删除的对象
            bpy.ops.object.select_all(action='DESELECT')
            for obj in temporary_objects:
                # 删除对象
                bpy.data.objects.remove(obj, do_unlink=True)

            # 恢复之前的选择和活动对象
            bpy.ops.object.select_all(action='DESELECT')
            if original_active_obj:
                original_active_obj.select_set(True)
                FnContext.set_active_object(context, original_active_obj)
            for original_obj in original_selected_objs:
                original_obj.select_set(True)


        # 更新MMD根对象的状态
        mmd_root = self.rootObject().mmd_root
        if hasattr(mmd_root, "show_temporary_objects") and mmd_root.show_temporary_objects:
            mmd_root.show_temporary_objects = False
        
        logging.info(" Finished cleaning in %f seconds.", time.time() - start_time)
        mmd_root.is_built = False  # 标记物理未构建
        
        # 恢复刚体世界的原始启用状态
        rigid_body.setRigidBodyWorldEnabled(rigidbody_world_enabled)

    def build(self, non_collision_distance_scale: float = 1.5, collision_margin: float = 1e-06):
        """构建完整的MMD物理系统
        
        该方法是物理构建的主要入口点，协调以下步骤：
        1. 临时禁用刚体世界
        2. 如果已构建，先清理现有物理系统
        3. 设置构建状态标记
        4. 执行预构建准备工作
        5. 构建刚体和非碰撞约束
        6. 构建和更新关节
        7. 执行后构建清理和收尾工作
        8. 恢复刚体世界的原始启用状态
        
        Args:
            non_collision_distance_scale: 非碰撞距离缩放系数，用于确定何时创建额外的非碰撞约束
            collision_margin: 碰撞边距值，用于调整刚体碰撞检测的精度
        """
        # 临时禁用刚体世界并保存当前启用状态
        rigidbody_world_enabled = rigid_body.setRigidBodyWorldEnabled(False)
        
        # 如果已经构建了物理系统，先清理
        if self.__root.mmd_root.is_built:
            self.clean()
            return {'FINISHED'}
            
        # 设置构建状态标记
        self.__root.mmd_root.is_built = True
        logging.info("****************************************")
        logging.info(" Build rig")
        logging.info("****************************************")
        
        start_time = time.time()
        
        # 执行预构建准备工作
        self.__preBuild()
        
        # 构建刚体和非碰撞约束
        self.buildRigids(non_collision_distance_scale, collision_margin)
        
        # 构建和更新关节
        self.buildJoints()
        
        # 执行后构建清理和收尾工作
        self.__postBuild()
        
        logging.info(" Finished building in %f seconds.", time.time() - start_time)
        
        # 恢复刚体世界的原始启用状态
        rigid_body.setRigidBodyWorldEnabled(rigidbody_world_enabled)

# Blender操作符类
# 用于构建MMD刚体物理系统的Blender操作符
class MMD_RIG_PHYSICS_BUILD(bpy.types.Operator):
    bl_idname = "mmd_rig_physics.build"  # 操作符ID
    bl_label = "Build MMD Rig Physics"  # 操作符显示名称
    bl_description = "Translate physics of selected MMD object into format usable by Blender"  # 操作符描述
    bl_options = {"REGISTER", "UNDO"}  # 操作符选项：可注册、可撤销

    # 非碰撞距离缩放系数属性
    non_collision_distance_scale: bpy.props.FloatProperty(
        name="Non-Collision Distance Scale",  # 属性显示名称
        description="The distance scale for creating extra non-collision constraints while building physics",  # 属性描述
        min=0,  # 最小值
        soft_max=10,  # 软最大值（UI滑块的最大值）
        default=1.5,  # 默认值
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

    def execute(self, context):
        """执行操作符的主要逻辑
        
        该方法执行以下步骤：
        1. 启用刚体世界
        2. 查找选中的MMD根对象
        3. 创建Model对象并构建物理系统
        4. 处理可能的错误并报告结果
        
        Args:
            context: Blender上下文
            
        Returns:
            操作结果状态（FINISHED或CANCELLED）
        """
        # 确保刚体世界已启用
        if context.scene.rigidbody_world:
            context.scene.rigidbody_world.enabled = True

        # 查找选中的MMD根对象
        root_object = None
        for obj in context.selected_objects:
            if obj.mmd_type == "ROOT":  # 检查是否为MMD根对象
                root_object = obj
                break
                
        # 如果没有找到根对象，报告错误
        if root_object is None:
            self.report({"ERROR"}, "Selected object is not an MMD root object")
            return {"CANCELLED"}

        try:
            # 创建Model对象并构建物理系统
            rig = Model(root_object)
            rig.build(self.non_collision_distance_scale, self.collision_margin)
            
            # 设置根对象为活动对象
            FnContext.set_active_object(context, root_object)
            return {"FINISHED"}
        except Exception as e:
            # 处理异常并报告错误
            self.report({"ERROR"}, f"Failed to build physics: {str(e)}")
            logging.error("Failed to build physics: %s", str(e))
            return {"CANCELLED"}

# Blender菜单类
class MMD_RIG_PHYSICS_MT_main(bpy.types.Menu):
    bl_label = "MMD Rig Physics"
    bl_idname = "MMD_RIG_PHYSICS_MT_main"

    def draw(self, context):
        layout = self.layout
        layout.operator(MMD_RIG_PHYSICS_BUILD.bl_idname)

# 注册函数
def register():
    # 将菜单添加到3D视图的对象菜单中
    bpy.types.VIEW3D_MT_object.append(draw_menu)

# 取消注册函数
def unregister():
    # 从3D视图的对象菜单中移除
    bpy.types.VIEW3D_MT_object.remove(draw_menu)

# 菜单绘制函数
def draw_menu(self, context):
    layout = self.layout
    layout.menu(MMD_RIG_PHYSICS_MT_main.bl_idname)
