# 每日气运值 MCP 服务

基于传统易学简化算法，结合用户出生日期与当前日期，计算每日气运值分数（60~100分）的 MCP (Model Context Protocol) 服务。

## ✨ 功能特性

- 🔮 **气运值计算**：基于天干地支、五行生克、纳音五行等多维度算法
- 🧮 **四柱八字推算**：年柱、月柱、日柱、时柱完整计算
- 🌊 **五行分析**：相生相克关系、五行平衡度、纳音互动
- 💡 **开运建议**：吉位方位、幸运色、贵人五行等个性化建议
- 🌐 **MCP 协议支持**：SSE / Streamable HTTP / STDIO 三种传输模式
- ☁️ **阿里百炼兼容**：可直接接入阿里百炼平台的智能体

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/daily_fortune.git
cd daily_fortune

# 安装依赖
pip install -e ".[dev]"
```

## 🚀 启动服务

### SSE 模式（推荐阿里百炼使用）

```bash
daily-fortune-mcp --transport sse --host 0.0.0.0 --port 8000
```

### STDIO 模式

```bash
daily-fortune-mcp --transport stdio
```

### Streamable HTTP 模式

```bash
daily-fortune-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## 🛠️ MCP 工具列表

### 1. calculate_fortune

计算每日气运值分数。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| birth_date | string | 是 | 出生日期，格式 YYYY-MM-DD |
| birth_time | string | 否 | 出生时间（0-23时），默认午时(12) |
| current_date | string | 否 | 查询日期，默认今天 |

**返回示例：**
```json
{
  "score": 82,
  "day_master": "丙",
  "day_master_element": "火",
  "birth_sizhu": "年:庚午 月:壬午 日:丙寅 时:甲未",
  "today_sizhu": "年:甲辰 月:丁卯 日:戊子 时:戊午",
  "details": {
    "day_gan_relation": 7.5,
    "wuxing_environment": 6.8,
    "nayin_interaction": 5.0,
    "year_month_influence": 7.5,
    "wuxing_balance": 8.0,
    "weights": {
      "day_gan_relation": "25%",
      "wuxing_environment": "30%",
      "nayin_interaction": "15%",
      "year_month_influence": "15%",
      "wuxing_balance": "15%"
    }
  },
  "summary": "【中吉】今日运势不错，稳步前行，可有所获。日主属火，如火般热情主动",
  "suggestions": [
    "今日吉位：南方",
    "今日幸运色：红色、紫色",
    "贵人五行：木（生我者）、火（同我者）",
    "今日宜：稳步推进、维护关系、处理日常事务"
  ]
}
```

### 2. get_wuxing_info

查询五行属性详细信息。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| element | string | 是 | 五行：木/火/土/金/水 |

### 3. get_ganzhi_info

根据出生日期查询四柱八字信息。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| birth_date | string | 是 | 出生日期，格式 YYYY-MM-DD |
| birth_time | string | 否 | 出生时间（0-23时），默认午时 |

## ☁️ 阿里百炼平台接入

### 📘 详细部署教程

👉 **[阿里云服务器部署指南（保姆级）](./DEPLOY.md)** — 从零开始，每一步都有完整命令，复制粘贴即可。

### 快速启动

**Docker 方式（推荐）：**
```bash
# 构建并启动
docker compose up -d

# 或者手动构建
docker build -t daily-fortune-mcp .
docker run -d --name daily-fortune-mcp --restart=always -p 8000:8000 daily-fortune-mcp
```

**直接部署：**
```bash
pip install -e .
daily-fortune-mcp --transport sse --host 0.0.0.0 --port 8000
```

### 阿里百炼配置

服务部署成功后，在阿里百炼平台的「MCP 工具」配置中添加：
- 传输协议：**SSE**
- 服务地址：`http://<你的服务器公网IP>:8000/sse`

## 🧮 算法说明

气运值计算基于以下五个维度，加权求和后映射到 60~100 分区间：

| 维度 | 权重 | 说明 |
|------|------|------|
| 日主与流日天干关系 | 25% | 天干五合、阴阳互补、五行生克 |
| 五行环境生助度 | 30% | 当日四柱各五行对日主的生助程度 |
| 纳音五行互动 | 15% | 出生日柱纳音与流日纳音的五行关系 |
| 流年流月影响 | 15% | 流年、流月天干对日主的影响 |
| 五行平衡度 | 15% | 日主五行在综合环境中的占比平衡性 |

## 🧪 测试

```bash
pytest tests/ -v
```

## 📄 许可证

MIT License
