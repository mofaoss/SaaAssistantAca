from app.framework.infra.config.app_config import is_non_chinese_ui_language


def ui_text(zh_text: str, en_text: str) -> str:
    """Framework-level bilingual text selector."""
    if is_non_chinese_ui_language():
        return en_text
    return zh_text

