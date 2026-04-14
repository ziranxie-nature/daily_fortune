"""
每日气运值计算引擎

基于传统易学简化算法，结合用户出生四柱与当日四柱，
计算每日气运值分数（60~100分）。

算法核心逻辑：
1. 计算用户出生四柱（年月日时）与当日四柱
2. 以日主五行为核心，分析当日五行环境对日主的生克关系
3. 综合考虑多个维度打分，映射到60~100区间

评分维度：
- 日主受生程度（当日五行对日主的生助）
- 日主与流日天干的关系
- 日主与流年天干的关系
- 日主与流月天干的关系
- 纳音五行互动
- 阴阳协调度
"""

from datetime import datetime
from dataclasses import dataclass

from .wuxing import (
    SiZhu, GanZhi,
    calculate_sizhu, get_day_ganzhi, get_month_ganzhi, get_year_ganzhi,
    get_hour_ganzhi,
    wuxing_relation, get_sizhu_wuxing_distribution,
    get_day_master_element, get_wuxing_strength,
    SHENG, KE, WUXING_INDEX,
)


@dataclass
class FortuneResult:
    """气运值计算结果"""
    score: int                     # 气运分数（60~100）
    birth_sizhu: SiZhu             # 出生四柱
    today_sizhu: SiZhu             # 当日四柱
    day_master: str                # 日主五行
    day_master_element: str        # 日主五行属性
    details: dict                  # 详细评分项
    summary: str                   # 气运简评
    suggestions: list[str]         # 开运建议

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "day_master": self.day_master,
            "day_master_element": self.day_master_element,
            "birth_sizhu": str(self.birth_sizhu),
            "today_sizhu": str(self.today_sizhu),
            "details": self.details,
            "summary": self.summary,
            "suggestions": self.suggestions,
        }


def _score_relation(relation: str) -> float:
    """
    根据五行关系给出评分贡献

    生我者（被生）= 大吉，我生者（生）= 小耗
    克我者（被克）= 大凶，我克者（克）= 小吉（得财）
    同我者（同）= 中吉
    """
    scores = {
        "被生": 8.0,   # 有贵人相助
        "同": 6.0,     # 平稳顺遂
        "克": 4.0,     # 主动出击，得财
        "生": 2.0,     # 付出消耗
        "被克": 0.0,   # 受阻受困
    }
    return scores.get(relation, 3.0)


def _calc_day_gan_score(birth_day_gan: str, today_day_gan: str) -> float:
    """
    计算日主天干与流日天干的关系评分

    天干五合加成：甲己合、乙庚合、丙辛合、丁壬合、戊癸合
    """
    wx1 = birth_day_gan  # 这里是完整天干
    # 天干五合
    wuhe = {
        "甲": "己", "己": "甲",
        "乙": "庚", "庚": "乙",
        "丙": "辛", "辛": "丙",
        "丁": "壬", "壬": "丁",
        "戊": "癸", "癸": "戊",
    }

    from .wuxing import TIAN_GAN_WUXING, TIAN_GAN_YINYANG

    base_score = _score_relation(
        wuxing_relation(TIAN_GAN_WUXING[birth_day_gan], TIAN_GAN_WUXING[today_day_gan])
    )

    # 天干五合加分
    if wuhe.get(birth_day_gan) == today_day_gan:
        base_score += 3.0  # 五合为大吉，贵人运

    # 阴阳协调
    if TIAN_GAN_YINYANG[birth_day_gan] != TIAN_GAN_YINYANG[today_day_gan]:
        base_score += 1.0  # 阴阳互补

    return min(base_score, 10.0)


def _calc_wuxing_environment_score(birth_sizhu: SiZhu, today_sizhu: SiZhu) -> float:
    """
    计算当日五行环境对日主的生助程度

    分析当日四柱中各五行对日主的生克关系，
    判断日主在今日五行环境中的强弱。
    """
    day_master_wx = get_day_master_element(birth_sizhu)

    # 当日各柱五行对日主的关系评分
    total_score = 0.0

    for gz in today_sizhu.to_list():
        # 天干对日主
        gan_rel = wuxing_relation(day_master_wx, gz.gan_wuxing)
        total_score += _score_relation(gan_rel) * 0.6  # 天干影响权重0.6

        # 地支对日主
        zhi_rel = wuxing_relation(day_master_wx, gz.zhi_wuxing)
        total_score += _score_relation(zhi_rel) * 0.4  # 地支影响权重0.4

    # 归一化到0~10分
    max_possible = 4 * (8.0 * 0.6 + 8.0 * 0.4)  # 全部"被生"的理论最大值
    normalized = (total_score / max_possible) * 10.0

    return min(max(normalized, 0.0), 10.0)


