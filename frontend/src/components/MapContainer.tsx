"use client";

import dynamic from "next/dynamic";

const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => (
    <div
      id="canvas-container"
      style={{
        position: "fixed",
        inset: 0,
        background: "#09090b",
      }}
    />
  ),
});

export default function MapContainer() {
  return <MapView />;
}
