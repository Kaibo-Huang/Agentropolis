import type { CityStateDelta } from "../events/event.js";
import type { Citizen } from "./citizen.js";
import type { OccupationType } from "./types.js";

/**
 * Actions a citizen can take each step. Each action has effects on the citizen
 * and a small contribution to city-wide metrics.
 */
export type CitizenAction =
  | { type: "support_policy" }
  | { type: "oppose_policy" }
  | { type: "protest" }
  | { type: "move_neighborhood"; neighborhood: string }
  | { type: "change_job"; occupation: OccupationType; income: number }
  | { type: "share_opinion" };

/** Strength of one citizen's action on city metrics (kept small). */
const CITIZEN_IMPACT = 0.01;

/**
 * Apply the action to the citizen (mutates citizen) and return the city delta.
 */
export function applyAction(
  citizen: Citizen,
  action: CitizenAction
): CityStateDelta {
  switch (action.type) {
    case "support_policy": {
      citizen.addHappiness(2);
      return {
        publicOpinion: CITIZEN_IMPACT * 1,
      };
    }
    case "oppose_policy": {
      citizen.addHappiness(-1);
      return {
        publicOpinion: CITIZEN_IMPACT * -1,
      };
    }
    case "protest": {
      citizen.addHappiness(-3); // Stressful
      return {
        publicOpinion: CITIZEN_IMPACT * -3,
      };
    }
    case "move_neighborhood": {
      citizen.setNeighborhood(action.neighborhood);
      citizen.addHappiness(1);
      return {
        publicOpinion: CITIZEN_IMPACT * 0.5,
      };
    }
    case "change_job": {
      citizen.setOccupation(action.occupation);
      citizen.setIncome(action.income);
      citizen.addHappiness(2);
      return {
        economy: CITIZEN_IMPACT * 2,
        publicOpinion: CITIZEN_IMPACT * 0.5,
      };
    }
    case "share_opinion": {
      citizen.addHappiness(1);
      return {
        publicOpinion: CITIZEN_IMPACT * (citizen.opinion > 50 ? 0.5 : -0.5),
      };
    }
    default:
      return {};
  }
}
