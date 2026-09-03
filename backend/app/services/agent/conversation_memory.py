from typing import List, Dict, Any, Optional
from backend.app.services.agent.intent_classifier import IntentEnum, IntentClassificationResult, LanguageEnum


class ConversationState:
    def __init__(self, history: Optional[List[Dict[str, str]]] = None):
        self.history: List[Dict[str, str]] = history or []
        self.active_issue_number: Optional[int] = None
        self.active_file: Optional[str] = None
        self.active_topic: Optional[str] = None
        self.language_preference: Optional[LanguageEnum] = None
        self.last_intent: Optional[IntentEnum] = None

        self._reconstruct_from_history()

    def _reconstruct_from_history(self):
        """
        Parses previous conversational turns to restore short-term memory references.
        """
        if not self.history:
            return

        for turn in reversed(self.history):
            content = turn.get("content", "").lower()
            # Look for mentioned issue numbers
            import re
            m = re.search(r"issue\s+#?([0-9]+)", content)
            if m and not self.active_issue_number:
                self.active_issue_number = int(m.group(1))

            # Look for mentioned files
            f_match = re.search(r"(?:app/[a-zA-Z0-9_\-]+\.py|requirements\.txt|README\.md)", content)
            if f_match and not self.active_file:
                self.active_file = f_match.group(0)

            # Look for topics
            if "sql" in content or "sqli" in content:
                self.active_topic = "SQL Injection"
            elif "secret" in content or "key" in content:
                self.active_topic = "Hardcoded Secrets"
            elif "test" in content or "pytest" in content:
                self.active_topic = "Unit Tests"

            if self.active_issue_number and self.active_file:
                break


class ConversationManager:
    """
    Maintains Short-Term and Working Memory, performing Pronoun & Ellipsis Resolution.
    """

    @classmethod
    def resolve_context_and_pronouns(
        cls,
        classification: IntentClassificationResult,
        state: ConversationState,
        all_issues_count: int
    ) -> IntentClassificationResult:
        """
        Transforms ambiguous follow-up questions ('fix it', 'why is it vulnerable', 'the second one')
        into grounded semantic intents using short-term conversational context.
        """
        q_lower = classification.normalized_query.lower()

        # 1. Resolve Pronouns in Ambiguous Requests ("fix it", "resolve that", "how to solve it")
        if classification.intent == IntentEnum.AMBIGUOUS_REQUEST or "it" in q_lower.split() or "that" in q_lower.split():
            if any(w in q_lower for w in ["fix", "solve", "resolve", "address", "repair"]):
                target_num = classification.extracted_entities.get("issue_number") or state.active_issue_number or 1
                if 1 <= target_num <= all_issues_count:
                    classification.intent = IntentEnum.SOLVE_ONE_BY_ONE
                    classification.extracted_entities["issue_number"] = target_num
                    classification.confidence = 0.90

            elif any(w in q_lower for w in ["explain", "why", "what", "detail"]):
                if state.active_file or state.active_topic:
                    classification.intent = IntentEnum.EXPLANATION
                    classification.extracted_entities["target_file"] = state.active_file
                    classification.extracted_entities["target_topic"] = state.active_topic
                    classification.confidence = 0.88

        # 2. Update state with current turn's extracted entities
        if "issue_number" in classification.extracted_entities:
            state.active_issue_number = classification.extracted_entities["issue_number"]

        state.last_intent = classification.intent
        return classification
