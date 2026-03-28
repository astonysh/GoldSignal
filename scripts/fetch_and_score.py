"""
========================================
黄金宏观信号系统 — 数据抓取与评分脚本
========================================

使用方法：
  1. 安装依赖：
       pip install requests

  2. 申请免费 FRED API Key：
       https://fredaccount.stlouisfed.org/login/secure/
       登录后进入 My Account → API Keys → Request API Key

  3. 设置环境变量：
       export FRED_API_KEY="你的API Key"

  4. 运行脚本：
       python3 scripts/fetch_and_score.py

FRED API Key 申请地址：https://fred.stlouisfed.org/docs/api/api_key.html
"""

import os
import json
import math
import datetime
import requests

# ============================================================
# API Key 从环境变量 FRED_API_KEY 读取
# 运行前请先执行：export FRED_API_KEY="你的API Key"
# ============================================================
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# Worker 接口地址，从环境变量读取
WORKER_URL = os.environ.get("WORKER_URL", "")

# Worker 写入密钥，从环境变量读取
WORKER_WRITE_TOKEN = os.environ.get("WORKER_WRITE_TOKEN", "")

# FRED API 基础地址
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# 每次拉取最近多少天的数据
FETCH_LIMIT = 60

# 趋势计算使用最近多少天
TREND_DAYS = 30

# 各指标的 FRED Series ID
SERIES_IDS = {
    "DFII10":       "10年期TIPS实际收益率",
    "BAMLH0A0HYM2": "高收益债利差",
    "WALCL":        "美联署资产负债表",
    "DTWEXBGS":     "美元指数",
    "T10Y2Y":       "收益率曲线斜率 (10Y-2Y)",
    "T10BIE":       "10年期盈亏平衡通胀率 (BEI)",
    "GVZ":          "黄金波动率指数 (GVZ)",
}

# 各指标拉取失败时使用的默认值（基于历史合理区间）
DEFAULT_VALUES = {
    "DFII10":       2.0,    # 单位：%
    "BAMLH0A0HYM2": 3.5,    # 单位：%（计算时会乘以100换算为bps）
    "WALCL":        70000,  # 单位：百亿美元（FRED原始单位为百万美元）
    "DTWEXBGS":     104.0,  # 无单位
    "T10Y2Y":       -0.2,   # 倒挂状态
    "T10BIE":       2.3,    # 2.3%
    "GVZ":          15.0,   # 15.0
}


# ============================================================
# 第一部分：API 数据拉取
# ============================================================

def get_api_key() -> str:
    """
    读取 FRED API Key。
    从环境变量 FRED_API_KEY 读取，为空时返回空字符串并打印警告。
    """
    return FRED_API_KEY


def fetch_series(series_id: str, api_key: str) -> list[dict]:
    """
    从 FRED API 拉取指定 series 的最近 FETCH_LIMIT 条观测数据。

    参数：
        series_id: FRED 数据系列 ID（如 "DFII10"）
        api_key: FRED API Key

    返回：
        按时间降序排列的观测记录列表，每条记录格式为 {"date": "YYYY-MM-DD", "value": float}
        如果拉取失败，返回空列表。
    """
    params = {
        "series_id":  series_id,
        "api_key":    api_key,
        "file_type":  "json",
        "sort_order": "desc",
        "limit":      FETCH_LIMIT,
    }

    try:
        response = requests.get(FRED_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        raw_data = response.json()
    except requests.exceptions.Timeout:
        print(f"  [错误] {series_id} 请求超时（超过10秒），将使用默认值。")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"  [错误] {series_id} HTTP 错误：{e}，将使用默认值。")
        return []
    except requests.exceptions.RequestException as e:
        print(f"  [错误] {series_id} 网络请求失败：{e}，将使用默认值。")
        return []
    except (KeyError, ValueError) as e:
        print(f"  [错误] {series_id} 数据解析失败：{e}，将使用默认值。")
        return []

    # 过滤掉 FRED 用 "." 表示的缺失值，只保留有效数字
    observations = []
    for obs in raw_data.get("observations", []):
        raw_value = obs.get("value", ".")
        if raw_value == ".":
            # 跳过缺失值
            continue
        try:
            observations.append({
                "date":  obs["date"],
                "value": float(raw_value),
            })
        except (ValueError, KeyError):
            # 跳过格式异常的记录
            continue

    return observations


