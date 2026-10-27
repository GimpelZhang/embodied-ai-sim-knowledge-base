#!/usr/bin/env python3
import os
import sys
import re
import json
import math
import argparse
import traceback
import resource

resource.setrlimit(resource.RLIMIT_NOFILE,
                   (65535, resource.getrlimit(resource.RLIMIT_NOFILE)[1]))

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np
import mujoco
import imageio

from libero.libero.benchmark import get_benchmark
from libero.libero.envs import OffScreenRenderEnv

GOAL_RE = re.compile(r"\((On|Inside)\s+([A-Za-z0-9_\-]+)\s+([A-Za-z0-9_\-]+)\)")
OBJINT_RE = re.compile(r"\(:obj_of_interest\s+([^)]*)\)")

FPS = 20
FRAME_DT = 1.0 / FPS
HORIZON = 2500


def parse_goal(bddl_path):
    with open(bddl_path, "r") as f:
        txt = f.read()
    m = GOAL_RE.search(txt)
    if m:
        return m.group(2), m.group(3)
    mo = OBJINT_RE.search(txt)
    if mo:
        names = mo.group(1).split()
        if len(names) >= 2:
            return names[0], names[1]
    return None, None


def body_extent(env, obj_name):
    m = env.sim.model._model
    bid = None
    for n in (obj_name + "_main", obj_name):
        try:
            b = m.body_name2id(n)
            if b is not None and b >= 0:
                bid = b
                break
        except Exception:
            pass
    if bid is None:
        return 0.05, 0.88, 0.95
    base = np.array(m.body_pos[bid], dtype=np.float64)
    rad = 0.0
    zmin, zmax = 1e9, -1e9
    gids = np.where(m.geom_bodyid == bid)[0]
    for gid in gids:
        gt = int(m.geom_type[gid])
        wp = base + np.array(m.geom_pos[gid], dtype=np.float64)
        sz = np.array(m.geom_size[gid], dtype=np.float64)
        if gt == int(mujoco.mjtGeom.mjGEOM_SPHERE):
            r = float(sz[0])
            h = r
        elif gt in (int(mujoco.mjtGeom.mjGEOM_CYLINDER),
                    int(mujoco.mjtGeom.mjGEOM_CAPSULE)):
            r = float(sz[0])
            h = float(sz[1])
        elif gt == int(mujoco.mjtGeom.mjGEOM_BOX):
            r = float(math.hypot(sz[0], sz[1]))
            h = float(sz[2])
        else:
            r = 0.03
            h = 0.03
        rad = max(rad, float(math.hypot(wp[0] - base[0], wp[1] - base[1])) + r)
        zmin = min(zmin, float(wp[2]) - h)
        zmax = max(zmax, float(wp[2]) + h)
    return float(rad), float(zmin), float(zmax)


def eef_yaw(quat):
    w, x, y, z = [float(v) for v in quat]
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def axis_err(yaw, target_ang):
    ang = yaw + math.pi / 2.0
    return (ang - target_ang + math.pi / 2.0) % math.pi - math.pi / 2.0


def servo(target, eef, yaw_err=None, gripper=-1.0, gain=0.5, maxd=0.05):
    a = np.zeros(7, dtype=np.float64)
    tgt = np.asarray(target, dtype=np.float64)
    ee = np.asarray(eef, dtype=np.float64)
    delta = np.clip(gain * (tgt - ee), -maxd, maxd)
    a[:3] = delta / maxd
    if yaw_err is not None:
        a[5] = float(np.clip(-2.0 * yaw_err, -0.5, 0.5))
    a[6] = float(gripper)
    return a


def hold(yaw_err=None, gripper=-1.0):
    a = np.zeros(7, dtype=np.float64)
    if yaw_err is not None:
        a[5] = float(np.clip(-2.0 * yaw_err, -0.5, 0.5))
    a[6] = float(gripper)
    return a


