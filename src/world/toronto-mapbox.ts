/**
 * Mapbox GL JS 3D map centered on Toronto: terrain + 3D building extrusions.
 * Same integration as TorontoScene: container, startRenderLoop(getState), updateState(state, day), dispose.
 * Set VITE_MAPBOX_ACCESS_TOKEN in .env for the map to load.
 */
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import type { CityState } from "../types/city-state.js";

/** Hex colors for building height gradient (low → high). Default: warm to cool. */
export type BuildingColorPalette = readonly [string, string, ...string[]];

export interface TorontoMapboxOptions {
  container: HTMLElement;
  onResize?: () => void;
  /** Colors for 3D buildings by height (low to high). 2–5 hex colors recommended. */
  buildingColors?: BuildingColorPalette;
}

// Toronto downtown
const TORONTO_CENTER: [number, number] = [-79.3832, 43.6532];

// Default: warm (low) → cool (tall) gradient
const DEFAULT_BUILDING_PALETTE: BuildingColorPalette = [
  "#a8c5c9", // light teal
  "#5a9b6e", // green
  "#4a90a4", // blue
  "#6b7b8c", // blue-gray
  "#7d6e83", // mauve
];

/** Build a Mapbox interpolate expression for fill-extrusion-color by height. */
function buildingColorExpression(
  palette: BuildingColorPalette
): mapboxgl.Expression {
  const stops: (number | string)[] = [];
  const n = palette.length;
  const heightStops = [0, 25, 75, 150, 300]; // heights in m for gradient stops
  for (let i = 0; i < n; i++) {
    const h = heightStops[Math.min(i, heightStops.length - 1)];
    stops.push(h, palette[i]);
  }
  return ["interpolate", ["linear"], ["get", "height"], ...stops] as mapboxgl.Expression;
}

function setup3D(
  map: mapboxgl.Map,
  buildingColors: BuildingColorPalette = DEFAULT_BUILDING_PALETTE
): void {
  // 3D terrain
  if (!map.getSource("mapbox-dem")) {
    map.addSource("mapbox-dem", {
      type: "raster-dem",
      url: "mapbox://mapbox.mapbox-terrain-dem-v1",
      tileSize: 512,
      maxzoom: 14,
    });
    map.setTerrain({ source: "mapbox-dem", exaggeration: 1.2 });
  }

  // 3D buildings (fill-extrusion) — skip if already added (e.g. same style reload)
  if (map.getLayer("add-3d-buildings")) return;

  const layers = map.getStyle().layers;
  const labelLayer = layers?.find(
    (layer) =>
      layer.type === "symbol" &&
      "layout" in layer &&
      layer.layout &&
      typeof (layer.layout as Record<string, unknown>)["text-field"] !== "undefined"
  );
  const beforeId = labelLayer?.id;

  map.addLayer(
    {
      id: "add-3d-buildings",
      source: "composite",
      "source-layer": "building",
      filter: ["==", "extrude", "true"],
      type: "fill-extrusion",
      minzoom: 14,
      paint: {
        "fill-extrusion-color": buildingColorExpression(buildingColors),
        "fill-extrusion-height": [
          "interpolate",
          ["linear"],
          ["zoom"],
          14,
          0,
          14.05,
          ["get", "height"],
        ],
        "fill-extrusion-base": [
          "interpolate",
          ["linear"],
          ["zoom"],
          14,
          0,
          14.05,
          ["get", "min_height"],
        ],
        "fill-extrusion-opacity": 0.9,
      },
    },
    beforeId
  );
}

export class TorontoMapboxScene {
  private map: mapboxgl.Map | null = null;
  private animationId: number = 0;
  private currentStyle: "light" | "dark" = "light";
  private readonly buildingColors: BuildingColorPalette;

  constructor(options: TorontoMapboxOptions) {
    const { container, buildingColors } = options;
    this.buildingColors = buildingColors ?? DEFAULT_BUILDING_PALETTE;
    const env = (typeof import.meta !== "undefined" && (import.meta as { env?: Record<string, string> }).env) || {};
    const token = env.VITE_MAPBOX_ACCESS_TOKEN || "";

    if (!token) {
      console.warn(
        "VITE_MAPBOX_ACCESS_TOKEN not set. Add it to .env to load the Mapbox map."
      );
      container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;font-family:system-ui;">
        Set VITE_MAPBOX_ACCESS_TOKEN in .env to load the map.
      </div>`;
      return;
    }

    this.map = new mapboxgl.Map({
      container,
      accessToken: token,
      style: "mapbox://styles/mapbox/light-v11",
      center: TORONTO_CENTER,
      zoom: 14.5,
      pitch: 50,
      bearing: -17,
      antialias: true,
    });

    this.map.addControl(new mapboxgl.NavigationControl(), "top-right");

    this.map.on("style.load", () => {
      if (this.map) setup3D(this.map, this.buildingColors);
    });
  }

  updateState(_state: Readonly<CityState>, day: number): void {
    if (!this.map) return;
    const timeOfDay = (day % 24) / 24;
    const isNight = timeOfDay < 0.25 || timeOfDay > 0.75;
    const wantStyle = isNight ? "dark" : "light";
    if (this.currentStyle === wantStyle) return;
    this.currentStyle = wantStyle;
    const styleUrl =
      wantStyle === "dark"
        ? "mapbox://styles/mapbox/dark-v11"
        : "mapbox://styles/mapbox/light-v11";
    this.map.setStyle(styleUrl);
  }

  startRenderLoop(
    getState: () => { state: Readonly<CityState>; day: number }
  ): void {
    const tick = () => {
      this.animationId = requestAnimationFrame(tick);
      const { state, day } = getState();
      this.updateState(state, day);
    };
    tick();
  }

  dispose(): void {
    cancelAnimationFrame(this.animationId);
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }
}
