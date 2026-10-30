from google.genai import types

from helpdesk.search import search_policies
from helpdesk.tools import get_booking, calculate_refund

# Gemini Tool Declarations
tool_search_policies = types.FunctionDeclaration(
    name="search_policies",
    description="Search CityWheels rules, prices, FAQ, age limits, and cancellation policies.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"query": types.Schema(type="STRING", description="Keywords to search in policies")},
        required=["query"]
    )
)

tool_get_booking = types.FunctionDeclaration(
    name="get_booking",
    description="Fetch details of a booking by its ID (e.g., CW-1001).",
    parameters=types.Schema(
        type="OBJECT",
        properties={"booking_id": types.Schema(type="STRING", description="The booking ID")},
        required=["booking_id"]
    )
)

tool_calculate_refund = types.FunctionDeclaration(
    name="calculate_refund",
    description="Calculate the refund amount for a booking if cancelled now.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"booking_id": types.Schema(type="STRING", description="The booking ID")},
        required=["booking_id"]
    )
)

CITYWHEELS_TOOLS = [
    types.Tool(
        function_declarations=[tool_search_policies, tool_get_booking, tool_calculate_refund]
    )
]

SYSTEM_INSTRUCTION = """
You are the customer support assistant for CityWheels, a bike rental shop.
Current reference date & time: 2026-06-10 09:00:00+02:00.

Rules:
1. Answer questions ONLY using information from tool call results. Do NOT use outside general knowledge.
2. For any pricing, policy, age, or schedule questions, call `search_policies`.
3. For booking queries, call `get_booking`.
4. For cancellation or refund inquiries, ALWAYS call `calculate_refund`. Do NOT compute refund math yourself.
5. If the question cannot be answered from tools or is completely unrelated to CityWheels, state that you cannot answer and direct the customer to contact staff at help@citywheels.example or +48 000 000 000.
6. Never make up booking numbers, prices, or policies.
"""
