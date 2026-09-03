from __future__ import annotations

import asyncio

from agents import LanguageAgent, PlannerAgent, ReviewerAgent, WorkerAgent, WriterAgent
from config import settings
from providers.base import LLMProvider
from schemas import AgentMessage, CompactRunResult, RunResult, TaskStatus, WorkerResult


class Orchestrator:
    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider
        self.language = LanguageAgent()
        self.planner = PlannerAgent()
        self.worker = WorkerAgent()
        self.reviewer = ReviewerAgent()
        self.writer = WriterAgent()
        self.messages: list[AgentMessage] = []

    def log(self, sender: str, receiver: str, kind: str, summary: str, task_id: str | None = None, **payload):
        self.messages.append(AgentMessage(
            sequence=len(self.messages) + 1,
            sender=sender,
            receiver=receiver,
            message_type=kind,
            task_id=task_id,
            human_summary=summary,
            payload=payload,
        ))

    async def run(self, user_text: str) -> RunResult:
        if self.provider:
            return await self._run_quota_efficient(user_text)

        self.messages = []
        analysis = await self.language.analyze(user_text, self.provider)
        self.log(self.language.name, "Host Agent", "language_analysis", "The request was converted into an intent, entities, constraints, ambiguities, and a semantic frame.")
        if analysis.ambiguities:
            self.log("Host Agent", "User", "clarification_required", analysis.ambiguities[0].question)

        plan = await self.planner.plan(analysis, self.provider)
        plan.tasks = plan.tasks[: settings.max_tasks]
        self.log(self.planner.name, "Host Agent", "task_plan", f"The planner created {len(plan.tasks)} bounded tasks and selected suitable specialist roles.")

        completed: dict[str, WorkerResult] = {}
        while len(completed) < len(plan.tasks):
            ready = [
                task for task in plan.tasks
                if task.id not in completed
                and task.status != TaskStatus.running
                and all(dep in completed for dep in task.dependencies)
            ]
            if not ready:
                raise RuntimeError("The task plan contains an unresolved or cyclic dependency.")
            ready = ready[: settings.max_parallel_workers]
            for task in ready:
                task.status = TaskStatus.running
                self.log("Host Agent", task.assigned_role, "task_assignment", f"Assigned {task.id}: {task.title}", task.id, objective=task.objective)
            outputs = await asyncio.gather(*[
                self.worker.execute(task, analysis, [completed[d] for d in task.dependencies], self.provider)
                for task in ready
            ])
            for task, output in zip(ready, outputs):
                task.status = TaskStatus.completed
                completed[task.id] = output
                self.log(task.assigned_role, "Host Agent", "task_result", f"Completed {task.id}: {task.title}", task.id, uncertainties=output.uncertainties)

        ordered_results = [completed[t.id] for t in plan.tasks]
        review = await self.reviewer.review(analysis, ordered_results, self.provider)
        for task in plan.tasks:
            task.status = TaskStatus.reviewed if review.approved else TaskStatus.revision
        self.log(self.reviewer.name, "Host Agent", "review", f"Review score: {review.score}/10. {'Approved' if review.approved else 'Revision required'}.", issues=review.issues)

        final_answer = await self.writer.write(analysis, ordered_results, review, self.provider)
        self.log(self.writer.name, "User", "final_response", "The approved findings were selected, ordered, adapted, and realized as a final response.")
        return RunResult(
            analysis=analysis,
            plan=plan,
            worker_results=ordered_results,
            review=review,
            final_answer=final_answer,
            messages=self.messages,
        )

    async def _run_quota_efficient(self, user_text: str) -> RunResult:
        """Execute all logical agent stages in one validated Gemini request.

        This preserves role separation and an observable communication trace while
        using one API request per preview, which is appropriate for free-tier demos.
        """
        prompt = f"""You are the Host Agent of a hierarchical multi-agent language-processing
        framework. Process the user's task through the logical agents below and return one complete,
schema-valid CompactRunResult.

USER REQUEST:
{user_text}

REQUIRED LOGICAL WORKFLOW:
1. Language Understanding Agent: normalize the request; identify the precise intent, entities,
key phrases, explicit constraints, genuine ambiguities, and a useful semantic frame. Do not invent
constraints.
2. Planner Agent: create 2-4 solvable, complete, non-redundant subtasks with valid dependencies.
Assign every task a specific expert role appropriate to this request, never the generic role
"Worker Agent".
3. Specialist Agents: provide substantive, task-specific WorkerResult content for every planned
task. The results must contain material usable directly in the requested deliverable—never
placeholder text, generic workflow advice, or mock commentary. Keep each worker result compact:
only information that materially contributes to the deliverable, with at most four key points.
4. Reviewer Agent: score relevance, completeness, specificity, consistency, and compliance with
every requested deliverable. Record concrete strengths and issues.
5. NLG Writer Agent: create the actual polished deliverable the user requested. Cover every
requested item, synthesize specialist work, and use the correct genre, format, tone, and language.
Do not mention agents, prompts, schemas, mock modes, or internal workflow in final_answer.
CONSISTENCY RULES:
- Task IDs and WorkerResult task_ids must match.
- Mark completed tasks as reviewed if approved, or revision_requested if not approved.
- final_answer must be a complete usable preview, not an explanation of what could be produced.
- Avoid repeating the same material across worker results, review fields, and final_answer.
- Keep analysis and review concise. Let final_answer take most of the response budget.
- Preserve the user's original request exactly in LanguageAnalysis.original_text.
"""
        compact = await self.provider.generate_structured(prompt, CompactRunResult)
        compact.analysis.original_text = user_text
        compact.plan.tasks = compact.plan.tasks[: settings.max_tasks]
        valid_ids = {task.id for task in compact.plan.tasks}
        compact.worker_results = [
            worker for worker in compact.worker_results if worker.task_id in valid_ids
        ]
        messages: list[AgentMessage] = [
            AgentMessage(
                sequence=1,
                sender="Language Understanding Agent",
                receiver="Host Agent",
                message_type="language_analysis",
                human_summary=f"Interpreted the request as {compact.analysis.intent.replace('_', ' ')} and extracted its language constraints.",
            ),
            AgentMessage(
                sequence=2,
                sender="Planner Agent",
                receiver="Host Agent",
                message_type="task_plan",
                human_summary=f"Created {len(compact.plan.tasks)} non-redundant tasks and selected specialist roles.",
            ),
        ]
        for task in compact.plan.tasks:
            messages.append(AgentMessage(
                sequence=len(messages) + 1,
                sender="Host Agent",
                receiver=task.assigned_role,
                message_type="task_assignment",
                task_id=task.id,
                human_summary=f"Assigned {task.id}: {task.title}",
            ))
            messages.append(AgentMessage(
                sequence=len(messages) + 1,
                sender=task.assigned_role,
                receiver="Host Agent",
                message_type="task_result",
                task_id=task.id,
                human_summary=f"Completed {task.id}: {task.title}",
            ))
        messages.extend([
            AgentMessage(
                sequence=len(messages) + 1,
                sender="Reviewer Agent",
                receiver="Host Agent",
                message_type="review",
                human_summary=f"Scored the material {compact.review.score}/10 and {'approved it' if compact.review.approved else 'requested revision'}.",
            ),
            AgentMessage(
                sequence=len(messages) + 2,
                sender="NLG Writer Agent",
                receiver="User",
                message_type="preview",
                human_summary="Synthesized the approved specialist material into the requested preview.",
            ),
        ])
        return RunResult(
            analysis=compact.analysis,
            plan=compact.plan,
            worker_results=compact.worker_results,
            review=compact.review,
            final_answer=compact.final_answer,
            messages=messages,
        )
