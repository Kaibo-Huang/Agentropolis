/**
 * Society simulation: city state, events, and discrete-day engine.
 * Structured for easy extension with AI agents (hooks, Event interface, read-only state).
 */
export { clampCityState, DEFAULT_CITY_STATE, } from "./types/city-state.js";
export { applyEventToState } from "./events/event.js";
export { SAMPLE_EVENTS } from "./events/events-catalog.js";
export { SimulationEngine } from "./engine/simulation-engine.js";
export { computeDailyUpdate } from "./engine/rules.js";
//# sourceMappingURL=index.js.map