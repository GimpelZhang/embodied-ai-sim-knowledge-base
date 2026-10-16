"""Q2 方案平目录导入夹具（Task0b 从 sim-praxis 迁入）。

三件生产脚本在方案目录内是平目录布局，而逐字迁入的 analyze_q2.py 保留其
引擎仓时代的绝对导入 ``sandbox.track2.carla_lidar_weather.optics_model``
（脚本一字未改，sha256 锁在 manifest）。本夹具把方案目录放上 sys.path，
并把平目录 optics_model 注册成该绝对路径的模块别名——只影响测试进程，
不修改任何生产文件。
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

SOLUTION_DIR = Path(__file__).resolve().parents[1]
if str(SOLUTION_DIR) not in sys.path:
    sys.path.insert(0, str(SOLUTION_DIR))

import optics_model  # noqa: E402

for _pkg in ("sandbox", "sandbox.track2",
             "sandbox.track2.carla_lidar_weather"):
    module = types.ModuleType(_pkg)
    module.__path__ = []  # 标记为包，阻止真实 sandbox 包搜索
    sys.modules.setdefault(_pkg, module)
sys.modules.setdefault(
    "sandbox.track2.carla_lidar_weather.optics_model", optics_model)
