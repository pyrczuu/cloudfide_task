import os

from google import genai
from google.genai import types

from helpdesk.llm import SYSTEM_INSTRUCTION, CITYWHEELS_TOOLS
from helpdesk.search import search_policies
from helpdesk.tools import get_booking, calculate_refund


class HelpdeskAgent:
    def __init__(self, client=None, model_name="gemini-2.5-flash"):
        self.client = client or genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = model_name

    def run(self, user_query: str) -> str:
        messages = [types.Content(role="user", parts=[types.Part.from_text(text=user_query)])]

        while True:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=CITYWHEELS_TOOLS
                )
            )

            # Check if model wants to call tools
            function_calls = response.function_calls
            if not function_calls:
                return response.text

            # Execute tool calls
            messages.append(response.candidates[0].content)
            response_parts = []

            for call in function_calls:
                name = call.name
                args = call.args

                if name == "search_policies":
                    res = search_policies(args.get("query", ""))
                elif name == "get_booking":
                    res = get_booking(args.get("booking_id", ""))
                elif name == "calculate_refund":
                    res = calculate_refund(args.get("booking_id", ""))
                else:
                    res = {"error": f"Unknown tool: {name}"}

                response_parts.append(
                    types.Part.from_function_response(name=name, response={"result": res})
                )

            messages.append(types.Content(role="user", parts=response_parts))
