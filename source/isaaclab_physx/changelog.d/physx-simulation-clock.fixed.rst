* Fixed PhysX simulation time remaining at zero after explicit physics steps and the legacy
  simulation-manager compatibility getter calling an unavailable native method. The common
  clock now advances after each completed step and supplies the current time to PhysX.
  Rendering and resets within a live context preserve the clock; closing and creating a new
  simulation context restarts it at zero.
