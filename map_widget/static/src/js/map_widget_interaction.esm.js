// Copyright 2026 mytime.click
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import {registry} from "@web/core/registry";
import {Interaction} from "@web/public/interaction";
import {MapWidget} from "@map_widget/components/map_widget/map_widget.esm";

/**
 * Mounts a MapWidget on a public page from data attributes.
 *
 * Any QWeb template can render the map without JavaScript:
 *
 * ```xml
 * <div class="o_map_widget"
 *      data-map-image="/web/image/map.booking.map/1/image"
 *      data-zones="[{...}]"
 *      data-legend="[{...}]"
 *      data-legend-position="bottom_left">
 *   <div class="o_map_widget_mount"/>
 * </div>
 * ```
 *
 * See `readme/USAGE.md` for the full attribute list.
 */
export class MapWidgetInteraction extends Interaction {
    static selector = ".o_map_widget";

    setup() {
        const zones = JSON.parse(this.el.dataset.zones || "[]");
        const mapImageUrl = this.el.dataset.mapImage;
        const mountEl = this.el.querySelector(".o_map_widget_mount");
        const selectable = this.el.dataset.selectable === "true";
        const selectedItemIds = (this.el.dataset.selectedItems || "")
            .split(",")
            .map((value) => Number(value))
            .filter((value) => Number.isInteger(value) && value > 0);
        const props = {
            zones,
            mapImageUrl,
            selectedItemIds,
            legend: JSON.parse(this.el.dataset.legend || "[]"),
            legendPosition: this.el.dataset.legendPosition || "none",
        };
        if (selectable) {
            props.onSelectItem = (items) => {
                const input = document.getElementById(this.el.dataset.inputId);
                // A selector (not a single id): a page can show the same map
                // twice, with both Continue buttons sharing this class.
                const buttons = document.querySelectorAll(
                    this.el.dataset.buttonSelector
                );
                if (input) {
                    input.value = items.map((item) => item.id).join(",");
                }
                buttons.forEach((button) => {
                    button.disabled = items.length === 0;
                });
            };
        }
        this.mountComponent(mountEl, MapWidget, props);
    }
}

registry
    .category("public.interactions")
    .add("map_widget.map_widget", MapWidgetInteraction);
