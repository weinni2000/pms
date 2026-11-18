# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models

from odoo.addons.map_booking.models.map_booking_state import STATE_FREE, STATE_OCCUPIED


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    map_booking_map_calculated_id = fields.Many2one(
        "map.booking.map",
        string="Map",
        compute="_compute_map_booking_map_calculated_id",
        store=True,
        readonly=False,
        help="Floor plan the rooms of this reservation are picked on. It "
        "follows the reserved rooms: the map holding most of them is chosen, "
        "and a reservation without rooms starts on the first map with rooms.",
    )
    map_booking_room_ids_calculated = fields.Many2many(
        "hotel.room",
        string="Rooms on the Map",
        compute="_compute_map_booking_room_ids_calculated",
        readonly=False,
        help="Rooms of the reservation lines. Picking a room on the map adds "
        "it to a line of its room type; removing it takes it off that line.",
    )
    map_booking_room_count_calculated = fields.Integer(
        string="Selected Rooms",
        compute="_compute_map_booking_capacity_calculated",
    )
    map_booking_capacity_calculated = fields.Integer(
        string="Selected Capacity",
        compute="_compute_map_booking_capacity_calculated",
        help="Number of guests the selected rooms can hold.",
    )
    map_booking_data_calculated = fields.Json(
        compute="_compute_map_booking_data_calculated"
    )

    @api.depends("reservation_line.reserve")
    def _compute_map_booking_map_calculated_id(self):
        """Keep the map while it holds a reserved room, else switch to the one
        holding most of them; without rooms, start on the first map."""
        rooms_by_map = self._get_map_booking_rooms_by_map()
        first_map_id = next(iter(rooms_by_map), self.env["map.booking.map"])
        for reservation_id in self:
            room_ids = reservation_id.reservation_line.reserve._origin
            map_id = reservation_id.map_booking_map_calculated_id._origin
            counts = {
                candidate_id: len(map_room_ids & room_ids)
                for candidate_id, map_room_ids in rooms_by_map.items()
            }
            if not counts.get(map_id) and any(counts.values()):
                map_id = max(counts, key=counts.get)
            reservation_id.map_booking_map_calculated_id = map_id or first_map_id

    @api.model
    def _get_map_booking_rooms_by_map(self):
        """Hotel rooms held by the zones of each map, maps in their order."""
        rooms_by_map = {}
        zone_ids = self.env["map.booking.zone"].search(
            ["|", ("room_ids", "!=", False), ("room_type_ids", "!=", False)],
            order="map_id, id",
        )
        for zone_id in zone_ids:
            map_id = zone_id.map_id
            rooms_by_map[map_id] = (
                rooms_by_map.get(map_id, self.env["hotel.room"])
                | zone_id._get_zone_rooms()
            )
        return rooms_by_map

    @api.depends("reservation_line.reserve")
    def _compute_map_booking_room_ids_calculated(self):
        for reservation_id in self:
            reservation_id.map_booking_room_ids_calculated = (
                reservation_id.reservation_line.reserve
            )

    @api.depends("map_booking_room_ids_calculated.capacity")
    def _compute_map_booking_capacity_calculated(self):
        for reservation_id in self:
            room_ids = reservation_id.map_booking_room_ids_calculated
            reservation_id.map_booking_room_count_calculated = len(room_ids)
            reservation_id.map_booking_capacity_calculated = sum(
                room_ids.mapped("capacity")
            )

    @api.onchange("map_booking_room_ids_calculated")
    def _onchange_map_booking_room_ids_calculated(self):
        """Keep the reservation lines in step with the rooms picked on the map."""
        room_ids = self.map_booking_room_ids_calculated
        for line_id in self.reservation_line:
            line_id.reserve &= room_ids
        self.reservation_line -= self.reservation_line.filtered(
            lambda line_id: not line_id.reserve
        )
        for room_id in room_ids - self.reservation_line.reserve:
            line_id = self.reservation_line.filtered(
                lambda line_id, room_id=room_id: (
                    line_id.categ_id == room_id.room_categ_id
                )
            )[:1]
            if line_id:
                line_id.reserve |= room_id
            else:
                self.reservation_line |= self.env["hotel.reservation.line"].new(
                    {
                        "categ_id": room_id.room_categ_id.id,
                        "reserve": [Command.set(room_id.ids)],
                    }
                )

    @api.depends(
        "map_booking_map_calculated_id",
        "map_booking_map_calculated_id.zone_ids.points",
        "map_booking_map_calculated_id.zone_ids.room_ids",
        "map_booking_map_calculated_id.zone_ids.room_type_ids",
        "map_booking_map_calculated_id.zone_ids.room_ids.capacity",
        "checkin",
        "checkout",
        "state",
    )
    def _compute_map_booking_data_calculated(self):
        colors_by_code = self.env["map.booking.state"]._get_colors_by_code()
        for reservation_id in self:
            map_id = reservation_id.map_booking_map_calculated_id._origin
            if not map_id:
                reservation_id.map_booking_data_calculated = False
                continue
            shapes = []
            for zone_id in map_id.zone_ids:
                shapes += reservation_id._get_map_booking_zone_shapes(
                    zone_id, colors_by_code
                )
            reservation_id.map_booking_data_calculated = {
                "image_url": map_id._get_image_url(),
                "shapes": shapes,
                "legend": map_id._get_availability_legend(),
                "legend_position": map_id._get_legend_position(),
                "label_scale": map_id.label_scale or 1,
            }

    def _get_map_booking_zone_shapes(self, zone_id, colors_by_code):
        """Shapes of a zone, colored for the stay of this reservation.

        Only the hotel rooms of the zone count: each one is an item that can
        be picked while it is free during the stay. The zone is free while one
        of its rooms is, and occupied once they are all booked. The caption
        tells how many guests the rooms of the zone can hold.
        """
        self.ensure_one()
        shape_list = zone_id._get_map_shapes()
        if not shape_list:
            return []
        room_units = []
        if self.checkin and self.checkout:
            room_units = [
                (unit, busy)
                for unit, busy in zone_id._get_bookable_units(
                    self.checkin, self.checkout
                )
                if unit._name == "hotel.room"
            ]
        capacity = sum(zone_id._get_zone_rooms().mapped("capacity"))
        caption = False
        if capacity == 1:
            caption = self.env._("1 guest")
        elif capacity:
            caption = self.env._("%(capacity)s guests")
            caption = caption % {"capacity": capacity}
        state = False
        if room_units:
            free = any(not busy for _unit, busy in room_units)
            state = STATE_FREE if free else STATE_OCCUPIED
        for shape in shape_list:
            shape["state"] = state
            shape["colors"] = colors_by_code.get(state)
            shape["caption"] = caption
            shape["items"] = [
                {
                    "id": unit.id,
                    "name": unit.name,
                    "selectable": not busy,
                    "url": False,
                }
                for unit, busy in room_units
            ]
        return shape_list
