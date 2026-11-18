// Copyright 2026 mytime.click
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {Component, onWillUpdateProps, useState} from "@odoo/owl";
import {MapWidget} from "@map_widget/components/map_widget/map_widget.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

/**
 * Map editor: draws the polygon of a zone, and edits or removes the outline of
 * the existing ones, straight on the map image.
 *
 * Points are persisted in the image's own pixel space, so the outlines keep
 * matching the picture at any rendered size.
 */
export class MapBookingMapPreviewField extends Component {
    static template = "map_booking.MapBookingMapPreviewField";
    static components = {MapWidget};
    static props = {...standardFieldProps};

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            zones: [...(this.previewData.zones || [])],
            shapes: [...(this.previewData.shapes || [])],
            selectedZoneId: null,
            draftPoints: [],
            drawing: false,
        });
        onWillUpdateProps((nextProps) => {
            const data = nextProps.record.data[nextProps.name] || {};
            this.state.zones = [...(data.zones || [])];
            this.state.shapes = [...(data.shapes || [])];
        });
    }

    get previewData() {
        return this.props.record.data[this.props.name] || {};
    }

    get mapImageUrl() {
        return this.previewData.image_url || "";
    }

    get legend() {
        return this.previewData.legend || [];
    }

    get legendPosition() {
        return this.previewData.legend_position || "none";
    }

    get draftPoints() {
        return this.state.draftPoints.map(({x, y}) => `${x},${y}`).join(" ");
    }

    get selectedZoneName() {
        const zone = this.state.zones.find(({id}) => id === this.state.selectedZoneId);
        return zone ? zone.name : "";
    }

    get selectedShape() {
        const zoneId = this.state.selectedZoneId;
        return (
            (zoneId &&
                this.state.shapes.find(
                    ({zone_id: shapeZoneId, points}) => shapeZoneId === zoneId && points
                )) ||
            null
        );
    }

    get canStartNewPolygon() {
        return Boolean(this.state.selectedZoneId && !this.selectedShape);
    }

    get canClear() {
        // While drawing it drops the new points; otherwise it removes the
        // outline of the picked zone so it can be drawn again.
        return this.state.drawing || Boolean(this.selectedShape);
    }

    get labelScale() {
        return this.props.record.data.label_scale || 1;
    }

    onLabelScaleChange(ev) {
        // Persist on the record so the size survives a save and is shared with
        // the availability tab; the form's dirty/save flow handles storing it.
        this.props.record.update({label_scale: Number(ev.target.value) || 1});
    }

    onZoneChange(ev) {
        this.selectZone(Number(ev.target.value) || null);
    }

    selectZone(zoneId) {
        // Picked in the dropdown or by clicking its outline on the map.
        this.state.selectedZoneId = zoneId;
        this.state.draftPoints = [];
        this.state.drawing = false;
    }

    startNewPolygon() {
        // A polygon can only be drawn for a chosen zone without one.
        if (!this.canStartNewPolygon) {
            return;
        }
        this.state.drawing = true;
        this.state.draftPoints.splice(0);
    }

    addPoint(point) {
        if (this.state.drawing && this.state.selectedZoneId) {
            this.state.draftPoints.push(point);
        }
    }

    clearPoints() {
        this.state.draftPoints.splice(0);
    }

    async onClearClick() {
        if (this.state.drawing) {
            // Drop the points drawn so far and leave drawing mode; "New
            // polygon" starts over.
            this.clearPoints();
            this.state.drawing = false;
        } else if (this.selectedShape) {
            await this.removeZone(this.selectedShape);
        }
    }

    async saveZone() {
        const mapId = this.props.record.resId;
        if (!mapId) {
            this.notification.add(_t("Save the map before outlining a zone."), {
                type: "warning",
            });
            return;
        }
        if (!this.state.selectedZoneId || this.state.draftPoints.length < 3) {
            this.notification.add(_t("Select a zone and mark at least three points."), {
                type: "warning",
            });
            return;
        }
        const zone = this.state.zones.find(({id}) => id === this.state.selectedZoneId);
        if (!zone) {
            // The zone list can be refreshed from the record while a zone is
            // still selected; saving would then store points for a zone the
            // button no longer knows how to draw.
            this.notification.add(_t("The selected zone is no longer available."), {
                type: "warning",
            });
            return;
        }
        const points = this.draftPoints;
        await this.orm.write("map.booking.zone", [this.state.selectedZoneId], {
            map_id: mapId,
            points,
        });
        this.state.shapes = this.state.shapes.filter(
            ({zone_id: zoneId}) => zoneId !== zone.id
        );
        this.state.shapes.push({
            id: `zone-${zone.id}`,
            zone_id: zone.id,
            name: zone.name,
            code: zone.code,
            symbol: zone.symbol,
            points,
            items: [],
            state: false,
        });
        this.clearPoints();
        this.state.drawing = false;
        this.notification.add(_t("The zone was saved."), {type: "success"});
    }

    async onCornersChanged(zoneId, points) {
        if (!zoneId || !points) {
            return;
        }
        await this.orm.write("map.booking.zone", [zoneId], {points});
        const shape = this.state.shapes.find(({zone_id: id}) => id === zoneId);
        if (shape) {
            shape.points = points;
        }
        this.notification.add(_t("The zone outline was updated."), {
            type: "success",
        });
    }

    async removeZone(zone) {
        await this.orm.write("map.booking.zone", [zone.zone_id], {points: false});
        this.state.shapes = this.state.shapes.filter(
            ({zone_id: zoneId}) => zoneId !== zone.zone_id
        );
        if (this.state.selectedZoneId === zone.zone_id) {
            this.clearPoints();
        }
        this.notification.add(_t("The zone outline was removed."), {
            type: "success",
        });
    }
}

registry.category("fields").add("map_booking_map_preview", {
    component: MapBookingMapPreviewField,
    supportedTypes: ["json"],
});
