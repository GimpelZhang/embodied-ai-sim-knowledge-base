#!/usr/bin/env python3
"""Q2 在 Carla 0.10.0 内采集「天气 → 固态式 LiDAR 点云」最小对照数据。

设计（面试题第 2 题；受控实验而非驾驶演示）：
- 静态自车、同一位姿与场景，逐段切换天气（clear / rain_hard / fog_dense），
  排除轨迹/场景变化混杂；每段静置 settle 后同步采集。
- 两个传感器同位置：ray_cast（带 intensity 的几何 LiDAR）与
  ray_cast_semantic（逐射线语义真值），同参数，用于「自由空间伪回波」
  配准检验与逐类别强度统计。
- 固态式扫描：120° 窄水平 FOV、16 线、10Hz、50m 量程（MEMS 式近似）。
- 同步模式 fixed_dt=0.1；每段存 N 帧（1Hz 抽帧，float32 xyzi + int32 标签）。
- Car­la 无原生雪天气（WeatherParameters 无 snow 字段，0.10.0 实测）：
  雪条件不伪造原生预设，雪的点云效应只在 optics_model 层对 clear 帧叠加。

只依赖 carla client wheel + numpy；在宿主 /mnt/venvs/simpraxis 运行，连接
--net=host 的 Carla 服务端 127.0.0.1:2000。确定性：同步模式 + 固定参数；
repeat=3 为独立进程重跑（静态场景下用于验证可重复性）。
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np

try:
    import carla
except ImportError as exc:  # pragma: no cover
    raise SystemExit("需要 carla 0.10.0 client wheel（见 task8 Q2 证据）") from exc

# 预设值全部显式给出（不依赖引擎预设常量），溯源：Carla PythonAPI
# WeatherParameters，范围 0–100；雾距离以米计。
PRESETS = {
    "clear": {
        "cloudiness": 5.0, "precipitation": 0.0, "precipitation_deposits": 0.0,
        "wind_intensity": 0.0, "fog_density": 0.0, "fog_distance": 0.0,
        "fog_falloff": 0.0, "wetness": 0.0,
        "scattering_intensity": 1.0, "mie_scattering_scale": 1.0,
        "rayleigh_scattering_scale": 0.03, "dust_storm": 0.0,
    },
    "rain_hard": {
        "cloudiness": 80.0, "precipitation": 90.0,
        "precipitation_deposits": 70.0, "wind_intensity": 40.0,
        "fog_density": 5.0, "fog_distance": 0.0, "fog_falloff": 0.0,
        "wetness": 80.0,
        "scattering_intensity": 1.0, "mie_scattering_scale": 1.0,
        "rayleigh_scattering_scale": 0.03, "dust_storm": 0.0,
    },
    "fog_dense": {
        "cloudiness": 60.0, "precipitation": 0.0,
        "precipitation_deposits": 0.0, "wind_intensity": 0.0,
        "fog_density": 100.0, "fog_distance": 5.0, "fog_falloff": 2.0,
        "wetness": 0.0,
        "scattering_intensity": 1.0, "mie_scattering_scale": 1.0,
        "rayleigh_scattering_scale": 0.03, "dust_storm": 0.0,
    },
}
# 0.10.0 蓝图库实测无 tesla（仅 11 种车：ford/fuso/sprinter/patrol/charger/
# cooper/mkz 等），按偏好选实际存在的三厢车；不硬编码已下架蓝图。
VEHICLE_PREFERENCE = (
    "vehicle.lincoln.mkz", "vehicle.mini.cooper", "vehicle.nissan.patrol",
    "vehicle.dodge.charger",
)
ORDER = ("clear", "rain_hard", "fog_dense")
SETTLE_TICKS = 30        # 切天气后静置 3 s 让粒子/沉积稳定
COLLECT_TICKS = 100      # 每段 10 s
SAVE_EVERY = 10          # 1 Hz 抽帧


def _make_weather(vals: dict) -> "carla.WeatherParameters":
    w = carla.WeatherParameters()
    for k, v in vals.items():
        setattr(w, k, v)
    return w


def _lidar_bp(world: "carla.World", *, semantic: bool):
    kind = "ray_cast_semantic" if semantic else "ray_cast"
    bp = world.get_blueprint_library().find(f"sensor.lidar.{kind}")
    # 属性在两版蓝图上同名；若个别属性不存在则记录并跳过（不静默弱化）
    for key, val in (("channels", "16"), ("range", "50"),
                     ("points_per_second", "300000"),
                     ("rotation_frequency", "10"),
                     ("horizontal_fov", "120"), ("sensor_tick", "0.1")):
        if bp.has_attribute(key):
            bp.set_attribute(key, val)
    return bp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=2000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--map", default=None, help="缺省用 Town10HD_Opt 或首个可用")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--control-all-clear", action="store_true",
                    help="阴性对照：三段全部下发 clear 天气（保留段标签），"
                         "用于定位点数抖动是否为 RNG 随 tick 推进的伪相关")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    client = carla.Client(args.host, args.port)
    client.set_timeout(30.0)
    version = client.get_server_version()
    maps = client.get_available_maps()
    map_name = args.map or (
        "/Game/Carla/Maps/Town10HD_Opt" if "/Game/Carla/Maps/Town10HD_Opt" in maps
        else maps[0])
    world = client.load_world(map_name.rsplit("/", 1)[-1])

    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.1
    settings.no_rendering_mode = False
    world.apply_settings(settings)

    actors = []
    try:
        bp_lib = world.get_blueprint_library()
        avail_vehicles = [b.id for b in bp_lib.filter("vehicle.*")]
        vehicle_id = next((v for v in VEHICLE_PREFERENCE if v in avail_vehicles),
                          None)
        if vehicle_id is None:
            raise RuntimeError(f"偏好车辆均不可用，蓝图库车辆: {avail_vehicles}")
        car_bp = bp_lib.find(vehicle_id)
        spawn = world.get_map().get_spawn_points()[12]
        vehicle = world.spawn_actor(car_bp, spawn)
        actors.append(vehicle)
        vehicle.set_autopilot(False)
        vehicle.apply_control(carla.VehicleControl())  # 静态：全零控制

        lid_tf = carla.Transform(carla.Location(x=0.0, y=0.0, z=1.8))
        lid_geo = world.spawn_actor(
            _lidar_bp(world, semantic=False), lid_tf, attach_to=vehicle)
        sem_geo = world.spawn_actor(
            _lidar_bp(world, semantic=True), lid_tf, attach_to=vehicle)
        actors.extend([lid_geo, sem_geo])

        frames: dict = {}
        buf_l, buf_s = [], []
        lid_geo.listen(lambda d: buf_l.append(d))
        sem_geo.listen(lambda d: buf_s.append(d))

        # actor.attributes 是 spawn 后的实际生效值（蓝图 get_attribute 在
        # 0.10.0 pure-python wheel 上有坏绑定，会抛 std::exception）
        _attr_keys = ("channels", "range", "points_per_second",
                      "rotation_frequency", "horizontal_fov", "sensor_tick",
                      "upper_fov", "lower_fov",
                      "atmosphere_attenuation_rate", "dropoff_general_rate",
                      "dropoff_intensity_limit", "dropoff_zero_intensity",
                      "noise_stddev")
        lid_attrs = {"geo": {k: lid_geo.attributes.get(k) for k in _attr_keys},
                     "sem": {k: sem_geo.attributes.get(k) for k in _attr_keys}}

        for preset in ORDER:
            # 阴性对照：三段物理上全是 clear，段标签不变（隔离 tick 位置/RNG 效应）
            vals = PRESETS["clear"] if args.control_all_clear else PRESETS[preset]
            world.set_weather(_make_weather(vals))
            for _ in range(SETTLE_TICKS):
                world.tick()
            seg = []
            for ti in range(COLLECT_TICKS):
                world.tick()
                if ti % SAVE_EVERY != 0 or not buf_l or not buf_s:
                    continue
                # 取本段最新一对帧（10Hz 缓存里最后一帧）
                dl, ds = buf_l[-1], buf_s[-1]
                pl = np.frombuffer(dl.raw_data, dtype=np.float32).reshape(-1, 4)
                ps = np.frombuffer(ds.raw_data,
                                   dtype=np.dtype([("x", "f4"), ("y", "f4"),
                                                   ("z", "f4"), ("cos", "f4"),
                                                   ("idx", "u4"), ("tag", "u4")]))
                seg.append({
                    "tick": ti,
                    "geo": pl.copy(),
                    "sem_xyz": np.stack(
                        [ps["x"], ps["y"], ps["z"]], axis=1).copy(),
                    "sem_tag": ps["tag"].astype(np.int32).copy(),
                    "tf": [dl.transform.location.x, dl.transform.location.y,
                           dl.transform.location.z],
                })
            frames[preset] = seg

        meta = {"server_version": str(version), "map": str(world.get_map().name),
                "vehicle": vehicle_id, "vehicles_available": avail_vehicles,
                "lidar_attrs": lid_attrs,
                "presets": ORDER,
                "preset_values": ({p: PRESETS["clear"] for p in ORDER}
                                  if args.control_all_clear else PRESETS),
                "control_all_clear": args.control_all_clear,
                "settle_ticks": SETTLE_TICKS, "collect_ticks": COLLECT_TICKS,
                "save_every": SAVE_EVERY,
                "spawn": [spawn.location.x, spawn.location.y, spawn.location.z],
                "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "repeat": args.repeat,
                "note_atmosphere": "ray_cast 蓝图带静态 atmosphere_attenuation_rate"
                                   "（默认 0.004 /m），是传感器常量、不随天气变化；"
                                   "三预设实测点云统计用于证明其天气不变性",
                "note_snow": "Carla 0.10.0 WeatherParameters 无 snow 字段；"
                             "雪通道仅在 optics_model 层建模"}
        np.savez_compressed(out / f"frames_rep{args.repeat}.npz",
                            **{f"{p}__{i}__{k}": v
                               for p in ORDER for i, f in enumerate(frames[p])
                               for k, v in f.items() if isinstance(v, np.ndarray)})
        (out / f"meta_rep{args.repeat}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": True, "out": str(out),
                          "frames": {p: len(frames[p]) for p in ORDER}},
                         ensure_ascii=False))
    finally:
        # 任何异常路径都回收 actor，避免同步模式与车辆残留在服务端
        for a in reversed(actors):
            try:
                if hasattr(a, "stop"):
                    a.stop()
                a.destroy()
            except Exception:
                pass
        settings = world.get_settings()
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None
        world.apply_settings(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
