# 🚀 阿里云服务器部署指南（保姆级）

> 本文档手把手教你把「每日气运值 MCP 服务」部署到阿里云服务器上，并接入阿里百炼平台。
> 每一步都有完整命令，你只需要**复制粘贴**即可。

---

## 📋 前置要求

| 项目 | 最低要求 |
|------|---------|
| 阿里云 ECS 实例 | 1核1G 即可（本服务非常轻量） |
| 操作系统 | Ubuntu 22.04 / 20.04（推荐） |
| 公网 IP | 需要有，阿里百炼需要能访问到 |
| 本地工具 | SSH 客户端（如 Windows Terminal / PuTTY） |

> 💡 **端口说明**：本服务默认使用 **8890** 端口（避免与常见的 80/443/8000 端口冲突）。
> 容器内部仍然监听 8000，通过 Docker 映射到服务器的 8890。

---

## 方案选择

提供两种部署方案，**推荐方案一（Docker）**，最省心：

| 方案 | 优点 | 缺点 |
|------|------|------|
| 方案一：Docker 部署 ⭐ | 隔离干净、一条命令启动、升级方便 | 需先装 Docker |
| 方案二：直接部署 | 不需要 Docker | 需手动装 Python、配虚拟环境、配进程守护 |

---

## 方案一：Docker 部署（推荐）

### 第1步：SSH 连接到你的阿里云服务器

```bash
# 把 <你的服务器IP> 替换成实际的公网 IP
ssh root@<你的服务器IP>

# 如果用的非 root 用户（比如 ecs-user）：
ssh ecs-user@<你的服务器IP>
```

> 💡 如果是 Windows 用户，在 Windows Terminal / PowerShell 中直接运行上面的命令即可。
> 首次连接会问你是否信任服务器，输入 `yes` 回车。

### 第2步：安装 Docker

```bash
# 更新包管理器
sudo apt-get update

# 安装 Docker
sudo apt-get install -y docker.io

# 启动 Docker 并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装成功（看到版本号就对了）
docker --version
```

> ✅ 输出示例：`Docker version 24.0.7, build afdd53b`

### 第2.5步：配置 Docker 镜像加速（国内服务器必做！）

> ⚠️ **国内服务器拉 Docker Hub 镜像会超时或鉴权失败，必须配置国内镜像源！**
> 如果你遇到 `i/o timeout`、`DeadlineExceeded` 或 `authorization failed` 错误，就是这个问题。

```bash
# 创建 Docker 配置目录（如果不存在）
sudo mkdir -p /etc/docker

# 写入镜像加速配置（多源备份，一个不通自动切下一个）
sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://docker.m.daocloud.io"
  ]
}
EOF

# 重启 Docker 使配置生效
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置是否生效（看到 Registry Mirrors 里有地址就对了）
docker info | grep -A 5 "Registry Mirrors"
```

> ✅ 输出应包含上面配置的镜像地址。

### 第3步：上传项目代码到服务器

在你**本地电脑**上操作（不是服务器上）：

```bash
# 方式A：如果你的代码在 GitHub/Gitee 上
ssh root@<你的服务器IP> "git clone https://github.com/你的用户名/daily_fortune.git /opt/daily_fortune"

# 方式B：如果没有 Git 仓库，用 scp 上传整个项目文件夹
# 先在本地进入项目上级目录，然后执行：
scp -r daily_fortune root@<你的服务器IP>:/opt/
```

> 💡 如果你是 Windows 用户，可以用 WinSCP 等图形化工具把 `daily_fortune` 文件夹上传到服务器的 `/opt/` 目录。

### 第4步：构建 Docker 镜像

回到**服务器上**操作：

```bash
cd /opt/daily_fortune

# 先单独测试能否拉取基础镜像（确认镜像加速生效）
sudo docker pull python:3.12-slim

# 构建镜像（第一次大约需要 1-2 分钟）
sudo docker build -t daily-fortune-mcp:latest .
```

> ✅ 看到 `Successfully built xxxxx` 和 `Successfully tagged daily-fortune-mcp:latest` 就成功了。
> 如果 `docker pull` 超时，说明镜像加速没配好，回到第2.5步检查。

### 第5步：启动 Docker 容器

```bash
# 停掉可能存在的旧容器（首次部署不需要，但以后更新时用）
sudo docker rm -f daily-fortune-mcp 2>/dev/null

# 启动容器（8890 是服务器对外端口，8000 是容器内部端口）
sudo docker run -d \
  --name daily-fortune-mcp \
  --restart=always \
  -p 8890:8000 \
  daily-fortune-mcp:latest
```

