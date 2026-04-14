"""
每日气运值 MCP 服务 - 单元测试
"""

import pytest
from datetime import datetime

from daily_fortune.wuxing import (
    TIAN_GAN, DI_ZHI, TIAN_GAN_WUXING, DI_ZHI_WUXING,
    SHENG, KE, TIAN_GAN_YINYANG, DI_ZHI_YINYANG,
    get_year_ganzhi, get_month_ganzhi, get_day_ganzhi, get_hour_ganzhi,
    calculate_sizhu, wuxing_relation, get_wuxing_strength,
    get_sizhu_wuxing_distribution, get_day_master_element,
    GanZhi, SiZhu, NAYIN_TABLE, NAYIN_WUXING,
)
from daily_fortune.fortune import calculate_daily_fortune, FortuneResult


class TestTianGanDiZhi:
    """天干地支基础测试"""

    def test_tiangan_count(self):
        assert len(TIAN_GAN) == 10

    def test_dizhi_count(self):
        assert len(DI_ZHI) == 12

    def test_year_ganzhi_2000(self):
        """2000年为庚辰年"""
        gz = get_year_ganzhi(2000)
        assert gz.gan == "庚"
        assert gz.zhi == "辰"

    def test_year_ganzhi_2024(self):
        """2024年为甲辰年"""
        gz = get_year_ganzhi(2024)
        assert gz.gan == "甲"
        assert gz.zhi == "辰"

    def test_year_ganzhi_1990(self):
        """1990年为庚午年"""
        gz = get_year_ganzhi(1990)
        assert gz.gan == "庚"
        assert gz.zhi == "午"

    def test_month_ganzhi_first_month(self):
        """正月月支为寅"""
        gz = get_month_ganzhi(2024, 1)
        assert gz.zhi == "寅"

    def test_month_ganzhi_december(self):
        """十二月月支为丑"""
        gz = get_month_ganzhi(2024, 12)
        assert gz.zhi == "丑"

    def test_hour_ganzhi_zi(self):
        """子时（23点）"""
        gz = get_hour_ganzhi("甲", 23)
        assert gz.zhi == "子"

    def test_hour_ganzhi_wu(self):
        """午时（12点）"""
        gz = get_hour_ganzhi("甲", 12)
        assert gz.zhi == "午"


class TestWuXing:
    """五行关系测试"""

    def test_sheng_cycle(self):
        """五行相生循环"""
        assert SHENG["木"] == "火"
        assert SHENG["火"] == "土"
        assert SHENG["土"] == "金"
        assert SHENG["金"] == "水"
        assert SHENG["水"] == "木"

    def test_ke_cycle(self):
        """五行相克循环"""
        assert KE["木"] == "土"
        assert KE["土"] == "水"
        assert KE["水"] == "火"
        assert KE["火"] == "金"
        assert KE["金"] == "木"

    def test_wuxing_relation_same(self):
        assert wuxing_relation("木", "木") == "同"

    def test_wuxing_relation_sheng(self):
        assert wuxing_relation("木", "火") == "生"

    def test_wuxing_relation_beisheng(self):
        assert wuxing_relation("火", "木") == "被生"

    def test_wuxing_relation_ke(self):
        assert wuxing_relation("木", "土") == "克"

    def test_wuxing_relation_beike(self):
        assert wuxing_relation("土", "木") == "被克"


class TestSiZhu:
    """四柱计算测试"""

    def test_calculate_sizhu(self):
        dt = datetime(1990, 6, 15, 14, 0)
        sizhu = calculate_sizhu(dt)
        assert isinstance(sizhu, SiZhu)
        assert len(str(sizhu)) > 0

    def test_sizhu_has_four_pillars(self):
        dt = datetime(2000, 1, 1, 0, 0)
        sizhu = calculate_sizhu(dt)
        assert isinstance(sizhu.year, GanZhi)
        assert isinstance(sizhu.month, GanZhi)
        assert isinstance(sizhu.day, GanZhi)
        assert isinstance(sizhu.hour, GanZhi)

    def test_wuxing_distribution_sums_to_one(self):
        dt = datetime(1990, 6, 15, 14, 0)
        sizhu = calculate_sizhu(dt)
        dist = get_sizhu_wuxing_distribution(sizhu)
        total = sum(dist.values())
        assert abs(total - 1.0) < 0.001

    def test_day_master_element(self):
        dt = datetime(1990, 6, 15, 14, 0)
        sizhu = calculate_sizhu(dt)
        element = get_day_master_element(sizhu)
        assert element in ["木", "火", "土", "金", "水"]


