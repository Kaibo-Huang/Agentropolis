import { clampCityState } from "../types/city-state.js";
/**
 * Apply an event's delta to the current city state (deltas are added to current values).
 * Returns the new state (clamped) and the application result for logging.
 */
export function applyEventToState(state, event) {
    const previousState = { ...state };
    const d = event.delta;
    const newState = clampCityState({
        population: state.population + (d.population ?? 0),
        economy: state.economy + (d.economy ?? 0),
        publicHealth: state.publicHealth + (d.publicHealth ?? 0),
        housingCost: state.housingCost + (d.housingCost ?? 0),
        pollution: state.pollution + (d.pollution ?? 0),
        publicOpinion: state.publicOpinion + (d.publicOpinion ?? 0),
    });
    return {
        previousState,
        newState,
        event,
        message: event.description ?? `Applied: ${event.name}`,
    };
}
//# sourceMappingURL=event.js.map