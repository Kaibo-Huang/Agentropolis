"use client";

import { useState } from "react";
import { useSimulationStore } from "../store/simulationStore";

export default function AvatarSheet() {
  const showAvatarSheet = useSimulationStore((s) => s.showAvatarSheet);
  const toggleAvatarSheet = useSimulationStore((s) => s.toggleAvatarSheet);
  const createFollowerWithAvatar = useSimulationStore(
    (s) => s.createFollowerWithAvatar,
  );
  const log = useSimulationStore((s) => s.log);
  const session = useSimulationStore((s) => s.session);

  const [name, setName] = useState("You");
  const [skinTone, setSkinTone] = useState(40);
  const [bodyType, setBodyType] = useState("average");
  const [hairTexture, setHairTexture] = useState("straight");
  const [hairStyle, setHairStyle] = useState("short");
  const [hairColor, setHairColor] = useState("#4a3728");
  const [outfit, setOutfit] = useState("casual");
  const [outfitColor, setOutfitColor] = useState("#2c3e50");
  const [glasses, setGlasses] = useState(false);
  const [hat, setHat] = useState(false);
  const [bag, setBag] = useState(false);
  const [scarf, setScarf] = useState(false);

  const handleJoin = async () => {
    if (!session) {
      log("No session; start simulation first.");
      return;
    }
    const accessories = [
      glasses && "glasses",
      hat && "hat",
      bag && "bag",
      scarf && "scarf",
    ].filter(Boolean) as string[];

    try {
      await createFollowerWithAvatar(name.trim() || "You", {
        skinTone: skinTone / 100,
        bodyType,
        hairTexture,
        hairStyle,
        hairColor,
        outfit,
        outfitColor,
        accessories,
      });
      toggleAvatarSheet();
    } catch (err) {
      log(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <div className={`avatar-sheet${showAvatarSheet ? " open" : ""}`}>
      <h2>Create your avatar</h2>
      <p className="avatar-desc">
        Join the simulation with a custom avatar. No photos — pick style and
        colors.
      </p>
      <div className="avatar-form">
        <label>
          Name{" "}
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={128}
          />
        </label>
        <label>
          Skin tone{" "}
          <input
            type="range"
            min={0}
            max={100}
            value={skinTone}
            onChange={(e) => setSkinTone(Number(e.target.value))}
          />{" "}
          <span>{(skinTone / 100).toFixed(2)}</span>
        </label>
        <label>
          Body{" "}
          <select value={bodyType} onChange={(e) => setBodyType(e.target.value)}>
            <option value="slim">Slim</option>
            <option value="average">Average</option>
            <option value="broad">Broad</option>
          </select>
        </label>
        <label>
          Hair texture{" "}
          <select
            value={hairTexture}
            onChange={(e) => setHairTexture(e.target.value)}
          >
            <option value="straight">Straight</option>
            <option value="wavy">Wavy</option>
            <option value="curly">Curly</option>
            <option value="coily">Coily</option>
          </select>
        </label>
        <label>
          Hair style{" "}
          <select
            value={hairStyle}
            onChange={(e) => setHairStyle(e.target.value)}
          >
            <option value="short">Short</option>
            <option value="long">Long</option>
            <option value="fade">Fade</option>
            <option value="bun">Bun</option>
            <option value="braids">Braids</option>
            <option value="afro">Afro</option>
            <option value="ponytail">Ponytail</option>
          </select>
        </label>
        <label>
          Hair color{" "}
          <input
            type="color"
            value={hairColor}
            onChange={(e) => setHairColor(e.target.value)}
          />
        </label>
        <label>
          Outfit{" "}
          <select value={outfit} onChange={(e) => setOutfit(e.target.value)}>
            <option value="casual">Casual</option>
            <option value="professional">Professional</option>
            <option value="student">Student</option>
            <option value="athletic">Athletic</option>
            <option value="construction">Construction</option>
            <option value="service">Service</option>
          </select>
        </label>
        <label>
          Outfit color{" "}
          <input
            type="color"
            value={outfitColor}
            onChange={(e) => setOutfitColor(e.target.value)}
          />
        </label>
        <fieldset className="avatar-accessories">
          <legend>Accessories</legend>
          <label>
            <input
              type="checkbox"
              checked={glasses}
              onChange={(e) => setGlasses(e.target.checked)}
            />{" "}
            Glasses
          </label>
          <label>
            <input
              type="checkbox"
              checked={hat}
              onChange={(e) => setHat(e.target.checked)}
            />{" "}
            Hat
          </label>
          <label>
            <input
              type="checkbox"
              checked={bag}
              onChange={(e) => setBag(e.target.checked)}
            />{" "}
            Bag
          </label>
          <label>
            <input
              type="checkbox"
              checked={scarf}
              onChange={(e) => setScarf(e.target.checked)}
            />{" "}
            Scarf
          </label>
        </fieldset>
        <div className="avatar-preview" style={{ backgroundColor: outfitColor }} />
        <button
          type="button"
          className="btn btn-primary btn-avatar-join"
          onClick={handleJoin}
        >
          Join simulation
        </button>
      </div>
    </div>
  );
}
