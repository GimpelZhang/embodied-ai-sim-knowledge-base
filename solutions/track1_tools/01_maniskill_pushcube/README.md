# Track1 #1 — ManiSkill3 PushCube 真实 rollout（SAPIEN 3.0.3 / EGL 无头）

- 冻结输入：`inputs/tracks/track_1_samples.txt` 第 1 条工具（track1 / index=1，ManiSkill）
- 仿真引擎：SAPIEN（`sim_engine.slug: sapien`）最低版本 3.0.3；ManiSkill 3.0.1
  （引擎仓 pins 钉死，见 sim-praxis CLAUDE.md 硬规则 8，方案不覆盖版本）
- 用途：Phase 1 Task7 Track1 两引擎真实 rollout 之一，Rung1–4 判定载体
  （阈值真值在引擎仓 `orchestrator/judge/thresholds.py`，公开仓不复制数字）

## 运行面

```bash
python maniskill_pushcube.py --out-dir <workdir> --run-id <run_id>
# 可选：--seed --hold-steps --aim-offset --reach-offset
#       --preload-mm --preload-ramp-frames --push-speed-factor --push-z
```

`--out-dir`/`--run-id` 必填，由 Task7 编排器注入；GPU 无头环境需
`PYOPENGL_PLATFORM=egl`，SAPIEN PhysX 库按 `$HOME/.sapien/physx` 缓存
（容器内 HOME 指向持久缓存卷）。脚本内置大量硬自检（传感器/坐标/接触），
失败以非零码退出。

## 溯源

正本 = 引擎仓 Phase 1 仓内版逐字复制（sandbox/track1/maniskill_pushcube.py，
sha256 见 manifest），即 Task7 实跑所用版本；`v1_run_relpath: null`。
Task0b（2026-10-17）三层分离时从 sim-praxis 迁入本公开仓。
