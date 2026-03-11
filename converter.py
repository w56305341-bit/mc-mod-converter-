"""
ModConverter - Core Engine
Handles: extraction, manifest generation, packaging → .mcaddon / .mcpack
"""

import os
import uuid
import json
import shutil
import zipfile
import tempfile
import random
import string
from datetime import datetime


# ─── Minecraft pack name word banks ───
_ADJECTIVES = [
    "Epic", "Ancient", "Mystic", "Shadow", "Crystal", "Nether",
    "Celestial", "Cursed", "Golden", "Emerald", "Obsidian", "Blazing",
    "Frozen", "Storm", "Phantom", "Arcane", "Void", "Enchanted",
]
_NOUNS = [
    "Realms", "Overhaul", "Edition", "Pack", "World", "Dimension",
    "Tweaks", "Legends", "Chronicles", "Saga", "Origins", "Expansion",
    "Mod", "Add-On", "Adventures", "Remix", "Reborn",
]


def _random_name() -> str:
    return f"{random.choice(_ADJECTIVES)} {random.choice(_NOUNS)}"


def _random_version() -> list:
    return [random.randint(0, 1), random.randint(0, 9), random.randint(0, 20)]


class ModConverter:
    """Converts raw mod folders/ZIPs into valid .mcaddon or .mcpack files."""

    def __init__(self, status_callback=None):
        self._log = status_callback or (lambda msg, *a, **kw: print(msg))

    # ─────────────────────────────────────────────
    #  Public API
    # ─────────────────────────────────────────────

    def convert(self, source_path: str, output_format: str = "mcaddon") -> str | None:
        """
        Main entry point.
        Returns path to the generated .mcaddon / .mcpack, or None on failure.
        """
        try:
            with tempfile.TemporaryDirectory() as work_dir:
                self._log("📂 Extracting source files...", "folder-zip", (0.4, 0.8, 1, 1))
                extracted = self._extract(source_path, work_dir)

                self._log("🔍 Analysing pack structure...", "magnify", (0.7, 0.7, 1, 1))
                pack_root = self._find_pack_root(extracted)

                self._log("📝 Generating manifest.json...", "file-document-edit", (1, 0.85, 0.2, 1))
                manifest = self._ensure_manifest(pack_root)
                pack_name = manifest["header"]["name"]
                self._log(f'   Pack name: "{pack_name}"', "tag", (0.8, 0.8, 0.8, 1))

                self._log("📦 Packaging into archive...", "package-variant-closed", (0.5, 0.9, 0.5, 1))
                output_path = self._package(pack_root, pack_name, output_format)

            self._log(f"✔ Saved: {os.path.basename(output_path)}", "check-bold", (0.1, 1, 0.4, 1))
            return output_path

        except Exception as e:
            self._log(f"❌ Error: {e}", "alert-circle", (1, 0.3, 0.3, 1))
            raise

    # ─────────────────────────────────────────────
    #  Step 1 – Extract
    # ─────────────────────────────────────────────

    def _extract(self, source_path: str, work_dir: str) -> str:
        dest = os.path.join(work_dir, "src")
        os.makedirs(dest, exist_ok=True)

        if os.path.isdir(source_path):
            # Folder selected – copy everything in
            shutil.copytree(source_path, dest, dirs_exist_ok=True)
        elif zipfile.is_zipfile(source_path):
            with zipfile.ZipFile(source_path, "r") as zf:
                zf.extractall(dest)
        else:
            raise ValueError(f"Unsupported source type: {source_path}")

        return dest

    # ─────────────────────────────────────────────
    #  Step 2 – Find real pack root
    # ─────────────────────────────────────────────

    def _find_pack_root(self, extracted: str) -> str:
        """
        Some ZIPs wrap everything in a single subfolder.
        Walk up until we find a directory that has pack content.
        """
        for root, dirs, files in os.walk(extracted):
            # Signs of a pack root: manifest.json OR known folders
            has_manifest = "manifest.json" in files
            has_pack_dirs = any(
                d in dirs
                for d in (
                    "behaviors", "resources", "scripts",
                    "entities", "textures", "models", "items",
                    "blocks", "animations", "render_controllers",
                )
            )
            if has_manifest or has_pack_dirs:
                return root

        # No recognisable structure – treat top-level as root
        return extracted

    # ─────────────────────────────────────────────
    #  Step 3 – manifest.json
    # ─────────────────────────────────────────────

    def _ensure_manifest(self, pack_root: str) -> dict:
        manifest_path = os.path.join(pack_root, "manifest.json")

        # ── Already has manifest ──
        if os.path.isfile(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                self._log("   Found existing manifest.json ✓", "check", (0.5, 1, 0.5, 1))
                existing = self._patch_manifest(existing)
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2)
                return existing
            except (json.JSONDecodeError, KeyError):
                self._log("   Existing manifest invalid – regenerating...", "alert", (1, 0.7, 0.2, 1))

        # ── Generate new manifest ──
        pack_type = self._detect_pack_type(pack_root)
        manifest = self._generate_manifest(pack_type)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        self._log(f"   Created manifest (type: {pack_type})", "file-plus", (0.4, 1, 0.6, 1))
        return manifest

    def _detect_pack_type(self, pack_root: str) -> str:
        """Heuristic: does this look like a resource pack or behaviour pack?"""
        entries = set(os.listdir(pack_root))
        resource_hints = {"textures", "sounds", "ui", "font", "models"}
        behaviour_hints = {"behaviors", "scripts", "entities", "items", "blocks", "animations"}
        is_resource = bool(entries & resource_hints)
        is_behaviour = bool(entries & behaviour_hints)

        if is_resource and not is_behaviour:
            return "resources"
        if is_behaviour and not is_resource:
            return "data"
        # Mixed or unknown → addon (both)
        return "addon"

    def _generate_manifest(self, pack_type: str) -> dict:
        name = _random_name()
        version = _random_version()

        base = {
            "format_version": 2,
            "header": {
                "description": f"Auto-converted pack – {name}",
                "name": name,
                "uuid": str(uuid.uuid4()),
                "version": version,
                "min_engine_version": [1, 20, 0],
            },
            "modules": [],
        }

        if pack_type == "resources":
            base["modules"].append({
                "description": "Resource module",
                "type": "resources",
                "uuid": str(uuid.uuid4()),
                "version": version,
            })
        elif pack_type == "data":
            base["modules"].append({
                "description": "Behaviour module",
                "type": "data",
                "uuid": str(uuid.uuid4()),
                "version": version,
            })
        else:
            # Full addon – add both
            base["modules"].append({
                "description": "Behaviour module",
                "type": "data",
                "uuid": str(uuid.uuid4()),
                "version": version,
            })
            base["modules"].append({
                "description": "Resource module",
                "type": "resources",
                "uuid": str(uuid.uuid4()),
                "version": version,
            })

        return base

    def _patch_manifest(self, manifest: dict) -> dict:
        """Ensure required fields exist in an existing manifest."""
        header = manifest.setdefault("header", {})
        if not header.get("uuid"):
            header["uuid"] = str(uuid.uuid4())
        if not header.get("version"):
            header["version"] = _random_version()
        if not header.get("min_engine_version"):
            header["min_engine_version"] = [1, 20, 0]
        if not header.get("name"):
            header["name"] = _random_name()
        manifest.setdefault("format_version", 2)
        return manifest

    # ─────────────────────────────────────────────
    #  Step 4 – Package into .mcaddon / .mcpack
    # ─────────────────────────────────────────────

    def _package(self, pack_root: str, pack_name: str, output_format: str) -> str:
        # Sanitise name for filename
        safe_name = "".join(
            c if c.isalnum() or c in " _-" else "_" for c in pack_name
        ).strip().replace(" ", "_")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.{output_format}"

        # Save to Downloads (or app dir on desktop)
        output_dir = self._get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        # Write ZIP with .mcaddon / .mcpack extension
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for dirpath, _, filenames in os.walk(pack_root):
                for fname in filenames:
                    full = os.path.join(dirpath, fname)
                    arcname = os.path.relpath(full, pack_root)
                    zf.write(full, arcname)

        size_kb = os.path.getsize(output_path) // 1024
        self._log(f"   Archive size: {size_kb} KB", "zip-box", (0.6, 0.9, 0.6, 1))
        return output_path

    def _get_output_dir(self) -> str:
        from kivy.utils import platform
        if platform == "android":
            try:
                from android.storage import primary_external_storage_path
                return os.path.join(primary_external_storage_path(), "Download", "MCModConverter")
            except Exception:
                from kivy.app import App
                return App.get_running_app().user_data_dir
        else:
            return os.path.join(os.path.expanduser("~"), "Downloads", "MCModConverter")
