# SAA 开发者手册（中文）

> English version: `docs/developer_en.md`

## 0. 先用一句人话讲清架构

把这个项目想象成“盖房子”：

- `app/framework` 是地基、水电、承重墙：通用、稳定、可复用。
- `app/features` 是装修和家具：和具体游戏玩法强相关，随需求变化。
- `module` 就是一间间可插拔功能房间：钓鱼房、商店房、登录房……
- `periodic` 和 `on_demand` 是两种“使用方式”：一个按计划排班，一个随点随干。

这套设计的核心收益是：
你可以不停加“新房间（模块）”，但不用每次都砸掉整栋楼（framework）。

## 0.1 什么是“周期性任务”和“非周期任务”（最重要）

- 周期性（`periodic`）：可排班、可串行队列、偏“日常托管”。
- 非周期（`on_demand`）：手动点启动、单任务运行、偏“特定场景工具”。

### 周期性任务（Periodic）

典型特征：

1. 在周期页面勾选，可按时间规则自动触发（每日/每周等）。
2. 由调度器和队列线程统一编排，可与其他任务串行执行。
3. 通常要求“尽量从任意状态可恢复”，会依赖返回主页/统一前置流程。
4. 任务元数据除了模块注册，还要在 `periodic_task_wiring.py` 配置调度信息。

示例：登录、福利、商店、体力、角色碎片、奖励、执行退出。

### 非周期任务（On-Demand）

典型特征：

1. 用户手动点击开始，不走定时调度。
2. 默认是“单任务运行”策略（一次只跑一个主动任务）。
3. 常用于“需要手动摆好初始场景”的功能。
4. 更像一个可随时调用的工具页，而不是托管日程。

示例：钓鱼、迷宫、心动水弹、抓帕鲁。
例如钓鱼通常要求你先站到正确位置再点开始，这就是典型非周期任务。

### 还有一种：被动非周期模块（Passive）

例如 `trigger`（自动辅助）这种常驻型能力：

1. 也挂在 on-demand 宿主里
2. 但不进入普通“单任务执行队列”
3. 更偏全局开关/辅助行为


## 1. 写模块前必须先懂的核心能力与约束
## 1.1 `auto`核心自动化功能
模块里的 `auto` 是框架线程统一注入的：

1. `TaskQueueThread`（周期）或 `ModuleTaskThread`（非周期）启动时创建 `RuntimeAutomationSession`
2. `RuntimeAutomationSession.prepare()` 内部调用 `BaseTask.init_auto(...)`
3. 默认工厂创建 `Automation(...)`
4. 线程再用 `module_class(auto, logger)` 实例化你的模块

也就是说，你的模块只需要老老实实初始化加上`auto`：

```python
class XxxModule:
    def __init__(self, auto, logger):
        self.auto = auto
        self.logger = logger
```

## 1.2 `auto` 常用能力有哪些（最常用三件套）

路径：`app/framework/infra/automation/automation.py`

1. 截图：`auto.take_screenshot()`
2. 识别：`auto.find_element(...)`（图像或文本）
3. 动作：`auto.click_element(...)` / `auto.press_key(...)` / `auto.move_click(...)`

“原子操作”机制：`automation.py` 里很多关键动作受装饰器保护，支持暂停/停止中断。

## 1.3 配置怎么读才对

路径：`app/framework/infra/config/app_config.py`

规则很简单：

1. 在 `run()` 里读配置，不要在 `__init__` 固化。
2. 统一从 `config.xxx.value` 读取。
3. UI 只改配置，不直接喂 usecase 业务参数。

例如 `close_game`：

```python
if config.CheckBox_close_game.value:
    ...
if config.CheckBox_shutdown.value:
    ...
```

这样用户改完配置，下次执行会立刻生效。

## 1.4 循环与超时约束（这是稳定性的命）

和旧文档一致，推荐状态机循环骨架：

