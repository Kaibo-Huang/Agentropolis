/**
 * Personality traits for citizens. All 0–100 unless noted.
 */
export interface PersonalityTraits {
  /** Willingness to take risks (0 = cautious, 100 = risk-seeking). */
  riskTolerance: number;
  /** Political leaning (0 = left, 100 = right). */
  politicalLeaning: number;
  /** Trust in government (0 = distrust, 100 = high trust). */
  trustInGovernment: number;
}

/** Clamp value to [min, max]. */
function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function clampTraits(t: PersonalityTraits): PersonalityTraits {
  return {
    riskTolerance: clamp(t.riskTolerance, 0, 100),
    politicalLeaning: clamp(t.politicalLeaning, 0, 100),
    trustInGovernment: clamp(t.trustInGovernment, 0, 100),
  };
}

/** Occupation identifier; income and job-change logic can key off this. */
export type OccupationType =
  | "unemployed"
  | "teacher"
  | "engineer"
  | "healthcare"
  | "retail"
  | "manufacturing"
  | "government"
  | "other";
