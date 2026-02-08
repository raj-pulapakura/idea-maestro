from app.agents.state.types import Doc


empty_docs: dict[str, Doc] = {
    "the_pitch": Doc(
        title="The Pitch",
        description="Describe the problem, solution, target user, value prop, and positioning.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "risk_register": Doc(
        title="Risk Register",
        description="List of risks with severity and mitigation.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
        "business_model": Doc(
        title="Business Model",
        description="Describe the business model, monetization, pricing, revenue milestones.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "feature_roadmap": Doc(
        title="Feature Roadmap",
        description="Describe the feature roadmap, MVP, v2, and stretch features.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "gtm_plan": Doc(
        title="GTM Plan",
        description="Describe the GTM plan, launch, channels, growth loops.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "technical_spec": Doc(
        title="Technical Spec",
        description="Describe the technical spec, architecture, stack, timeline, milestones.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "competitor_analysis": Doc(
                title="Competitor Analysis",
        description="Describe the competitor analysis, competitors, market share, product differentiation, market position.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "open_questions": Doc(
        title="Open Questions",
        description="List of open questions for the user to answer.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
}
