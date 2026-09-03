from __future__ import annotations

from providers.base import LLMProvider
from schemas import LanguageAnalysis, TaskNode, TaskPlan


class PlannerAgent:
    name = "Planner Agent"

    async def plan(self, analysis: LanguageAnalysis, provider: LLMProvider | None = None) -> TaskPlan:
        if provider:
            prompt = f"""You are a hierarchical planning and agent-allocation specialist. Create at most
five solvable, complete, non-redundant tasks. For every task, select a specific expert role suited
to that task in assigned_role (for example Story Architect, Character Agent, Dialogue Agent,
Research Agent, or Synthesis Agent—not the generic name Worker Agent). Include valid dependencies
and a concrete expected output. Cover every deliverable requested by the user. Do not solve the task.
Language analysis: {analysis.model_dump_json()}"""
            return await provider.generate_structured(prompt, TaskPlan)
        return self._mock_plan(analysis)

    def _mock_plan(self, analysis: LanguageAnalysis) -> TaskPlan:
        subjects = analysis.entities or ["the main topic"]
        tasks: list[TaskNode] = []
        if analysis.intent == "write_email":
            tasks.extend([
                TaskNode(id="T1", title="Understand purpose and recipient", objective="Identify why the email is being written, who will receive it, and the required details.", assigned_role="Context Analyst", expected_output="email brief"),
                TaskNode(id="T2", title="Draft the email", objective="Create a complete subject line and email body that fulfills the request.", dependencies=["T1"], assigned_role="Email Drafting Agent", expected_output="email draft"),
                TaskNode(id="T3", title="Adapt tone and clarity", objective="Improve politeness, clarity, concision, and recipient-appropriate wording.", dependencies=["T2"], assigned_role="Language & Tone Agent", expected_output="refined email"),
            ])
        elif analysis.intent == "compare" and len(subjects) >= 2:
            tasks.extend([
                TaskNode(id="T1", title=f"Analyze {subjects[0]}", objective=f"Identify the defining features, uses, benefits, and limitations of {subjects[0]}.", assigned_role="Subject Specialist A"),
                TaskNode(id="T2", title=f"Analyze {subjects[1]}", objective=f"Identify the defining features, uses, benefits, and limitations of {subjects[1]}.", assigned_role="Subject Specialist B"),
                TaskNode(id="T3", title="Establish comparison criteria", objective="Choose fair criteria that match the user's audience and purpose.", assigned_role="Comparison Analyst"),
                TaskNode(id="T4", title="Compare the findings", objective="Produce a balanced comparison using the approved criteria.", dependencies=["T1", "T2", "T3"], assigned_role="Synthesis Agent"),
            ])
        else:
            topic = subjects[0]
            tasks.extend([
                TaskNode(id="T1", title="Understand the request", objective=f"Identify the purpose, audience, and essential information concerning {topic}.", assigned_role="Requirements Analyst"),
                TaskNode(id="T2", title="Develop the content", objective=f"Produce the important content, examples, or reasoning needed for {topic}.", assigned_role="Task Specialist"),
                TaskNode(id="T3", title="Structure and refine", objective="Arrange and improve the content to match the requested format and audience.", dependencies=["T1", "T2"], assigned_role="Language & Structure Agent"),
            ])
        return TaskPlan(
            goal=analysis.normalized_text,
            tasks=tasks,
            planning_notes=[
                "Solvability: each leaf task has a bounded objective.",
                "Completeness: the set covers definition, evidence, organization, and comparison when required.",
                "Non-redundancy: overlapping tasks were removed.",
            ],
        )
