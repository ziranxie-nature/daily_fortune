"""
天干地支与五行算法模块

实现传统易学中天干地支的基本计算，包括：
- 年柱、月柱、日柱、时柱的天干地支推算
- 五行属性映射
- 五行生克关系判定
- 纳音五行查表
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

# ============ 基础常量 ============

# 十天干
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 十二地支
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干五行映射
TIAN_GAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 地支五行映射
DI_ZHI_WUXING = {
    "子": "水", "丑": "土",
    "寅": "木", "卯": "木",
    "辰": "土", "巳": "火",
    "午": "火", "未": "土",
    "申": "金", "酉": "金",
    "戌": "土", "亥": "水",
}

# 天干阴阳
TIAN_GAN_YINYANG = {
    "甲": "阳", "乙": "阴",
    "丙": "阳", "丁": "阴",
    "戊": "阳", "己": "阴",
    "庚": "阳", "辛": "阴",
    "壬": "阳", "癸": "阴",
}

# 地支阴阳
DI_ZHI_YINYANG = {
    "子": "阳", "丑": "阴",
    "寅": "阳", "卯": "阴",
    "辰": "阳", "巳": "阴",
    "午": "阳", "未": "阴",
    "申": "阳", "酉": "阴",
    "戌": "阳", "亥": "阴",
}

# 五行生克关系
# 相生：木生火、火生土、土生金、金生水、水生木
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 相克：木克土、土克水、水克火、火克金、金克木
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 五行序号（用于数值计算）
WUXING_INDEX = {"木": 0, "火": 1, "土": 2, "金": 3, "水": 4}

# 六十甲子纳音表
NAYIN_TABLE = {
    ("甲", "子"): "海中金", ("乙", "丑"): "海中金",
    ("丙", "寅"): "炉中火", ("丁", "卯"): "炉中火",
    ("戊", "辰"): "大林木", ("己", "巳"): "大林木",
    ("庚", "午"): "路旁土", ("辛", "未"): "路旁土",
    ("壬", "申"): "剑锋金", ("癸", "酉"): "剑锋金",
    ("甲", "戌"): "山头火", ("乙", "亥"): "山头火",
    ("丙", "子"): "涧下水", ("丁", "丑"): "涧下水",
    ("戊", "寅"): "城头土", ("己", "卯"): "城头土",
    ("庚", "辰"): "白蜡金", ("辛", "巳"): "白蜡金",
    ("壬", "午"): "杨柳木", ("癸", "未"): "杨柳木",
    ("甲", "申"): "泉中水", ("乙", "酉"): "泉中水",
    ("丙", "戌"): "屋上土", ("丁", "亥"): "屋上土",
    ("戊", "子"): "霹雳火", ("己", "丑"): "霹雳火",
    ("庚", "寅"): "松柏木", ("辛", "卯"): "松柏木",
    ("壬", "辰"): "长流水", ("癸", "巳"): "长流水",
    ("甲", "午"): "砂石金", ("乙", "未"): "砂石金",
    ("丙", "申"): "山下火", ("丁", "酉"): "山下火",
    ("戊", "戌"): "平地木", ("己", "亥"): "平地木",
    ("庚", "子"): "壁上土", ("辛", "丑"): "壁上土",
    ("壬", "寅"): "金箔金", ("癸", "卯"): "金箔金",
    ("甲", "辰"): "覆灯火", ("乙", "巳"): "覆灯火",
    ("丙", "午"): "天河水", ("丁", "未"): "天河水",
    ("戊", "申"): "大驿土", ("己", "酉"): "大驿土",
    ("庚", "戌"): "钗钏金", ("辛", "亥"): "钗钏金",
    ("壬", "子"): "桑柘木", ("癸", "丑"): "桑柘木",
    ("甲", "寅"): "大溪水", ("乙", "卯"): "大溪水",
    ("丙", "辰"): "沙中土", ("丁", "巳"): "沙中土",
    ("戊", "午"): "天上火", ("己", "未"): "天上火",
    ("庚", "申"): "石榴木", ("辛", "酉"): "石榴木",
    ("壬", "戌"): "大海水", ("癸", "亥"): "大海水",
}

# 纳音五行映射
NAYIN_WUXING = {
    "海中金": "金", "炉中火": "火", "大林木": "木", "路旁土": "土", "剑锋金": "金",
    "山头火": "火", "涧下水": "水", "城头土": "土", "白蜡金": "金", "杨柳木": "木",
    "泉中水": "水", "屋上土": "土", "霹雳火": "火", "松柏木": "木", "长流水": "水",
    "砂石金": "金", "山下火": "火", "平地木": "木", "壁上土": "土", "金箔金": "金",
    "覆灯火": "火", "天河水": "水", "大驿土": "土", "钗钏金": "金", "桑柘木": "木",
    "大溪水": "水", "沙中土": "土", "天上火": "火", "石榴木": "木", "大海水": "水",
}


# ============ 数据结构 ============

@dataclass
class GanZhi:
    """天干地支对"""
    gan: str  # 天干
    zhi: str  # 地支

    @property
    def gan_wuxing(self) -> str:
        """天干五行"""
        return TIAN_GAN_WUXING[self.gan]

    @property
    def zhi_wuxing(self) -> str:
        """地支五行"""
        return DI_ZHI_WUXING[self.zhi]

    @property
    def gan_yinyang(self) -> str:
        """天干阴阳"""
        return TIAN_GAN_YINYANG[self.gan]

    @property
    def zhi_yinyang(self) -> str:
        """地支阴阳"""
        return DI_ZHI_YINYANG[self.zhi]

    @property
    def nayin(self) -> str:
        """纳音"""
        return NAYIN_TABLE.get((self.gan, self.zhi), "")

    @property
    def nayin_wuxing(self) -> str:
        """纳音五行"""
        nayin = self.nayin
        return NAYIN_WUXING.get(nayin, "") if nayin else ""

    def __str__(self) -> str:
        return f"{self.gan}{self.zhi}"


@dataclass
class SiZhu:
    """四柱（年月日时）"""
    year: GanZhi
    month: GanZhi
    day: GanZhi
    hour: GanZhi

    def to_list(self) -> list[GanZhi]:
        return [self.year, self.month, self.day, self.hour]

    def __str__(self) -> str:
        return f"年:{self.year} 月:{self.month} 日:{self.day} 时:{self.hour}"


# ============ 核心计算函数 ============

def get_year_ganzhi(year: int) -> GanZhi:
    """
    计算年柱天干地支

    以公历年份计算，年份以立春为界（此处简化为按公历年份计算）。
    天干 = (年份 - 4) % 10
    地支 = (年份 - 4) % 12
    """
    gan_idx = (year - 4) % 10
    zhi_idx = (year - 4) % 12
    return GanZhi(gan=TIAN_GAN[gan_idx], zhi=DI_ZHI[zhi_idx])


def get_month_ganzhi(year: int, month: int) -> GanZhi:
    """
    计算月柱天干地支（简化版）

    月支固定：正月寅、二月卯...十一月子、十二月丑
    月干根据年干推算（五虎遁月法）：
    - 甲己年起丙寅月
    - 乙庚年起戊寅月
    - 丙辛年起庚寅月
    - 丁壬年起壬寅月
    - 戊癸年起甲寅月
    """
    # 月支：正月=寅(2)，依次递增
    zhi_idx = (month + 1) % 12  # 正月=寅=2 → (1+1)%12=2 ✓
    # 但实际上月份1对应寅(2)，月份2对应卯(3)...月份11对应子(0)，月份12对应丑(1)
    zhi_idx = (month + 1) % 12

    # 年干决定月干起始
    year_gan_idx = (year - 4) % 10
    # 五虎遁：甲己→丙(2)，乙庚→戊(4)，丙辛→庚(6)，丁壬→壬(8)，戊癸→甲(0)
    start_gan_map = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0, 5: 2, 6: 4, 7: 6, 8: 8, 9: 0}
    start_gan = start_gan_map[year_gan_idx]

    # 月干 = 起始干 + (月份数-1)的偏移
    # 正月干=起始干，二月干=起始干+1...
    gan_idx = (start_gan + month - 1) % 10

    return GanZhi(gan=TIAN_GAN[gan_idx], zhi=DI_ZHI[zhi_idx])


def get_day_ganzhi(year: int, month: int, day: int) -> GanZhi:
    """
    计算日柱天干地支

    使用蔡勒公式的变体，基于已知基准日推算。
    基准：2000年1月1日为甲子日（简化计算，实际需查历表）
    
    注意：此处采用简化的儒略日数算法，确保日常使用精度。
    """
    # 计算儒略日数
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    # 以已知基准日推算干支
    # 2000年1月7日为甲子日（儒略日 2451551）
    # 实际验证调整：用更准确的基准
    base_jd = 2451551  # 2000年1月7日
    offset = (jd - base_jd) % 60

    gan_idx = offset % 10
    zhi_idx = offset % 12

    return GanZhi(gan=TIAN_GAN[gan_idx], zhi=DI_ZHI[zhi_idx])


def get_hour_ganzhi(day_gan: str, hour: int) -> GanZhi:
    """
    计算时柱天干地支

    时支固定：23-1子、1-3丑、3-5寅...21-23亥
    时干根据日干推算（五鼠遁时法）：
    - 甲己日起甲子时
    - 乙庚日起丙子时
    - 丙辛日起戊子时
    - 丁壬日起庚子时
    - 戊癸日起壬子时
    """
    # 时支：0时=子(0)，2时=丑(1)...22时=子(0)
    # 23时开始算下一日的子时
    if hour == 23:
        zhi_idx = 0
    else:
        zhi_idx = (hour + 1) // 2

    # 日干决定时干起始
    day_gan_idx = TIAN_GAN.index(day_gan)
    # 五鼠遁：甲己→甲(0)，乙庚→丙(2)，丙辛→戊(4)，丁壬→庚(6)，戊癸→壬(8)
    start_gan_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 0, 6: 2, 7: 4, 8: 6, 9: 8}
    start_gan = start_gan_map[day_gan_idx]

    # 时干偏移
    gan_idx = (start_gan + zhi_idx) % 10

    return GanZhi(gan=TIAN_GAN[gan_idx], zhi=DI_ZHI[zhi_idx])


def calculate_sizhu(birth_dt: datetime) -> SiZhu:
    """
    计算四柱八字

    Args:
        birth_dt: 出生日期时间

    Returns:
        SiZhu: 四柱对象
    """
    year = birth_dt.year
    month = birth_dt.month
    day = birth_dt.day
    hour = birth_dt.hour

    year_gz = get_year_ganzhi(year)
    month_gz = get_month_ganzhi(year, month)
    day_gz = get_day_ganzhi(year, month, day)
    hour_gz = get_hour_ganzhi(day_gz.gan, hour)

    return SiZhu(year=year_gz, month=month_gz, day=day_gz, hour=hour_gz)


def wuxing_relation(wx1: str, wx2: str) -> str:
    """
    判断两个五行之间的关系

    Returns:
        "生": wx1生wx2
        "被生": wx1被wx2生
        "克": wx1克wx2
        "被克": wx1被wx2克
        "同": wx1与wx2相同
    """
    if wx1 == wx2:
        return "同"
    if SHENG[wx1] == wx2:
        return "生"
    if SHENG[wx2] == wx1:
        return "被生"
    if KE[wx1] == wx2:
        return "克"
    if KE[wx2] == wx1:
        return "被克"
    return "无关"


def get_wuxing_strength(ganzhi: GanZhi) -> dict[str, int]:
    """
    计算一个干支中各五行的力量值

    天干力量 > 地支力量
    同属性叠加
    """
    strength: dict[str, int] = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    strength[ganzhi.gan_wuxing] += 6  # 天干主气
    strength[ganzhi.zhi_wuxing] += 4  # 地支主气
    return strength


def get_sizhu_wuxing_distribution(sizhu: SiZhu) -> dict[str, float]:
    """
    计算四柱五行分布比例

    Returns:
        各五行占比（0~1之间）
    """
    total_strength: dict[str, int] = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}

    for gz in sizhu.to_list():
        s = get_wuxing_strength(gz)
        for wx, val in s.items():
            total_strength[wx] += val

    total = sum(total_strength.values()) or 1
    return {wx: val / total for wx, val in total_strength.items()}


def get_day_master_element(sizhu: SiZhu) -> str:
    """
    获取日主五行（日柱天干的五行属性）
    这是八字分析的核心——"日主"代表命主自身
    """
    return sizhu.day.gan_wuxing