```python
timeout = Timer(30).start()
while True:
    auto.take_screenshot()
    # 识别状态 -> 执行动作
    if timeout.reached():
        logger.error("xxx 超时")
        break
```

必须遵守：

1. 循环必须有超时或退出条件。
2. 每次关键动作后要考虑画面状态是否变化再决定 `continue`。
3. 不要让模块陷入“没有超时的死循环”。

## 1.5 比例与窗口约束

目前仍基于 16:9 约束运行。
`BaseTask.determine_screen_ratio(...)` 会做比例检查，不满足会失败返回。

开发时要点：

1. 尽量用相对区域（crop）和缩放后的坐标。
2. 不要假设每个人都是同一个分辨率。

## 1.6 OCR 怎么走

framework 入口：`app/framework/infra/vision/ocr_service.py` 的 `run_ocr(...)`
它会动态转发到业务 OCR 实现：`app/features/modules/ocr/ocr.py`。

错字替换仍依赖运行时词表（可通过词表页面维护）：

- `runtime/appdata/ocr_replacements.json`

## 1.7 日志怎么走

UI 日志能力：`app/framework/infra/logging/gui_logger.py`

规则：

1. 模块里用注入的 `logger`，不要直接 `print`。
2. logger 已经是跨线程安全写入 UI。
3. 日志是排查行为问题的第一证据，关键分支必须打点。

## 1.8 资源路径约束（最容易踩坑）

1. 业务匹配图放：`app/features/assets/<module>/...`
2. 通用图标/QSS/翻译放：根目录 `resources/`
3. 不要再用旧路径（`app/presentation/resources/*` 等）

---

## 2. 先上手：直接用项目里最简单的典型模块（`close_game`）

这一节不用“假例子”，直接拆真实代码。
`close_game` 是目前最短路径的标准模块：配置读取简单、UI 结构清晰、注册链路完整。

## 2.1 为什么选 `close_game`

它完整覆盖了“一个 periodic 模块最小闭环”的 4 件事：

1. `usecase`：读配置并执行动作
2. `ui`：页面控件定义
3. `module_specs`：注册到统一模块协议
4. `periodic_task_wiring`：接入周期调度元数据

## 2.2 真实 usecase 长什么样

文件：`app/features/modules/close_game/usecase/close_game_usecase.py`

```python
class CloseGameModule:
    def __init__(self, auto, logger):
        self.auto = auto
        self.logger = logger

    def run(self):
        if config.CheckBox_close_game.value:
            ...
        if config.CheckBox_shutdown.value:
            ...
        if config.CheckBox_close_proxy.value:
            ...
```

你要记住的关键点：

1. 线程实例化签名固定：`__init__(auto, logger)`。
2. 线程入口固定：`run()`。
3. 配置从 `config` 读，不从 UI 直接取。

## 2.3 真实 UI 长什么样

文件：`app/features/modules/close_game/ui/close_game_periodic_page.py`

```python
class CloseGamePage(ModulePageBase):
    def __init__(self, parent=None):
        super().__init__("page_close_game", parent=parent, host_context="periodic", use_default_layout=True)
        self.CheckBox_close_game = CheckBox(self)
        self.CheckBox_close_proxy = CheckBox(self)
        self.CheckBox_shutdown = CheckBox(self)
        ...
        self.finalize()
```

要点：

1. 建议继承 `ModulePageBase`，自动吃到 host_context 的尺寸策略。
2. 控件 `objectName` 要稳定，对应配置项和绑定逻辑。

## 2.4 真实注册怎么写

文件：`app/features/modules/module_specs.py`（节选）

```python
ModuleSpec(
    id="task_close_game",
    zh_name="执行退出",
    en_name="Execute Exit",
    order=110,
    hosts=(HostContext.PERIODIC,),
    ui_factory=lambda parent, _host: CloseGamePage(parent),
    module_class=CloseGameModule,
    ui_bindings=ModuleUiBindings(page_attr="page_close_game"),
)
```

