# -*- coding: utf-8 -*-
import io
import os
import zipfile


def build_app_zip_bytes(root_dir: str) -> bytes:
    """
    Create a ZIP of the whole app folder so the user can unpack it later.
    We skip Python cache artifacts to keep the archive smaller.
    """
    root_dir = os.path.abspath(root_dir)
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Skip common cache dirs.
            dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git", ".venv", "venv"}]

            for name in filenames:
                if name.endswith((".pyc", ".pyo")):
                    continue
                full_path = os.path.join(dirpath, name)
                rel = os.path.relpath(full_path, root_dir)
                zf.write(full_path, arcname=rel)

    return buf.getvalue()

