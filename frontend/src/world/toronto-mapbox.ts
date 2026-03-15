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

const MAPBOX_STYLE_LANDING = "mapbox://styles/danielp1231231/cmmr4yn9s007f01qs9f9h0wjq";
const MAPBOX_STYLE_SIMULATION = "mapbox://styles/mapbox/standard";

export interface TorontoMapboxOptions {
  container: HTMLElement;
  onResize?: () => void;
  /** Colors for 3D buildings by height (low to high). 2–5 hex colors recommended. */
  buildingColors?: BuildingColorPalette;
  /** True when landing page is shown first: start at Earth view for zoom-in. */
  landingFirstView?: boolean;
}

// Toronto downtown
const TORONTO_CENTER: [number, number] = [-79.38175019453755, 43.64369424043282];

const BASE_VIEWPORT_BOUNDS = {
  west: -79.42,
  east: -79.34,
  south: 43.62,
  north: 43.69,
} as const;

const LEFT_VIEWPORT_EXPANSION_RATIO = 0.2;
const BASE_VIEWPORT_WIDTH = BASE_VIEWPORT_BOUNDS.east - BASE_VIEWPORT_BOUNDS.west;
const VIEWPORT_BOUNDS = {
  west: BASE_VIEWPORT_BOUNDS.west - BASE_VIEWPORT_WIDTH * LEFT_VIEWPORT_EXPANSION_RATIO,
  east: BASE_VIEWPORT_BOUNDS.east,
  south: BASE_VIEWPORT_BOUNDS.south,
  north: BASE_VIEWPORT_BOUNDS.north,
} as const;

// Landing route: 88 Queens Quay West → CN Tower → return loop (different path)
// Coordinates: 88 Queens Quay W ≈ [-79.3787, 43.64085], CN Tower ≈ [-79.38705, 43.64257]
export interface LandingRouteKeyframe {
  lng: number;
  lat: number;
  bearing: number; // degrees, 0 = north, 90 = east
}
const LANDING_ROUTE: LandingRouteKeyframe[] = [
  { lng: -79.3787, lat: 43.64085, bearing: 285 },   // 88 Queens Quay W, looking west
  { lng: -79.381, lat: 43.641, bearing: 290 },
  { lng: -79.3835, lat: 43.6414, bearing: 295 },
  { lng: -79.386, lat: 43.6422, bearing: 300 },
  { lng: -79.38705, lat: 43.64257, bearing: 0 },    // CN Tower base, looking north
  // Return loop (east then south along different streets)
  { lng: -79.3862, lat: 43.6432, bearing: 65 },
  { lng: -79.384, lat: 43.6435, bearing: 90 },
  { lng: -79.381, lat: 43.643, bearing: 120 },
  { lng: -79.3795, lat: 43.6418, bearing: 160 },
  { lng: -79.3787, lat: 43.64085, bearing: 285 },   // back to start
];
const LANDING_ROUTE_DURATION_MS = 45000; // full loop
const LANDING_ZOOM = 17.4;
const LANDING_PITCH = 82;

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

// ── Zone data ──
// Zone polygons (residential neighborhoods + work districts) are fetched from
// the backend API at runtime, which is the single source of truth.
// See: GET /api/zones/residential, GET /api/zones/work-districts

import { ApiClient } from "../api/client";

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
const THOUGHT_BUBBLE_INTERVAL_MS = 2400;
const THOUGHT_BUBBLE_OFFSET: [number, number] = [0, 28];
const DEFAULT_THOUGHT_MESSAGES = [
  "Maybe I should reroute through King Street today.",
  "Crowds feel lighter around the waterfront right now.",
  "One more tick and this neighborhood might shift.",
  "I should check what everyone is posting downtown.",
  "Feels like a good hour to make a move.",
];

function pickDifferentRandomIndex(
  length: number,
  current: number | null,
): number {
  if (length <= 1) return 0;
  let next = Math.floor(Math.random() * length);
  while (current !== null && next === current) {
    next = Math.floor(Math.random() * length);
  }
  return next;
}

function followersWithPosition(
  followers: MapFollower[],
): Array<MapFollower & { position: LngLat }> {
  return followers.filter(
    (f): f is MapFollower & { position: LngLat } => f.position !== null,
  );
}

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

