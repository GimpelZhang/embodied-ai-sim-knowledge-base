# Track1 #2 — MuJoCo 3.15.0 接触推动 Cube（EGL 无头）

- 冻结输入：`inputs/tracks/track_1_samples.txt` 第 2 条工具（track1 / index=2，MuJoCo）
- 仿真引擎：MuJoCo（`sim_engine.slug: mujoco`）最低版本 3.15.0
  （引擎仓 pins 钉死：mujoco 3.15.0、numpy 1.26.4，方案不覆盖版本）
- 用途：Phase 1 Task7 Track1 两引擎真实 rollout 之一，Rung1–4 判定载体；
  Rung1 逐物理子步穿模、Rung2 接触时长/力 CV/目标窗口、Rung3 时间步带、
  Rung4 VLM 判定（阈值真值在引擎仓 `orchestrator/judge/thresholds.py`）

## 运行面

```bash
python mujoco_contact_push.py --out-dir <workdir> --run-id <run_id>
# 可选：--width 640 --height 480
```

`--out-dir`/`--run-id` 必填，由 Task7 编排器注入；GPU 无头环境需
`MUJOCO_GL=egl`、`PYOPENGL_PLATFORM=egl`。产物含 telemetry/视频/封面，
供 rung 判定与真人卡片使用。

## 溯源

正本 = 引擎仓 Phase 1 仓内版逐字复制（sandbox/track1/mujoco_contact_push.py，
sha256 见 manifest），即 Task7 实跑所用版本；`v1_run_relpath: null`。
Task0b（2026-10-17）三层分离时从 sim-praxis 迁入本公开仓。
