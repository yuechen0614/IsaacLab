* Added public OvPhysxManager readiness and opaque binding-generation queries.
  STOP invalidates consumer bindings; a non-soft reset restores them with a new
  generation even when the native runtime is reused. Failed STOP cleanup must
  succeed before reset publishes a new ready event.
