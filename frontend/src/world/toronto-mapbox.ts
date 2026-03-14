/**
 * Mapbox GL JS 3D map centered on Toronto: terrain + 3D building extrusions.
 * Same integration as TorontoScene: container, startRenderLoop(getHourOfDay), updateState(hourOfDay), dispose.
 * Set VITE_MAPBOX_ACCESS_TOKEN in .env for the map to load.
 */
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import type { LngLat } from "../api/types.js";

export interface MapFollower {
  follower_id: number;
  archetype_id: number;
  name: string;
  position: LngLat | null;
  happiness: number;
}

/** Hex colors for building height gradient (low → high). Default: warm to cool. */
export type BuildingColorPalette = readonly [string, string, ...string[]];

export interface TorontoMapboxOptions {
  container: HTMLElement;
  onResize?: () => void;
  /** Colors for 3D buildings by height (low to high). 2–5 hex colors recommended. */
  buildingColors?: BuildingColorPalette;
}

// Toronto downtown
const TORONTO_CENTER: [number, number] = [-79.38175019453755, 43.64369424043282];

/** Zoom step per click (default Mapbox is 1; smaller = less powerful). */
const ZOOM_DELTA = 0.45;

/** Custom zoom control: same look as NavigationControl but smaller step and position. */
class GentleZoomControl {
  private map?: mapboxgl.Map;
  private container?: HTMLElement;

  onAdd(map: mapboxgl.Map): HTMLElement {
    this.map = map;
    const container = document.createElement("div");
    container.className = "mapboxgl-ctrl mapboxgl-ctrl-group";
    container.style.marginBottom = "24px";

    const zoomIn = document.createElement("button");
    zoomIn.className = "mapboxgl-ctrl-icon mapboxgl-ctrl-zoom-in";
    zoomIn.type = "button";
    zoomIn.setAttribute("aria-label", "Zoom in");
    zoomIn.innerHTML = "+";
    zoomIn.style.fontSize = "18px";
    zoomIn.style.fontWeight = "600";
    zoomIn.style.lineHeight = "1";
    zoomIn.style.backgroundImage = "none";
    zoomIn.addEventListener("click", () => this.zoom(1));

    const zoomOut = document.createElement("button");
    zoomOut.className = "mapboxgl-ctrl-icon mapboxgl-ctrl-zoom-out";
    zoomOut.type = "button";
    zoomOut.setAttribute("aria-label", "Zoom out");
    zoomOut.innerHTML = "−";
    zoomOut.style.fontSize = "18px";
    zoomOut.style.fontWeight = "600";
    zoomOut.style.lineHeight = "1";
    zoomOut.style.backgroundImage = "none";
    zoomOut.addEventListener("click", () => this.zoom(-1));

    container.append(zoomIn, zoomOut);
    this.container = container;
    return container;
  }

  private zoom(direction: 1 | -1): void {
    if (!this.map) return;
    const current = this.map.getZoom();
    const next = Math.min(22, Math.max(0, current + direction * ZOOM_DELTA));
    this.map.easeTo({ zoom: next, duration: 320 });
  }

  onRemove(): void {
    this.container?.remove();
    this.container = undefined;
    this.map = undefined;
  }
}

// Default: warm (low) → cool (tall) gradient
const DEFAULT_BUILDING_PALETTE: BuildingColorPalette = [
  "#819382", // light teal
  "#93A294", // green
  "#A5B2A6", // blue
  "#B7C1B8", // blue-gray
  "#DBE0DC", // mauve
];

