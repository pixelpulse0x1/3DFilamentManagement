# 3DFilamentManagement — 技术参考文档

## 版本: v0.6.2.3

---

## 1. 项目目录树

```
3DFilamentManagement/                    # 项目总根目录
├── workspace/                           # ★ 主工作空间（Docker 构建上下文）
│   ├── app.py                           # 应用工厂 (create_app) + 多环境自适应路径底座
│   ├── modules/                         # Flask Blueprint 模块
│   │   ├── __init__.py
│   │   ├── db.py                        # 版本化迁移引擎 (LATEST_VERSION=11)
│   │   ├── i18n.py                      # 中英双语字典 (624 条目)
│   │   ├── base/                        # 基础模块
│   │   │   ├── __init__.py
│   │   │   ├── routes.py                # 页面路由、设置、背景、外观、备份、系统API
│   │   │   ├── bg_utils.py              # 背景管理 (CRUD + 种子化 + 文件服务)
│   │   │   └── migrate_utils.py         # 旧版数据导入 (db / txt)
│   │   ├── filaments/                   # 耗材核心模块
│   │   │   ├── __init__.py
│   │   │   └── routes.py                # CRUD、使用记录、统计数据、交叉矩阵、状态校验守卫
│   │   ├── materials/                   # 材料类型 CRUD
│   │   ├── brands/                      # 品牌与盘重管理
│   │   ├── channels/                    # 购买渠道
│   │   ├── images/                      # 耗材实物图 (上传/替换/删除)
│   │   ├── printers/                    # 打印机、槽位、上机/下机、打印机型号
│   │   └── tools/                       # 成本计算器与历史记录
│   │       ├── __init__.py
│   │       └── routes.py                # 计算器 CRUD、保存/详情/删除、_safe_float() 防护
│   ├── static/                          # 前端静态资源
│   │   ├── css/
│   │   │   ├── main.css                 # 玻璃拟态主题 + 全部页面样式
│   │   │   └── responsive.css           # 响应式适配
│   │   ├── js/
│   │   │   ├── app.js                   # 主应用逻辑 (全局 i18n、状态管理、通知)
│   │   │   ├── settings.js              # 设置 + 外观 + 背景 + 备份
│   │   │   ├── printers.js              # 设备管理 (打印机/槽位/上机/下机)
│   │   │   ├── printer_models.js        # 打印机型号管理 + "点击拥有"一键资产化
│   │   │   ├── brands.js                # 品牌树 CRUD (级联盘型选择)
│   │   │   ├── channels.js              # 购买渠道 CRUD
│   │   │   ├── images.js                # 实物图 CRUD + 灯箱预览
│   │   │   ├── roi.js                   # ROI 效能账单 (参数持久化)
│   │   │   ├── cost_calculator.js       # 商业成本计算器 (动态增行/反序列化/实时看板)
│   │   │   ├── materials.js             # 材料类型 CRUD
│   │   │   └── manufacturers.js         # 品牌/厂商 CRUD
│   │   └── uploads/
│   │       └── backgrounds/             # 默认背景图 Background.png (2MB)
│   ├── templates/                       # Jinja2 HTML 模板
│   │   ├── base.html                    # 主布局 (侧边栏 + 内容区 + 模态框 + i18n 注入)
│   │   ├── components/
│   │   │   ├── sidebar.html             # 多级手风琴导航 (含版本号)
│   │   │   └── modals.html              # 共享耗材模态框 + 图片灯箱
│   │   ├── dashboard/                   # 仪表板子页面
│   │   │   ├── overview.html            # 库存总览 (指标卡片/预警条/厂商统计)
│   │   │   ├── filaments.html           # 耗材管理 (表格/筛选/批量操作)
│   │   │   ├── logs.html                # 使用记录 (表格/撤回)
│   │   │   ├── daily.html               # 使用图表 (月度趋势/每日柱状)
│   │   │   └── filament_stats.html      # 交叉矩阵统计 (材料×5态)
│   │   ├── settings/                    # 设置子页面
│   │   │   ├── general.html             # 常规 (语言/低库存阈值/数据迁移)
│   │   │   ├── appearance.html          # 外观 (卡片透明度/颜色/模糊度实时预览)
│   │   │   └── advanced.html            # 高级 (备份下载/热还原)
│   │   ├── tools/
│   │   │   └── cost_calculator.html     # 双栏成本计算器 (耗材/设备/后处理/看板)
│   │   ├── device_management.html       # 设备管理 (打印机列表/槽位)
│   │   ├── printer_models.html          # 打印机型号库 (36款内置)
│   │   ├── brand_management.html        # 品牌与盘型管理 (树状折叠)
│   │   ├── channel_management.html      # 购买渠道管理
│   │   ├── image_management.html        # 实物图管理
│   │   ├── roi.html                     # ROI 效能账单
│   │   └── materials.html               # 材料类型管理
│   ├── data/                            # 【运行时】持久化数据宿主 (三轨道自适应)
│   │   ├── database/
│   │   │   └── filament_inventory.db    # SQLite 主数据库
│   │   └── uploads/
│   │       ├── backgrounds/             # 用户上传 + 种子化的背景图
│   │       └── filaments/               # 用户上传的耗材实物图
│   ├── test_suite.py                    # E2E 集成测试套件 (24 项)
│   ├── requirements.txt                 # Python 依赖 (Flask==3.0.3, openpyxl==3.1.5)
│   ├── Dockerfile                       # Docker 镜像构建文件
│   ├── docker-compose.yml               # Docker 编排 (端口 9055:3155)
│   ├── entrypoint.sh                    # 容器入口脚本 (pip install + app 启动)
│   ├── 运行系统.bat                      # Windows 一键启动脚本 (含 DEBUG_MODE 开关)
│   ├── Windows一键编译exe程序.bat         # Windows 全流程编译打包脚本
│   └── TECHNICAL_REFERENCE.md           # 本技术参考文档
├── archive/                             # 代码存档 (空)
├── tests/                               # 测试资源 (空)
├── research/                            # 版本需求文档 (v0.6.1.1 ~ v0.6.2.3)
└── docs_private/                        # 原始软件本体 + 网页代码提取存档
```

### 1.1 多环境数据目录路径解析

`app.py` 在启动时通过三轨道探测确定 `DATA_DIR`，所有持久化数据（SQLite 数据库、上传文件）均存储在此目录下：

