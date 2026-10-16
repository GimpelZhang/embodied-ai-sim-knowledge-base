#!/usr/bin/env python3
"""Task7 Track1 场景 1：MuJoCo 原生「最小接触推送」真实 rollout。

物理任务（与 Rung1–3 契约对齐，但不为阈值倒填数据）：
  平面上一个 5cm 立方块（object，0.1kg），平面推板（ee，覆盖方块整个
  立面、x 滑接 + 位置作动器）沿 +x 以 min-jerk 平滑轨迹把方块推入目标
  公差盒并压向末端固定挡块，随后保持 0.8s。全程记录：
    - 每帧 ee/object 位姿（真实 mj_step 状态）；
    - 每物理子步所有接触对的最大穿模深度（contact.dist<0 的量）；
    - ee-object 接触力：mj_contactForce 各接触点力（接触系→世界系）
      矢量求和后的合力模（等价腕部 F/T 读数）。不能用 efc_force 纯法向行：
      默认金字塔摩擦锥下滑动传力走摩擦锥斜向行，滑动段纯法向行读 0
      （v4 实测误判推送段全程「无接触」，证据 run_smoke_mujoco_4）；
      data.cfrc_ext 在 mj_step 路径不更新，3.15 实测恒零，禁用。
产物（写 --out-dir，必须在挂载卷内）：
  telemetry.json   单 JSON 对象（judge.file_backed_evaluate 契约）
  video.mp4        EGL 离屏渲染，libx264/yuv420p/crf28，60fps 量级
  cover.png        首帧封面
  manifest.json    版本/参数/接触几何事实（安装版本清单另由调用方落）

锁内适配（计划 Task7 L557）：计划产物名 telemetry.jsonl，但
file_backed_evaluate（nodes.py）与 validate_telemetry 要求单 JSON 对象
（json.load），故本场景落 telemetry.json；差异在 Task7 commit body 留痕。

禁用：numpy 合成帧/假遥测（渲染帧必须来自 mujoco.Renderer.render()）。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

# EGL 必须在 import mujoco 前
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np  # noqa: E402
import mujoco  # noqa: E402

# --- 物理/任务参数（全部显式，无裸数字散落在算法里） ---
PHYS_DT = 0.002                # MuJoCo 积分步长（默认接触 τ 同量级）
SUBSTEPS = 8                   # 每渲染/遥测帧 8 子步 → frame dt = 0.016
FRAME_DT = PHYS_DT * SUBSTEPS
SETTLE_S = 0.2
PUSH_S = 2.0
HOLD_S = 0.8

CUBE_HALF = 0.025              # 5cm 块，TASK_OBJECT_SCALE_M
CUBE_MASS = 0.1
# 锁内适配（第一性原理修正，判定阈值未动；宿主纯力学扫描证据
# runs/phase1/task7_track1/probe/，各版 run_smoke_mujoco_* 整目录保留）：
# v1 r=2cm 球推：球面攀爬方块立面、接触对反复消失，方块滞在 x=0.253 未到
#   挡块，Rung2 最长连续接触 0.912s<1.0s 真实失败。
# v2 平面推板+kp=200：高刚度作动器配默认软接触（solref 0.02）在 2ms 步长下
#   颤振——帧末 mj_forward 采样 efc_force 恒~0（接触力只存在于子步冲击瞬间），
#   方块仍在挡块前 5.9cm 处抖停。
# v3 轻量推板+kp=60+子步峰值力：outcome 入盒（末位 0.270）但机制为假——宿主
#   力学转储发现位置作动器吃的是滑接**相对坐标**，v1–v3 误喂世界 x，整条
#   轨迹平移 X_START：推板实际止于 0.235，挡块从未参与，持位靠静摩擦（延 2.5s
#   仍蠕变）。outcome 与 mechanism 分开报告，未用入盒掩盖假机制。
# v4（本版）：ctrl 改喂 x_traj-X_START（修复坐标语义）；显式推板 0.02kg；
#   kp=100、2.0s 准静态推送（峰值 0.30m/s）；末端越位 6mm 保持 ~0.6N 压紧。
#   宿主扫描实测（未为阈值倒填，kp150 因 CV 0.32–0.35 被真实否决，kp100 选中）：
#   首触后接触连续 2.54s 零中断、抵墙持位法向力恒 0.599N、终速~1e-15 零蠕变、
#   最大穿模 0.22mm、末位 0.305 贴墙；contact_cv=0.182。
# v4.1（本版）：v4 容器真实 run（run_smoke_mujoco_4）Rung1–3 虽过，但暴露
#   测量错误：纯法向 efc 行在滑动推送段读 0（金字塔摩擦锥的斜向传力），稳定
#   接触段被误记为仅抵墙后 1.008s（阈值余量 8ms）。改测 mj_contactForce
#   世界系合力模后宿主实测：首触后连续接触 2.544s 零中断、CV 0.173、
#   持位合力恒 0.599N。物理参量未动，只修正「测什么力」。
#   Rung1–3 阈值/查询一律未改，接触摩擦取 0.3（干木面量级，显式可溯源）。
PUSHER_HALF_X = 0.01
PUSHER_HALF_Y = 0.04
PUSHER_HALF_Z = CUBE_HALF       # 0..0.05 与方块等高，底面恰贴地
PUSHER_MASS = 0.02              # 轻薄推板，降低撞击惯性（显式 mass，不靠默认密度）
FRICTION = 0.3
PUSHER_DAMPING = 1.0
PUSHER_KP = 100.0
X_START = -0.04                 # 推板中心（+x 面 -0.03，与方块立面留 5mm 初始间隙）
X_END = 0.276                   # 持位目标（世界 x）：贴墙几何位 0.270 之外越位 6mm 保持压紧
WALL_X = 0.33                   # 固定挡块接触面 x（方块中心止于 0.305）
SOLREF_STIFF = "0.01 1"         # 推板/方块/挡块接触对：比默认 0.02 更刚，减颤振
GOAL_CENTER = [0.30, 0.0, CUBE_HALF]
GOAL_HALF = [0.05, 0.05, 0.05]
CONTACT_EPS_N = 1e-3

XML = f"""
<mujoco model="simpraxis_t7_contact_push">
  <option timestep="{PHYS_DT}"/>
  <default>
    <geom friction="{FRICTION} 0.005 0.0001"/>
  </default>
  <worldbody>
    <light pos="0.25 -0.5 1.2" dir="0 0.4 -1"/>
    <geom name="floor" type="plane" size="2 2 0.1"/>
    <!-- 目标区可视化（纯视觉薄框，不参与碰撞：contype=0） -->
    <geom name="goal_mark" type="box" pos="0.30 0 0.001"
          size="0.05 0.05 0.001" contype="0" conaffinity="0"
          rgba="0.1 0.7 0.2 0.35"/>
    <geom name="backstop" type="box" pos="{WALL_X + 0.01} 0 0.05"
          size="0.01 0.06 0.05" rgba="0.5 0.5 0.55 1" solref="{SOLREF_STIFF}"/>
    <body name="cube" pos="0 0 {CUBE_HALF}">
      <freejoint name="cube_joint"/>
      <geom name="cube_geom" type="box" size="{CUBE_HALF} {CUBE_HALF} {CUBE_HALF}"
            mass="{CUBE_MASS}" rgba="0.85 0.25 0.15 1" solref="{SOLREF_STIFF}"/>
    </body>
    <body name="pusher" pos="{X_START} 0 {CUBE_HALF}">
      <joint name="pusher_x" type="slide" axis="1 0 0" damping="{PUSHER_DAMPING}"/>
      <geom name="pusher_geom" type="box"
            size="{PUSHER_HALF_X} {PUSHER_HALF_Y} {PUSHER_HALF_Z}"
            mass="{PUSHER_MASS}"
            rgba="0.15 0.35 0.85 1" solref="{SOLREF_STIFF}"/>
    </body>
  </worldbody>
  <actuator>
    <position name="pusher_pos" joint="pusher_x" kp="{PUSHER_KP}"
              ctrlrange="-1 1" ctrllimited="false"/>
  </actuator>
