// Copyright 2026 mytime.click
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {Component} from "@odoo/owl";
import {MapWidget} from "@map_widget/components/map_widget/map_widget.esm";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

/**
 * Read-only map of the availability of a whole map at a tested stay period.
 *
 * Reads the computed JSON straight from the record (reactive) rather than
 * caching it, so the map recolors when the tested stay recomputes.
 */
export class MapBookingZoneMapField extends Component {
    static template = "map_booking.MapBookingZoneMapField";
    static components = {MapWidget};
    static props = {...standardFieldProps};

    get previewData() {
        return this.props.record.data[this.props.name] || {};
    }

    get shapes() {
        return this.previewData.shapes || [];
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

    get labelScale() {
        return this.props.record.data.label_scale || 1;
    }
}

registry.category("fields").add("map_booking_zone_map", {
    component: MapBookingZoneMapField,
    supportedTypes: ["json"],
});
