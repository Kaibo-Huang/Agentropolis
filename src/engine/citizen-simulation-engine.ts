import type { CityState } from "../types/city-state.js";
import { clampCityState, DEFAULT_CITY_STATE } from "../types/city-state.js";
import type { Event, EventApplicationResult } from "../events/event.js";
import { applyEventToState } from "../events/event.js";
import type { CityStateDelta } from "../events/event.js";
import { computeDailyUpdate } from "./rules.js";
import type { Citizen } from "../citizens/citizen.js";
import { decideAction } from "../citizens/decision.js";
import type { CitizenAction } from "../citizens/actions.js";
import { applyAction } from "../citizens/actions.js";
import { evaluateCityStateForCitizen } from "../citizens/evaluate.js";
import { SocialNetwork } from "../citizens/social-network.js";

const RECENT_EVENTS_MAX = 10;
const OPINION_SPREAD_STRENGTH = 0.08;

/**
 * Hooks for the citizen-aware simulation (includes base engine hooks plus citizen actions).
 */
export interface CitizenSimulationEngineHooks {
  /** Called after each day step with previous and next city state. */
  onStep?(previous: CityState, next: CityState, day: number): void;
  /** Called after an event is applied. */
  onEventApplied?(result: EventApplicationResult, day: number): void;
  /** Called when a citizen takes an action (citizen id, action, city delta from that action). */
  onCitizenAction?(
    citizenId: string,
    action: CitizenAction,
    cityDelta: CityStateDelta,
    day: number
  ): void;
}

/**
 * Merge multiple city-state deltas into one, then apply to state and clamp.
 */
function applyDeltasToState(
  state: CityState,
  deltas: CityStateDelta[]
): CityState {
  const combined: CityStateDelta = {};
  for (const d of deltas) {
    if (d.population !== undefined)
      combined.population = (combined.population ?? 0) + d.population;
    if (d.economy !== undefined)
      combined.economy = (combined.economy ?? 0) + d.economy;
    if (d.publicHealth !== undefined)
      combined.publicHealth = (combined.publicHealth ?? 0) + d.publicHealth;
    if (d.housingCost !== undefined)
      combined.housingCost = (combined.housingCost ?? 0) + d.housingCost;
    if (d.pollution !== undefined)
      combined.pollution = (combined.pollution ?? 0) + d.pollution;
    if (d.publicOpinion !== undefined)
      combined.publicOpinion = (combined.publicOpinion ?? 0) + d.publicOpinion;
  }
  return clampCityState({
    population: state.population + (combined.population ?? 0),
    economy: state.economy + (combined.economy ?? 0),
    publicHealth: state.publicHealth + (combined.publicHealth ?? 0),
    housingCost: state.housingCost + (combined.housingCost ?? 0),
    pollution: state.pollution + (combined.pollution ?? 0),
    publicOpinion: state.publicOpinion + (combined.publicOpinion ?? 0),
  });
}

/**
 * Simulation engine that includes AI citizens. Each step:
 * 1. Base daily update (economy, health, pollution, etc.)
 * 2. Citizens evaluate city state (happiness updated from conditions)
 * 3. Each citizen decides an action (support/oppose, protest, move, change job, share opinion)
 * 4. Actions are applied (citizen state + small city deltas)
 * 5. Social network spreads opinions between connected citizens
 */
export class CitizenSimulationEngine {
  private _state: CityState;
  private _day: number;
  private _citizens: Map<string, Citizen>;
  private _socialNetwork: SocialNetwork;
  private _recentEvents: Event[];
  private _hooks: CitizenSimulationEngineHooks;

  constructor(
    initialState: CityState = { ...DEFAULT_CITY_STATE },
    options: {
      citizens?: Citizen[];
      socialNetwork?: SocialNetwork;
      hooks?: CitizenSimulationEngineHooks;
    } = {}
  ) {
    this._state = { ...initialState };
    this._day = 0;
    this._citizens = new Map();
    for (const c of options.citizens ?? []) {
      this._citizens.set(c.id, c);
    }
    this._socialNetwork = options.socialNetwork ?? new SocialNetwork();
    this._recentEvents = [];
    this._hooks = options.hooks ?? {};
  }

  get state(): Readonly<CityState> {
    return this._state;
  }

  get day(): number {
    return this._day;
  }

  /** All citizens (read-only map). */
  get citizens(): ReadonlyMap<string, Citizen> {
    return this._citizens;
  }

  /** Social network for opinion spreading. */
  get socialNetwork(): SocialNetwork {
    return this._socialNetwork;
  }

  /** Add a citizen and ensure they are in the social graph. */
  addCitizen(citizen: Citizen): void {
    this._citizens.set(citizen.id, citizen);
    this._socialNetwork.addCitizen(citizen.id);
  }

  /**
   * Advance by one day: base update, citizen evaluation, decisions, actions, opinion spread.
   */
  step(): CityState {
    const previous = this._state;

    // 1. Base daily dynamics
    this._state = computeDailyUpdate(previous);

    // 2. Citizens evaluate city state (happiness from conditions)
    for (const citizen of this._citizens.values()) {
      evaluateCityStateForCitizen(citizen, this._state);
    }

    // 3. Each citizen decides and applies an action; collect city deltas
    const cityDeltas: CityStateDelta[] = [];
    for (const citizen of this._citizens.values()) {
      const action = decideAction(
        citizen,
        this._state,
        this._recentEvents
      );
      const delta = applyAction(citizen, action);
      cityDeltas.push(delta);
      this._hooks.onCitizenAction?.(citizen.id, action, delta, this._day + 1);
    }

    // 4. Apply combined citizen impact to city state
    this._state = applyDeltasToState(this._state, cityDeltas);

    // 5. Social network: opinions spread between neighbors
    this._socialNetwork.spreadOpinions(this._citizens, OPINION_SPREAD_STRENGTH);

    this._day += 1;
    this._hooks.onStep?.(previous, this._state, this._day);
    return this._state;
  }

  applyEvent(event: Event): EventApplicationResult {
    const result = applyEventToState(this._state, event);
    this._state = result.newState;
    this._recentEvents.push(event);
    if (this._recentEvents.length > RECENT_EVENTS_MAX) {
      this._recentEvents.shift();
    }
    this._hooks.onEventApplied?.(result, this._day);
    return result;
  }

  runDays(days: number): CityState {
    for (let i = 0; i < days; i++) {
      this.step();
    }
    return this._state;
  }
}
