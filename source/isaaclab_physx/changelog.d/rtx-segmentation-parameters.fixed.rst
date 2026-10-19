* Fixed Isaac RTX semantic and instance segmentation filters on Isaac Sim 6.2 by passing the
  predicate explicitly to Replicator annotators.
* Preserved raw semantic IDs when colorization was disabled by omitting color mappings, and
  avoided passing empty mappings that forced Replicator into colorized output.
