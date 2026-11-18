// Copyright 2026 mytime.click
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {Component, onWillStart, useExternalListener, useState} from "@odoo/owl";
import {Interaction} from "@web/public/interaction";
import {MapWidget} from "@map_widget/components/map_widget/map_widget.esm";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

const DATE_INPUT_IDS = ["date_start", "date_end"];

function getDateValues() {
    const values = {};
    for (const id of DATE_INPUT_IDS) {
        const input = document.getElementById(id);
        if (input && input.value) {
            values[id] = input.value;
        }
    }
    return values;
}

/**
 * Map of the booking dialog: the booked property is highlighted, the zones are
 * colored for the dates of the dialog, and clicking another free zone opens
 * the booking dialog of its property, keeping the dates.
 */
export class PmsWebsiteMap extends Component {
    static template = "map_booking_pms_website_sale.PmsWebsiteMap";
    static components = {MapWidget};
    static props = {propertyId: Number};

    setup() {
        this.state = useState({data: {}, key: 0});
        onWillStart(() => this.load());
        useExternalListener(document, "change", (ev) => {
            if (DATE_INPUT_IDS.includes(ev.target.id)) {
                this.load();
            }
        });
    }

    async load() {
        const values = getDateValues();
        this.state.data =
            (await rpc(`/property/${this.props.propertyId}/map_booking`, values)) || {};
        // Redraw the map: its own copy of the picked items starts over.
        this.state.key++;
    }

    onSelectItems(items) {
        const other = items.find((item) => item.id !== this.props.propertyId);
        if (other && other.website_url) {
            const params = new URLSearchParams({book: "1", ...getDateValues()});
            window.location.href = `${other.website_url}?${params}`;
            return;
        }
        // The booked property cannot be unpicked: highlight it again.
        this.state.key++;
    }
}

export class PmsWebsiteMapInteraction extends Interaction {
    static selector = ".o_map_booking_pms_website_map";

    setup() {
        this.mountComponent(
            this.el.querySelector(".o_map_booking_pms_website_map_mount"),
            PmsWebsiteMap,
            {propertyId: Number(this.el.dataset.propertyId)}
        );
    }

    start() {
        // Arrived from another property's map: reopen the dialog with the dates.
        const params = new URLSearchParams(window.location.search);
        if (!params.get("book")) {
            return;
        }
        for (const id of DATE_INPUT_IDS) {
            const input = document.getElementById(id);
            if (input && params.get(id)) {
                input.value = params.get(id);
                input.dispatchEvent(new Event("change", {bubbles: true}));
            }
        }
        const modal = document.getElementById("pmsBookingModal");
        if (modal && window.Modal) {
            window.Modal.getOrCreateInstance(modal).show();
        }
    }
}

registry
    .category("public.interactions")
    .add("map_booking_pms_website_sale.map", PmsWebsiteMapInteraction);
