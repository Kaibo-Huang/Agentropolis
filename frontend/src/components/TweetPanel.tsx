"use client";

import { useMemo } from "react";
import { useSimulationStore } from "../store/simulationStore";

export default function TweetPanel() {
  const posts = useSimulationStore((s) => s.posts);
  const followers = useSimulationStore((s) => s.followers);

  const followerNameById = useMemo(
    () => new Map(followers.map((f) => [f.follower_id, f.name])),
    [followers],
  );

  if (posts.length === 0) {
    return (
      <p className="tweet-empty">
        No posts yet. Advance the simulation to see city chatter.
      </p>
    );
  }

  return (
    <div className="tweet-list">
      {posts.slice(0, 20).map((p) => (
        <div key={p.post_id} className="tweet">
          <span className="tweet-author">
            {followerNameById.get(p.follower_id) ?? `Follower #${p.follower_id}`}
          </span>
          <span className="tweet-text">{p.text}</span>
          <span className="tweet-time">
            {new Date(p.virtual_time).toLocaleTimeString("en-CA", {
              timeZone: "America/Toronto",
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
            })}
          </span>
        </div>
      ))}
    </div>
  );
}
