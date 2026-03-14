/** Clamp a value to [min, max]. */
function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}
const MIN = 0;
const MAX = 100;
/**
 * Clamp all city state metrics to their valid ranges.
 * Population is kept >= 0; other metrics are clamped to [0, 100].
 */
export function clampCityState(state) {
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
export const DEFAULT_CITY_STATE = {
    population: 100000,
    economy: 50,
    publicHealth: 70,
    housingCost: 40,
    pollution: 30,
    publicOpinion: 50,
};
//# sourceMappingURL=city-state.js.map