| 轨道 | DATA_DIR 路径 | 示例 |
|------|-------------|------|
| A: PyInstaller | `{EXE_DIR}/../data/` | `C:\...\3D_Inventory_Management_v0.6.2.3\data\` |
| B: Docker | `os.environ.get("DATA_DIR")` → `/data/` | `/data/` (数据卷挂载点) |
| C: Dev | `app.py` 同级 `data/` | `workspace/data/` |

---

## 2. SQLite 数据库结构

数据库文件路径由 `modules/db.py` 的 `get_db_path(data_dir)` 函数生成：`{DATA_DIR}/database/filament_inventory.db`。所有表均使用 SQLite 外键约束（`PRAGMA foreign_keys = ON`），由迁移引擎自动开启。

### 2.1 表: `filaments` (耗材)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 唯一耗材ID |
| name | TEXT | NOT NULL | 耗材名称 |
| material_type | TEXT | NOT NULL | 材料类型 |
| color | TEXT | NOT NULL | 颜色 (hex色码) |
| location | TEXT | | 存储位置 |
| status | TEXT | NOT NULL DEFAULT '全新' | 全新 / 闲置 / 用尽（不足由重量动态判定） |
| initial_weight | REAL | NOT NULL DEFAULT 1000.0 | 初始重量 (g) |
| current_weight | REAL | NOT NULL | 当前剩余重量 (g) |
| is_favorite | BOOLEAN | NOT NULL DEFAULT 0 | 常用标记 |
| is_loaded | INTEGER | DEFAULT 0 | (v0.4.2.2) 双轨制：1=已上机 |
| created_at | TEXT | DEFAULT datetime('now','localtime') | 创建时间 |
| purchase_date | TEXT | | 购买日期 |
| purchase_price | REAL | | 购买价格 (¥) |
| opened_at | TEXT | | 开封日期 |
| image_id | INTEGER | FK→filament_images(id) ON DELETE SET NULL | 实物图 |
| remark | TEXT | | 自定义备注 |
| channel_id | INTEGER | FK→channels(id) ON DELETE SET NULL | 购买渠道 |
| brand_id | INTEGER | FK→brands(id) ON DELETE SET NULL | 关联品牌/盘型 |

### 2.2 表: `usage_records` (使用记录)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| filament_id | INTEGER | NOT NULL | 外键 → filaments.id |
| used_weight | REAL | NOT NULL | 使用重量 (g) |
| note | TEXT | | 使用备注 |
| used_at | TEXT | DEFAULT datetime('now','localtime') | 使用时间 |

### 2.3 表: `settings` (设置)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 单例 (id=1) |
| threshold | INTEGER | DEFAULT 200 | 低库存预警阈值 (g) |
| default_weight | REAL | DEFAULT 1000.0 | 新耗材默认初始重量 (g) |

### 2.4 表: `materials` (材料类型)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| name | TEXT | UNIQUE NOT NULL | 材料类型名称 |
| description | TEXT | DEFAULT '' | 描述 |

### 2.5 表: `printers` (打印机)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| name | TEXT | UNIQUE NOT NULL | 打印机名称 |
| model | TEXT | DEFAULT '' | 型号文本 |
| model_id | INTEGER | FK→printer_models(id) ON DELETE SET NULL | 关联型号 |
| created_at | TEXT | DEFAULT datetime('now','localtime') | |

### 2.6 表: `printer_slots` (打印机槽位)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| printer_id | INTEGER | NOT NULL, FK→printers(id) ON DELETE CASCADE | 所属打印机 |
| slot_name | TEXT | NOT NULL | 槽位名称 (例: "AMS-A1") |
| current_filament_id | INTEGER | UNIQUE, FK→filaments(id) ON DELETE SET NULL | 当前绑定的耗材 |

### 2.7 表: `printer_models` (打印机型号) — v0.4.1.0, 扩展于 v0.5.0.0
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| brand | TEXT | NOT NULL | 品牌名称 |
| model_name | TEXT | NOT NULL UNIQUE | 型号名称 |
| technology | TEXT | DEFAULT 'FDM' | 成型技术: FDM / SLA / DLP / SLS / Multi-jet+UV |
| bed_size | TEXT | DEFAULT '' | 成型尺寸 (例: "256x256x256") |
| power_w | INTEGER | DEFAULT 200 | (v0.5.0.0) 额定功率 (W) |
| value_yuan | REAL | DEFAULT 0.0 | (v0.5.0.0) 参考价格 (¥) |
| lifespan_h | INTEGER | DEFAULT 20000 | (v0.5.0.0) 预期寿命 (小时) |
| remark | TEXT | DEFAULT '' | 特性描述 |

内置数据: 36 款型号 (拓竹 12 款, 创想三维 8 款, Prusa 5 款, Flashforge 4 款, Raise3D 7 款)。

### 2.8 表: `filament_images` (实物图)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| name | TEXT | NOT NULL | 友好名称 |
| file_name | TEXT | NOT NULL | UUID 文件名 |
| created_at | TEXT | DEFAULT datetime('now','localtime') | |

### 2.9 表: `channels` (购买渠道)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| name | TEXT | UNIQUE NOT NULL | 渠道名称 |
| description | TEXT | DEFAULT '' | 描述 |

### 2.10 表: `brands` (品牌与盘型)
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| name | TEXT | NOT NULL | 品牌名称 |
| spool_type | TEXT | DEFAULT '标准盘' | 盘型名称 |
| spool_weight | REAL | NOT NULL DEFAULT 0.0 | 空盘重量 (g) |
| remark | TEXT | DEFAULT '' | 备注 |
||| UNIQUE(name, spool_type) | 品牌+盘型联合唯一 |

### 2.11 表: `calculation_history` (成本计算历史) — v0.5.1.0
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| project_name | TEXT | NOT NULL | 项目/模型名称 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| filaments_json | TEXT | NOT NULL | 耗材配置 JSON 数组 (见 §3) |
| printers_json | TEXT | NOT NULL | 打印机配置 JSON 数组 |
| post_processing_json | TEXT | DEFAULT '[]' | 后处理 JSON 数组 |
| design_fee | REAL | DEFAULT 0.0 | 建模/设计费 |
| packaging_fee | REAL | DEFAULT 0.0 | 包装费 |
| shipping_fee | REAL | DEFAULT 0.0 | 快递费 |
| other_fee | REAL | DEFAULT 0.0 | 其他杂费 |
| tax_rate | REAL | DEFAULT 0.0 | 税率 (%) |
| platform_commission_rate | REAL | DEFAULT 0.0 | 平台抽成 (%) |
| profit_rate_expect | REAL | DEFAULT 0.0 | 期望利润率 (%) |
| labor_markup_fee | REAL | DEFAULT 0.0 | 辛苦费 |
| total_cost | REAL | NOT NULL | 计算得出的总成本 |
| suggested_price | REAL | NOT NULL | 计算得出的建议报价 |
| pure_profit | REAL | NOT NULL | 计算得出的纯利润 |

### 2.12 表: `system_settings` (系统设置)
键值对存储。主要键值:

| 键 | 默认值 | 说明 |
|-----|---------|-------------|
| `active_background` | `"Background.png"` | 当前活跃背景图 |
| `card_opacity` | `"0.15"` | 卡片透明度 |
| `card_color` | `"#ffffff"` | 卡片颜色 |
| `card_blur` | `"1"` | 背景模糊度 (px) |
| `low_weight_threshold` | `"100"` | 低库存（不足）阈值 (g) |
| `system_language` | `"zh"` | (v0.6.0.0) 界面语言: zh / en |
| `database_version` | `"1"` → `"11"` | 数据库迁移版本号 |

### 2.13 表: `system_configs` (系统配置) — v0.4.3.0
| 列名 | 类型 | 约束 | 说明 |
|--------|------|-------------|-------------|
| config_key | TEXT | PRIMARY KEY | 配置键 |
| config_value | TEXT | NOT NULL | 配置值 |

默认值: `market_price_per_gram=0.15`, `cost_per_gram=0.01`。

---

## 3. JSON 存储设计 (calculation_history)

动态多行组件以 JSON 字符串形式存储在 SQLite TEXT 列中:

```json
// filaments_json — 耗材配置
[
  {
    "filament_id": 1,
    "material_name": "拓竹-PLA-黑",
    "weight_g": 150.0,
    "purge_g": 20.0,
    "cost_per_g": 0.05,
    "is_support": 0,
    "current_g": 850.0
  }
]