**参数解释：**
- `-d`：后台运行
- `--name`：容器名称，方便后续管理
- `--restart=always`：服务器重启后自动启动容器
- `-p 8890:8000`：把容器内的 8000 端口映射到服务器的 **8890** 端口

> ⚠️ **如果 8890 也被占用了**，报错 `address already in use`，可以换成其他端口，比如 `-p 9000:8000`，把下面的 8890 都替换成 9000 即可。

### 第6步：验证服务是否正常

```bash
# 查看容器状态（STATUS 应该是 Up）
sudo docker ps

# 查看服务日志
sudo docker logs daily-fortune-mcp

# 用 curl 测试 SSE 端点
curl -N http://localhost:8890/sse
```

> ✅ 如果 `docker ps` 显示容器状态为 `Up`，并且 `curl` 有响应，说明服务启动成功！

### 第7步：配置阿里云安全组（重要！）

阿里百炼需要从公网访问你的服务，必须在安全组中放行 **8890** 端口：

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 进入 **云服务器 ECS** → 找到你的实例
3. 点击 **安全组** → **配置规则** → **添加安全组规则**
4. 配置如下：

| 配置项 | 值 |
|--------|-----|
| 规则方向 | 入方向 |
| 授权策略 | 允许 |
| 协议类型 | TCP |
| 端口范围 | 8890/8890 |
| 授权对象 | 0.0.0.0/0 |
| 描述 | MCP服务端口 |

5. 点击**确定**保存

> ⚠️ 如果不配安全组，外网访问不了你的服务，阿里百炼也连不上！

### 第8步：验证公网访问

在你**本地电脑**的浏览器中访问：

```
http://<你的服务器公网IP>:8890/sse
```

> ✅ 如果浏览器开始持续加载（SSE 是长连接，不会立刻返回完整页面），说明公网访问正常！

---

## 方案二：直接部署（不用 Docker）

### 第1步：SSH 连接服务器

同方案一第1步。

### 第2步：安装 Python 3.10+

```bash
# Ubuntu 22.04 自带 Python 3.10，先检查版本
python3 --version

# 如果版本低于 3.10，需要安装：
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3-pip
```

> ✅ `python3 --version` 输出 `Python 3.10.x` 或更高即可。

### 第3步：上传项目代码

同方案一第3步。

### 第4步：创建虚拟环境并安装依赖

```bash
cd /opt/daily_fortune

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 配置 pip 使用阿里云镜像加速（国内服务器推荐）
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.trusted-host mirrors.aliyun.com

# 安装项目
pip install -e .
```

> ✅ 看到 `Successfully installed daily-fortune-mcp-1.0.0` 就成功了。

### 第5步：测试运行

```bash
# 先前台运行，确认没问题（注意这里用的是 8890 端口）
daily-fortune-mcp --transport sse --host 0.0.0.0 --port 8890
```

> ✅ 看到类似 `Uvicorn running on http://0.0.0.0:8890` 的输出就对了。
> 按 `Ctrl+C` 停掉，接下来配置后台运行。

### 第6步：配置 systemd 守护进程（让服务自动运行）

```bash
# 创建 systemd 服务文件
sudo tee /etc/systemd/system/daily-fortune-mcp.service > /dev/null << 'EOF'
[Unit]
Description=Daily Fortune MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/daily_fortune
ExecStart=/opt/daily_fortune/venv/bin/daily-fortune-mcp --transport sse --host 0.0.0.0 --port 8890
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start daily-fortune-mcp

# 设置开机自启
sudo systemctl enable daily-fortune-mcp

# 查看服务状态
sudo systemctl status daily-fortune-mcp
```

> ✅ 看到 `active (running)` 就对了。

**常用管理命令：**
```bash
# 查看日志
sudo journalctl -u daily-fortune-mcp -f

# 重启服务
sudo systemctl restart daily-fortune-mcp

# 停止服务
sudo systemctl stop daily-fortune-mcp
```

### 第7步：配置安全组

同方案一第7步（放行 8890 端口）。

---

## 🔒 进阶配置（可选但推荐）

### 配置 Nginx 反向代理 + 域名（更专业）

直接用 IP:端口 虽然能用，但不够专业。如果你有域名，建议用 Nginx 反代：

