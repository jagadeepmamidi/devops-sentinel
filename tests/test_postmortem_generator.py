import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.postmortem_generator import PostmortemGenerator

@pytest.fixture
def mock_ai_client():
    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_generate_postmortem_with_ai(mock_ai_client):
    generator = PostmortemGenerator(ai_client=mock_ai_client)

    incident = {
        'id': 'inc-123',
        'title': 'Test Incident',
        'severity': 'P1',
        'service_name': 'Test Service',
        'description': 'Something went wrong',
        'detected_at': '2023-10-01T10:00:00Z',
        'resolved_at': '2023-10-01T12:00:00Z'
    }

    events = [
        {'timestamp': '2023-10-01T10:00:00Z', 'description': 'Incident detected'},
        {'timestamp': '2023-10-01T11:00:00Z', 'description': 'Fix deployed'},
        {'timestamp': '2023-10-01T12:00:00Z', 'description': 'Incident resolved'}
    ]

    mock_response = MagicMock()
    mock_response.content = """
    ```json
    {
        "summary": "A test incident occurred due to something going wrong.",
        "impact": "Users were unable to access the service.",
        "root_cause": "A bug in the code.",
        "contributing_factors": "Lack of testing.",
        "what_went_well": "Response was quick.",
        "improvements": "Add more tests.",
        "action_items": "| Priority | Action | Owner | Due |\\n|---|---|---|---|",
        "lessons": "Test more."
    }
    ```
    """
    mock_ai_client.ainvoke.return_value = mock_response

    result = await generator.generate(incident, events)

    assert result['incident_id'] == 'inc-123'
    assert result['sections']['summary'] == "A test incident occurred due to something going wrong."
    assert "A test incident occurred due to something going wrong." in result['markdown']
    assert "Generated with DevOps Sentinel AI" in result['markdown']

@pytest.mark.asyncio
async def test_generate_postmortem_without_ai():
    generator = PostmortemGenerator(ai_client=None)

    incident = {
        'id': 'inc-124',
        'title': 'Test Incident No AI',
        'severity': 'P2',
        'service_name': 'Test Service',
        'description': 'Something went wrong',
        'detected_at': '2023-10-01T10:00:00Z',
        'resolved_at': '2023-10-01T12:00:00Z'
    }

    events = []

    result = await generator.generate(incident, events)

    assert result['incident_id'] == 'inc-124'
    # Check that template content is used
    assert "The incident was detected by automated monitoring" in result['sections']['summary']
    assert "Generated with DevOps Sentinel AI" in result['markdown']