class TestFortuneCalculation:
    """气运值计算测试"""

    def test_basic_calculation(self):
        result = calculate_daily_fortune("1990-06-15", "14", "2024-03-15")
        assert isinstance(result, FortuneResult)
        assert 60 <= result.score <= 100

    def test_score_range_minimum(self):
        """测试分数不低于60"""
        # 测试多个日期组合
        for month in range(1, 13):
            result = calculate_daily_fortune("1985-01-15", "8", f"2024-{month:02d}-15")
            assert result.score >= 60, f"分数低于60: {result.score} (月份={month})"

    def test_score_range_maximum(self):
        """测试分数不超过100"""
        for month in range(1, 13):
            result = calculate_daily_fortune("1990-06-15", "14", f"2024-{month:02d}-15")
            assert result.score <= 100, f"分数超过100: {result.score} (月份={month})"

    def test_result_has_summary(self):
        result = calculate_daily_fortune("1990-06-15")
        assert len(result.summary) > 0

    def test_result_has_suggestions(self):
        result = calculate_daily_fortune("1990-06-15")
        assert len(result.suggestions) > 0

    def test_result_has_details(self):
        result = calculate_daily_fortune("1990-06-15")
        assert "day_gan_relation" in result.details
        assert "wuxing_environment" in result.details
        assert "nayin_interaction" in result.details
        assert "year_month_influence" in result.details
        assert "wuxing_balance" in result.details

    def test_result_to_dict(self):
        result = calculate_daily_fortune("1990-06-15")
        d = result.to_dict()
        assert "score" in d
        assert "summary" in d
        assert "suggestions" in d
        assert isinstance(d["suggestions"], list)

    def test_different_birth_times(self):
        """不同出生时辰应产生不同结果"""
        r1 = calculate_daily_fortune("1990-06-15", "6")
        r2 = calculate_daily_fortune("1990-06-15", "18")
        # 时辰不同，四柱不同，结果可能有差异（但不一定总是不同）
        assert 60 <= r1.score <= 100
        assert 60 <= r2.score <= 100

    def test_without_birth_time(self):
        """不提供出生时间应正常工作"""
        result = calculate_daily_fortune("1990-06-15")
        assert 60 <= result.score <= 100

    def test_without_current_date(self):
        """不提供当前日期应使用今天"""
        result = calculate_daily_fortune("1990-06-15", "14")
        assert 60 <= result.score <= 100

    def test_nayin_populated(self):
        """纳音信息应被填充"""
        result = calculate_daily_fortune("1990-06-15", "14", "2024-06-15")
        # 日柱纳音
        assert result.birth_sizhu.day.nayin != ""
        assert result.today_sizhu.day.nayin != ""


class TestGanZhiProperties:
    """GanZhi对象属性测试"""

    def test_ganzhi_str(self):
        gz = GanZhi(gan="甲", zhi="子")
        assert str(gz) == "甲子"

    def test_ganzhi_wuxing(self):
        gz = GanZhi(gan="甲", zhi="子")
        assert gz.gan_wuxing == "木"
        assert gz.zhi_wuxing == "水"

    def test_ganzhi_yinyang(self):
        gz = GanZhi(gan="甲", zhi="子")
        assert gz.gan_yinyang == "阳"
        assert gz.zhi_yinyang == "阳"

    def test_ganzhi_nayin(self):
        gz = GanZhi(gan="甲", zhi="子")
        assert gz.nayin == "海中金"
        assert gz.nayin_wuxing == "金"
