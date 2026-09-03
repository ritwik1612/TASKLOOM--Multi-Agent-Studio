import asyncio
import unittest

from orchestrator import Orchestrator
from schemas import (
    CompactRunResult,
    ConstraintSet,
    LanguageAnalysis,
    ReviewResult,
    TaskNode,
    TaskPlan,
    TaskStatus,
    WorkerResult,
)


class CountingProvider:
    def __init__(self):
        self.calls = 0

    async def generate_structured(self, prompt, schema):
        self.calls += 1
        self.prompt = prompt
        return CompactRunResult(
            analysis=LanguageAnalysis(
                original_text="temporary",
                normalized_text="Write a concise email.",
                intent="write_email",
                constraints=ConstraintSet(output_format="email"),
            ),
            plan=TaskPlan(
                goal="Write an email",
                tasks=[
                    TaskNode(
                        id="T1",
                        title="Draft",
                        objective="Draft the email",
                        assigned_role="Email Drafting Agent",
                        status=TaskStatus.reviewed,
                    )
                ],
            ),
            worker_results=[WorkerResult(task_id="T1", title="Draft", content="Drafted")],
            review=ReviewResult(approved=True, score=9),
            final_answer="Subject: Meeting\n\nHello, may we meet on Friday?",
        )

    async def generate_text(self, prompt):
        raise AssertionError("The preview path should not make a second text-generation call.")


class PipelineTests(unittest.TestCase):
    def test_provider_preview_uses_exactly_one_model_call(self):
        provider = CountingProvider()
        request = "Write a concise email asking for a Friday meeting."
        result = asyncio.run(Orchestrator(provider).run(request))
        self.assertEqual(provider.calls, 1)
        self.assertEqual(result.analysis.original_text, request)
        self.assertEqual(result.final_answer.splitlines()[0], "Subject: Meeting")

    def test_mock_pipeline_completes(self):
        result = asyncio.run(Orchestrator().run("Compare Python and Java for beginners in simple English."))
        self.assertEqual(result.analysis.intent, "compare")
        self.assertGreaterEqual(len(result.plan.tasks), 3)
        self.assertTrue(result.review.approved)
        self.assertIn("Proposed Comparison", result.final_answer)

    def test_email_task_selects_specialists_and_creates_preview(self):
        result = asyncio.run(Orchestrator().run(
            "Write a polite email to my project guide asking for a meeting on Friday."
        ))
        self.assertEqual(result.analysis.intent, "write_email")
        self.assertEqual(
            [task.assigned_role for task in result.plan.tasks],
            ["Context Analyst", "Email Drafting Agent", "Language & Tone Agent"],
        )
        self.assertIn("Subject:", result.final_answer)
        self.assertIn("Dear Project Guide", result.final_answer)

    def test_ambiguity_detection(self):
        result = asyncio.run(Orchestrator().run("Explain Java"))
        self.assertEqual(len(result.analysis.ambiguities), 1)


if __name__ == "__main__":
    unittest.main()