// Downtown Toronto neighborhood polygons (GeoJSON: [lng, lat], closed ring).
// These are rough, but aligned more closely with real districts.
const REGIONS: Array<{ name: string; color: string; polygon: GeoJSON.Polygon }> = [
  // Roughly King St W / Queen St W between University and Yonge
  {
    name: "Financial District",
    color: "#22c55e",
    polygon: {
      type: "Polygon",
      coordinates: [
        [
          [-79.3875, 43.6465], // University & King
          [-79.3780, 43.6465], // Yonge & King
          [-79.3780, 43.6518], // Yonge & Queen
          [-79.3875, 43.6518], // University & Queen
          [-79.3875, 43.6465],
        ],
      ],
    },
  },
  // South of Queen, west of University to Spadina
  {
    name: "Entertainment District",
    color: "#3b82f6",
    polygon: {
      type: "Polygon",
      coordinates: [
        [
          [-79.3965, 43.6425], // Spadina & King
          [-79.3875, 43.6425], // University & King
          [-79.3875, 43.6490], // University & Queen
          [-79.3965, 43.6490], // Spadina & Queen
          [-79.3965, 43.6425],
        ],
      ],
    },
  },
  // Waterfront from Spadina to Jarvis
  {
    name: "Harbourfront",
    color: "#0ea5e9",
    polygon: {
      type: "Polygon",
      coordinates: [
        [
          [-79.3965, 43.6345], // Spadina & Queens Quay
          [-79.3720, 43.6345], // Jarvis-ish & Queens Quay
          [-79.3720, 43.6405],
          [-79.3965, 43.6405],
          [-79.3965, 43.6345],
        ],
      ],
    },
  },
  // East of Yonge, south of King towards Distillery / St. Lawrence
  {
    name: "St. Lawrence / Distillery",
    color: "#f59e0b",
    polygon: {
      type: "Polygon",
      coordinates: [
        [
          [-79.3735, 43.6455], // Sherbourne & Front
          [-79.3610, 43.6455], // Parliament
          [-79.3610, 43.6535], // up to King/Front area
          [-79.3735, 43.6535],
          [-79.3735, 43.6455],
        ],
      ],
    },
  },
  // Church-Wellesley area north of Carlton, east of Yonge
  {
    name: "Church-Wellesley",
    color: "#a855f7",
    polygon: {
      type: "Polygon",
      coordinates: [
        [
          [-79.3860, 43.6645], // Yonge & Wellesley
          [-79.3725, 43.6645], // Jarvis-ish
          [-79.3725, 43.6715], // north toward Bloor
          [-79.3860, 43.6715],
          [-79.3860, 43.6645],
        ],
      ],
    },
  },
];

/** Height-based color gradient (for default layer when not in a region). */
function buildingColorExpression(
  palette: BuildingColorPalette
): mapboxgl.Expression {
  const stops: (number | string)[] = [];
  const n = palette.length;
  const heightStops = [0, 25, 75, 150, 300];
  for (let i = 0; i < n; i++) {
    const h = heightStops[Math.min(i, heightStops.length - 1)];
    stops.push(h, palette[i]);
  }
  return ["interpolate", ["linear"], ["get", "height"], ...stops] as mapboxgl.Expression;
}

/** Common height/base paint; pass a color string or expression. */
function buildingExtrusionPaint(
  color: string | mapboxgl.Expression
): Record<string, unknown> {
  return {
    "fill-extrusion-color": color,
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
  };
}

const ARCHETYPE_COLORS: Record<number, string> = {};
const COLOR_POOL = [
  "#7dd3c0", "#2563eb", "#dc2626", "#16a34a", "#ca8a04",
  "#7c3aed", "#0891b2", "#4b5563", "#f472b6", "#fb923c",
  "#10b981", "#6366f1", "#ec4899", "#14b8a6", "#f59e0b",
];

function getArchetypeColor(archetypeId: number): string {
  if (!ARCHETYPE_COLORS[archetypeId]) {
    ARCHETYPE_COLORS[archetypeId] = COLOR_POOL[(archetypeId - 1) % COLOR_POOL.length];
  }
  return ARCHETYPE_COLORS[archetypeId];
}

function buildFollowerGeoJSON(
  followers: MapFollower[],
): GeoJSON.FeatureCollection<GeoJSON.Point> {
  const features: GeoJSON.Feature<GeoJSON.Point>[] = [];
  for (const f of followers) {
    if (!f.position) continue;
    features.push({
      type: "Feature",
      properties: {
        id: f.follower_id,
        name: f.name,
        color: getArchetypeColor(f.archetype_id),
        happiness: f.happiness,
      },
      geometry: {
        type: "Point",
        coordinates: f.position, // already [lng, lat] from toMapbox()
      },
    });
  }
  return { type: "FeatureCollection", features };
}

