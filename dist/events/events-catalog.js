/**
 * Example events for testing and as templates for AI-generated events.
 * In an AI extension, agents would construct Event objects with similar deltas.
 */
export const SAMPLE_EVENTS = {
    recession: {
        id: "recession",
        name: "Economic Recession",
        description: "Markets tumble; unemployment rises.",
        delta: { economy: -20, publicOpinion: -15, housingCost: -5 },
    },
    boom: {
        id: "boom",
        name: "Economic Boom",
        description: "New industry and jobs boost the economy.",
        delta: { economy: 15, publicOpinion: 10, housingCost: 10, pollution: 5 },
    },
    pandemic: {
        id: "pandemic",
        name: "Health Crisis",
        description: "Outbreak strains healthcare and confidence.",
        delta: { publicHealth: -25, publicOpinion: -20, economy: -10 },
    },
    greenPolicy: {
        id: "green-policy",
        name: "Green Policy Initiative",
        description: "Investment in clean energy and transport.",
        delta: { pollution: -15, publicOpinion: 10, economy: -5 },
    },
    housingSubsidy: {
        id: "housing-subsidy",
        name: "Housing Subsidy Program",
        description: "Government support for affordable housing.",
        delta: { housingCost: -15, publicOpinion: 15, economy: -5 },
    },
    disaster: {
        id: "disaster",
        name: "Natural Disaster",
        description: "Flooding and damage hit the city.",
        delta: {
            publicHealth: -15,
            economy: -20,
            pollution: 10,
            publicOpinion: -25,
            housingCost: 5,
        },
    },
};
//# sourceMappingURL=events-catalog.js.map