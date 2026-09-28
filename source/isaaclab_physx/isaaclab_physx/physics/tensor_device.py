# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Warp tensor views for different Lab compute and native PhysX devices.

Only mixed-device simulations use these views. Native physics parameters stay on
PhysX's parameter device (usually CPU); state/force writes use its simulation
device. Public reads are stable Warp buffers on the requested compute device.
"""

from __future__ import annotations

from functools import wraps
from typing import Any

import warp as wp

_STATE_WRITES = frozenset(
    {
        "set_root_transforms",
        "set_root_velocities",
        "set_dof_positions",
        "set_dof_velocities",
        "set_dof_actuation_forces",
        "set_dof_position_targets",
        "set_dof_velocity_targets",
        "set_transforms",
        "set_velocities",
        "set_kinematic_targets",
        "wake_up",
        "apply_forces",
        "apply_forces_and_torques_at_position",
        "set_simulation_nodal_positions",
        "set_simulation_nodal_velocities",
        "set_simulation_nodal_kinematic_targets",
    }
)
_PARAMETER_WRITES = frozenset(
    {
        "set_dof_limits",
        "set_dof_stiffnesses",
        "set_dof_dampings",
        "set_dof_max_forces",
        "set_dof_drive_model_properties",
        "set_dof_friction_coefficients",
        "set_dof_friction_properties",
        "set_dof_max_velocities",
        "set_dof_armatures",
        "set_masses",
        "set_coms",
        "set_inertias",
        "set_disable_gravities",
        "set_disable_simulations",
        "set_material_properties",
        "set_compliant_material_properties",
        "set_contact_offsets",
        "set_rest_offsets",
        "set_fixed_tendon_properties",
        "set_spatial_tendon_properties",
        "set_dynamic_friction",
        "set_youngs_modulus",
        "set_poissons_ratio",
    }
)


class _ArrayTransfers:
    """Own stable copy buffers for one view, not global or articulation caches."""

    def __init__(self):
        self.buffers: dict[Any, wp.array] = {}

    def convert(self, value: Any, device: str, key: Any) -> Any:
        if isinstance(value, wp.array):
            if str(value.device) == device:
                return value
            buffer = self.buffers.get(key)
            if (
                buffer is None
                or buffer.shape != value.shape
                or buffer.dtype != value.dtype
                or str(buffer.device) != device
            ):
                buffer = wp.empty_like(value, device=device)
                self.buffers[key] = buffer
            # Native PhysX and Warp may use different streams. Synchronize only
            # at an actual device boundary so copies and native calls see writes.
            if value.device.is_cuda:
                wp.synchronize_device(value.device)
            wp.copy(buffer, value)
            if buffer.device.is_cuda:
                wp.synchronize_device(buffer.device)
            elif value.device.is_cuda:
                wp.synchronize_device(value.device)
            return buffer
        if isinstance(value, tuple):
            return tuple(self.convert(item, device, (key, i)) for i, item in enumerate(value))
        if isinstance(value, list):
            return [self.convert(item, device, (key, i)) for i, item in enumerate(value)]
        if isinstance(value, dict):
            return {name: self.convert(item, device, (key, name)) for name, item in value.items()}
        return value


class DeviceTensorView:
    """Present one native object view on a separate compute device."""

    def __init__(self, native_view: Any, device: str, native_device: str, parameter_device: str):
        self.native_view = native_view
        self.device = device
        self._native_device = native_device
        self._parameter_device = parameter_device
        self._transfers = _ArrayTransfers()
        self._methods: dict[str, Any] = {}
        self._closed = False

    def close(self) -> None:
        """Release staging arrays before another stage creates new views."""
        self._closed = True
        self._transfers.buffers.clear()
        self._methods.clear()

    def __getattr__(self, name: str) -> Any:
        if self._closed:
            raise RuntimeError("PhysX tensor view belongs to a closed simulation.")
        native = getattr(self.native_view, name)
        if not callable(native):
            return native
        if name in self._methods:
            return self._methods[name]
        is_read = name.startswith("get_")
        if name in _STATE_WRITES:
            target = self._native_device
        elif name in _PARAMETER_WRITES:
            target = self._parameter_device
        elif is_read:
            target = self._native_device
        elif name.startswith(("set_", "apply_")):
            raise NotImplementedError(f"Mixed-device tensor transfer is not defined for {name}.")
        else:
            return native

        @wraps(native)
        def call(*args, **kwargs):
            if self._closed:
                raise RuntimeError("PhysX tensor view belongs to a closed simulation.")
            args = self._transfers.convert(args, target, (name, "args"))
            kwargs = self._transfers.convert(kwargs, target, (name, "kwargs"))
            result = native(*args, **kwargs)
            if is_read:
                return self._transfers.convert(result, self.device, (name, "result"))
            return result

        self._methods[name] = call
        return call


class DeviceSimulationView:
    """Create mixed-device object views while keeping one native simulation owner."""

    def __init__(self, native_view: Any, device: str):
        self.native_view = native_view
        self.device = str(wp.get_device(device))
        self._views: list[DeviceTensorView] = []

    def invalidate(self) -> None:
        """Invalidate the native simulation and discard all transfer buffers."""
        for view in self._views:
            view.close()
        self._views.clear()
        self.native_view.invalidate()

    def __getattr__(self, name: str) -> Any:
        native = getattr(self.native_view, name)
        if name.startswith("create_") and name.endswith("_view") and callable(native):

            @wraps(native)
            def create(*args, **kwargs):
                param = self.native_view.param_device_ordinal
                view = DeviceTensorView(
                    native(*args, **kwargs),
                    self.device,
                    str(self.native_view.device),
                    "cpu" if param < 0 else f"cuda:{param}",
                )
                self._views.append(view)
                return view

            return create
        return native
