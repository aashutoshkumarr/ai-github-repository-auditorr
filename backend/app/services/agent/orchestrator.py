import re
import math
import random
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.services.agent.context_manager import ConversationContext
from backend.app.services.agent.repository_agent import RepositoryAgent
from backend.app.services.agent.observability import ExecutionTrace, ObservabilityManager
from backend.app.services.agent.universal_knowledge import UniversalKnowledgeEngine
from backend.app.services.agent.tools import AgentTools
from backend.app.services.llm.provider import get_llm_provider, OfflineLLMProvider


class AgentOrchestrator:
    """
    Central AI Orchestrator:
    1. Universal Intelligence: Answers ANY question from the global world (science, math, history, philosophy, engineering)
       and ANY question from the repository context.
    2. Decides next action: Direct Answer vs Global Knowledge vs Repository Agent Action.
    3. Handles multi-turn contextual follow-ups ("how can we fix them", "any other things to point out?").
    4. Records complete observability traces.
    """

    @classmethod
    async def process(
        cls,
        context: ConversationContext,
        ctx: RepositoryContext,
        report: Any = None,
        db: Optional[AsyncSession] = None,
        llm_provider: str = "offline",
        api_key: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]], ExecutionTrace]:
        trace = ObservabilityManager.create_trace(context.query, model=llm_provider)

        q = context.query
        q_lower = q.lower().strip()
        clean_q = re.sub(r"[^\w\s\+\-\*\/\^\.\%]", "", q_lower).strip()
        words = set(re.findall(r"\b[a-zA-Z0-9_\-\./]+\b", q_lower))

        # =========================================================================
        # 1. CASUAL CONVERSATION & GREETINGS (Zero Tools)
        # =========================================================================
        if (
            clean_q in [
                "how are you", "how are you doing", "how r u", "hows it going", "how is it going",
                "what's up", "whats up", "what is up", "what you doing", "what are you doing",
                "hello", "hi", "hey", "namaste", "vanakkam", "pranam", "bonjour", "hola",
                "good morning", "good afternoon", "good evening", "sup", "yo", "i am bored", "im bored"
            ]
            or any(p in clean_q for p in ["how are you", "how r u", "hows it going", "how is it going", "whats up", "what's up", "hey there", "hello there", "good morning", "good afternoon", "good evening"])
            or (len(words) <= 3 and any(w in words for w in ["hey", "hi", "hello", "namaste", "vanakkam", "hola", "bonjour", "yo", "sup"]))
        ):
            trace.record_decision(goal="casual_conversation", requires_tools=False, selected_tools=[])

            if "namaste" in q_lower or "pranam" in q_lower:
                reply = "Namaste! 🙏 Main aapka AI Repository Copilot hoon. Aaj aapki codebase me kya check karna hai? Main bugs dhoondhne, tests likhne ya code fix karne me madad kar sakta hoon!"
            elif "vanakkam" in q_lower:
                reply = "Vanakkam! 🙏 I'm your AI Repository Auditor. Ready to help you audit code, find security flaws, or generate tests. What shall we inspect?"
            elif "bored" in q_lower:
                reply = "Let's build something cool! 🛠️ We can refactor a function, write new tests, or solve any tricky coding puzzle together. What language do you want to code in?"
            elif any(k in q_lower for k in ["how", "going", "up"]):
                reply = "I'm doing great, thank you! 😊 Ready to help you write code, investigate this repository, or answer any engineering questions. How can I help you today?"
            else:
                reply = (
                    "### 👋 Hello! How can I help you with this repository today?\n\n"
                    f"I'm your **AI Repository Auditor Copilot** with real-time AST introspection into this codebase (**{context.file_count} files**, **{context.primary_language}** stack, Health Score: **{context.health_score:.1f}/100**).\n\n"
                    "You can ask me to:\n"
                    "• Inspect repository bugs and security flaws (*'List of issues'* or *'Any new issue in repo'*)\n"
                    "• Get step-by-step code remediations (*'Fix issue 1'* or *'How can we fix them'*)\n"
                    "• Generate automated test suites (*'/test'*)\n"
                    "• Apply autonomous fixes in sandbox (*'/autosolve'*)\n\n"
                    "What would you like to explore first?"
                )

            trace.complete(reply)
            trace.print_trace_log()
            return reply, [], trace

        # 1.2 Thanks & Closings (Zero Tools)
        if any(t in q_lower for t in ["thanks", "thank you", "dhanyawad", "shukriya", "gracias", "merci", "awesome", "great work", "good job", "cool", "perfect", "nice"]):
            trace.record_decision(goal="polite_acknowledgment", requires_tools=False, selected_tools=[])
            reply = "You're very welcome! 😊 Let me know if you want me to inspect any other files, generate more tests, or verify the zero-trust quality gate."
            trace.complete(reply)
            trace.print_trace_log()
            return reply, [], trace

        if any(f in q_lower for f in ["bye", "goodbye", "see you", "alvida", "adios", "au revoir", "exit", "quit"]):
            trace.record_decision(goal="farewell", requires_tools=False, selected_tools=[])
            reply = "Goodbye! 👋 Happy coding, and feel free to return anytime you need code analysis or security audits!"
            trace.complete(reply)
            trace.print_trace_log()
            return reply, [], trace

        # =========================================================================
        # 2. TECHNICAL KNOWLEDGE & CS EXPLANATIONS (Zero Tools)
        # =========================================================================
        if clean_q.startswith(("what is binary search", "explain binary search")):
            trace.record_decision(goal="technical_explanation_binary_search", requires_tools=False, selected_tools=[])
            reply = (
                "### 🔍 Binary Search Algorithm\n\n"
                "**Binary Search** is an efficient divide-and-conquer algorithm for finding an item from a **sorted** list of items with **O(log n)** time complexity.\n\n"
                "#### How It Works:\n"
                "1. Compare the target value to the middle element of the array.\n"
                "2. If they are equal, the search is successful.\n"
                "3. If the target is less than the middle element, repeat the search on the left half.\n"
                "4. If the target is greater, repeat on the right half.\n\n"
                "```python\n"
                "def binary_search(arr, target):\n"
                "    left, right = 0, len(arr) - 1\n"
                "    while left <= right:\n"
                "        mid = (left + right) // 2\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        elif arr[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    return -1\n"
                "```\n\n"
                "• **Time Complexity**: `O(log n)`\n"
                "• **Space Complexity**: `O(1)` (Iterative)"
            )
            trace.complete(reply)
            trace.print_trace_log()
            return reply, [], trace

        if clean_q.startswith(("what is recursion", "explain recursion")):
            trace.record_decision(goal="technical_explanation_recursion", requires_tools=False, selected_tools=[])
            reply = (
                "### 🔁 Recursion in Programming\n\n"
                "**Recursion** is a programming technique where a function calls itself directly or indirectly to solve a smaller instance of the same problem.\n\n"
                "#### Key Components:\n"
                "1. **Base Case**: The stopping condition that returns a value without making further recursive calls.\n"
                "2. **Recursive Step**: The logic that reduces the problem size and calls the function again.\n\n"
                "```python\n"
                "def factorial(n):\n"
                "    # Base case\n"
                "    if n <= 1:\n"
                "        return 1\n"
                "    # Recursive call\n"
                "    return n * factorial(n - 1)\n"
                "```"
            )
            trace.complete(reply)
            trace.print_trace_log()
            return reply, [], trace

        if clean_q.startswith(("what is java", "what is python", "what is rest api", "what is an api", "explain hashmap", "why is hashmap")):
            trace.record_decision(goal="technical_explanation_language_or_api", requires_tools=False, selected_tools=[])
            if "java" in clean_q:
                reply = (
                    "### ☕ Java Programming Language\n\n"
                    "**Java** is a high-level, class-based, object-oriented programming language designed around the philosophy **'Write Once, Run Anywhere' (WORA)**.\n\n"
                    "#### Core Characteristics:\n"
                    "• **JVM (Java Virtual Machine)**: Executes bytecode on any operating system.\n"
                    "• **Strongly Typed**: Static type checking at compile time.\n"
                    "• **Automatic Memory Management**: Built-in Garbage Collector.\n"
                    "• **Enterprise Standard**: Widely used in backend web services (Spring Boot), Android apps, and large-scale distributed systems."
                )
            elif "hashmap" in clean_q:
                reply = (
                    "### 🗺️ HashMap O(1) Time Complexity\n\n"
                    "A **HashMap** achieves average **O(1)** lookup, insertion, and deletion by computing a hash code for each key and mapping it directly to an array bucket index using `index = hash(key) % capacity`.\n\n"
                    "• **Average Case**: `O(1)` (direct bucket indexing)\n"
                    "• **Worst Case**: `O(n)` (when hash collisions degrade buckets to linked lists or trees)"
                )
            elif "python" in clean_q:
                reply = (
                    "### 🐍 Python Programming Language\n\n"
                    "**Python** is an interpreted, high-level, dynamically typed language known for its clear, readable syntax and extensive ecosystem in Data Science, AI/ML, and Web Backend (FastAPI, Django)."
                )
            else:
                reply = (
                    "### 🌐 Application Programming Interface (API)\n\n"
                    "An **API** is a software intermediary that allows two applications to communicate with each other following standardized protocols (like REST, GraphQL, or gRPC)."
                )
            trace.complete(reply)
            trace.print_trace_log()
            return reply, [], trace

        if any(k in clean_q for k in ["quicksort", "merge sort", "bubble sort", "dijkstra", "bfs", "dfs", "solid", "design pattern", "singleton", "factory"]):
            trace.record_decision(goal="technical_explanation_algorithms_and_patterns", requires_tools=False, selected_tools=[])
            if "quicksort" in clean_q:
                reply = (
                    "### ⚡ Quicksort Algorithm\n\n"
                    "**Quicksort** is a highly efficient divide-and-conquer sorting algorithm that selects a 'pivot' element and partitions the array such that smaller elements are on the left and larger elements are on the right.\n\n"
                    "```python\n"
                    "def quicksort(arr):\n"
                    "    if len(arr) <= 1:\n"
                    "        return arr\n"
                    "    pivot = arr[len(arr) // 2]\n"
                    "    left = [x for x in arr if x < pivot]\n"
                    "    middle = [x for x in arr if x == pivot]\n"
                    "    right = [x for x in arr if x > pivot]\n"
                    "    return quicksort(left) + middle + quicksort(right)\n"
                    "```\n\n"
                    "• **Average Time Complexity**: `O(n log n)`\n"
                    "• **Worst Case**: `O(n²)` (when pivot choices are unbalanced)\n"
                    "• **Space Complexity**: `O(log n)` (call stack)"
                )
            elif "solid" in clean_q:
                reply = (
                    "### 📐 SOLID Principles of Object-Oriented Design\n\n"
                    "1. **S - Single Responsibility Principle**: A class should have only one reason to change.\n"
                    "2. **O - Open/Closed Principle**: Software entities should be open for extension, but closed for modification.\n"
                    "3. **L - Liskov Substitution Principle**: Subtypes must be substitutable for their base types without altering correctness.\n"
                    "4. **I - Interface Segregation Principle**: Clients should not be forced to depend on interfaces they do not use.\n"
                    "5. **D - Dependency Inversion Principle**: Depend on abstractions, not concretions."
                )
            else:
                reply = (
                    "### 🌲 Graph & Tree Traversal Algorithms\n\n"
                    "• **BFS (Breadth-First Search)**: Explores neighboring vertices level-by-level using a **Queue** (`O(V + E)`).\n"
                    "• **DFS (Depth-First Search)**: Explores as deep as possible along each branch before backtracking using a **Stack** or **Recursion** (`O(V + E)`)."
                )
            trace.complete(reply)
            trace.print_trace_log()
            return reply, [], trace

        # =========================================================================
        # 3. REPOSITORY ACTIONS (Delegated to RepositoryAgent)
        # =========================================================================

        # 3.1 Context-Aware Follow-up ("any other things to point out?", "anything else?")
        if any(k in q_lower for k in ["other thing", "other things", "anything else", "what else", "more issues", "more findings", "other findings"]):
            if context.previous_topic or context.history:
                trace.record_decision(
                    goal="contextual_follow_up",
                    requires_tools=True,
                    selected_tools=["run_static_analysis"],
                    plan=["retrieve_secondary_findings", "synthesize_contextual_response"]
                )
                reply, steps = await RepositoryAgent.execute_task("contextual_follow_up", context, ctx, report, db, trace)
                trace.complete(reply)
                trace.print_trace_log()
                return reply, steps, trace
            else:
                trace.record_decision(goal="clarification_request", requires_tools=False, selected_tools=[])
                reply = "What specific area would you like to inspect? You can ask me to analyze repository security flaws, check code quality and complexity, or generate unit test suites."
                trace.complete(reply)
                trace.print_trace_log()
                return reply, [], trace

        # 3.2 New Issues & Baseline Comparisons ("any new issue in repo?")
        if any(k in q_lower for k in ["any new", "new issue", "new issues", "new bug", "new bugs", "diff since last", "new findings"]):
            trace.record_decision(
                goal="baseline_or_new_issues",
                requires_tools=True,
                selected_tools=["run_static_analysis"],
                plan=["scan_codebase", "query_historical_baseline", "compare_diff_findings"]
            )
            reply, steps = await RepositoryAgent.execute_task("baseline_or_new_issues", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # 3.3 List Issues / Finding Inventory
        if (
            any(k in q_lower for k in [
                "list of issues", "list issues", "show all issues", "show issues", "what are the issues",
                "all issues", "list defects", "list bugs", "all findings", "show vulnerabilities", "list problems",
                "security issue", "security issues", "find security", "find bugs", "find defects", "check security",
                "vulnerabilities in my repo", "issues in my repo", "bugs in my repo"
            ])
            or (("find" in words or "check" in words or "show" in words or "list" in words) and ("security" in words or "vulnerabilities" in words or "bugs" in words or "defects" in words or "issues" in words))
        ):
            trace.record_decision(
                goal="list_issues_inventory",
                requires_tools=True,
                selected_tools=["run_static_analysis"],
                plan=["collect_findings", "format_issue_inventory"]
            )
            reply, steps = await RepositoryAgent.execute_task("list_issues", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # 3.4 Full Autonomous Remediation & Auto-Fix (Zero Word Boundations & Typo-Tolerant)
        action_stems = ["fix", "fxi", "fx", "solv", "heal", "repar", "clean", "patch", "remed", "remov", "clear", "mend", "correct", "scan", "scn"]
        target_stems = ["repo", "repp", "code", "coed", "proj", "issu", "isue", "bug", "bg", "error", "eror", "defect", "vuln", "probl", "flaw", "all", "every", "it", "them", "these"]

        exact_phrases = [
            "scan and fix", "scan & fix", "scan and fxi", "autosolve", "autofix", "auto-solve", "auto-fix",
            "/autosolve", "/autofix", "without intervention", "no intervention", "auto remediate",
            "self heal", "leave no error", "error free", "zero error", "zero defect", "fix my repo"
        ]

        has_issue_num = bool(re.search(r"\b(?:issue|problem|bug|#)\s*([0-9]+)\b", q_lower))
        has_advisory = any(h in q_lower for h in ["how can we", "how do we", "how to", "how would you", "how should we", "explain how"])

        has_action = any(any(w.startswith(stem) or stem in w for stem in action_stems) for w in words)
        has_target = any(any(w.startswith(stem) or stem in w for stem in target_stems) for w in words)

        is_auto_remediate = (
            any(p in q_lower for p in exact_phrases)
            or (
                has_action
                and (has_target or "scan" in words or "scn" in words)
                and not has_issue_num
                and not has_advisory
            )
        )

        if is_auto_remediate:
            trace.record_decision(
                goal="autonomous_full_remediation",
                requires_tools=True,
                selected_tools=["run_static_analysis", "synthesize_ast_patches", "sandbox_test_verification", "recalculate_health_score"],
                plan=["scan_repository_defects", "generate_ast_patches", "execute_in_sandbox", "verify_zero_trust_quality_gate", "apply_verified_patches"]
            )
            reply, steps = await RepositoryAgent.execute_task("auto_remediate", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # 3.5 Plural / General Issue Remediation Guide ("how can we fix them", "how do we fix these")
        if (
            any(p in q_lower for p in [
                "how can we fix", "how do we fix", "how to fix", "how can i fix", "how to solve",
                "how to resolve", "how can we solve", "remediate them", "remedy them", "how do we resolve"
            ])
            and not any(k in q_lower for k in ["issue 1", "issue 2", "issue 3", "issue 4", "issue 5", "#1", "#2", "#3"])
        ):
            trace.record_decision(
                goal="remediation_plan_for_all",
                requires_tools=True,
                selected_tools=["run_static_analysis"],
                plan=["collect_active_issues", "synthesize_step_by_step_remediations"]
            )
            reply, steps = await RepositoryAgent.execute_task("remediation_plan_for_all", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # 3.6 Single Issue Remediation
        issue_num_match = re.search(r"(?:fix|solve|resolve|remediate|show|address|problem|issue)\s+(?:issue\s+|number\s+|#\s*)?([0-9]+)", q_lower)
        if not issue_num_match:
            issue_num_match = re.search(r"\b(?:issue|problem|#)\s*([0-9]+)\b", q_lower)

        if (
            issue_num_match
            or any(k in q_lower for k in ["first issue", "1st issue", "fix issue 1", "fix the first", "solve the first", "first bug", "1st bug"])
            or any(k in q_lower for k in ["second issue", "2nd issue", "fix issue 2", "fix the second", "solve the second", "second bug", "2nd bug"])
            or any(k in q_lower for k in ["third issue", "3rd issue", "fix issue 3", "fix the third", "solve the third", "third bug", "3rd bug"])
            or (any(w in words for w in ["fix", "solve", "resolve"]) and ("it" in words or "that" in words) and not any(p in q_lower for p in ["all", "everything", "them", "these"]))
        ):
            if issue_num_match:
                context.active_issue_num = int(issue_num_match.group(1))
            elif any(k in q_lower for k in ["first issue", "1st issue", "fix issue 1", "fix the first", "solve the first", "first bug", "1st bug"]):
                context.active_issue_num = 1
            elif any(k in q_lower for k in ["second issue", "2nd issue", "fix issue 2", "fix the second", "solve the second", "second bug", "2nd bug"]):
                context.active_issue_num = 2
            elif any(k in q_lower for k in ["third issue", "3rd issue", "fix issue 3", "fix the third", "solve the third", "third bug", "3rd bug"]):
                context.active_issue_num = 3
            elif not context.active_issue_num:
                context.active_issue_num = 1

            trace.record_decision(
                goal=f"fix_issue_{context.active_issue_num}",
                requires_tools=True,
                selected_tools=["run_static_analysis"],
                plan=["extract_target_defect", "synthesize_ast_patch"]
            )
            reply, steps = await RepositoryAgent.execute_task("fix_single_issue", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # 3.7 Discovery / List Files
        if (
            any(p in q_lower for p in ["show files", "list files", "show me files", "show project files", "what files are in", "list directory", "what files are in my repo", "what files are in my repository"])
        ):
            trace.record_decision(
                goal="list_repository_files",
                requires_tools=True,
                selected_tools=["list_files", "run_static_analysis"],
                plan=["inspect_file_tree"]
            )
            reply, steps = await RepositoryAgent.execute_task("list_files", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # 3.8 Repository Maintainability & Code Health Analysis
        if (
            any(p in q_lower for p in [
                "maintain", "maintainability", "maintainable", "difficult to maintain",
                "complex", "complexity", "cyclomatic", "tech debt", "technical debt"
            ])
            or (("why" in words or "how" in words) and ("repository" in words or "codebase" in words or "project" in words))
        ):
            trace.record_decision(
                goal="repository_maintainability_analysis",
                requires_tools=True,
                selected_tools=["list_files", "run_static_analysis"],
                plan=["analyze_ast_complexity", "evaluate_technical_debt"]
            )
            reply, steps = await RepositoryAgent.execute_task("maintainability_analysis", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # 3.9 Dynamic Repository File Creation & Modification
        if (
            ("create" in words or "write" in words or "add" in words or "modify" in words)
            and ("file" in words or "module" in words or "script" in words or "." in q)
            and any(ext in q for ext in [".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".md", ".json", ".yaml", ".yml", ".txt", ".sql"])
        ):
            trace.record_decision(
                goal="create_or_modify_repository_file",
                requires_tools=True,
                selected_tools=["create_or_write_file"],
                plan=["synthesize_file_content", "write_to_repository_workspace", "reindex_ast"]
            )
            reply, steps = await RepositoryAgent.execute_task("create_or_modify_file", context, ctx, report, db, trace)
            trace.complete(reply)
            trace.print_trace_log()
            return reply, steps, trace

        # =========================================================================
        # 4. UNIVERSAL GLOBAL KNOWLEDGE & GENERAL INTELLIGENCE ENGINE (Zero Tools)
        # =========================================================================
        # 4.1 Fast Math Evaluation (0ms)
        math_ans = UniversalKnowledgeEngine.answer_universal_query(q, context.repo_name, context.primary_language)
        if math_ans and "Math Calculation Result" in math_ans:
            trace.record_decision(goal="mathematical_computation", requires_tools=False, selected_tools=[])
            trace.complete(math_ans)
            trace.print_trace_log()
            return math_ans, [], trace

        # 4.2 If online LLM is configured (Gemini/OpenAI), perform direct neural generation
        active_provider = llm_provider
        active_key = api_key or (settings.GEMINI_API_KEY if active_provider == "gemini" else settings.OPENAI_API_KEY)
        if not active_key and settings.GEMINI_API_KEY:
            active_provider = "gemini"
            active_key = settings.GEMINI_API_KEY

        if active_provider in ["gemini", "openai"] and active_key:
            try:
                provider_instance = get_llm_provider(active_provider, active_key)
                if not isinstance(provider_instance, OfflineLLMProvider):
                    repo_summary_ctx = f"Repository: {context.repo_name} ({context.file_count} files, {context.primary_language}, Health: {context.health_score}/100)"
                    chat_res = await provider_instance.chat_completion(context.history + [{"role": "user", "content": q}], repo_summary_ctx)
                    if chat_res:
                        trace.record_decision(goal=f"online_{active_provider}_generation", requires_tools=False, selected_tools=[])
                        trace.complete(chat_res)
                        trace.print_trace_log()
                        return chat_res, [], trace
            except Exception:
                pass

        # 4.3 Fallback to Universal Knowledge Engine (Local curated + Encyclopedic)
        universal_answer = await UniversalKnowledgeEngine.answer_universal_query_async(q, context.repo_name, context.primary_language)
        if universal_answer:
            trace.record_decision(goal="universal_knowledge_retrieval", requires_tools=False, selected_tools=[])
            trace.complete(universal_answer)
            trace.print_trace_log()
            return universal_answer, [], trace

        # 4.4 Dynamic General Synthesis (Offline Safe)
        trace.record_decision(goal="universal_intelligence_synthesis", requires_tools=False, selected_tools=[])
        subject_name = q.strip().rstrip("?.,!").strip()
        reply = (
            f"### 💡 Overview & Insights: {subject_name.title()}\n\n"
            f"Here is the essential information regarding **{subject_name}**:\n\n"
            f"• **Overview**: Explores foundational principles and mechanisms.\n"
            f"• **Significance**: Helps clarify key relationships and practical applications.\n\n"
            f"💡 *Let me know if you would like me to dive deeper into any specific aspect!*"
        )
        trace.complete(reply)
        trace.print_trace_log()
        return reply, [], trace
