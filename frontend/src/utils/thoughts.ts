import type { PostResponse } from "../api/types";

export const BASE_AGENT_THOUGHTS = [
  "Transit nodes are busier than usual. Small delay, big ripple.",
  "A quiet morning often becomes an active afternoon.",
  "Happiness drifts upward when routes stay predictable.",
  "Neighborhood chatter tends to spike right after each tick.",
  "Agents near the core react faster to event changes.",
];

export function buildThoughtPool(
  latestPost: PostResponse | null,
  followerNameById: Map<number, string>,
): string[] {
  const pool = [...BASE_AGENT_THOUGHTS];
  if (!latestPost) return pool;

  const snippet =
    latestPost.text.length > 68
      ? `${latestPost.text.slice(0, 65)}...`
      : latestPost.text;
  const author =
    followerNameById.get(latestPost.follower_id) ??
    `Follower #${latestPost.follower_id}`;

  return [`${author}: ${snippet}`, ...pool];
}
