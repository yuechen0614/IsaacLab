* Explicitly cancelled EventDispatcher ``ObserverGuard`` subscriptions when
  deregistering PhysX callbacks, preventing retained observers from invoking
  callbacks from a closed simulation context in a later simulation context.
