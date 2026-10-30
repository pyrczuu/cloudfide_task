import os
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ExecTimeoutError
from google import genai
from google.genai import types
from helpdesk.tools import get_booking, calculate_refund
from helpdesk.search import search_policies
from helpdesk.llm import CITYWHEELS_TOOLS, SYSTEM_INSTRUCTION

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("helpdesk.agent")

class HelpdeskAgent:
    def __init__(self, client=None, model_name="gemini-3.8-flash", timeout_seconds=45, max_turns=5):
        self.client = client or genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_turns = max_turns

    def _execute_tool(self, name: str, args: dict):
        logger.info(f"Executing tool: {name} with args: {args}")
        try:
            if name == "search_policies":
                return search_policies(args.get("query", ""))
            elif name == "get_booking":
                return get_booking(args.get("booking_id", ""))
            elif name == "calculate_refund":
                return calculate_refund(args.get("booking_id", ""))
            return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}

    def run(self, user_query: str) -> str:
        messages = [types.Content(role="user", parts=[types.Part.from_text(text=user_query)])]

        for turn in range(self.max_turns):
            logger.info(f"Agent Turn {turn + 1}/{self.max_turns}")

            executor = ThreadPoolExecutor(max_workers=1)
            try:
                future = executor.submit(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=CITYWHEELS_TOOLS,
                    )
                )
                response = future.result(timeout=self.timeout_seconds)
            except ExecTimeoutError:
                logger.error("API call to Gemini timed out.")
                return "ERROR_TIMEOUT: Request timed out while contacting Gemini API."
            except Exception as e:
                logger.error(f"API call failed: {e}")
                return f"ERROR_API: {str(e)}"
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

            function_calls = getattr(response, "function_calls", None)
            if not function_calls:
                return response.text or "I apologize, but I could not formulate a response."

            if response.candidates and response.candidates[0].content:
                messages.append(response.candidates[0].content)

            tool_response_parts = []
            for call in function_calls:
                tool_result = self._execute_tool(call.name, call.args or {})
                if not isinstance(tool_result, dict):
                    tool_result = {"result": tool_result}

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response=tool_result
                    )
                )

            messages.append(types.Content(role="user", parts=[types.Part.from_text(text=""), *tool_response_parts]))

        return "Reached max turns without a final answer."