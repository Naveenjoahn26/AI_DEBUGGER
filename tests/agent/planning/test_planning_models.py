from repository.agent.planning.models import Plan, PlanStep, PlanStepStatus
from repository.agent.state.models import AgentState


def test_plan_can_track_steps():
    plan = Plan(
        steps=[
            PlanStep(
                description="Find login endpoint",
                status=PlanStepStatus.COMPLETED,
            ),
            PlanStep(
                description="Inspect authentication service",
                status=PlanStepStatus.IN_PROGRESS,
            ),
            PlanStep(
                description="Verify root cause",
            ),
        ],
        current_step=1,
    )

    assert len(plan.steps) == 3
    assert plan.current_step == 1
    assert plan.steps[0].status == PlanStepStatus.COMPLETED


def test_agent_state_can_contain_plan():
    plan = Plan(
        steps=[
            PlanStep(
                description="Find login endpoint"
            )
        ]
    )

    state = AgentState(
        goal="Find the login bug",
        plan=plan,
    )

    assert state.plan is not None
    assert state.plan.steps[0].description == "Find login endpoint"
