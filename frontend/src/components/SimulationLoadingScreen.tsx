interface SimulationLoadingScreenProps {
  title?: string;
  message?: string;
}

export default function SimulationLoadingScreen({
  title = "Loading simulation",
  message = "Please wait while the city map syncs.",
}: SimulationLoadingScreenProps) {
  return (
    <section className="sim-loading-screen" aria-live="polite">
      <div className="sim-loading-content">
        <span className="sim-loading-spinner" aria-hidden="true" />
        <h2 className="sim-loading-title">{title}</h2>
        <p className="sim-loading-message">{message}</p>
      </div>
    </section>
  );
}
