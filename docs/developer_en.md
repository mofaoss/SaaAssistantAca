# SAA Developer Guide (English)

> 中文版: `docs/developer.md`  
> Goal: help any contributor understand the current architecture quickly and ship a complete module PR end-to-end.

## 1. Architecture Overview

The project now uses a two-root + composition-root model:

- `app/framework`: reusable framework layer
- `app/features`: game/business layer

Core principles:

1. `framework` should not hardcode game-specific business logic.
2. `features` wires concrete business implementations into framework via `bootstrap`.
3. `periodic` and `on_demand` share one module protocol; only scheduling strategy differs.
4. Each module owns its own `ui + usecase`; host pages focus on registration, layout, intent emission, and state rendering.

---

## 2. Startup and Dependency Injection Flow

1. `SAA.py` bootstraps Qt and runs `StartupController`.
2. `_create_main_window()` builds a feature bridge through `build_main_window_bridge()`.
3. `MainWindow(feature_bridge=...)` asks the bridge to:
   - configure module registry
   - create periodic page
   - create on-demand page
   - initialize OCR
4. Host pages load module specs dynamically from registry and mount module UIs.

This keeps `framework` interface-driven and `features` implementation-driven.

---

## 3. Directory and Key File Responsibilities

### 3.1 Entry and Build

| File | Responsibility |
|---|---|
| `SAA.py` | App entry, startup task pipeline, main window creation, translators. |
| `requirements.txt` | Python dependencies. |
| `PerfectBuild/build.py` | Build scripts (Nuitka/PyInstaller/installer flow). |
| `PerfectBuild/perfect_build.py` | Build metadata (version/name/icon). |
| `PerfectBuild/assets/shapely.libs/.load-order-shapely-2.0.7` | Shapely load-order patch included at build time. |

### 3.2 `app/framework/application`

#### modules

| File | Responsibility |
|---|---|
| `framework/application/modules/contracts.py` | Module contracts (`ModuleSpec`, `HostContext`, `ModuleUiBindings`). |
| `framework/application/modules/registry.py` | Provider registration and dynamic module-spec retrieval. |

#### periodic (application-level scheduling)

| File | Responsibility |
|---|---|
| `framework/application/periodic/periodic_controller.py` | Periodic run state machine and thread lifecycle. |
| `framework/application/periodic/periodic_orchestration.py` | Pure orchestration helpers (task selection/rule copy/formatting). |
| `framework/application/periodic/periodic_dispatcher.py` | Schedule/runtime message dispatching helpers. |
| `framework/application/periodic/periodic_page_actions.py` | Page-level actions use cases (presets/rules/runtime). |
| `framework/application/periodic/periodic_settings_usecase.py` | Periodic settings read/write behavior. |
| `framework/application/periodic/periodic_ui_binding_usecase.py` | UI-control to config binding wiring. |
| `framework/application/periodic/on_demand_runner.py` | Single-task runner strategy for on-demand host. |

#### tasks (compatibility + bridge)

| File | Responsibility |
|---|---|
| `framework/application/tasks/periodic_task_specs.py` | Bridge to feature-side periodic specs provider. |
| `framework/application/tasks/periodic_defaults.py` | Bridge to feature-side periodic default sequence builder. |
| `framework/application/tasks/periodic_task_profile.py` | Merges periodic specs and module registry into runtime profile. |
| `framework/application/tasks/task_definition.py` | Legacy-compatible task definition model. |
| `framework/application/tasks/task_registry.py` | Legacy registry generated from unified module registry. |
| `framework/application/tasks/task_policy.py` | Task policy constants (for example primary task id). |
| `framework/application/tasks/sequence_serializer.py` | Sequence serialization helper. |

#### other application domains

| File | Responsibility |
|---|---|
| `framework/application/hotkey/routing.py` | Global F8 action routing by context. |
| `framework/application/startup/interface_plan.py` | Startup/deferred interface creation planning. |

### 3.3 `app/framework/core`

#### interfaces

| File | Responsibility |
|---|---|
| `framework/core/interfaces/main_window_bridge.py` | Main-window feature bridge protocol. |
| `framework/core/interfaces/game_environment.py` | Runtime game environment interface. |
| `framework/core/interfaces/periodic_ports.py` | Ports consumed by periodic page (enter game/supplies/tips/etc.). |