function setupFollowerLayer(map: mapboxgl.Map, followers: MapFollower[]): void {
  if (map.getSource("followers")) return;
  map.addSource("followers", {
    type: "geojson",
    data: buildFollowerGeoJSON(followers),
  });
  map.addLayer({
    id: "followers-layer",
    type: "circle",
    source: "followers",
    paint: {
      "circle-radius": [
        "interpolate", ["linear"], ["zoom"],
        12, 2,
        15, 5,
        18, 8,
      ],
      "circle-color": ["get", "color"],
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "rgba(255,255,255,0.9)",
      "circle-opacity": [
        "interpolate", ["linear"], ["get", "happiness"],
        0, 0.4,
        1, 1.0,
      ],
    },
  });
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

  // Region tints: GeoJSON fill so each area has a visible color (Mapbox "within" doesn't work for building polygons).
  if (!map.getSource("toronto-regions")) {
    const regionFeatures: GeoJSON.Feature<GeoJSON.Polygon>[] = REGIONS.map(
      (r) => ({
        type: "Feature",
        properties: { color: r.color, name: r.name },
        geometry: r.polygon,
      })
    );
    map.addSource("toronto-regions", {
      type: "geojson",
      data: { type: "FeatureCollection", features: regionFeatures },
    });
  }
  map.addLayer(
    {
      id: "toronto-regions-fill",
      type: "fill",
      source: "toronto-regions",
      paint: {
        "fill-color": ["get", "color"],
        "fill-opacity": 0.7,
        "fill-outline-color": "#020617",
      },
    },
    beforeId
  );

  map.addLayer(
    {
      id: "add-3d-buildings",
      source: "composite",
      "source-layer": "building",
      filter: ["==", "extrude", "true"],
      type: "fill-extrusion",
      minzoom: 14,
      paint: buildingExtrusionPaint(buildingColorExpression(buildingColors)),
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
      // Mapbox Standard (vector) for a clean, modern base map.
      style: "mapbox://styles/mapbox/standard",
      center: TORONTO_CENTER,
      zoom: 15.5,
      pitch: 60,
      bearing: -20,
      antialias: true,
    });

    this.map.addControl(new GentleZoomControl(), "bottom-right");

    this.map.on("style.load", () => {
      if (this.map) {
        setup3D(this.map, this.buildingColors);
        setupFollowerLayer(this.map, []);
      }
    });
  }

  updateState(hourOfDay: number): void {
    if (!this.map) return;
    const timeOfDay = hourOfDay / 24;
    const isNight = timeOfDay < 0.25 || timeOfDay > 0.75;
    const mode = isNight ? "dark" : "light";

    // Soft camera motion over the day (slight pitch + bearing drift, Cities: Skylines‑style).
    const basePitch = 60;
    const pitchWobble = Math.cos(timeOfDay * Math.PI * 2) * 4;
    this.map.setPitch(basePitch + pitchWobble);

    const baseBearing = -20;
    const bearingDrift = Math.sin(timeOfDay * Math.PI * 2) * 6;
    this.map.setBearing(baseBearing + bearingDrift);

    // Atmospheric fog for day/night mood.
    if (this.currentStyle !== mode) {
      this.currentStyle = mode;
      if (isNight) {
        this.map.setFog({
          color: "#020617",
          "horizon-blend": 0.35,
          range: [0.6, 6.0],
          "space-color": "#000010",
          "star-intensity": 0.6,
        } as any);
      } else {
        this.map.setFog({
          color: "#e2e8f0",
          "horizon-blend": 0.18,
          range: [0.9, 8.0],
          "space-color": "#0b1120",
          "star-intensity": 0.0,
        } as any);
      }
    }
  }

  setFollowers(followers: MapFollower[]): void {
    if (!this.map) return;
    const source = this.map.getSource("followers");
    if (source && "setData" in source) {
      (source as mapboxgl.GeoJSONSource).setData(buildFollowerGeoJSON(followers));
    }
  }

  startRenderLoop(getHourOfDay: () => number): void {
    const tick = () => {
      this.animationId = requestAnimationFrame(tick);
      this.updateState(getHourOfDay());
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