```bash
# 安装 Nginx
sudo apt-get install -y nginx

# 创建配置文件
sudo tee /etc/nginx/sites-available/daily-fortune-mcp > /dev/null << 'EOF'
server {
    listen 80;
    server_name fortune.yourdomain.com;  # 替换成你的域名

    location / {
        proxy_pass http://127.0.0.1:8890;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;           # SSE 必须关闭缓冲
        proxy_cache off;               # 关闭缓存
        proxy_read_timeout 86400s;     # SSE 长连接超时设为 24 小时
    }
}
EOF

# 启用配置
sudo ln -sf /etc/nginx/sites-available/daily-fortune-mcp /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

> ⚠️ 记得在阿里云安全组中也放行 80 端口（如果还没放行的话）。
> 然后在域名 DNS 解析中，把 `fortune.yourdomain.com` 的 A 记录指向你的服务器公网 IP。

### 配置 HTTPS（更安全）

```bash
# 安装 certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 自动申请并配置 HTTPS 证书
sudo certbot --nginx -d fortune.yourdomain.com

# 设置自动续期
sudo systemctl enable certbot.timer
```

> ✅ 配置后阿里百炼的 MCP 地址就可以用 `https://fortune.yourdomain.com/sse`

---

## ☁️ 阿里百炼平台接入

> 📘 **详细的百炼接入教程请查看：[BAILIAN.md](./BAILIAN.md)**
>
> 包含脚本部署方式、AI网关方式、JSON配置模板、智能体提示词、常见问题等。

**快速要点：**

1. 百炼 MCP 管理 → 点击「+」→ 选择 **「使用脚本部署」**
2. 安装方式选 **http**（远程服务）
3. MCP 配置 JSON：
```json
{
  "mcpServers": {
    "daily-fortune": {
      "url": "http://<你的服务器公网IP>:8890/sse",
      "type": "sse"
    }
  }
}
```
4. 部署后创建智能体，**必须选 Plus 模型**（Max 不支持 MCP）
5. 在智能体中勾选该 MCP 服务即可

---

## 🔄 更新服务版本

### Docker 方式更新：

```bash
cd /opt/daily_fortune

# 拉取最新代码
git pull

# 重新构建镜像
sudo docker build -t daily-fortune-mcp:latest .

# 停掉旧容器，启动新容器
sudo docker rm -f daily-fortune-mcp
sudo docker run -d \
  --name daily-fortune-mcp \
  --restart=always \
  -p 8890:8000 \
  daily-fortune-mcp:latest
```

### 直接部署方式更新：

```bash
cd /opt/daily_fortune

# 拉取最新代码
git pull

# 激活虚拟环境
source venv/bin/activate

# 重新安装
pip install -e .

# 重启服务
sudo systemctl restart daily-fortune-mcp
```

---

## 🔍 故障排查

### 问题1：容器启动后马上退出

```bash
# 查看退出日志
sudo docker logs daily-fortune-mcp

# 常见原因：端口被占用
# 检查端口占用
sudo lsof -i :8890
# 杀掉占用进程或换个端口
sudo docker rm -f daily-fortune-mcp
sudo docker run -d --name daily-fortune-mcp --restart=always -p 9000:8000 daily-fortune-mcp:latest
```

### 问题2：本地能访问但公网访问不了

1. **检查安全组**：确保 **8890** 端口已放行（见第7步）
2. **检查防火墙**：
   ```bash
   sudo ufw status
   # 如果开启了防火墙，需要放行端口：
   sudo ufw allow 8890/tcp
   ```
3. **检查容器状态**：`sudo docker ps` 确认容器在运行

### 问题3：SSE 连接很快断开

如果用了 Nginx 反代，确保配置了：
- `proxy_buffering off;`
- `proxy_cache off;`
- `proxy_read_timeout 86400s;`

### 问题4：阿里百炼连不上 MCP

1. 先在你本地浏览器测试 `http://<公网IP>:8890/sse` 是否能访问
2. 确认填写的地址末尾有 `/sse`
3. 如果是 HTTPS，确保证书有效（`certbot` 自动申请的证书有效）

### 问题5：查看实时日志

```bash
# Docker 方式
sudo docker logs -f daily-fortune-mcp

# 直接部署方式
sudo journalctl -u daily-fortune-mcp -f
```

---

## 📝 快速命令速查表

| 操作 | Docker 命令 | 直接部署命令 |
|------|------------|-------------|
| 启动服务 | `sudo docker start daily-fortune-mcp` | `sudo systemctl start daily-fortune-mcp` |
| 停止服务 | `sudo docker stop daily-fortune-mcp` | `sudo systemctl stop daily-fortune-mcp` |
| 重启服务 | `sudo docker restart daily-fortune-mcp` | `sudo systemctl restart daily-fortune-mcp` |
| 查看状态 | `sudo docker ps` | `sudo systemctl status daily-fortune-mcp` |
| 查看日志 | `sudo docker logs -f daily-fortune-mcp` | `sudo journalctl -u daily-fortune-mcp -f` |
| 更新版本 | 见上方"更新服务版本" | 见上方"更新服务版本" |
