<p align="center">
  <strong>🌐 Bilingual · 🐳 Docker · 🪟 Windows Portable · 📊 Cost Calculator</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v0.6.2.2-blue" alt="version" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license" />
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20Docker-orange" alt="platform" />
  <img src="https://img.shields.io/badge/i18n-中文%20%7C%20English-ff69b4" alt="i18n" />
</p>

---

# 3D Filament Inventory Management System / 3D 打印耗材库存管理系统

A full-featured consumable asset management tool for 3D printing enthusiasts, small studios, and print farms. Track filaments from purchase to depletion, manage printers and slots, and calculate project costs with a built-in commercial pricing engine.

一款面向 3D 打印爱好者、小型工作室和打印农场的全功能耗材资产管理工具。耗材全生命周期追踪、设备与槽位管理、内置商业成本计算器。

**GitHub:** [pixelpulse0x1/3DFilamentManagement](https://github.com/pixelpulse0x1/3DFilamentManagement)

---

## 📖 English

### ✨ Key Features

- **Dashboard & Statistics** — Inventory overview, weight tracking, low-stock alerts, per-brand stats, cross status matrix (Material × 5-state)
- **Filament Management** — Full lifecycle (purchase → open → load → deplete), 5-state machine, dual-track loading, weighing calculator, batch operations
- **Device Management** — Multi-printer + multi-slot (AMS), load/unload with auto status sync, 36 built-in printer models (Bambu Lab / Creality / Prusa / etc.)
- **Commercial Pricing Engine** — Dynamic multi-row cost calculator, `Suggested Price = (Total Cost + Labor) / (1 − Profit% − Platform% − Tax%)`, zero-denominator protection, history center (50 records)
- **Reports** — Usage logs with withdraw mechanism, monthly/daily charts (Chart.js), ROI billing, 7-sheet Excel export
- **System** — Glassmorphism dark UI, background customization, one-click backup & hot restore, data migration from legacy DB
- **i18n** — 624-key Chinese/English bilingual dictionary, instant language switch, status enum disaster prevention (triple-layer defense)

### 🚀 Quick Start

#### Option 1: Docker Pull

```bash
docker pull pixelpulse01/3dfilamentmanagement:latest

docker run -d \
  --name 3dfilament \
  -p 9055:3155 \
  -v /opt/docker-stacks/3dfilamentmanagement:/data \
  -e SECRET_KEY=your-random-secret-key \
  -e TZ=Asia/Shanghai \
  pixelpulse01/3dfilamentmanagement:latest
```

Then visit **http://<your-server-ip>:9055**

#### Option 2: Docker Compose (Recommended)

Create a `docker-compose.yml`:

```yaml
services:
  3dfilamentmanagement:
    image: pixelpulse01/3dfilamentmanagement:latest
    container_name: 3dfilamentmanagement
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - SECRET_KEY=change-me-to-random-string
      - DATA_DIR=/data
    ports:
      - "9055:3155"
    volumes:
      - /opt/docker-stacks/3dfilamentmanagement:/data
```

Then:

```bash
docker compose up -d
```

### 🔧 Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-p 9055:3155` | `9055:3155` | Host port : Container port (container always listens on 3155) |
| `-v ...:/data` | — | Persistent data volume (database + uploads) |
| `SECRET_KEY` | `change-me-to-random-string` | Flask secret key — **change this in production** |
| `TZ` | `Asia/Shanghai` | Timezone (affects `datetime('now','localtime')` in SQLite) |
| `DATA_DIR` | `/data` | Data directory inside container (usually leave as default) |

### 📁 Data Persistence

All data is stored in `/data` inside the container:

```
/data/
├── database/
│   └── filament_inventory.db     # SQLite database (auto-migrated on startup)
└── uploads/
    ├── backgrounds/              # Background images
    └── filaments/                # Filament photos
```

Mount a host directory to `/data` to persist your database and uploads across container rebuilds.

### 🏗️ Build from Source

```bash
git clone https://github.com/pixelpulse0x1/3DFilamentManagement.git
cd 3DFilamentManagement/workspace

# Build & run
docker compose build --no-cache
docker compose up -d
```

### 🖥️ Windows Portable Edition

A zero-dependency Windows portable version is also available. Download `3D_Inventory_Management_v0.6.2.2.zip` from the [GitHub Releases](https://github.com/pixelpulse0x1/3DFilamentManagement), extract anywhere, and double-click `运行系统.bat` — no Python installation required.

### 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10 + Flask (Blueprint architecture) |
| Database | SQLite3 (versioned migration engine, V1→V11) |
| Frontend | Vanilla JS + Jinja2 + Chart.js |
| UI | Glassmorphism dark theme |
| Testing | 24-case E2E integration test suite |

### 📖 Documentation

- [TECHNICAL_REFERENCE.md](https://github.com/pixelpulse0x1/3DFilamentManagement/blob/main/workspace/TECHNICAL_REFERENCE.md) — Full technical reference (DB schema, API docs, migration engine, pricing formulas, build & packaging guide) — *in Chinese*

### 🔄 Version History

| Version | Date | Highlights |
|---------|------|------------|
| v0.6.2.2 | May 2026 | DEBUG_MODE log suppression, one-click build script, background seeding fix |
| v0.6.2.0 | May 2026 | Windows portable edition, multi-environment adaptive paths |
| v0.6.1.2 | May 2026 | i18n audit, status enum disaster prevention |
| v0.6.1.0 | May 2026 | i18n multilingual framework |
| v0.5.2.2 | Apr 2026 | 502 fixes, zero-denominator protection |
| v0.5.1.0 | Apr 2026 | Cost calculator with Chart.js dashboard |

### 📄 License

MIT License. See [LICENSE](https://github.com/pixelpulse0x1/3DFilamentManagement/blob/main/workspace/LICENSE).

---

## 📖 中文

### ✨ 核心功能

- **仪表板与统计** — 库存总览看板、使用重量追踪、低库存预警、厂商耗材统计、材料类型 × 5 态交叉矩阵
- **耗材管理** — 全生命周期（购买→开封→上机→耗尽）、5 态状态机、双轨上机、称重计算器、批量操作
- **设备管理** — 多打印机 + 多槽位 (AMS)、上机/下机自动状态同步、36 款内置打印机型号（拓竹/创想三维/Prusa 等）
- **商业报价引擎** — 多行动态成本计算器、`建议报价 = (总成本 + 辛苦费) / (1 − 利润率% − 平台抽成% − 税率%)`、分母为零防崩溃、50 条历史记录
- **使用记录与报表** — 撤回机制、月度/每日图表 (Chart.js)、ROI 效能账单、Excel 7 表导出
- **系统管理** — 玻璃拟态深色 UI、外观定制、一键备份与热还原、旧版数据迁移
- **国际化** — 624 键中英双语字典、即时语言切换、状态枚举通信防灾（三层防御）

### 🚀 快速开始

#### 方式一：直接拉取镜像

```bash
docker pull pixelpulse01/3dfilamentmanagement:latest

docker run -d \
  --name 3dfilament \
  -p 9055:3155 \
  -v /opt/docker-stacks/3dfilamentmanagement:/data \
  -e SECRET_KEY=your-random-secret-key \
  -e TZ=Asia/Shanghai \
  pixelpulse01/3dfilamentmanagement:latest
```

访问 **http://<你的服务器IP>:9055**

#### 方式二：Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
services:
  3dfilamentmanagement:
    image: pixelpulse01/3dfilamentmanagement:latest
    container_name: 3dfilamentmanagement
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - SECRET_KEY=change-me-to-random-string
      - DATA_DIR=/data
    ports:
      - "9055:3155"
    volumes:
      - /opt/docker-stacks/3dfilamentmanagement:/data
```

然后执行：

```bash
docker compose up -d
```

### 🔧 配置参数说明

| 参数 | 默认值 | 说明 |
|-----------|---------|-------------|
| `-p 9055:3155` | `9055:3155` | 宿主机端口:容器端口（容器内固定监听 3155） |
| `-v ...:/data` | — | 数据持久化卷（数据库 + 上传文件） |
| `SECRET_KEY` | `change-me-to-random-string` | Flask 密钥 — **生产环境请务必修改** |
| `TZ` | `Asia/Shanghai` | 时区（影响 SQLite `datetime('now','localtime')`） |
| `DATA_DIR` | `/data` | 容器内数据目录（通常无需修改） |

### 📁 数据持久化

所有数据存储在容器内 `/data` 目录：

```
/data/
├── database/
│   └── filament_inventory.db     # SQLite 数据库（启动时自动迁移）
└── uploads/
    ├── backgrounds/              # 背景图
    └── filaments/                # 耗材实物图
```

将宿主机目录挂载到 `/data` 即可在容器重建后保留数据库和上传文件。

### 🏗️ 从源码构建

```bash
git clone https://github.com/pixelpulse0x1/3DFilamentManagement.git
cd 3DFilamentManagement/workspace

# 构建并启动
docker compose build --no-cache
docker compose up -d
```

### 🖥️ Windows 绿色便携版

同时提供零依赖的 Windows 绿色便携版。从 [GitHub Releases](https://github.com/pixelpulse0x1/3DFilamentManagement) 下载 `3D_Inventory_Management_v0.6.2.2.zip`，解压到任意目录，双击 `运行系统.bat` 即可启动——无需安装 Python 或任何运行环境。

### 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10 + Flask (Blueprint 模块化架构) |
| 数据库 | SQLite3 (版本化迁移引擎, V1→V11) |
| 前端 | Vanilla JS + Jinja2 模板 + Chart.js |
| UI | 玻璃拟态 (Glassmorphism) 深色主题 |
| 测试 | 24 项 E2E 集成测试 |

### 📖 文档

- [TECHNICAL_REFERENCE.md](https://github.com/pixelpulse0x1/3DFilamentManagement/blob/main/workspace/TECHNICAL_REFERENCE.md) — 完整技术参考（数据库结构 · API 文档 · 迁移引擎 · 报价公式 · 打包编译 · 部署指南）

### 🔄 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| v0.6.2.2 | 2026-05 | DEBUG_MODE 日志静音、一键编译脚本、背景图种子化修复 |
| v0.6.2.0 | 2026-05 | Windows 绿色便携版、多环境自适应路径底座 |
| v0.6.1.2 | 2026-05 | i18n 完备性审计、状态枚举通信防灾 |
| v0.6.1.0 | 2026-05 | i18n 多语言框架上线 |
| v0.5.2.2 | 2026-04 | 全线 502 修复、分母为零防崩溃 |
| v0.5.1.0 | 2026-04 | 成本计算器全量上线 + Chart.js 看板 |

### 📄 License

MIT License. 详见 [LICENSE](https://github.com/pixelpulse0x1/3DFilamentManagement/blob/main/workspace/LICENSE)。

---

<p align="center">
  <sub>Built with ❤️ by <a href="https://github.com/pixelpulse0x1">pixelpulse0x1</a></sub>
</p>
