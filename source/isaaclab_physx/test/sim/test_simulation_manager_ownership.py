# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Verify PhysX lifecycle ownership when its package is imported before Kit starts."""

import sys

from isaaclab_physx.physics import PhysxCfg

from isaaclab.test.utils import launch_test_simulation

# Launch Kit only after importing the PhysX config to reproduce normal entry-point config resolution.
launch_test_simulation()

import pytest
from isaaclab_physx.physics import PhysxManager

import carb

from isaaclab.sim.utils import enable_extension

enable_extension("isaacsim.core.simulation_manager")
import isaacsim.core.simulation_manager as simulation_manager_module

import isaaclab.sim as sim_utils
from isaaclab.physics import PhysicsManager
from isaaclab.sim import SimulationCfg, SimulationContext
from isaaclab.test.utils import resolve_test_sim_device

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def setup_teardown():
    """Create a fresh stage and simulation context for each test."""
    SimulationContext.clear_instance()
    sim_utils.create_new_stage()
    yield
    SimulationContext.clear_instance()


@pytest.mark.isaacsim_ci
def test_initialize_claims_simulation_manager_lifecycle():
    """PhysxManager disables conflicting callbacks without patching supported Isaac Sim versions."""
    original_manager = simulation_manager_module.SimulationManager
    assert original_manager is not PhysxManager
    implementation_module = sys.modules["isaacsim.core.simulation_manager.impl.simulation_manager"]
    supports_startup_setting = hasattr(implementation_module, "_SETTING_ENABLE_DEFAULT_CALLBACKS")

    SimulationContext(cfg=SimulationCfg(physics=PhysxCfg()))

    setting = "/exts/isaacsim.core.simulation_manager/enable_default_callbacks"
    assert not carb.settings.get_settings().get_as_bool(setting)
    assert not any(original_manager.get_default_callback_status().values())
    if supports_startup_setting:
        assert simulation_manager_module.SimulationManager is original_manager
    else:
        assert simulation_manager_module.SimulationManager is PhysxManager


@pytest.mark.isaacsim_ci
def test_clock_tracks_completed_steps_and_compatibility_reads():
    """Physics, rather than rendering or wall time, advances the common clock [s]."""
    import omni.physx

    sim = SimulationContext(cfg=SimulationCfg(physics=PhysxCfg(), device=resolve_test_sim_device(), dt=0.004))
    sim.reset()
    durations = []
    subscription = omni.physx.get_physx_interface().subscribe_physics_step_events(durations.append)
    assert PhysicsManager.get_simulation_time() == 0.0
    for count in range(1, 6):
        sim.step(render=False)
        expected = count * sim.cfg.dt
        assert PhysxManager.get_simulation_time() == pytest.approx(expected)
        assert PhysicsManager.get_simulation_time() == pytest.approx(expected)
        assert PhysxManager._simulation_manager_interface.get_simulation_time() == pytest.approx(expected)
    assert len(durations) == 5
    assert sum(durations) == pytest.approx(PhysicsManager.get_simulation_time())
    for _ in range(3):
        sim.forward()
        sim.render()
    assert PhysicsManager.get_simulation_time() == pytest.approx(expected)
    assert len(durations) == 5
    del subscription


@pytest.mark.isaacsim_ci
def test_clock_survives_reset_and_restarts_with_new_context():
    """Reset refreshes a live context; closing/recreating it begins a new clock."""
    cfg = SimulationCfg(physics=PhysxCfg(), device=resolve_test_sim_device(), dt=0.004)
    sim = SimulationContext(cfg=cfg)
    sim.reset()
    sim.step(render=False)
    assert PhysicsManager.get_simulation_time() == pytest.approx(cfg.dt)
    for soft in (True, False):
        sim.reset(soft=soft)
        assert PhysicsManager.get_simulation_time() == pytest.approx(cfg.dt)
    SimulationContext.clear_instance()
    assert PhysicsManager.get_simulation_time() == 0.0
    sim_utils.create_new_stage()
    sim = SimulationContext(cfg=cfg)
    assert PhysicsManager.get_simulation_time() == 0.0
    sim.reset()
    sim.step(render=False)
    assert PhysicsManager.get_simulation_time() == pytest.approx(cfg.dt)
