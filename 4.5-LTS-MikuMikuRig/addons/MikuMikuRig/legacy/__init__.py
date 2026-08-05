"""Legacy 0.56 版本 — 包入口（实际代码在 legacy_main.py，auto_load 可发现）"""
from .legacy_main import (
    # PropertyGroup
    MMR_LEGACY_property,
    # 面板基类
    Mmr_Panel_Base,
    # 面板
    MikuMikuRig_1, MikuMikuRig_2, MikuMikuRig_3,
    MikuMikuRig_4, MikuMikuRig_5,
    # 操作符
    OT_Generate_Rig_Legacy,
    # 注册函数
    register, unregister,
    # 工具函数
    alert_error, _legacy_poll,
)