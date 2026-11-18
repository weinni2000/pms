// Copyright 2026 mytime.click
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import {
    Component,
    onMounted,
    onWillUnmount,
    onWillUpdateProps,
    useRef,
    useState,
} from "@odoo/owl";

/**
 * Interactive map: renders an image and draws its clickable zones on top of it.
 *
 * A zone is a polygon whose points live in the image's own pixel space
 * (`"x1,y1 x2,y2 x3,y3 ..."`), so the overlay keeps matching the picture at any
 * rendered size. The component supports three modes:
 *
 * - read-only: hovering shows the zone name, clicking opens its items panel;
 * - selection: clicking picks the zone's items one by one, then unpicks
 *   them, reporting them in `onSelectItem`;
 * - editing: draws new polygons and lets the user drag, add or remove corners.
 *
 * Consumers convert Odoo records into the plain objects documented in
 * `readme/USAGE.md` and push the result back from the callbacks.
 */
export class MapWidget extends Component {
    static template = "map_widget.MapWidget";
    static props = {
        zones: Array,
        mapImageUrl: String,
        editable: {type: Boolean, optional: true},
        draftPoints: {type: String, optional: true},
        onMapClick: {type: Function, optional: true},
        onRemoveZone: {type: Function, optional: true},
        onCloseDraft: {type: Function, optional: true},
        onCornersChanged: {type: Function, optional: true},
        // Editor: the zone picked outside the map, highlighted and editable.
        activeZoneId: {optional: true},
        onActiveZoneChange: {type: Function, optional: true},
        selectedItemIds: {type: Array, optional: true},
        onSelectItem: {type: Function, optional: true},
        legend: {type: Array, optional: true},
        legendPosition: {type: String, optional: true},
        labelScale: {type: Number, optional: true},
    };

    setup() {
        this.mapImageRef = useRef("mapImage");
        this.mapSvgRef = useRef("mapSvg");
        this.updateMapWidth = () => {
            const image = this.mapImageRef.el;
            if (!image) {
                return;
            }
            // Drives the legend size so it stays proportional to the map.
            const nextWidth = Math.round(image.getBoundingClientRect().width);
            if (nextWidth !== this.state.mapWidth) {
                this.state.mapWidth = nextWidth;
            }
        };
        this.state = useState({
            naturalWidth: 0,
            naturalHeight: 0,
            mapWidth: 0,
            hoveredZoneId: null,
            selectedZoneId: null,
            // Multiple items can be selected at once (one per free resource).
            selectedItemIds: this.props.selectedItemIds
                ? [...this.props.selectedItemIds]
                : [],
            // Corner-editing an existing zone (editor only).
            editZoneId: null,
            editPoints: [],
            draggingCorner: null,
            // Moving a whole outline (editor only).
            draggingZoneId: null,
        });
        onWillUpdateProps((nextProps) => {
            const zoneId = nextProps.activeZoneId;
            const outline = (zones) =>
                (zones.find(({zone_id}) => zone_id && zone_id === zoneId) || {}).points;
            // Follow a new pick, and a new outline drawn for the picked zone.
            if (
                zoneId !== this.props.activeZoneId ||
                outline(nextProps.zones) !== outline(this.props.zones)
            ) {
                this.activateZone(zoneId, nextProps.zones);
            }
        });
        onMounted(() => {
            this.activateZone(this.props.activeZoneId, this.props.zones);
            this.updateMapWidth();
            window.addEventListener("resize", this.updateMapWidth);
        });
        onWillUnmount(() => window.removeEventListener("resize", this.updateMapWidth));
    }

    get isDrafting() {
        return Boolean(this.props.draftPoints);
    }

    get draftPointList() {
        return this.props.draftPoints
            ? this.props.draftPoints
                  .split(/\s+/)
                  .filter(Boolean)
                  .map((point) => point.split(",").map(Number))
            : [];
    }

    get draftStartPoint() {
        // The first point of the polygon being drawn — shown as a marker the
        // user can click to close and save the zone.
        return this.draftPointList[0];
    }

    onCloseDraftClick() {
        if (this.props.onCloseDraft) {
            this.props.onCloseDraft();
        }
    }

    get showLegend() {
        return Boolean(
            this.props.legend &&
                this.props.legend.length &&
                this.props.legendPosition &&
                this.props.legendPosition !== "none"
        );
    }

    get legendClass() {
        return `o_map_widget_legend o_map_widget_legend_${this.props.legendPosition}`;
    }

