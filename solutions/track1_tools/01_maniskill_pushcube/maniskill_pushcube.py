#!/usr/bin/env python3
"""Task7 Track1 场景 2：ManiSkill3 PushCube-v1 真实 Panda rollout（SAPIEN/PhysX）。

物理任务（官方 PandaArmMotionPlanningSolver 策略，真实物理 + 真实 Vulkan 帧）：
  Panda 在桌面上把 4cm 立方块推入前方圆形目标（goal_radius=0.1m），规划结束
  冻结末动作 1.3s（130 控制步）保持接触。全程按控制帧记录：
    - ee：tcp 世界位姿（base.agent.tcp.pose.p）；
    - object：cube 世界位姿（base.obj.pose.p）；
    - contact_forces：手指/手爪各链接对 cube 的 get_pairwise_contact_forces
      三维矢量**求和后取模**（等价腕部 F/T 合力，与 MuJoCo 场景口径一致）；
    - 另存水平/竖直分量（contact_forces_horizontal_n / _vertical_n）与桌面
      法向反力，仅供机制审计，判定器不读（additionalProperties=true）；
    - penetrations：每物理步 scene.get_contacts() 全部接触点
      max(0, -PhysxContactPoint.separation) 的最大值。

后端选择（锁内适配，证据 runs/phase1/task7_track1/probe/，Task7 commit body 留痕）：
  生产用 sim_backend=physx_cpu + render_backend=gpu（Vulkan）。同种子双后端
  探针实测（2026-10-14，pushcube_proto_{cpu,gpu}.json、
  pushcube_forces_{cpu,gpu}.json）：
  1) GPU(PhysxGpuSystem) 无 scene.get_contacts()（AttributeError），拿不到
     逐接触点 separation → 无法诚实产出 Rung1 契约要求的每物理子步穿模深度；
  2) GPU 下冻结末动作「持位」段 get_pairwise_contact_forces 读数坍塌
     （120 帧仅 29 帧非零、最长连续 9 帧、均值 0.037N），而 CPU 同策略
     120/120 帧恒 ~24.4N、桌面反力同步 ~23.8N；GPU 力查询不能作为接触
     持续性证据。CPU 物理 + GPU 渲染可同时工作（探针帧 512×512 真实出图）。
  本选择不放宽任何判定阈值；残余风险（CPU 单环境性能）与 Task7 双引擎
  矩阵目的（跨引擎规则判定一致性）无冲突。

圆→盒映射（诚实、从严）：任务成功区是半径 r=0.1 的圆 + z<cube_half+5e-3
  （push_cube.py evaluate 原文），telemetry 契约只吃 axis-aligned 盒。
  goal_box 取圆的**内接正方形** half_xy=r/√2≈0.07071（盒是圆的严格子集：
  入盒必入圆，入圆未必入盒），z 半长 = cube_half+5e-3=0.025。为此规划
  瞄准点比官方 solvePushCube 的 -0.12 更深（PUSH_AIM_OFFSET=-0.07），把
  块推到圆心更深处——这是更严的任务几何，不是阈值放宽。outcome（入圆）
  与 mechanism（见下）在 manifest 分开报告。

持位机制事实（不得在报告里写成「水平预紧」）：探针持位稳态转储显示
  24.4N 合力中约 23N 为**竖直**分量——闭合手爪的指尖骑在块后上棱
  （接触点 z≈0.040=块顶高、法向 ≈+z、Panda 手指资产摩擦 μ=2.0），PD
  关节把臂重/保持力经指尖压向块、桌面反力 ~23.8N 平衡；水平分量约 7N。
  这是官方策略在钉死版本下的真实接触构型（与 MuJoCo 场景的推板-挡墙
  水平预紧不同），块 1.3s 内位姿静止（位姿差分 <1e-5 m/frame）是事实，
  但机制描述必须按本注释写，不得声称「侧向恒力夹持」。

禁用：numpy 合成帧/假遥测；渲染帧必须来自 env.render() 的 render_camera。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np  # noqa: E402

# --- 任务/物理参数（显式可溯源；判定阈值在 orchestrator/judge/thresholds.py） ---
SEED = 0
SIM_FREQ = 100                  # SimConfig 默认 sim_freq=100（锁内适配：不覆盖）
CONTROL_FREQ = 100              # 覆盖默认 20 → dt=0.01，落 Rung3 [1/120,1/30]
FRAME_DT = 1.0 / CONTROL_FREQ
SUBSTEPS_PER_FRAME = 1         # sim_freq==control_freq：每控制帧恰好 1 物理步
HOLD_STEPS = 130               # 1.3s 持位（>1.0s 接触持续性要求 + 0.5s 末窗余量）
# 锁内适配（计划无此常量，实测留痕）：冻结末动作后，块在持位首 ~10 帧（0.1s）
# 经历推动→静止的减速瞬态（hold_motion_diagnostic.json：v 0.0109 单调衰减，
# 第 9 帧 <0.005，末 30 帧 max 0.0032、净漂 0.07mm），属 settling 非 creep。
# 持位静止自检只对「排除 0.3s 稳定前缀后的持续持位窗」（实测 ~10 帧衰减的 3 倍
# 余量；余 100 帧=1.0s，恰为接触持续性时长）。telemetry 仍记录全部 130 帧，
# 判定器的接触 run / 末 0.5s 目标窗均独立取全量数据，不被裁剪。
HOLD_SETTLE_STEPS = 30
HOLD_STATIC_WINDOW_MIN = 100   # 排除瞬态后持续持位窗至少 1.0s（100 位置帧）
REACH_OFFSET_X = -0.05         # 官方 solvePushCube 首段瞄准点（块后 5cm）
PUSH_AIM_OFFSET_X = -0.085     # 锁内适配（探针实测，2026-10-14）：官方 -0.12 仅入圆；
                               # -0.07 持位法向塌（窗 CV 0.39）；-0.085 配慢速+预紧入内接
                               # 方盒且全程接触窗 CV 0.246（-0.09 起非单调劣化，见探针）
CONTACT_EPS_N = 1e-3
GOAL_RADIUS = 0.1              # PushCube-v1.goal_radius（钉死版本真值）
CUBE_HALF = 0.02               # PushCube-v1.cube_half_size
GOAL_HALF_XY = GOAL_RADIUS / math.sqrt(2.0)   # 圆内接正方形（严格子集）
GOAL_HALF_Z = CUBE_HALF + 5e-3               # 与 env 成功判据 z 条件一致
HOLD_STATIC_V_MAX = 0.01       # 持续持位窗逐帧速度上界（m/s，位姿差分，非判定阈值）
HOLD_STATIC_DRIFT_MAX_M = 0.001  # 持续持位窗净位移上界 1mm（块半宽 20mm 的 5%，防蠕变）
# 锁内适配（机制修正，2026-10-14 取证；判定阈值 0.30 未动）：mplib 的 screw 轨迹按
# 关节速度/加速度限位做时间参数化（官方解算器构造时 joint_vel_limits=0.9），
# follow_path 每控制帧执行一个路点。默认速度下手指在 0.13-0.17 m/s 巡航段首次
# 接触块，前 10 帧接触力从阈值冲到 ~0.5N 再回稳（该 10 帧 bin std=0.162）；对
# probe_aim_0085 实测 telemetry 的反事实测算：仅此接触建立瞬态就把最长接触窗
# CV 从 0.225（剔除前 10 帧）抬到 0.282。第二段 screw 规划前把 mplib 实例上的
# 速度/加速度限位整体乘该因子（减半→接触瞬间相对速度 ~0.07 m/s），规划+执行后
# 立即还原；不改库代码，与官方解算器同一公开旋钮（构造参数 joint_vel_limits）。
# 更深 IK 持位预紧：全速段 3/4/5/6/7/8mm 六组实测会引发粘滑（hold CV 0.33-0.53），
# 但配合 0.5 慢速推动后 5mm 把最长窗 CV 从 0.394 拉到 0.246（combos05p5）；瞬时
# 打入目标仍在持位首帧留下 std 0.165 冲击，故再用 PRELOAD_RAMP_FRAMES 线性压入。
PUSH_SPEED_FACTOR = 0.5
PUSH_PRELOAD_MM = 5.0            # 持位关节目标的额外压入深度（mm，dry_run IK 末端）
# 预紧施加方式（探针留痕，2026-10-14）：线性慢压（30/50 帧，≈0.01-0.017 m/s）实测
# 让块在「持位静止窗」持续蠕动（v_max 0.018-0.023>0.01 自检，未放水）——慢压长期
# 骑在动摩擦阈值上；瞬时打入是一次粘滑后落入静摩擦平衡（自检绿、末 80 帧
# 0.168±0.002N）。故生产默认 0=瞬时打入；>0 仅作机制探针参数保留并落 manifest。
PRELOAD_RAMP_FRAMES = 0

ENGINE_SIM_BACKEND = "physx_cpu"
ENGINE_RENDER_BACKEND = "gpu"


def _to_np(x) -> np.ndarray:
    import torch
    if isinstance(x, torch.Tensor):
        x = x.detach().cpu().numpy()
    return np.asarray(x, dtype=float).reshape(-1)


class TelemetryEnv:
    """薄包装：planner 调 env.step 时逐帧记录真实状态（其余属性透传）。"""

    def __init__(self, env):
        self._env = env
        self.unwrapped = env.unwrapped
        base = env.unwrapped
        self._cube = base.obj
        self._contact_links = [
            lk for lk in base.agent.robot.get_links()
            if "finger" in lk.name.lower() or "hand" in lk.name.lower()
        ]
        self._table = base.table_scene.table
        self.rows: list[dict] = []
        self.last_action = None
        self.frames: list[np.ndarray] = []

    def __getattr__(self, item):
        return getattr(self._env, item)

    def reset(self, *a, **k):
        return self._env.reset(*a, **k)

    def _max_penetration(self) -> float:
        """本物理步全场景最大嵌入深度（米）；separation<0 才是穿模。

        PhysX 接触流形里 positive separation（contact_offset 内的近接对点）
        与零冲量点都存在，必须只取负值（探针 pushcube_forces_cpu.json 取证）。
        仅 physx_cpu 提供 get_contacts（GPU PhysxGpuSystem 无此 API）。
        """
        m = 0.0
        for contact in self._env.unwrapped.scene.get_contacts():
            for pt in contact.points:
                sep = float(np.asarray(pt.separation).reshape(-1)[0])
                if sep < 0.0:
                    m = max(m, -sep)
        return m

    def _contact_force(self) -> tuple[float, float, float, float]:
        """返回 (合力模, 水平分量模, 竖直分量, 桌面法向反力模），单位 N。"""
        scene = self._env.unwrapped.scene
        total = np.zeros(3)
        for lk in self._contact_links:
            f = scene.get_pairwise_contact_forces(lk, self._cube)
            total += _to_np(f)[:3]
        horizontal = float(np.linalg.norm(total[:2]))
        vertical = float(abs(total[2]))
        table_f = _to_np(scene.get_pairwise_contact_forces(
            self._table, self._cube))[:3]
        return (float(np.linalg.norm(total)), horizontal, vertical,
                float(np.linalg.norm(table_f)))

    def step(self, action):
        self.last_action = action
        out = self._env.step(action)
        base = self._env.unwrapped
        tcp = _to_np(base.agent.tcp.pose.p)[:3]
        obj = _to_np(base.obj.pose.p)[:3]
        f_all, f_xy, f_z, f_table = self._contact_force()
        pen = self._max_penetration()
        self.rows.append({
            "tcp": tcp, "obj": obj,
            "f": f_all, "f_xy": f_xy, "f_z": f_z, "f_table": f_table,
            "pen": pen, "active": f_all > CONTACT_EPS_N,
        })
        frame = self._render_np(self._env.render())
        self.frames.append(frame)
        return out

    @staticmethod
    def _render_np(frame) -> np.ndarray:
        import torch
        if isinstance(frame, torch.Tensor):
            frame = frame.detach().cpu().numpy()
        arr = np.asarray(frame)
        if arr.ndim == 4 and arr.shape[0] == 1:  # GPU 批形态 (1,H,W,3)
            arr = arr[0]
        return arr


def _cv(arr: np.ndarray) -> float:
    arr = np.asarray(arr, dtype=float)
    return float(arr.std() / arr.mean()) if arr.mean() > 1e-12 else float("inf")


def _contact_profile(forces, fxy, fz, active, dt: float,
                     n0: int) -> dict:
    """接触力剖面诊断（镜像 Rung2 的最长连续接触窗 CV 口径，仅审计不判定）。

    用来区分两种机制：水平轻推（MuJoCo v4.1 实测均值 ~0.5N、CV 0.17、水平主导）
    与指尖楔入块底棱的竖直楔紧（本场景早期实测 ~21N、竖直主导、推动段 CV 0.53）。
    """
    f = np.abs(np.asarray(forces, dtype=float))
    xy = np.asarray(fxy, dtype=float)
    z = np.asarray(fz, dtype=float)
    am = np.asarray(active, dtype=bool)
    i0 = int(np.argmax(am)) if am.any() else -1
    if i0 < 0:
        return {"contact": False}
    # 最长连续 True 窗（与 orchestrator/judge/rungs.py 同口径）
    best_i, best_n, cur_i, cur_n = i0, 0, i0, 0
    for k in range(i0, len(am)):
        if am[k]:
            if cur_n == 0:
                cur_i = k
            cur_n += 1
            if cur_n > best_n:
                best_i, best_n = cur_i, cur_n
        else:
            cur_n = 0
    win = f[best_i:best_i + best_n]
    push = f[i0:n0] if n0 > i0 else f[i0:i0]
    hold = f[n0:]
    return {
        "contact": True,
        "first_contact_frame": i0,
        "longest_run_frames": best_n,
        "longest_run_s": round(best_n * dt, 4),
        "run_force_mean_n": round(float(win.mean()), 4),
        "run_contact_cv": round(_cv(win), 4),
        "push_force_mean_n": round(float(push.mean()), 4) if len(push) else None,
        "push_contact_cv": round(_cv(push), 4) if len(push) else None,
        "hold_force_mean_n": round(float(hold.mean()), 4) if len(hold) else None,
        "hold_contact_cv": round(_cv(hold), 4) if len(hold) else None,
        "hold_horizontal_mean_n": round(float(xy[n0:].mean()), 4),
        "hold_vertical_mean_n": round(float(z[n0:].mean()), 4),
        "run_first25_n": [round(float(v), 3) for v in f[i0:i0 + 25]],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--hold-steps", type=int, default=HOLD_STEPS)
    ap.add_argument("--aim-offset", type=float, default=PUSH_AIM_OFFSET_X)
    ap.add_argument("--reach-offset", type=float, default=REACH_OFFSET_X)
    ap.add_argument("--preload-mm", type=float, default=PUSH_PRELOAD_MM,
                    help="持位关节目标额外压入深度（mm，dry_run IK 更深末端）")
    ap.add_argument("--preload-ramp-frames", type=int, default=PRELOAD_RAMP_FRAMES,
                    help="持位前 N 帧把关节目标线性压入到 preload 深度，0=瞬时打入")
    ap.add_argument("--push-speed-factor", type=float, default=PUSH_SPEED_FACTOR,
                    help="第二段 screw 规划的关节速度/加速度限位比例（接触建立柔顺化）")
    ap.add_argument("--push-z", type=float, default=None,
                    help="screw 目标 z（米）；默认块心高，避免继承地面 goal_region z")
    args = ap.parse_args()

    import imageio.v2 as imageio
    import gymnasium as gym
    import sapien
    import mani_skill  # noqa: F401  确保注册 PushCube-v1
    from mani_skill.examples.motionplanning.panda.motionplanner import (
        PandaArmMotionPlanningSolver,
    )

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    t_wall0 = time.time()

    env = gym.make(
        "PushCube-v1",
        obs_mode="none",
        control_mode="pd_joint_pos",
        render_mode="rgb_array",
        sim_backend=ENGINE_SIM_BACKEND,
        render_backend=ENGINE_RENDER_BACKEND,
        sim_config=dict(control_freq=CONTROL_FREQ),
        max_episode_steps=None,
    )
    base = env.unwrapped
    env.reset(seed=args.seed)
    assert int(base.sim_freq) == SIM_FREQ and int(base.control_freq) == CONTROL_FREQ

    rec = TelemetryEnv(env)
    planner = PandaArmMotionPlanningSolver(
        rec, debug=False, vis=False,
        base_pose=base.agent.robot.pose,
        visualize_target_grasp_pose=False, print_env_info=False)

    # 官方两段 screw 策略（solvePushCube）：闭合 → 块后 5cm → 目标圆后偏移点。
    # 锁内适配（机制修正，探针+宿主 Rung2 取证）：官方 demo 第二段 screw 的 z
    # 继承地面 goal_region 位姿，把 TCP 从块心高 0.019 压到 0.015，指尖楔入块
    # 底棱，实测接触 ~21N 且竖直主导、推动段 CV 0.53（Rung2 全长 CV 0.371>0.30）。
    # 两段 screw 的 z 一律钉到块心高，使指面正对块后竖直面、接触水平轻推
    # （对齐已全绿的 MuJoCo v4.1：~0.5N、CV 0.17）。判定阈值 0.30 未动。
    push_z = float(args.push_z) if args.push_z is not None \
        else float(base.obj.pose.sp.p[2])
    tcp_q = base.agent.tcp.pose.sp.q
    reach_xyz = base.obj.pose.sp.p + np.array([args.reach_offset, 0, 0])
    reach_xyz[2] = push_z
    planner.close_gripper()
    reach_pose = sapien.Pose(p=reach_xyz, q=tcp_q)
    planner.move_to_pose_with_screw(reach_pose)
    push_xyz = base.goal_region.pose.sp.p + np.array([args.aim_offset, 0, 0])
    push_xyz[2] = push_z
    push_pose = sapien.Pose(p=push_xyz, q=tcp_q)
    # 接触建立柔顺化（见 PUSH_SPEED_FACTOR 注释）：仅缩放第二段 screw 的规划限位，
    # 首段空中 screw 与夹爪闭合保持官方速度；执行后立即还原（finally 覆盖规划失败）。
    _mpl = planner.planner
    _vel_lim0 = np.asarray(_mpl.joint_vel_limits).copy()
    _acc_lim0 = np.asarray(_mpl.joint_acc_limits).copy()
    _mpl.joint_vel_limits = _vel_lim0 * float(args.push_speed_factor)
    _mpl.joint_acc_limits = _acc_lim0 * float(args.push_speed_factor)
    try:
        push_rc = planner.move_to_pose_with_screw(push_pose)
    finally:
        _mpl.joint_vel_limits = _vel_lim0
        _mpl.joint_acc_limits = _acc_lim0
    assert push_rc != -1, "第二段 screw 规划失败（官方解算器两段均失败）"

    # 持位预紧（机制修正，零墙；判定阈值 0.30 全程未动）：PushCube 无墙，screw
    # 末端减速到静止时块回弹、手指回到目标位姿致 PD 误差≈0，慢速推动（factor 0.5）
    # 下持位法向塌到 0.105N（推动平台 0.26N，窗 CV 0.394）。MuJoCo v4.1 靠抵墙维持
    # 0.599N；本场景改用更深的关节目标让 PD 持续施压：dry_run 取更深 5mm 位姿的
    # 末端 IK 关节目标但不执行轨迹（实测再跑 screw 法向仍塌），到位即瞬时打入目标，
    # 一次粘滑后落入静摩擦平衡（combos05p5：末 80 帧 0.168±0.002N、块不蠕变，
    # 最长接触窗 CV 0.246）。慢压线性插值（PRELOAD_RAMP_FRAMES>0）实测诱发持续
    # 蠕动、过不了静止自检，仅留作探针参数，生产默认 0。
    hold_action = rec.last_action
    if args.preload_mm:
        deep_xyz = push_xyz + np.array([args.preload_mm / 1000.0, 0.0, 0.0])
        deep_pose = sapien.Pose(p=deep_xyz, q=tcp_q)
        plan = planner.move_to_pose_with_screw(deep_pose, dry_run=True)
        if plan == -1 or plan is None or not len(plan.get("position", [])):
            raise AssertionError(
                f"持位预紧 IK 失败（preload={args.preload_mm}mm），不静默降级")
        n_arm = int(np.asarray(rec.last_action).shape[0]) - 1
        q_deep = np.asarray(plan["position"][-1]).reshape(-1)[:n_arm]
        hold_action = np.hstack([q_deep, np.asarray(rec.last_action)[n_arm:]])
    assert hold_action is not None, "planner 未产生任何 action"

    # 持位：可选线性压入前缀 + 恒定关节目标冻结（PD 关节保持，真实接触；不是墙）
    n0 = len(rec.rows)
    ramp = int(args.preload_ramp_frames) if args.preload_mm else 0
    assert 0 <= ramp < args.hold_steps, "preload-ramp-frames 必须在 [0, hold_steps)"
    if ramp:
        q_start = np.asarray(rec.last_action, dtype=float).reshape(-1)
        q_final = np.asarray(hold_action, dtype=float).reshape(-1)
        for k in range(ramp):
            alpha = (k + 1.0) / ramp
            rec.step(q_start + alpha * (q_final - q_start))
        freeze_steps = args.hold_steps - ramp
    else:
        freeze_steps = args.hold_steps
    for _ in range(freeze_steps):
        rec.step(hold_action)
    planner.close()

    n_frames = len(rec.rows)
    assert n_frames >= 6, f"帧数 {n_frames} 不足契约下限 6"

    # —— 视频（真实 render_camera 帧；精确 100fps，不重定时） ——
    video_path = os.path.join(out_dir, "video.mp4")
    cover_path = os.path.join(out_dir, "cover.png")
    writer = imageio.get_writer(
        video_path, fps=1.0 / FRAME_DT,
        codec="libx264", quality=8, macro_block_size=None,
        output_params=["-pix_fmt", "yuv420p", "-crf", "28"])
    try:
        for fi, frame in enumerate(rec.frames):
            assert frame.dtype == np.uint8 and frame.ndim == 3, frame.shape
            if fi == 0:
                imageio.imwrite(cover_path, frame)
                var0 = float(frame.astype("float32").var())
                assert var0 > 10.0, f"首帧疑似纯色 var={var0}"
            writer.append_data(frame)
    finally:
        writer.close()

    # —— 组装时序 ——
    ee_positions = [r["tcp"].round(6).tolist() for r in rec.rows]
    object_poses = [r["obj"].round(6).tolist() for r in rec.rows]
    contact_forces = [round(r["f"], 6) for r in rec.rows]
    contact_forces_xy = [round(r["f_xy"], 6) for r in rec.rows]
    contact_forces_z = [round(r["f_z"], 6) for r in rec.rows]
    table_forces = [round(r["f_table"], 6) for r in rec.rows]
    contact_active = [bool(r["active"]) for r in rec.rows]
    penetrations = [round(r["pen"], 7) for r in rec.rows]
    assert len(penetrations) == n_frames * SUBSTEPS_PER_FRAME

    goal_xy = _to_np(base.goal_region.pose.p)[:2]
    goal_center = [float(goal_xy[0]), float(goal_xy[1]), CUBE_HALF]
    goal_half = [GOAL_HALF_XY, GOAL_HALF_XY, GOAL_HALF_Z]
    obj_end = object_poses[-1]
    dist_circle = float(np.linalg.norm(
        np.array(obj_end[:2]) - goal_xy))
    env_success = bool(base.evaluate()["success"].reshape(-1)[0].item())

    # —— 物理事实自检（不读判定器阈值；异常即非零退出，绝不写假数据） ——
    assert all(math.isfinite(v) for row in ee_positions for v in row)
    assert all(math.isfinite(v) for row in object_poses for v in row)
    first_contact = next((i for i, a in enumerate(contact_active) if a), None)
    assert first_contact is not None, "全程无 ee-object 接触力"
    hold_active = contact_active[n0:]
    assert all(hold_active), \
        f"持位 {args.hold_steps} 帧存在无接触帧：{sum(hold_active)}/{len(hold_active)}"
    # 接触力剖面（审计口径同 Rung2；不作场景内阈值判定，CV 判定权在判定器）
    profile = _contact_profile(
        contact_forces, contact_forces_xy, contact_forces_z,
        contact_active, FRAME_DT, n0)
    in_box = all(abs(obj_end[k] - goal_center[k]) <= goal_half[k] + 1e-9
                 for k in range(3))
    assert in_box, \
        f"末帧块不在圆形目标内接方盒：{obj_end} center={goal_center}"
    assert env_success and dist_circle < GOAL_RADIUS, \
        f"env 成功判据 False 或 dist={dist_circle}>={GOAL_RADIUS}"
    # 持位静止：位姿有限差分时序（不信任 get_linear_velocity 缓存，
    # 探针观察到位姿静止时该读数恒定非零，疑似 CPU 路径缓冲不刷新）。
    # 诊断：区分首帧残余速度衰减（settling）与持续蠕变（creep，v3 教训）。
    hold_xy = np.array([r["obj"] for r in rec.rows[n0:]], dtype=float)
    hold_step = np.linalg.norm(np.diff(hold_xy, axis=0), axis=1)
    hold_v = hold_step / FRAME_DT
    # 锁内适配（见 HOLD_SETTLE_STEPS 注释）：自检只约束排除减速瞬态后的持续
    # 持位窗；全段 v_max 仍落诊断/manifest 供审计，不隐藏首帧瞬态。
    assert args.hold_steps - HOLD_SETTLE_STEPS >= HOLD_STATIC_WINDOW_MIN, \
        f"持位 {args.hold_steps} 帧扣除 {HOLD_SETTLE_STEPS} 稳定前缀后不足 " \
        f"{HOLD_STATIC_WINDOW_MIN} 帧持续窗"
    static_xy = hold_xy[HOLD_SETTLE_STEPS:]
    static_v = hold_v[HOLD_SETTLE_STEPS:]
    static_net_disp = float(np.linalg.norm(static_xy[-1] - static_xy[0]))
    top_idx = np.argsort(hold_v)[-5:][::-1].tolist()
    diag = {
        "hold_steps": args.hold_steps,
        "settle_steps": HOLD_SETTLE_STEPS,
        "static_window_frames": int(len(static_xy)),
        "v_max_full_mps": round(float(hold_v.max()), 6),
        "v_max_static_window_mps": round(float(static_v.max()), 6),
        "static_window_net_disp_m": round(static_net_disp, 7),
        "top5_full": [{"hold_frame": int(i), "v_mps": round(float(hold_v[i]), 6),
                       "step_m": round(float(hold_step[i]), 7)} for i in top_idx],
        "v_first10": [round(float(v), 6) for v in hold_v[:10]],
        "v_last10": [round(float(v), 6) for v in hold_v[-10:]],
        "net_disp_full_m": round(float(
            np.linalg.norm(hold_xy[-1] - hold_xy[0])), 7),
    }
    (Path(out_dir) / "hold_motion_diagnostic.json").write_text(
        json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")
    assert float(static_v.max()) < HOLD_STATIC_V_MAX, \
        f"持续持位窗（排除{HOLD_SETTLE_STEPS}帧瞬态）块未静止，" \
        f"v_max={static_v.max():.4f} m/s（全段峰值 {hold_v.max():.4f}）"
    assert static_net_disp <= HOLD_STATIC_DRIFT_MAX_M, \
        f"持续持位窗净漂移 {static_net_disp*1e3:.3f}mm > " \
        f"{HOLD_STATIC_DRIFT_MAX_M*1e3:.1f}mm，疑似蠕变而非静止持位"
    # 接触连续性起点必须在持位段结束前（机制事实，非凑阈值）
    assert n_frames - first_contact >= int(1.0 / FRAME_DT), \
        "首触过晚，无法形成 ≥1.0s 接触段"

    telemetry = {
        "dt": FRAME_DT,
        "ee_positions": ee_positions,
        "object_poses": object_poses,
        "goal_box": {"center": goal_center, "half_extents": goal_half},
        "penetrations": penetrations,
        "contact_forces": contact_forces,
        "contact_active": contact_active,
        "substeps_per_frame": SUBSTEPS_PER_FRAME,
        "engine": "sapien",
        "run_id": args.run_id,
        "ccd": {"swept": False},
        "scenario": "maniskill_pushcube",
        # 机制审计字段（判定器不读）：
        "contact_forces_horizontal_n": contact_forces_xy,
        "contact_forces_vertical_n": contact_forces_z,
        "table_normal_forces_n": table_forces,
    }
    tele_path = os.path.join(out_dir, "telemetry.json")
    with open(tele_path, "w", encoding="utf-8") as fh:
        json.dump(telemetry, fh, ensure_ascii=False)

    hold_forces = contact_forces[n0:]
    hold_fxy = contact_forces_xy[n0:]
    hold_fz = contact_forces_z[n0:]
    hold_table = table_forces[n0:]
    active_forces = [f for f in contact_forces if f > CONTACT_EPS_N]
    manifest = {
        "run_id": args.run_id,
        "scenario": "maniskill_pushcube",
        "engine": "sapien",
        "sim_backend": ENGINE_SIM_BACKEND,
        "render_backend": ENGINE_RENDER_BACKEND,
        "sapien_version": sapien.__version__,
        "maniskill_version": mani_skill.__version__,
        "numpy_version": np.__version__,
        "python": sys.version.split()[0],
        "seed": args.seed,
        "frame_dt_s": FRAME_DT,
        "sim_freq_hz": SIM_FREQ,
        "control_freq_hz": CONTROL_FREQ,
        "substeps_per_frame": SUBSTEPS_PER_FRAME,
        "n_frames": n_frames,
        "planner": "PandaArmMotionPlanningSolver",
        "reach_offset_x": args.reach_offset,
        "push_aim_offset_x": args.aim_offset,
        "push_target_z_m": round(push_z, 6),
        "preload_mm": args.preload_mm,
        "preload_ramp_frames": args.preload_ramp_frames,
        "push_speed_factor": args.push_speed_factor,
        "contact_profile": profile,
        "hold_steps": args.hold_steps,
        "goal_region": "circle",
        "goal_radius_m": GOAL_RADIUS,
        "goal_box_mapping": "axis-aligned inscribed square of success circle "
                            "(half=r/sqrt2, strict subset); z half=cube_half+5e-3",
        "first_contact_frame": first_contact,
        "contact_force_max_n": max(active_forces),
        "contact_force_mean_n": sum(active_forces) / len(active_forces),
        "hold_contact_frames": sum(hold_active),
        "hold_force_min_n": min(hold_forces),
        "hold_force_mean_n": sum(hold_forces) / len(hold_forces),
        "hold_horizontal_mean_n": sum(hold_fxy) / len(hold_fxy),
        "hold_vertical_mean_n": sum(hold_fz) / len(hold_fz),
        "hold_table_normal_mean_n": sum(hold_table) / len(hold_table),
        "hold_v_max_full_mps": round(float(hold_v.max()), 6),
        "hold_settle_steps": HOLD_SETTLE_STEPS,
        "hold_static_window_frames": int(len(static_xy)),
        "hold_v_max_static_window_mps": round(float(static_v.max()), 6),
        "hold_static_window_net_disp_m": round(static_net_disp, 7),
        "max_penetration_m": max(penetrations),
        "object_xyz_end": obj_end,
        "goal_center": goal_center,
        "dist_to_circle_center_end_m": round(dist_circle, 6),
        "env_success_end": env_success,
        "mechanism_note": "steady hold contact is PD-maintained finger-on-cube "
                         "top-rear edge (vertical-dominant, finger friction mu=2.0); "
                         "no wall; cube static by pose finite-difference",
        "wall_s": round(time.time() - t_wall0, 3),
        "artifacts": {"telemetry": tele_path, "video": video_path,
                      "cover": cover_path},
    }
    with open(os.path.join(out_dir, "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "run_id": args.run_id,
                      "n_frames": n_frames,
                      "first_contact_frame": first_contact,
                      "max_penetration_m": round(max(penetrations), 6),
                      "contact_force_mean_n":
                          round(manifest["contact_force_mean_n"], 4),
                      "hold_f_mean_n": round(manifest["hold_force_mean_n"], 4),
                      "hold_fxy_mean_n": round(manifest["hold_horizontal_mean_n"], 4),
                      "hold_fz_mean_n": round(manifest["hold_vertical_mean_n"], 4),
                      "contact_cv_longest_run": profile.get("run_contact_cv"),
                      "push_cv": profile.get("push_contact_cv"),
                      "hold_cv": profile.get("hold_contact_cv"),
                      "push_z": round(push_z, 4),
                      "dist_circle_end": round(dist_circle, 4),
                      "object_xyz_end": [round(v, 4) for v in obj_end]},
                     ensure_ascii=False))
    env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
