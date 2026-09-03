from __future__ import annotations

from providers.base import LLMProvider
from schemas import LanguageAnalysis, ReviewResult, WorkerResult


class ReviewerAgent:
    name = "Reviewer Agent"

    async def review(
        self,
        analysis: LanguageAnalysis,
        results: list[WorkerResult],
        provider: LLMProvider | None = None,
    ) -> ReviewResult:
        if provider:
            prompt = f"""You are a strict quality-control reviewer. Assess relevance, completeness,
specificity, internal consistency, uncertainty, and satisfaction of every user deliverable and
language constraint. Reject placeholder, generic, or meta-level content. Approve only when the
material is substantive enough for the final writer to create the requested deliverable.
Original request: {analysis.original_text}
Analysis: {analysis.model_dump_json()}
Results: {[r.model_dump() for r in results]}"""
            return await provider.generate_structured(prompt, ReviewResult)
        issues = []
        if not results:
            issues.append("No worker results were produced.")
        if any(not r.content.strip() for r in results):
            issues.append("At least one worker returned empty content.")
        return ReviewResult(
            approved=not issues,
            score=8 if not issues else 4,
            strengths=["All planned tasks produced structured results.", "User constraints remained attached to the workflow."],
            issues=issues,
            revision_instruction="Regenerate the missing or empty task result." if issues else "",
        )
