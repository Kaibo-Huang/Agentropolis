/**
 * Mapbox GL JS 3D map centered on Toronto: terrain + 3D building extrusions.
 * Same integration as TorontoScene: container, startRenderLoop(getHourOfDay), updateState(hourOfDay), dispose.
 * Set VITE_MAPBOX_ACCESS_TOKEN in .env for the map to load.
 */
import mapboxgl from "mapbox-gl";
import type { LngLat } from "../api/types.js";

/** Resolved avatar params for rendering (from seed or custom). */
export interface MapFollowerAvatar {
  skinTone: number;
  bodyType: string;
  hairTexture: string;
  hairStyle: string;
  hairColor: string;
  outfit: string;
  outfitColor: string;
  accessories: string[];
}

export interface MapFollower {
  follower_id: number;
  archetype_id: number;
  name: string;
  position: LngLat | null;
  happiness: number;
  /** Resolved avatar params for future avatar layer; undefined if not resolved */
  avatar?: MapFollowerAvatar;
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
    const next = Math.min(18, Math.max(13, current + direction * ZOOM_DELTA));
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

// ── Voronoi zone computation ──
// Zones are computed from seed points using Delaunay/Voronoi tessellation,
// then clipped to a land polygon that follows the Toronto shoreline.
// This produces organic, natural-looking boundaries that tile all visible land.

import { Delaunay } from "d3-delaunay";

// Seed points for residential neighborhoods (same as backend)
const RESIDENTIAL_SEEDS = [
  { name: "Liberty Village / Exhibition",      lng: -79.411, lat: 43.640, color: "#10b981" },
  { name: "Queen West / Trinity-Bellwoods",    lng: -79.416, lat: 43.670, color: "#f59e0b" },
  { name: "Entertainment / Harbourfront",      lng: -79.390, lat: 43.643, color: "#3b82f6" },
  { name: "Chinatown / Kensington",            lng: -79.392, lat: 43.668, color: "#ef4444" },
  { name: "Financial / St. Lawrence",          lng: -79.373, lat: 43.645, color: "#22c55e" },
  { name: "Downtown Yonge / Church-Wellesley", lng: -79.373, lat: 43.668, color: "#a855f7" },
  { name: "Corktown / Distillery",             lng: -79.348, lat: 43.650, color: "#f97316" },
  { name: "Cabbagetown / Regent Park",         lng: -79.348, lat: 43.670, color: "#06b6d4" },
];

// Seed points for work districts (same as backend)
// bounds = [min_lng, min_lat, max_lng, max_lat] from original rectangles on main
const WORK_SEEDS = [
  { name: "Financial District",     lng: -79.3805, lat: 43.6485, color: "#2563eb", bounds: [-79.387, 43.644, -79.374, 43.653] as const },
  { name: "Entertainment District", lng: -79.393,  lat: 43.6465, color: "#7c3aed", bounds: [-79.400, 43.642, -79.386, 43.651] as const },
  { name: "Tech Corridor",          lng: -79.4125, lat: 43.6405, color: "#0891b2", bounds: [-79.420, 43.636, -79.405, 43.645] as const },
  { name: "UofT District",          lng: -79.3945, lat: 43.6635, color: "#1d4ed8", bounds: [-79.401, 43.658, -79.388, 43.669] as const },
  { name: "TMU District",           lng: -79.380,  lat: 43.659,  color: "#0369a1", bounds: [-79.385, 43.654, -79.375, 43.664] as const },
  { name: "Government District",    lng: -79.3895, lat: 43.659,  color: "#b91c1c", bounds: [-79.396, 43.652, -79.383, 43.666] as const },
  { name: "Hospital Row",           lng: -79.388,  lat: 43.6615, color: "#dc2626", bounds: [-79.393, 43.655, -79.383, 43.668] as const },
  { name: "CNE / Exhibition Place", lng: -79.4125, lat: 43.636,  color: "#ca8a04", bounds: [-79.420, 43.633, -79.405, 43.639] as const },
];
const WORK_BUFFER = 0.003; // ~300m buffer around original bounds

// Land polygon: extended clip boundary with Toronto shoreline on south edge.
// Covers full visible viewport at minZoom 13 (well beyond maxBounds).
// MUST be counter-clockwise for Sutherland-Hodgman clipping (isInside test).
const LAND_POLYGON: [number, number][] = [
  // Start NW, go CCW: west edge down, shoreline west-to-east, east edge up, top edge west
  // Extended to cover full viewport at zoom 13 with pitch on large screens
  [-79.55, 43.75],
  [-79.55, 43.628],    // SW: far west (Humber Bay / Mimico)
  // Shoreline waypoints (west to east) — refined to track actual waterfront
  [-79.45, 43.630],    // Humber Bay east
  [-79.435, 43.631],   // Sunnyside area
  [-79.425, 43.631],   // Exhibition Place west / Marilyn Bell Park
  [-79.418, 43.630],   // BMO Field / Exhibition Place south edge
  [-79.412, 43.631],   // Ontario Place / Budweiser Stage
  [-79.407, 43.632],   // Stadium Rd / Fort York approach
  [-79.402, 43.633],   // Bathurst Quay / Portland slip
  [-79.398, 43.634],   // Music Garden
  [-79.395, 43.635],   // Spadina Quay / HTO Park
  [-79.389, 43.636],   // Rees St slip
  [-79.383, 43.637],   // York Quay / Harbourfront Centre
  [-79.378, 43.637],   // York / Simcoe slip
  [-79.373, 43.638],   // Yonge Quay / Jack Layton Ferry Terminal
  [-79.368, 43.638],   // Jarvis / Queens Quay
  [-79.363, 43.639],   // Jarvis slip
  [-79.358, 43.640],   // Parliament slip
  [-79.350, 43.641],   // Sugar Beach / Sherbourne Common
  [-79.340, 43.644],   // Keating Channel / Villiers Island
  [-79.330, 43.646],   // Cherry Beach approach
  [-79.30, 43.648],    // East Bayfront / Port Lands
  // East edge up to NE
  [-79.24, 43.648],
  [-79.24, 43.75],
  // Close
  [-79.55, 43.75],
];

// Voronoi bounding box (must cover LAND_POLYGON entirely)
const VORONOI_BOUNDS: [number, number, number, number] = [-79.55, 43.62, -79.24, 43.75];

/**
 * Sutherland-Hodgman polygon clipping algorithm.
 * Clips `subject` polygon against `clip` polygon.
 * Both are arrays of [x, y] coordinate pairs (assumed closed: last != first is ok).
 */
function clipPolygon(
  subject: [number, number][],
  clip: [number, number][],
): [number, number][] {
  let output = subject.slice();
  for (let i = 0; i < clip.length - 1; i++) {
    if (output.length === 0) return [];
    const edgeStart = clip[i];
    const edgeEnd = clip[i + 1];
    const input = output;
    output = [];
    for (let j = 0; j < input.length; j++) {
      const current = input[j];
      const prev = input[(j + input.length - 1) % input.length];
      const currInside = isInside(current, edgeStart, edgeEnd);
      const prevInside = isInside(prev, edgeStart, edgeEnd);
      if (currInside) {
        if (!prevInside) {
          output.push(intersect(prev, current, edgeStart, edgeEnd));
        }
        output.push(current);
      } else if (prevInside) {
        output.push(intersect(prev, current, edgeStart, edgeEnd));
      }
    }
  }
  return output;
}

function isInside(p: [number, number], a: [number, number], b: [number, number]): boolean {
  return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0;
}

function intersect(
  a: [number, number], b: [number, number],
  c: [number, number], d: [number, number],
): [number, number] {
  const a1 = b[1] - a[1], b1 = a[0] - b[0], c1 = a1 * a[0] + b1 * a[1];
  const a2 = d[1] - c[1], b2 = c[0] - d[0], c2 = a2 * c[0] + b2 * c[1];
  const det = a1 * b2 - a2 * b1;
  return [(c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det];
}

/**
 * Compute Voronoi zones from seed points, clipped to the land polygon.
 */
function computeVoronoiZones(
  seeds: Array<{ name: string; lng: number; lat: number; color: string }>,
): Array<{ name: string; color: string; polygon: GeoJSON.Polygon }> {
  const delaunay = Delaunay.from(seeds, s => s.lng, s => s.lat);
  const voronoi = delaunay.voronoi(VORONOI_BOUNDS);
  return seeds.map((seed, i) => {
    const rawCell = voronoi.cellPolygon(i);
    // rawCell is closed: [[x,y], ..., [x,y]] where first == last
    const clipped = clipPolygon(rawCell as [number, number][], LAND_POLYGON);
    // Close the polygon for GeoJSON
    const coords = clipped.slice();
    if (coords.length > 0 && (coords[0][0] !== coords[coords.length - 1][0] || coords[0][1] !== coords[coords.length - 1][1])) {
      coords.push(coords[0]);
    }
    return {
      name: seed.name,
      color: seed.color,
      polygon: { type: "Polygon" as const, coordinates: [coords] },
    };
  });
}

// ── Residential Neighborhoods (8) ──
// Voronoi cells from seed points, clipped to land polygon (shoreline-aware).
const RESIDENTIAL_ZONES = computeVoronoiZones(RESIDENTIAL_SEEDS);

// ── Work Districts (8) ──
// Voronoi cells clipped to both land polygon AND local envelope (buffered original bounds).
// This gives organic Voronoi edges between neighboring districts without expanding to fill the map.
const WORK_ZONES = (() => {
  const delaunay = Delaunay.from(WORK_SEEDS, s => s.lng, s => s.lat);
  const voronoi = delaunay.voronoi(VORONOI_BOUNDS);
  return WORK_SEEDS.map((seed, i) => {
    const rawCell = voronoi.cellPolygon(i) as [number, number][];
    // Clip to land polygon (shoreline), then to local envelope
    const b = seed.bounds;
    const localEnvelope: [number, number][] = [
      [b[0] - WORK_BUFFER, b[1] - WORK_BUFFER],
      [b[2] + WORK_BUFFER, b[1] - WORK_BUFFER],
      [b[2] + WORK_BUFFER, b[3] + WORK_BUFFER],
      [b[0] - WORK_BUFFER, b[3] + WORK_BUFFER],
      [b[0] - WORK_BUFFER, b[1] - WORK_BUFFER],
    ];
    const clipped = clipPolygon(clipPolygon(rawCell, LAND_POLYGON), localEnvelope);
    const coords = clipped.slice();
    if (coords.length > 0 && (coords[0][0] !== coords[coords.length - 1][0] || coords[0][1] !== coords[coords.length - 1][1])) {
      coords.push(coords[0]);
    }
    return {
      name: seed.name,
      color: seed.color,
      polygon: { type: "Polygon" as const, coordinates: [coords] },
    };
  });
})();

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

const TRAVEL_DURATION_MS = 3000;

function easeInOut(t: number): number {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

function interpolateFollowers(
  from: MapFollower[],
  to: MapFollower[],
  t: number,
): MapFollower[] {
  const fromMap = new Map<number, LngLat>(
    from.flatMap(f => f.position ? [[f.follower_id, f.position]] : [])
  );
  return to.map(f => {
    if (!f.position) return f;
    const prev = fromMap.get(f.follower_id);
    if (!prev) return f;
    return {
      ...f,
      position: [
        prev[0] + (f.position[0] - prev[0]) * t,
        prev[1] + (f.position[1] - prev[1]) * t,
      ] as LngLat,
    };
  });
}

function buildFollowerGeoJSON(
  followers: MapFollower[],
): GeoJSON.FeatureCollection<GeoJSON.Point> {
  const features: GeoJSON.Feature<GeoJSON.Point>[] = [];
  for (const f of followers) {
    if (!f.position) continue;
    // Use avatar outfit color when resolved, else fall back to archetype color
    const color = f.avatar?.outfitColor ?? getArchetypeColor(f.archetype_id);
    features.push({
      type: "Feature",
      properties: {
        id: f.follower_id,
        name: f.name,
        color,
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

/** Interpolate skin tone 0–1 to hex (light → dark). */
function skinToneToHex(t: number): string {
  const light = [0xf5, 0xe6, 0xd3];
  const dark = [0x2d, 0x1f, 0x14];
  const r = Math.round(light[0] + (dark[0] - light[0]) * t);
  const g = Math.round(light[1] + (dark[1] - light[1]) * t);
  const b = Math.round(light[2] + (dark[2] - light[2]) * t);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

/** Build popup HTML for a follower as a profile card. */
function buildFollowerPopupHTML(f: MapFollower): string {
  const happinessPct = Math.round(f.happiness * 100);
  const color = f.avatar?.outfitColor ?? getArchetypeColor(f.archetype_id);
  const appearance =
    f.avatar
      ? [
          escapeHtml(f.avatar.bodyType),
          `${escapeHtml(f.avatar.hairStyle)} · ${escapeHtml(f.avatar.hairColor)}`,
          `${escapeHtml(f.avatar.outfit)}`,
          f.avatar.accessories.length
            ? f.avatar.accessories.map(escapeHtml).join(", ")
            : null,
        ]
          .filter(Boolean)
          .join(" · ")
      : "";

  return `
    <div class="profile-card">
      <header class="profile-card-header">
        <div class="profile-card-avatar" style="background-color:${escapeHtml(color)}"></div>
        <div class="profile-card-title">
          <span class="profile-card-name">${escapeHtml(f.name)}</span>
          <span class="profile-card-meta">Archetype ${f.archetype_id}</span>
        </div>
      </header>
      <div class="profile-card-body">
        <div class="profile-card-row">
          <span class="profile-card-label">Mood</span>
          <div class="profile-card-happiness">
            <div class="profile-card-happiness-bar" style="width:${happinessPct}%"></div>
            <span class="profile-card-happiness-text">${happinessPct}%</span>
          </div>
        </div>
        ${appearance ? `<div class="profile-card-row profile-card-appearance"><span class="profile-card-label">Look</span><span>${appearance}</span></div>` : ""}
      </div>
    </div>`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Add Mapbox built-in circle layer for followers (avatar color from properties). */
function setupFollowerLayer(
  map: mapboxgl.Map,
  followers: MapFollower[],
): void {
  if (map.getSource("followers")) return;
  map.addSource("followers", {
    type: "geojson",
    data: buildFollowerGeoJSON(followers),
  });
  map.addLayer({
    id: "followers-layer",
    type: "circle",
    source: "followers",
    minzoom: 12,
    paint: {
      "circle-radius": [
        "interpolate",
        ["linear"],
        ["zoom"],
        12, 2,
        15, 5,
        18, 8,
      ],
      "circle-color": ["get", "color"],
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "rgba(255,255,255,0.9)",
      "circle-opacity": [
        "interpolate",
        ["linear"],
        ["get", "happiness"],
        0, 0.4,
        1, 1,
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

  // ── Residential Neighborhoods (soft tint) ──
  if (!map.getSource("toronto-residential")) {
    const residentialFeatures: GeoJSON.Feature<GeoJSON.Polygon>[] = RESIDENTIAL_ZONES.map(
      (z) => ({
        type: "Feature" as const,
        properties: { color: z.color, name: z.name },
        geometry: z.polygon,
      })
    );
    map.addSource("toronto-residential", {
      type: "geojson",
      data: { type: "FeatureCollection", features: residentialFeatures },
    });
  }
  map.addLayer(
    {
      id: "toronto-residential-fill",
      type: "fill",
      source: "toronto-residential",
      slot: "middle",
      paint: {
        "fill-color": ["get", "color"],
        "fill-opacity": 0.18,
      },
    },
    beforeId
  );
  map.addLayer(
    {
      id: "toronto-residential-outline",
      type: "line",
      source: "toronto-residential",
      slot: "middle",
      paint: {
        "line-color": ["get", "color"],
        "line-width": 1.5,
        "line-dasharray": [4, 3],
        "line-opacity": 0.6,
      },
    },
    beforeId
  );
  map.addLayer({
    id: "toronto-residential-labels",
    type: "symbol",
    source: "toronto-residential",
    layout: {
      "text-field": ["get", "name"],
      "text-size": 11,
      "text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
      "text-anchor": "center",
      "text-max-width": 8,
    },
    paint: {
      "text-color": "#374151",
      "text-halo-color": "rgba(255,255,255,0.85)",
      "text-halo-width": 1.5,
      "text-opacity": 0.8,
    },
  });

  // ── Work Districts (bold overlay) ──
  if (!map.getSource("toronto-work")) {
    const workFeatures: GeoJSON.Feature<GeoJSON.Polygon>[] = WORK_ZONES.map(
      (z) => ({
        type: "Feature" as const,
        properties: { color: z.color, name: z.name },
        geometry: z.polygon,
      })
    );
    map.addSource("toronto-work", {
      type: "geojson",
      data: { type: "FeatureCollection", features: workFeatures },
    });
  }
  map.addLayer(
    {
      id: "toronto-work-fill",
      type: "fill",
      source: "toronto-work",
      slot: "middle",
      paint: {
        "fill-color": ["get", "color"],
        "fill-opacity": 0.35,
      },
    },
    beforeId
  );
  map.addLayer(
    {
      id: "toronto-work-outline",
      type: "line",
      source: "toronto-work",
      slot: "middle",
      paint: {
        "line-color": ["get", "color"],
        "line-width": 2,
        "line-opacity": 0.8,
      },
    },
    beforeId
  );
  map.addLayer({
    id: "toronto-work-labels",
    type: "symbol",
    source: "toronto-work",
    layout: {
      "text-field": ["get", "name"],
      "text-size": 12,
      "text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"],
      "text-anchor": "center",
      "text-max-width": 7,
    },
    paint: {
      "text-color": "#1f2937",
      "text-halo-color": "rgba(255,255,255,0.9)",
      "text-halo-width": 1.8,
      "text-opacity": 0.9,
    },
  });

  // "composite" source only exists in classic Mapbox styles (streets-v12, etc.).
  // The Standard style has built-in 3D buildings, so skip if source is missing.
  if (map.getSource("composite")) {
    map.addLayer(
      {
        id: "add-3d-buildings",
        source: "composite",
        "source-layer": "building",
        filter: ["==", "extrude", "true"],
        type: "fill-extrusion",
        minzoom: 14,
        slot: "middle",
        paint: buildingExtrusionPaint(buildingColorExpression(buildingColors)),
      },
      beforeId
    );
  }
}

export class TorontoMapboxScene {
  private map: mapboxgl.Map | null = null;
  private animationId: number = 0;
  private currentStyle: "light" | "dark" = "light";
  private readonly buildingColors: BuildingColorPalette;
  private followers: MapFollower[] = [];
  private container: HTMLElement;
  private userInteracting: boolean = false;
  private dragPos: { x: number; y: number } | null = null;
  private onMouseMove: ((e: MouseEvent) => void) | null = null;
  private onMouseUp: ((e: MouseEvent) => void) | null = null;
  private boundMouseUp: ((e: MouseEvent) => void) | null = null;
  private onWheel: ((e: WheelEvent) => void) | null = null;
  private onContainerMouseDown: ((e: MouseEvent) => void) | null = null;
  private lastFollowers: MapFollower[] = [];
  private animFromFollowers: MapFollower[] = [];
  private animToFollowers: MapFollower[] = [];
  private animStartTime: number = -1;
  private followerPopup: mapboxgl.Popup | null = null;
  private pendingFollowers: MapFollower[] | null = null;
  // Store map event handlers for cleanup
  private mapHandlers: { event: string; handler: (...args: unknown[]) => void; layer?: string }[] = [];

  constructor(options: TorontoMapboxOptions) {
    const { container, buildingColors } = options;
    this.container = container;
    this.buildingColors = buildingColors ?? DEFAULT_BUILDING_PALETTE;
    const token = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || "";

    if (!token) {
      console.warn(
        "NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN not set. Add it to .env.local to load the Mapbox map."
      );
      container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280;font-family:system-ui;">
        Set NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN in .env.local to load the map.
      </div>`;
      return;
    }

    this.map = new mapboxgl.Map({
      container,
      accessToken: token,
      style: "mapbox://styles/mapbox/standard",
      center: TORONTO_CENTER,
      zoom: 15.2,
      minZoom: 13,
      maxZoom: 18,
      pitch: 40,
      maxPitch: 60,
      bearing: -20,
      antialias: true,
      // Downtown Toronto core: Bathurst → DVP, waterfront → Bloor
      maxBounds: [
        [-79.42, 43.62], // SW: Bathurst & lakeshore
        [-79.34, 43.69], // NE: just east of DVP & Bloor
      ],
    });

    this.map.addControl(new GentleZoomControl(), "bottom-right");

    this.followerPopup = new mapboxgl.Popup({
      closeButton: true,
      closeOnClick: false,
      className: "follower-popup-container",
      anchor: "bottom",
      offset: [0, 500],
    });

    const CLICK_MOVE_THRESHOLD_PX = 6;

    const d = 10;
    const getBox = (point: { x: number; y: number }) =>
      [
        [point.x - d, point.y - d],
        [point.x + d, point.y + d],
      ] as [mapboxgl.PointLike, mapboxgl.PointLike];

    const tryShowFollowerPopup = (point: { x: number; y: number }) => {
      if (!this.map || !this.followerPopup) return;
      const features = this.map.queryRenderedFeatures(getBox(point), {
        layers: ["followers-layer"],
      });
      if (features.length === 0) return;
      const feat = features[0];
      const fid = feat.properties?.id as number | undefined;
      if (fid == null) return;
      const follower = this.lastFollowers.find((f) => f.follower_id === fid);
      if (!follower) return;
      const coord = (feat.geometry as GeoJSON.Point).coordinates;
      const lngLat = { lng: coord[0], lat: coord[1] };
      this.followerPopup
        .setLngLat(lngLat)
        .setHTML(buildFollowerPopupHTML(follower))
        .addTo(this.map);
    };

    const closeFollowerPopupWithAnimation = () => {
      if (!this.followerPopup || !this.map) return;
      if (!this.followerPopup.isOpen()) return;
      const containerEl = this.map.getContainer();
      const popupEl = containerEl.querySelector(".follower-popup-container");
      if (!popupEl) {
        this.followerPopup.remove();
        return;
      }
      popupEl.classList.add("popup-closing");
      const onEnd = () => {
        popupEl.removeEventListener("transitionend", onEnd);
        this.followerPopup?.remove();
      };
      popupEl.addEventListener("transitionend", onEnd);
    };

    // Manual drag-to-pan: bypass whatever is blocking Mapbox's internal dragPan.
    this.onContainerMouseDown = (e: MouseEvent) => {
      if (e.button !== 0) return;
      // Don't intercept clicks on Mapbox controls (zoom buttons, etc.)
      if ((e.target as HTMLElement).closest(".mapboxgl-ctrl")) return;
      this.dragPos = { x: e.clientX, y: e.clientY };
      this.userInteracting = true;
      container.style.cursor = "grabbing";
    };
    container.addEventListener("mousedown", this.onContainerMouseDown);

    const BOUNDS_W = -79.38, BOUNDS_E = -79.37, BOUNDS_S = 43.63, BOUNDS_N = 43.66;
    const clampCenter = () => {
      if (!this.map) return;
      const c = this.map.getCenter();
      const lng = Math.max(BOUNDS_W, Math.min(BOUNDS_E, c.lng));
      const lat = Math.max(BOUNDS_S, Math.min(BOUNDS_N, c.lat));
      if (lng !== c.lng || lat !== c.lat) {
        this.map.setCenter([lng, lat]);
      }
    };

    this.onMouseMove = (e: MouseEvent) => {
      if (!this.dragPos || !this.map) return;
      const dx = e.clientX - this.dragPos.x;
      const dy = e.clientY - this.dragPos.y;
      this.map.panBy([-dx, -dy], { duration: 0 });
      clampCenter();
      this.dragPos = { x: e.clientX, y: e.clientY };
    };

    this.onMouseUp = (e: MouseEvent) => {
      if (!this.dragPos) return;
      const dx = e.clientX - this.dragPos.x;
      const dy = e.clientY - this.dragPos.y;
      const moved = Math.sqrt(dx * dx + dy * dy);
      const wasClick = moved < CLICK_MOVE_THRESHOLD_PX;
      this.dragPos = null;
      this.userInteracting = false;
      container.style.cursor = "";

      if (wasClick && this.map) {
        const rect = container.getBoundingClientRect();
        const point = { x: e.clientX - rect.left, y: e.clientY - rect.top };
        const features = this.map.queryRenderedFeatures(getBox(point), {
          layers: ["followers-layer"],
        });
        const popupEl = this.map.getContainer().querySelector(".follower-popup-container");
        const clickedOutsideCard = popupEl && !popupEl.contains(e.target as Node);
        if (
          this.followerPopup?.isOpen() &&
          clickedOutsideCard &&
          features.length === 0
        ) {
          closeFollowerPopupWithAnimation();
          return;
        }
        if (features.length > 0) {
          tryShowFollowerPopup(point);
        }
      }
    };

    const onMouseEnterFollowers = () => {
      if (this.map) this.map.getCanvas().style.cursor = "pointer";
    };
    const onMouseLeaveFollowers = () => {
      if (this.map) this.map.getCanvas().style.cursor = "";
    };
    this.map.on("mouseenter", "followers-layer", onMouseEnterFollowers);
    this.map.on("mouseleave", "followers-layer", onMouseLeaveFollowers);

    this.boundMouseUp = (e: MouseEvent) => this.onMouseUp?.(e);
    window.addEventListener("mousemove", this.onMouseMove!);
    window.addEventListener("mouseup", this.boundMouseUp);

    // Pause day-cycle pitch/bearing animation during any user interaction
    // (drag, rotate, zoom) so setPitch/setBearing don't interrupt easeTo animations.
    const startInteract = () => { this.userInteracting = true; };
    const endInteract = () => { this.userInteracting = false; };
    this.map.on("dragstart", startInteract);
    this.map.on("dragend", endInteract);
    this.map.on("rotatestart", startInteract);
    this.map.on("rotateend", endInteract);
    this.map.on("zoomstart", startInteract);
    this.map.on("zoomend", endInteract);

    // Store handler references for dispose() cleanup
    this.mapHandlers = [
      { event: "mouseenter", handler: onMouseEnterFollowers, layer: "followers-layer" },
      { event: "mouseleave", handler: onMouseLeaveFollowers, layer: "followers-layer" },
      { event: "dragstart", handler: startInteract },
      { event: "dragend", handler: endInteract },
      { event: "rotatestart", handler: startInteract },
      { event: "rotateend", handler: endInteract },
      { event: "zoomstart", handler: startInteract },
      { event: "zoomend", handler: endInteract },
    ];

    // Disable Mapbox's built-in scroll zoom — it drifts north on pitched maps
    // because it zooms toward the raycasted ground point under the cursor.
    // Replace with a center-based zoom that uses easeTo so it never drifts.
    // Disable Mapbox's built-in scroll zoom (drifts north on pitched maps).
    // Use jumpTo so rapid events accumulate instantly without interrupting each other.
    this.map.scrollZoom.disable();
    this.onWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (!this.map) return;
      let delta: number;
      if (e.deltaMode === 0)      delta = -e.deltaY * 0.008;  // trackpad pixels
      else if (e.deltaMode === 1) delta = -e.deltaY * 0.4;    // mouse wheel lines
      else                        delta = -e.deltaY * 1.5;    // pages
      const next = Math.min(18, Math.max(13, this.map.getZoom() + delta));
      this.map.jumpTo({ zoom: next });
    };
    container.addEventListener("wheel", this.onWheel, { passive: false });

    this.map.on("load", () => {
      if (!this.map) return;
      this.map.setMinZoom(13);
      this.map.setMaxZoom(18);
    });

    // style.load fires on every style (re)load — re-add custom layers each time,
    // restoring the last known followers so dots don't disappear.
    this.map.on("style.load", () => {
      if (!this.map) return;
      setup3D(this.map, this.buildingColors);
      setupFollowerLayer(this.map, this.lastFollowers);
      // Apply any followers queued before style was ready
      if (this.pendingFollowers) {
        const pending = this.pendingFollowers;
        this.pendingFollowers = null;
        this.setFollowers(pending);
      }
    });
  }

  updateState(hourOfDay: number): void {
    if (!this.map) return;
    const timeOfDay = hourOfDay / 24;
    const isNight = timeOfDay < 0.25 || timeOfDay > 0.75;
    const mode = isNight ? "dark" : "light";

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
        });
      } else {
        this.map.setFog({
          color: "#e2e8f0",
          "horizon-blend": 0.18,
          range: [0.9, 8.0],
          "space-color": "#0b1120",
          "star-intensity": 0.0,
        });
      }
    }

    // Animate follower dots from their previous positions to the new ones.
    if (this.animToFollowers.length > 0 && this.animStartTime >= 0) {
      const raw = (performance.now() - this.animStartTime) / TRAVEL_DURATION_MS;
      const t = easeInOut(Math.min(raw, 1));
      const interpolated = interpolateFollowers(this.animFromFollowers, this.animToFollowers, t);
      const source = this.map.getSource("followers");
      if (source && "setData" in source) {
        (source as mapboxgl.GeoJSONSource).setData(buildFollowerGeoJSON(interpolated));
      }
    }
  }

  setFollowers(followers: MapFollower[]): void {
    if (followers === this.lastFollowers) return;

    // Guard: if map style hasn't loaded yet, queue for later
    if (!this.map || !this.map.isStyleLoaded()) {
      this.pendingFollowers = followers;
      return;
    }

    // Snapshot current display positions as the animation start
    this.animFromFollowers = this.animToFollowers.length > 0
      ? interpolateFollowers(
          this.animFromFollowers,
          this.animToFollowers,
          this.animStartTime < 0 ? 1 : Math.min((performance.now() - this.animStartTime) / TRAVEL_DURATION_MS, 1),
        )
      : followers;
    this.animToFollowers = followers;
    this.animStartTime = performance.now();
    this.lastFollowers = followers;
  }

  startRenderLoop(getHourOfDay: () => number): void {
    if (this.animationId !== 0) return; // prevent double render loops
    const tick = () => {
      this.animationId = requestAnimationFrame(tick);
      this.updateState(getHourOfDay());
    };
    tick();
  }

  dispose(): void {
    cancelAnimationFrame(this.animationId);
    this.animationId = 0;

    // Remove window-level listeners
    if (this.onMouseMove) window.removeEventListener("mousemove", this.onMouseMove);
    if (this.boundMouseUp) window.removeEventListener("mouseup", this.boundMouseUp);

    // Remove container-level listeners
    if (this.onWheel) {
      this.container.removeEventListener("wheel", this.onWheel);
    }
    if (this.onContainerMouseDown) {
      this.container.removeEventListener("mousedown", this.onContainerMouseDown);
    }

    // Remove all map event listeners
    if (this.map) {
      for (const { event, handler, layer } of this.mapHandlers) {
        if (layer) {
          this.map.off(event, layer, handler as () => void);
        } else {
          this.map.off(event, handler as () => void);
        }
      }
    }
    this.mapHandlers = [];

    // Cleanup popup and map
    this.followerPopup?.remove();
    this.followerPopup = null;
    if (this.map) {
      this.map.remove();
      this.map = null;
    }

    // Nullify handler references
    this.onMouseMove = null;
    this.onMouseUp = null;
    this.boundMouseUp = null;
    this.onWheel = null;
    this.onContainerMouseDown = null;
  }
}