    get legendStyle() {
        // Scale the legend font with the rendered map width (everything else in
        // the legend is sized in em), so it stays proportional and never
        // dominates a small map. Clamped to keep it readable.
        const width = this.state.mapWidth;
        if (!width) {
            return undefined;
        }
        const fontPx = Math.max(9, Math.min(14, width * 0.03));
        return `font-size: ${fontPx}px`;
    }

    onImageLoad(ev) {
        this.state.naturalWidth = ev.target.naturalWidth;
        this.state.naturalHeight = ev.target.naturalHeight;
        this.updateMapWidth();
    }

    get hoveredZone() {
        return this.props.zones.find((zone) => zone.id === this.state.hoveredZoneId);
    }

    get selectedZone() {
        return this.props.zones.find(
            (zone) => zone.zone_id === this.state.selectedZoneId
        );
    }

    onZoneHover(zoneId) {
        this.state.hoveredZoneId = zoneId;
    }

    onZoneClick(zone, ev) {
        if (this.props.editable) {
            if (this.zoneDragged) {
                // The click that ends a move must not reload the old outline.
                this.zoneDragged = false;
                return;
            }
            // In the editor, click an existing zone (with an outline) to edit
            // its corners — unless a new polygon is currently being drawn.
            if (this.props.onCornersChanged && !this.isDrafting && zone.points) {
                if (ev) {
                    ev.stopPropagation();
                }
                this.startCornerEdit(zone);
            }
            return;
        }
        if (this.props.onSelectItem) {
            // Each click books the next still-free item in the zone, so a zone
            // holding several items can be clicked several times; once all of
            // them are picked, the next click unpicks the zone again.
            this.toggleZone(zone);
            return;
        }
        this.state.selectedZoneId = zone.zone_id;
    }

    startCornerEdit(zone) {
        this.state.editZoneId = zone.zone_id;
        this.state.editPoints = this.zonePoints(zone);
        this.state.draggingCorner = null;
        if (this.props.onActiveZoneChange && zone.zone_id !== this.props.activeZoneId) {
            // Clicking an outline on the map picks its zone outside, too.
            this.props.onActiveZoneChange(zone.zone_id);
        }
    }

    activateZone(zoneId, zones) {
        // Open the outline of the zone picked outside the map for editing, or
        // stop editing when that zone has no outline (yet) or none is picked.
        const zone = zoneId && zones.find(({zone_id}) => zone_id === zoneId);
        if (zone && zone.points) {
            this.state.editZoneId = zone.zone_id;
            this.state.editPoints = this.zonePoints(zone);
        } else {
            this.state.editZoneId = null;
            this.state.editPoints = [];
        }
        this.state.draggingCorner = null;
    }

    isActiveZone(zone) {
        return Boolean(zone.zone_id) && zone.zone_id === this.props.activeZoneId;
    }

    isEditingZone(zone) {
        return (
            zone.zone_id === this.state.editZoneId && this.state.editPoints.length > 0
        );
    }

    zonePointsString(zone) {
        if (this.isEditingZone(zone)) {
            return this.state.editPoints.map((point) => point.join(",")).join(" ");
        }
        return zone.points;
    }

    eventToImageCoords(ev) {
        const svg = this.mapSvgRef.el;
        const matrix = svg && svg.getScreenCTM();
        if (!matrix) {
            return null;
        }
        // Map the pointer through the SVG's own transform, so the result is in
        // the picture's pixel space whatever the layout does to the box.
        const point = svg.createSVGPoint();
        point.x = ev.clientX;
        point.y = ev.clientY;
        const {x, y} = point.matrixTransform(matrix.inverse());
        // A corner can never leave the picture: the pointer may be captured
        // outside of it while dragging, so clamp to the image's own size.
        const clamp = (value, max) => Math.min(Math.max(Math.round(value), 0), max);
        return [clamp(x, this.state.naturalWidth), clamp(y, this.state.naturalHeight)];
    }

    saveCorners() {
        if (this.props.onCornersChanged) {
            this.props.onCornersChanged(
                this.state.editZoneId,
                this.state.editPoints.map((point) => point.join(",")).join(" ")
            );
        }
    }

    onCornerPointerDown(index, ev) {
        ev.stopPropagation();
        ev.target.setPointerCapture(ev.pointerId);
        this.state.draggingCorner = index;
        this.cornerDragged = false;
    }

    onCornerPointerMove(index, ev) {
        if (this.state.draggingCorner !== index) {
            return;
        }
        const coords = this.eventToImageCoords(ev);
        if (coords) {
            this.state.editPoints[index] = coords;
            this.cornerDragged = true;
        }
    }

