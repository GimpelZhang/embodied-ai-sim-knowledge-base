#!/usr/bin/env python3
"""Task8 Track2 Q1：Genesis humanoid 结冰/油污域随机化（DR）对照实验。

计划依据：Phase_1_Plan_detailed.md L561–572（Q1 必做）：
  第一性原理 DR（接触刚度 Kp/阻尼 Kd 非对称对数随机化、摩擦锥极值）；
  N≥3 随机种子 × 两组（正常地面 / 低摩擦+油污参数）；统一 telemetry schema；
  接触力曲线、滑移距离、成功率对照；产物 dr_controls_vs_experimental.csv；
  分屏视频 + 抽帧拼图（≤30s）。L571：物理结果与预期矛盾时禁止调参到
  「好看」为止——outcome 与 mechanism 分开报告，矛盾本身是结论。

三组臂（两组是计划下限；第三组直接服务 kick-off Case A 语义）：
  normal      正常地面：μ=0.7，名义接触参数，无足底扰动，统一标准推力。
  ice_nominal 「硬地策略直入冰面」对照臂（Case A 对照组）：μ=0.05、名义接触
              参数、无 DR，同一反应踏步控制器直入。
  ice_dr      「低摩擦+油污 + DR 包络」实验组（Case A 实验组）：
              μ~LogUniform[0.05,0.4]（摩擦锥极值覆盖），接触 Kp~LogUniform
              [1e4,1e6] N/m 量级、Kd~LogUniform[15,200] s⁻¹ 量级**独立**对数
              采样（非对称：Kp/Kd 不由单一 timeconst 绑定），足底微随机
              wrench（水平面力 + 偏航力矩，模拟油膜不均）。
  策略族三臂共用：世界坐标两杆 IK + capture-point/Raibert 式落足反应踏步
  控制器（开发期在 μ=0.7 以逐位一致性冻结，见 commit body）。本实验不做
  策略学习，DR 是环境鲁棒性包络刻画；不宣称 sim2real 训练收益（outcome 与
  mechanism 分开报告）。

接触参数到 Genesis 7 元组的第一性原理映射（genesis/utils/geom.py:2417
default_solver_params 文档原文）：
  aref = -b·vel - k·imp·pos
  b（阻尼 Kd）= 2 / (dmax·τ)
  k（刚度 Kp）= 1 / (dmax²·τ²·ζ²)
  故独立给定 (Kp,Kd) 反解：τ = 2/(dmax·Kd)，ζ = 1/(dmax·τ·√Kp)。
  名义默认元组 (τ=.01（被 2·substep_dt 下限兜底）, ζ=1, dmin=.9, dmax=.95,
  width=1e-3, mid=.5, power=2) 反推名义 Kd≈210.5 s⁻¹、Kp≈1.11e4 s⁻²。
  锁内适配（Task8，2026-10-15）：
  (1) Genesis 接触摩擦取两 geom 的 max（rigid/collider/contact.py:398，
      下限 1e-2），humanoid.xml default geom friction=.7（L40）使只改地面
      材质的多档 μ 轨迹逐位相同（实测）；build 后对双足全部 geom 同步
      set_friction(μ)，max(μ,μ)=μ。
  (2) 接触 sol 参数按 geom 设置，接触对取两侧混合值——DR 臂对地面 geom 与
      双足 geom 同时下发同一元组，消除混合歧义（set_sol_params 读回实测一致）。
      名义两臂（normal/ice_nominal）**不下发** sol、逐字沿用引擎默认（默认
      τ=0 经 _sanitize_sol_params 兜底为 2·substep_dt=.01，数学等同名义元组）。
      曾经怀疑 build 后 set_sol_params「等价」覆盖会改轨迹，已用门控 A/B 排除：
      名义臂不覆盖后结果不变，sol 非差异源（见 (5) 真根因）。
  (3) 标准化外部水平推力（躯干 +x，35N×0.2s）来自 20/35/50N ×
      μ(.7/.1/.05) 九格标定（sw4，证据由图运行期拷入
      push_window_calibration.json）。标定必须在 (5) 的确定性求解臂口径下
      采集；早期 autotuner 口径网格（sw2/sw3，含当时选定的 20N）只留作
      根因证据，不用于窗口选择。sw4 结果（矛盾原样保留，L571）：
        20N：.7 存活 / .1 zmin 1.073、tilt 30.5° 大幅滑移后恢复 / .05 平稳
             ——非单调，中等 μ 最差，20N 不可用；
        35N：.7 存活（9.88°，滑移 .37/.25），.1 f251、.05 f257 均倾覆
             （峰速 12.6/8.6、16.8/6.9 m/s）——唯一有序可分辨档，选定；
        50N：三档全倒（f231/f212/f224），无对照价值；
        无扰动基线：.7/.1 存活，.05 在 decomposed 臂下末段自溃（f351，
        接触帧 248/264 vs 干地 ~320/300）——「硬地策略直入冰面」即使无
        推力也不稳健，推力把差异在 t≈5.1s 提前并放大。
      注：20N 推力下 .05 存活而无推力 .05 反倒是 f351 自溃（推力改变
      步态相位），跌倒率对扰动的非单调性本身作为机制结论报告。
      种子推力时刻 [3.0, 2.7, 3.3]s：s=0 锚定标定相位（分屏/拼图取 s=0），
      s=1/2 ±0.3s 扫步态相位（确定性，可复现）。
  (4) Genesis 无 entity 级外力 API：经 human._solver.apply_links_external_
      force/torque 下发；外力每物理子步清零，故每子步重复施加。
  (5) **求解器双数值臂非确定性（本任务关键根因，2026-10-15 容器内实证）**：
      Genesis 1.3.3 GPU 刚体求解器有 monolith/decomposed 两条数值不同的求
      解臂，prefer_decomposed_solver 默认 -1 时由**按步计时 autotuner** 在
      仿真运行中挑选（rigid_solver.py:746-754 注释原文："which one runs at
      a given step follows the machine"）。同容器/同 venv/同参数/同种子跨
      进程可得到不同轨迹（μ=.05/20N 一格：一进程 f391 倾覆 zmin=.273，
      另一进程存活 tilt 9.0°，各口径各自跨进程可复现）。已用 2×2 矩阵逐
      项排除：摄像机渲染（网格脚本加 --video 仍 f391）、(2) 的 sol 覆盖
      （门控 A/B 不变）、两脚本循环体差异（机器逐行 diff 等价）、CUDA 用户
      态库漂移（交付容器内 sw3 逐位复现宿主旧网格）。对策：gs.init 显式
      use_deterministic_algorithms=True 钉死 decomposed 臂 + torch 确定性
      （同格跨进程两跑逐位一致已验证）；并固定 GS_ENABLE_ZEROCOPY=0
      ——zerocopy 默认 ON 时 get_contacts 直接触发 int32 gather 缺陷
      （RuntimeError: gather Expected dtype int64 for index），不是性能选项。
      该口径下 20N 的 μ 响应与 autotuner 口径不同（如 μ=.1 出现大幅滑移
      后恢复、μ=.05 反而平稳），非单调按 L571 原样报告，不调参。

两种模式（父进程不 import genesis，避免单进程多 Scene/GPU 状态污染；
每 rollout 独立子进程，genesis.init 每进程一次——确定性求解臂口径下同参数
跨进程逐位复现（rep1==rep2 已验证）；batch 父进程 env 显式固定
GS_ENABLE_ZEROCOPY=0）：
  rollout --params-json P --telemetry T [--video V] [--label L]
  batch   --out-dir D --seeds 3 [--calibration-json C]
产物：telemetry/*.json、videos/*.mp4、dr_controls_vs_experimental.csv、
  plots/{contact_forces,slip_comparison}.png、split_*_s0.mp4（分屏 ≤30s）、
  collage.png（抽帧拼图）、cover.png、summary.json、SUMMARY.md、manifest.json。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import time

# 坐标/物理常量（与开发期冻结的稳定控制器一致，勿随手调）
L1 = 0.40
L2 = 0.39
DT = 0.005
CTRL_HZ = 100.0
TELEM_HZ = 50.0

SCHEMA_VERSION = "simpraxis.task8.track2.telemetry.v1"
ARMS = ("normal", "ice_nominal", "ice_dr")

# 名义接触元组（Genesis 默认；τ=.01 是 substep_dt=0.005 时的下限兜底值）
NOMINAL_SOL = {"tau": 0.01, "zeta": 1.0, "dmin": 0.9, "dmax": 0.95,
               "width": 1e-3, "mid": 0.5, "power": 2.0}
NOMINAL_MU = 0.7
ICE_MU = 0.05
# 标准化推力扰动（确定性求解臂口径九格标定 sw4，见模块 docstring (3)）：
# 35N×.2s 是唯一有序可分辨档——μ=.7 存活（tilt 9.88°），μ=.1/.05 均倾覆
# （f251/f257，峰速 12.6/16.8 m/s）；20N 档非单调（μ=.1 大幅滑移后恢复而
# μ=.05 平稳）、50N 档三档全倒；无扰动 μ=.05 在该臂下亦会末段自溃（f351）。
PUSH_N = 35.0
PUSH_DUR = 0.2
# seed0 锚定九格标定的 3.0s 相位（分屏/拼图均取 s0）；seed1/2 ±0.3s 扫步态相位
PUSH_T_BY_SEED = [3.0, 2.7, 3.3]
# DR 包络（第一性原理，见 docstring）
DR_MU_RANGE = (0.05, 0.4)
DR_KP_RANGE = (1e4, 1e6)
DR_KD_RANGE = (15.0, 200.0)
WRENCH_F_SIGMA = 2.0     # N，水平面
WRENCH_T_SIGMA = 0.2     # Nm，偏航


# --------------------------------------------------------------------------- #
# 参数抽样（纯函数；种子 → 参数完全确定）
# --------------------------------------------------------------------------- #
def _sol_kp_kd(sol: dict) -> tuple[float, float]:
    """Genesis 7 元组 → 等效 (Kp, Kd)，公式见模块 docstring。"""
    kd = 2.0 / (sol["dmax"] * sol["tau"])
    kp = 1.0 / (sol["dmax"] ** 2 * sol["tau"] ** 2 * sol["zeta"] ** 2)
    return kp, kd


def draw_params(arm: str, seed: int) -> dict:
    push = {"n": PUSH_N, "dur": PUSH_DUR, "t": PUSH_T_BY_SEED[seed]}
    gains = {"leg_kp": 1500.0, "leg_kv": 60.0,
             "abdomen_kp": 600.0, "abdomen_kv": 30.0,
             "upper_kp": 300.0, "upper_kv": 20.0}
    if arm == "normal":
        sol = dict(NOMINAL_SOL)
        kp, kd = _sol_kp_kd(sol)
        sol["Kp_eq"], sol["Kd_eq"] = kp, kd
        return {"arm": arm, "seed": seed, "mu": NOMINAL_MU,
                "cone_half_angle_deg": math.degrees(math.atan(NOMINAL_MU)),
                "contact": sol, "override_sol": False,
                "wrench": {"f_sigma": 0.0, "t_sigma": 0.0},
                "push": push, "gains": gains}
    if arm == "ice_nominal":
        sol = dict(NOMINAL_SOL)
        kp, kd = _sol_kp_kd(sol)
        sol["Kp_eq"], sol["Kd_eq"] = kp, kd
        return {"arm": arm, "seed": seed, "mu": ICE_MU,
                "cone_half_angle_deg": math.degrees(math.atan(ICE_MU)),
                "contact": sol, "override_sol": False,
                "wrench": {"f_sigma": 0.0, "t_sigma": 0.0},
                "push": push, "gains": gains}
    if arm == "ice_dr":
        # 独立对数均匀抽样（非对称 DR）；固定大素数偏移避免与 gs seed 同源相关
        rng = np_random(20261015 + seed * 7919)
        mu = math.exp(rng.uniform(math.log(DR_MU_RANGE[0]),
                                  math.log(DR_MU_RANGE[1])))
        kp_d = math.exp(rng.uniform(math.log(DR_KP_RANGE[0]),
                                    math.log(DR_KP_RANGE[1])))
        kd_d = math.exp(rng.uniform(math.log(DR_KD_RANGE[0]),
                                    math.log(DR_KD_RANGE[1])))
        dmax = NOMINAL_SOL["dmax"]
        tau = 2.0 / (dmax * kd_d)
        tau = max(tau, 2.0 * DT + 1e-4)   # Genesis 硬下限 2·substep_dt
        zeta = 1.0 / (dmax * tau * math.sqrt(kp_d))
        if zeta <= 0:
            raise ValueError(f"DR ζ 非正：{zeta}")
        sol = {"tau": tau, "zeta": zeta, "dmin": NOMINAL_SOL["dmin"],
               "dmax": dmax, "width": NOMINAL_SOL["width"],
               "mid": NOMINAL_SOL["mid"], "power": NOMINAL_SOL["power"]}
        kp_eq, kd_eq = _sol_kp_kd(sol)
        return {"arm": arm, "seed": seed, "mu": mu,
                "cone_half_angle_deg": math.degrees(math.atan(mu)),
                "override_sol": True,
                "contact": {**sol, "Kp_eq": kp_eq, "Kd_eq": kd_eq,
                            "Kp_target": kp_d, "Kd_target": kd_d},
                "wrench": {"f_sigma": WRENCH_F_SIGMA,
                           "t_sigma": WRENCH_T_SIGMA},
                "push": push, "gains": gains}
    raise ValueError(f"未知 arm：{arm}")


def np_random(seed):
    import numpy as np
    return np.random.default_rng(seed)


# --------------------------------------------------------------------------- #
# rollout（genesis 在函数内 import，父进程不触碰）
# --------------------------------------------------------------------------- #
def run_rollout(params: dict, telemetry_path: str | None,
                video_path: str | None, label: str, dur_s: float = 8.0,
                cadence_hz: float = 1.0, step_len: float = 0.22,
                step_h: float = 0.07, vdes: float = 0.2,
                t_ds: float = 0.8, theta_des: float = 0.05,
                k_v: float = 0.18, k_th: float = 0.12, k_w: float = 0.02,
                lean_lat: float = 0.14, contact_n: float = 25.0,
                settle: float = 0.5) -> dict:
    os.environ.setdefault("GS_ENABLE_ZEROCOPY", "0")
    import numpy as np
    import genesis as gs
    from genesis.utils import geom as gs_geom

    def np_(t):
        return t.detach().cpu().numpy() if hasattr(t, "detach") else np.asarray(t)

    def leg_ik(x, z, eps=1e-6):
        """矢状面两杆 IK（冻结版，见模块 docstring 坐标约定）。"""
        r = math.sqrt(x * x + z * z)
        r = min(r, L1 + L2 - 0.0001)
        cos_kap = (L1 * L1 + L2 * L2 - r * r) / (2 * L1 * L2)
        kap = math.acos(max(-1.0, min(1.0, cos_kap)))
        beta = math.pi - kap
        delta = math.atan2(x, z)
        gam = math.asin(max(-1.0, min(1.0, L2 * math.sin(beta) / max(r, eps))))
        return delta + gam, beta

    seed = int(params["seed"])
    mu = float(params["mu"])
    sol = params["contact"]
    sol_tuple = np.array([sol["tau"], sol["zeta"], sol["dmin"], sol["dmax"],
                          sol["width"], sol["mid"], sol["power"]], dtype=np.float64)
    wrench = params["wrench"]
    push = params["push"]
    gains = params["gains"]

    # 锁内适配(5)：钉死 decomposed 求解臂，关闭按步计时 autotuner 的跨进程
    # 非确定性（rigid_solver.py:746-754；根因证据见模块 docstring (5)）。
    gs.init(backend=gs.gpu, seed=seed, use_deterministic_algorithms=True)
    scene = gs.Scene(sim_options=gs.options.SimOptions(dt=DT, substeps=1),
                     show_viewer=False,
                     renderer=gs.options.renderers.Rasterizer())
    scene.add_entity(gs.morphs.Plane(),
                     material=gs.materials.Rigid(friction=mu))
    human = scene.add_entity(gs.morphs.MJCF(file="xml/humanoid.xml"))
    cam = scene.add_camera(model="pinhole", res=(640, 480),
                           pos=(1.8, -2.2, 1.25), lookat=(0.6, 0, 0.85),
                           fov=42, GUI=False)
    scene.build()

    n = human.n_dofs

    def ji(name):
        return int(np_(human.get_joint(name).dofs_idx_local).reshape(-1)[0])

    leg = {
        "R": {"hip": ji("hip_y_right"), "knee": ji("knee_right"),
              "ank": ji("ankle_y_right"), "hipx": ji("hip_x_right"),
              "hipz": ji("hip_z_right")},
        "L": {"hip": ji("hip_y_left"), "knee": ji("knee_left"),
              "ank": ji("ankle_y_left"), "hipx": ji("hip_x_left"),
              "hipz": ji("hip_z_left")},
    }
    upper_names = ["abdomen_x", "abdomen_y", "abdomen_z"]
    for side in ("right", "left"):
        upper_names += [f"shoulder1_{side}", f"shoulder2_{side}",
                        f"elbow_{side}"]
    kp = np.zeros(n)
    kv = np.zeros(n)
    for d in [d for s in leg.values() for d in s.values()]:
        kp[d] = gains["leg_kp"]
        kv[d] = gains["leg_kv"]
    for nm in upper_names:
        try:
            d = ji(nm)
        except Exception:
            continue
        if nm.startswith("abdomen"):
            kp[d] = gains["abdomen_kp"]
            kv[d] = gains["abdomen_kv"]
        else:
            kp[d] = gains["upper_kp"]
            kv[d] = gains["upper_kv"]
    human.set_dofs_kp(kp)
    human.set_dofs_kv(kv)
    q0 = np.asarray(np_(human.get_dofs_position())).reshape(-1).copy()

    torso = human.get_link("torso")
    thigh = {"R": human.get_link("thigh_right"),
             "L": human.get_link("thigh_left")}
    foot = {"R": human.get_link("foot_right"),
            "L": human.get_link("foot_left")}
    ground = scene.entities[0]

    # 锁内适配(1)：双侧摩擦 max-combine → 双足 geom 同步压到 μ（三臂都下发）。
    # 锁内适配(2)：接触 sol 7 元组仅 DR 臂覆盖（地面 + 双足 geom 同值消歧）；
    # 名义两臂逐字沿用引擎默认，与九格标定逐位可比（见模块 docstring(2)）。
    if params.get("override_sol", False):
        for g in list(ground.geoms):
            g.set_sol_params(sol_tuple)
    for s in ("R", "L"):
        foot[s].set_friction(mu)
        if params.get("override_sol", False):
            for g in foot[s].geoms:
                g.set_sol_params(sol_tuple)

    writer = None
    if video_path:
        import imageio.v2 as imageio
        writer = imageio.get_writer(
            video_path, fps=int(TELEM_HZ), codec="libx264", quality=8,
            macro_block_size=None,
            output_params=["-pix_fmt", "yuv420p", "-crf", "28"])

    ctrl_every = max(1, int(round((1 / CTRL_HZ) / DT)))
    n_steps = int(dur_s / DT)
    frame_every = max(1, int(round((1 / TELEM_HZ) / DT)))

    for _ in range(int(settle / DT)):
        human.control_dofs_position(q0)
        scene.step()

    def wpos(lk):
        return np.asarray(np_(lk.get_pos())).reshape(3)

    planted = {s: wpos(foot[s]).copy() for s in ("R", "L")}
    fstate = {"R": "stance", "L": "stance"}
    next_plant = {"R": None, "L": None}
    swing_t0 = {"R": 0.0, "L": 0.0}
    abd_x = ji("abdomen_x")
    theta_prev = None
    theta_dot = 0.0
    foot_idx = {s: int(np_(lk.idx).reshape(-1)[0])
                for s, lk in foot.items()}
    torso_idx = int(np_(torso.idx).reshape(-1)[0])
    link_idx_all = {s: int(np_(foot[s].idx).reshape(-1)[0])
                    for s in ("R", "L")}
    # 足底 wrench 噪声独立 RNG（与参数抽样、gs seed 分开记录）
    wrench_rng = np.random.default_rng(np.uint64(9901 + seed * 131
                                                 + ARMS.index(params["arm"]) * 7717))

    def contact_rows(ci):
        fr = np.asarray(np_(ci["force_a"])).reshape(-1, 3) \
            if "force_a" in ci else np.zeros((0, 3))
        la = np.asarray(np_(ci["link_a"])).reshape(-1) \
            if "link_a" in ci else np.zeros(0, int)
        lb = np.asarray(np_(ci["link_b"])).reshape(-1) \
            if "link_b" in ci else np.zeros(0, int)
        return fr, la, lb

    def foot_forces_now():
        ci = human.get_contacts(with_entity=ground)
        fr, la, lb = contact_rows(ci)
        ff = {"R": 0.0, "L": 0.0}
        for s in ("R", "L"):
            fid = foot_idx[s]
            rows = [k for k in range(fr.shape[0])
                    if fid in (int(la[k]) if k < len(la) else -1,
                               int(lb[k]) if k < len(lb) else -1)]
            if rows:
                ff[s] = float(np.linalg.norm(fr[rows].sum(axis=0)))
        return ff

    series_t, z_tr, x_tr, tilt_l, vx_l = [], [], [], [], []
    foot_force = {"R": [], "L": []}
    foot_slip = {"R": [], "L": []}
    slip_dist = {"R": 0.0, "L": 0.0}
    contact_frames = {"R": 0, "L": 0}
    fall_frame = None
    slip_vmax_window = {"R": 0.0, "L": 0.0}
    t0 = time.time()

    for step_i in range(n_steps):
        t = step_i * DT
        pos_t = np.asarray(np_(torso.get_pos())).reshape(3)
        quat = np.asarray(np_(torso.get_quat())).reshape(4)
        Rm = np.asarray(gs_geom.quat_to_R(quat)).reshape(3, 3)
        theta = math.atan2(Rm[0, 2], Rm[2, 2])
        vx = float(np.asarray(np_(torso.get_vel())).reshape(3)[0])

        target = q0.copy()
        if step_i % ctrl_every == 0:
            cyc = step_i // ctrl_every
            ctrl_dt = ctrl_every * DT
            if theta_prev is not None:
                w_raw = (theta - theta_prev) / ctrl_dt
                theta_dot = 0.7 * theta_dot + 0.3 * w_raw
            theta_prev = theta
            teff = max(0.0, t - t_ds)
            ph = 2 * math.pi * cadence_hz * teff
            fnow = foot_forces_now()
            stance_sides = []
            for s in ("R", "L"):
                p = (ph + (0.0 if s == "R" else math.pi)) % (2 * math.pi)
                want_swing = p >= math.pi
                hip_w = np.asarray(np_(thigh[s].get_pos())).reshape(3)
                if fstate[s] == "stance" and want_swing:
                    fstate[s] = "swing"
                    swing_t0[s] = t
                    t_sw = 0.5 / cadence_hz
                    x_pred = pos_t[0] + vx * t_sw
                    x_plant = (x_pred + 0.5 * step_len
                               + k_v * (vx - vdes)
                               + k_th * (theta - theta_des)
                               + k_w * theta_dot)
                    next_plant[s] = np.array([x_plant, float(hip_w[1]),
                                              planted[s][2]])
                if fstate[s] == "swing":
                    u = (t - swing_t0[s]) / (0.5 / cadence_hz)
                    landed = (u >= 0.55 and fnow[s] > contact_n) or u >= 1.0
                    if landed:
                        planted[s] = wpos(foot[s]).copy()
                        next_plant[s] = None
                        fstate[s] = "stance"
                        tgt_w = planted[s].copy()
                    else:
                        u = min(max(u, 0.0), 1.0)
                        sp = planted[s]
                        tgt_w = sp.copy()
                        s_ = 3 * u * u - 2 * u * u * u
                        tgt_w[0] += (next_plant[s][0] - sp[0]) * s_
                        tgt_w[1] = next_plant[s][1]
                        tgt_w[2] = next_plant[s][2] - step_h * math.sin(math.pi * u)
                else:
                    stance_sides.append(s)
                    tgt_w = planted[s].copy()
                dx = float(tgt_w[0] - hip_w[0])
                dz = float(hip_w[2] - tgt_w[2])
                gamma, beta = leg_ik(dx, dz)
                alpha = gamma - theta
                target[leg[s]["hip"]] = q0[leg[s]["hip"]] - alpha
                target[leg[s]["knee"]] = q0[leg[s]["knee"]] - beta
                target[leg[s]["ank"]] = q0[leg[s]["ank"]] + (theta + alpha - beta)
            if len(stance_sides) == 1:
                s0 = stance_sides[0]
                target[abd_x] = q0[abd_x] + lean_lat * (1.0 if s0 == "R" else -1.0)
            human.control_dofs_position(target)

        # 锁内适配(4)：外部力每子步清零，必须在 scene.step() 前每子步重发。
        # 标准化躯干水平推力（+x）。
        if push["n"] > 0.0 and push["t"] <= t < push["t"] + push["dur"]:
            human._solver.apply_links_external_force(
                force=np.array([[push["n"], 0.0, 0.0]]),
                links_idx=np.array([torso_idx]))
        # 油污微随机 wrench：双足水平面力 + 偏航力矩（油膜不均的近似；
        # 近似口径写进 SUMMARY/telemetry，判定器不据此放宽阈值）。
        if wrench["f_sigma"] > 0.0 or wrench["t_sigma"] > 0.0:
            for s in ("R", "L"):
                if wrench["f_sigma"] > 0.0:
                    human._solver.apply_links_external_force(
                        force=np.array([[
                            wrench_rng.normal(0.0, wrench["f_sigma"]),
                            wrench_rng.normal(0.0, wrench["f_sigma"]),
                            0.0]]),
                        links_idx=np.array([link_idx_all[s]]))
                if wrench["t_sigma"] > 0.0:
                    human._solver.apply_links_external_torque(
                        torque=np.array([[0.0, 0.0,
                                          wrench_rng.normal(0.0, wrench["t_sigma"])]]),
                        links_idx=np.array([link_idx_all[s]]))
        scene.step()

        if step_i % frame_every == 0:
            if writer is not None:
                out = cam.render(rgb=True)
                rgb = np.asarray(np_(out[0]))
                if rgb.ndim == 4:
                    rgb = rgb[0]
                writer.append_data(rgb[..., :3].astype(np.uint8))
            z_tr.append(float(pos_t[2]))
            x_tr.append(float(pos_t[0]))
            series_t.append(round(t, 4))
            tilt = math.degrees(math.acos(max(-1, min(1, Rm[2, 2]))))
            tilt_l.append(tilt)
            vx_l.append(vx)
            ci = human.get_contacts(with_entity=ground)
            forces, la, lb = contact_rows(ci)
            in_window = (push["t"] <= t < push["t"] + 2.5)
            for s in ("R", "L"):
                fid = foot_idx[s]
                rows = [k for k in range(forces.shape[0])
                        if fid in (int(la[k]) if k < len(la) else -1,
                                   int(lb[k]) if k < len(lb) else -1)]
                fmag = float(np.linalg.norm(forces[rows].sum(axis=0))) if rows else 0.0
                fv = np.asarray(np_(foot[s].get_vel())).reshape(3)
                vxy = float(np.linalg.norm(fv[:2]))
                foot_force[s].append(fmag)
                foot_slip[s].append(vxy)
                if fmag > 2.0:
                    contact_frames[s] += 1
                    slip_dist[s] += vxy * (1.0 / TELEM_HZ)
                if in_window:
                    slip_vmax_window[s] = max(slip_vmax_window[s], vxy)
            if fall_frame is None and (pos_t[2] < 0.85 or tilt > 50.0):
                fall_frame = len(z_tr) - 1

    if writer is not None:
        writer.close()

    fell = fall_frame is not None
    telemetry = {
        "schema": SCHEMA_VERSION,
        "label": label,
        "engine": "genesis",
        "engine_version": "1.3.3",
        "params": params,
        "sim": {"dt": DT, "ctrl_hz": CTRL_HZ, "telem_hz": TELEM_HZ,
                "dur_s": dur_s, "frames": len(z_tr),
                "gs_enable_zerocopy": False,
                # 锁内适配(5)：True=decomposed 臂钉死，无 autotuner 非确定性
                "use_deterministic_algorithms": True},
        "series": {
            "t": series_t,
            "torso_z": [round(v, 4) for v in z_tr],
            "torso_x": [round(v, 4) for v in x_tr],
            "tilt_deg": [round(v, 3) for v in tilt_l],
            "vx": [round(v, 4) for v in vx_l],
            "contact_force_R": [round(v, 2) for v in foot_force["R"]],
            "contact_force_L": [round(v, 2) for v in foot_force["L"]],
            "slip_v_R": [round(v, 4) for v in foot_slip["R"]],
            "slip_v_L": [round(v, 4) for v in foot_slip["L"]],
        },
        "outcomes": {
            "success": not fell,
            "fell": fell,
            "fall_frame": fall_frame,
            "fall_time_s": (None if fall_frame is None
                            else round(fall_frame / TELEM_HZ, 3)),
            "torso_z_min": round(min(z_tr), 4),
            "torso_z_last": round(z_tr[-1], 4),
            "torso_x_last": round(x_tr[-1], 4),
            "tilt_max_deg": round(max(tilt_l), 2),
            "vx_mean_tail": round(float(np.mean(vx_l[len(vx_l) // 4:])), 3),
            "slip_dist_m": {s: round(slip_dist[s], 4) for s in slip_dist},
            "slip_v_max_mps": {s: round(max(foot_slip[s]), 3) for s in foot_slip},
            "slip_v_max_postpush_mps": {s: round(slip_vmax_window[s], 3)
                                        for s in slip_vmax_window},
            "contact_force_peak_N": {s: round(max(foot_force[s]), 2)
                                     for s in foot_force},
            "contact_frames": contact_frames,
            "sim_wall_s": round(time.time() - t0, 2),
        },
        "video_relpath": (os.path.basename(video_path) if video_path else None),
    }
    if telemetry_path:
        os.makedirs(os.path.dirname(os.path.abspath(telemetry_path)), exist_ok=True)
        with open(telemetry_path, "w") as f:
            json.dump(telemetry, f, indent=1)
    print(json.dumps({"label": label, "mu": round(mu, 4),
                      "fell": fell, "fall_frame": fall_frame,
                      "slip_v_max": telemetry["outcomes"]["slip_v_max_mps"],
                      "slip_dist": telemetry["outcomes"]["slip_dist_m"]},
                     ensure_ascii=False))
    return telemetry


# --------------------------------------------------------------------------- #
# batch 聚合（父进程；不 import genesis/torch）
# --------------------------------------------------------------------------- #
CSV_FIELDS = [
    "run_id", "arm", "seed", "mu", "cone_half_angle_deg",
    "contact_Kp_eq", "contact_Kd_eq", "contact_tau", "contact_zeta",
    "contact_Kp_target", "contact_Kd_target",
    "wrench_f_sigma", "wrench_t_sigma",
    "push_n", "push_t", "push_dur",
    "success", "fell", "fall_frame", "fall_time_s",
    "torso_z_min", "tilt_max_deg", "vx_mean_tail",
    "slip_dist_R_m", "slip_dist_L_m",
    "slip_vmax_R_mps", "slip_vmax_L_mps",
    "slip_vmax_postpush_R_mps", "slip_vmax_postpush_L_mps",
    "force_peak_R_N", "force_peak_L_N",
    "contact_frames_R", "contact_frames_L",
    "sim_wall_s", "video_relpath",
]


def _flatten(run_id: str, p: dict, o: dict) -> dict:
    return {
        "run_id": run_id, "arm": p["arm"], "seed": p["seed"],
        "mu": round(p["mu"], 6),
        "cone_half_angle_deg": round(p["cone_half_angle_deg"], 3),
        "contact_Kp_eq": round(p["contact"]["Kp_eq"], 2),
        "contact_Kd_eq": round(p["contact"]["Kd_eq"], 3),
        "contact_tau": round(p["contact"]["tau"], 6),
        "contact_zeta": round(p["contact"]["zeta"], 6),
        "contact_Kp_target": round(p["contact"].get("Kp_target",
                                                    p["contact"]["Kp_eq"]), 2),
        "contact_Kd_target": round(p["contact"].get("Kd_target",
                                                    p["contact"]["Kd_eq"]), 3),
        "wrench_f_sigma": p["wrench"]["f_sigma"],
        "wrench_t_sigma": p["wrench"]["t_sigma"],
        "push_n": p["push"]["n"], "push_t": p["push"]["t"],
        "push_dur": p["push"]["dur"],
        "success": int(o["success"]), "fell": int(o["fell"]),
        "fall_frame": o["fall_frame"] if o["fall_frame"] is not None else "",
        "fall_time_s": o["fall_time_s"] if o["fall_time_s"] is not None else "",
        "torso_z_min": o["torso_z_min"], "tilt_max_deg": o["tilt_max_deg"],
        "vx_mean_tail": o["vx_mean_tail"],
        "slip_dist_R_m": o["slip_dist_m"]["R"],
        "slip_dist_L_m": o["slip_dist_m"]["L"],
        "slip_vmax_R_mps": o["slip_v_max_mps"]["R"],
        "slip_vmax_L_mps": o["slip_v_max_mps"]["L"],
        "slip_vmax_postpush_R_mps": o["slip_v_max_postpush_mps"]["R"],
        "slip_vmax_postpush_L_mps": o["slip_v_max_postpush_mps"]["L"],
        "force_peak_R_N": o["contact_force_peak_N"]["R"],
        "force_peak_L_N": o["contact_force_peak_N"]["L"],
        "contact_frames_R": o["contact_frames"]["R"],
        "contact_frames_L": o["contact_frames"]["L"],
        "sim_wall_s": o["sim_wall_s"],
        "video_relpath": "videos/" + os.path.basename(video_name(run_id)),
    }


def video_name(run_id: str) -> str:
    return f"{run_id}.mp4"


def run_batch(out_dir: str, seeds: int, calibration_json: str | None,
              dur_s: float) -> dict:
    import shutil
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw

    os.makedirs(os.path.join(out_dir, "telemetry"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "videos"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "plots"), exist_ok=True)
    if calibration_json and os.path.isfile(calibration_json):
        dst_cal = os.path.join(out_dir, "push_window_calibration.json")
        # 源文件可能就位于 out_dir 内（如 --calibration-json 指向 out_dir 下的
        # push_window_calibration.json），copyfile 会抛 SameFileError；
        # 用 samefile 判定同一文件时跳过拷贝。
        if not (os.path.exists(dst_cal)
                and os.path.samefile(calibration_json, dst_cal)):
            shutil.copyfile(calibration_json, dst_cal)

    # 1) 逐 rollout 子进程（顺序执行，单卡）
    rows = []
    telemetries = {}
    for arm in ARMS:
        for seed in range(seeds):
            run_id = f"{arm}_s{seed}"
            p = draw_params(arm, seed)
            p_path = os.path.join(out_dir, "telemetry", f"{run_id}.params.json")
            t_path = os.path.join(out_dir, "telemetry", f"{run_id}.json")
            v_path = os.path.join(out_dir, "videos", video_name(run_id))
            with open(p_path, "w") as f:
                json.dump(p, f, indent=1)
            cmd = [sys.executable, os.path.abspath(__file__), "rollout",
                   "--params-json", p_path, "--telemetry", t_path,
                   "--video", v_path, "--label", run_id,
                   "--dur-s", str(dur_s)]
            env = dict(os.environ)
            env["GS_ENABLE_ZEROCOPY"] = "0"
            env.setdefault("HOME", "/mnt/caches/home")
            print(f"[batch] === {run_id} μ={p['mu']:.4f} ===", flush=True)
            pr = subprocess.run(cmd, env=env)
            if pr.returncode != 0:
                raise RuntimeError(f"rollout 子进程失败：{run_id} rc={pr.returncode}")
            with open(t_path) as f:
                tel = json.load(f)
            telemetries[run_id] = tel
            rows.append(_flatten(run_id, p, tel["outcomes"]))

    # 2) CSV（计划点名产物）
    csv_path = os.path.join(out_dir, "dr_controls_vs_experimental.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)

    # 3) 接触力曲线（每臂 seed0；推力窗口灰带）
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    for ax, arm in zip(axes, ARMS):
        tel = telemetries[f"{arm}_s0"]
        t = tel["series"]["t"]
        ax.plot(t, tel["series"]["contact_force_R"], label="R", lw=1.2)
        ax.plot(t, tel["series"]["contact_force_L"], label="L", lw=1.2)
        pb = tel["params"]["push"]
        ax.axvspan(pb["t"], pb["t"] + pb["dur"], color="grey", alpha=0.25,
                   label="push")
        ax.set_ylabel(f"{arm}\nforce N")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("t (s)")
    fig.suptitle("Foot contact force (seed 0)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "plots", "contact_forces.png"), dpi=130)
    plt.close(fig)

    # 4) 滑移对照（峰速 / 滑移距离，跨种子均值+极差）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    metrics = [("slip_vmax_postpush_R_mps", "slip_vmax_postpush_L_mps",
                "peak slip speed post-push (m/s)"),
               ("slip_dist_R_m", "slip_dist_L_m",
                "slip distance (m)")]
    for ax, (kr, kl, title) in zip((ax1, ax2), metrics):
        means, los, his = [], [], []
        for arm in ARMS:
            per_seed = []
            for seed in range(seeds):
                r = next(x for x in rows if x["run_id"] == f"{arm}_s{seed}")
                per_seed.append(max(float(r[kr]), float(r[kl])))
            m = sum(per_seed) / len(per_seed)
            means.append(m)
            los.append(m - min(per_seed))
            his.append(max(per_seed) - m)
        ax.bar(ARMS, means, yerr=[los, his], capsize=6,
               color=["#4C72B0", "#C44E52", "#55A868"])
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "plots", "slip_comparison.png"), dpi=130)
    plt.close(fig)

    # 5) 组分汇总（outcome 与 mechanism 分列）
    summary = {"schema": SCHEMA_VERSION, "seeds": seeds,
               "disturbance": {"push_n": PUSH_N, "push_dur_s": PUSH_DUR,
                               "push_t_by_seed": PUSH_T_BY_SEED[:seeds]},
               "dr_envelope": {"mu_loguniform": DR_MU_RANGE,
                               "Kp_loguniform": DR_KP_RANGE,
                               "Kd_loguniform": DR_KD_RANGE,
                               "wrench": {"f_sigma_n": WRENCH_F_SIGMA,
                                          "t_sigma_nm": WRENCH_T_SIGMA}},
               "groups": {}}
    for arm in ARMS:
        rs = [x for x in rows if x["run_id"].startswith(arm + "_s")]
        n = len(rs)
        succ = sum(int(x["success"]) for x in rs)
        summary["groups"][arm] = {
            "n": n,
            "success_rate": succ / n,
            "n_fell": n - succ,
            "fall_frames": [x["fall_frame"] for x in rs],
            "mu_per_seed": [x["mu"] for x in rs],
            "slip_dist_m_mean": [
                round(sum(float(x[f"slip_dist_{s}_m"]) for x in rs) / n, 4)
                for s in ("R", "L")],
            "slip_vmax_postpush_mps_max": [
                round(max(max(float(x[f"slip_vmax_postpush_{s}_mps"]) for x in rs)
                          for s in ("R", "L")), 3)],
            "tilt_max_deg_max": round(max(float(x["tilt_max_deg"]) for x in rs), 2),
        }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)

    # 6) 分屏视频（ffmpeg hstack；每段 8s ≪ 30s 上限）
    def hstack(a: str, b: str, out_name: str):
        pa = os.path.join(out_dir, "videos", video_name(a))
        pb = os.path.join(out_dir, "videos", video_name(b))
        po = os.path.join(out_dir, out_name)
        cmd = ["ffmpeg", "-y", "-i", pa, "-i", pb,
               "-filter_complex", "hstack=inputs=2",
               "-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
               po]
        pr = subprocess.run(cmd, capture_output=True, text=True)
        if pr.returncode != 0:
            raise RuntimeError(f"ffmpeg hstack 失败 {out_name}:\n{pr.stderr[-2000:]}")

    hstack("normal_s0", "ice_nominal_s0",
           "split_normal_vs_ice_nominal_s0.mp4")
    hstack("ice_nominal_s0", "ice_dr_s0",
           "split_ice_nominal_vs_ice_dr_s0.mp4")

    # 7) 抽帧拼图（3 臂 × 6 帧，PIL 标注 arm/μ/结果）
    reps = ["normal_s0", "ice_nominal_s0", "ice_dr_s0"]
    ncol = 6
    frames = {}
    for rid in reps:
        reader = imageio.get_reader(os.path.join(out_dir, "videos",
                                                 video_name(rid)))
        seq = reader.count_frames()
        idx = [int(round(k * (seq - 1) / (ncol - 1))) for k in range(ncol)]
        frames[rid] = [reader.get_data(i) for i in idx]
        reader.close()
    h0, w0 = frames[reps[0]][0].shape[:2]
    label_h = 36
    sheet = Image.new("RGB", (w0 * ncol, (h0 + label_h) * len(reps)),
                      (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for r, rid in enumerate(reps):
        tel = telemetries[rid]
        o = tel["outcomes"]
        txt = (f"{rid}  mu={tel['params']['mu']:.3f}  "
               f"{'FELL@' + str(o['fall_time_s']) + 's' if o['fell'] else 'STOOD'}  "
               f"slip_peak={max(o['slip_v_max_mps']['R'], o['slip_v_max_mps']['L']):.2f}m/s")
        draw.text((8, r * (h0 + label_h) + 8), txt, fill=(0, 0, 0))
        for c, img in enumerate(frames[rid]):
            im = Image.fromarray(img[..., :3])
            sheet.paste(im, (c * w0, r * (h0 + label_h) + label_h))
    sheet.save(os.path.join(out_dir, "collage.png"))
    sheet.resize((w0 * ncol // 2, (h0 + label_h) * len(reps) // 2)) \
        .save(os.path.join(out_dir, "cover.png"))

    # 8) SUMMARY.md（outcome / mechanism 分离）
    g = summary["groups"]
    md = [
        "# Task8 Track2 Q1 — Genesis 结冰/油污 DR 对照（seed0 摘要见分屏）",
        "",
        f"- 随机种子数：{seeds}；标准化扰动：躯干 +x {PUSH_N}N×{PUSH_DUR}s，"
        f"时刻按种子扫相位 {summary['disturbance']['push_t_by_seed']}s",
        "- 策略族三臂共用同一反应踏步控制器（无策略学习；DR 为环境鲁棒性包络）。",
        "",
        "## Outcome（成功率/倾覆，不修饰矛盾）",
        "",
        "| arm | μ/种子 | 成功率 | 倾覆帧 | 最大倾角° |",
        "|---|---|---|---|---|",
    ]
    for arm in ARMS:
        gg = g[arm]
        md.append(
            f"| {arm} | {[round(x, 3) for x in gg['mu_per_seed']]} | "
            f"{gg['success_rate']:.2f} ({int(gg['success_rate'] * gg['n'])}/{gg['n']}) | "
            f"{gg['fall_frames']} | {gg['tilt_max_deg_max']} |")
    md += [
        "",
        "## Mechanism（滑移/接触力，独立于成败）",
        "",
        "| arm | 滑移距离均值 m (R,L) | 推力后峰速 max m/s |",
        "|---|---|---|",
    ]
    for arm in ARMS:
        gg = g[arm]
        md.append(f"| {arm} | {gg['slip_dist_m_mean']} | "
                  f"{gg['slip_vmax_postpush_mps_max']} |")
    md += [
        "",
        "接触力曲线见 plots/contact_forces.png，滑移对照见 "
        "plots/slip_comparison.png；分屏 split_*_s0.mp4；拼图 collage.png。",
        "",
        "## 口径声明",
        "- μ 经双足 geom 双侧 set_friction 真实下发（max-combine 修复，"
        "contact.py:398）；接触刚度/阻尼经 set_sol_params 7 元组反解下发，"
        "地面+双足同侧一致避免混合歧义。",
        "- 油污 wrench 为足底水平面高斯力+偏航力矩的近似（每物理子步施加），"
        "不是油膜流体模型；近似口径不参与成功判定。",
        "- 若成功率随 μ/DR 非单调，按计划 L571 原样报告：矛盾本身是结论。",
        "",
    ]
    with open(os.path.join(out_dir, "SUMMARY.md"), "w") as f:
        f.write("\n".join(md))

    # 9) manifest
    manifest = {
        "schema": SCHEMA_VERSION,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runs": [f"{arm}_s{s}" for arm in ARMS for s in range(seeds)],
        "artifacts": ["dr_controls_vs_experimental.csv", "summary.json",
                      "SUMMARY.md", "collage.png", "cover.png",
                      "plots/contact_forces.png", "plots/slip_comparison.png",
                      "split_normal_vs_ice_nominal_s0.mp4",
                      "split_ice_nominal_vs_ice_dr_s0.mp4"],
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("[batch] DONE", csv_path)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rollout")
    r.add_argument("--params-json", required=True)
    r.add_argument("--telemetry", default=None)
    r.add_argument("--video", default=None)
    r.add_argument("--label", default="")
    r.add_argument("--dur-s", type=float, default=8.0)
    b = sub.add_parser("batch")
    b.add_argument("--out-dir", required=True)
    b.add_argument("--seeds", type=int, default=3)
    b.add_argument("--dur-s", type=float, default=8.0)
    b.add_argument("--calibration-json", default=None)
    args = ap.parse_args(argv)

    if args.cmd == "rollout":
        with open(args.params_json) as f:
            params = json.load(f)
        # humanoid.xml 相对路径：切到 genesis assets，消除 cwd 依赖
        import genesis as gs  # noqa: F40  （仅为定位包路径，不 init）
        assets = os.path.join(os.path.dirname(gs.__file__), "assets")
        os.chdir(assets)
        run_rollout(params, args.telemetry, args.video, args.label,
                    dur_s=args.dur_s)
        return 0

    if args.cmd == "batch":
        run_batch(args.out_dir, args.seeds, args.calibration_json, args.dur_s)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
