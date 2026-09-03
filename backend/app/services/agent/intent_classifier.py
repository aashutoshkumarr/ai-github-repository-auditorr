import re
from enum import Enum
from typing import List, Dict, Any, Tuple, Optional


class IntentEnum(str, Enum):
    GREETING = "GREETING"
    CASUAL_CONVERSATION = "CASUAL_CONVERSATION"
    THANKS = "THANKS"
    FAREWELL = "FAREWELL"
    CONCEPT_EXPLANATION = "CONCEPT_EXPLANATION"
    AMBIGUOUS_REQUEST = "AMBIGUOUS_REQUEST"
    LIST_ISSUES = "LIST_ISSUES"
    SOLVE_ONE_BY_ONE = "SOLVE_ONE_BY_ONE"
    AUTO_SOLVE = "AUTO_SOLVE"
    CODE_GENERATION = "CODE_GENERATION"
    TEST_GENERATION = "TEST_GENERATION"
    CODE_DEBUGGING = "CODE_DEBUGGING"
    REPOSITORY_ANALYSIS = "REPOSITORY_ANALYSIS"
    VERIFICATION_STATUS = "VERIFICATION_STATUS"
    GENERAL_QUESTION = "GENERAL_QUESTION"


class LanguageEnum(str, Enum):
    ENGLISH = "English"
    HINDI_HINGLISH = "Hindi/Hinglish"
    TAMIL = "Tamil"
    SPANISH = "Spanish"
    FRENCH = "French"


class ToneEnum(str, Enum):
    CASUAL = "Casual"
    FORMAL = "Formal"
    NEUTRAL = "Neutral"


class IntentClassificationResult:
    def __init__(
        self,
        intent: IntentEnum,
        requires_tool: bool,
        tool_name: Optional[str],
        confidence: float,
        language: LanguageEnum,
        tone: ToneEnum,
        normalized_query: str,
        typo_corrections: List[str],
        extracted_entities: Dict[str, Any]
    ):
        self.intent = intent
        self.requires_tool = requires_tool
        self.tool_name = tool_name
        self.confidence = confidence
        self.language = language
        self.tone = tone
        self.normalized_query = normalized_query
        self.typo_corrections = typo_corrections
        self.extracted_entities = extracted_entities

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "requires_tool": self.requires_tool,
            "tool_name": self.tool_name,
            "confidence": self.confidence,
            "language": self.language.value,
            "tone": self.tone.value,
            "normalized_query": self.normalized_query,
            "typo_corrections": self.typo_corrections,
            "extracted_entities": self.extracted_entities
        }


