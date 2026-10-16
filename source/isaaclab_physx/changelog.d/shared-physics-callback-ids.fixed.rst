* Allocated legacy Isaac event callback IDs from the shared physics-manager counter,
  preventing stale PhysX handles from deregistering callbacks after a backend change.
