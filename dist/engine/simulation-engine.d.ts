import type { CityState } from "../types/city-state.js";
import type { Event, EventApplicationResult } from "../events/event.js";
/**
 * Callbacks for extending the engine (e.g. logging, AI agents, UI).
 * Hook into step and event application without modifying core logic.
 */
export interface SimulationEngineHooks {
    /** Called after each day step with previous and next state. */
    onStep?(previous: CityState, next: CityState, day: number): void;
    /** Called after an event is applied. */
    onEventApplied?(result: EventApplicationResult, day: number): void;
}
/**
 * Simulation engine: advances time in discrete days and applies events.
 * Designed so that an AI agent can:
 * - Read current state
 * - Call applyEvent() with generated or chosen events
 * - Optionally react in hooks (onStep, onEventApplied)
 */
export declare class SimulationEngine {
    private _state;
    private _day;
    private _hooks;
    constructor(initialState?: CityState, hooks?: SimulationEngineHooks);
    /** Current city state (read-only snapshot). */
    get state(): Readonly<CityState>;
    /** Current simulation day (0 = start). */
    get day(): number;
    /**
     * Advance the simulation by one day.
     * Applies internal update rules only; events are applied via applyEvent().
     */
    step(): CityState;
    /**
     * Apply an event to the current city state immediately (same day).
     * Use this for policy changes, disasters, or any one-off modifier.
     */
    applyEvent(event: Event): EventApplicationResult;
    /**
     * Run the simulation for a number of days without applying any events.
     * Useful for testing or for an AI that only intervenes at certain days.
     */
    runDays(days: number): CityState;
}
//# sourceMappingURL=simulation-engine.d.ts.map