#### task_engine

| File | Responsibility |
|---|---|
| `framework/core/task_engine/base_task.py` | Base task context (`auto` init and ratio checks). |
| `framework/core/task_engine/runtime_session.py` | Automation session lifecycle (`prepare/reset/stop`). |
| `framework/core/task_engine/threads.py` | Queue thread and single-module thread implementations. |
| `framework/core/task_engine/scheduler.py` | Periodic rule polling and task triggering. |
| `framework/core/task_engine/hotkey_poller.py` | Global hotkey polling utility. |

#### other core domains

| File | Responsibility |
|---|---|
| `framework/core/event_bus/global_task_bus.py` | Cross-page run-state and stop-request bus. |
| `framework/core/config/daily_sequence.py` | Task sequence normalization. |
| `framework/core/config/migration.py` | Sequence schema migration. |
| `framework/core/observability/error_codes.py` | App error code definitions. |
| `framework/core/observability/reporting.py` | Exception capture/wrapping. |

### 3.4 `app/framework/infra`

| Path | Responsibility |
|---|---|
| `framework/infra/automation/*` | Low-level automation (input/screenshot/window tracking/timers). |
| `framework/infra/vision/*` | Image matching and OCR services. |
| `framework/infra/config/app_config.py` | Global config schema/defaults/serialization. |
| `framework/infra/config/setting.py` | App constants and config file path. |
| `framework/infra/config/json_parser.py` | JSON parser helpers. |
| `framework/infra/logging/gui_logger.py` | UI logger pipe. |
| `framework/infra/events/signal_bus.py` | Qt signal bus. |
| `framework/infra/runtime/paths.py` | Runtime paths (`runtime/appdata/log/temp`). |
| `framework/infra/system/windows.py` | Windows handle/window primitives. |
| `framework/infra/system/cpu.py` | CPU capability checks. |
| `framework/infra/update/updater.py` | Update checks and update helpers. |

### 3.5 `app/framework/ui`

#### shared

| File | Responsibility |
|---|---|
| `framework/ui/shared/text.py` | language-aware text helper. |
| `framework/ui/shared/style_sheet.py` | QSS entry points. |
| `framework/ui/shared/icon.py` | icon wrappers. |
| `framework/ui/shared/localizer.py` | Traditional Chinese localization patching. |
| `framework/ui/shared/widget_tree.py` | widget-tree traversal helper. |

#### views

| File | Responsibility |
|---|---|
| `framework/ui/views/main_window.py` | Main shell, navigation, tray, global F8 dispatch. |
| `framework/ui/views/periodic_tasks_page.py` | Periodic host page (render + intent + scheduler integration). |
| `framework/ui/views/periodic_tasks_view.py` | Periodic pure view container. |
| `framework/ui/views/on_demand_tasks_page.py` | On-demand host page (single-run strategy + shared log). |
| `framework/ui/views/on_demand_tasks_view.py` | On-demand pure view container. |
| `framework/ui/views/periodic_base.py` | `BaseInterface` and `ModulePageBase` unified base. |
| `framework/ui/views/display.py` | Display page. |
| `framework/ui/views/help.py` | Help page. |
| `framework/ui/views/setting_view.py` | Settings page. |
| `framework/ui/views/ocr_replacement_table*.py` | OCR replacement table UI. |

#### widgets

`framework/ui/widgets/*` contains reusable widgets (message box, cards, tree, slider cards, etc.).

### 3.6 `app/features`

#### bootstrap (feature composition roots)

| File | Responsibility |
|---|---|
| `features/bootstrap/main_window_wiring.py` | Wires business implementations into framework interfaces. |
| `features/bootstrap/periodic_task_wiring.py` | Feature-side periodic scheduling metadata/default sequence source. |

#### modules

- Standard module layout: `features/modules/<module>/ui` + `features/modules/<module>/usecase`
- Unified registration source: `features/modules/module_specs.py`
- Module starter template: `features/modules/_template/README.md`

Current module IDs from registry:

