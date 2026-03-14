import type { Citizen } from "./citizen.js";

/**
 * Simple undirected social graph: each citizen has a set of neighbor IDs.
 * Used to spread opinions between connected citizens.
 */
export class SocialNetwork {
  private _edges = new Map<string, Set<string>>();

  /** Add a bidirectional connection between two citizens. */
  connect(idA: string, idB: string): void {
    if (idA === idB) return;
    this.addEdge(idA, idB);
    this.addEdge(idB, idA);
  }

  private addEdge(from: string, to: string): void {
    let set = this._edges.get(from);
    if (!set) {
      set = new Set();
      this._edges.set(from, set);
    }
    set.add(to);
  }

  /** Get neighbor IDs for a citizen. */
  getNeighbors(id: string): ReadonlySet<string> {
    return this._edges.get(id) ?? new Set();
  }

  /** Check if two citizens are connected. */
  areConnected(idA: string, idB: string): boolean {
    return this._edges.get(idA)?.has(idB) ?? false;
  }

  /** Add a citizen to the graph (no edges yet). */
  addCitizen(id: string): void {
    if (!this._edges.has(id)) {
      this._edges.set(id, new Set());
    }
  }

  /**
   * Spread opinions: each citizen's opinion blends toward the average opinion
   * of their neighbors. Strength in (0, 1]; higher = more influence.
   */
  spreadOpinions(
    citizens: Map<string, Citizen>,
    strength: number
  ): void {
    const clampedStrength = Math.max(0.01, Math.min(1, strength));
    const order = [...citizens.keys()];

    for (const id of order) {
      const citizen = citizens.get(id);
      if (!citizen) continue;

      const neighbors = this.getNeighbors(id);
      if (neighbors.size === 0) continue;

      let sum = 0;
      let count = 0;
      for (const nid of neighbors) {
        const neighbor = citizens.get(nid);
        if (neighbor) {
          sum += neighbor.opinion;
          count += 1;
        }
      }
      if (count === 0) continue;

      const avgOpinion = sum / count;
      citizen.blendOpinion(avgOpinion, clampedStrength);
    }
  }

  /**
   * Build a simple random graph: each citizen gets roughly `degree` connections
   * to others (no self, no duplicate edges).
   */
  static randomGraph(
    citizenIds: string[],
    degree: number
  ): SocialNetwork {
    const net = new SocialNetwork();
    for (const id of citizenIds) {
      net.addCitizen(id);
    }
    const n = citizenIds.length;
    if (n < 2) return net;

    const actualDegree = Math.min(degree, n - 1);
    const maxAttempts = n * n;
    for (let i = 0; i < citizenIds.length; i++) {
      const id = citizenIds[i];
      const current = net.getNeighbors(id).size;
      let need = actualDegree - current;
      let attempts = 0;
      while (need > 0 && attempts < maxAttempts) {
        attempts += 1;
        const j = Math.floor(Math.random() * n);
        if (j !== i && !net.areConnected(id, citizenIds[j])) {
          net.connect(id, citizenIds[j]);
          need -= 1;
        }
      }
    }
    return net;
  }
}
