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
/**
 * Clamp all city state metrics to their valid ranges.
 * Population is kept >= 0; other metrics are clamped to [0, 100].
 */
export declare function clampCityState(state: CityState): CityState;
/** Default initial city state. */
export declare const DEFAULT_CITY_STATE: CityState;
//# sourceMappingURL=city-state.d.ts.map