// printers_json — 设备配置
[
  {
    "printer_id": 2,
    "printer_name": "P1S-01",
    "print_time_mins": 330,
    "power_w": 105,
    "value_yuan": 3899,
    "lifespan_h": 20000
  }
]

// post_processing_json — 后处理配置
[
  {
    "process_name": "拆支撑",
    "charge_type": "hourly",
    "rate": 15.0,
    "quantity": 1.5,
    "subtotal": 22.5
  }
]
```

---

## 4. 版本化迁移引擎

`modules/db.py` 实现版本化增量数据库迁移引擎，`LATEST_VERSION = 11`。

### 4.1 迁移流程

1. **`init_db(data_dir)`** — app 启动时调用，确保数据库文件与目录存在。
2. **`_ensure_migrations(db_path, data_dir)`** — 读取 `system_settings` 中存储的 `database_version` 键，与 `LATEST_VERSION` 比对。
3. **逐级迁移** — 从当前版本依次执行 `Vn→Vn+1` 迁移函数，每步完成后立即 COMMIT 并更新 `database_version`。
4. **冷备份** — 每次迁移步骤执行前，自动创建 `filament_inventory.db.v{N}.bak` 备份文件（与数据库同目录）。

### 4.2 迁移步骤表

| 步骤 | 版本 | 变更内容 |
|------|---------|---------|
| V1→V2 | v0.2.4.0 | 新增 printers, printer_slots 表; filaments.status 列 |
| V2→V3 | v0.3.0.0 | 新增 filament_images 表; filaments.image_id/remark; 文件重组 |
| V3→V4 | v0.3.1.0 | 新增 channels 表; filaments.channel_id 外键 |
| V4→V5 | v0.4.0.0 | 新增 brands 表; filaments.brand_id 外键 |
| V5→V6 | v0.4.1.0 | 新增 printer_models 表; printers.model_id 外键 |
| V6→V7 | v0.4.2.2 | 新增 filaments.is_loaded 列; 上机双轨制 |
| V7→V8 | v0.4.3.0 | 新增 system_configs 表; ROI 默认参数 |
| V8→V9 | v0.5.0.0 | printer_models 新增 power_w/value_yuan/lifespan_h; 15 款精准参数 |
| V9→V10 | v0.5.1.0 | 新增 calculation_history 表 |
| V10→V11 | v0.6.0.0 | system_settings 新增 system_language 设置项 |

冷备份: 每次迁移步骤执行前自动创建 `filament_inventory.db.v{N}.bak`。

---

## 5. 商业报价引擎

### 5.1 核心公式

$$\text{建议最终报价} = \frac{\text{生产总成本} + \text{额外加收辛苦费}}{1 - \text{期望利润率}\% - \text{平台抽成}\% - \text{税率}\%}$$

### 5.2 分项计算

**单行耗材材料费:**
$$\text{单行耗材费} = (\text{预估克重} + \text{排废克重}) \times \frac{\text{购入单价(元/kg)}}{1000}$$

**单行设备折旧费:**
$$\text{单行设备折旧费} = \frac{\text{打印总分钟数}}{60} \times \frac{\text{设备购买价值}}{\text{预计寿命小时数}}$$

**单行设备电费:**
$$\text{单行设备电费} = \frac{\text{打印总分钟数}}{60} \times \frac{\text{设备功率W}}{1000} \times 0.6\text{元/度}$$

**生产总成本:**
$$\text{生产总成本} = \sum\text{耗材费} + \sum\text{电费} + \sum\text{折旧费} + \sum\text{后处理} + \text{附加费}$$

### 5.3 分母为零防崩溃保护

在 `POST /api/tools/calculator/save` 中:
```python
denominator = 1 - (profit_rate / 100.0) - (commission_rate / 100.0) - (tax_rate / 100.0)
if denominator <= 0:
    return jsonify({"status": "error", "error": "期望利润率+平台抽成+税率之和不能大于或等于100%，请调整参数后重试"}), 400
