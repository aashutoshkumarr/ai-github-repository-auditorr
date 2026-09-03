import time
import uuid
from typing import Dict, Any, List, Optional


class ExecutionTrace:
    def __init__(
        self,
        request_id: str,
        user_query: str,
        prompt_version: str = "v2.5",
        model: str = "neural-orchestrator-offline"
    ):
        self.request_id = request_id
        self.user_query = user_query
        self.prompt_version = prompt_version
        self.model = model
        self.start_time = time.time()
        self.decision: Dict[str, Any] = {}
        self.tool_calls: List[Dict[str, Any]] = []
        self.final_response_preview: str = ""
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0

    def record_decision(self, goal: str, requires_tools: bool, selected_tools: List[str], plan: Optional[List[str]] = None):
        self.decision = {
            "goal": goal,
            "requires_tools": requires_tools,
            "selected_tools": selected_tools,
            "plan": plan or []
        }

    def record_tool_call(self, tool_name: str, tool_input: Dict[str, Any], tool_output: Any):
        self.tool_calls.append({
            "tool": tool_name,
            "input": tool_input,
            "output_preview": str(tool_output)[:160]
        })

    def complete(self, response_text: str):
        self.duration_ms = round((time.time() - self.start_time) * 1000, 2)
        self.final_response_preview = response_text[:200]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "prompt_version": self.prompt_version,
            "model": self.model,
            "duration_ms": self.duration_ms,
            "decision": self.decision,
            "tool_calls_count": len(self.tool_calls),
            "tool_calls": self.tool_calls,
            "error": self.error
        }

    def print_trace_log(self):
        try:
            print(f"\n+--- [ORCHESTRATOR TRACE] {self.request_id} -----------------------")
            print(f"| Query: \"{self.user_query}\"")
            print(f"| Prompt Version: {self.prompt_version} | Model: {self.model} | Latency: {self.duration_ms}ms")
            print(f"| Goal: {self.decision.get('goal')} | Requires Tools: {self.decision.get('requires_tools')}")
            if self.decision.get("selected_tools"):
                print(f"| Tools Selected: {', '.join(self.decision.get('selected_tools', []))}")
            print(f"| Tools Executed: {len(self.tool_calls)}")
            clean_prev = self.final_response_preview.replace("\n", " ")[:100]
            print(f"| Response Preview: {clean_prev}...")
            print(f"+----------------------------------------------------------\n")
        except Exception:
            pass


class ObservabilityManager:
    @classmethod
    def create_trace(cls, user_query: str, model: str = "offline") -> ExecutionTrace:
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        return ExecutionTrace(
            request_id=req_id,
            user_query=user_query,
            prompt_version="v2.5",
            model=model
        )
