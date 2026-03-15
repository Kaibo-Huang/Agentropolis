import SimulationView from "../../../components/SimulationView";

interface SimulationPageProps {
  params: Promise<{ sessionId: string }>;
}

export default async function SimulationPage({
  params,
}: SimulationPageProps) {
  const { sessionId } = await params;
  return <SimulationView sessionId={sessionId} />;
}
