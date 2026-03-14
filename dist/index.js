/**
 * Society simulation: city state, events, discrete-day engine, and AI citizens.
 * Structured for easy extension with AI agents (hooks, Event interface, read-only state).
 */
export { clampCityState, DEFAULT_CITY_STATE, } from "./types/city-state.js";
export { applyEventToState } from "./events/event.js";
export { SAMPLE_EVENTS } from "./events/events-catalog.js";
export { SimulationEngine } from "./engine/simulation-engine.js";
export { computeDailyUpdate } from "./engine/rules.js";
export { clampTraits } from "./citizens/types.js";
export { Citizen } from "./citizens/citizen.js";
export { applyAction } from "./citizens/actions.js";
export { decideAction } from "./citizens/decision.js";
export { evaluateCityStateForCitizen } from "./citizens/evaluate.js";
export { SocialNetwork } from "./citizens/social-network.js";
export { createSampleCitizens } from "./citizens/sample-citizens.js";
export { CitizenSimulationEngine } from "./engine/citizen-simulation-engine.js";
//# sourceMappingURL=index.js.map