| id | host | UI example | Usecase example |
|---|---|---|---|
| `task_login` | periodic | `enter_game/ui/enter_game_periodic_page.py` | `enter_game/usecase/enter_game_usecase.py` |
| `task_supplies` | periodic | `collect_supplies/ui/collect_supplies_periodic_page.py` | `collect_supplies/usecase/collect_supplies_usecase.py` |
| `task_shop` | periodic | `shopping/ui/shop_periodic_page.py` | `shopping/usecase/shopping_usecase.py` |
| `task_stamina` | periodic | `use_power/ui/use_power_periodic_page.py` | `use_power/usecase/use_power_usecase.py` |
| `task_shards` | periodic | `person/ui/person_periodic_page.py` | `person/usecase/person_usecase.py` |
| `task_chasm` | periodic | `chasm/ui/chasm_periodic_page.py` | `chasm/usecase/chasm_usecase.py` |
| `task_reward` | periodic | `get_reward/ui/reward_periodic_page.py` | `get_reward/usecase/get_reward_usecase.py` |
| `task_operation` | periodic | `operation_action/ui/operation_periodic_page.py` | `operation_action/usecase/operation_usecase.py` |
| `task_weapon` | periodic | `upgrade/ui/weapon_upgrade_periodic_page.py` | `upgrade/usecase/weapon_upgrade_usecase.py` |
| `task_shard_exchange` | periodic | `jigsaw/ui/shard_exchange_periodic_page.py` | `jigsaw/usecase/shard_exchange_usecase.py` |
| `task_close_game` | periodic | `close_game/ui/close_game_periodic_page.py` | `close_game/usecase/close_game_usecase.py` |
| `trigger` | on_demand | `trigger/ui/trigger_interface.py` | `trigger/usecase/auto_f_usecase.py` |
| `fishing` | on_demand | `fishing/ui/fishing_interface.py` | `fishing/usecase/fishing_usecase.py` |
| `action` | on_demand | `operation_action/ui/operation_interface.py` | `operation_action/usecase/operation_usecase.py` |
| `water_bomb` | on_demand | `water_bomb/ui/water_bomb_interface.py` | `water_bomb/usecase/water_bomb_usecase.py` |
| `alien_guardian` | on_demand | `alien_guardian/ui/alien_guardian_interface.py` | `alien_guardian/usecase/alien_guardian_usecase.py` |
| `maze` | on_demand | `maze/ui/maze_interface.py` | `maze/usecase/maze_usecase.py` |
| `drink` | on_demand | `drink/ui/drink_interface.py` | `drink/usecase/drink_usecase.py` |
| `capture_pals` | on_demand | `capture_pals/ui/capture_pals_interface.py` | `capture_pals/usecase/capture_pals_usecase.py` |

#### assets and utils

| Path | Responsibility |
|---|---|
| `features/assets/<module>/*` | business image assets (template matching/tutorial assets). |
| `features/utils/home_navigation.py` | business home-navigation flow. |
| `features/utils/network.py` | feature-side update/event data fetchers. |
| `features/utils/updater.py` | update helper logic. |
| `features/utils/randoms.py` | feature random helpers. |
| `features/utils/text_normalizer.py` | feature text normalization helper. |

---

## 4. Build a New Module Quickly

## 4.1 Pick module type

- Periodic module: schedulable, appears in periodic task queue.
- On-demand module: single-run start/stop flow.
- Passive module: helper UI/capability not included in normal queue (`passive=True`).

## 4.2 Create structure

```text
app/features/modules/<your_module>/
  ui/
  usecase/
```

## 4.3 Implement usecase class (minimum contract)

```python
class YourModule:
    def __init__(self, auto, logger):
        self.auto = auto
        self.logger = logger

    def run(self):
        ...
```

Best practices:

1. Start each loop with screenshot refresh.
2. Always include timeout/escape conditions.
3. Use logger for key transitions only.
4. Avoid hardcoded absolute resolution assumptions.

## 4.4 Implement UI with unified base

```python
from app.framework.ui.views.periodic_base import ModulePageBase

class YourPage(ModulePageBase):
    def __init__(self, parent=None):
        super().__init__("page_your_module", parent=parent, host_context="periodic", use_default_layout=True)
        ...
        self.finalize()
```

`bind_host_context()` automatically applies sizing strategy for periodic vs on-demand context.

## 4.5 Register in module specs

Add a `ModuleSpec` in `features/modules/module_specs.py`:

