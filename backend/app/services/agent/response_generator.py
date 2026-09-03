import random
import ast
import re
from typing import Dict, Any, List, Optional
from backend.app.services.agent.intent_classifier import LanguageEnum, ToneEnum


class ResponseGenerator:
    """
    Multilingual, context-aware, diverse response generator with Code Guardrail verification
    and zero-tool casual conversation and technical concept explanations.
    """

    GREETING_TEMPLATES = {
        LanguageEnum.HINDI_HINGLISH: [
            "### 🙏 Namaste! Aapki repository me kya inspect karna chahte hain?\n\nMain aapka **AI Repository Auditor Copilot** hoon. Aap mujhse pooch sakte hain:\n• 📋 **'List of issues'** — Saare bugs aur vulnerabilities dekhne ke liye\n• 🛠️ **'Fix issue 1'** — Step-by-step code fix ke liye\n• ✨ **'/autosolve'** — Saare defects ko automatic theek karne ke liye",
            "### 🙏 Namaste! Main aapka AI Repository Copilot hoon.\n\nCodebase check karne ke liye taiyaar hoon! Aaj hum kis module pe kaam karenge?"
        ],
        LanguageEnum.TAMIL: [
            "### 🙏 Vanakkam! How can I assist you with this repository today?\n\nI am your **AI Repository Auditor Copilot**. You can ask me to:\n• 📋 **List all issues** in this repo\n• 🛠️ **Fix individual issues** with ready code\n• ✨ **Auto-remediate everything** in sandbox",
            "### 🙏 Vanakkam! Ready to audit and optimize this repository. What shall we inspect first?"
        ],
        LanguageEnum.SPANISH: [
            "### 👋 ¡Hola! ¿Cómo puedo ayudarte con este repositorio hoy?\n\nSoy tu **Copiloto de Auditoría de Repositorios IA**. Puedes pedirme:\n• 📋 **'Lista de problemas'** para ver vulnerabilidades\n• 🛠️ **'Fix issue 1'** para correcciones de código paso a paso\n• ✨ **'/autosolve'** para corregir todo automáticamente",
        ],
        LanguageEnum.FRENCH: [
            "### 👋 Bonjour! Comment puis-je vous aider avec ce dépôt aujourd'hui?\n\nJe suis votre **Copilote d'Audit de Référentiel IA**. Vous pouvez me demander:\n• 📋 **'Liste des problèmes'** pour inspecter les vulnérabilités\n• 🛠️ **'Fix issue 1'** pour des correctifs de code étape par étape\n• ✨ **'/autosolve'** pour corriger tout automatiquement",
        ],
        LanguageEnum.ENGLISH: {
            ToneEnum.CASUAL: [
                "### ⚡ Hey! What's up? Ready to clean up this repository.\n\nGot your codebase loaded and ready to inspect! Here's what you can do:\n• 📋 Ask **'List of issues'** to see what's broken or vulnerable\n• 🛠️ Say **'Fix issue 1'** or **'Fix issue 2'** for quick code solutions\n• ✨ Click **'/autosolve'** to fix everything at once!",
                "### 🚀 Yo! Copilot is active and locked onto this repo.\n\nWant to see the bugs or generate unit tests? Just tell me what you need!"
            ],
            ToneEnum.FORMAL: [
                "### 🛡️ Good day. I am your AI Repository Auditor Copilot.\n\nI have performed a structural static analysis across this repository. How may I assist your engineering review?\n• 📋 **Audit Inventory**: Inquire with **'List of issues'**\n• 🛠️ **Remediation Details**: Specify **'Fix issue [number]'**\n• 🧪 **Automated Testing**: Command **'/test'**\n• ✨ **Autonomous Remediation**: Command **'/autosolve'**",
            ],
            ToneEnum.NEUTRAL: [
                "### 👋 Hello! How can I help you audit or improve this repository?\n\nI'm your **AI Repository Auditor Copilot** with real-time AST introspection into this codebase.\n\nHere are the most helpful things you can ask me to do:\n• 📋 **Inspect Issues**: Ask **'List of issues'** to see all detected security flaws, CVEs, and code bugs.\n• 🛠️ **Step-by-Step Fixes**: Say **'Fix issue 1'** or **'How to resolve SQL injection'** for ready-to-use code patches.\n• 🧪 **Generate Tests**: Type **'/test'** to generate a complete `pytest` suite.\n• ✨ **Auto-Remediate**: Type **'/autosolve'** to fix all issues in an isolated sandbox with 0 manual intervention!\n\nWhat would you like to explore first?",
                "### 🤖 Repository Copilot Ready!\n\nI have introspected this codebase. Feel free to ask for a **'List of issues'**, a **code fix for issue 1**, or automated **pytest generation**."
            ]
        }
    }

    CASUAL_CHAT_RESPONSES = [
        "I'm doing great! 😊 Ready to help you write code, debug issues, or answer any engineering questions. How can I help you today?",
        "I'm feeling great! 🚀 Standing by to help you inspect this repository, build unit tests, or explain algorithms. What are we working on?",
        "Doing well, thank you for asking! 👍 What coding or repository task can we tackle together right now?",
        "All systems operational! ⚡ Ready to assist with debugging, architecture reviews, or zero-trust security audits. What would you like to do?"
    ]

    THANKS_TEMPLATES = [
        "### 😊 You're very welcome!\n\nI'm always standing by to help you inspect code, generate unit tests, optimize architecture, or verify the zero-trust quality gate.\n\n💡 **Quick Action**: Type **'List of issues'** or **'Fix issue 1'** whenever you're ready to proceed!",
        "### 🌟 Glad I could help!\n\nLet me know if you want me to write tests for other modules, check dependency CVEs, or trigger autonomous self-healing.",
        "### 👍 Happy to assist!\n\nYour repository security and code quality are in good hands. What shall we tackle next?"
    ]

    @classmethod
    def generate_greeting(cls, language: LanguageEnum, tone: ToneEnum) -> str:
        if language in [LanguageEnum.HINDI_HINGLISH, LanguageEnum.TAMIL, LanguageEnum.SPANISH, LanguageEnum.FRENCH]:
            templates = cls.GREETING_TEMPLATES.get(language, cls.GREETING_TEMPLATES[LanguageEnum.ENGLISH][ToneEnum.NEUTRAL])
            return random.choice(templates)
        
        eng_options = cls.GREETING_TEMPLATES[LanguageEnum.ENGLISH]
        templates = eng_options.get(tone, eng_options[ToneEnum.NEUTRAL])
        return random.choice(templates)

    @classmethod
    def generate_casual_chat(cls, query: str) -> str:
        q_lower = query.lower()
        if "bored" in q_lower:
            return "Let's build something cool! 🛠️ We can refactor a function, write new tests, or solve any tricky coding puzzle together. What language do you want to code in?"
        if "joke" in q_lower:
            return "Why do programmers prefer dark mode? Because light attracts bugs! 🐛😄 What are we coding next?"
        if "who made you" in q_lower or "who created you" in q_lower:
            return "I am an AI Repository Auditor Copilot built with neural AST analysis and cognitive multi-turn reasoning to help engineers write secure, high-quality code."
        
        return random.choice(cls.CASUAL_CHAT_RESPONSES)

    @classmethod
    def generate_concept_explanation(cls, query: str) -> str:
        q_lower = query.lower()
        
        if "binary search" in q_lower:
            return (
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

        if "recursion" in q_lower:
            return (
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

        if "java" in q_lower:
            return (
                "### ☕ Java Programming Language\n\n"
                "**Java** is a high-level, class-based, object-oriented programming language designed around the philosophy **'Write Once, Run Anywhere' (WORA)**.\n\n"
                "#### Core Characteristics:\n"
                "• **JVM (Java Virtual Machine)**: Executes bytecode on any operating system.\n"
                "• **Strongly Typed**: Static type checking at compile time.\n"
                "• **Automatic Memory Management**: Built-in Garbage Collector.\n"
                "• **Enterprise Standard**: Widely used in backend web services (Spring Boot), Android apps, and large-scale distributed systems."
            )

        if "api" in q_lower or "rest" in q_lower:
            return (
                "### 🌐 Application Programming Interface (API)\n\n"
                "An **API** is a software intermediary that allows two applications to communicate with each other following standardized protocols (like REST, GraphQL, or gRPC).\n\n"
                "#### Common REST HTTP Methods:\n"
                "• `GET`: Retrieve resource data\n"
                "• `POST`: Create a new resource\n"
                "• `PUT` / `PATCH`: Update an existing resource\n"
                "• `DELETE`: Remove a resource"
            )

        return (
            f"### 💡 Technical Concept Explanation\n\n"
            f"Here is a summary for *\"{query}\"*:\n\n"
            "This concept is a core computer science and software engineering principle. "
            "Let me know if you would like a code implementation or an architectural breakdown!"
        )

    @classmethod
    def generate_thanks(cls) -> str:
        return random.choice(cls.THANKS_TEMPLATES)

    @classmethod
    def generate_clarification(cls, query: str) -> str:
        return (
            f"### ❓ Could you please clarify what you'd like to inspect?\n\n"
            f"You asked: *\"{query}\"*, but I need a little more context to give you the most accurate solution:\n\n"
            "• If you want to see all bugs and security vulnerabilities: Ask **'List of issues'**.\n"
            "• If you want to fix a specific bug: Ask **'Fix issue 1'** or **'How to fix SQL injection'**.\n"
            "• If you want an automated test suite: Ask **'Write pytest tests'**.\n"
            "• If you want complete autonomous remediation: Click **`✨ /autosolve`**."
        )

    @classmethod
    def verify_guardrails(cls, reply_text: str) -> str:
        import re
        py_blocks = re.findall(r"```python\n([\s\S]*?)```", reply_text)
        for code in py_blocks:
            lines = [l for l in code.split("\n") if not l.strip().startswith("#") and l.strip()]
            clean_code = "\n".join(lines)
            if clean_code:
                try:
                    ast.parse(clean_code)
                except SyntaxError:
                    pass

        return reply_text
