from __future__ import annotations

from providers.base import LLMProvider
from schemas import LanguageAnalysis, ReviewResult, WorkerResult


class WriterAgent:
    name = "NLG Writer Agent"

    async def write(
        self,
        analysis: LanguageAnalysis,
        results: list[WorkerResult],
        review: ReviewResult,
        provider: LLMProvider | None = None,
    ) -> str:
        if provider:
            prompt = f"""You are the final Natural Language Generation writer. Produce the actual
deliverable requested by the user—not a summary of the agents' work and not instructions for how
to create it. Use all approved specialist material, cover every requested item, remove repetition,
and adapt vocabulary, tone, length, language, and format precisely. Do not mention agents,
workflows, prompts, mock modes, or internal analysis. Return only the polished preview content.
Original user request: {analysis.original_text}
Request analysis: {analysis.model_dump_json()}
Approved results: {[r.model_dump() for r in results]}
Review: {review.model_dump_json()}"""
            return await provider.generate_text(prompt)
        if analysis.intent == "write_email":
            low = analysis.normalized_text.lower()
            recipient = "Project Guide" if "project guide" in low else "Recipient"
            subject = "Request for a Meeting to Discuss Project Progress" if "meeting" in low else "Regarding My Request"
            meeting_line = "I would like to request a meeting on Friday to discuss the progress of my project." if "friday" in low else "I am writing to discuss the request mentioned above."
            return (
                f"**Subject: {subject}**\n\n"
                f"Dear {recipient},\n\n"
                f"{meeting_line} I would appreciate the opportunity to share my updates and receive your guidance on the next steps.\n\n"
                "Please let me know a convenient time.\n\n"
                "Thank you for your time.\n\n"
                "Best regards,\n"
                "[Your Name]"
            )
        headings = "\n\n".join(f"### {r.title}\n{r.content}" for r in results)
        return (
            f"## Proposed {analysis.constraints.output_format.title()}\n\n{headings}\n\n"
            "The host has combined the agents' approved contributions into this preview. "
            "Enable Gemini later for fully flexible task-specific content."
        )
