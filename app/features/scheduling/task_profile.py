# coding:utf-8
from __future__ import annotations

from dataclasses import dataclass

from app.features.modules.chasm.usecase.chasm_usecase import ChasmModule
from app.features.modules.close_game.usecase.close_game_usecase import CloseGameModule
from app.features.modules.collect_supplies.usecase.collect_supplies_usecase import CollectSuppliesModule
from app.features.modules.enter_game.usecase.enter_game_usecase import EnterGameModule
from app.features.modules.get_reward.usecase.get_reward_usecase import GetRewardModule
from app.features.modules.jigsaw.usecase.shard_exchange_usecase import ShardExchangeModule
from app.features.modules.operation_action.usecase.operation_usecase import OperationModule
from app.features.modules.person.usecase.person_usecase import PersonModule
from app.features.modules.shopping.usecase.shopping_usecase import ShoppingModule
from app.features.modules.upgrade.usecase.weapon_upgrade_usecase import WeaponUpgradeModule
from app.features.modules.use_power.usecase.use_power_usecase import UsePowerModule
from app.features.scheduling.periodic_specs import PERIODIC_TASK_SPECS, PRIMARY_PERIODIC_TASK_ID


@dataclass(frozen=True)
class PeriodicTaskProfile:
    task_registry: dict[str, dict]
    primary_task_id: str
    mandatory_task_ids: frozenset[str]
    force_first_task_ids: frozenset[str]
    primary_option_key: str


_PERIODIC_MODULE_CLASS_BY_TASK_ID = {
    "task_login": EnterGameModule,
    "task_supplies": CollectSuppliesModule,
    "task_shop": ShoppingModule,
    "task_stamina": UsePowerModule,
    "task_shards": PersonModule,
    "task_chasm": ChasmModule,
    "task_reward": GetRewardModule,
    "task_operation": OperationModule,
    "task_weapon": WeaponUpgradeModule,
    "task_shard_exchange": ShardExchangeModule,
    "task_close_game": CloseGameModule,
}

_CACHED_PROFILE: PeriodicTaskProfile | None = None


def _build_task_registry() -> dict[str, dict]:
    registry: dict[str, dict] = {}
    for spec in PERIODIC_TASK_SPECS:
        task_id = spec["id"]
        registry[task_id] = {
            "module_class": _PERIODIC_MODULE_CLASS_BY_TASK_ID[task_id],
            "ui_page_index": spec.get("ui_page_index"),
            "option_key": spec.get("option_key"),
            "zh_name": spec["zh_name"],
            "en_name": spec["en_name"],
            "requires_home_sync": spec.get("requires_home_sync", True),
            "is_mandatory": spec.get("is_mandatory", False),
            "force_first": spec.get("force_first", False),
        }
    return registry


def get_periodic_task_profile() -> PeriodicTaskProfile:
    global _CACHED_PROFILE
    if _CACHED_PROFILE is not None:
        return _CACHED_PROFILE

    registry = _build_task_registry()
    mandatory_task_ids = frozenset(
        task_id for task_id, meta in registry.items() if bool(meta.get("is_mandatory", False))
    )
    force_first_task_ids = frozenset(
        task_id for task_id, meta in registry.items() if bool(meta.get("force_first", False))
    )
    primary_option_key = registry.get(PRIMARY_PERIODIC_TASK_ID, {}).get("option_key", "CheckBox_entry_1")

    _CACHED_PROFILE = PeriodicTaskProfile(
        task_registry=registry,
        primary_task_id=PRIMARY_PERIODIC_TASK_ID,
        mandatory_task_ids=mandatory_task_ids,
        force_first_task_ids=force_first_task_ids,
        primary_option_key=primary_option_key,
    )
    return _CACHED_PROFILE

