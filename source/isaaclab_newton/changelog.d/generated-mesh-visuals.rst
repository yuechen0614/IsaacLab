Fixed
^^^^^

* Preserved visible source mesh topology and material bindings after Newton
  collision approximation. Standalone meshes remained visible to Newton Warp
  while their collision hulls stayed hidden; invisible, guide-purpose and
  dedicated collision geometry retained their existing visibility policy.
