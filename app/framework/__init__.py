from app.framework.i18n import install_global_translate_symbol
from app.framework.i18n.import_rewrite import install_import_rewrite

# Ensure `_()` is always available from builtins for all app.framework modules,
# so rewritten callsites don't need per-file imports.
install_global_translate_symbol()
install_import_rewrite()
