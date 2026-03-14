import { DEFAULT_CITY_STATE } from "../types/city-state.js";
import { applyEventToState } from "../events/event.js";
import { computeDailyUpdate } from "./rules.js";
/**
 * Simulation engine: advances time in discrete days and applies events.
 * Designed so that an AI agent can:
 * - Read current state
 * - Call applyEvent() with generated or chosen events
 * - Optionally react in hooks (onStep, onEventApplied)
 */
export class SimulationEngine {
    constructor(initialState = { ...DEFAULT_CITY_STATE }, hooks = {}) {
        this._state = { ...initialState };
        this._day = 0;
        this._hooks = hooks;
    }
    /** Current city state (read-only snapshot). */
    get state() {
        return this._state;
    }
    /** Current simulation day (0 = start). */
    get day() {
        return this._day;
    }
    /**
     * Advance the simulation by one day.
     * Applies internal update rules only; events are applied via applyEvent().
     */
    step() {
        const previous = this._state;
        this._state = computeDailyUpdate(previous);
        this._day += 1;
        this._hooks.onStep?.(previous, this._state, this._day);
        return this._state;
    }
    /**
     * Apply an event to the current city state immediately (same day).
     * Use this for policy changes, disasters, or any one-off modifier.
     */
    applyEvent(event) {
        const result = applyEventToState(this._state, event);
        this._state = result.newState;
        this._hooks.onEventApplied?.(result, this._day);
        return result;
    }
    /**
     * Run the simulation for a number of days without applying any events.
     * Useful for testing or for an AI that only intervenes at certain days.
     */
    runDays(days) {
        for (let i = 0; i < days; i++) {
            this.step();
        }
        return this._state;
    }
}
//# sourceMappingURL=simulation-engine.js.map