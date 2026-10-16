* Refreshed CPU PhysX Fabric output before rendering so tensor pose writes
  appeared in the next frame. This used a Fabric stage rebind on PhysX 110.3
  and added render-time overhead; GPU PhysX retained its direct Fabric update.
  Non-Fabric rendering explicitly published transforms to USD. Neither path
  advanced the physics clock.

* Preserve CPU Fabric pose refreshes through the on-demand scene-data publication path without rebinding clean frames.
