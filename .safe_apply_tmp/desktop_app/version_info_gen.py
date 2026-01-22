from __future__ import annotations

import json
from pathlib import Path

def _load_meta(repo_root: Path) -> dict:
    p = repo_root / "desktop_app" / "app_meta.json"
    return json.loads(p.read_text(encoding="utf-8"))

def _split_version(v: str) -> tuple[int,int,int,int]:
    parts = [int(x) for x in str(v).strip().split(".") if x.strip().isdigit()]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])

def build_version_info_text(*, version: str, company: str, product: str, description: str) -> str:
    a,b,c,d = _split_version(version)
    # PyInstaller's version file format (VSVersionInfo)
    # Keep it strict and stable.
    return f'''
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({a},{b},{c},{d}),
    prodvers=({a},{b},{c},{d}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [
        StringStruct('CompanyName', '{company}'),
        StringStruct('FileDescription', '{description}'),
        StringStruct('FileVersion', '{version}'),
        StringStruct('InternalName', '{product}'),
        StringStruct('OriginalFilename', '{product}.exe'),
        StringStruct('ProductName', '{product}'),
        StringStruct('ProductVersion', '{version}')
        ])
      ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
'''.lstrip()

def generate_version_file(repo_root: Path) -> Path:
    meta = _load_meta(repo_root)
    version = str(meta.get("version","0.1.0"))
    company = str(meta.get("company_name","CryptoBotPro"))
    product = str(meta.get("app_name","CryptoBotPro"))
    desc = str(meta.get("display_name","Crypto Bot Pro"))

    out = repo_root / "desktop_app" / "version_info.txt"
    out.write_text(build_version_info_text(
        version=version, company=company, product=product, description=desc
    ), encoding="utf-8")
    return out
