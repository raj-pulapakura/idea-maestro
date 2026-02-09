from app.agents.state.types import Doc


empty_docs: dict[str, Doc] = {
    "product_brief": Doc(
        title="Product Brief",
        description="Describe the core problem, target user, value proposition, and positioning.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "evidence_assumptions_log": Doc(
        title="Evidence & Assumptions Log",
        description="Track key assumptions with confidence level and validation status.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "mvp_scope_non_goals": Doc(
        title="MVP Scope & Non-Goals",
        description="Define what is in scope for MVP and explicitly list what is out of scope.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "technical_plan": Doc(
        title="Technical Plan",
        description="Describe architecture, stack decisions, delivery milestones, and constraints.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "gtm_plan": Doc(
        title="GTM Plan",
        description="Describe launch strategy, distribution channels, and growth experiments.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "business_model_pricing": Doc(
        title="Business Model & Pricing",
        description="Describe monetization model, packaging, pricing, and core unit economics.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "risk_decision_log": Doc(
        title="Risk & Decision Log",
        description="Track major risks, tradeoffs, and decision rationale over time.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
    "next_actions_board": Doc(
        title="Next Actions Board",
        description="Maintain a prioritized list of concrete tasks for the next two weeks.",
        content="",
        version=1,
        updated_by=None,
        updated_at=None,
    ),
}
