from __future__ import annotations

import re

from providers.base import LLMProvider
from schemas import Ambiguity, ConstraintSet, LanguageAnalysis


class LanguageAgent:
    name = "Language Understanding Agent"

    async def analyze(self, text: str, provider: LLMProvider | None = None) -> LanguageAnalysis:
        if provider:
            prompt = f"""You are a language-understanding agent. Analyze the request without solving it.
Extract intent, entities, key phrases, constraints, ambiguities, and a compact semantic frame.
Do not invent constraints. Original request: {text!r}"""
            return await provider.generate_structured(prompt, LanguageAnalysis)
        return self._mock_analysis(text)

    def _mock_analysis(self, text: str) -> LanguageAnalysis:
        normalized = re.sub(r"\s+", " ", text.strip())
        normalized = re.sub(r"\bpls\b|\bplz\b", "please", normalized, flags=re.I)
        normalized = re.sub(r"\bu\b", "you", normalized, flags=re.I)
        if normalized and normalized[-1] not in ".?!":
            normalized += "."
        low = normalized.lower()
        intent = next(
            (name for term, name in [
                ("email", "write_email"), ("e-mail", "write_email"),
                ("letter", "write_letter"), ("proposal", "write_proposal"),
                ("compare", "compare"), ("summar", "summarize"), ("translate", "translate"),
                ("plan", "create_plan"), ("report", "generate_report"), ("explain", "explain"),
                ("write", "write_content"), ("draft", "write_content"), ("analy", "analyze")
            ] if term in low),
            "answer_question",
        )
        audience = "beginners" if "beginner" in low else "students" if "student" in low else "general"
        language = "Hindi" if "hindi" in low else "English"
        tone = "polite and professional" if any(x in low for x in ("polite", "formal", "professional")) else "friendly" if "friendly" in low else "simple and beginner-friendly" if any(x in low for x in ("simple", "beginner")) else "clear and helpful"
        length = "short" if "short" in low else "detailed" if any(x in low for x in ("detailed", "comprehensive")) else "medium"
        output_format = "email" if intent == "write_email" else "letter" if intent == "write_letter" else "proposal" if intent == "write_proposal" else "comparison" if intent == "compare" else "report" if "report" in low else "structured response"
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", normalized)
        capitals = re.findall(r"\b(?:[A-Z][A-Za-z0-9+#.-]*)(?:\s+[A-Z][A-Za-z0-9+#.-]*)*\b", text)
        entities = list(dict.fromkeys(quoted + [x for x in capitals if x.lower() not in {"compare", "explain", "prepare", "create"}]))
        if intent == "compare":
            match = re.search(r"compare\s+(.+?)\s+(?:and|vs\.?|versus)\s+(.+?)(?:\s+for|\s+in|[.,?]|$)", low)
            if match:
                entities = [match.group(1).strip().title(), match.group(2).strip().title()]
        ambiguities = []
        if re.fullmatch(r"(?:please\s+)?(?:explain|describe)\s+java\.?", low):
            ambiguities.append(Ambiguity(
                term="Java",
                possible_meanings=["programming language", "island", "coffee"],
                question="Do you mean the Java programming language, Java island, or Java coffee?",
            ))
        constraints = ConstraintSet(
            audience=audience,
            language=language,
            tone=tone,
            length=length,
            output_format=output_format,
        )
        return LanguageAnalysis(
            original_text=text,
            normalized_text=normalized,
            intent=intent,
            entities=entities,
            key_phrases=[intent.replace("_", " "), audience, output_format],
            constraints=constraints,
            ambiguities=ambiguities,
            semantic_frame={
                "action": intent,
                "subjects": entities,
                "beneficiary": audience,
                "requested_output": output_format,
            },
        )
