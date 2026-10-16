Fixed
^^^^^

* Preserved the input expression when source-instance asset lookup selected one prim,
  allowing uniquely matched assets to have different names across environments and
  keeping concrete-path queries limited to the requested instance. Multiple-match
  queries kept their existing destination expressions with concrete suffixes.
* Fell back to actual stage matches for assets authored after cloning when the
  clone-plan source contained no matching prim. Missing assets still raised errors.
* Used one process-wide physics callback ID allocator across backend classes, so
  delayed destruction from an earlier backend could not remove a later callback.
