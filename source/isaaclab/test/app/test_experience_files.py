# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the shipped experience files. These inspect the files and do not launch the simulator."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ``.kit`` files repeat section headers, so they cannot be parsed as TOML.
_SECTION_RE = re.compile(r"^\s*\[+(?P<name>[^\[\]]+)\]+\s*$")
_DEPENDENCY_RE = re.compile(r'^\s*"(?P<name>[^"]+)"\s*=')


def _kit_dependencies(apps_dir: Path, experience: str) -> set[str]:
    """Collect the extension names declared in an experience file's dependency sections."""
    dependencies: set[str] = set()
    in_dependencies = False

    for line in (apps_dir / experience).read_text(encoding="utf-8").splitlines():
        section = _SECTION_RE.match(line)
        if section is not None:
            in_dependencies = section.group("name").strip() == "dependencies"
            continue
        if in_dependencies:
            dependency = _DEPENDENCY_RE.match(line)
            if dependency is not None:
                dependencies.add(dependency.group("name"))

    return dependencies


@pytest.mark.parametrize("experience", ["isaaclab.python.kit", "isaaclab.python.headless.kit"])
def test_base_experiences_enable_native_storage(source_checkout_root: Path, experience: str):
    """Test the base experiences load the extension that applies ``ISAACSIM_ASSET_ROOT``."""
    assert "isaacsim.storage.native" in _kit_dependencies(source_checkout_root / "apps", experience)


@pytest.mark.parametrize(
    "experience, base",
    [
        ("isaaclab.python.rendering.kit", "isaaclab.python"),
        ("isaaclab.python.xr.openxr.kit", "isaaclab.python"),
        ("isaaclab.python.headless.rendering.kit", "isaaclab.python.headless"),
        ("isaaclab.python.xr.openxr.headless.kit", "isaaclab.python.xr.openxr"),
    ],
)
def test_derived_experiences_inherit_native_storage(source_checkout_root: Path, experience: str, base: str):
    """Test the derived experiences inherit native storage from a base experience."""
    assert base in _kit_dependencies(source_checkout_root / "apps", experience)


@pytest.mark.parametrize(
    "experience",
    [
        "isaaclab.python.kit",
        "isaaclab.python.headless.kit",
        "isaaclab.python.rendering.kit",
        "isaaclab.python.headless.rendering.kit",
        "isaaclab.python.xr.openxr.kit",
        "isaaclab.python.xr.openxr.headless.kit",
    ],
)
def test_experiences_do_not_scan_python_packages_as_kit_extensions(source_checkout_root: Path, experience: str):
    """Python packages lack Kit manifests and must not enter extension discovery."""
    apps_dir = source_checkout_root / "apps"
    source_dir = (source_checkout_root / "source").resolve()
    in_extension_paths = False
    for line in (apps_dir / experience).read_text(encoding="utf-8").splitlines():
        section = _SECTION_RE.match(line)
        if section is not None:
            in_extension_paths = section.group("name").strip() == "settings.app.exts"
            continue
        if not in_extension_paths:
            continue
        path_entry = re.match(r'^\s*"(?P<path>[^"]+)"\s*,?', line)
        if path_entry is None:
            continue
        folder = path_entry.group("path").replace("${app}", str(apps_dir))
        if "${" in folder:
            continue  # Isaac Sim/Kit paths resolve against the installed runtime.
        resolved = Path(folder).resolve()
        assert not resolved.is_relative_to(source_dir), (
            f"{experience} scans Python packages as Kit extensions: {folder}"
        )
