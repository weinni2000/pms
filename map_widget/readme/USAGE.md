## Use the `MapWidget` component

```javascript
import {MapWidget} from "@map_widget/components/map_widget/map_widget.esm";

export class MyMap extends Component {
    static components = {MapWidget};

    get zones() {
        return [
            {
                id: "zone-1",
                zone_id: 1,
                name: "Zone A",
                code: "A",
                symbol: "fa-home",
                points: "10,10 110,10 110,60 10,60",
                state: "free",
                colors: {fill: "#198754", stroke: "#146c43", hover: "#22a06b"},
                items: [{id: 11, name: "Pitch A1", selectable: true}],
            },
        ];
    }
}
```

```xml
<MapWidget zones="zones" mapImageUrl="'/web/image/my.model/1/image'"/>
```

### Props

| Prop | Type | Description |
| --- | --- | --- |
| `zones` | Array | Zones to draw (see below). |
| `mapImageUrl` | String | URL of the image the zones are drawn on. |
| `editable` | Boolean | Turns the map into a zone editor. |
| `draftPoints` | String | Polyline of the polygon currently being drawn. |
| `onMapClick` | Function | `({x, y})` of a click, in image pixels (editor only). |
| `onRemoveZone` | Function | `(zone)` when the editor's remove button is clicked. |
| `onCloseDraft` | Function | Called when the draft polygon's first point is clicked. |
| `onCornersChanged` | Function | `(zoneId, points)` when the editor moved a corner. |
| `selectedItemIds` | Array | Ids of the items picked from the map. |
| `onSelectItem` | Function | `(items)` with the items picked so far. |
| `legend` | Array | `[{label, color}]` entries of the color legend. |
| `legendPosition` | String | `top_left`, `top_right`, `bottom_left`, `bottom_right` or `none`. |
| `labelScale` | Number | Zoom factor of the zone codes drawn on the map. |

### Zone object

| Key | Description |
| --- | --- |
| `id` | Unique key of the zone on the map. |
| `zone_id` | Record id, reported back by the callbacks. |
| `name` | Shown in the tooltip and as the item panel's title. |
| `code` | Short text drawn inside the zone (nothing is drawn when empty). |
| `symbol` | Font Awesome class drawn above the code (e.g. `fa-home`). |
| `points` | Polygon outline: `"x1,y1 x2,y2 x3,y3"` in the image's pixel space. |
| `state` | Availability state code, added as an `o_map_widget_zone_state_<state>` class. |
| `colors` | `{fill, stroke, hover}` CSS colors, fed to the zone's custom properties. |
| `color_class` | Extra CSS classes used to color the zone (e.g. a Gantt palette class). |
| `items` | Items of the zone: `{id, name, selectable, url, state_label}`. |

## Use the public interaction

Any QWeb template can mount the map without JavaScript:

```xml
<div class="o_map_widget"
     t-att-data-map-image="map_image_url"
     t-attf-data-zones="{{ zones_json }}"
     t-attf-data-legend="{{ legend_json }}"
     data-legend-position="bottom_left"
     data-selectable="true"
     data-input-id="picked_items"
     data-button-selector=".o_continue">
    <div class="o_map_widget_mount"/>
</div>
```

| Attribute | Description |
| --- | --- |
| `data-map-image` | URL of the image. |
| `data-zones` | JSON array of zone objects. |
| `data-legend` | JSON array of `{label, color}` entries. |
| `data-legend-position` | Legend position (`none` hides it). |
| `data-selected-items` | Comma-separated ids of the already picked items. |
| `data-selectable` | `true` to let visitors pick items on the map. |
| `data-input-id` | Id of the hidden input receiving the picked ids. |
| `data-button-selector` | CSS selector of the buttons disabled while nothing is picked. |
