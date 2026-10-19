* Fixed retained rigid-object and articulation tensor views across STOP/reset
  by closing each asset-owned view before replacing it. Failed cleanup preserves
  the view for a later retry.
