# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/naima/.codex/.chatgpt-projects/g-p-6ab65feb00b48191a24211d8511a485f/ats_windows_3_0_2/core/launch.py'],
    pathex=['C:/Users/naima/.codex/.chatgpt-projects/g-p-6ab65feb00b48191a24211d8511a485f/ats_windows_3_0_2/core'],
    binaries=[],
    datas=[('C:/Users/naima/.codex/.chatgpt-projects/g-p-6ab65feb00b48191a24211d8511a485f/ats_windows_3_0_2/core/assets', 'assets'), ('C:/Users/naima/.codex/.chatgpt-projects/g-p-6ab65feb00b48191a24211d8511a485f/ats_windows_3_0_2/core/presets', 'presets')],
    hiddenimports=['ats_studio', 'ats_studio.__main__', 'ats_studio.assets', 'ats_studio.audio_packs', 'ats_studio.capabilities', 'ats_studio.caption_presets', 'ats_studio.cinematic_transitions', 'ats_studio.fast_audio', 'ats_studio.finishing', 'ats_studio.fonts', 'ats_studio.hardware', 'ats_studio.linter', 'ats_studio.media', 'ats_studio.moments', 'ats_studio.music', 'ats_studio.portable_smoke', 'ats_studio.pro_audio', 'ats_studio.pro_compositor', 'ats_studio.pro_renderer', 'ats_studio.pro_schema', 'ats_studio.pro_spec', 'ats_studio.product', 'ats_studio.project_settings', 'ats_studio.renderer', 'ats_studio.schema', 'ats_studio.ui', 'ats_studio.ui_parts', 'ats_studio.ui_parts.audio_workers', 'ats_studio.ui_parts.common', 'ats_studio.ui_parts.dialogs', 'ats_studio.ui_parts.inspector', 'ats_studio.ui_parts.views', 'ats_studio.ui_parts.workers', 'ats_studio.user_data', 'ats_studio.visual_director'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoTimelineSync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:/Users/naima/.codex/.chatgpt-projects/g-p-6ab65feb00b48191a24211d8511a485f/ats_windows_3_0_2/core/assets/icons/AutoTimelineSync.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoTimelineSync',
)
