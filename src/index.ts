/**
 * Society simulation: city state, events, discrete-day engine, and AI citizens.
 * Structured for easy extension with AI agents (hooks, Event interface, read-only state).
 */

// City state
export type { CityState } from "./types/city-state.js";
export {
  clampCityState,
  DEFAULT_CITY_STATE,
} from "./types/city-state.js";

// Events
export type { Event, CityStateDelta, EventApplicationResult } from "./events/event.js";
export { applyEventToState } from "./events/event.js";
export { SAMPLE_EVENTS } from "./events/events-catalog.js";

// Engine
export type { SimulationEngineHooks } from "./engine/simulation-engine.js";
export { SimulationEngine } from "./engine/simulation-engine.js";
export { computeDailyUpdate } from "./engine/rules.js";

// Citizens (AI agents)
export type { PersonalityTraits, OccupationType } from "./citizens/types.js";
export { clampTraits } from "./citizens/types.js";
export { Citizen } from "./citizens/citizen.js";
export type { CitizenAction } from "./citizens/actions.js";
export { applyAction } from "./citizens/actions.js";
export { decideAction } from "./citizens/decision.js";
export { evaluateCityStateForCitizen } from "./citizens/evaluate.js";
export { SocialNetwork } from "./citizens/social-network.js";
export { createSampleCitizens } from "./citizens/sample-citizens.js";

// Citizen-aware simulation engine
export type { CitizenSimulationEngineHooks } from "./engine/citizen-simulation-engine.js";
export { CitizenSimulationEngine } from "./engine/citizen-simulation-engine.js";
