import type { CityState } from "../types/city-state.js";
import { clampCityState } from "../types/city-state.js";

/**
 * Daily update rules: how the city state evolves each step without external events.
 * Kept in a separate module so they can be tuned or replaced (e.g. by AI or config).
 *
 * Simple rules used here:
 * - Economy influences housing cost (high economy -> higher cost).
 * - Pollution negatively affects public health.
 * - Health and economy influence public opinion.
 * - Population has mild pressure on housing and pollution.
 */

const INFLUENCE = 0.02; // How much one metric affects another per day (small = stable)
const POPULATION_PRESSURE = 1e-6; // Effect of population on housing/pollution per capita

/**
 * Compute the next city state after one day, using only internal dynamics.
 * Does not apply any events; the engine applies events separately.
 */
export function computeDailyUpdate(state: CityState): CityState {
  const {
    population,
    economy,
    publicHealth,
    housingCost,
    pollution,
    publicOpinion,
  } = state;

  // Economy pulls housing cost toward it (rich city -> expensive housing)
  const housingCostDrift = (economy - housingCost) * INFLUENCE;
  // Pollution hurts health
  const healthDrift = -pollution * INFLUENCE * 0.5;
  // Economy and health boost opinion; pollution and high housing cost hurt it
  const opinionDrift =
    (economy + publicHealth) * INFLUENCE * 0.3 -
    pollution * INFLUENCE * 0.2 -
    (housingCost > 60 ? INFLUENCE * 0.5 : 0);
  // Population growth slightly increases housing cost and pollution (pressure)
  const popFactor = Math.min(population * POPULATION_PRESSURE, 0.5);
  const housingPressure = popFactor * 2;
  const pollutionPressure = popFactor * 3;
  // Economy tends to mean revert slightly toward 50 if no external shock
  const economyDrift = (50 - economy) * INFLUENCE * 0.2;
  // Pollution decays slowly if below a threshold (cleanup effect)
  const pollutionDecay = pollution > 20 ? 0 : -0.1;

  const next: CityState = {
    population: Math.max(0, population),
    economy: economy + economyDrift,
    publicHealth: publicHealth + healthDrift,
    housingCost: housingCost + housingCostDrift + housingPressure,
    pollution: Math.max(0, pollution + pollutionPressure + pollutionDecay),
    publicOpinion: publicOpinion + opinionDrift,
  };

  return clampCityState(next);
}
