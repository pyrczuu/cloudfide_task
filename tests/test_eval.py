import json
import pytest
from unittest.mock import MagicMock, patch

# Import application components
from helpdesk.tools import get_booking, calculate_refund
from helpdesk.agent import HelpdeskAgent

def test_agent_tool_calling_loop():
    """
    Tests that the agent loop properly interprets model function calls,
    executes Python tool logic, feeds back tool results, and returns the final answer.
    """
    # 1. Mock first response: Model requests tool execution `calculate_refund(booking_id='CW-1001')`
    mock_func_call = MagicMock()
    mock_func_call.name = "calculate_refund"
    mock_func_call.args = {"booking_id": "CW-1001"}

    mock_candidate_content = MagicMock()
    mock_first_response = MagicMock()
    mock_first_response.function_calls = [mock_func_call]
    mock_first_response.candidates = [MagicMock(content=mock_candidate_content)]

    # 2. Mock second response: Model uses tool output to produce the final text answer
    mock_second_response = MagicMock()
    mock_second_response.function_calls = None
    mock_second_response.text = "If you cancel booking CW-1001 now, you will receive a total refund of €90.00 (€40.00 rental refund + €50.00 deposit) returned to your original payment card."

    # 3. Setup Gemini Client Mock
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [
        mock_first_response,
        mock_second_response,
    ]

    # 4. Instantiate agent with mocked client and run query
    agent = HelpdeskAgent(client=mock_client)
    answer = agent.run("How much refund will I get if I cancel CW-1001 right now?")

    # 5. Assertions
    assert "€90.00" in answer
    assert mock_client.models.generate_content.call_count == 2


def test_agent_refusal_unrelated_question():
    """Tests that the agent directly answers/refuses queries without calling tools."""
    mock_response = MagicMock()
    mock_response.function_calls = None
    mock_response.text = "I am sorry, but I can only answer questions related to CityWheels. Please contact staff at help@citywheels.example for other inquiries."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    agent = HelpdeskAgent(client=mock_client)
    answer = agent.run("What is the capital of Australia?")

    assert "CityWheels" in answer or "contact" in answer
    assert mock_client.models.generate_content.call_count == 1