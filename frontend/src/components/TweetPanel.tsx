"use client";

import { useSimulationStore } from "../store/simulationStore";

export default function TweetPanel() {
  const posts = useSimulationStore((s) => s.posts);

  return (
    <aside className="tweet-panel">
      <h2>Latest Posts</h2>
      <div>
        {posts.slice(0, 20).map((p) => (
          <div key={p.post_id} className="tweet">
            <span className="tweet-author">Follower #{p.follower_id}</span>
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
    </aside>
  );
}