文件：`app/features/bootstrap/periodic_task_wiring.py`（节选）

```python
{
    "id": "task_close_game",
    "ui_page_index": 10,
    "option_key": "CheckBox_close_game_10",
    "requires_home_sync": False,
    "default_activation_config": [{"type": "daily", "day": 0, "time": "00:00", "max_runs": 1}],
}
```

## 2.5 你要做“田庄加瓦”时，照着改哪几处

把 `close_game` 当模板复制一份，改 4 个地方就能跑起来：

1. 新建目录 `features/modules/farm_tiles/{ui,usecase}`。
2. 写 `FarmTilesModule(auto, logger).run()`。
3. 在 `module_specs.py` 增加 `task_farm_tiles` 的 `ModuleSpec`。
4. 在 `periodic_task_wiring.py` 增加 `task_farm_tiles` 的周期元数据。

如果你的逻辑像旧文档“酒馆”一样是状态机循环，也完全没问题，保留：

- `while True + take_screenshot()`
- 多状态分支处理
- `Timer` 超时兜底

## 2.6 快速验证

```bash
python -m compileall app
python scripts/smoke_modules.py
```

通过标准：

1. 无 `ImportError/ModuleNotFoundError/NameError`
2. 新模块 UI 可构建
3. 线程可启动（业务成功不是这一步的强制条件）

---

## 3. PR 代码要求与完整工程流程

## 3.1 必须遵守的边界

1. `framework` 不直接写死某个业务模块实现。
2. 模块注册统一走 `features/modules/module_specs.py`。
3. 周期调度元数据统一走 `features/bootstrap/periodic_task_wiring.py`。
4. 业务图像放 `app/features/assets`，不要塞回 framework。

## 3.2 本地提交前检查（必跑）

```bash
python -m compileall app
python -m py_compile SAA.py
python scripts/smoke_modules.py
python scripts/smoke_release.py
python scripts/release_cleanup_pack.py --startup-seconds 8
```

## 3.3 PR 描述最少包含

1. 改动动机（为什么要改）
2. 架构影响（改了哪些层、哪些边界）
3. 验证结果（命令 + 结果）
4. 风险与回滚方案

## 3.4 审查退回高频原因

1. 业务代码回流到 framework 通用层
2. 绕开 registry 写硬编码页面装配
3. 资源路径改了但引用没改，启动报 `Cannot open file ...`
4. 线程未正确停掉，出现 `QThread: Destroyed while thread is still running`

---

## 4. 项目介绍（架构总览 + 启动流程）

## 4.1 当前架构分层

- `app/framework`：通用能力（application/core/infra/ui）
- `app/features`：业务能力（bootstrap/modules/assets/utils）

核心思想：

1. `framework` 提供壳和协议，不关心具体游戏玩法。
2. `features` 决定“装什么模块、怎么组合”。
3. `bootstrap` 是组合根：负责把 features 注入 framework。

## 4.2 启动注入链路

1. `SAA.py` 启动 `StartupController`
2. `_create_main_window()` 调 `build_main_window_bridge()`
3. `MainWindow(feature_bridge=...)` 通过桥接拿到：
   - 模块注册
   - periodic 页面
   - on_demand 页面
   - OCR 初始化
4. 宿主页再从 registry 动态挂载模块 UI

这条链路的意义：低层不耦合高层业务，高层能自由替换。

---

## 5. 目录与关键文件职责（详细）

## 5.1 入口与构建

| 文件 | 用途 |
|---|---|
| `SAA.py` | 应用入口、启动任务编排、主窗口创建。 |
| `requirements.txt` | Python 依赖清单。 |
| `PerfectBuild/build.py` | Nuitka/PyInstaller 与安装包构建流程。 |
| `PerfectBuild/perfect_build.py` | 构建元信息（版本/名称/图标）。 |
| `PerfectBuild/assets/shapely.libs/.load-order-shapely-2.0.7` | shapely 加载顺序补丁。 |

