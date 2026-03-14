import type { PersonalityTraits } from "./types.js";
import { clampTraits } from "./types.js";
import type { OccupationType } from "./types.js";

/** Clamp a value to [0, 100]. */
function clamp100(value: number): number {
  return Math.max(0, Math.min(100, value));
}

/**
 * A citizen agent with identity, economics, personality, and satisfaction.
 * State is updated by actions and by opinion spreading from the social network.
 */
export class Citizen {
  readonly id: string;
  name: string;
  age: number;
  occupation: OccupationType;
  income: number;
  readonly personality: PersonalityTraits;
  happiness: number;
  /** Current opinion/satisfaction (0–100); used for social spreading. */
  opinion: number;
  /** Neighborhood label (for "move neighborhood" flavor). */
  neighborhood: string;

  constructor(options: {
    id: string;
    name: string;
    age: number;
    occupation?: OccupationType;
    income?: number;
    personality: PersonalityTraits;
    happiness?: number;
    opinion?: number;
    neighborhood?: string;
  }) {
    this.id = options.id;
    this.name = options.name;
    this.age = Math.max(0, options.age);
    this.occupation = options.occupation ?? "other";
    this.income = Math.max(0, options.income ?? 50);
    this.personality = clampTraits(options.personality);
    this.happiness = clamp100(options.happiness ?? 50);
    this.opinion = clamp100(options.opinion ?? 50);
    this.neighborhood = options.neighborhood ?? "downtown";
  }

  /** Apply a happiness change (e.g. from an action or city conditions). */
  addHappiness(delta: number): void {
    this.happiness = clamp100(this.happiness + delta);
  }

  /** Apply an opinion change (e.g. from social spread or events). */
  setOpinion(value: number): void {
    this.opinion = clamp100(value);
  }

  /** Blend opinion toward a target (for social influence). */
  blendOpinion(targetOpinion: number, strength: number): void {
    this.opinion = clamp100(
      this.opinion + (targetOpinion - this.opinion) * strength
    );
  }

  /** Update income (e.g. job change). */
  setIncome(value: number): void {
    this.income = Math.max(0, value);
  }

  /** Update occupation (e.g. change job action). */
  setOccupation(occupation: OccupationType): void {
    this.occupation = occupation;
  }

  /** Update neighborhood (e.g. move action). */
  setNeighborhood(neighborhood: string): void {
    this.neighborhood = neighborhood;
  }

  /** Snapshot for read-only exposure (e.g. hooks, UI). */
  snapshot(): Readonly<{
    id: string;
    name: string;
    age: number;
    occupation: OccupationType;
    income: number;
    personality: PersonalityTraits;
    happiness: number;
    opinion: number;
    neighborhood: string;
  }> {
    return {
      id: this.id,
      name: this.name,
      age: this.age,
      occupation: this.occupation,
      income: this.income,
      personality: { ...this.personality },
      happiness: this.happiness,
      opinion: this.opinion,
      neighborhood: this.neighborhood,
    };
  }
}