def _calc_nayin_score(birth_sizhu: SiZhu, today_sizhu: SiZhu) -> float:
    """
    计算纳音五行互动评分

    日柱纳音与流日纳音的五行关系
    """
    birth_nayin_wx = birth_sizhu.day.nayin_wuxing
    today_nayin_wx = today_sizhu.day.nayin_wuxing

    if not birth_nayin_wx or not today_nayin_wx:
        return 5.0  # 无纳音信息时取中值

    relation = wuxing_relation(birth_nayin_wx, today_nayin_wx)
    score = _score_relation(relation)

    # 映射到0~10
    return (score / 8.0) * 10.0


def _calc_year_month_score(birth_sizhu: SiZhu, today_sizhu: SiZhu) -> float:
    """
    计算流年、流月对日主的影响评分
    """
    from .wuxing import TIAN_GAN_WUXING

    day_master_wx = get_day_master_element(birth_sizhu)

    # 流年天干对日主
    year_rel = wuxing_relation(day_master_wx, TIAN_GAN_WUXING[today_sizhu.year.gan])
    year_score = _score_relation(year_rel)

    # 流月天干对日主
    month_rel = wuxing_relation(day_master_wx, TIAN_GAN_WUXING[today_sizhu.month.gan])
    month_score = _score_relation(month_rel)

    # 年占60%，月占40%
    combined = year_score * 0.6 + month_score * 0.4

    return (combined / 8.0) * 10.0


def _calc_balance_score(birth_sizhu: SiZhu, today_sizhu: SiZhu) -> float:
    """
    计算五行平衡度评分

    日主五行在当日五行环境中的占比情况：
    - 占比适中(15%~35%)为佳，日主得势
    - 占比过低(<10%)则日主偏弱
    - 占比过高(>50%)则过刚易折
    """
    day_master_wx = get_day_master_element(birth_sizhu)

    # 合并出生和当日五行分布
    birth_dist = get_sizhu_wuxing_distribution(birth_sizhu)
    today_dist = get_sizhu_wuxing_distribution(today_sizhu)

    # 综合五行环境（当日权重更大）
    combined = {wx: birth_dist[wx] * 0.3 + today_dist[wx] * 0.7 for wx in WUXING_INDEX}

    day_master_ratio = combined[day_master_wx]

    # 最佳区间 15%~35%，得分最高
    if 0.15 <= day_master_ratio <= 0.35:
        score = 10.0
    elif 0.10 <= day_master_ratio < 0.15 or 0.35 < day_master_ratio <= 0.40:
        score = 7.0
    elif 0.05 <= day_master_ratio < 0.10 or 0.40 < day_master_ratio <= 0.50:
        score = 4.0
    else:
        score = 2.0

    return score


def _generate_summary(score: int, day_master_wx: str, details: dict) -> str:
    """
    根据分数和详情生成气运简评
    """
    if score >= 92:
        level = "大吉"
        desc = "今日气运极佳，万事顺遂，宜大展宏图"
    elif score >= 85:
        level = "吉"
        desc = "今日运势上佳，贵人相助，宜积极行动"
    elif score >= 78:
        level = "中吉"
        desc = "今日运势不错，稳步前行，可有所获"
    elif score >= 72:
        level = "小吉"
        desc = "今日运势平稳，守成为主，小有收获"
    elif score >= 66:
        level = "平"
        desc = "今日运势平淡，谨慎行事，不宜冒进"
    else:
        level = "小凶"
        desc = "今日运势偏弱，宜静不宜动，蓄势待发"

    # 根据日主五行添加个性化描述
    wx_advice = {
        "木": "如草木般坚韧不拔",
        "火": "如火般热情主动",
        "土": "如大地般沉稳厚重",
        "金": "如金属般刚毅果断",
        "水": "如水般灵活变通",
    }

    return f"【{level}】{desc}。日主属{day_master_wx}，{wx_advice.get(day_master_wx, '')}"


