from __future__ import annotations

from providers.base import LLMProvider
from schemas import LanguageAnalysis, TaskNode, WorkerResult


class WorkerAgent:
    name = "Worker Agent"

    async def execute(
        self,
        task: TaskNode,
        analysis: LanguageAnalysis,
        dependencies: list[WorkerResult],
        provider: LLMProvider | None = None,
    ) -> WorkerResult:
        if provider:
            prompt = f"""You are the {task.assigned_role}. Complete the assigned task with substantive,
task-specific material that can be used directly in the final response. Respect every user
constraint and the original creative or factual intent. Do not discuss the workflow or provide
generic advice. Identify genuine uncertainty, but do not use placeholder text.
Task: {task.model_dump_json()}
Original request: {analysis.original_text}
Language constraints: {analysis.constraints.model_dump_json()}
Dependency results: {[d.model_dump() for d in dependencies]}"""
            return await provider.generate_structured(prompt, WorkerResult)
        dependency_note = ""
        if dependencies:
            dependency_note = " It integrates the completed findings from: " + ", ".join(d.title for d in dependencies) + "."
        topic = ", ".join(analysis.entities) or "the requested topic"
        points = [
            f"The task focuses on {task.objective.rstrip('.').lower()}.",
            f"The explanation should remain {analysis.constraints.tone} for {analysis.constraints.audience}.",
            "The result should distinguish central ideas from supporting examples and avoid unsupported certainty.",
        ]
        return WorkerResult(
            task_id=task.id,
            title=task.title,
            content=f"Mock research result for {topic}: " + " ".join(points) + dependency_note,
            key_points=points,
            uncertainties=["Mock mode demonstrates orchestration; factual content will be produced during Gemini testing."],
        )