def sim_step(env, action, writer, counter, last_img):
    obs, reward, done, info = env.step(action)
    img = obs.get("agentview_image")
    if img is not None:
        arr = np.asarray(img)
        last_img[0] = arr
        if writer is not None:
            writer.append_data(arr)
            counter[0] += 1
    return obs, bool(done)


def object_names(obs):
    out = []
    for k in obs.keys():
        if not k.endswith("_pos"):
            continue
        name = k[:-4]
        if "robot" in name or "_to_" in name:
            continue
        out.append(name)
    return out


def pick_offset_angle(obs, grasp_obj, rad):
    gpos = np.asarray(obs[grasp_obj + "_pos"], dtype=np.float64)
    others = []
    for name in object_names(obs):
        if name == grasp_obj:
            continue
        p = obs.get(name + "_pos")
        if p is None:
            continue
        others.append(np.asarray(p, dtype=np.float64)[:2])
    best_ang = 0.0
    best_clear = -1e9
    for ang in np.linspace(0.0, 2.0 * math.pi, 24, endpoint=False):
        gx = gpos[0] + rad * math.cos(ang)
        gy = gpos[1] + rad * math.sin(ang)
        dmin = 1e9
        for op in others:
            d = math.hypot(gx - op[0], gy - op[1])
            if d < dmin:
                dmin = d
        if dmin > best_clear:
            best_clear = dmin
            best_ang = float(ang)
    return best_ang