```

此前置守卫阻止除零崩溃（否则会向上传播为 502 Bad Gateway）。

此外，所有数值字段均由 `_safe_float()` 保护:
```python
def _safe_float(val, default=0.0):
    try: return float(val)
    except (ValueError, TypeError): return default
```

### 5.4 前端输入校验

前端保存前三重检查:
1. `project_name` 不能为空 → 400
2. `filaments` 数组不能为空 → 400
3. `printers` 数组不能为空 → 400

---

## 6. 前端状态反序列化

### 6.1 历史记录载入/克隆流程

用户点击 **📂 载入编辑**:
1. `GET /api/tools/calculator/detail/<id>` 返回含 JSON 数组的完整记录
2. `document.getElementById('currentRecordId').value = d.id` — 标记为 UPDATE
3. `deserializeFilaments()` 清空容器，遍历项目，调用 `addFilamentRow()`，填充隐藏输入框
4. `deserializePrinters()` 和 `deserializePost()` 遵循相同模式
5. `recalc()` 重新渲染看板和饼图
6. 保存按钮变为 "更新当前记录"

用户点击 **👥 复制克隆**:
1. 与编辑相同加载数据
2. `currentRecordId` 显式清空为 `""`
3. 保存按钮显示 "保存为新的计算" — 触发 INSERT

### 6.2 动态 DOM 行生命周期

每个 `addFilamentRow()` 创建一个 `<div class="calc-row">`，包含:
- "点击选择耗材" 按钮（打开选择器模态框）
- 隐藏输入框: `filament-id`, `filament-price`, `filament-init`, `filament-current`, `filament-name`
- 重量/排废输入框、单价显示、支撑复选框、删除按钮

耗材选择器模态框 (`filamentPickerModal`) 提供搜索、状态筛选和可排序表格。

### 6.3 库存超量警告

如果 `(预估克重 + 排废克重) > 当前剩余重量`，行边框变为警告色 (`border: 2px solid var(--warning)`)。

---

## 7. API 参考

### 7.1 耗材
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/filaments | 全量列表 (ORDER BY is_favorite DESC, id DESC) |
| POST | /api/filaments | 创建单个 |
| PUT | /api/filaments/:id | 更新（部分字段） |
| DELETE | /api/filaments/:id | 上机状态阻止删除；删除关联记录 |
| POST | /api/filaments/batch | 批量创建 |
| POST | /api/filaments/:id/use | 记录使用量; 重量归零自动解绑 |
| POST | /api/filaments/delete-multiple | 批量删除 |

### 7.2 使用记录

| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/usage_records | 列表 (JOIN filaments 包含 material_type/color/name) |
| PUT | /api/usage_records/:id | 仅编辑备注 (note 字段)，不改变重量 |
| DELETE | /api/usage_records/:id | 撤回使用记录 — 自动将 used_weight 加回 filaments.current_weight |

> **撤回机制**: 删除使用记录时，后端的 `DELETE` handler 会将记录的 `used_weight` 值加回耗材当前重量，同时解除重量归零触发过的自动解绑逻辑。

### 7.3 统计数据
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/statistics | 聚合统计; `?filter=all\|remaining\|used` |
| GET | /api/stats/matrix | 材料类型 × 5 态交叉矩阵; `?filter=all\|全新\|闲置\|上机\|不足\|用尽` |

### 7.4 材料类型、品牌、渠道
| 端点 | 方法 | 说明 |
|----------|---------|-------------|
| /api/materials | GET/POST, /:id PUT/DELETE | 材料类型（安全删除） |
| /api/brands | GET/POST, /:id PUT/DELETE, /rename POST | 品牌/盘型管理 |
| /api/channels | GET/POST, /:id PUT/DELETE | 购买渠道 |

### 7.5 打印机与槽位
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/printers | 列表（嵌套槽位 + 耗材 JOIN） |
| POST | /api/printers | 创建（含 model_id） |
| DELETE | /api/printers/:id | 级联释放耗材 |
| POST | /api/printers/:id/slots | 添加槽位 |
| DELETE | /api/slots/:id | 删除槽位，释放耗材 |
| PUT | /api/slots/:id/bind | 上机绑定 (设置 is_loaded=1) |
| PUT | /api/slots/:id/unbind | 下机解绑 (设置 is_loaded=0) |
| POST | /api/printers/from-model | 一键拥有: 从型号快速创建设备 |

### 7.6 打印机型号
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/printer_models | 列表（含功率/价值/寿命） |
| POST | /api/printer_models | 创建自定义型号 |
| PUT | /api/printer_models | 更新（PUT 含 id） |
| DELETE | /api/printer_models/:id | 删除（有打印机引用时阻止） |

### 7.7 实物图
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/images | 列表（含引用计数 ref_count） |
| POST | /api/images/upload | 上传 (multipart, 最大 5MB) |
| PUT | /api/images/:id | 更新名称或替换文件 |
| DELETE | /api/images/:id | 删除文件+记录 (耗材 SET NULL) |

### 7.8 设置、背景、备份

| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET/PUT | /api/settings | 读写阈值、默认重量、低库存阈值、系统语言 |
| GET/PUT | /api/settings/appearance | 读写卡片透明度、颜色、模糊度 (实时预览) |
| GET | /api/settings/background | 返回 `{active, backgrounds: [...]}` |
| POST | /api/settings/background/upload | 上传背景 (multipart, jpg/jpeg/png/webp) |
| POST | /api/settings/background/set | `{filename}` → 设置为活跃背景 |
| POST | /api/settings/background/delete | `{filename}` → 删除 (Background.png 受保护) |
| GET | /api/settings/backup | 下载整个 /data 目录的 ZIP 包 |
| POST | /api/settings/backup/restore | 上传 ZIP → 清空 /data → 解压覆盖 → 自动运行迁移 |

**背景图存储架构**:
- **源文件**: `static/uploads/backgrounds/Background.png` — 随源码/default分支打包
- **运行时目录**: `{DATA_DIR}/uploads/backgrounds/` — Flask 通过 `/uploads/backgrounds/<filename>` 路由从此目录读取
- **种子化**: `seed_default_background()` 在 app 首次启动时将 `Background.png` 从 `static/` 复制到 `data/` 目录 (已存在则跳过)
- **文件服务**: `send_from_directory()` 直接读取文件系统，不经过 Flask static 路由，确保图片实时更新

### 7.9 系统
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/system/status | 程序版本、数据库版本、/data 健康状态 |
| GET/POST | /api/system/config | 读写 system_configs 配置 |

### 7.10 工具 — 成本计算器
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/tools/calculator/history | 最近 50 条历史记录 |
| POST | /api/tools/calculator/save | 保存 (无 id 时 INSERT, 有 id 时 UPDATE) |
| GET | /api/tools/calculator/detail/:id | 完整记录（含 JSON 反序列化） |
| DELETE | /api/tools/calculator/history/:id | 删除记录 |

### 7.11 Excel 导出
| 方法 | 端点 | 说明 |
|--------|----------|-------------|
| GET | /api/export/excel | 7 个工作表的 .xlsx (耗材、材料、记录、打印机、槽位、渠道、品牌) |

### 7.12 页面路由
| 端点 | 说明 |
|----------|-------------|
| / | 库存总览 |
| /dashboard/overview | 库存总览 |
| /dashboard/filaments | 耗材管理 |
| /dashboard/logs | 使用记录 |
| /dashboard/daily | 使用图表 |
| /dashboard/filament-stats | 交叉矩阵统计 |
| /dashboard/brands | 品牌与盘型管理 |
| /dashboard/printer-models | 打印机型号管理 |
| /materials | 材料类型 |
| /channels | 购买渠道 |
| /images | 实物图 |
| /devices | 设备管理 |
| /settings/general | 常规设置 |
| /settings/appearance | 外观设置 |
| /settings/advanced | 高级设置 |
| /roi | ROI 效能账单 |
| /tools/cost_calculator | 成本计算器 |

---

## 8. E2E 集成测试

### 8.1 测试套件

`test_suite.py` — 24 项自动化 API 测试，覆盖计算器保存校验、数据 API 字段完整性、全局端点健康检查。

```bash
# 基本用法
python test_suite.py --base-url http://192.168.37.132:9055

