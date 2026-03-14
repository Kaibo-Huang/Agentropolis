import { Citizen } from "./citizen.js";
import type { PersonalityTraits } from "./types.js";
import type { OccupationType } from "./types.js";
import { SocialNetwork } from "./social-network.js";

const NAMES = [
  "Alex", "Jordan", "Sam", "Morgan", "Riley",
  "Casey", "Quinn", "Avery", "Blake", "Dakota",
];

/**
 * Create a set of sample citizens with varied personalities and a random social graph.
 * Useful for quick testing of CitizenSimulationEngine.
 */
export function createSampleCitizens(
  count: number,
  options: { averageDegree?: number } = {}
): { citizens: Citizen[]; socialNetwork: SocialNetwork } {
  const citizens: Citizen[] = [];
  const degree = options.averageDegree ?? 2;

  for (let i = 0; i < count; i++) {
    const personality: PersonalityTraits = {
      riskTolerance: 30 + Math.random() * 50,
      politicalLeaning: Math.random() * 100,
      trustInGovernment: 25 + Math.random() * 55,
    };
    const occupations: OccupationType[] = [
      "teacher", "engineer", "healthcare", "retail", "manufacturing", "government", "other",
    ];
    const occupation = occupations[Math.floor(Math.random() * occupations.length)];
    const income = 30 + Math.floor(Math.random() * 60);
    const citizen = new Citizen({
      id: `citizen-${i}`,
      name: NAMES[i % NAMES.length] + (i >= NAMES.length ? ` ${i}` : ""),
      age: 25 + Math.floor(Math.random() * 45),
      occupation,
      income,
      personality,
      happiness: 40 + Math.random() * 40,
      opinion: 40 + Math.random() * 40,
      neighborhood: ["downtown", "suburbs", "waterfront"][i % 3],
    });
    citizens.push(citizen);
  }

  const socialNetwork = SocialNetwork.randomGraph(
    citizens.map((c) => c.id),
    degree
  );
  return { citizens, socialNetwork };
}
