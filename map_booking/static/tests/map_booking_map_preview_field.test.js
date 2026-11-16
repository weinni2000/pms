// Copyright 2026 mytime.click
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {describe, expect, test} from "@odoo/hoot";
import {click, queryAll, queryOne, select, waitFor} from "@odoo/hoot-dom";
import {animationFrame} from "@odoo/hoot-mock";
import {
    defineModels,
    fields,
    models,
    mountView,
    onRpc,
} from "@web/../tests/web_test_helpers";

// An 800 x 600 picture the browser really loads, so the map gets its size.
const IMAGE_URL =
    "data:image/svg+xml," +
    encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"/>'
    );

class MapBookingMap extends models.Model {
    _name = "map.booking.map";

    label_scale = fields.Float();
    preview_data_calculated = fields.Json();

    _records = [
        {
            id: 1,
            label_scale: 1,
            preview_data_calculated: {
                map_id: 1,
                image_url: IMAGE_URL,
                zones: [
                    {id: 1, name: "Flat 1", code: "F1", symbol: false, map_id: 1},
                    {id: 2, name: "Flat 2", code: "F2", symbol: false, map_id: 1},
                ],
                shapes: [
                    {
                        id: "zone-1",
                        zone_id: 1,
                        name: "Flat 1",
                        code: "F1",
                        symbol: false,
                        points: "10,10 110,10 110,60 10,60",
                        items: [],
                        state: false,
                    },
                ],
                legend: [],
                legend_position: "none",
            },
        },
    ];
}

defineModels([MapBookingMap]);

async function mountEditor() {
    await mountView({
        type: "form",
        resModel: "map.booking.map",
        resId: 1,
        arch: `<form>
            <field name="label_scale" invisible="1"/>
            <field name="preview_data_calculated" widget="map_booking_map_preview"/>
        </form>`,
    });
    await waitFor(".o_map_widget_svg");
}

describe.current.tags("desktop");

describe("Map booking map editor", () => {
    test("New polygon is only offered for a zone without an outline", async () => {
        await mountEditor();
        expect(".o_map_widget_editor .btn-success").toHaveCount(0);
        await select("1", {target: "#o_map_booking_zone_select"});
        await animationFrame();
        expect(".o_map_widget_editor .btn-success").toHaveCount(0);
        await select("2", {target: "#o_map_booking_zone_select"});
        await animationFrame();
        expect(".o_map_widget_editor .btn-success").toHaveText("New polygon: Flat 2");
    });

    test("Clear removes the points drawn so far and stops drawing", async () => {
        await mountEditor();
        await select("2", {target: "#o_map_booking_zone_select"});
        await animationFrame();
        await click(".o_map_widget_editor .btn-success");
        await animationFrame();
        const svg = queryOne(".o_map_widget_svg");
        await click(svg, {position: {x: 100, y: 100}, relative: true});
        await click(svg, {position: {x: 200, y: 100}, relative: true});
        await animationFrame();
        expect(".o_map_widget_zone_draft").toHaveCount(1);
        const clear = queryAll(".o_map_widget_editor .btn-secondary").find(
            (button) => button.textContent.trim() === "Clear"
        );
        await click(clear);
        await animationFrame();
        expect(".o_map_widget_zone_draft").toHaveCount(0);
        // Back to the start: "New polygon" is offered again, Clear is gone.
        expect(".o_map_widget_editor .btn-success").toHaveText("New polygon: Flat 2");
        expect(".o_map_widget_editor .btn-secondary").toHaveCount(0);
    });

    test("Clear removes the outline of the picked zone", async () => {
        onRpc("map.booking.zone", "write", ({args}) => {
            expect.step(args);
            return true;
        });
        await mountEditor();
        expect(".o_map_widget_editor .btn-secondary").toHaveCount(0);
        await select("1", {target: "#o_map_booking_zone_select"});
        await animationFrame();
        await click(".o_map_widget_editor .btn-secondary");
        await animationFrame();
        expect.verifySteps([[[1], {points: false}]]);
        expect(".o_map_widget_zone").toHaveCount(0);
        // The zone can now be drawn again.
        expect(".o_map_widget_editor .btn-success").toHaveText("New polygon: Flat 1");
    });

    test("Clear works before any point is placed", async () => {
        await mountEditor();
        await select("2", {target: "#o_map_booking_zone_select"});
        await animationFrame();
        await click(".o_map_widget_editor .btn-success");
        await animationFrame();
        await click(".o_map_widget_editor .btn-secondary");
        await animationFrame();
        expect(".o_map_widget_editor .btn-success").toHaveText("New polygon: Flat 2");
    });
});
