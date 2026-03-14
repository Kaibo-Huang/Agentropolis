import type { CityState } from "../types/city-state.js";
import type { Event } from "../events/event.js";
import type { Citizen } from "./citizen.js";
import type { CitizenAction } from "./actions.js";
import type { OccupationType } from "./types.js";

const NEIGHBORHOODS = ["downtown", "suburbs", "waterfront", "industrial", "riverside"] as const;
const OCCUPATIONS: { occupation: OccupationType; income: number }[] = [
  { occupation: "teacher", income: 55 },
  { occupation: "engineer", income: 85 },
  { occupation: "healthcare", income: 70 },
  { occupation: "retail", income: 35 },
  { occupation: "manufacturing", income: 50 },
  { occupation: "government", income: 65 },
  { occupation: "other", income: 45 },
];

/**
 * Decides which action a citizen takes this step based on personality,
 * current city conditions, and recent events.
 */
export function decideAction(
  citizen: Citizen,
  cityState: CityState,
  recentEvents: Event[]
): CitizenAction {
  const { personality, happiness, opinion, income, occupation } = citizen;
  const { economy, housingCost, pollution } = cityState;

  // Recent event impact: low trust + recent negative events -> more oppose/protest
  const recentNegative = recentEvents.some(
    (e) =>
      (e.delta.publicOpinion ?? 0) < 0 ||
      (e.delta.economy ?? 0) < 0 ||
      (e.delta.publicHealth ?? 0) < 0
  );
  const recentPositive = recentEvents.some(
    (e) =>
      (e.delta.publicOpinion ?? 0) > 0 ||
      (e.delta.economy ?? 0) > 0
  );

  const discontent =
    (100 - happiness) * 0.3 +
    (100 - opinion) * 0.2 +
    (housingCost > 60 ? 15 : 0) +
    (pollution > 50 ? 10 : 0) +
    (economy < 40 ? 10 : 0);
  const isDiscontent = discontent > 35;

  const supportsGovernment = personality.trustInGovernment > 50 && recentPositive;
  const opposesGovernment = personality.trustInGovernment < 50 && recentNegative;

  // Protest: high discontent, low trust, risk-tolerant
  if (
    isDiscontent &&
    personality.trustInGovernment < 45 &&
    personality.riskTolerance > 55
  ) {
    return { type: "protest" };
  }

  // Oppose policy: discontent or low trust, not quite protesting
  if (opposesGovernment || (isDiscontent && personality.trustInGovernment < 60)) {
    return { type: "oppose_policy" };
  }

  // Support policy: trust government and recent positive or decent conditions
  if (supportsGovernment || (personality.trustInGovernment > 65 && !isDiscontent)) {
    return { type: "support_policy" };
  }

  // Move neighborhood: housing cost pain + risk tolerance (willing to move)
  if (housingCost > 55 && personality.riskTolerance > 40) {
    const other = NEIGHBORHOODS.filter((n) => n !== citizen.neighborhood);
    if (other.length > 0) {
      const pick = other[Math.floor(Math.random() * other.length)];
      return { type: "move_neighborhood", neighborhood: pick };
    }
  }

  // Change job: low income + risk tolerance, or low happiness from economy
  if (
    (income < 45 || (economy < 45 && happiness < 50)) &&
    personality.riskTolerance > 35
  ) {
    const other = OCCUPATIONS.filter((o) => o.occupation !== occupation);
    if (other.length > 0) {
      const pick = other[Math.floor(Math.random() * other.length)];
      return { type: "change_job", occupation: pick.occupation, income: pick.income };
    }
  }

  // Default: share opinion (spread satisfaction/dissatisfaction)
  return { type: "share_opinion" };
}
