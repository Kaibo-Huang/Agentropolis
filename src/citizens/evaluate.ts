import type { CityState } from "../types/city-state.js";
import type { Citizen } from "./citizen.js";

/**
 * Update a citizen's happiness based on current city conditions.
 * Called each step so citizens "evaluate" the city. Personality moderates
 * how much they care about each factor (e.g. risk-tolerant may care less about economy).
 */
const DAILY_HAPPINESS_DELTA_SCALE = 0.05;

export function evaluateCityStateForCitizen(
  citizen: Citizen,
  cityState: CityState
): void {
  const { economy, publicHealth, housingCost, pollution, publicOpinion } =
    cityState;

  // Base satisfaction from city metrics (roughly -1 to +1 per factor)
  const economyScore = (economy - 50) / 50;
  const healthScore = (publicHealth - 50) / 50;
  const housingScore = (50 - housingCost) / 50; // High cost = bad
  const pollutionScore = (50 - pollution) / 50; // High pollution = bad
  const opinionScore = (publicOpinion - 50) / 50;

  // Trust in government amplifies reaction to public opinion (government performance)
  const trustWeight = 0.3 + (citizen.personality.trustInGovernment / 100) * 0.4;
  const delta =
    economyScore * 0.2 +
    healthScore * 0.25 +
    housingScore * 0.2 +
    pollutionScore * 0.15 +
    opinionScore * trustWeight;

  const happinessDelta = delta * DAILY_HAPPINESS_DELTA_SCALE * 10; // Small daily nudge
  citizen.addHappiness(happinessDelta);
}