    onCornerPointerUp(index, ev) {
        if (this.state.draggingCorner !== index) {
            return;
        }
        ev.target.releasePointerCapture(ev.pointerId);
        this.state.draggingCorner = null;
        // Only persist when the corner actually moved (ignore plain clicks and
        // the click pair of a double-click that removes a corner).
        if (this.cornerDragged) {
            this.saveCorners();
        }
    }

    canMoveZone(zone) {
        return Boolean(
            this.props.editable &&
                this.props.onCornersChanged &&
                !this.isDrafting &&
                zone.points
        );
    }

    onZonePointerDown(zone, ev) {
        // Only the left mouse button (or a touch/pen contact) moves an outline.
        if (!this.canMoveZone(zone) || ev.button !== 0) {
            return;
        }
        const start = this.eventToImageCoords(ev);
        if (!start) {
            return;
        }
        if (!this.isEditingZone(zone)) {
            this.startCornerEdit(zone);
        }
        ev.target.setPointerCapture(ev.pointerId);
        this.state.draggingZoneId = zone.zone_id;
        this.zoneDragStart = start;
        this.zoneDragPoints = this.state.editPoints.map((point) => [...point]);
        this.zoneDragged = false;
    }

    onZonePointerMove(zone, ev) {
        if (this.state.draggingZoneId !== zone.zone_id) {
            return;
        }
        const coords = this.eventToImageCoords(ev);
        if (!coords) {
            return;
        }
        const [dx, dy] = this.limitMoveOffset(
            this.zoneDragPoints,
            coords[0] - this.zoneDragStart[0],
            coords[1] - this.zoneDragStart[1]
        );
        if (dx || dy) {
            this.zoneDragged = true;
        }
        this.state.editPoints = this.zoneDragPoints.map(([x, y]) => [x + dx, y + dy]);
    }

    /**
     * The [dx, dy] shift to apply to `points`, reduced so the outline as a
     * whole stays inside the picture.
     */
    limitMoveOffset(points, dx, dy) {
        const xs = points.map(([x]) => x);
        const ys = points.map(([, y]) => y);
        const limit = (value, min, max) => Math.min(Math.max(value, min), max);
        return [
            limit(dx, -Math.min(...xs), this.state.naturalWidth - Math.max(...xs)),
            limit(dy, -Math.min(...ys), this.state.naturalHeight - Math.max(...ys)),
        ];
    }

    onZonePointerUp(zone, ev) {
        if (this.state.draggingZoneId !== zone.zone_id) {
            return;
        }
        ev.target.releasePointerCapture(ev.pointerId);
        this.state.draggingZoneId = null;
        if (this.zoneDragged) {
            this.saveCorners();
        }
    }

    removeCorner(index, ev) {
        if (ev) {
            ev.stopPropagation();
        }
        // A polygon needs at least three corners.
        if (this.state.editPoints.length <= 3) {
            return;
        }
        this.state.editPoints.splice(index, 1);
        this.saveCorners();
    }

    insertCorner(index, ev) {
        ev.stopPropagation();
        const coords = this.eventToImageCoords(ev);
        if (!coords) {
            return;
        }
        // Add a corner on the clicked edge, between its two endpoints.
        this.state.editPoints.splice(index + 1, 0, coords);
        this.saveCorners();
    }

    onMapClick(ev) {
        if (!this.props.editable || !this.props.onMapClick) {
            return;
        }
        const coords = this.eventToImageCoords(ev);
        if (coords) {
            this.props.onMapClick({x: coords[0], y: coords[1]});
        }
    }

    zonePoints(zone) {
        return zone.points
            .split(/\s+/)
            .filter(Boolean)
            .map((point) => point.split(",").map(Number));
    }

    zoneLabelPosition(zone) {
        const points = this.zonePoints(zone);
        const total = points.reduce(
            (position, [x, y]) => ({
                x: position.x + x,
                y: position.y + y,
            }),
            {x: 0, y: 0}
        );
        return {x: total.x / points.length, y: total.y / points.length};
    }

    get labelScale() {
        return this.props.labelScale || 1;
    }

    get labelFontPx() {
        // Base font size of the marker code (see SCSS), scaled by the slider.
        return 11 * this.labelScale;
    }

    zoneMarkerBox(zone) {
        // A box centered on the zone centroid so the label stays centered as it
        // grows/shrinks with the slider.
        const center = this.zoneLabelPosition(zone);
        const width = 140 * this.labelScale;
        const height = 44 * this.labelScale;
        return {
            x: center.x - width / 2,
            y: center.y - height / 2,
            width,
            height,
        };
    }

    zoneTopRight(zone) {
        const points = this.zonePoints(zone);
        return {
            x: Math.max(...points.map(([x]) => x)),
            y: Math.min(...points.map(([, y]) => y)),
        };
    }

