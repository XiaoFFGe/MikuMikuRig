from MikuMikuRig.common.i18n.dictionary import preprocess_dictionary

dictionary = {
    "zh_CN": {
        ("*", "MMD tool"): "MMD工具",
        ("Operator", "Optimization MMD Armature"): "优化MMD骨骼",
        ("Operator", "Build a controller"): "生成控制器",
        ("", "Extras"): "额外选项",
        ("*", "Controller options"): "控制器选项",
        ("", "Polar target"): "极向目标",
        ("", "Shoulder linkage"): "肩膀联动",
        ("", "Customize the initial pose"): "自定初始姿势",
        ("", "This option has a serious bug and should not be enabled"): "此选项存在严重的Bug，不要启用",
        ("", "presets"): "预设",
        ("", "Import presets"): "导入预设",
        ("Operator", "Import presets"): "导入预设",
        ("Operator", "Export presets"): "导出预设",
        ("", "Bend the arm bones"): "弯曲手臂骨骼",
        ("Operator", "make presets"): "制作预设",
        ("Operator", "Exit the designation"): "退出指定",
        ("Operator", "designated"): "指定",
        ("Operator", "Export VMD actions"): "导出VMD动作",
        ("", "Sets the default orientation"): "设置默认朝向",
        ("", "MMR Preset Editor"): "MMR预设编辑器",
        ("*", "MMR Preset Editor"): "MMR预设编辑器",
        ("", "Reference bones"): "参考骨骼",
        ("", "Professional version"): "专业版",
        ("", "Only meta bones are generated"): "仅生成元骨骼",
        ("*", "Bone retargeting"): "骨骼重定向",
        ("Operator", "Import FBX actions"): "导入FBX动作",
        ("Operator", "Import VMD actions"): "导入VMD动作",
        ("Operator", "Open the presets folder"): "打开预设文件夹",
        ("", "Finger tip bone repair"): "修复手指末端骨骼",
        ("", "Finger options"): "手指选项",
        ("", "Upper body linkage"): "上半身联动",
        ("", "Thumb twist aligns with the world Z-axis"): "拇指扭转与世界Z轴对齐",
        ("", "No Hide skeleton"): "不隐藏原骨架",
        ("", "Bend the leg bones"): "弯曲腿部骨骼",
        ("", "Bend angle"): "角度",
        ("", "Use ITASC solver"): "使用ITASC解算器",
        ("", "ORG mode"): "ORG模式",
    }
}

dictionary = preprocess_dictionary(dictionary)

dictionary["zh_HANS"] = dictionary["zh_CN"]
