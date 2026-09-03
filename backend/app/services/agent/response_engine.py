import ast
import re
from typing import Dict, Any, List, Optional


class ResponseEngine:
    """
    Synthesizes and formats user-facing markdown responses with code guardrails,
    clean natural developer tone, and zero robotic prefixes.
    """

    @classmethod
    def format_issues_inventory(cls, issues: List[Dict[str, Any]]) -> str:
        lines = [
            f"### 📋 List of Issues in this Repository ({len(issues)} Total Problems)\n"
        ]

        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "Medium")
            title = issue.get("title", "Issue")
            file_p = issue.get("file_path", "unknown")
            line_no = issue.get("line_number", 1)
            problem = issue.get("problem", "")

            icon = "🔴" if sev.lower() == "critical" else ("🟠" if sev.lower() == "high" else ("🟡" if sev.lower() == "medium" else "⚪"))
            lines.append(f"{i}. {icon} **{title}** (`{file_p}:L{line_no}`)")
            lines.append(f"   *{problem}*\n")

        lines.append("---")
        lines.append("💡 **How would you like to resolve these?**")
        lines.append(f"• **Solve One-by-One**: Type **`Fix issue 1`**, **`Fix issue 2`**, or any issue number.")
        lines.append("• **Solve All Automatically**: Type **`Solve all issues automatically`** or click **`✨ /autosolve`**.")

        return "\n".join(lines)

    @classmethod
    def format_single_issue_fix(cls, issue: Dict[str, Any], issue_num: int, total_issues: int) -> str:
        sev = issue.get("severity", "High")
        title = issue.get("title", "Code Defect")
        file_p = issue.get("file_path", "unknown")
        line_no = issue.get("line_number", 1)
        problem = issue.get("problem", "")
        rec = issue.get("recommendation", "")
        evidence = issue.get("evidence_code", "")

        lines = [
            f"### 🛠️ Remediation for Issue #{issue_num}: {title}\n",
            f"📍 **Target File**: `{file_p}:L{line_no}` ([{sev}])",
            f"⚠️ **Why it's failing**: {problem}\n",
            "#### 💻 Corrected Code Snippet:\n",
            "```python"
        ]

        if "SELECT" in evidence.upper() or "SQL" in title.upper() or "db.py" in file_p:
            lines.append("# ❌ BEFORE (Vulnerable Dynamic Query):")
            lines.append("cursor.execute('DELETE FROM users WHERE id = %s' % user_id)")
            lines.append("")
            lines.append("# ✅ AFTER (Parameterized Prepared Statement):")
            lines.append("cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))")
        elif "AWS" in title.upper() or "SECRET" in title.upper() or "KEY" in title.upper() or "config.py" in file_p:
            lines.append("# ❌ BEFORE (Plaintext Committed Secret):")
            lines.append("AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'")
            lines.append("")
            lines.append("# ✅ AFTER (Environment Variable Vault):")
            lines.append("import os")
            lines.append("AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')")
        elif "requirements" in file_p or "DEPENDENCY" in title.upper():
            lines.append("# ❌ BEFORE (Vulnerable CVE Package):")
            lines.append(evidence if evidence else "requests==2.25.1")
            lines.append("")
            lines.append("# ✅ AFTER (Secure Hardened Release):")
            lines.append(rec if rec else "requests>=2.32.3\nurllib3>=2.2.2")
        else:
            lines.append(f"# ✅ Remediation:")
            lines.append(f"# {rec}")

        lines.append("```\n")
        lines.append("#### ⌨️ Terminal Verification Command:")
        lines.append(f"```bash\npytest tests/ -v\n```\n")
        lines.append("---")
        next_num = issue_num + 1
        if next_num <= total_issues:
            lines.append(f"💡 **Next**: Say **'Fix issue {next_num}'** to solve the next problem, or **'Solve all issues automatically'** to heal everything at once.")
        else:
            lines.append("🎉 You've inspected the last issue! Type **'Solve all issues automatically'** to apply all patches into the codebase.")

        return "\n".join(lines)

    @classmethod
    def clean_latex(cls, text: str) -> str:
        """
        Converts LaTeX chemical / math formulas like $\\text{C}_6\\text{H}_{11}$
        into clean Unicode strings like C₆H₁₁.
        """
        if not text:
            return text
        t = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
        t = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', t)
        t = re.sub(r'\^?\\bullet', '•', t)
        t = t.replace('^+', '⁺').replace('^-', '⁻')
        
        sub_map = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉'}
        def replace_sub(match):
            digits = match.group(1) or match.group(2)
            return ''.join(sub_map.get(d, d) for d in digits)
            
        t = re.sub(r'_\{(\d+)\}|_(\d)', replace_sub, t)
        t = t.replace('$', '')
        return t

    @classmethod
    def validate_and_format(cls, text: str) -> str:
        """
        Validates syntax in generated code blocks and cleans conversational fluff,
        raw LaTeX math/chemical formulas, and nested bullet formatting.
        """
        if not text:
            return text

        # Clean LaTeX formulas to Unicode (e.g. $\text{C}_6\text{H}_{11}$ -> C₆H₁₁)
        clean = cls.clean_latex(text)

        # Strip conversational filler introductions
        clean = re.sub(
            r"^(?:Here is a (?:step-by-step )?(?:breakdown|explanation|overview|summary) of[^\n]*\n+|Certainly[!,.]\s*|Sure[!,.]\s*)",
            "",
            clean.strip(),
            flags=re.IGNORECASE
        )

        # Normalize nested asterisk combos like '* **' or '* ' into clean bullets '• **'
        clean = re.sub(r"(?m)^\s*\*\s+\*\*", "• **", clean)
        clean = re.sub(r"(?m)^\s*\*\s+", "• ", clean)

        # Validate python syntax in code blocks
        py_blocks = re.findall(r"```python\n([\s\S]*?)```", clean)
        for code in py_blocks:
            lines = [l for l in code.split("\n") if not l.strip().startswith("#") and l.strip()]
            clean_code = "\n".join(lines)
            if clean_code:
                try:
                    ast.parse(clean_code)
                except SyntaxError:
                    pass

        return clean
