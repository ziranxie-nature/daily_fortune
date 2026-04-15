"""
每日气运值 MCP Server

基于传统易学简化算法的每日气运值MCP服务，
支持被阿里百炼等平台的智能体通过SSE协议调用。

提供以下工具：
- calculate_fortune: 计算每日气运值
- get_wuxing_info: 查询五行属性信息
- get_ganzhi_info: 查询天干地支信息
"""

import json
import argparse
import logging
from datetime import datetime
from typing import Callable

import uvicorn
from starlette.types import ASGIApp, Receive, Scope, Send

from mcp.server.fastmcp import FastMCP

from .fortune import calculate_daily_fortune
from .wuxing import (
    calculate_sizhu, get_year_ganzhi, get_month_ganzhi,
    get_day_ganzhi, get_hour_ganzhi,
    TIAN_GAN, DI_ZHI, TIAN_GAN_WUXING, DI_ZHI_WUXING,
    TIAN_GAN_YINYANG, DI_ZHI_YINYANG,
    SHENG, KE, NAYIN_TABLE, NAYIN_WUXING,
    wuxing_relation, get_day_master_element,
    get_sizhu_wuxing_distribution,
)

logger = logging.getLogger(__name__)


class TrustAllHostsMiddleware:
    """
    将所有请求的 Host 头重写为 localhost，
    绕过 mcp 库的 DNS 重绑定保护（TransportSecurityMiddleware）。
    适用于部署在公网 IP 的 MCP 服务被百炼等平台直接访问的场景。
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            # 将 headers 中的 host 改为 localhost
            headers = dict(scope.get("headers", []))
            headers[b"host"] = b"localhost"
            scope["headers"] = list(headers.items())
        await self.app(scope, receive, send)


# 创建 FastMCP 服务器实例
mcp = FastMCP(
    name="每日气运值",
    instructions="基于传统易学简化算法，结合用户出生日期与当前日期，计算每日气运值分数（60~100分）。提供天干地支、五行生克、纳音等维度的气运分析。",
)


@mcp.tool()
def calculate_fortune(
    birth_date: str,
    birth_time: str | None = None,
    current_date: str | None = None,
) -> str:
    """
    计算每日气运值分数。结合用户出生日期时间和当前日期时间，基于传统易学简化算法
    （天干地支、五行生克、纳音五行等），计算出一个60~100分的气运值，并附带详细的
    五行分析、气运简评和开运建议。

    Args:
        birth_date: 用户出生日期，格式为 YYYY-MM-DD，例如 "1990-06-15"
        birth_time: 用户出生时间（24小时制小时数），格式为 HH，例如 "14" 表示下午2点。
                    不提供时默认为午时(12点)。
        current_date: 要查询的日期，格式为 YYYY-MM-DD。不提供时默认为今天。

    Returns:
        JSON格式的气运值计算结果，包含：
        - score: 气运分数(60~100)
        - day_master: 日主天干
        - day_master_element: 日主五行属性
        - birth_sizhu: 出生四柱八字
        - today_sizhu: 当日四柱八字
        - details: 各维度评分详情
        - summary: 气运简评
        - suggestions: 开运建议列表
    """
    try:
        result = calculate_daily_fortune(
            birth_date=birth_date,
            birth_time=birth_time,
            current_date=current_date,
        )
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    except ValueError as e:
        return json.dumps({
            "error": f"参数格式错误: {str(e)}",
            "hint": "birth_date 格式为 YYYY-MM-DD，birth_time 格式为 HH（0-23）",
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": f"计算失败: {str(e)}",
        }, ensure_ascii=False)


@mcp.tool()
def get_wuxing_info(element: str) -> str:
    """
    查询指定五行的详细信息，包括其相生关系、相克关系和基本属性。

    Args:
        element: 五行名称，可选值：木、火、土、金、水

    Returns:
        JSON格式的五行信息，包含：
        - element: 五行名称
        - generates: 该五行所生的五行
        - generated_by: 生该五行的五行
        - overcomes: 该五行所克的五行
        - overcome_by: 克该五行的五行
        - associated_gan: 关联天干
        - associated_zhi: 关联地支
        - direction: 方位
        - season: 季节
        - color: 代表色
    """
    valid_elements = ["木", "火", "土", "金", "水"]
    if element not in valid_elements:
        return json.dumps({
            "error": f"无效的五行: {element}",
            "valid_values": valid_elements,
        }, ensure_ascii=False)

    # 相生关系
    generates = SHENG[element]
    generated_by = next((k for k, v in SHENG.items() if v == element), "")

    # 相克关系
    overcomes = KE[element]
    overcome_by = next((k for k, v in KE.items() if v == element), "")

    # 关联天干
    associated_gan = [g for g, wx in TIAN_GAN_WUXING.items() if wx == element]

    # 关联地支
    associated_zhi = [z for z, wx in DI_ZHI_WUXING.items() if wx == element]

    # 扩展属性
    attributes = {
        "木": {"direction": "东方", "season": "春季", "color": "绿色/青色"},
        "火": {"direction": "南方", "season": "夏季", "color": "红色/紫色"},
        "土": {"direction": "中央", "season": "四季末", "color": "黄色/棕色"},
        "金": {"direction": "西方", "season": "秋季", "color": "白色/银色"},
        "水": {"direction": "北方", "season": "冬季", "color": "黑色/蓝色"},
    }

    info = {
        "element": element,
        "generates": generates,
        "generated_by": generated_by,
        "overcomes": overcomes,
        "overcome_by": overcome_by,
        "associated_gan": associated_gan,
        "associated_zhi": associated_zhi,
        **attributes.get(element, {}),
    }

    return json.dumps(info, ensure_ascii=False, indent=2)


@mcp.tool()
def get_ganzhi_info(
    birth_date: str,
    birth_time: str | None = None,
) -> str:
    """
    根据出生日期时间计算四柱八字（天干地支）信息，返回年柱、月柱、日柱、时柱
    的天干地支、五行属性、阴阳和纳音等详细信息。

    Args:
        birth_date: 出生日期，格式为 YYYY-MM-DD，例如 "1990-06-15"
        birth_time: 出生时间（24小时制小时数），格式为 HH，例如 "14"。
                    不提供时默认为午时(12点)。

    Returns:
        JSON格式的四柱八字信息，包含：
        - sizhu: 四柱八字（年月日时）
        - each_pillar: 各柱详细（天干、地支、五行、阴阳、纳音）
        - wuxing_distribution: 五行分布比例
        - day_master: 日主天干及五行
    """
    try:
        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
        if birth_time:
            birth_dt = birth_dt.replace(hour=int(birth_time))
        else:
            birth_dt = birth_dt.replace(hour=12)

        sizhu = calculate_sizhu(birth_dt)
        wuxing_dist = get_sizhu_wuxing_distribution(sizhu)
        day_master_wx = get_day_master_element(sizhu)

        pillars = []
        labels = ["年柱", "月柱", "日柱", "时柱"]
        for label, gz in zip(labels, sizhu.to_list()):
            pillars.append({
                "position": label,
                "ganzhi": str(gz),
                "gan": gz.gan,
                "zhi": gz.zhi,
                "gan_wuxing": gz.gan_wuxing,
                "zhi_wuxing": gz.zhi_wuxing,
                "gan_yinyang": gz.gan_yinyang,
                "zhi_yinyang": gz.zhi_yinyang,
                "nayin": gz.nayin,
                "nayin_wuxing": gz.nayin_wuxing,
            })

        result = {
            "birth_date": birth_date,
            "birth_time": birth_time or "12",
            "sizhu": str(sizhu),
            "each_pillar": pillars,
            "wuxing_distribution": {
                k: f"{v:.1%}" for k, v in wuxing_dist.items()
            },
            "day_master": {
                "gan": sizhu.day.gan,
                "element": day_master_wx,
            },
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
    except ValueError as e:
        return json.dumps({
            "error": f"参数格式错误: {str(e)}",
            "hint": "birth_date 格式为 YYYY-MM-DD，birth_time 格式为 HH（0-23）",
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": f"计算失败: {str(e)}",
        }, ensure_ascii=False)


def main():
    """启动MCP服务器"""
    parser = argparse.ArgumentParser(description="每日气运值MCP服务器")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio", "streamable-http"],
        default="sse",
        help="传输协议类型（默认: sse，推荐阿里百炼使用 sse）",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="服务器监听地址（默认: 0.0.0.0）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器监听端口（默认: 8000）",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return

    # SSE / Streamable-HTTP 模式：获取 ASGI app，用 uvicorn 启动
    try:
        if args.transport == "sse":
            app = mcp.sse_app()
        else:
            app = mcp.streamable_http_app()
    except AttributeError:
        # 旧版 mcp 库没有 sse_app / streamable_http_app 方法
        try:
            mcp.run(transport=args.transport, host=args.host, port=args.port)
        except TypeError:
            mcp.run(transport=args.transport)
        return

    # 包裹 TrustAllHostsMiddleware，绕过 mcp 内部的 Host 校验
    # 这样无论百炼用 IP 还是域名访问，都不会被 421 拦截
    wrapped_app = TrustAllHostsMiddleware(app)
    uvicorn.run(wrapped_app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
