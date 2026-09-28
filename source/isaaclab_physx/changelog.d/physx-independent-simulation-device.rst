Added
^^^^^

* Added ``PhysxCfg.simulation_device`` to select the native PhysX CPU/CUDA device
  independently of ``SimulationCfg.device`` (Lab compute). The default ``None``
  continued to follow the compute device. Mixed-device views copied Warp reads
  into reusable compute-device buffers and routed state/parameter writes to
  their native devices. Native simulation startup and teardown used the solver
  device, and closing the simulation released the transfer buffers. Matching
  devices kept the original native views without additional copies.

Fixed
^^^^^

* Refreshed CPU PhysX Fabric output before rendering so tensor pose writes
  appeared in the next frame. This used a Fabric stage rebind on PhysX 110.3
  and added render-time overhead; GPU PhysX retained its direct Fabric update.
  Non-Fabric rendering explicitly published transforms to USD. Neither path
  advanced the physics clock.
