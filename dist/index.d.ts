/**
 * Society simulation: city state, events, and discrete-day engine.
 * Structured for easy extension with AI agents (hooks, Event interface, read-only state).
 */
export type { CityState } from "./types/city-state.js";
export { clampCityState, DEFAULT_CITY_STATE, } from "./types/city-state.js";
export type { Event, CityStateDelta, EventApplicationResult } from "./events/event.js";
export { applyEventToState } from "./events/event.js";
export { SAMPLE_EVENTS } from "./events/events-catalog.js";
export type { SimulationEngineHooks } from "./engine/simulation-engine.js";
export { SimulationEngine } from "./engine/simulation-engine.js";
export { computeDailyUpdate } from "./engine/rules.js";
//# sourceMappingURL=index.d.ts.map