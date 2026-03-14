import type { CityState } from "../types/city-state.js";
/**
 * Deltas to apply to city state. Only include keys you want to change.
 * Positive/negative values are added to the current metric (then clamped).
 */
export type CityStateDelta = Partial<{
    population: number;
    economy: number;
    publicHealth: number;
    housingCost: number;
    pollution: number;
    publicOpinion: number;
}>;
/**
 * An event that can be applied to the simulation (policy change, disaster, etc.).
 * Extend this interface for richer event types (e.g. duration, conditions).
 */
export interface Event {
    /** Unique identifier for this event instance or type. */
    id: string;
    /** Human-readable name. */
    name: string;
    /** Optional description for UI or logs. */
    description?: string;
    /** Deltas to apply to the current city state when the event is applied. */
    delta: CityStateDelta;
}
/**
 * Result of applying an event: the new state and optional message.
 * Useful for logging and UI feedback when integrating AI agents.
 */
export interface EventApplicationResult {
    previousState: CityState;
    newState: CityState;
    event: Event;
    message?: string;
}
/**
 * Apply an event's delta to the current city state (deltas are added to current values).
 * Returns the new state (clamped) and the application result for logging.
 */
export declare function applyEventToState(state: CityState, event: Event): EventApplicationResult;
//# sourceMappingURL=event.d.ts.map