Reusable OWL widget that turns any image into an interactive map. It draws
clickable zones (polygons in the image's own pixel space) on top of a picture,
colors them from a per-zone color map, and can edit them in place.

The widget ships in two flavors:

- the ``MapWidget`` OWL component, for backend views and other components;
- the ``.o_map_widget`` public interaction, which mounts the same component
  from plain data attributes on any website or portal template.

It carries no data model: it is the rendering half of an interactive map, and
feature modules such as ``map_booking`` add the records, colors and
availability logic on top of it.