- `id`
- `hosts`
- `ui_factory`
- `module_class`
- `ui_bindings`

## 4.6 For periodic modules, add scheduling metadata

Update `features/bootstrap/periodic_task_wiring.py` with:

- `id`
- `ui_page_index`
- `option_key`
- `default_activation_config`
- optional flags: `requires_home_sync`, `is_mandatory`, `force_first`

This file is for scheduling metadata only, not for UI display text.

## 4.7 If special business actions are needed, use ports

Define/extend ports in `framework/core/interfaces/periodic_ports.py`, implement in `features`, and inject through `features/bootstrap/main_window_wiring.py`.  
Do not hardwire concrete business imports into low-level framework modules.

## 4.8 Asset path rules

1. Business assets live in `app/features/assets/...`
2. Shared UI icons/qss/i18n live in root `resources/`
3. Never reintroduce old paths like `app/presentation/resources/*` or `app/framework/ui/resources/*`

---

## 5. Infrastructure Quick Reference

| Need | Use |
|---|---|
| execute automation in module | `self.auto` from runtime session |
| read config | `app.framework.infra.config.app_config.config` |
| write UI logs | injected `logger` |
| queue periodic tasks | `TaskQueueThread` via `PeriodicController` |
| run one module | `ModuleTaskThread` via `OnDemandRunner` |
| publish cross-page state | `global_task_bus.publish_state(...)` |
| trigger global stop | `global_task_bus.request_stop()` |
| i18n text | `BaseInterface._ui_text()` / `framework/ui/shared/text.py` |

---

## 6. PR Standards and Engineering Process

## 6.1 Architecture gates

1. No direct business-module dependency in `framework/core` or `framework/infra`.
2. No game-specific business logic hardcoded in generic framework UI shell.
3. Module registration must go through `features/modules/module_specs.py`.
4. Periodic default/schedule metadata must be centralized in `features/bootstrap/periodic_task_wiring.py`.
5. New business images must be under `features/assets` with updated code references.

## 6.2 Required local checks

```bash
python -m compileall app
python -m py_compile SAA.py
python scripts/smoke_modules.py
python scripts/smoke_release.py
python scripts/release_cleanup_pack.py --startup-seconds 8
```

Must satisfy:

1. no `ModuleNotFoundError / ImportError / NameError`
2. no UI construction failure in smoke checks
3. startup smoke should not crash early

## 6.3 PR workflow (recommended)

1. Sync `main`, create a feature branch (recommended prefix: `codex/`).
2. Commit in small logical chunks.
3. PR description should include:
   - why this change exists
   - architectural impact (layers/files touched)
   - verification commands and outputs
   - risk and rollback notes
4. Include screenshots/videos for UI changes.

## 6.4 Auto-reject conditions

1. Business logic leaked back into framework generic layer.
2. Hardcoded page/module assembly bypassing registry.
3. Resource path refactor without runtime path fix (`Cannot open file ...` errors).
4. Thread lifecycle leaks (`QThread: Destroyed while thread is still running`).
5. Missing verification evidence.

---

## 7. Troubleshooting

## 7.1 Module not visible

Check:

1. host registration in `module_specs.py`
2. `ui_factory` returns page with valid object name
3. `ui_bindings.page_attr` is unique and accessible

## 7.2 Periodic task never runs

Check:

1. task id exists in `periodic_task_wiring.py`
2. `default_activation_config` schema is valid
3. runtime config has `use_periodic/execution_config` enabled

## 7.3 On-demand log/state mismatch

Check:

1. `OnDemandRunner` state clear path
2. injected `module_thread_cls`
3. module trying to bypass shared log behavior

## 7.4 Tray icon missing

Check:

1. icon files under root `resources/icons` and `resources/logo`
2. `resources/resource.qrc` includes them and `resource_qrc.py` is up to date

---

## 8. Fastest Path for New Contributors

1. Read sections 1, 2, 4, 6 first.
2. Run:
   - `python -m compileall app`
   - `python scripts/smoke_modules.py`
3. Copy `_template`, create a minimal module, register it in `module_specs.py`.
4. Ensure it mounts and starts cleanly.
5. Then add real business logic and config binding.

Once you can finish that loop, you can independently deliver production-grade module PRs in this repo.