# Docker 容器内运行
docker exec 3dfilamentmanagement python test_suite.py --base-url http://localhost:3155
```

特性:
- **服务器就绪轮询**: 测试前轮询 `GET /api/system/status` 最多 10 次 (间隔 2 秒)，确保服务已启动
- **`safe_json()` 解析器**: 多级回退 (`response.json()` → `json.loads(response.text)` → 错误日志)，兼容 Content-Type 缺失场景
- **清晰断言**: 所有测试返回 `PASS` / `FAIL` + 期望值 vs 实际值详情
- **非零退出码**: 任一测试失败则 `sys.exit(1)`，可集成 CI/CD

### 8.2 测试覆盖

| 编号 | 类别 | 验证内容 |
|------|----------|-------------------|
| C1 | 计算器保存 | 空 project_name → 400 拒绝 |
| C2 | 计算器保存 | 空字符串/脏数据不崩溃 (`_safe_float()` 防护) |
| D | 计算器保存 | 分母 ≤ 0 → 400 错误提示 (防除零) |
| A | 数据 API | `GET /api/filaments` 返回列表，含 brand_id/channel_id 字段 |
| B | 设置 API | `GET /api/settings` 返回 threshold 字段 |
| G1-G11 | 全局端点 | 11 个核心 API 全部返回 200 |

### 8.3 数据库连接治理

`app.py` 中的 `@app.teardown_appcontext`:
```python
@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        try: db.close()
        except Exception: pass
```
确保每个 HTTP 请求上下文释放其 SQLite 连接，防止连接池耗尽和 "Database is locked" 故障。

### 8.4 迁移步骤 try/except 包裹

每个 `_run_migration()` 步骤均被包裹:
```python
try:
    _run_migration(current, current + 1, data_dir, conn)
    current += 1
except Exception as e:
    logger.error("Migration V%d→V%d failed: %s", current, current+1, e)
    conn.rollback()
    raise RuntimeError(...) from e
```

---

## 9. Windows 绿色便携版架构 (v0.6.2.2)

### 9.1 多环境自适应路径底座

`app.py` 启动时自动探测运行环境，动态切换数据目录、静态资源路径和绑定地址：

| 环境 | 探测方式 | BASE_DIR | 绑定地址 | 默认端口 |
|------|---------|----------|---------|---------|
| A 轨道：PyInstaller 打包 | `getattr(sys, 'frozen', False)` | `server.exe` 所在 `backend/` 的上级目录 | `127.0.0.1` | `9055` |
| B 轨道：Docker 容器 | `/.dockerenv` 存在 或 `IS_DOCKER=true` | `app.py` 所在目录 | `0.0.0.0` | `3155` |
| C 轨道：开发环境 | 以上均不满足 | `app.py` 所在目录 | `127.0.0.1` | `9055` |

关键实现:
```python
IS_FROZEN = getattr(sys, 'frozen', False)
IS_DOCKER = os.path.exists('/.dockerenv') or os.environ.get('IS_DOCKER') == 'true'
```

- **A 轨道**: `static/` 和 `templates/` 与 `backend/` 平级存放，PyInstaller 打包时无需 `--add-data`
- **B 轨道**: 通过 `DATA_DIR` 环境变量覆盖数据目录，兼容已有 Docker 数据卷挂载
- **C 轨道**: 默认使用 `app.py` 同级 `data/` 目录

### 9.2 Windows 启动脚本

`运行系统.bat` — 一体化生命周期控制脚本：

1. **前置防灾**: `taskkill /f /im server.exe` 强杀残留进程，确保 9055 端口不冲突。
2. **调试开关**: `set DEBUG_MODE=false` — 环境变量透传给 `server.exe`，`false` 时 suppress 高频轮询 INFO 日志，`true` 时恢复全量日志。
3. **信息回显**: 打印应用根目录、数据库路径、静态资源路径、当前调试模式状态。
4. **浏览器唤醒**: 延迟 2 秒自动打开 `http://127.0.0.1:9055`。
5. **前台阻塞**: 直接执行 `backend\server.exe`，Flask WARNING 级别日志实时回显在 CMD 窗口。
6. **安全退出**: 关闭窗口或按 `Ctrl+C` 即可退出，系统安全下机并自动释放端口。

### 9.2a 日志静音引擎 (v0.6.2.2)

`app.py` 通过读取环境变量 `DEBUG_MODE` 动态控制 Werkzeug 日志级别：

```python
_is_debug_env = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
if not _is_debug_env:
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
```

