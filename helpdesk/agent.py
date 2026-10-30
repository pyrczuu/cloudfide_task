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
    def __init__(self, client=None, model_name="gemini-3.8-flash", timeout_seconds=15, max_turns=5):
        self.client = client or genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_turns = max_turns

    def _execute_tool(self, name: str, args: dict):
        """Dispatches and executes local tool functions."""
        logger.info(f"Executing tool: {name} with args: {args}")
        try:
            if name == "search_policies":
                return search_policies(args.get("query", ""))
            elif name == "get_booking":
                return get_booking(args.get("booking_id", ""))
            elif name == "calculate_refund":
                return calculate_refund(args.get("booking_id", ""))
            else:
                return {"error": f"Unknown tool name: {name}"}
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}

    def run(self, user_query: str) -> str:
        messages = [types.Content(role="user", parts=[types.Part.from_text(text=user_query)])]

        for turn in range(self.max_turns):
            logger.info(f"Agent Turn {turn + 1}/{self.max_turns}")

            # Do NOT use 'with ThreadPoolExecutor' context manager, as its exit block waits for hung threads.
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(
                self.client.models.generate_content,
                model=self.model_name,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=CITYWHEELS_TOOLS,
                )
            )

            try:
                response = future.result(timeout=self.timeout_seconds)
            except ExecTimeoutError:
                logger.error("API call to Gemini timed out.")
                executor.shutdown(wait=False, cancel_futures=True)
                return "ERROR_TIMEOUT: Request timed out while contacting Gemini API."
            except Exception as e:
                logger.error(f"API call failed: {e}")
                executor.shutdown(wait=False, cancel_futures=True)
                return f"ERROR_API: {str(e)}"
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

            # Check for text response
            function_calls = getattr(response, "function_calls", None)
            if not function_calls:
                logger.info("Model returned final text response.")
                return response.text or "I apologize, but I could not formulate a response."

            # Append model message to history
            if response.candidates and response.candidates[0].content:
                messages.append(response.candidates[0].content)

            # Process function calls
            tool_response_parts = []
            for call in function_calls:
                tool_name = call.name
                tool_args = call.args or {}

                tool_result = self._execute_tool(tool_name, tool_args)

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": tool_result}
                    )
                )

            messages.append(types.Content(role="user", parts=tool_response_parts))

        logger.warning("Agent exceeded maximum turn limit.")
        return "I apologize, but I could not answer your request within the allowed steps. Please contact support at help@citywheels.example."