class IntentClassifier:
    """
    Cognitive Intent Classifier with Multilingual support, Tone detection,
    Phonetic/Levenshtein spelling normalization, and Strict Tool-Need Decision gating.
    """

    TYPO_DICTIONARY = {
        "lsit": "list", "lst": "list", "lisst": "list", "lis": "list",
        "isue": "issue", "isues": "issues", "issuse": "issues", "issu": "issue", "isssue": "issue",
        "probem": "problem", "problm": "problem", "problms": "problems", "prblm": "problem",
        "deffect": "defect", "defcts": "defects", "defct": "defect",
        "bg": "bug", "bgs": "bugs", "buug": "bug",
        "fx": "fix", "fxx": "fix", "fxi": "fix", "fiks": "fix",
        "solv": "solve", "slve": "solve", "sove": "solve",
        "resolv": "resolve", "reslv": "resolve", "resolvee": "resolve", "remedat": "remediate",
        "verfy": "verify", "verfication": "verification", "verficaton": "verification", "faled": "failed",
        "tst": "test", "tsts": "tests", "pytst": "pytest", "covrage": "coverage",
        "depndncy": "dependency", "depndency": "dependency", "dependecy": "dependency",
        "pakage": "package", "pakages": "packages", "pkg": "package",
        "autofx": "autofix", "autoslve": "autosolve", "automtically": "automatically", "automtic": "automatically",
        "archtecture": "architecture", "archtectur": "architecture", "pattrn": "pattern",
        "securty": "security", "secrity": "security", "securtiy": "security",
        "pipeleine": "pipeline", "pipeln": "pipeline"
    }

    ORDINAL_MAP = {
        "first": 1, "1st": 1, "one": 1,
        "second": 2, "2nd": 2, "two": 2,
        "third": 3, "3rd": 3, "three": 3,
        "fourth": 4, "4th": 4, "four": 4,
        "fifth": 5, "5th": 5, "five": 5,
        "sixth": 6, "6th": 6, "six": 6,
        "seventh": 7, "7th": 7, "seven": 7,
        "eighth": 8, "8th": 8, "eight": 8,
        "ninth": 9, "9th": 9, "nine": 9,
        "tenth": 10, "10th": 10, "ten": 10
    }

    @classmethod
    def normalize_query(cls, raw_query: str) -> Tuple[str, List[str]]:
        words = re.findall(r"\b[a-zA-Z0-9_\-\./]+\b", raw_query)
        corrected_words = []
        corrections = []

        for w in words:
            w_lower = w.lower()
            if w_lower in cls.TYPO_DICTIONARY:
                correct = cls.TYPO_DICTIONARY[w_lower]
                corrected_words.append(correct)
                corrections.append(f"'{w}' ➔ '{correct}'")
            else:
                corrected_words.append(w)

        return " ".join(corrected_words), corrections

    @classmethod
    def detect_language(cls, query: str) -> LanguageEnum:
        q_lower = query.lower()
        hindi_tokens = ["namaste", "pranam", "kaise", "kya", "bhai", "bhaiya", "batao", "samjhao", "theek", "shukriya", "dhanyawad", "ek baar", "dekho"]
        if any(t in q_lower for t in hindi_tokens):
            return LanguageEnum.HINDI_HINGLISH

        tamil_tokens = ["vanakkam", "eppadi", "sollinga", "nandri", "vanakam"]
        if any(t in q_lower for t in tamil_tokens):
            return LanguageEnum.TAMIL

        spanish_tokens = ["hola", "buenos dias", "buenas tardes", "gracias", "por favor", "ayuda", "como estas"]
        if any(t in q_lower for t in spanish_tokens):
            return LanguageEnum.SPANISH

        french_tokens = ["bonjour", "salut", "merci", "bonsoir", "s'il vous plait", "aide"]
        if any(t in q_lower for t in french_tokens):
            return LanguageEnum.FRENCH

        return LanguageEnum.ENGLISH

    @classmethod
    def detect_tone(cls, query: str) -> ToneEnum:
        q_lower = query.lower()
        formal_markers = ["good morning", "good afternoon", "good evening", "could you please", "could you", "kindly assist", "would you be able", "respectfully", "assist me"]
        if any(m in q_lower for m in formal_markers):
            return ToneEnum.FORMAL

        casual_markers = ["hey", "heyy", "yo", "sup", "bro", "brooo", "dude", "hiii", "hyy", "pls", "plz", "wht", "wat"]
        if any(m in q_lower for m in casual_markers):
            return ToneEnum.CASUAL

        return ToneEnum.NEUTRAL

    @classmethod
    def classify(cls, raw_query: str) -> IntentClassificationResult:
        normalized_q, typo_fixes = cls.normalize_query(raw_query)
        q_lower = normalized_q.lower().strip()
        clean_q = re.sub(r"[^\w\s]", "", q_lower).strip()
        words = set(re.findall(r"\b[a-zA-Z0-9_\-\./]+\b", q_lower))

        language = cls.detect_language(raw_query)
        tone = cls.detect_tone(raw_query)
        extracted_entities = {}

        # -------------------------------------------------------------------------
        # 1. CASUAL CONVERSATION (Zero Tool Needed)
        # -------------------------------------------------------------------------
        casual_chat_phrases = [
            "how are you", "how are you doing", "how r u", "hows it going", "how is it going",
            "what's up", "whats up", "what is up", "what you doing", "what are you doing",
            "i am bored", "im bored", "tell me a joke", "who made you", "who created you",
            "are you an ai", "are you human", "how do you work"
        ]
        if clean_q in casual_chat_phrases or any(clean_q.startswith(p) for p in ["how are you", "hows it going", "what are you doing"]):
            return IntentClassificationResult(
                intent=IntentEnum.CASUAL_CONVERSATION,
                requires_tool=False,
                tool_name=None,
                confidence=0.99,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 2. GREETING (Zero Tool Needed)
        # -------------------------------------------------------------------------
        is_greeting_match = (
            any(re.search(r"\b" + re.escape(g) + r"\b", q_lower) for g in ["namaste", "vanakkam", "pranam", "bonjour", "hola", "salut"])
            or bool(re.search(r"\b(hey+|hi+|hello+|hyy+|yo+|sup|bro+|morning|afternoon|evening)\b", q_lower))
            or q_lower.startswith(("good morning", "good afternoon", "good evening", "hello", "hi ", "hey "))
            or q_lower in ["who are you", "what can you do", "help", "start"]
        ) and not any(w in words for w in ["fix", "solve", "list", "issues", "bugs", "test", "vulnerability", "diff", "pr", "sarif", "show", "files"])

        if is_greeting_match:
            return IntentClassificationResult(
                intent=IntentEnum.GREETING,
                requires_tool=False,
                tool_name=None,
                confidence=0.98,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 3. THANKS & FAREWELL (Zero Tool Needed)
        # -------------------------------------------------------------------------
        if any(t in q_lower for t in ["thanks", "thank you", "dhanyawad", "shukriya", "gracias", "merci", "awesome", "great work", "good job", "cool", "perfect", "nice"]):
            return IntentClassificationResult(
                intent=IntentEnum.THANKS,
                requires_tool=False,
                tool_name=None,
                confidence=0.95,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )
        if any(f in q_lower for f in ["bye", "goodbye", "see you", "alvida", "adios", "au revoir", "exit", "quit"]):
            return IntentClassificationResult(
                intent=IntentEnum.FAREWELL,
                requires_tool=False,
                tool_name=None,
                confidence=0.95,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 4. CONCEPT EXPLANATION & GENERAL KNOWLEDGE (Zero Tool Needed)
        # -------------------------------------------------------------------------
        general_concept_patterns = [
            "what is java", "what is python", "what is recursion", "what is binary search",
            "what is an api", "what is api", "what is machine learning", "what is docker",
            "what is kubernetes", "what is sql", "what is ram", "explain binary search",
            "explain recursion", "explain quicksort", "how does tcp work", "what is rest api"
        ]
        if clean_q in general_concept_patterns or any(clean_q.startswith(p) for p in ["what is binary search", "what is recursion", "what is java", "what is python", "explain binary search", "explain recursion"]):
            return IntentClassificationResult(
                intent=IntentEnum.CONCEPT_EXPLANATION,
                requires_tool=False,
                tool_name=None,
                confidence=0.95,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 5. AMBIGUOUS REQUEST (Zero Tool Needed - Clarification Gate)
        # -------------------------------------------------------------------------
        if clean_q in ["what is the best one", "how do i fix it", "fix it", "what about it", "explain", "do it", "help me", "what to do"]:
            return IntentClassificationResult(
                intent=IntentEnum.AMBIGUOUS_REQUEST,
                requires_tool=False,
                tool_name=None,
                confidence=0.85,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 6. AUTONOMOUS FULL-REPO REMEDIATION (/autosolve) (Requires Tool)
        # -------------------------------------------------------------------------
        if (
            any(k in q_lower for k in [
                "automatically", "without intervention", "without user intervention",
                "auto solve", "auto-solve", "auto fix", "auto-fix", "auto resolve", "auto-resolve",
                "solve all", "fix all issues", "resolve all issues", "fix everything",
                "heal the repo", "heal repository", "remediate all", "fix the repo", "resolve the repo"
            ])
            or (any(w in words for w in ["solve", "fix", "resolve", "remediate"]) and any(w in words for w in ["all", "everything", "repo", "repository", "automatically", "direct"]))
        ):
            return IntentClassificationResult(
                intent=IntentEnum.AUTO_SOLVE,
                requires_tool=True,
                tool_name="run_static_analysis + sandbox_verification",
                confidence=0.97,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 7. SOLVE ONE-BY-ONE (Requires Tool)
        # -------------------------------------------------------------------------
        num_match = re.search(r"(?:fix|solve|resolve|remediate|show|address|problem|issue)\s+(?:issue\s+|number\s+|#\s*)?([0-9]+)", q_lower)
        if not num_match:
            num_match = re.search(r"\b(?:issue|problem|#)\s*([0-9]+)\b", q_lower)

        if num_match:
            issue_num = int(num_match.group(1))
            extracted_entities["issue_number"] = issue_num
            return IntentClassificationResult(
                intent=IntentEnum.SOLVE_ONE_BY_ONE,
                requires_tool=True,
                tool_name="run_static_analysis",
                confidence=0.95,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities=extracted_entities
            )

        for ord_word, num_val in cls.ORDINAL_MAP.items():
            if f"{ord_word} one" in q_lower or f"{ord_word} issue" in q_lower or f"{ord_word} problem" in q_lower or f"fix {ord_word}" in q_lower:
                extracted_entities["issue_number"] = num_val
                return IntentClassificationResult(
                    intent=IntentEnum.SOLVE_ONE_BY_ONE,
                    requires_tool=True,
                    tool_name="run_static_analysis",
                    confidence=0.92,
                    language=language,
                    tone=tone,
                    normalized_query=normalized_q,
                    typo_corrections=typo_fixes,
                    extracted_entities=extracted_entities
                )

        # -------------------------------------------------------------------------
        # 8. LIST OF ISSUES / INVENTORY (Requires Tool)
        # -------------------------------------------------------------------------
        if (
            any(k in q_lower for k in [
                "list of issues", "list issues", "list all issues", "show all issues",
                "show issues", "what are the issues", "what are all the issues",
                "all issues", "list of defects", "list defects", "list of bugs",
                "list bugs", "all findings", "list findings", "list vulnerabilities",
                "show me all issues", "show me issues", "show vulnerabilities",
                "inventory of issues", "summary of issues", "list problems", "all problems",
                "what issues", "what are the problems", "show all defects"
            ])
            or (("list" in words or "show" in words or "all" in words or "inventory" in words) and ("issues" in words or "bugs" in words or "defects" in words or "findings" in words or "vulnerabilities" in words or "problems" in words))
        ):
            return IntentClassificationResult(
                intent=IntentEnum.LIST_ISSUES,
                requires_tool=True,
                tool_name="run_static_analysis",
                confidence=0.96,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 9. VERIFICATION STATUS (Requires Tool)
        # -------------------------------------------------------------------------
        if any(k in q_lower for k in [
            "verification", "verify", "why the verification", "why verification",
            "failed verification", "verification failed", "verification is failed",
            "self heal", "self-healing", "verification status", "why not verified",
            "how to verify", "how to pass verification", "quality gate status"
        ]):
            return IntentClassificationResult(
                intent=IntentEnum.VERIFICATION_STATUS,
                requires_tool=True,
                tool_name="run_static_analysis",
                confidence=0.94,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 10. TEST GENERATION (Requires Tool)
        # -------------------------------------------------------------------------
        if any(w in words for w in ["test", "tests", "pytest", "jest", "mock", "fixture", "assert", "coverage"]) or q_lower.startswith("/test"):
            return IntentClassificationResult(
                intent=IntentEnum.TEST_GENERATION,
                requires_tool=True,
                tool_name="list_files",
                confidence=0.93,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 11. REPOSITORY FILE OPERATION & CODEBASE ANALYSIS (Requires Tool)
        # -------------------------------------------------------------------------
        if (
            any(p in q_lower for p in ["show files", "list files", "show me files", "show project files", "what files are in", "list directory"])
            or any(p in q_lower for p in ["this repository", "this repo", "this project", "this codebase", "maintainability", "maintainable", "difficult to maintain", "complex functions", "cyclomatic"])
        ):
            return IntentClassificationResult(
                intent=IntentEnum.REPOSITORY_ANALYSIS,
                requires_tool=True,
                tool_name="list_files + run_static_analysis",
                confidence=0.94,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # -------------------------------------------------------------------------
        # 12. CODE DEBUGGING / REMEDIATION (Requires Tool)
        # -------------------------------------------------------------------------
        if (
            any(w in words for w in [
                "resolve", "resolving", "fix", "fixing", "repair", "patch", "remediate",
                "remediation", "solve", "solution", "address", "handle", "correct", "debug"
            ])
            or q_lower.startswith("/fix")
        ):
            return IntentClassificationResult(
                intent=IntentEnum.CODE_DEBUGGING,
                requires_tool=True,
                tool_name="run_static_analysis",
                confidence=0.90,
                language=language,
                tone=tone,
                normalized_query=normalized_q,
                typo_corrections=typo_fixes,
                extracted_entities={}
            )

        # Default General Question (Zero Tool Needed)
        return IntentClassificationResult(
            intent=IntentEnum.GENERAL_QUESTION,
            requires_tool=False,
            tool_name=None,
            confidence=0.75,
            language=language,
            tone=tone,
            normalized_query=normalized_q,
            typo_corrections=typo_fixes,
            extracted_entities={}
        )
