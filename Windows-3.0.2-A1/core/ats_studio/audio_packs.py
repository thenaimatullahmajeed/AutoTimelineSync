"""Verified, local audio packs. File paths cannot escape the pack directory."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re


def packs_dir() -> Path:
    from .user_data import user_data_root
    return user_data_root() / 'packs'


def installed_user_assets() -> tuple[dict, list[str]]:
    assets = {}; warnings = []
    root = packs_dir()
    for manifest in sorted(root.glob('*/manifest.json')):
        try:
            data = json.loads(manifest.read_text(encoding='utf-8'))
            pack_id = data['id']
            if not re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}',pack_id):
                raise ValueError('invalid pack id')
            entries = data['assets']
            if not isinstance(entries,list): raise ValueError('assets must be an array')
            pending = {}
            for item in entries:
                key = item['id']; kind = item['kind']
                if not re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}',key) or kind not in {'sfx','music','ambience'}:
                    raise ValueError('invalid asset id or kind')
                if not item.get('license') or not item.get('author') or not item.get('source'):
                    raise ValueError(f'{key}: license, author and source are required')
                duration = item['duration_s']; loudness = item['loudness_lufs']
                if isinstance(duration,bool) or not isinstance(duration,(int,float)) or not math.isfinite(duration) or duration<=0:
                    raise ValueError(f'{key}: invalid duration')
                if kind=='sfx' and duration>1.2:raise ValueError(f'{key}: SFX must be <=1.2 seconds')
                if isinstance(loudness,bool) or not isinstance(loudness,(int,float)) or not math.isfinite(loudness):
                    raise ValueError(f'{key}: invalid loudness')
                variants = item['variants']
                if not isinstance(variants,list) or not 1<=len(variants)<=9:raise ValueError(f'{key}: 1..9 variants required')
                files=[]
                for variant in variants:
                    path=(manifest.parent/variant['file']).resolve()
                    if not path.is_relative_to(manifest.parent.resolve()) or not path.is_file():
                        raise ValueError(f'{key}: missing file or path outside pack')
                    if path.suffix.lower() not in {'.wav','.mp3','.m4a','.flac','.ogg'}:
                        raise ValueError(f'{key}: unsupported audio file')
                    digest=hashlib.sha256(path.read_bytes()).hexdigest()
                    if digest!=variant['sha256']:raise ValueError(f'{key}: SHA-256 mismatch')
                    files.append(path)
                identity=(kind,key)
                if identity in assets or identity in pending:raise ValueError(f'duplicate {kind} id {key}')
                pending[identity]={**item,'pack':pack_id,'files':files}
            assets.update(pending)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            warnings.append(f'Audio pack {manifest.parent.name} skipped: {exc}')
    return assets,warnings


def asset_ids(kind: str, builtin) -> frozenset:
    assets,_=installed_user_assets()
    return frozenset(builtin)|{key for (category,key) in assets if category==kind}


def pack_ids() -> set[str]:
    assets,_=installed_user_assets()
    return {'SFX_ARCHIVE_V1'}|{asset['pack'] for asset in assets.values()}
