// Copyright 2026 mytime.click
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import {MapWidget} from "@map_widget/components/map_widget/map_widget.esm";
import {describe, expect, test} from "@odoo/hoot";
import {animationFrame} from "@odoo/hoot-mock";
import {click, queryAll, queryOne} from "@odoo/hoot-dom";
import {mountWithCleanup} from "@web/../tests/web_test_helpers";

const ZONES = [
    {
        id: "zone-1",
        zone_id: 1,
        name: "Zone A",
        code: "A",
        symbol: false,
        points: "10,10 110,10 110,60 10,60",
        items: [
            {id: 11, name: "Pitch A1", selectable: true},
            {id: 12, name: "Pitch A2", selectable: false},
        ],
    },
    {
        id: "zone-2",
        zone_id: 2,
        name: "Zone B",
        code: false,
        symbol: false,
        points: "210,10 310,10 310,60 210,60",
        items: [],
    },
];

/**
 * Mounts the widget and pretends its image loaded, so the SVG overlay renders
 * (it waits for the image's natural size to build its viewBox).
 */
async function mountMap(props = {}) {
    const map = await mountWithCleanup(MapWidget, {
        props: {
            zones: ZONES,
            mapImageUrl: "/web/image/map.booking.map/1/image",
            ...props,
        },
    });
    const img = queryOne(".o_map_widget_img");
    Object.defineProperty(img, "naturalWidth", {value: 800, configurable: true});
    Object.defineProperty(img, "naturalHeight", {value: 600, configurable: true});
    img.dispatchEvent(new Event("load"));
    await animationFrame();
    return map;
}

describe.current.tags("desktop");

describe("Map widget", () => {
    test("draws one polygon per zone, in the image's pixel space", async () => {
        await mountMap();
        const polygons = queryAll(".o_map_widget_zone");
        expect(polygons).toHaveLength(2);
        expect(polygons[0]).toHaveAttribute("points", ZONES[0].points);
        expect(queryOne(".o_map_widget_svg")).toHaveAttribute("viewBox", "0 0 800 600");
    });

    test("draws the picture inside the SVG, in the zones' pixel space", async () => {
        await mountMap();
        const picture = queryOne(".o_map_widget_svg_image");
        expect(picture).toHaveAttribute("href", "/web/image/map.booking.map/1/image");
        expect(picture).toHaveAttribute("width", "800");
        expect(picture).toHaveAttribute("height", "600");
        // The <img> only keeps the layout size once the SVG draws the picture.
        expect(".o_map_widget_img").toHaveClass("o_map_widget_img_sizer");
    });

    test("the zone picked outside the map is highlighted", async () => {
        await mountMap({
            editable: true,
            onCornersChanged: () => null,
            activeZoneId: 2,
        });
        const [zoneA, zoneB] = queryAll(".o_map_widget_zone");
        expect(zoneB).toHaveClass("o_map_widget_zone_active");
        expect(zoneB).toHaveClass("o_map_widget_zone_editing");
        expect(zoneA).not.toHaveClass("o_map_widget_zone_active");
        // Its corners can be dragged straight away.
        expect(queryAll(".o_map_widget_corner")).toHaveLength(4);
    });

    test("clicking an outline in the editor picks its zone", async () => {
        let picked = null;
        await mountMap({
            editable: true,
            onCornersChanged: () => null,
            onActiveZoneChange: (zoneId) => (picked = zoneId),
        });
        await click(queryAll(".o_map_widget_zone")[0]);
        await animationFrame();
        expect(picked).toBe(1);
    });

    test("a moved outline never leaves the picture", async () => {
        const map = await mountMap();
        // Zone A spans x 10..110 and y 10..60 on an 800 x 600 picture.
        const points = [
            [10, 10],
            [110, 10],
            [110, 60],
            [10, 60],
        ];
        expect(map.limitMoveOffset(points, 30, 40)).toEqual([30, 40]);
        expect(map.limitMoveOffset(points, -50, -50)).toEqual([-10, -10]);
        expect(map.limitMoveOffset(points, 1000, 1000)).toEqual([690, 540]);
    });

    test("shows the zone label only when the zone has a code", async () => {
        await mountMap();
        expect(queryAll(".o_map_widget_zone_marker")).toHaveLength(1);
        expect(queryOne(".o_map_widget_zone_marker_badge")).toHaveText("A");
    });

    test("clicking a zone opens its items panel", async () => {
        await mountMap();
        expect(queryAll(".o_map_widget_panel")).toHaveLength(0);
        await click(queryAll(".o_map_widget_zone")[0]);
        await animationFrame();
        expect(queryOne(".o_map_widget_panel")).toHaveText(/Zone A/);
        expect(queryOne(".o_map_widget_panel")).toHaveText(/Pitch A1/);
    });

    test("the legend stays hidden without a position", async () => {
        await mountMap({
            legend: [{label: "Free", color: "#198754"}],
            legendPosition: "none",
        });
        expect(queryAll(".o_map_widget_legend")).toHaveLength(0);
    });

    test("the legend lists the availability entries", async () => {
        await mountMap({
            legend: [{label: "Free", color: "#198754"}],
            legendPosition: "bottom_left",
        });
        expect(queryOne(".o_map_widget_legend")).toHaveText("Free");
        expect(queryOne(".o_map_widget_legend_swatch")).toHaveAttribute(
            "style",
            "background-color: #198754"
        );
    });

    test("selection mode reports the items picked on the map", async () => {
        let selection = null;
        await mountMap({onSelectItem: (items) => (selection = items)});
        const [zoneA, zoneB] = queryAll(".o_map_widget_zone");
        // A zone holding nothing selectable is greyed out.
        expect(zoneB).toHaveClass("o_map_widget_zone_disabled");
        await click(zoneA);
        await animationFrame();
        expect(selection.map((item) => item.name)).toEqual(["Pitch A1"]);
        // The chip lists the picked item and removes it again.
        expect(queryOne(".o_map_widget_selected_chip")).toHaveText("Pitch A1");
        await click(queryOne(".o_map_widget_selected_chip .btn-close"));
        await animationFrame();
        expect(selection).toEqual([]);
    });

    test("the draft polyline follows the points being drawn", async () => {
        await mountMap({draftPoints: "10,10 100,10 100,50", editable: true});
        expect(queryOne(".o_map_widget_zone_draft")).toHaveAttribute(
            "points",
            "10,10 100,10 100,50"
        );
    });
});