def _generate_suggestions(score: int, day_master_wx: str, details: dict) -> list[str]:
    """
    根据评分生成开运建议
    """
    suggestions = []

    # 根据日主五行推荐方位
    wx_direction = {
        "木": "东方",
        "火": "南方",
        "土": "中央或本地",
        "金": "西方",
        "水": "北方",
    }
    suggestions.append(f"今日吉位：{wx_direction.get(day_master_wx, '中庭')}")

    # 根据日主五行推荐颜色
    wx_color = {
        "木": "绿色、青色",
        "火": "红色、紫色",
        "土": "黄色、棕色",
        "金": "白色、银色",
        "水": "黑色、蓝色",
    }
    suggestions.append(f"今日幸运色：{wx_color.get(day_master_wx, '黄色')}")

    # 根据日主五行推荐贵人五行
    wx_noble = {
        "木": "水（生我者）、木（同我者）",
        "火": "木（生我者）、火（同我者）",
        "土": "火（生我者）、土（同我者）",
        "金": "土（生我者）、金（同我者）",
        "水": "金（生我者）、水（同我者）",
    }
    suggestions.append(f"贵人五行：{wx_noble.get(day_master_wx, '')}")

    # 根据分数给行动建议
    if score >= 85:
        suggestions.append("今日宜：大胆决策、拓展人脉、启动新项目")
    elif score >= 72:
        suggestions.append("今日宜：稳步推进、维护关系、处理日常事务")
    else:
        suggestions.append("今日宜：修身养性、复盘总结、避免重大决策")

    # 根据详细评分给出针对性建议
    if details.get("day_gan_relation", 5) < 4:
        suggestions.append("流日天干与日主相克，注意人际关系中的摩擦")
    if details.get("wuxing_balance", 5) < 4:
        suggestions.append("五行偏枯，可通过着装颜色和环境方位调和")
    if details.get("nayin_interaction", 5) < 4:
        suggestions.append("纳音不和，今日宜低调行事，避免冲动消费")

    return suggestions[:6]  # 最多6条建议


def calculate_daily_fortune(
    birth_date: str,
    birth_time: str | None = None,
    current_date: str | None = None,
) -> FortuneResult:
    """
    计算每日气运值

    Args:
        birth_date: 出生日期，格式 "YYYY-MM-DD"
        birth_time: 出生时间，格式 "HH" (24小时制)，默认12时
        current_date: 当前日期，格式 "YYYY-MM-DD"，默认为今天

    Returns:
        FortuneResult: 气运值计算结果
    """
    # 解析出生日期
    birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
    if birth_time:
        birth_dt = birth_dt.replace(hour=int(birth_time))
    else:
        birth_dt = birth_dt.replace(hour=12)  # 默认午时

    # 解析当前日期
    if current_date:
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
    else:
        current_dt = datetime.now()

    # 计算出生四柱
    birth_sizhu = calculate_sizhu(birth_dt)

    # 计算当日四柱（以午时为代表时段，取日柱为主）
    today_sizhu = calculate_sizhu(current_dt.replace(hour=12))

    # 日主五行
    day_master_wx = get_day_master_element(birth_sizhu)
    day_master = birth_sizhu.day.gan

    # ============ 多维度评分 ============

    # 维度1：日主与流日天干关系（权重25%）
    day_gan_score = _calc_day_gan_score(birth_sizhu.day.gan, today_sizhu.day.gan)

    # 维度2：当日五行环境对日主的生助（权重30%）
    wuxing_env_score = _calc_wuxing_environment_score(birth_sizhu, today_sizhu)

    # 维度3：纳音五行互动（权重15%）
    nayin_score = _calc_nayin_score(birth_sizhu, today_sizhu)

    # 维度4：流年流月影响（权重15%）
    year_month_score = _calc_year_month_score(birth_sizhu, today_sizhu)

    # 维度5：五行平衡度（权重15%）
    balance_score = _calc_balance_score(birth_sizhu, today_sizhu)

    # 详细评分
    details = {
        "day_gan_relation": round(day_gan_score, 1),
        "wuxing_environment": round(wuxing_env_score, 1),
        "nayin_interaction": round(nayin_score, 1),
        "year_month_influence": round(year_month_score, 1),
        "wuxing_balance": round(balance_score, 1),
        "weights": {
            "day_gan_relation": "25%",
            "wuxing_environment": "30%",
            "nayin_interaction": "15%",
            "year_month_influence": "15%",
            "wuxing_balance": "15%",
        },
    }

    # ============ 加权总分 ============
    weighted_score = (
        day_gan_score * 0.25
        + wuxing_env_score * 0.30
        + nayin_score * 0.15
        + year_month_score * 0.15
        + balance_score * 0.15
    )

    # ============ 映射到60~100区间 ============
    # weighted_score 范围约为 0~10
    # 线性映射：0→60, 10→100
    # 公式：score = 60 + (weighted_score / 10) * 40
    final_score = int(60 + (weighted_score / 10.0) * 40)

    # 确保在范围内
    final_score = max(60, min(100, final_score))

    # 生成简评和建议
    summary = _generate_summary(final_score, day_master_wx, details)
    suggestions = _generate_suggestions(final_score, day_master_wx, details)

    return FortuneResult(
        score=final_score,
        birth_sizhu=birth_sizhu,
        today_sizhu=today_sizhu,
        day_master=day_master,
        day_master_element=day_master_wx,
        details=details,
        summary=summary,
        suggestions=suggestions,
    )