</mujoco>
"""


def min_jerk_x(t0: float, t1: float, x0: float, x1: float):
    """返回 f(t)；五阶 min-jerk 轨迹（起止速度/加速度均 0）。"""
    def f(t: float) -> float:
        if t <= t0:
            return x0
        if t >= t1:
            return x1
        u = (t - t0) / (t1 - t0)
        return x0 + (x1 - x0) * (10 * u**3 - 15 * u**4 + 6 * u**5)
    return f


def pair_force(model, data, a_name: str, b_name: str) -> float:
    """b 对 a 的当前接触**合力模**（N，世界系；多接触点矢量求和取模）。

    用 mj_contactForce 取每点接触系 6D wrench，前 3 维经 contact.frame
    旋回世界系后求和；符号约定为 a 受到的力（a==geom1 时接触系力反向）。
    不取 efc_force 纯法向行：默认金字塔摩擦锥把摩擦传力编入斜向约束行，
    滑动接触下纯法向行恒~0 而物体已被真实推动（v4 证据 run_smoke_mujoco_4）。
    """
    ga = model.geom(a_name).id
    gb = model.geom(b_name).id
    total = np.zeros(3)
    for i in range(data.ncon):
        c = data.contact[i]
        if {c.geom1, c.geom2} != {ga, gb}:
            continue
        wrench = np.zeros(6)
        mujoco.mj_contactForce(model, data, i, wrench)
        f_world = c.frame.reshape(3, 3).T @ wrench[:3]
        if c.geom1 == ga:
            f_world = -f_world
        total += f_world
    return float(np.linalg.norm(total))


def max_penetration(model, data) -> float:
    """本子步所有接触对最大嵌入深度（米，非负；dist<0 为穿模）。"""
    m = 0.0
    for i in range(data.ncon):
        d = float(data.contact[i].dist)
        if d < 0.0:
            m = max(m, -d)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    args = ap.parse_args()

    import imageio.v2 as imageio

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    t_wall0 = time.time()

    model = mujoco.MjModel.from_xml_string(XML)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    n_settle = int(SETTLE_S / FRAME_DT)
    n_push = int(PUSH_S / FRAME_DT)
    n_hold = int(HOLD_S / FRAME_DT)
    n_frames = n_settle + n_push + n_hold

    x_traj = min_jerk_x(SETTLE_S, SETTLE_S + PUSH_S, X_START, X_END)

    renderer = mujoco.Renderer(model, height=args.height, width=args.width)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.13, 0.0, 0.03]
    cam.distance = 0.95
    cam.elevation = -22
    cam.azimuth = 70

    video_path = os.path.join(out_dir, "video.mp4")
    cover_path = os.path.join(out_dir, "cover.png")
    writer = imageio.get_writer(
        video_path, fps=1.0 / FRAME_DT,   # 精确 62.5fps：帧 dt=0.016，不四舍五入重定时
        codec="libx264", quality=8, macro_block_size=None,
        output_params=["-pix_fmt", "yuv420p", "-crf", "28"])

    ee_positions: list[list[float]] = []
    object_poses: list[list[float]] = []
    contact_forces: list[float] = []
    contact_active: list[bool] = []
    # 方块-挡块法向力（机制证据：本任务要求末端真实抵墙，不只位姿入盒；
    # v3 教训——outcome 在盒但挡块从未参与，故独立记录且在自检中断言）
    wall_forces: list[float] = []
    penetrations: list[float] = []
    force_trace = []
    first_contact_frame = None
    first_wall_frame = None

    try:
        sim_t = 0.0
        for fi in range(n_frames):
            # 力测量在每个物理子步做（v2 教训：软接触下帧末 mj_forward 的
            # efc_force 恒~0，真实力只存在于子步内）；frame 级取子步峰值，
            # contact_active 看子步内是否存在有效接触力。
            frame_force = 0.0
            frame_wall = 0.0
            frame_active = False
            for _ in range(SUBSTEPS):
                # v4 关键修正：position actuator 的 ctrl 是滑接相对坐标
                # （body pos 偏移量），不是世界 x；喂世界坐标会令整条轨迹
                # 平移 X_START（v1–v3 假机制根因，见上方版本注释）。
                data.ctrl[0] = x_traj(sim_t) - X_START
                mujoco.mj_step(model, data)
                sim_t += PHYS_DT
                penetrations.append(max_penetration(model, data))
                sf = pair_force(model, data, "pusher_geom", "cube_geom")
                wf = pair_force(model, data, "cube_geom", "backstop")
                if sf > frame_force:
                    frame_force = sf
                if wf > frame_wall:
                    frame_wall = wf
                if sf > CONTACT_EPS_N:
                    frame_active = True
                if wf > CONTACT_EPS_N and first_wall_frame is None:
                    first_wall_frame = fi
            mujoco.mj_forward(model, data)

            ee = [float(data.body("pusher").xpos[0]),
                  float(data.body("pusher").xpos[1]),
                  float(data.body("pusher").xpos[2])]
            obj = [float(data.body("cube").xpos[0]),
                   float(data.body("cube").xpos[1]),
                   float(data.body("cube").xpos[2])]
            f = frame_force
            active = frame_active
            if active and first_contact_frame is None:
                first_contact_frame = fi
            ee_positions.append(ee)
            object_poses.append(obj)
            contact_forces.append(round(f, 6))
            contact_active.append(active)
            wall_forces.append(round(frame_wall, 6))
            force_trace.append(round(f, 4))

            renderer.update_scene(data, camera=cam)
            img = renderer.render()
            assert img.dtype == np.uint8 and img.ndim == 3, img.shape
            if fi == 0:
                imageio.imwrite(cover_path, img)
                var0 = float(img.astype("float32").var())
                assert var0 > 10.0, f"首帧疑似纯色 var={var0}"
            writer.append_data(img)
    finally:
        writer.close()
        try:
            renderer.close()
        except Exception:  # noqa: BLE001 - EGL 析构期已知噪音
            pass

    # —— 物理事实自检（不读判定器阈值；异常即非零退出，绝不写假数据） ——
    assert first_contact_frame is not None, "全程无 ee-object 接触"
    assert penetrations and max(penetrations) >= 0.0
    obj_end = object_poses[-1]
    in_goal = all(abs(obj_end[k] - GOAL_CENTER[k]) <= GOAL_HALF[k]
                  for k in range(3))
    assert in_goal, f"末帧方块不在目标盒：{obj_end}"
    assert all(math.isfinite(v) for row in ee_positions for v in row)
    assert all(math.isfinite(v) for row in object_poses for v in row)
    # 机制自检（非阈值凑数）：持位段每一帧方块都必须真实抵住挡块，
    # 禁止 v3「入盒但挡块零接触」的假机制再次出现。
    assert first_wall_frame is not None, "全程无 cube-backstop 接触"
    hold_wall = wall_forces[-n_hold:]
    assert all(w > CONTACT_EPS_N for w in hold_wall), \
        f"持位段存在未抵墙帧，wall forces tail={hold_wall[:4]}..."
    assert first_wall_frame < n_frames - n_hold, "抵墙起始晚于持位段"
    assert all(math.isfinite(v) for v in wall_forces)

    telemetry = {
        "dt": FRAME_DT,
        "ee_positions": ee_positions,
        "object_poses": object_poses,
        "goal_box": {"center": GOAL_CENTER, "half_extents": GOAL_HALF},
        "penetrations": penetrations,
        "contact_forces": contact_forces,
        "contact_active": contact_active,
        # 额外机制证据字段（telemetry_schema additionalProperties=true）：
        # 每帧子步峰值 cube-backstop 法向力；判定器不读它，仅供机制审计。
        "wall_contact_forces": wall_forces,
        "substeps_per_frame": SUBSTEPS,
        "engine": "mujoco",
        "run_id": args.run_id,
        "ccd": {"swept": False},
        "scenario": "mujoco_native_contact_push",
    }
    tele_path = os.path.join(out_dir, "telemetry.json")
    with open(tele_path, "w", encoding="utf-8") as fh:
        json.dump(telemetry, fh, ensure_ascii=False)

    active_forces = [f for f in force_trace if f > CONTACT_EPS_N]
    manifest = {
        "run_id": args.run_id,
        "scenario": "mujoco_native_contact_push",
        "mujoco_version": mujoco.__version__,
        "numpy_version": np.__version__,
        "python": sys.version.split()[0],
        "frame_dt_s": FRAME_DT,
        "phys_dt_s": PHYS_DT,
        "substeps_per_frame": SUBSTEPS,
        "n_frames": n_frames,
        "first_contact_frame": first_contact_frame,
        "first_wall_contact_frame": first_wall_frame,
        "contact_force_max_n": max(active_forces),
        "contact_force_mean_n": sum(active_forces) / len(active_forces),
        "wall_contact_hold_min_n": min(hold_wall),
        "wall_contact_hold_mean_n": sum(hold_wall) / len(hold_wall),
        "pusher_mass_kg": PUSHER_MASS,
        "max_penetration_m": max(penetrations),
        "object_xyz_end": obj_end,
        "goal_center": GOAL_CENTER,
        "wall_x": WALL_X,
        "friction_coef": FRICTION,
        "pusher_kp": PUSHER_KP,
        "wall_s": round(time.time() - t_wall0, 3),
        "artifacts": {"telemetry": tele_path, "video": video_path,
                      "cover": cover_path},
    }
    with open(os.path.join(out_dir, "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "run_id": args.run_id,
                      "n_frames": n_frames,
                      "first_contact_frame": first_contact_frame,
                      "first_wall_contact_frame": first_wall_frame,
                      "max_penetration_m": round(max(penetrations), 6),
                      "contact_force_mean_n":
                          round(manifest["contact_force_mean_n"], 4),
                      "wall_hold_min_n": round(manifest["wall_contact_hold_min_n"], 4),
                      "object_xyz_end": [round(v, 4) for v in obj_end]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
