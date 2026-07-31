from pathlib import Path
import os

from PyInstaller.utils.hooks import collect_all

root = Path(SPEC).resolve().parent
age_executable = Path(os.environ["RBF_AGE_EXE"]).resolve()
age_keygen_executable = Path(os.environ["RBF_AGE_KEYGEN_EXE"]).resolve()
output_name = os.environ.get("RBF_OUTPUT_NAME", "RBF-Recovery-Tool")
for executable, label in (
    (age_executable, "age"),
    (age_keygen_executable, "age-keygen"),
):
    if not executable.is_file():
        raise SystemExit(f"{label} executable not found: {executable}")

# Both executables retain their native platform names inside the frozen bundle.
datas = []
binaries = [
    (str(age_executable), "bin"),
    (str(age_keygen_executable), "bin"),
]
hiddenimports = []
for package in ("paramiko", "cryptography", "bcrypt", "nacl"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

a = Analysis(
    [str(root / "src/launcher.py")],
    pathex=[str(root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=output_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
