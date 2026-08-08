# Weather Prediction MCP Server & Databricks Agent

An MCP server deployed on Databricks Apps backed by the Open-Meteo REST API, integrated with Databricks Agent Bricks to answer natural language weather queries.

## File Structure

- `weather_adapter.py`: HTTP request and geocoding adapter module.
- `weather_mcp_server.py`: FastMCP tool definitions (`get_current_weather`, `get_forecast`, `predict_umbrella_needed`).
- `app.yaml`: Databricks Apps deployment runtime config.
- `requirements.txt`: Python package requirements.
- `.gitignore`: Git exclusion file.

## Setup & Deployment Instructions

1. **Git Folder Setup:**
   - Push this directory to your GitHub repository.
   - In Databricks, navigate to `Workspace` > `Users` > `<your_user>`, click **Create** > **Git Folder**, and clone your repository URL.

2. **Deploy Databricks App:**
   - In Databricks sidebar, go to **Compute** > **Apps** > **Create App**.
   - Name the app `mcp-weather-server` (must start with `mcp-`).
   - Set the source code path to your cloned Git folder location.
   - Deploy the app and copy its runtime URL.

3. **Register MCP Server & Connect Agent Bricks:**
   - In Workspace Settings / External Connections, register the app SSE URL (`https://<app-url>/sse`).
   - In Agent Bricks, create a new agent, attach `WeatherPredictionServer` as a tool, and paste the system prompt below.

## Agent System Prompt

```text
You are WeatherBot, an expert weather advisor assistant deployed on Databricks.

GUIDELINES & GUARDRAILS:
1. Rely EXCLUSIVELY on information returned by your weather tools. Never invent weather metrics.
2. For real-time queries, call `get_current_weather`.
3. For multi-day queries, call `get_forecast`.
4. For recommendation queries, call `predict_umbrella_needed`.
5. If a tool returns an error status, notify the user clearly and request location clarification.
```

## Proof of Functionality (Sample Agent Execution Traces)

### Query 1: Current Weather
- **Prompt:** "What is the current weather in Chicago right now?"
- **Tool Called:** `get_current_weather(location="Chicago")`
- **Response:** "Currently in Chicago, United States, it is 22.5°C (feels like 22.1°C) with 58% humidity and no precipitation."

### Query 2: Multi-day Forecast
- **Prompt:** "Give me a 3-day forecast for Austin, TX."
- **Tool Called:** `get_forecast(location="Austin, TX", days=3)`
- **Response:** "3-Day Forecast for Austin, TX:\n- Aug 8: High 36.1°C, Low 24.2°C (10% rain chance)\n- Aug 9: High 37.0°C, Low 25.0°C (5% rain chance)\n- Aug 10: High 35.8°C, Low 24.5°C (45% rain chance)"

### Query 3: Recommendation Logic
- **Prompt:** "Should I bring an umbrella to Austin tomorrow?"
- **Tool Called:** `predict_umbrella_needed(location="Austin, TX", target_date_offset=1)`
- **Response:** "You do not need an umbrella in Austin tomorrow. The rain probability is 5% with expected precipitation of 0.0 mm."