    onRemoveZoneClick(zone) {
        if (this.props.onRemoveZone) {
            this.props.onRemoveZone(zone);
        }
    }

    get selectedItems() {
        const byId = new Map();
        for (const zone of this.props.zones) {
            for (const item of zone.items || []) {
                byId.set(item.id, item);
            }
        }
        return this.state.selectedItemIds.map((id) => byId.get(id)).filter(Boolean);
    }

    isSelectedItem(item) {
        return this.state.selectedItemIds.includes(item.id);
    }

    selectedCountForZone(zone) {
        return (zone.items || []).filter((item) =>
            this.state.selectedItemIds.includes(item.id)
        ).length;
    }

    hasSelectableItem(zone) {
        return (zone.items || []).some((item) => item.selectable);
    }

    itemClass(item) {
        const classes = ["o_map_widget_item", "btn", "w-100", "text-start"];
        classes.push(
            this.isSelectedItem(item) ? "btn-primary" : "btn-outline-secondary"
        );
        return classes.join(" ");
    }

    onItemClick(item) {
        if (!item.selectable || !this.props.onSelectItem) {
            return;
        }
        if (this.state.selectedItemIds.includes(item.id)) {
            this.removeItem(item.id);
        } else {
            this.state.selectedItemIds.push(item.id);
            this.notifySelection();
        }
    }

    toggleZone(zone) {
        // Each click picks the next still-selectable item of the zone, so
        // clicking a zone holding several items selects them one after another.
        // When nothing is left to pick, the click removes the zone's picked
        // items: clicking a highlighted zone unselects it.
        const items = zone.items || [];
        const next = items.find(
            (item) => item.selectable && !this.state.selectedItemIds.includes(item.id)
        );
        if (next) {
            this.state.selectedItemIds.push(next.id);
            this.notifySelection();
            return;
        }
        const zoneItemIds = new Set(items.map((item) => item.id));
        const kept = this.state.selectedItemIds.filter((id) => !zoneItemIds.has(id));
        if (kept.length !== this.state.selectedItemIds.length) {
            this.state.selectedItemIds = kept;
            this.notifySelection();
        }
    }

    removeItem(itemId) {
        const index = this.state.selectedItemIds.indexOf(itemId);
        if (index !== -1) {
            this.state.selectedItemIds.splice(index, 1);
            this.notifySelection();
        }
    }

    notifySelection() {
        if (this.props.onSelectItem) {
            this.props.onSelectItem(this.selectedItems);
        }
    }

    closePanel() {
        this.state.selectedZoneId = null;
    }

    isSelectedZone(zone) {
        return this.selectedCountForZone(zone) > 0;
    }

    zoneClass(zone) {
        const classes = ["o_map_widget_zone"];
        if (zone.state) {
            classes.push(`o_map_widget_zone_state_${zone.state}`);
        }
        if (zone.color_class) {
            classes.push(zone.color_class);
        }
        if (this.isSelectedZone(zone)) {
            // The chosen zone is highlighted in radiant gold; every other zone
            // keeps its own availability colour (no greying out).
            classes.push("o_map_widget_zone_gold");
        }
        if (zone.id === this.state.hoveredZoneId) {
            classes.push("o_map_widget_zone_hover");
        }
        if (zone.zone_id === this.state.selectedZoneId) {
            classes.push("o_map_widget_zone_selected");
        }
        if (this.isEditingZone(zone)) {
            classes.push("o_map_widget_zone_editing");
        }
        if (this.isActiveZone(zone)) {
            classes.push("o_map_widget_zone_active");
        }
        if (zone.zone_id === this.state.draggingZoneId) {
            classes.push("o_map_widget_zone_moving");
        }
        if (
            this.props.onSelectItem &&
            !this.isSelectedZone(zone) &&
            !this.hasSelectableItem(zone)
        ) {
            classes.push("o_map_widget_zone_disabled");
        }
        return classes.join(" ");
    }

    zoneStyle(zone) {
        // Feed the zone's availability colors into CSS custom properties so the
        // SCSS renders straight from them.
        const colors = zone.colors;
        const vars = [];
        if (colors) {
            if (colors.fill) {
                vars.push(`--o-zone-fill: ${colors.fill}`);
            }
            if (colors.stroke) {
                vars.push(`--o-zone-stroke: ${colors.stroke}`);
            }
            if (colors.hover) {
                vars.push(`--o-zone-hover: ${colors.hover}`);
            }
        }
        return vars.length ? vars.join("; ") : undefined;
    }
}
