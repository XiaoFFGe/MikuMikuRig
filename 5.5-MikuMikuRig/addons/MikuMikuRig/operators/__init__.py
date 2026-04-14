import bpy

def has_keyframes_for_property(obj, data_path):
    """检查属性是否有关键帧"""

    if not obj.animation_data or not obj.animation_data.action:
        return False

    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == data_path and fcurve.keyframe_points:
            return True

    # 移除路径中的引号差异
    data_path = data_path.replace("'", '"')

    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == data_path and fcurve.keyframe_points:
            return True
    return False