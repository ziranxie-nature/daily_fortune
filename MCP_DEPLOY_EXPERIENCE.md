# MCP 服务部署开发经验（实战总结）

> 基于 daily_fortune MCP 服务在阿里云服务器 + 阿里百炼平台部署过程中的真实踩坑记录，适用于所有基于 FastMCP 的 MCP 服务开发。

---

## 一、Docker 部署篇

### 1.1 国内 Docker Hub 镜像拉取超时

**问题**：`docker build` 时 `FROM python:3.12-slim` 报 i/o timeout，国内服务器无法直连 docker.io。

**方案**：在服务器上配置 `/etc/docker/daemon.json`，添加国内镜像加速：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://docker.m.daocloud.io"
  ]
}
```

配置后执行 `sudo systemctl daemon-reload && sudo systemctl restart docker`。

**注意**：不要用 `registry.cn-hangzhou.aliyuncs.com/library/python:3.12-slim` 替代，该镜像已不再公开，会报 authorization failed。Dockerfile 中保持 `FROM python:3.12-slim`，靠 daemon.json 代理拉取。

### 1.2 docker compose vs docker-compose

**问题**：新版 Docker（v2+）自带 `docker compose` 插件（空格），旧版独立工具 `docker-compose`（连字符）可能未安装。

**判断方法**：
```bash
docker compose version    # 新版，能执行就是新版
docker-compose version    # 旧版，command not found 说明没装
```

**建议**：所有文档和命令统一用 `docker compose`（空格版），符合 Docker 官方当前推荐。

### 1.3 镜像缓存导致代码未更新

**问题**：修改代码后 `docker compose up` 不生效，容器里跑的还是旧代码。

**原因**：`docker compose up` 默认不会重新 build，直接用已有镜像。

**解决**：每次改代码后必须强制重建：
```bash
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```

### 1.4 端口冲突排查

**问题**：容器启动报 `address already in use`。

**排查**：
```bash
sudo ss -tlnp | grep <端口号>
```

**建议**：Web 服务约定俗成用 8000 端口，如果服务器上已有网站占用，MCP 服务改用其他端口（如 8890），只在 docker-compose.yml 的端口映射中改外部端口，容器内部仍用 8000。

---

## 二、FastMCP / mcp SDK 篇

### 2.1 HTTP 421 Misdirected Request（最重要）

**问题**：公网 IP 访问 MCP SSE 端点返回 421，但 localhost 访问正常。

**根因**：mcp 1.27.0 的 `FastMCP` 默认 `host="127.0.0.1"`，检测到 host 为 localhost 会自动开启 DNS rebinding protection（`TransportSecurityMiddleware`），只放行 `localhost/127.0.0.1` 的 Host 头，其他一律 421。

**正确修复**：在创建 FastMCP 时传入两个参数：

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    name="服务名",
    host="0.0.0.0",  # 不触发自动保护
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False  # 显式关闭
    ),
)
```

**失败的方案（不要重复踩坑）**：

| 方案 | 为何失败 |
|------|---------|
| 外层 ASGI Middleware 改 Host 头 | TransportSecurityMiddleware 挂在 sse_app 内部，外层 middleware 改 scope headers 时序不对 |
| monkey-patch TransportSecurityMiddleware | FastMCP 初始化时会根据 host 参数重新创建 security 实例，patch 被覆盖 |
| 只传 `host="0.0.0.0"` 不传 transport_security | 某些版本可能仍会默认开启保护，不够保险 |

**诊断方法**：在容器内部直接模拟公网 Host 头请求，排除 Nginx 等中间层干扰：
```bash
sudo docker exec <容器名> python3 -c "
import urllib.request
req = urllib.request.Request('http://127.0.0.1:8000/sse')
req.add_header('Host', '<公网IP>:<端口>')
try:
    resp = urllib.request.urlopen(req, timeout=5)
    print('Status:', resp.status)
except urllib.error.HTTPError as e:
    print('Error:', e.code, e.reason)
    print(e.read().decode())
"
```

### 2.2 FastMCP.run() TypeError

**问题**：`mcp.run(transport="sse", host="0.0.0.0", port=8000)` 报 `got an unexpected keyword argument 'host'`。

**原因**：旧版 mcp 库的 `FastMCP.run()` 方法不支持 `host`/`port` 参数。

**兼容写法**：
```python
try:
    app = mcp.sse_app()
except AttributeError:
    # 旧版没有 sse_app，用 run()
    try:
        mcp.run(transport="sse", host="0.0.0.0", port=8000)
    except TypeError:
        mcp.run(transport="sse")
    return

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.3 FastMCP 构造参数注意事项

- **`version` 参数**：mcp 1.27.0 的 FastMCP 不支持 `version` 参数，用 `instructions` 代替传递服务描述。
- **`host` 参数**：务必传 `"0.0.0.0"` 而非默认的 `"127.0.0.1"`，否则公网访问会触发安全保护。
- **pyproject.toml 中的版本声明**：用 `dependencies = ["mcp>=1.27.0"]` 确保拉到新版 SDK。

---

## 三、阿里百炼平台接入篇

### 3.1 推荐接入方式：脚本部署

百炼有四种 MCP 接入方式，推荐用**脚本部署**，填入 JSON 配置：

```json
{
  "mcpServers": {
    "daily-fortune": {
      "url": "http://47.99.175.242:8890/sse",
      "type": "sse"
    }
  }
}
```

### 3.2 百炼报错定位

百炼报 421 时，错误信息可能不完整。建议：
1. 先在服务器本地 `curl -v --max-time 5 http://localhost:8890/sse` 确认 localhost 通
2. 再 `curl -v --max-time 5 http://47.99.175.242:8890/sse` 确认公网通
3. 用容器内诊断命令（见 2.1）确认是 mcp 还是中间层问题

---

## 四、通用排障流程

遇到 MCP 服务访问问题时，按此顺序排查：

```
1. 容器是否在运行？ → sudo docker ps
2. 容器日志有无报错？ → sudo docker compose logs -f
3. 容器内服务是否正常？ → sudo docker exec <容器> curl http://localhost:8000/sse
4. 宿主机能否访问？ → curl http://localhost:8890/sse
5. 公网能否访问？ → curl http://<公网IP>:8890/sse
6. 是否 Nginx/防火墙拦截？ → sudo ss -tlnp | grep 8890
7. 是否 mcp SDK Host 校验？ → 容器内模拟公网 Host 头请求
```

---

## 五、项目配置检查清单

部署前确认以下文件已正确配置：

- [ ] `pyproject.toml`：`mcp>=1.27.0`、`uvicorn` 在 dependencies 中
- [ ] `server.py`：FastMCP 传 `host="0.0.0.0"` + `transport_security=TransportSecuritySettings(...)`
- [ ] `Dockerfile`：`FROM python:3.12-slim`，pip 用阿里云镜像
- [ ] `docker-compose.yml`：端口映射正确，`restart: always`
- [ ] 服务器 `/etc/docker/daemon.json`：已配置国内镜像加速
- [ ] 防火墙/安全组：公网端口已放行
