#!/usr/bin/env python3
"""Q2（Carla 固态 LiDAR 雨雪雾）：基于物理光学的天气-材质传感器模型。

面试题（inputs/tracks/track_2_samples.txt 第 2 题）要求「基于物理光学特性设计
传感器材质模型」。Carla 自带 sensor.lidar.ray_cast 是**几何光线投射**：与天气
体积介质无交互（0.10.0 PythonAPI 原文 “simulates a rotating LIDAR using
ray-casting”，无任何大气散射参数）。本模块按「表面通道 / 天气通道 / 探测器
通道」三段显式建模，作为引擎之外的材质层叠加：

1. 表面通道（目标回波）
   - 单程 Beer–Lambert 透射 T(r)=exp(-α·r)，双程光雷达功率衰减 ∝ T(r)^2；
     对 Carla 已含 1/r² 的 intensity 只乘双程透射与湿润材质系数。
   - 湿润材质系数 m(tag)：水膜改变 905 nm BRDF——沥青漫反射变暗、高光瓣变窄
     （Rasshofer et al., *Automotive LiDAR in Adverse Weather*, 2011）。
2. 天气通道（体积散射杂波）
   - 雨滴 Marshall–Palmer (1948) 指数谱；雪 Gunn–Marshall (1958) 指数谱
     （S 为融化当量 mm/h）；雾用 Koschmieder (1924) 能见度反演。
   - 消光与后向散射系数由滴谱积分 Qext/Qb 闭式给出（大球 x=πD/λ≫1，
     Qext→2 消光悖论；905 nm、D=0.5–5 mm 时 x≈1700–17000）。
   - 沿光束分壳层按 Poisson 注入降水伪回波（强度按双程透射加权、径向抖动
     σ_r），近场盲区（近场后向散射致 APD 饱和）按 p_blind 丢弃目标点。
3. 探测器通道
   - 强度阈值探测：I·增益 + 散粒噪声（Poisson 计数 √N）低于 i_min 即丢点。

所有物理常数在文件内溯源（论文/教材），非裸数字（规则7/阈值溯源）。
模型**不是**对真实传感器的标定复刻（无真实天气 LiDAR 数据标定），残差在
SUMMARY.md 中分开报告：outcome（Carla 原生无天气响应）与 mechanism（本层
按一级原理给出可标定结构）。纯 numpy 1.26.4、确定性（rng 显式传入）。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# 物理常数（逐条溯源；单位在注释中钉死）
# ---------------------------------------------------------------------------
WAVELENGTH_NM = 905.0  # 主流车规半导体激光器波长（另有 1550 nm，不在本实验）

# Marshall & Palmer (1948), Q.J.R. Meteorol. Soc. 74: N(D)=N0 exp(-Λ D)
# D 单位 mm；N0 单位 mm^-1 m^-3；Λ = 4.1 R^-0.21，单位 mm^-1，R 为雨强 mm/h
RAIN_N0 = 8000.0          # mm^-1 m^-3
RAIN_LAMBDA_K = 4.1       # mm^-1 · (mm/h)^0.21
RAIN_LAMBDA_EXP = -0.21

# Gunn & Marshall (1958), Q.J.R. Meteorol. Soc. 84（雪滴谱，融化当量）：
# N0=3800 mm^-1 m^-3；Λ = 2.29 S^-0.45 mm^-1，S 为水当量雪强 mm/h
SNOW_N0 = 3800.0
SNOW_LAMBDA_K = 2.29
SNOW_LAMBDA_EXP = -0.45

# 大球 Mie/几何光学区消光效率 Qext→2（消光悖论）；球形大粒子后向散射效率
# 在 0.1–1 间振荡（Mie 谐振），取保守中值 0.4 并在 SUMMARY 做敏感性声明：
# 该参数应以真实天气回波数据标定，本实验只断言量级与单调性。
# 依据：Rasshofer et al. (2011) 综述 Fig. 9–11 量级带。
QEXT_LARGE_SPHERE = 2.0
QBACK_DEFAULT = 0.4

# Koschmieder (1924)：气象能见度 V(m) 与 550 nm 消光 α=3.912/V。
# 905 nm 对典型雾滴 MVD 10–20 µm（x≈35–70，Qext 波长中性）近似同值；
# 偏差作为雾通道残差声明，不调参拟合。
KOSCHMIEDER_K = 3.912
FOG_LAMBDA_RATIO_905 = 1.0

# 光束几何：车规 LiDAR 典型光束发散半角 ~1 mrad（全角 2 mrad）
BEAM_DIVERGENCE_HALF_RAD = 0.001
# 近场饱和盲区：强降水时 0–r_blind 的近场后向散射可使接收通道饱和。
# r_blind 随雨强线性外推（20 mm/h≈1m → 100 mm/h≈5m，量级据 Rasshofer
# 2011 Fig.12 的 bloom 现象，非拟合常数）；另以概率 p_blind 表达部分盲。
RBLIND_AT_100_MMH = 5.0
# 探测器阈值：归一化 intensity（Carla intensity∈[0,1]，干沥青 1m≈1 标定）
DETECT_I_MIN = 0.02
DETECT_SHOT_NOISE_REL = 0.05  # √N 散粒噪声相对幅度（保守上限，声明非标定）
RADIAL_NOISE_M = 0.02         # 降水回波测距抖动 σ（脉宽对应 ~3ns 量级）
# 距离门（range bin）：探测器对单脉冲做距离分箱的**积分**后向散射功率，而非
# 单滴触发（单滴截面比表面小 ~αΔr/ρ 量级，裸 Poisson 截获近零，无法表达
# bloom）。门宽 0.3 m（≈2 ns，车规脉冲宽度量级）。
RANGE_BIN_M = 0.3
RANGE_BIN_MAX_M = 50.0
# 干沥青 905 nm 反射率量级 0.10–0.20（Rasshofer 2011 表；取 0.10 下限作归
# 一基准）：同距离门内体积散射功率/路面回波 ≈ β·Δr/ρ·T²。
ROAD_REFLECTIVITY_905 = 0.10

# 905 nm 湿润表面相对干表面的漫反射强度系数（水膜镜面重分布；Rasshofer 2011
# Table II 量级：湿沥青回波约为干沥青 0.6–0.8，取 0.7）。Carla 无材质光谱
# 通道时统一按道路表面近似；未知 tag 系数 1.0（不改写）。
WET_FACTOR = {
    "road": 0.7,
    "sidewalk": 0.75,
    "terrain": 0.85,
    "unknown": 1.0,
}

# 雨消光经验对照（Rasshofer et al. 2011, 式 a_R=1.075·R^0.68 dB/km，905 nm）：
# R=2.5→2.0、50→15.4、100→26.5 dB/km；滴谱积分值在 ×1.4 内（测试断言）。
RAIN_EMP_K = 1.075
RAIN_EMP_EXP = 0.68
RAIN_DSD_VS_EMPIRIC_TOL = 1.5   # 滴谱积分/经验式 比值上限（不调参，只对账）
FOG_V50_ALPHA_RANGE_1_KM = (50.0, 120.0)  # V≈50 m 浓雾 α 文献带 (1/km)


@dataclass(frozen=True)
class WeatherSpec:
    """天气条件（三通道参数载体）。

    kind: clear/rain/snow/fog；rate_mmh 降水强（融化当量）；visibility_m 雾
    能见度；wetness 0/1 是否启用湿润材质；每个值均来自采集脚本天气预设。
    """

    kind: str
    rate_mmh: float = 0.0
    visibility_m: float = float("inf")
    wetness: bool = False

    def __post_init__(self) -> None:
        if self.kind not in ("clear", "rain", "snow", "fog"):
            raise ValueError(f"未知天气类型: {self.kind}")
        if self.rate_mmh < 0 or self.visibility_m <= 0:
            raise ValueError("天气参数越界")


@dataclass(frozen=True)
class OpticsParams:
    # 注：光束发散角在「体积散射/表面回波」功率比中与 r² 同消，模型不显式
    # 依赖 beam_half_rad；该常数保留作文献口径引用。
    qback: float = QBACK_DEFAULT
    detect_i_min: float = DETECT_I_MIN
    shot_noise_rel: float = DETECT_SHOT_NOISE_REL
    radial_noise_m: float = RADIAL_NOISE_M
    wet_factor: dict = field(default_factory=lambda: dict(WET_FACTOR))


def _exp_dsd_integrals(n0: float, lam: float, *,
                       qback: float = QBACK_DEFAULT) -> tuple[float, float]:
    """指数滴谱 N(D)=N0 e^-ΛD 的截面积分（D 以 mm，N 以 mm^-1·m^-3）。

    ∫₀∞ D² e^-ΛD dD = 2/Λ³；返回 (消光系数, 后向散射系数)，单位 1/m。
    截面 πD²/4 以 mm² 计 → ×1e-6 转 m²。

    L-9：qback（大球后向散射效率）此前是 OpticsParams 上的零消费字段；
    现显式穿到积分里，默认 QBACK_DEFAULT 保证数值与历史结果逐位一致。
    alpha 只依赖 QEXT_LARGE_SPHERE（消光悖论 =2），不受 qback 影响。
    """
    d2 = 2.0 / lam ** 3
    cross_m2_sum = (math.pi / 4.0) * n0 * d2 * 1e-6
    alpha = QEXT_LARGE_SPHERE * cross_m2_sum
    beta = qback * cross_m2_sum
    return alpha, beta


def extinction_coefficients(w: WeatherSpec, *,
                            qback: float = QBACK_DEFAULT) -> dict:
    """返回 {'alpha': 单程消光 1/m, 'beta_pi': 后向散射 1/(m·sr) 近似,
    'source': 溯源标签}。clear 时严格为 0（恒等模型，测试可断言）。

    L-9：qback 关键字参数由 apply_optics 从 OpticsParams.qback 透传；
    默认 QBACK_DEFAULT，alpha（消光通道）任何取值下都不变。"""
    if w.kind == "clear":
        return {"alpha": 0.0, "beta_pi": 0.0, "source": "clear"}
    if w.kind == "rain":
        lam = RAIN_LAMBDA_K * w.rate_mmh ** RAIN_LAMBDA_EXP
        a, b = _exp_dsd_integrals(RAIN_N0, lam, qback=qback)
        return {"alpha": a, "beta_pi": b,
                "source": "Marshall-Palmer(1948), Λ=4.1R^-0.21"}
    if w.kind == "snow":
        lam = SNOW_LAMBDA_K * w.rate_mmh ** SNOW_LAMBDA_EXP
        a, b = _exp_dsd_integrals(SNOW_N0, lam, qback=qback)
        return {"alpha": a, "beta_pi": b,
                "source": "Gunn-Marshall(1958), Λ=2.29S^-0.45"}
    # fog：能见度反演
    a = FOG_LAMBDA_RATIO_905 * KOSCHMIEDER_K / w.visibility_m
    return {"alpha": a, "beta_pi": a * qback / QEXT_LARGE_SPHERE,
            "source": "Koschmieder(1924), α=3.912/V @905nm≈550nm"}


def apply_optics(points: np.ndarray, intensity: np.ndarray,
                 weather: WeatherSpec, rng: np.random.Generator, *,
                 origin: np.ndarray | None = None,
                 surface_tag: np.ndarray | None = None,
                 params: OpticsParams | None = None) -> dict:
    """把三段光学材质模型施加到一帧几何点云。

    入参
      points      (N,3) Carla ray_cast 世界系点
      intensity   (N,)  Carla intensity ∈ [0,1]
      origin      (3,) 雷达相位中心（世界系）；默认原点
      surface_tag (N,) 每点材质 tag（road/sidewalk/.../unknown）
    返回 dict：
      points/intensity/is_weather/surface_tag/near_blind_mask/detect_drop_mask
      与每帧标量 alpha/beta_pi/weather_points_count/transmission_mean。
    天气通道是**追加**伪点（is_weather=True），目标点只做衰减/丢失，绝不把
    伪点伪装成表面点（No Fake Physics：来源可分，L571 outcome/mechanism 分开）。
    """
    p = params or OpticsParams()
    pts = np.asarray(points, dtype=np.float64)
    inten = np.asarray(intensity, dtype=np.float64)
    n = len(pts)
    # L-9：积分实际消费 OpticsParams.qback（此前该字段零消费）；默认值
    # QBACK_DEFAULT，默认参数下天气注入与历史批次数值逐位一致，alpha 不变。
    coeff = extinction_coefficients(weather, qback=p.qback)
    alpha, beta = coeff["alpha"], coeff["beta_pi"]

    o = np.zeros(3) if origin is None else np.asarray(origin, dtype=np.float64)
    rel = pts - o
    r = np.linalg.norm(rel, axis=1) if n else np.zeros(0)

    # 1) 表面通道：双程透射 + 湿润材质系数
    trans = np.exp(-2.0 * alpha * r) if n else np.zeros(0)
    m_wet = np.ones(n)
    if weather.wetness and surface_tag is not None:
        tags = np.asarray(surface_tag)
        m_wet = np.array([p.wet_factor.get(t, 1.0) for t in tags])
    i_surf = inten * trans * m_wet

    # 2a) 探测器通道：散粒噪声 + 阈值
    shot = rng.normal(1.0, p.shot_noise_rel, size=n) if n else np.zeros(0)
    i_obs = np.maximum(i_surf * shot, 0.0)
    detect_drop = i_obs < p.detect_i_min

    # 2b) 近场饱和盲：雨/雪越强，近场目标点越易被 bloom 淹没
    near_blind = np.zeros(n, dtype=bool)
    false_rays_list: list[np.ndarray] = []
    false_i_list: list[np.ndarray] = []
    if weather.kind in ("rain", "snow") and weather.rate_mmh > 0:
        r_blind = RBLIND_AT_100_MMH * min(weather.rate_mmh, 100.0) / 100.0
        p_blind = min(weather.rate_mmh / 100.0, 0.9)
        near_blind = (r < r_blind) & (rng.random(n) < p_blind)

        # 2c) 天气通道：距离门积分功率 + Bernoulli 阈值探测。
        # 每条脉冲在同一距离门对天气体积的响应相同（与目标距离无关），故每个
        # 距离门的命中总数对全部射线服从 Binomial(n_rays, p_bin)：
        #   p_bin(r) = clip(βπ·Δr/ρ_road · T²(r) · (1+散粒噪声), 0, 1)
        # 近场 T≈1 → 雨强强时近场 bloom；远场随 T² 熄灭（物理单调）。
        edges = np.arange(0.5, RANGE_BIN_MAX_M + RANGE_BIN_M, RANGE_BIN_M)
        bin_w = np.diff(edges)
        bin_mid = 0.5 * (edges[:-1] + edges[1:])
        t2 = np.exp(-2.0 * alpha * bin_mid)
        p_base = np.clip(
            beta * bin_w / ROAD_REFLECTIVITY_905 * t2, 0.0, 1.0)
        directions = rel / np.maximum(r, 1e-9)[:, None]
        for j in range(len(bin_mid)):
            pj = p_base[j]
            if pj <= 0.0:
                continue
            k = int(rng.binomial(n, pj))
            if k == 0:
                continue
            ray_idx = rng.choice(n, size=k, replace=False)
            rr = bin_mid[j] + rng.normal(0.0, p.radial_noise_m, size=k)
            rr = np.clip(rr, edges[j], edges[j + 1])
            new_pts = o + directions[ray_idx] * rr[:, None]
            ii = np.clip(pj * t2[j]
                         * rng.normal(1.0, p.shot_noise_rel, size=k),
                         0.0, 1.0)
            false_rays_list.append(new_pts)
            false_i_list.append(ii)

    keep = ~(detect_drop | near_blind)
    out_pts = [pts[keep]]
    out_i = [i_obs[keep]]
    out_tag = (["surface"] * int(keep.sum()))
    if false_rays_list:
        fp = np.concatenate(false_rays_list, axis=0)
        fi = np.concatenate(false_i_list, axis=0)
        out_pts.append(fp)
        out_i.append(fi)
        out_tag.extend(["weather"] * len(fi))
    all_pts = np.concatenate(out_pts, axis=0) if out_pts else np.zeros((0, 3))
    all_i = np.concatenate(out_i, axis=0) if out_i else np.zeros(0)

    return {
        "points": all_pts,
        "intensity": all_i,
        "surface_tag": np.array(out_tag),
        "is_weather": np.array([t == "weather" for t in out_tag]),
        "near_blind_mask": near_blind,
        "detect_drop_mask": detect_drop,
        "kept_mask": keep,
        "alpha_per_m": alpha,
        "beta_pi_per_m_sr": beta,
        "coeff_source": coeff["source"],
        "n_input": int(n),
        "n_weather_false": int(sum(len(x) for x in false_i_list)),
        "n_surface_kept": int(keep.sum()),
        "transmission_mean": float(trans.mean()) if n else 1.0,
    }