## 5.2 framework/application

### modules

| 文件 | 用途 |
|---|---|
| `framework/application/modules/contracts.py` | 模块协议定义（`ModuleSpec` 等）。 |
| `framework/application/modules/registry.py` | 模块 spec provider 注册与读取。 |

### periodic

| 文件 | 用途 |
|---|---|
| `framework/application/periodic/periodic_controller.py` | 周期运行状态机与线程生命周期。 |
| `framework/application/periodic/periodic_orchestration.py` | 纯编排函数（任务筛选、规则复制、日程文本等）。 |
| `framework/application/periodic/periodic_page_actions.py` | 预设/规则/运行态页面动作。 |
| `framework/application/periodic/periodic_settings_usecase.py` | 配置持久化逻辑。 |
| `framework/application/periodic/periodic_ui_binding_usecase.py` | UI 控件绑定逻辑。 |
| `framework/application/periodic/on_demand_runner.py` | 单任务启动/停止策略。 |
| `framework/application/periodic/periodic_dispatcher.py` | 调度结果分发。 |

### tasks（桥接与兼容层）

| 文件 | 用途 |
|---|---|
| `framework/application/tasks/periodic_task_specs.py` | 从 features 侧读周期任务 spec。 |
| `framework/application/tasks/periodic_defaults.py` | 从 features 侧读默认周期序列。 |
| `framework/application/tasks/periodic_task_profile.py` | 生成周期页 runtime profile。 |
| `framework/application/tasks/task_registry.py` | 从统一 registry 生成 legacy registry。 |
| `framework/application/tasks/task_definition.py` | 任务定义结构。 |
| `framework/application/tasks/task_policy.py` | 任务策略常量。 |
| `framework/application/tasks/sequence_serializer.py` | 序列化辅助。 |

### 其他

| 文件 | 用途 |
|---|---|
| `framework/application/hotkey/routing.py` | F8 快捷键路由。 |
| `framework/application/startup/interface_plan.py` | 启动时页面加载计划。 |

## 5.3 framework/core

### interfaces

| 文件 | 用途 |
|---|---|
| `framework/core/interfaces/main_window_bridge.py` | 主窗口 bridge 协议。 |
| `framework/core/interfaces/game_environment.py` | 游戏环境接口。 |
| `framework/core/interfaces/periodic_ports.py` | 周期页业务端口协议。 |

### task_engine

| 文件 | 用途 |
|---|---|
| `framework/core/task_engine/base_task.py` | `auto` 初始化与窗口比例检查。 |
| `framework/core/task_engine/runtime_session.py` | 自动化会话 prepare/reset/stop。 |
| `framework/core/task_engine/threads.py` | `TaskQueueThread`/`ModuleTaskThread`。 |
| `framework/core/task_engine/scheduler.py` | 周期规则轮询触发。 |
| `framework/core/task_engine/hotkey_poller.py` | 全局快捷键轮询。 |

### 其他 core

| 文件 | 用途 |
|---|---|
| `framework/core/event_bus/global_task_bus.py` | 跨页面运行态与停止请求。 |
| `framework/core/config/daily_sequence.py` | 序列规范化。 |
| `framework/core/config/migration.py` | 序列 schema 迁移。 |
| `framework/core/observability/*` | 错误码与异常上报。 |

## 5.4 framework/infra

| 路径 | 用途 |
|---|---|
| `framework/infra/automation/*` | 后台输入、截图、窗口追踪。 |
| `framework/infra/vision/*` | 图像匹配与 OCR 服务。 |
| `framework/infra/config/app_config.py` | 全局配置定义。 |
| `framework/infra/config/setting.py` | 配置路径与项目常量。 |
| `framework/infra/logging/gui_logger.py` | UI 日志能力。 |
| `framework/infra/runtime/paths.py` | runtime 路径统一入口。 |
| `framework/infra/system/windows.py` | 句柄/窗口系统能力。 |
| `framework/infra/update/updater.py` | 更新能力。 |

