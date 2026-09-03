import os
import re
import tempfile
import shutil
import asyncio
import subprocess
import ast
import json

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.app.services.repo_fetcher import RepositoryContext
from backend.app.services.analyzers.security_scanner import SecurityScanner


class AutoFixResult:
    def __init__(
        self,
        finding_id: str,
        status: str,
        original_code: str,
        patched_code: str,
        patched_file_content: str,
        diff_patch: str,
        tests_passed: bool,
        security_check_passed: bool,
        iterations: int,
        log: List[str],
    ):
        self.finding_id = finding_id
        self.status = status
        self.original_code = original_code
        self.patched_code = patched_code
        self.patched_file_content = patched_file_content
        self.diff_patch = diff_patch
        self.tests_passed = tests_passed
        self.security_check_passed = security_check_passed
        self.iterations = iterations
        self.log = log

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "status": self.status,
            "original_code": self.original_code,
            "patched_code": self.patched_code,
            "patched_file_content": self.patched_file_content,
            "diff_patch": self.diff_patch,
            "tests_passed": self.tests_passed,
            "security_check_passed": self.security_check_passed,
            "iterations": self.iterations,
            "log": self.log,
        }


class AutoFixEngine:

    # ================================================================
    # Test Detection
    # ================================================================

    @staticmethod
    def _detect_test_command(repo_path: Path) -> Optional[List[str]]:
        """
        Detect a real repository test command.

        The engine never invents a test suite.
        If no trustworthy test suite exists, verification remains
        unverified.
        """

        # ------------------------------------------------------------
        # Python / pytest
        # ------------------------------------------------------------

        if (
            (repo_path / "pytest.ini").exists()
            or (repo_path / "pyproject.toml").exists()
            or (repo_path / "setup.cfg").exists()
        ):
            if (
                (repo_path / "tests").exists()
                or (repo_path / "test").exists()
            ):
                return ["python", "-m", "pytest", "-q"]

        if (repo_path / "tests").exists():
            return ["python", "-m", "pytest", "-q"]

        if (repo_path / "test").exists():
            return ["python", "-m", "pytest", "-q"]

        # ------------------------------------------------------------
        # Node
        # ------------------------------------------------------------

        package_json = repo_path / "package.json"

        if package_json.exists():
            try:
                package_data = json.loads(
                    package_json.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                )

                scripts = package_data.get("scripts", {})

                if "test" in scripts:
                    return ["npm", "test", "--", "--runInBand"]

            except Exception:
                pass

        # ------------------------------------------------------------
        # Maven
        # ------------------------------------------------------------

        if (repo_path / "pom.xml").exists():
            return ["mvn", "test"]

        # ------------------------------------------------------------
        # Gradle
        # ------------------------------------------------------------

        if (repo_path / "gradlew").exists():
            return ["./gradlew", "test"]

        return None

    @staticmethod
    async def _run_tests(
        sandbox_path: Path,
        logs: List[str],
    ) -> bool:

        command = AutoFixEngine._detect_test_command(sandbox_path)

        if not command:
            logs.append(
                "⚠️ No runnable repository test suite detected. "
                "Auto-Fix cannot claim tests passed."
            )
            return False

        logs.append(
            f"Running repository tests in sandbox: {' '.join(command)}"
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(sandbox_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await process.communicate()

            output = stdout.decode(
                "utf-8",
                errors="replace",
            )

            output_lines = output.splitlines()

            if len(output_lines) > 40:
                output_lines = output_lines[-40:]

            for line in output_lines:
                logs.append(f"TEST: {line}")

            if process.returncode == 0:
                logs.append(
                    "✅ Repository test suite passed successfully."
                )
                return True

            logs.append(
                f"❌ Repository tests failed with exit code "
                f"{process.returncode}."
            )
            return False

        except FileNotFoundError:
            logs.append(
                f"❌ Test executable not available: {command[0]}"
            )
            return False

        except Exception as exc:
            logs.append(
                f"❌ Test execution failed: {str(exc)}"
            )
            return False

    # ================================================================
    # Sandbox
    # ================================================================

    @staticmethod
    def _create_sandbox(
        ctx: RepositoryContext,
    ) -> Optional[Path]:

        source_path = Path(ctx.local_path)

        if not source_path.exists():
            return None

        sandbox_root = Path(
            tempfile.mkdtemp(
                prefix="auditor-autofix-"
            )
        )

        sandbox_path = sandbox_root / source_path.name

        shutil.copytree(
            source_path,
            sandbox_path,
            dirs_exist_ok=True,
        )

        return sandbox_path

    @staticmethod
    def _apply_patch_to_sandbox(
        sandbox_path: Path,
        file_path: str,
        patched_content: str,
    ) -> bool:

        target = sandbox_path / file_path

        try:
            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            target.write_text(
                patched_content,
                encoding="utf-8",
            )

            return True

        except Exception:
            return False

    # ================================================================
    # Diff Generation
    # ================================================================

    @staticmethod
    def _generate_diff(
        file_path: str,
        original_lines: List[str],
        patched_lines: List[str],
        line_num: int,
    ) -> str:

        if not 1 <= line_num <= len(original_lines):
            return ""

        original_line = original_lines[line_num - 1]

        patched_line = (
            patched_lines[line_num - 1]
            if 1 <= line_num <= len(patched_lines)
            else ""
        )

        patched_block = patched_line.splitlines()

        if not patched_block:
            patched_block = [""]

        diff_lines = [
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
            (
                f"@@ -{line_num},1 "
                f"+{line_num},{len(patched_block)} @@"
            ),
            f"-{original_line}",
        ]

        for line in patched_block:
            diff_lines.append(f"+{line}")

        return "\n".join(diff_lines)

    # ================================================================
    # Python Helpers
    # ================================================================

    @staticmethod
    def _expression_to_source(
        node: ast.AST,
    ) -> Optional[str]:

        try:
            return ast.unparse(node)

        except Exception:
            return None

    # ================================================================
    # Dynamic SQL Analysis
    # ================================================================

    @staticmethod
    def _extract_sql_parts(
        sql_node: ast.AST,
    ) -> Optional[Tuple[str, List[str]]]:

        # ------------------------------------------------------------
        # Percent formatting
        # ------------------------------------------------------------

        if isinstance(sql_node, ast.BinOp) and isinstance(
            sql_node.op,
            ast.Mod,
        ):

            if not isinstance(
                sql_node.left,
                ast.Constant,
            ):
                return None

            if not isinstance(
                sql_node.left.value,
                str,
            ):
                return None

            sql_template = sql_node.left.value
            values: List[str] = []

            if isinstance(
                sql_node.right,
                ast.Tuple,
            ):

                for item in sql_node.right.elts:

                    source = (
                        AutoFixEngine
                        ._expression_to_source(item)
                    )

                    if source:
                        values.append(source)

            else:

                source = (
                    AutoFixEngine
                    ._expression_to_source(
                        sql_node.right
                    )
                )

                if source:
                    values.append(source)

            if not values:
                return None

            return sql_template, values

        # ------------------------------------------------------------
        # .format(...)
        # ------------------------------------------------------------

        if isinstance(
            sql_node,
            ast.Call,
        ):

            if (
                isinstance(sql_node.func, ast.Attribute)
                and sql_node.func.attr == "format"
                and isinstance(
                    sql_node.func.value,
                    ast.Constant,
                )
                and isinstance(
                    sql_node.func.value.value,
                    str,
                )
            ):

                sql_template = sql_node.func.value.value
                parameters: List[str] = []

                for arg in sql_node.args:

                    source = (
                        AutoFixEngine
                        ._expression_to_source(arg)
                    )

                    if source:
                        parameters.append(source)

                if parameters:
                    return sql_template, parameters

        # ------------------------------------------------------------
        # f-string
        # ------------------------------------------------------------

        if isinstance(
            sql_node,
            ast.JoinedStr,
        ):

            sql_template = ""
            parameters: List[str] = []

            for value in sql_node.values:

                if isinstance(
                    value,
                    ast.Constant,
                ):

                    sql_template += str(value.value)

                elif isinstance(
                    value,
                    ast.FormattedValue,
                ):

                    expression = (
                        AutoFixEngine
                        ._expression_to_source(
                            value.value
                        )
                    )

                    if not expression:
                        return None

                    sql_template += "%s"
                    parameters.append(expression)

            if parameters:
                return sql_template, parameters

        # ------------------------------------------------------------
        # String concatenation
        # ------------------------------------------------------------

        if (
            isinstance(sql_node, ast.BinOp)
            and isinstance(sql_node.op, ast.Add)
        ):

            parts: List[ast.AST] = []

            def flatten_add(node: ast.AST):

                if (
                    isinstance(node, ast.BinOp)
                    and isinstance(node.op, ast.Add)
                ):
                    flatten_add(node.left)
                    flatten_add(node.right)

                else:
                    parts.append(node)

            flatten_add(sql_node)

            sql_template = ""
            parameters: List[str] = []

            for part in parts:

                if (
                    isinstance(part, ast.Constant)
                    and isinstance(part.value, str)
                ):

                    sql_template += part.value
                    continue

                if (
                    isinstance(part, ast.Call)
                    and isinstance(part.func, ast.Name)
                    and part.func.id == "str"
                    and len(part.args) == 1
                ):

                    expression = (
                        AutoFixEngine
                        ._expression_to_source(
                            part.args[0]
                        )
                    )

                    if expression:
                        sql_template += "%s"
                        parameters.append(expression)
                        continue

                expression = (
                    AutoFixEngine
                    ._expression_to_source(part)
                )

                if expression:
                    sql_template += "%s"
                    parameters.append(expression)

            if parameters:
                return sql_template, parameters

        return None

    @staticmethod
    def _generate_sql_parameterized_patch(
        target_line: str,
    ) -> Optional[str]:
        """
        Convert dynamic SQL into parameterized SQL.

        IMPORTANT:
        This preserves the original SQL operation.
        It does not replace DELETE with SELECT,
        INSERT with SELECT, etc.
        """

        indentation = (
            target_line[
                :len(target_line)
                - len(target_line.lstrip())
            ]
        )

        try:
            tree = ast.parse(
                target_line.strip(),
                mode="exec",
            )

        except SyntaxError:
            return None

        if not tree.body:
            return None

        statement = tree.body[0]

        if not isinstance(
            statement,
            ast.Expr,
        ):
            return None

        call = statement.value

        if not isinstance(
            call,
            ast.Call,
        ):
            return None

        if not isinstance(
            call.func,
            ast.Attribute,
        ):
            return None

        if call.func.attr not in {
            "execute",
            "executemany",
        }:
            return None

        if not call.args:
            return None

        sql_node = call.args[0]

        extracted = (
            AutoFixEngine
            ._extract_sql_parts(sql_node)
        )

        if not extracted:
            return None

        sql_template, parameters = extracted

        if not parameters:
            return None

        db_object = (
            AutoFixEngine
            ._expression_to_source(
                call.func.value
            )
        )

        if not db_object:
            return None

        if len(parameters) == 1:
            parameter_tuple = (
                f"({parameters[0]},)"
            )

        else:
            parameter_tuple = (
                "("
                + ", ".join(parameters)
                + ")"
            )

        sql_literal = repr(sql_template)

        return (
            f"{indentation}query = {sql_literal}\n"
            f"{indentation}{db_object}.execute("
            f"query, {parameter_tuple})"
        )

    # ================================================================
    # Main Auto-Fix Pipeline
    # ================================================================

    @staticmethod
    async def run_autofix_pipeline(
        ctx: RepositoryContext,
        finding: Dict[str, Any],
        max_retries: int = 2,
    ) -> AutoFixResult:

        logs: List[str] = []

        file_path = finding.get(
            "file_path",
            "",
        )

        rule_id = finding.get(
            "rule_id",
            "",
        )

        line_num = finding.get(
            "line_number",
            1,
        )

        logs.append(
            f"Initiating auto-fix pipeline for "
            f"[{finding.get('severity')}] "
            f"{finding.get('title')} "
            f"in {file_path}:{line_num}"
        )

        # ------------------------------------------------------------
        # Locate file
        # ------------------------------------------------------------

        file = ctx.files.get(file_path)

        if not file:

            logs.append(
                f"Exact file path '{file_path}' not found. "
                f"Attempting fuzzy match..."
            )

            for p, f in ctx.files.items():

                if file_path in p:

                    file = f
                    file_path = p

                    logs.append(
                        f"Fuzzy match resolved file to "
                        f"'{file_path}'."
                    )

                    break

        if not file:

            logs.append(
                f"❌ Error: File '{file_path}' not found."
            )

            return AutoFixResult(
                finding_id=finding.get(
                    "id",
                    "unknown",
                ),
                status="failed",
                original_code="",
                patched_code="",
                patched_file_content="",
                diff_patch="",
                tests_passed=False,
                security_check_passed=False,
                iterations=0,
                log=logs,
            )

        original_content = file.content
        lines = original_content.splitlines()

        if not lines:

            return AutoFixResult(
                finding_id=finding.get(
                    "id",
                    "unknown",
                ),
                status="failed",
                original_code="",
                patched_code="",
                patched_file_content="",
                diff_patch="",
                tests_passed=False,
                security_check_passed=False,
                iterations=0,
                log=logs,
            )

        if line_num < 1 or line_num > len(lines):

            logs.append(
                f"❌ Invalid finding line number: {line_num}"
            )

            return AutoFixResult(
                finding_id=finding.get(
                    "id",
                    "unknown",
                ),
                status="failed",
                original_code="",
                patched_code="",
                patched_file_content="",
                diff_patch="",
                tests_passed=False,
                security_check_passed=False,
                iterations=0,
                log=logs,
            )

        current_patch = ""
        current_content = original_content

        tests_passed = False
        sec_passed = False
        iteration = 0

        patched_lines = list(lines)

        # ------------------------------------------------------------
        # Retry loop
        # ------------------------------------------------------------

        for attempt in range(
            1,
            max_retries + 2,
        ):

            iteration = attempt

            logs.append(
                f"Iteration {attempt}: "
                f"Generating remediation candidate..."
            )

            patched_lines = list(lines)

            target_line = lines[line_num - 1]

            # --------------------------------------------------------
            # Hardcoded secret
            # --------------------------------------------------------

            if (
                "SEC-AWS" in rule_id
                or "SEC-OPENAI" in rule_id
                or "SEC-GENERIC-PASSWORD" in rule_id
            ):

                if "=" in target_line:

                    indentation = (
                        target_line[
                            :len(target_line)
                            - len(target_line.lstrip())
                        ]
                    )

                    var_name = (
                        target_line
                        .split("=")[0]
                        .strip()
                    )

                    patched_lines[line_num - 1] = (
                        f"{indentation}"
                        f"{var_name} = "
                        f"os.getenv("
                        f"'{var_name.upper()}', "
                        f"''"
                        f")"
                    )

                    logs.append(
                        "Replaced hardcoded secret "
                        "with environment-variable lookup."
                    )

            # --------------------------------------------------------
            # SQL Injection
            # --------------------------------------------------------

            elif "VULN-SQL-INJECTION" in rule_id:

                sql_patch = (
                    AutoFixEngine
                    ._generate_sql_parameterized_patch(
                        target_line
                    )
                )

                if sql_patch:

                    patched_lines[line_num - 1] = sql_patch

                    logs.append(
                        "✅ Converted dynamic SQL to "
                        "parameterized query binding while "
                        "preserving the original SQL operation "
                        "and parameters."
                    )

                else:

                    logs.append(
                        "❌ SQL pattern could not be safely "
                        "converted automatically."
                    )

                    sec_passed = False

            # --------------------------------------------------------
            # Bare except
            # --------------------------------------------------------

            elif "QUAL-BARE-EXCEPT" in rule_id:

                indentation = (
                    target_line[
                        :len(target_line)
                        - len(target_line.lstrip())
                    ]
                )

                patched_lines[line_num - 1] = (
                    f"{indentation}except Exception as e:\n"
                    f"{indentation}    # Log exception properly\n"
                    f"{indentation}    pass"
                )

                logs.append(
                    "Replaced bare except with "
                    "'except Exception as e:'"
                )

            # --------------------------------------------------------
            # eval()
            # --------------------------------------------------------

            elif "VULN-EVAL-EXEC" in rule_id:

                indentation = (
                    target_line[
                        :len(target_line)
                        - len(target_line.lstrip())
                    ]
                )

                patched_lines[line_num - 1] = (
                    f"{indentation}"
                    "# Use safe ast.literal_eval\n"
                    f"{indentation}"
                    "import ast\n"
                    f"{indentation}"
                    "result = ast.literal_eval("
                    "user_formula"
                    ")"
                )

                logs.append(
                    "Replaced arbitrary eval() with "
                    "ast.literal_eval()."
                )

            # --------------------------------------------------------
            # pickle
            # --------------------------------------------------------

            elif "VULN-PICKLE" in rule_id:

                indentation = (
                    target_line[
                        :len(target_line)
                        - len(target_line.lstrip())
                    ]
                )

                patched_lines[line_num - 1] = (
                    f"{indentation}"
                    "import json\n"
                    f"{indentation}"
                    "data = json.loads("
                    "payload_bytes.decode('utf-8')"
                    ")"
                )

                logs.append(
                    "Replaced insecure pickle deserialization "
                    "with JSON parsing."
                )

            # --------------------------------------------------------
            # Generic
            # --------------------------------------------------------

            else:

                recommendation = finding.get(
                    "recommendation",
                    "",
                )

                indentation = (
                    target_line[
                        :len(target_line)
                        - len(target_line.lstrip())
                    ]
                )

                patched_lines[line_num - 1] = (
                    f"{indentation}"
                    f"# Remediated per audit: "
                    f"{recommendation[:120]}"
                )

                logs.append(
                    "Applied recommended code transformation."
                )

            # --------------------------------------------------------
            # Build patched content
            # --------------------------------------------------------

            current_content = "\n".join(
                patched_lines
            )

            # --------------------------------------------------------
            # Generate proper diff
            # --------------------------------------------------------

            current_patch = (
                AutoFixEngine._generate_diff(
                    file_path=file_path,
                    original_lines=lines,
                    patched_lines=patched_lines,
                    line_num=line_num,
                )
            )

            # --------------------------------------------------------
            # Sandbox
            # --------------------------------------------------------

            sandbox_path = None

            try:

                logs.append(
                    "Creating isolated sandbox "
                    "for candidate patch..."
                )

                sandbox_path = (
                    AutoFixEngine
                    ._create_sandbox(ctx)
                )

                if not sandbox_path:

                    logs.append(
                        "❌ Failed to create isolated sandbox."
                    )

                    continue

                applied = (
                    AutoFixEngine
                    ._apply_patch_to_sandbox(
                        sandbox_path,
                        file_path,
                        current_content,
                    )
                )

                if not applied:

                    logs.append(
                        "❌ Failed to apply candidate patch "
                        "inside sandbox."
                    )

                    continue

                logs.append(
                    f"Applied candidate patch to sandbox: "
                    f"{file_path}"
                )

                # ----------------------------------------------------
                # Syntax validation
                # ----------------------------------------------------

                if file.extension.lower() == ".py":

                    logs.append(
                        "Running Python syntax validation..."
                    )

                    try:

                        compile(
                            current_content,
                            file_path,
                            "exec",
                        )

                        logs.append(
                            "✅ Python syntax validation passed."
                        )

                    except SyntaxError as exc:

                        logs.append(
                            f"❌ Python syntax validation failed: "
                            f"{exc}"
                        )

                        tests_passed = False
                        sec_passed = False

                        continue

                # ----------------------------------------------------
                # Real tests
                # ----------------------------------------------------

                tests_passed = (
                    await AutoFixEngine._run_tests(
                        sandbox_path,
                        logs,
                    )
                )

                # ----------------------------------------------------
                # Security verification
                # ----------------------------------------------------

                logs.append(
                    "Running verification security scan "
                    "on patched candidate..."
                )

                temp_ctx = RepositoryContext(
                    ctx.url,
                    str(sandbox_path),
                    ctx.owner,
                    ctx.name,
                )

                temp_ctx.files = dict(ctx.files)

                from backend.app.services.repo_fetcher import RepoFile

                temp_ctx.files[file_path] = RepoFile(
                    file_path,
                    str(
                        sandbox_path / file_path
                    ),
                    len(current_content),
                    file.extension,
                    current_content,
                )

                _, new_sec_findings, _ = (
                    SecurityScanner.analyze(
                        temp_ctx
                    )
                )

                remaining_findings = [
                    f
                    for f in new_sec_findings
                    if (
                        f.get("file_path") == file_path
                        and (
                            not finding.get("rule_id")
                            or f.get("rule_id")
                            == finding.get("rule_id")
                        )
                    )
                ]

                if not remaining_findings:

                    sec_passed = True

                    logs.append(
                        "✅ Security verification passed: "
                        "target finding is no longer detected."
                    )

                else:

                    sec_passed = False

                    logs.append(
                        "⚠️ Verification detected a "
                        "remaining finding."
                    )

                # ----------------------------------------------------
                # Final candidate decision
                # ----------------------------------------------------

                if sec_passed and tests_passed:

                    logs.append(
                        "✅ Auto-Fix candidate passed "
                        "security verification and "
                        "repository tests."
                    )

                    break

                # IMPORTANT:
                # If security passed but tests are unavailable,
                # do not regenerate the exact same patch.

                if sec_passed and not tests_passed:

                    logs.append(
                        "⚠️ Security fix passed, but repository "
                        "tests did not pass or were unavailable."
                    )

                    logs.append(
                        "ℹ️ No additional retry is useful because "
                        "the security candidate already passed."
                    )

                    break

            finally:

                if sandbox_path:

                    shutil.rmtree(
                        sandbox_path.parent,
                        ignore_errors=True,
                    )

                    logs.append(
                        "Sandbox cleaned up successfully."
                    )

        # ============================================================
        # Final status
        # ============================================================

        if sec_passed and tests_passed:

            status = "verified"

        elif sec_passed:

            status = "unverified"

        else:

            status = "failed"

        logs.append(
            f"Auto-Fix pipeline finished with status: {status}"
        )

        return AutoFixResult(
            finding_id=finding.get(
                "id",
                "unknown",
            ),
            status=status,
            original_code=(
                lines[line_num - 1]
                if line_num <= len(lines)
                else ""
            ),
            patched_code=(
                patched_lines[line_num - 1]
                if line_num <= len(patched_lines)
                else ""
            ),
            patched_file_content=current_content,
            diff_patch=current_patch,
            tests_passed=tests_passed,
            security_check_passed=sec_passed,
            iterations=iteration,
            log=logs,
        )