function buildThoughtBubbleHTML(
  followerName: string,
  thought: string,
): string {
  return `
    <div class="thought-bubble">
      <p class="thought-bubble-text">${escapeHtml(thought)}</p>
      <span class="thought-bubble-author">${escapeHtml(followerName)}</span>
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
  const data = buildFollowerGeoJSON(followers);
  const source = map.getSource("followers");
  if (!source) {
    map.addSource("followers", {
      type: "geojson",
      data,
    });
  } else if ("setData" in source) {
    (source as mapboxgl.GeoJSONSource).setData(data);
  }

  if (!map.getLayer("followers-layer")) {
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
}

function setup3D(
  map: mapboxgl.Map,
  buildingColors: BuildingColorPalette = DEFAULT_BUILDING_PALETTE,
  residentialGeoJSON?: GeoJSON.FeatureCollection,
  workGeoJSON?: GeoJSON.FeatureCollection,
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
  if (residentialGeoJSON && !map.getSource("toronto-residential")) {
    map.addSource("toronto-residential", {
      type: "geojson",
      data: residentialGeoJSON,
    });
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
  }

  // ── Work Districts (bold overlay) ──
  if (workGeoJSON && !map.getSource("toronto-work")) {
    map.addSource("toronto-work", {
      type: "geojson",
      data: workGeoJSON,
    });
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
  }

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
  private currentStyle: "light" | "dark" | null = null;
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
  private thoughtBubblePopup: mapboxgl.Popup | null = null;
  private thoughtBubbleModeEnabled: boolean = false;
  private thoughtBubbleTimerId: number | null = null;
  private thoughtBubbleFollowerId: number | null = null;
  private thoughtBubbleMessagePool: string[] = [
    ...DEFAULT_THOUGHT_MESSAGES,
  ];
  private pendingFollowers: MapFollower[] | null = null;
  // Store map event handlers for cleanup
  private mapHandlers: { event: string; handler: (...args: unknown[]) => void; layer?: string }[] = [];
  // Landing page: street-level fly-through 88 Queens Quay → CN Tower → back
  private landingStartTime: number = -1;
  private isLandingRoute: boolean = false;
  // Zone GeoJSON fetched from backend (single source of truth)
  private residentialGeoJSON: GeoJSON.FeatureCollection | null = null;
  private workGeoJSON: GeoJSON.FeatureCollection | null = null;
  private styleLoaded: boolean = false;
  /** True after the first Earth→Toronto zoom-in has run (only on first launch). */
  private initialZoomDone: boolean = false;
  /** True when switching from landing style to simulation style (setStyle in progress). */
  private switchingToSimulationStyle: boolean = false;

  constructor(options: TorontoMapboxOptions) {
    const { container, buildingColors, landingFirstView } = options;
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

    const startAtEarth = landingFirstView === true;
    const torontoBounds: [[number, number], [number, number]] = [
      [-79.42, 43.62], // SW: Bathurst & lakeshore
      [-79.34, 43.69], // NE: just east of DVP & Bloor
    ];
    this.map = new mapboxgl.Map({
      container,
      accessToken: token,
      style: startAtEarth ? MAPBOX_STYLE_LANDING : MAPBOX_STYLE_SIMULATION,
      center: TORONTO_CENTER,
      zoom: startAtEarth ? 2 : 15.2,
      minZoom: 2,
      maxZoom: 18,
      pitch: startAtEarth ? 0 : 40,
      maxPitch: 60,
      bearing: startAtEarth ? 0 : -20,
      antialias: true,
      // Downtown Toronto core: Bathurst → DVP, waterfront → Bloor,
      // with 50% extra viewport room on the west side.
      maxBounds: [
        [VIEWPORT_BOUNDS.west, VIEWPORT_BOUNDS.south],
        [VIEWPORT_BOUNDS.east, VIEWPORT_BOUNDS.north],
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

    this.thoughtBubblePopup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
      className: "thought-bubble-popup",
      anchor: "bottom",
      offset: THOUGHT_BUBBLE_OFFSET,
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

    const clampCenter = () => {
      if (!this.map) return;
      const c = this.map.getCenter();
      const lng = Math.max(VIEWPORT_BOUNDS.west, Math.min(VIEWPORT_BOUNDS.east, c.lng));
      const lat = Math.max(VIEWPORT_BOUNDS.south, Math.min(VIEWPORT_BOUNDS.north, c.lat));
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
      this.styleLoaded = true;
      setup3D(this.map, this.buildingColors, this.residentialGeoJSON ?? undefined, this.workGeoJSON ?? undefined);
      setupFollowerLayer(this.map, this.lastFollowers);
      // Style reload resets atmosphere state; force next frame to re-apply fog.
      this.currentStyle = null;
      // Apply any followers queued before style was ready
      if (this.pendingFollowers) {
        const pending = this.pendingFollowers;
        this.pendingFollowers = null;
        this.setFollowers(pending);
      }
      if (this.switchingToSimulationStyle) {
        this.switchingToSimulationStyle = false;
        this.map.setMaxBounds([
          [-79.42, 43.62],
          [-79.34, 43.69],
        ]);
        this.map.easeTo({
          center: TORONTO_CENTER,
          zoom: 15.2,
          pitch: 40,
          bearing: -20,
          duration: 1600,
        });
      }
    });

    // Fetch unified zone GeoJSON from backend (single source of truth).
    // Split into residential/work by type property for distinct styling.
    const zoneApi = new ApiClient(
      (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) || "http://localhost:8000"
    );
    zoneApi.getZones().then((allZones) => {
      const residential: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: allZones.features.filter((f) => f.properties?.type === "residential"),
      };
      const work: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: allZones.features.filter((f) => f.properties?.type === "work"),
      };
      this.residentialGeoJSON = residential;
      this.workGeoJSON = work;
      // If style already loaded before zones arrived, apply now
      if (this.styleLoaded && this.map) {
        setup3D(this.map, this.buildingColors, residential, work);
      }
    }).catch((err) => {
      console.warn("Failed to fetch zone data from backend:", err);
    });
  }

  setThoughtBubbleMessages(messages: string[]): void {
    const normalized = messages
      .map((message) => message.trim())
      .filter((message) => message.length > 0);
    this.thoughtBubbleMessagePool =
      normalized.length > 0
        ? normalized
        : [...DEFAULT_THOUGHT_MESSAGES];
  }

  setThoughtBubbleMode(enabled: boolean): void {
    if (this.thoughtBubbleModeEnabled === enabled) return;
    this.thoughtBubbleModeEnabled = enabled;

    if (!enabled) {
      this.stopThoughtBubbleLoop();
      return;
    }

    this.startThoughtBubbleLoop();
  }

  private startThoughtBubbleLoop(): void {
    if (!this.map) return;
    if (this.thoughtBubbleTimerId !== null) return;
    this.showRandomThoughtBubble();
    this.thoughtBubbleTimerId = window.setInterval(() => {
      this.showRandomThoughtBubble();
    }, THOUGHT_BUBBLE_INTERVAL_MS);
  }

  private stopThoughtBubbleLoop(): void {
    if (this.thoughtBubbleTimerId !== null) {
      window.clearInterval(this.thoughtBubbleTimerId);
      this.thoughtBubbleTimerId = null;
    }
    this.thoughtBubbleFollowerId = null;
    this.thoughtBubblePopup?.remove();
  }

  private showRandomThoughtBubble(): void {
    if (!this.map || !this.thoughtBubblePopup) return;
    const candidates = followersWithPosition(this.lastFollowers);
    if (candidates.length === 0) {
      this.thoughtBubblePopup.remove();
      this.thoughtBubbleFollowerId = null;
      return;
    }

    const currentFollowerIndex = candidates.findIndex(
      (follower) =>
        follower.follower_id === this.thoughtBubbleFollowerId,
    );
    const nextFollowerIndex = pickDifferentRandomIndex(
      candidates.length,
      currentFollowerIndex >= 0 ? currentFollowerIndex : null,
    );
    const follower = candidates[nextFollowerIndex];
    const nextThought =
      this.thoughtBubbleMessagePool[
        Math.floor(
          Math.random() * this.thoughtBubbleMessagePool.length,
        )
      ] ?? DEFAULT_THOUGHT_MESSAGES[0];

    this.thoughtBubbleFollowerId = follower.follower_id;
    this.thoughtBubblePopup
      .setLngLat(follower.position)
      .setHTML(buildThoughtBubbleHTML(follower.name, nextThought))
      .addTo(this.map);
  }

  private syncThoughtBubblePosition(
    renderedFollowers: MapFollower[],
  ): void {
    if (
      !this.thoughtBubbleModeEnabled ||
      !this.thoughtBubblePopup?.isOpen() ||
      this.thoughtBubbleFollowerId === null
    ) {
      return;
    }

    const activeFollower = renderedFollowers.find(
      (follower) =>
        follower.follower_id === this.thoughtBubbleFollowerId,
    );

    if (!activeFollower?.position) {
      this.showRandomThoughtBubble();
      return;
    }

    this.thoughtBubblePopup.setLngLat(activeFollower.position);
  }

  updateState(hourOfDay: number): void {
    if (!this.map) return;

    // Landing route: drive camera along street-level path when welcome screen is shown
    if (this.isLandingRoute && this.landingStartTime >= 0) {
      const elapsed = performance.now() - this.landingStartTime;
      const loopTime = elapsed % LANDING_ROUTE_DURATION_MS;
      const t = loopTime / LANDING_ROUTE_DURATION_MS;
      const n = LANDING_ROUTE.length - 1;
      const seg = Math.min(Math.floor(t * n), n - 1);
      const segT = (t * n) - seg;
      const a = LANDING_ROUTE[seg];
      const b = LANDING_ROUTE[seg + 1];
      const lng = a.lng + (b.lng - a.lng) * segT;
      const lat = a.lat + (b.lat - a.lat) * segT;
      let bearing = a.bearing + (b.bearing - a.bearing) * segT;
      if (Math.abs(b.bearing - a.bearing) > 180) {
        if (b.bearing > a.bearing) bearing = a.bearing - (360 - b.bearing + a.bearing) * segT;
        else bearing = a.bearing + (360 - a.bearing + b.bearing) * segT;
      }
      bearing = ((bearing % 360) + 360) % 360;
      this.map.jumpTo({
        center: [lng, lat],
        zoom: LANDING_ZOOM,
        pitch: LANDING_PITCH,
        bearing,
      });
      return;
    }

    const timeOfDay = hourOfDay / 24;
    const isNight = timeOfDay < 0.25 || timeOfDay > 0.75;
    const mode = isNight ? "dark" : "light";

    // Atmospheric fog for day/night mood.
    // Guard style-dependent map operations until style JSON is fully loaded.
    if (this.map.isStyleLoaded() && this.currentStyle !== mode) {
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

    let renderedFollowers = this.lastFollowers;

    // Animate follower dots from their previous positions to the new ones.
    if (this.animToFollowers.length > 0 && this.animStartTime >= 0) {
      const raw = (performance.now() - this.animStartTime) / TRAVEL_DURATION_MS;
      const t = easeInOut(Math.min(raw, 1));
      const interpolated = interpolateFollowers(this.animFromFollowers, this.animToFollowers, t);
      renderedFollowers = interpolated;
      const source = this.map.getSource("followers");
      if (source && "setData" in source) {
        (source as mapboxgl.GeoJSONSource).setData(buildFollowerGeoJSON(renderedFollowers));
      }
    }

    this.syncThoughtBubblePosition(renderedFollowers);
  }

  setFollowers(followers: MapFollower[]): void {
    if (followers === this.lastFollowers) return;

    // Guard: if map style hasn't loaded yet, queue for later
    if (!this.map || !this.map.isStyleLoaded()) {
      this.pendingFollowers = followers;
      return;
    }

    // Ensure source/layer exist even if style.load completed before our first follower sync.
    setupFollowerLayer(this.map, followers);

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

    // Apply immediately so dots appear on first load without waiting for a later tick/update.
    const source = this.map.getSource("followers");
    if (source && "setData" in source) {
      (source as mapboxgl.GeoJSONSource).setData(buildFollowerGeoJSON(followers));
    }

    if (!this.thoughtBubbleModeEnabled) return;

    const activeFollowerStillVisible = followers.some(
      (follower) =>
        follower.follower_id === this.thoughtBubbleFollowerId &&
        follower.position !== null,
    );
    if (!activeFollowerStillVisible) {
      this.showRandomThoughtBubble();
    }
  }

  /** Start street-level fly-through from 88 Queens Quay → CN Tower → back (landing page). */
  startLandingRoute(): void {
    this.isLandingRoute = true;
    if (!this.map) return;

    const k = LANDING_ROUTE[0];
    const dest = { center: [k.lng, k.lat] as [number, number], zoom: LANDING_ZOOM, pitch: LANDING_PITCH, bearing: k.bearing };

    if (!this.initialZoomDone) {
      this.initialZoomDone = true;
      const zoomInFromEarth = () => {
        this.map!.flyTo({
          ...dest,
          duration: 4200,
          essential: true,
        });
        this.map!.once("moveend", () => {
          this.landingStartTime = performance.now();
        });
      };
      if (this.map.getZoom() > 3) {
        this.map.jumpTo({ center: TORONTO_CENTER, zoom: 2, pitch: 0, bearing: 0 });
        this.map.once("moveend", zoomInFromEarth);
      } else {
        zoomInFromEarth();
      }
      return;
    }

    this.landingStartTime = performance.now();
    this.map.jumpTo(dest);
  }

  /** Stop landing route: switch to simulation style, then ease to default view. */
  stopLandingRoute(): void {
    this.isLandingRoute = false;
    this.landingStartTime = -1;
    if (this.map) {
      this.switchingToSimulationStyle = true;
      this.map.setStyle(MAPBOX_STYLE_SIMULATION);
    }
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
    this.stopThoughtBubbleLoop();
    this.followerPopup?.remove();
    this.followerPopup = null;
    this.thoughtBubblePopup = null;
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