## 5.5 framework/ui

| 文件 | 用途 |
|---|---|
| `framework/ui/views/main_window.py` | 主窗口外壳、导航、托盘。 |
| `framework/ui/views/periodic_tasks_page.py` | 周期任务宿主页。 |
| `framework/ui/views/on_demand_tasks_page.py` | 非周期宿主页。 |
| `framework/ui/views/periodic_base.py` | 模块 UI 统一基类。 |
| `framework/ui/views/display.py/help.py/setting_view.py` | 展示/帮助/设置页面。 |
| `framework/ui/shared/text.py` | 语言文本切换。 |
| `framework/ui/shared/style_sheet.py` | QSS 样式入口。 |
| `framework/ui/widgets/*` | 通用 UI 组件。 |

## 5.6 features

### bootstrap

| 文件 | 用途 |
|---|---|
| `features/bootstrap/main_window_wiring.py` | 业务组合根，向 framework 注入具体实现。 |
| `features/bootstrap/periodic_task_wiring.py` | 周期调度元数据与默认序列单一来源。 |

### modules

- 统一结构：`features/modules/<name>/{ui,usecase}`
- 总注册：`features/modules/module_specs.py`
- 模板：`features/modules/_template/README.md`

### assets + utils

| 路径 | 用途 |
|---|---|
| `features/assets/*` | 业务图片资源（匹配图/教程图）。 |
| `features/utils/home_navigation.py` | 返回主页业务流程。 |
| `features/utils/network.py` | 业务更新/活动数据拉取。 |
| `features/utils/updater.py` | 更新辅助。 |
| `features/utils/randoms.py` | 业务随机工具。 |
| `features/utils/text_normalizer.py` | 文本归一化。 |

---

## 6. 关键基础设施速查（开发时最常用）

| 需求 | 对应能力 |
|---|---|
| 模块执行自动化动作 | `auto`（由 `RuntimeAutomationSession` 提供） |
| 读写配置 | `framework/infra/config/app_config.py` 的 `config` |
| 输出日志到 UI | 注入的 `logger` |
| 周期队列执行 | `TaskQueueThread` + `PeriodicController` |
| 单模块执行 | `ModuleTaskThread` + `OnDemandRunner` |
| 跨页共享运行态 | `global_task_bus.publish_state(...)` |
| 全局请求停止 | `global_task_bus.request_stop()` |
| 中英文本 | `BaseInterface._ui_text()` / `framework/ui/shared/text.py` |

---

## 7. 常见问题排查

## 7.1 模块页面没出现

1. `module_specs.py` 是否注册到正确 `hosts`
2. `ui_factory` 返回的页面对象名是否正常
3. `ui_bindings.page_attr` 是否冲突或拼写错误

## 7.2 periodic 勾选了但不执行

1. `periodic_task_wiring.py` 是否存在对应 `id`
2. `default_activation_config` 格式是否正确
3. 配置中 `use_periodic` / `execution_config` 是否被覆盖

## 7.3 on_demand 日志/按钮状态异常

1. `OnDemandRunner` 状态是否及时清理
2. 模块是否绕开共享日志机制
3. 线程 stop 后是否正确回调 UI 状态

## 7.4 资源路径报错 `Cannot open file`

1. 资源是否在根目录 `resources/` 或业务 `features/assets/`
2. 代码是否还引用旧路径
3. `resources/resource.qrc` 与 `resource_qrc.py` 是否同步

---

## 8. 新贡献者最短上手路径

1. 先读第 0、1、2、3 节。
2. 跑一遍：
   - `python -m compileall app`
   - `python scripts/smoke_modules.py`
3. 按第 1 节做一个最小模块（哪怕先只打印日志）。
4. 提 PR 时按第 2 节 checklist 自检。

走完这一轮，你就能在这个项目里稳定交付一个完整模块。
