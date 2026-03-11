from __future__ import annotations

import os
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QPlainTextEdit
from qfluentwidgets import ComboBox

from app.framework.core.module_system.models import SchemaField
from app.framework.infra.config.app_config import config
from app.framework.ui.views.auto_page import AutoPage
from app.framework.ui.views import auto_page as auto_page_module

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class _DummyConfigItem:
    def __init__(self, value, default, options=None):
        self.value = value
        self.defaultValue = default
        self.options = options
        self.validator = None


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def _make_meta(*fields: SchemaField):
    return SimpleNamespace(id="fishing", name="Fishing", description="", config_schema=list(fields), actions={})


def test_combo_box_uses_config_options_values_roundtrip():
    _qapp()
    field = SchemaField(
        param_name="ComboBox_lure_type",
        field_id="ComboBox_lure_type",
        type_hint=int,
        default=0,
        required=False,
        label_key="",
        help_key="",
        label_default="Lure Type",
        help_default="",
        group="General",
        layout="half",
        icon=None,
        description_md=None,
    )
    item = _DummyConfigItem(value=1, default=0, options=[0, 1, 2, 3])

    setattr(config, field.param_name, item)
    try:
        page = AutoPage(module_meta=_make_meta(field))
        widget = page.field_widgets[field.param_name]
        assert isinstance(widget, ComboBox)
        assert widget.count() == 4

        page._set_widget_value(field, widget, 2)
        assert page._get_widget_value(field, widget) == 2
    finally:
        delattr(config, field.param_name)


def test_list_type_prefers_combo_box_adapter():
    _qapp()
    field = SchemaField(
        param_name="lure_candidates",
        field_id="lure_candidates",
        type_hint=list[str],
        default=["A", "B", "C"],
        required=False,
        label_key="",
        help_key="",
        label_default="Lure Candidates",
        help_default="",
        group="General",
        layout="half",
        icon=None,
        description_md=None,
    )
    item = _DummyConfigItem(value="B", default="A", options=["A", "B", "C"])

    setattr(config, field.param_name, item)
    try:
        page = AutoPage(module_meta=_make_meta(field))
        widget = page.field_widgets[field.param_name]
        assert isinstance(widget, ComboBox)
        page._set_widget_value(field, widget, "C")
        assert page._get_widget_value(field, widget) == "C"
    finally:
        delattr(config, field.param_name)


def test_dict_type_uses_text_edit_and_optional_int_coerces_text():
    _qapp()
    dict_field = SchemaField(
        param_name="dict_field",
        field_id="dict_field",
        type_hint=dict,
        default={"k": 1},
        required=False,
        label_key="",
        help_key="",
        label_default="Dict Field",
        help_default="",
        group="General",
        layout="full",
        icon=None,
        description_md=None,
    )
    optional_int_field = SchemaField(
        param_name="optional_num",
        field_id="optional_num",
        type_hint=int | None,
        default=None,
        required=False,
        label_key="",
        help_key="",
        label_default="Optional Num",
        help_default="",
        group="General",
        layout="half",
        icon=None,
        description_md=None,
    )

    setattr(config, dict_field.param_name, _DummyConfigItem(value={"k": 1}, default={"k": 1}))
    setattr(config, optional_int_field.param_name, _DummyConfigItem(value=None, default=None))
    try:
        page = AutoPage(module_meta=_make_meta(dict_field, optional_int_field))
        dict_widget = page.field_widgets[dict_field.param_name]
        assert isinstance(dict_widget, QPlainTextEdit)
        assert page._coerce_value_for_config(optional_int_field, "12") == 12
    finally:
        delattr(config, dict_field.param_name)
        delattr(config, optional_int_field.param_name)

def test_option_label_skips_placeholder_and_uses_generic_fallback_key():
    _qapp()
    field = SchemaField(
        param_name="ComboBox_fishing_mode",
        field_id="ComboBox_fishing_mode",
        type_hint=int,
        default=0,
        required=False,
        label_key="",
        help_key="",
        label_default="Fishing Mode",
        help_default="",
        group="General",
        layout="half",
        icon=None,
        description_md=None,
    )
    item = _DummyConfigItem(value=0, default=0, options=[0, 1])

    setattr(config, field.param_name, item)
    original_tr = auto_page_module.tr
    mapping = {
        "module.fishing.field.ComboBox_fishing_mode.option.0": "????",
        "module.fishing.option.combobox_fishing_mode.0": "GENERIC_OK",
    }

    def fake_tr(key: str, fallback=None, **_kwargs):
        if key in mapping:
            return mapping[key]
        return fallback if fallback is not None else key

    auto_page_module.tr = fake_tr
    try:
        page = AutoPage(module_meta=_make_meta(field))
        assert page._option_label(field, 0) == "GENERIC_OK"
    finally:
        auto_page_module.tr = original_tr
        delattr(config, field.param_name)


def test_explicit_option_label_without_wrapper_can_be_translated():
    _qapp()
    field = SchemaField(
        param_name="ComboBox_demo_mode",
        field_id="ComboBox_demo_mode",
        type_hint=int,
        default=0,
        required=False,
        label_key="",
        help_key="",
        label_default="Demo Mode",
        help_default="",
        group="General",
        layout="half",
        icon=None,
        description_md=None,
    )
    item = _DummyConfigItem(value=0, default=0, options=[(0, "High Performance"), (1, "Low Performance")])

    setattr(config, field.param_name, item)
    original_tr = auto_page_module.tr

    def fake_tr(key: str, fallback=None, **_kwargs):
        if key == "High Performance":
            return "ZH_HIGH"
        if key == "Low Performance":
            return "ZH_LOW"
        return fallback if fallback is not None else key

    auto_page_module.tr = fake_tr
    try:
        page = AutoPage(module_meta=_make_meta(field))
        widget = page.field_widgets[field.param_name]
        assert isinstance(widget, ComboBox)
        assert widget.itemText(0) == "ZH_HIGH"
        assert widget.itemText(1) == "ZH_LOW"
    finally:
        auto_page_module.tr = original_tr
        delattr(config, field.param_name)

