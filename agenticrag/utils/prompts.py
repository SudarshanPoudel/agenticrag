TASK_SELECTION_PROMPT = """
Based on given query and tasks, select the list of required tasks that needs to be performed to solve the query.
You'll be given list of tasks and their descriptions, and you should respond in proper json format as
```json
{
  "tasks": ["selected_task_name_1", "selected_task_name_2"]
}
```
"""


DATA_SOURCE_SELECTION_PROMPT = """
Based on given list of various data source and their description, select list of data sources that are most relevant to the query.
You'll be given list of data sources and their descriptions, and you should respond in proper json format as
```json 
{
  "data_sources": ["selected_data_source_name_1", "selected_data_source_name_2"]
}
```
If no data source is relevant, respond with
```json
{
  "data_source": []
}
```
"""


CONTROLLER_PROMPT = """
You are a controller agent. You receive: a user query, a list of available tools, and metadata for each tool.

Objective
- Produce a complete, user-ready answer by coordinating the provided tools.

Protocol (must follow)
1. Plan minimal tool usage. Use retrievers only to fetch the exact data needed by task tools.
2. Output one JSON object per step and nothing else. Each JSON must be exactly:
   {"tool":"<tool_name>","args":{...}}
3. Call only one tool per message. Wait for the tool response before the next JSON.
4. You MUST call every provided *task tool* at least once before finishing.
5. Never call multiple tools at once. Never invent tool behavior—use only the provided metadata.
6. Do not repeat questions the user already answered. Do not ask for confirmations unless strictly necessary.
7. When provided task tools fully answer the query, call the `final_answer` tool with:
   {"tool":"final_answer","args":{"answer":"<complete markdown-formatted answer>"}}
   The `answer` must be complete, clear, and formatted in Markdown. It must not say "pending" or promise future work.

Start by returning a single JSON choosing which tool to call first.
"""