- **`DEBUG_MODE=false` (默认)**: werkzeug logger → `WARNING`，仅 4xx/5xx 错误打印，前端高频轮询 `GET /api/statistics` 等 200 日志被静音。
- **`DEBUG_MODE=true`**: werkzeug logger 保持默认 `INFO`，全量 HTTP 请求日志滚动输出，用于排错。

### 9.2b 背景图种子化 (v0.6.2.2)

`modules/base/bg_utils.py` 的 `seed_default_background(data_dir, static_folder)` 在 `create_app()` 初始化阶段执行：

1. 检查 `{DATA_DIR}/uploads/backgrounds/Background.png` 是否已存在 → 已存在则跳过。
2. 从 `{STATIC_FOLDER}/uploads/backgrounds/Background.png` 读取源文件（2MB，暗色抽象纹理）。
3. 使用 `shutil.copy2()` 复制到数据目录，保留文件元数据。
4. 确保 `os.makedirs(bg_dir, exist_ok=True)` 自动创建目录树。

此机制解决了 Windows 便携版解压后 `data/` 目录为空导致背景图 404 的问题。

### 9.3 PyInstaller 打包规格

#### 一键编译脚本

项目根目录提供 `Windows一键编译exe程序.bat`，自动完成 8 步全流程：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 0 | 环境预检 | 检测 Python + Git 可用性 |
| 1 | 代码同步 | `git pull origin main` (Git 不可用时跳过) |
| 2 | 虚拟环境 | 创建隔离 `venv_build/`，防止打包体积虚胖 |
| 3 | 依赖安装 | flask + pyinstaller + openpyxl + requests |
| 4 | 清理旧产物 | 删除 `build/`、`backend/`、`*.spec` |
| 5 | PyInstaller 编译 | `--onedir --hidden-import=openpyxl` |
| 6 | 扁平化 | `xcopy /e /i /q /y` 递归复制 `backend/server/` → `backend/`，再 `rmdir` 删除空壳 |
| 7 | 发布包组装 | 复制 `backend/` + `static/` + `templates/` + `运行系统.bat` → 输出目录 |
| 8 | 清理收尾 | 删除 `build/`、`venv_build/`、`*.spec` |

> **Step 6 关键修复 (v0.6.2.2)**: 旧脚本使用 `move` 命令无法递归移动子目录，导致 `_internal/` (Python 运行时 DLL 依赖树) 被静默丢弃。改为 `xcopy /e /i /q /y` 递归复制后再 `rmdir /s /q` 删除空壳，确保 `server.exe` 启动时不报"拒绝连接"。

#### 手动编译阶段

```PowerShell
# 1. 在 Windows 上找一个干净的目录，从 Git 克隆/拉取最新代码
git clone https://github.com/pixelpulse0x1/3DFilamentManagement
cd 3DFilamentManagement

# 2. 切换并确保代码最新
git checkout main
git pull origin main

# 3. 创建纯净的独立沙盒（虚拟环境），防止打包体积虚胖
python -m venv venv

# 4. 临时更改 PowerShell 脚本执行策略（防止 Windows 拦截脚本运行）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 5. 激活虚拟环境（验算点：看到命令行开头出现 (venv) 字样说明隔离成功）
.\venv\Scripts\Activate.ps1

# 6. 隔离环境安装必要依赖
python -m pip install --upgrade pip
pip install openpyxl
pip install flask pyinstaller requests

# 7. 强力清除缓存并编译核心引擎（显式注入 openpyxl 隐式依赖）
pyinstaller --onedir --name server --clean --hidden-import=openpyxl --distpath ./backend --workpath ./build --specpath ./build app.py
```

> **⚙️ 编译幕后解析**： 执行后 PyInstaller 会自动解析 `app.py`，并将底层的 Python 解释器、Flask 框架以及 Windows 必须的 C++ 运行时 `.dll` 集中捞出。编译完成后，根目录下会多出 `build/`（缓存，可直接删除）和 `backend/`（成品库）。

#### 打包组装阶段

由于 PyInstaller 默认的规则会将可执行文件深埋在 `backend/server/server.exe` 路径下，为了匹配 `运行系统.bat` 的根路径感知逻辑，必须进行以下**物理拼装**：

1. 在任意位置创建一个新文件夹，命名为最终交付名称（如 `3D_Inventory_Management_v0.6.2.3`）。
2. 进入编译生成的 `backend/` 目录，展现出内部的 `server/` 文件夹。
3. **核心提炼**：进入该 `server/` 文件夹，**全选并剪切**内部所有文件（含 `server.exe` 和 `_internal/`），后退一级直接粘贴到 `backend/` 目录下，随后将空了的 `server/` 文件夹彻底删除。
4. 将此处理好的 `backend/` 整个文件夹复制到你新建的交付文件夹中。
5. 将项目源码根目录下的 `static/` 整个文件夹（含 CSS/JS/图标）复制过去。
6. 将项目源码根目录下的 `templates/` 整个文件夹（HTML 模板）复制过去。
7. 在新建的交付文件夹根目录下，右键新建一个文本文件，命名为 `运行系统.bat`，并将日常版 `.bat` 源码全量粘贴进去。

#### 上机实弹压测

1. 鼠标双击总根目录下的 `运行系统.bat`。
2. 弹出黑色的运维看板 CMD 窗口，自动执行防灾强杀逻辑。
3. 等待 2 秒后，Windows 默认浏览器会自动弹出一个新标签页，地址指向 `http://127.0.0.1:9055`。
4. 检查前端界面，确认版本号已完美刷新为 `v0.6.2.3`。
5. 尝试在前端上传一张耗材图片或添加一条记录，确认总根目录下自愈式创建出 `data/instance/data.db`。
6. 测试完毕后，在黑色 CMD 窗口中按下 `Ctrl + C`（或直接点右上角 `X` 关闭），系统将安全释放 `9055` 端口。

测试无误后，将 `3D_Inventory_Management_v0.6.2.3` 文件夹整体右键“压缩为 ZIP 文件”，即完成 **Windows 绿色便携版固件** 的发布。

#### 打包后标准目录结构

