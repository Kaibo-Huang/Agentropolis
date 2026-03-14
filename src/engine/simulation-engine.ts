import type { CityState } from "../types/city-state.js";
import { DEFAULT_CITY_STATE } from "../types/city-state.js";
import type { Event, EventApplicationResult } from "../events/event.js";
import { applyEventToState } from "../events/event.js";
import { computeDailyUpdate } from "./rules.js";

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
export class SimulationEngine {
  private _state: CityState;
  private _day: number;
  private _hooks: SimulationEngineHooks;

  constructor(
    initialState: CityState = { ...DEFAULT_CITY_STATE },
    hooks: SimulationEngineHooks = {}
  ) {
    this._state = { ...initialState };
    this._day = 0;
    this._hooks = hooks;
  }

  /** Current city state (read-only snapshot). */
  get state(): Readonly<CityState> {
    return this._state;
  }

  /** Current simulation day (0 = start). */
  get day(): number {
    return this._day;
  }

  /**
   * Advance the simulation by one day.
   * Applies internal update rules only; events are applied via applyEvent().
   */
  step(): CityState {
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
  applyEvent(event: Event): EventApplicationResult {
    const result = applyEventToState(this._state, event);
    this._state = result.newState;
    this._hooks.onEventApplied?.(result, this._day);
    return result;
  }

  /**
   * Run the simulation for a number of days without applying any events.
   * Useful for testing or for an AI that only intervenes at certain days.
   */
  runDays(days: number): CityState {
    for (let i = 0; i < days; i++) {
      this.step();
    }
    return this._state;
  }
}
