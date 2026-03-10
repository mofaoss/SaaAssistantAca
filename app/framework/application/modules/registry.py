from __future__ import annotations

from app.framework.application.modules.contracts import ModuleSpec, ModuleUiBindings
from app.framework.core.module_system import ModuleHost, get_modules_by_host, make_module_class
from app.framework.i18n.runtime import get_catalog


_DEFAULT_ZH_TITLE_FALLBACK: dict[str, str] = {
    "task_login": "自动登录",
    "task_supplies": "领取补给",
    "task_shop": "商店购买",
    "task_stamina": "领取体力",
    "task_shards": "角色碎片",
    "task_chasm": "神经模拟",
    "task_reward": "领取奖励",
    "task_operation": "行动任务",
    "task_weapon": "武器升级",
    "task_shard_exchange": "碎片兑换",
    "task_close_game": "关闭游戏",
}


def _resolve_localized_titles(meta) -> tuple[str, str]:
    key = f"module.{meta.id}.title"
    en_catalog = get_catalog("en")
    zh_cn_catalog = get_catalog("zh_CN")
    zh_hk_catalog = get_catalog("zh_HK")

    en_name = (en_catalog.get(key) or meta.en_name or meta.name or meta.id).strip()
    zh_name = (
        zh_cn_catalog.get(key)
        or zh_hk_catalog.get(key)
        or en_name
    ).strip()

    # i18n tooling may keep zh catalogs in English; preserve localized runtime UX for core periodic tasks.
    if zh_name == en_name:
        zh_name = _DEFAULT_ZH_TITLE_FALLBACK.get(meta.id, zh_name)

    return zh_name, en_name


def _meta_to_spec(meta, host: ModuleHost) -> ModuleSpec:
    if meta.ui_factory is None:
        if meta.page_cls is not None:
            meta.ui_factory = lambda parent, _host: meta.page_cls(parent)
        else:
            from app.framework.ui.views.auto_page import AutoPage

            meta.ui_factory = lambda parent, host_ctx, _meta=meta: AutoPage(parent, module_meta=_meta, host_context=host_ctx)

    if meta.ui_bindings is None:
        meta.ui_bindings = ModuleUiBindings(
            page_attr=f"page_{meta.id}",
            start_button_attr="PushButton_start",
            card_widget_attr="SimpleCardWidget_option",
            log_widget_attr="textBrowser_log",
        )

    module_class = meta.module_class or make_module_class(meta)
    zh_name, en_name = _resolve_localized_titles(meta)
    return ModuleSpec(
        id=meta.id,
        zh_name=zh_name,
        en_name=en_name,
        order=meta.order,
        hosts=(host,),
        ui_factory=meta.ui_factory,
        module_class=module_class,
        ui_bindings=meta.ui_bindings,
        passive=meta.passive,
    )


def get_periodic_module_specs() -> list[ModuleSpec]:
    metas = get_modules_by_host(ModuleHost.PERIODIC)
    return [_meta_to_spec(meta, ModuleHost.PERIODIC) for meta in metas]


def get_on_demand_module_specs(*, include_passive: bool = True) -> list[ModuleSpec]:
    metas = get_modules_by_host(ModuleHost.ON_DEMAND)
    if not include_passive:
        metas = [meta for meta in metas if not meta.passive]
    return [_meta_to_spec(meta, ModuleHost.ON_DEMAND) for meta in metas]