```Plaintext
3D_Inventory_Management_v0.6.2.3/    # 最终发布包总根目录
├── 运行系统.bat                       # 一键全自动入口脚本
├── static/                           # 前端静态资源（原样复制）
├── templates/                        # Jinja2 HTML 模板（原样复制）
├── backend/                          # 核心底层二进制座（已提炼扁平化）
│   ├── server.exe                    # 核心编译引擎（直接暴露在 backend 下）
│   └── _internal/                    # Python 底层依赖与 C++ 运行时 .dll 库
└── data/                             # 【运行时自动创建】持久化数据宿主槽
    ├── instance/
    │   └── data.db                   # 自动生成的本地 SQLite 数据库文件
    └── uploads/                      # 自动创建的耗材图片上传目录
```

#### 避坑要点

- **坚持使用 `--onedir`**：必须使用文件夹模式。严禁使用 `--onefile`（单文件模式每次启动都会在 Temp 目录解压，启动极慢且无法分离 `_internal` 依赖）。
- **静态资源外置**：`static/` 和 `templates/` 必须物理复制到总根目录，**不要**使用 `--add-data` 强行打进二进制，否则前端热更新将彻底失效。
- **规避隐式依赖坑**：打包命令中必须显式指定 `--hidden-import=openpyxl`，否则程序在加载 Excel 导出路由时会发生运行时闪退。
- **数据目录留空**：`data/` 目录及其子项目由后端底座在启动时通过 `os.makedirs` 自动自愈创建，交付包中无需预先建立，保证了固件的清爽。

---

## 10. 端口映射与 Docker 部署

### 10.1 docker-compose.yml

```yaml
services:
  3dfilamentmanagement:
    build: .
    image: pixelpulse01/3dfilamentmanagement:v0.6.2.3
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

### 10.2 端口与数据卷

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 容器内端口 | 3155 | `app.py` B 轨道自动绑定 |
| 宿主机端口 | 9055 | 对外访问统一端口 |
| 数据卷 | `/opt/docker-stacks/3dfilamentmanagement:/data` | 数据库 + 上传文件持久化 |
| SECRET_KEY | `change-me-to-random-string` | 生产环境务必修改 |
| TZ | `Asia/Shanghai` | 时区 (影响 datetime('now','localtime')) |

### 10.3 entrypoint.sh

```bash
#!/bin/bash
pip install openpyxl
exec python app.py
```

容器启动时自动安装 openpyxl (Excel 导出隐式依赖)，然后前台运行 Flask 应用。

### 10.4 Docker 部署命令

```bash
# 首次部署 / 版本更新
docker compose down
docker compose build --no-cache
docker compose up -d

# 查看日志
docker logs -f 3dfilamentmanagement

# 进入容器
docker exec -it 3dfilamentmanagement bash
```

### 10.5 镜像标签

| 标签 | 说明 |
|------|------|
| `pixelpulse01/3dfilamentmanagement:v0.6.2.3` | 当前版本 |
| `pixelpulse01/3dfilamentmanagement:latest` | 最新稳定版 |

---

## 11. i18n 国际化与状态枚举防灾架构 (v0.6.x)

### 11.1 设计原则

- **DB ↔ UI 分离**: 数据库存储中文状态值（"全新"/"闲置"/"上机"/"不足"/"用尽"），前端通过 `_i()` 映射为当前语言显示
- **表单值不变**: `<select>` 的 `value` 属性保持中文，仅文本显示使用 i18n，确保后端始终接收中文状态值
- **前端双辅助函数**: Jinja2 模板使用 `{{ i18n.key }}`，JavaScript 使用 `_i('key', 'fallback')`
- **后端状态校验**: `modules/filaments/routes.py` 增加 `VALID_STATUSES` 常量 + `_validate_status()` 守卫函数

### 11.2 状态枚举通信防灾 (v0.6.1.2 审计)

核心问题：前端切换为英文后，若 `<select>` 的 `value` 也使用 i18n 翻译值（如 "New"/"Idle"），则 POST/PUT 请求将英文状态值发送到后端，而后端 16+ 处逻辑分支全部硬编码匹配中文字符串，导致：
- 数据库写入英文状态值
- 所有状态判定逻辑失效（删除保护、上机绑定、统计矩阵等）

修复方案（三层防御）:
1. **前端表单层**: `<option value="全新">{{ i18n.status_new }}</option>` — value 固定中文，display 使用 i18n
2. **JS 筛选层**: `currentStatusFilters.has(_i('status_idle', '闲置'))` — 筛选器用 i18n 值匹配 checkbox，DB 字段用中文比较
3. **后端校验层**: `_validate_status()` 拦截非中文状态值，返回 400 错误

### 11.3 语言切换机制

**Jinja2 上下文处理器** (`app.py:inject_i18n()`):
```python
@app.context_processor
def inject_i18n():
    from modules.i18n import I18N
    # 从数据库 system_settings 读取 system_language 键值
    lang = row["value"] if row and row["value"] in I18N else "zh"
    return {'i18n': I18N.get(lang, I18N['zh']), 'current_lang': lang}
```

每个页面请求都执行此处理器，将当前语言的完整字典注入模板全局变量 `{{ i18n.xxx }}` 和 `window.I18N` JS 全局对象。

**JS 端辅助函数**:
- `_i(key, fallback)` — 翻译单个键，未找到时返回 fallback
- `_statusI18n(status)` — 将 DB 中文状态值映射为当前语言的显示文本
- `_fi18n(i18nValue)` — 反向映射：将 i18n 显示值转回中文 DB 状态值 (用于筛选器)

### 11.4 i18n 字典

`modules/i18n.py` — 624 键中英双语字典。结构:
```python
I18N = {
    'zh': { 'key': '中文值', ... },
    'en': { 'key': 'English Value', ... }
}
```

### 11.5 数据流

```
DB (中文状态值) → API (中文 JSON) → JS _statusI18n() → UI 显示（中/英）
                                      ↓
                              _i() / _fi18n() ← checkbox i18n 值 → JS 筛选逻辑
                                      ↓
                              <select value="全新"> (中文不变) → POST/PUT API → 后端校验
