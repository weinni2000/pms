// Copyright 2026 mytime.click
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {Component} from "@odoo/owl";
import {MapWidget} from "@map_widget/components/map_widget/map_widget.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {x2ManyCommands} from "@web/core/orm_service";

const ROOMS_FIELD = "map_booking_room_ids_calculated";

/**
 * Map of a hotel reservation: the zones are colored for the stay, and clicking
 * a free zone adds its room to the reservation lines (removing the chip of a
 * picked room takes it off again).
 *
 * The map only writes the picked rooms; the server onchange of that field
 * fills in the reservation lines.
 */
export class MapBookingHotelReservationMapField extends Component {
    static template = "map_booking_hotel_reservation.MapField";
    static components = {MapWidget};
    static props = {...standardFieldProps};

    setup() {
        // The map keeps its own copy of the picked rooms: remount it when
        // they change elsewhere (e.g. a line deleted in the list below).
        this.mapKey = 0;
        this.reportedIds = this.roomIds;
    }

    get mapData() {
        return this.props.record.data[this.props.name] || {};
    }

    get roomIds() {
        const rooms = this.props.record.data[ROOMS_FIELD];
        return rooms ? [...rooms.currentIds] : [];
    }

    get mapState() {
        const roomIds = this.roomIds;
        if (roomIds.join(",") !== this.reportedIds.join(",")) {
            this.reportedIds = roomIds;
            this.mapKey++;
        }
        return {key: `map-${this.mapKey}`, roomIds: this.reportedIds};
    }

    /**
     * Rooms picked so far (on the map or in the lines) against the guests of
     * the reservation, shown under the map.
     */
    get capacitySummary() {
        const data = this.props.record.data;
        const guests = (data.adults || 0) + (data.children || 0);
        const capacity = data.map_booking_capacity_calculated || 0;
        return {
            rooms: _t("Selected rooms: %(count)s", {
                count: data.map_booking_room_count_calculated || 0,
            }),
            guests: _t("Guests: %(capacity)s / %(guests)s", {capacity, guests}),
            enough: capacity >= guests,
        };
    }

    get isReadonly() {
        return Boolean(this.props.readonly);
    }

    async onSelectRooms(items) {
        const roomIds = items.map(({id}) => id);
        this.reportedIds = roomIds;
        await this.props.record.update({
            [ROOMS_FIELD]: [x2ManyCommands.set(roomIds)],
        });
    }
}

registry.category("fields").add("map_booking_hotel_reservation_map", {
    component: MapBookingHotelReservationMapField,
    supportedTypes: ["json"],
});
