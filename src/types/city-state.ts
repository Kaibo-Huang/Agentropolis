/**
 * City state metrics for the society simulation.
 * All numeric metrics use 0–100 scales unless otherwise noted, for consistent
 * event deltas and AI agent interfaces.
 */
export interface CityState {
  /** Total population (absolute count). */
  population: number;
  /** Economic health (0 = collapsed, 100 = thriving). */
  economy: number;
  /** Public health (0 = crisis, 100 = excellent). */
  publicHealth: number;
  /** Housing cost index (0 = very affordable, 100 = unaffordable). */
  housingCost: number;
  /** Pollution level (0 = clean, 100 = severe). */
  pollution: number;
  /** Public opinion / satisfaction (0 = hostile, 100 = very favorable). */
  publicOpinion: number;
}

/** Clamp a value to [min, max]. */
function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

const MIN = 0;
const MAX = 100;

/**
 * Clamp all city state metrics to their valid ranges.
 * Population is kept >= 0; other metrics are clamped to [0, 100].
 */
export function clampCityState(state: CityState): CityState {
  return {
    population: Math.max(0, state.population),
    economy: clamp(state.economy, MIN, MAX),
    publicHealth: clamp(state.publicHealth, MIN, MAX),
    housingCost: clamp(state.housingCost, MIN, MAX),
    pollution: clamp(state.pollution, MIN, MAX),
    publicOpinion: clamp(state.publicOpinion, MIN, MAX),
  };
}

/** Default initial city state. */
export const DEFAULT_CITY_STATE: CityState = {
  population: 100_000,
  economy: 50,
  publicHealth: 70,
  housingCost: 40,
  pollution: 30,
  publicOpinion: 50,
};