def run_episode(env, init_state, grasp_obj, place_obj, writer, counter, last_img):
    import math
    import os
    import re
    import numpy as np

    # ------------------------------------------------------------------
    # 单一控制循环纪律：本函数是本局唯一的 env.step 驱动者；
    # 所有动作都经 step_a -> sim_step(env, action7, ...)，目标驱动 servo 闭环。
    # ------------------------------------------------------------------
    def clip_a(a):
        return np.clip(np.asarray(a, dtype=np.float64).reshape(-1), -1.0, 1.0)

    def step_a(a):
        obs, _ = sim_step(env, clip_a(a), writer, counter, last_img)
        return obs

    def zeros_a(gripper=-1.0):
        a = np.zeros(7, dtype=np.float64)
        a[6] = float(gripper)
        return a

    def pos_of(obs, name):
        k = name + "_pos"
        if obs is not None and hasattr(obs, "keys") and k in obs:
            return np.asarray(obs[k], dtype=np.float64)
        return None

    def eef_of(obs):
        return np.asarray(obs["robot0_eef_pos"], dtype=np.float64)

    def scene_objs(obs):
        out = []
        for k in obs.keys():
            if not k.endswith("_pos"):
                continue
            n = k[:-4]
            if n.startswith("robot0") or "_to_" in n:
                continue
            if ("region" in n) or ("table" in n):
                continue
            out.append(n)
        return sorted(set(out))

    # 官方 goal 解析（case-sensitive 大写谓词）；bddl 路径取自 env 自身属性
    def parse_goal_names():
        bddl = getattr(env, "bddl_file_name", None)
        if not bddl or not os.path.isfile(bddl):
            return None
        try:
            with open(bddl, "r") as fh:
                txt = fh.read()
        except Exception:
            return None
        m = re.search(r"\((On|Inside)\s+([A-Za-z0-9_\-]+)\s+([A-Za-z0-9_\-]+)\)", txt)
        if not m:
            return None
        return m.group(2), m.group(3)

    def resolve_names(obs):
        g, p = grasp_obj, place_obj
        parsed = parse_goal_names()
        if parsed is not None:
            g2, p2 = parsed
            if pos_of(obs, g2) is not None:
                g = g2
            p = p2
        if pos_of(obs, g) is None:
            objs = [o for o in scene_objs(obs) if o != p]
            if not objs:
                raise RuntimeError("cannot resolve grasp object near " + str(place_obj))
            g = objs[0]
        return g, p

    # 目标位姿：真实物体 -> 其 _pos；区域名（含 region/table）-> 用区域名里
    # 命中的场景物体位置均值（例如 between_plate_ramekin 取盘与 ramekin 中点）
    def resolve_target(obs, g, p):
        pp = pos_of(obs, p)
        if pp is not None:
            return pp.copy(), False
        toks = set(p.split("_"))
        matched = [o for o in scene_objs(obs) if o != g and (toks & set(o.split("_")))]
        if matched:
            pts = np.stack([pos_of(obs, o) for o in matched])
            t = pts.mean(axis=0)
            t[2] = float(np.median(pts[:, 2]))
            return t, True
        raise RuntimeError("cannot resolve place target: " + str(p))

    # 两指 spread 轴相对世界 +x 的角误差（目标：把指轴对到 0，使壁在两指之间）
    def finger_axis_err():
        sim = env.sim
        model, data = sim.model, sim.data
        cand = []
        for i in range(model.ngeom):
            try:
                nm = model.geom_id2name(i)
            except Exception:
                nm = None
            if not nm:
                continue
            if ("finger_joint1" in nm) or ("finger_joint2" in nm):
                cand.append((i, nm))
        tips = [i for i, nm in cand if ("pad" in nm) or ("tip" in nm)]
        use = tips if len(tips) >= 2 else [i for i, _ in cand]
        if len(use) < 2:
            return 0.0
        p1 = np.asarray(data.geom_xpos[use[0]], dtype=np.float64)[:3]
        p2 = np.asarray(data.geom_xpos[use[-1]], dtype=np.float64)[:3]
        ang = math.atan2(float(p1[1] - p2[1]), float(p1[0] - p2[0]))
        return float((ang % math.pi) - 0.5 * math.pi)

    def move_to(obs, tgt, gripper, max_steps=140, tol=0.012):
        tgt = np.asarray(tgt, dtype=np.float64)
        for _ in range(max_steps):
            eef = eef_of(obs)
            d = tgt - eef
            if float(np.linalg.norm(d)) < tol:
                break
            delta = np.clip(0.5 * d, -0.05, 0.05)
            a = zeros_a(gripper)
            a[:3] = delta / 0.05
            obs = step_a(a)
        return obs

    def move_z(obs, z_tgt, gripper, max_steps=90, tol=0.005):
        for _ in range(max_steps):
            eef = eef_of(obs)
            dz = float(z_tgt - eef[2])
            if abs(dz) < tol:
                break
            a = zeros_a(gripper)
            a[2] = float(np.clip(0.5 * dz, -0.04, 0.04) / 0.05)
            obs = step_a(a)
        return obs

    def move_xy(obs, tgt_xy, gripper, z_hold, max_steps=150, tol=0.010):
        tgt_xy = np.asarray(tgt_xy, dtype=np.float64)[:2]
        for _ in range(max_steps):
            eef = eef_of(obs)
            if float(np.linalg.norm(eef[:2] - tgt_xy)) < tol:
                break
            d = np.array([tgt_xy[0] - eef[0], tgt_xy[1] - eef[1],
                          float(z_hold) - eef[2]], dtype=np.float64)
            delta = np.clip(0.5 * d, -0.05, 0.05)
            a = zeros_a(gripper)
            a[:3] = delta / 0.05
            obs = step_a(a)
        return obs

    def align_yaw(obs, gripper=-1.0):
        e0 = abs(finger_axis_err())
        if e0 < 0.10:
            return obs
        sgn = 1.0
        for _ in range(3):
            a = zeros_a(gripper)
            a[5] = 0.3
            obs = step_a(a)
        if abs(finger_axis_err()) > e0:
            sgn = -1.0
        bad = 0
        prev = e0
        for _ in range(100):
            e = finger_axis_err()
            if abs(e) < 0.12:
                break
            if abs(e) > prev + 0.005:
                bad += 1
                if bad >= 8:
                    sgn = -sgn
                    bad = 0
            else:
                bad = 0
            prev = abs(e)
            a = zeros_a(gripper)
            a[5] = float(np.clip(-2.0 * sgn * e, -0.5, 0.5))
            obs = step_a(a)
        return obs

    def restore():
        o = env.set_init_state(init_state)
        if o is None or not hasattr(o, "keys"):
            o = step_a(zeros_a(-1.0))
        for _ in range(10):
            o = step_a(zeros_a(-1.0))
        return o

    # reach -> 空中对齐指轴 -> 垂直下探 -> 闭爪 -> 抬升，物理判持（物体真随爪上升）
    def attempt_grasp(obs, gname, attempt):
        obj0 = pos_of(obs, gname)
        if obj0 is None:
            return False, obs
        offs = [(0.055, 0.0, 0.15), (0.050, 0.006, 0.15), (0.060, -0.006, 0.16)]
        ox, oy, hz = offs[attempt % len(offs)]
        hover = np.array([float(obj0[0]) + ox, float(obj0[1]) + oy,
                          float(obj0[2]) + hz], dtype=np.float64)
        obs = move_to(obs, hover, gripper=-1.0, max_steps=140, tol=0.012)
        obs = align_yaw(obs, gripper=-1.0)
        obj1 = pos_of(obs, gname)
        if obj1 is None:
            return False, obs
        obs = move_z(obs, float(obj1[2]) + 0.027, gripper=-1.0, max_steps=90, tol=0.005)
        for _ in range(16):
            obs = step_a(zeros_a(1.0))
        obj_before = pos_of(obs, gname)
        eef0 = eef_of(obs)
        for _ in range(50):
            a = zeros_a(1.0)
            a[2] = 1.0
            obs = step_a(a)
        obj_after = pos_of(obs, gname)
        eef1 = eef_of(obs)
        if obj_before is None or obj_after is None:
            return False, obs
        rise = float(obj_after[2] - obj_before[2])
        eef_rise = max(float(eef1[2] - eef0[2]), 1e-4)
        held = bool(rise > 0.05 and rise > 0.5 * eef_rise)
        return held, obs

    # ------------------------------ 局开始 ------------------------------
    obs = restore()
    try:
        g, p = resolve_names(obs)
    except Exception:
        return False

    grasped = False
    for attempt in range(3):
        ok, obs = attempt_grasp(obs, g, attempt)
        if ok:
            grasped = True
            break
        obs = restore()
    if not grasped:
        return False

    try:
        target, _is_region = resolve_target(obs, g, p)
    except Exception:
        return False

    eef = eef_of(obs)
    obj = pos_of(obs, g)
    trail = eef[:2] - obj[:2]
    goal_xy = np.asarray(target[:2], dtype=np.float64) + trail
    hz = float(max(eef[2], obj[2] + 0.07))

    # 分轴运输（先 x 后 y，各带闭爪沉降杀摆动），保持闭爪
    obs = move_xy(obs, goal_xy, gripper=1.0, z_hold=hz, max_steps=150, tol=0.010)
    obs = move_xy(obs, goal_xy, gripper=1.0, z_hold=hz, max_steps=70, tol=0.010)

    # 反应式下放：每步降 4mm，物体接近目标高度立即准备释放
    for _ in range(80):
        objp = pos_of(obs, g)
        eef = eef_of(obs)
        if objp is None:
            break
        if (float(objp[2]) - float(target[2])) <= 0.014:
            break
        if float(eef[2]) <= float(target[2]) + 0.035:
            break
        a = zeros_a(1.0)
        a[2] = -0.08
        obs = step_a(a)

    # 开爪与竖直上提同步（指竖直退出，避免横扫踢物体）
    for _ in range(28):
        a = zeros_a(-1.0)
        a[2] = 0.5
        obs = step_a(a)
    for _ in range(15):
        a = zeros_a(-1.0)
        a[2] = 0.2
        obs = step_a(a)
    for _ in range(20):
        obs = step_a(zeros_a(-1.0))

    try:
        return bool(env.check_success())
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="run")
    args = ap.parse_args()
    out_dir = args.out_dir
    run_id = args.run_id
    os.makedirs(out_dir, exist_ok=True)

    benchmark = get_benchmark("libero_spatial")()
    task_names = benchmark.get_task_names()

    writer = imageio.get_writer(
        os.path.join(out_dir, "video.mp4"),
        fps=FPS, codec="libx264", quality=8, macro_block_size=1,
    )
    counter = [0]
    last_img = [None]
    results = []
    telemetry_eps = []
    error = None

    try:
        for idx in range(len(task_names)):
            bddl = benchmark.get_task_bddl_file_path(idx)
            stem = os.path.splitext(os.path.basename(bddl))[0]
            task_id = "libero_spatial_" + stem
            bddl_rel = "libero_spatial/" + stem + ".bddl"
            grasp_obj, place_obj = parse_goal(bddl)
            if grasp_obj is None or place_obj is None:
                raise RuntimeError("goal parse failed for " + task_id)

            env = None
            try:
                try:
                    env = OffScreenRenderEnv(bddl_file_name=bddl, horizon=HORIZON)
                except TypeError:
                    env = OffScreenRenderEnv(bddl_file_name=bddl)
                for attr in ("horizon", "_max_episode_steps"):
                    try:
                        setattr(env, attr, HORIZON)
                    except Exception:
                        pass
                env.reset()
                init_states = benchmark.get_task_init_states(idx)
                if init_states is None or len(init_states) < 2:
                    raise RuntimeError("insufficient init states for " + task_id)
                n_succ = 0
                for ep in range(2):
                    ok = run_episode(env, init_states[ep], grasp_obj, place_obj,
                                     writer, counter, last_img)
                    ok = bool(ok)
                    n_succ += int(ok)
                    telemetry_eps.append({
                        "task_id": task_id,
                        "episode": ep,
                        "grasp_obj": grasp_obj,
                        "place_obj": place_obj,
                        "success": int(ok),
                    })
                results.append({
                    "task_id": task_id,
                    "bddl": bddl_rel,
                    "success": int(n_succ),
                    "episodes": 2,
                })
            finally:
                if env is not None:
                    try:
                        env.close()
                    except Exception:
                        pass
    except Exception:
        error = traceback.format_exc()
        sys.stderr.write(error)
        sys.stderr.flush()
    finally:
        try:
            writer.close()
        except Exception:
            pass

    results_obj = {
        "schema": "simpraxis.task7.libero_results.v1",
        "stage": "stage1_spatial",
        "suite_name": "libero_spatial",
        "n_episodes_per_task": 2,
        "judge": "libero_official",
        "tasks": results,
    }
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(results_obj, f, indent=2)

    telemetry = {
        "engine": "mujoco",
        "sim_engine": "mujoco",
        "run_id": run_id,
        "stage": "stage1_spatial",
        "suite_name": "libero_spatial",
        "judge": "libero_official",
        "n_episodes_per_task": 2,
        "dt": FRAME_DT,
        "control_freq": FPS,
        "physics_timestep": 0.002,
        "n_frames": counter[0],
        "episodes": telemetry_eps,
    }
    with open(os.path.join(out_dir, "telemetry.json"), "w") as f:
        json.dump(telemetry, f, indent=2)

    manifest = {"n_frames": int(counter[0]), "frame_dt_s": float(FRAME_DT)}
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    if last_img[0] is not None:
        imageio.imwrite(os.path.join(out_dir, "cover.png"), last_img[0])

    if error is not None:
        sys.exit(1)
    if len(results) != len(task_names):
        sys.stderr.write("incomplete suite: %d/%d tasks\n" % (len(results), len(task_names)))
        sys.exit(1)


if __name__ == "__main__":
    main()