```

---

## 13.docker构建

```dockerfile
sudo docker compose down && sudo docker compose build --no-cache && sudo docker compose up -d
```



## 12. 更新日志

### v0.6.2.3
- 修复国际化（i18n）翻译审计缺陷：成本计算器中 `In Stock`、`Weight(g)`、`Purge(g)`、`Support`、`Device`、`Params`、`Process`、`Mode`、`Qty` 等字段翻译补齐
- 修复设备管理与成本计算器数据联动缺陷：设备列表"绑定机型"列正常显示型号名称，成本计算器正确读取机器价格
- 新功能：设备列表增加"编辑"功能，支持重命名设备名称、重选绑定机型、添加备注
- 数据库迁移 V11→V12：`printers` 表新增 `notes` 字段
- Chart.js 图表视觉调优：月度使用量/每日统计图表字体颜色改为纯白，新增数据点数值渲染插件
- 新功能：中英双语赞赏模态框，微信赞赏码/支付宝红包码静态资源打包至 `static/img/donation/`
- 全局版本号 v0.6.2.2 → v0.6.2.3

### v0.6.2.2
- `运行系统.bat` 新增 `DEBUG_MODE` 调试开关（默认 false），环境变量透传至 `server.exe`
- `app.py` 日志引擎联动：`DEBUG_MODE=false` 时 suppress werkzeug INFO 日志，消除高频轮询日志刷屏
- `Windows一键编译exe程序.bat` 上线：8 步全流程（预检→同步→venv→依赖→编译→扁平化→组装→清理）
- 修复编译脚本 Step 6 `move`→`xcopy /e /i /q /y`：`move` 无法递归移动子目录导致 `_internal/` 依赖树丢失、`server.exe` 启动报拒绝连接
- 修复 Windows 便携版 Background.png 背景图丢失：`seed_default_background()` 在 `create_app()` 中从 `static/` 种子化到 `data/` 目录
- `bg_utils.py` 新增 `seed_default_background()` 函数：幂等复制，已存在则跳过
- 全项目版本号同步：`test_suite.py`、`sidebar.html`、`docker-compose.yml`、`routes.py` 统一至 v0.6.2.2
- `TECHNICAL_REFERENCE.md` 全量补全：目录树、数据库路径、API 细节、Docker 编排、i18n 语言切换、日志/背景机制

### v0.6.2.0
- Windows 绿色便携版正式发布：全内聚相对路径，解压即用
- `app.py` 多环境自适应路径底座（PyInstaller / Docker / Dev 三轨道）
- `运行系统.bat` 一体化生命周期控制脚本（防灾强杀 + 浏览器唤醒 + 前台阻塞回显）
- PyInstaller 打包规格：`--onedir` 文件夹模式，静态资源与模板外置
- 端口统一：Windows/Dev → 9055，Docker 容器内 → 3155

### v0.6.1.2
- 全系统 i18n 完备性审计：排查所有残留硬编码中文，确保英文模式零汉字
- 高危故障修复：`<select id="filamentStatus">` value 与 display 分离，防止前端发送英文状态值
- 后端状态输入校验 `_validate_status()` 守卫，拦截非法状态值
- 40+ 处后端错误消息英文化（printers/filaments/routes.py）
- 成本计算器筛选器 i18n→DB 状态值映射 (`_fi18n()`)
- 矩阵图表双语言 statusNames 注册
- 侧边栏版本号 vv 双重修复

### v0.6.1.1
- 地毯式 i18n 国际化全面补完：533 → 612 键
- 10 个 HTML 模板全量 i18n 包裹（overview/filaments/logs/daily/stats/modals/roi 等）
- 10 个 JS 文件全量 `_i()` 替换（alert/confirm/label/placeholder/chart labels）
- 后端 Excel 导出表名/列头 + 系统状态英文化

### v0.6.1.0
- i18n 多语言框架上线：`modules/i18n.py` 双语字典
- Flask `inject_i18n` 上下文处理器 + `window.I18N` JS 全局注入
- 系统设置 → 常规 → 语言切换（zh/en）
- 侧边栏/导航/设置/耗材管理面板首批翻译

### v0.6.0.0
- `system_language` 设置项 + V11 数据库迁移
- 基础 i18n 基础设施搭建

### v0.5.2.2
- 全线 502 修复：迁移步骤增加 try/except 包裹 + rollback；`@app.teardown_appcontext` 强制释放 DB 连接
- 计算器 save 增加三重前置拦截（项目名/耗材/设备为空→400）；分母≤0→400
- `_safe_float()` 类型强转兜底，脏数据降级为 0.0
- test_suite.py：24 项自动化测试全通过；`safe_json()` 多级 JSON 解析回退

### v0.5.2.1
- 计算器 save 空 filaments/printers → 400 拦截
- test_suite.py：`safe_json()` + `--base-url` argparse 修复

### v0.5.2.0
- 测试套件 test_suite.py 上线：Test C/D/A/B + 11 端点健康扫描
- 全局 `unhandledrejection` 错误兜底

### v0.5.1.0
- 成本计算器全量上线：双栏布局、动态增行、Chart.js 数据标签
- `calculation_history` 表（JSON 多行组件存储）
- tools 蓝图 + 完整 CRUD API
- 商业定价公式 + 实时 Dashboard

### v0.5.0.0
- 打印机型号新增 power_w / value_yuan / lifespan_h
- 15 款 Bambu/Creality 精准参数填充
- 「点击拥有」一键资产化

### v0.4.3.0
- 「工具」手风琴菜单 + ROI 迁移
- system_configs 表 + ROI 参数持久化

### v0.4.2.3
- 上机双轨制 checkbox + 启用称重修复 + 初始重量小铅笔解锁

### v0.4.2.2
- is_loaded 双轨制：上机从状态值剥离为独立布尔字段
- 前端双 Badge 渲染、筛选联动

### v0.4.2.1
- 外观默认值统一：opacity=0.15, blur=1px

### v0.4.2.0
- 品牌管理树状折叠 + 重命名
- 称重计算器修复 + 状态变更防呆 + 备份热还原引擎

### v0.4.1.1
- printer_models 36 款型号；设备管理手风琴菜单

### v0.4.0.0
- brands 表 (25 款盘重数据)；品牌级联下拉；ROI 效能账单

### v0.3.4.1 → v0.3.0.0
- 状态机 5 态互斥；记录报表三级导航；双轨迁移引擎 (V1→V4)

### v0.2.4.0 → v0.2.2.0
- 设备管理看板；玻璃拟态 UI；手风琴导航；Excel 多表导出

### v0.2.1.0 → v0.1.0.0
- Blueprint 模块化架构；HA 深色主题；Docker 容器化
