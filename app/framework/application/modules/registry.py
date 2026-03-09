from __future__ import annotations

import importlib
from collections.abc import Callable

from app.framework.application.modules.contracts import ModuleSpec


_periodic_specs_provider: Callable[[], list[ModuleSpec]] | None = None
_on_demand_specs_provider: Callable[[], list[ModuleSpec]] | None = None


def configure_module_spec_providers(
    *,
    periodic_provider: Callable[[], list[ModuleSpec]] | None = None,
    on_demand_provider: Callable[[], list[ModuleSpec]] | None = None,
) -> None:
    global _periodic_specs_provider
    global _on_demand_specs_provider
    if periodic_provider is not None:
        _periodic_specs_provider = periodic_provider
    if on_demand_provider is not None:
        _on_demand_specs_provider = on_demand_provider


def _default_periodic_provider() -> list[ModuleSpec]:
    module = importlib.import_module("app.features.modules.module_specs")
    provider = getattr(module, "get_periodic_module_specs", None)
    if callable(provider):
        return list(provider())
    return []


def _default_on_demand_provider() -> list[ModuleSpec]:
    module = importlib.import_module("app.features.modules.module_specs")
    provider = getattr(module, "get_on_demand_module_specs", None)
    if callable(provider):
        return list(provider(include_passive=True))
    return []


def get_periodic_module_specs() -> list[ModuleSpec]:
    provider = _periodic_specs_provider or _default_periodic_provider
    return sorted(list(provider()), key=lambda item: item.order)


def get_on_demand_module_specs(*, include_passive: bool = True) -> list[ModuleSpec]:
    provider = _on_demand_specs_provider or _default_on_demand_provider
    specs = sorted(list(provider()), key=lambda item: item.order)
    if include_passive:
        return specs
    return [spec for spec in specs if not spec.passive]

