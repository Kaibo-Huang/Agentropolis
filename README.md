# GenAI Genesis — Society Simulation

A TypeScript simulation of a city with **population**, **economy**, **public health**, **housing cost**, **pollution**, and **public opinion**. The engine runs in discrete days and supports an **Event** system for policy changes, disasters, and other one-off effects. The code is structured so you can extend it with AI agents later.

## Structure

- **`CityState`** — Holds all city metrics (0–100 scales except population). Use `clampCityState()` and `DEFAULT_CITY_STATE` from `types/city-state`.
- **Events** — `Event` has `id`, `name`, optional `description`, and a `delta` (partial changes applied to state). Use `applyEventToState()` or the engine’s `applyEvent()`.
- **SimulationEngine** — `step()` advances one day (internal rules only); `applyEvent(event)` applies an event immediately. Optional hooks: `onStep`, `onEventApplied`.

Internal daily rules (in `engine/rules.ts`): economy influences housing cost, pollution hurts health, and economy/health/pollution/housing influence public opinion. You can replace or extend these rules without changing the engine.

## Setup

```bash
npm install
npm run build
```

## Usage

```ts
import {
  SimulationEngine,
  DEFAULT_CITY_STATE,
  SAMPLE_EVENTS,
} from "genai-genesis";

const engine = new SimulationEngine(DEFAULT_CITY_STATE, {
  onStep(prev, next, day) {
    console.log(`Day ${day}: economy ${prev.economy} -> ${next.economy}`);
  },
});

engine.step();
engine.applyEvent(SAMPLE_EVENTS.recession);
engine.runDays(30);
console.log(engine.state);
```

## Extending with AI agents

- **Read state**: `engine.state` (read-only).
- **Act**: Call `engine.applyEvent({ id, name, description?, delta })` with agent-chosen or generated events.
- **Observe**: Use `onStep` and `onEventApplied` to feed state and outcomes back to the agent.
- **Custom rules**: Replace or wrap `computeDailyUpdate` in `engine/rules.ts` for different dynamics.

## License

MIT