def fetch_all_series(api_key: str) -> dict[str, list[dict]]:
    """
    依次拉取所有需要的 FRED 数据系列。

    返回：
        以 series_id 为键，观测记录列表为值的字典。
        拉取失败的系列返回空列表。
    """
    print("正在从 FRED 拉取数据...")
    results = {}
    for series_id, name in SERIES_IDS.items():
        print(f"  → 拉取 {series_id}（{name}）...")
        results[series_id] = fetch_series(series_id, api_key)
        count = len(results[series_id])
        if count > 0:
            print(f"    ✓ 获取到 {count} 条有效数据")
        else:
            print(f"    ✗ 未获取到有效数据，将使用默认值")
    return results


def get_latest_value(observations: list[dict], default: float) -> float:
    """
    从观测记录列表中取最新（第一条）的有效值。
    列表为空时返回默认值。
    """
    if observations:
        return observations[0]["value"]
    return default


def get_recent_values(observations: list[dict], days: int) -> list[float]:
    """
    从观测记录列表中取最近 days 条记录的值（列表已按时间降序排列）。
    """
    return [obs["value"] for obs in observations[:days]]


# ============================================================
# 第二部分：辅助计算
# ============================================================

def compute_linear_slope(values: list[float]) -> float:
    """
    用最小二乘法计算给定数值序列的线性趋势斜率。

    参数：
        values: 按时间降序排列的数值列表（最新的在前）

    返回：
        斜率（正值表示趋势上升，负值表示趋势下降）。
        数据点不足2个时返回 0。
    """
    n = len(values)
    if n < 2:
        return 0.0

    # 将数据反转为时间正序（最旧的在前），x 为时间序号
    reversed_values = list(reversed(values))
    x_vals = list(range(n))

    x_mean = sum(x_vals) / n
    y_mean = sum(reversed_values) / n

    numerator   = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, reversed_values))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将数值限制在 [min_val, max_val] 范围内。"""
    return max(min_val, min(max_val, value))


# ============================================================
# 第三部分：条件评分计算
# ============================================================

def score_condition1(observations_dfii10: list[dict]) -> tuple[float, float]:
    """
    计算条件一评分：实际利率（TIPS 10年期实际收益率 DFII10）。

    评分规则：
        < -0.5%  → 100分
        -0.5~0%  → 85分
        0~1%     → 65分
        1~1.5%   → 45分
        1.5~2%   → 25分
        > 2%     → 10分

    趋势调整（基于最近30天线性斜率）：
        斜率 < 0（趋势下降）→ +10分（上限100）
        斜率 > 0（趋势上升）→ -10分（下限0）

    返回：
        (最终评分, 最新实际收益率值)
    """
    latest = get_latest_value(observations_dfii10, DEFAULT_VALUES["DFII10"])

    # 基础分
    if latest < -0.5:
        base_score = 100.0
    elif latest < 0.0:
        base_score = 85.0
    elif latest < 1.0:
        base_score = 65.0
    elif latest < 1.5:
        base_score = 45.0
    elif latest < 2.0:
        base_score = 25.0
    else:
        base_score = 10.0

    # 趋势调整
    recent_values = get_recent_values(observations_dfii10, TREND_DAYS)
    slope = compute_linear_slope(recent_values)

    if slope < 0:
        # 趋势下降 → 对黄金有利 → 加分
        final_score = clamp(base_score + 10, 0, 100)
    elif slope > 0:
        # 趋势上升 → 对黄金不利 → 减分
        final_score = clamp(base_score - 10, 0, 100)
    else:
        final_score = base_score

    return final_score, latest


def score_condition2(
    observations_hy: list[dict],
    observations_walcl: list[dict],
) -> tuple[float, float, float]:
    """
    计算条件二评分：信用压力（高收益债利差 + 美联储资产负债表）。

    高收益债利差评分规则（BAMLH0A0HYM2，原始单位%，需×100换算为bps）：
        > 800bps  → 90分
        600~800   → 70分
        400~600   → 45分
        300~400   → 25分
        < 300     → 10分

    美联储资产负债表调整：
        WALCL 最近30天增幅 > 5%（QE信号）→ +15分

    返回：
        (最终评分, 高收益债利差bps值, 最新资产负债表值)
    """
    # 高收益债利差：% → bps
    hy_raw  = get_latest_value(observations_hy, DEFAULT_VALUES["BAMLH0A0HYM2"])
    hy_bps  = hy_raw * 100

    # 基础分
    if hy_bps > 800:
        base_score = 90.0
    elif hy_bps > 600:
        base_score = 70.0
    elif hy_bps > 400:
        base_score = 45.0
    elif hy_bps > 300:
        base_score = 25.0
    else:
        base_score = 10.0

    # 美联储资产负债表调整
    walcl_latest = get_latest_value(observations_walcl, DEFAULT_VALUES["WALCL"])
    walcl_recent = get_recent_values(observations_walcl, TREND_DAYS)

    # 取30天前的值（列表末尾，降序排列），与最新值对比
    qe_adjustment = 0.0
    if len(walcl_recent) >= 2:
        walcl_oldest_in_range = walcl_recent[-1]
        if walcl_oldest_in_range > 0:
            change_pct = (walcl_latest - walcl_oldest_in_range) / walcl_oldest_in_range
            if change_pct > 0.05:
                # 30天内增加超过5%，判断为 QE 信号，对黄金有利
                qe_adjustment = 15.0

    final_score = clamp(base_score + qe_adjustment, 0, 100)

    # 资产负债表以百亿美元显示（FRED 原始单位为百万美元，除以100换算为亿）
    walcl_display = walcl_latest / 100  # 百万美元 → 亿美元

    return final_score, hy_bps, walcl_display


def score_condition3(observations_dollar: list[dict]) -> tuple[float, float]:
    """
    计算条件三评分：结构性支撑（当前处于持续激活状态）。

    基础分固定为75分。
    美元指数调整（DTWEXBGS）：
        美元指数 < 95  → +10分（美元弱势，对黄金有利）
        美元指数 > 105 → -10分（美元强势，对黄金不利）
        95~105 之间   → 无调整

    返回：
        (最终评分, 最新美元指数值)
    """
    base_score = 75.0

    dollar = get_latest_value(observations_dollar, DEFAULT_VALUES["DTWEXBGS"])

    if dollar < 95:
        adjustment = 10.0
    elif dollar > 105:
        adjustment = -10.0
    else:
        adjustment = 0.0

    final_score = clamp(base_score + adjustment, 0, 100)

    return final_score, dollar


# ============================================================
# 新增：Regime 判定（Layer 1 & Layer 3）
# ============================================================

def compute_macro_regime(
    observations_slope: list[dict],
    observations_bei: list[dict]
) -> tuple[float, str]:
    """
    Layer 1 宏观底色判定：
    根据收益率曲线斜率 (T10Y2Y) 和 通胀预期 (BEI) 进行四象限划分。

    返回：
        (评分乘数, Regime名称)
    """
    slope = get_latest_value(observations_slope, DEFAULT_VALUES["T10Y2Y"])
    bei   = get_latest_value(observations_bei, DEFAULT_VALUES["T10BIE"])

    # 简化的四象限模型
    if slope < 0 and bei > 2.2:
        return 1.25, "STAGFLATION（滞胀/衰退预期）" # 黄金最友好
    elif slope > 0 and bei > 2.5:
        return 1.10, "OVERHEATING（过热/二次通胀）"  # 黄金抗通胀
    elif slope > 0 and bei < 2.0:
        return 0.85, "RECOVERY（复苏/通缩压力）"   # 对黄金较难受
    else:
        return 1.0, "NEUTRAL（中性市场环境）"


def compute_volatility_correction(observations_gvz: list[dict]) -> tuple[float, str]:
    """
    Layer 3 波动率/变点修正：
    利用 GVZ (黄金波动率指数) 判定是否存在规律断裂或恐慌。

    返回：
        (置信度系数, 修正说明)
    """
    gvz_latest = get_latest_value(observations_gvz, DEFAULT_VALUES["GVZ"])
    gvz_recent = get_recent_values(observations_gvz, TREND_DAYS)

    if not gvz_recent:
        return 1.0, "正常"

    gvz_avg = sum(gvz_recent) / len(gvz_recent)

    if gvz_latest > gvz_avg * 1.3:
        # 波动率异常爆发（通常是事件冲击），根据索罗斯反身性，降低原有规律的置信度
        return 0.7, "高波动/规律断裂警告"
    elif gvz_latest < gvz_avg * 0.7:
        # 极度波动压缩，可能正在酝酿突破
        return 1.1, "极度波动压缩（蓄势）"
    else:
        return 1.0, "波动正常"


# ============================================================
# 第四部分：综合信号判断
# ============================================================

def determine_signal(
    score1: float,
    score2: float,
    score3: float,
    regime_multiplier: float,
    vol_multiplier: float,
) -> str:
    """
    根据三个条件的评分及 Regime 修正判断综合信号。

    计算修正后的核心分：
    核心分 = (条件一 * 0.6 + 条件二 * 0.4) * regime_multiplier * vol_multiplier
    """
    # 基础核心分（实际利率占大头）
    base_avg = (score1 * 0.6 + score2 * 0.4)
    adjusted_score = base_avg * regime_multiplier * vol_multiplier

    if adjusted_score >= 65:
        return "HOLD"
    if adjusted_score <= 35:
        return "AVOID"
    if score3 >= 85 and 40 <= score1 <= 69:
        return "STRUCTURAL_SUPPORT"
    return "WATCH"


# ============================================================
# 第五部分：结果输出
# ============================================================

# 信号含义对照表
SIGNAL_LABELS = {
    "HOLD":               "持有",
    "AVOID":              "回避",
    "STRUCTURAL_SUPPORT": "结构性支撑",
    "WATCH":              "观望",
}


def print_results(
    today: str,
    tips_yield: float,
    hy_spread_bps: float,
    fed_balance: float,
    dollar_index: float,
    score1: float,
    score2: float,
    score3: float,
    regime_name: str,
    vol_status: str,
    signal: str,
) -> None:
    """
    在终端以格式化方式打印评估结果。
    """
    signal_label = SIGNAL_LABELS.get(signal, signal)

    print()
    print("=" * 50)
    print("黄金宏观信号系统 V2 (Regime-Based) — 今日评估")
    print(f"日期：{today}")
    print("=" * 50)
    print()
    print("【Layer 1：宏观底色 (Macro Regime)】")
    print(f"  当前状态：{regime_name}")
    print()
    print("【Layer 2：核心指标 (Core Indicators)】")
    print(f"  TIPS实际收益率 (DFII10)：{tips_yield:+.2f}% (得分: {score1:.0f})")
    print(f"  高收益债利差 (BAMLH0A0HYM2)：{hy_spread_bps:.0f} bps (得分: {score2:.0f})")
    print(f"  美元指数 (DTWEXBGS)：{dollar_index:.1f} (结构支撑: {score3:.0f})")
    print()
    print("【Layer 3：实时修正 (Real-time Correction)】")
    print(f"  波动率/变点状态：{vol_status}")
    print()
    print("【最终综合信号】")
    print(f"  >>> {signal}（{signal_label}）<<<")
    print()
    print("=" * 50)
    print()


def save_results(
    today: str,
    tips_yield: float,
    hy_spread_bps: float,
    fed_balance: float,
    dollar_index: float,
    score1: float,
    score2: float,
    score3: float,
    signal: str,
    regime_name: str = "",
    vol_status: str = "",
    output_path: str = "result.json",
) -> None:
    """
    将评估结果保存为 JSON 文件。

    参数：
        output_path: 输出文件路径，默认为当前目录下的 result.json
    """
    result = {
        "date":              today,
        "condition1_score":  round(score1),
        "condition2_score":  round(score2),
        "condition3_score":  round(score3),
        "overall_signal":    signal,
        "tips_yield":        round(tips_yield, 4),
        "hy_spread":         round(hy_spread_bps),
        "fed_balance":       round(fed_balance),
        "dollar_index":      round(dollar_index, 2),
        "regime":            regime_name,
        "vol_correction":    vol_status,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已保存至：{output_path}")
    except OSError as e:
        print(f"[警告] 无法保存结果文件：{e}")


def send_to_worker(result):
    """把评分结果发送到 Cloudflare Worker 存入 D1 数据库"""

    # 如果没有配置 Worker URL，跳过这一步
    if not WORKER_URL or not WORKER_WRITE_TOKEN:
        print("\n[提示] 未配置 WORKER_URL 或 WORKER_WRITE_TOKEN，跳过发送到数据库。")
        return False

    url = f"{WORKER_URL}/api/update"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WORKER_WRITE_TOKEN}"
    }

    try:
        print(f"\n正在发送数据到 Worker：{url}")
        response = requests.post(url, json=result, headers=headers, timeout=15)

        if response.status_code == 200:
            print(f"  ✓ 数据已成功写入数据库，日期：{result['date']}")
            return True
        else:
            print(f"  [错误] Worker 返回状态码：{response.status_code}")
            print(f"  响应内容：{response.text}")
            return False

    except requests.exceptions.Timeout:
        print("  [错误] 发送超时，Worker 没有在 15 秒内响应")
        return False
    except Exception as e:
        print(f"  [错误] 发送失败：{e}")
        return False


# ============================================================
# 主函数入口
# ============================================================

def main() -> None:
    """
    脚本主入口：依次完成数据拉取、评分计算、结果输出与保存。
    """
    # 获取今日日期
    today = datetime.date.today().isoformat()

    # 读取 API Key
    api_key = get_api_key()
    if not api_key:
        print("[警告] 未检测到 FRED_API_KEY 环境变量，API 请求可能会失败。")
        print("       请先运行：export FRED_API_KEY=\"你的API Key\"\n")

    # 第一步：拉取所有数据
    all_data = fetch_all_series(api_key)

    # 第二步：计算各条件评分及 Regime 修正
    print("正在计算评分与 Regime 修正...")

    # 旧有指标
    score1, tips_yield    = score_condition1(all_data.get("DFII10", []))
    score2, hy_bps, fed_balance = score_condition2(all_data.get("BAMLH0A0HYM2", []), all_data.get("WALCL", []))
    score3, dollar_index  = score_condition3(all_data.get("DTWEXBGS", []))

    # 新增：Regime 与 波动率修正
    regime_mult, regime_name = compute_macro_regime(all_data.get("T10Y2Y", []), all_data.get("T10BIE", []))
    vol_mult, vol_status     = compute_volatility_correction(all_data.get("GVZ", []))

    # 第三步：判断综合信号
    signal = determine_signal(score1, score2, score3, regime_mult, vol_mult)

    # 第四步：打印结果
    print_results(
        today         = today,
        tips_yield    = tips_yield,
        hy_spread_bps = hy_bps,
        fed_balance   = fed_balance,
        dollar_index  = dollar_index,
        score1        = score1,
        score2        = score2,
        score3        = score3,
        regime_name   = regime_name,
        vol_status    = vol_status,
        signal        = signal,
    )

    # 第五步：保存 JSON 结果
    save_results(
        today         = today,
        tips_yield    = tips_yield,
        hy_spread_bps = hy_bps,
        fed_balance   = fed_balance,
        dollar_index  = dollar_index,
        score1        = score1,
        score2        = score2,
        score3        = score3,
        signal        = signal,
        regime_name   = regime_name,
        vol_status    = vol_status,
    )

    # 准备发送到 Worker 的最终字典
    result = {
        "date":              today,
        "condition1_score":  round(score1),
        "condition2_score":  round(score2),
        "condition3_score":  round(score3),
        "overall_signal":    signal,
        "tips_yield":        round(tips_yield, 4),
        "hy_spread":         round(hy_bps),
        "fed_balance":       round(fed_balance),
        "dollar_index":      round(dollar_index, 2),
        "regime":            regime_name,
        "vol_correction":    vol_status,
    }

    # 发送到 Worker 数据库
    send_to_worker(result)


if __name__ == "__main__":
    main()
