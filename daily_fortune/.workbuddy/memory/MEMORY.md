# 项目长期记忆

## 每日气运值MCP服务 (daily_fortune)
- **路径**: d:\code_work\MCPs\daily_fortune
- **技术栈**: Python 3.10+, FastMCP (mcp>=1.6.0), hatchling构建
- **算法**: 基于传统易学简化算法，5维度加权评分（日主与流日天干25%、五行环境生助30%、纳音互动15%、流年流月15%、五行平衡15%），线性映射到60~100分
- **MCP工具**: calculate_fortune(核心), get_wuxing_info, get_ganzhi_info
- **传输协议**: SSE(默认/推荐阿里百炼), STDIO, Streamable-HTTP
- **注意**: FastMCP构造函数不支持version参数，需用instructions代替
- **测试**: 35个单元测试全部通过
