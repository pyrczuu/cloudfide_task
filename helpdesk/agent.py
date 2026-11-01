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
    def __init__(self, client=None, model_name="gemini-3.8-flash", timeout_seconds=120, max_turns=5):
        self.client = client or genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_turns = max_turns

    def _execute_tool(self, name: str, args: dict) -> dict:
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
        # Create a Chat session to let the SDK natively manage history & turns
        chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=CITYWHEELS_TOOLS,
            )
        )

        response = None
        current_input = user_query

        for turn in range(self.max_turns):
            logger.info(f"Agent Turn {turn + 1}/{self.max_turns}")

            executor = ThreadPoolExecutor(max_workers=1)
            try:
                # Wrap the API call with timeout protection
                future = executor.submit(chat.send_message, current_input)
                response = future.result(timeout=self.timeout_seconds)
            except ExecTimeoutError:
                logger.error("API call to Gemini timed out.")
                return "ERROR_TIMEOUT: Request timed out while contacting Gemini API."
            except Exception as e:
                logger.error(f"API call failed: {e}")
                return f"ERROR_API: {str(e)}"
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

            # If the model didn't call any tools, we have the final answer!
            if not getattr(response, "function_calls", None):
                logger.info("Model returned final text response.")
                return response.text or "I apologize, but I could not formulate a response."

            # Execute tool calls and prepare function response parts
            tool_response_parts = []
            for call in response.function_calls:
                tool_result = self._execute_tool(call.name, call.args or {})
                if not isinstance(tool_result, dict):
                    tool_result = {"result": tool_result}

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response=tool_result
                    )
                )

            # Pass function execution results directly back into the chat as the next turn
            current_input = tool_response_parts

        return "I apologize, but I could not answer your request within the allowed steps. Please contact support at help@citywheels.example."