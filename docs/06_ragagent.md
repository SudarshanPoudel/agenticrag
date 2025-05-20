# RAGAgent

The `RAGAgent` is a high-level controller that orchestrates the complete retrieval-augmented generation (RAG) pipeline. It autonomously selects relevant datasets, appropriate retrievers, and task-specific tools to fulfill user queries using an LLM as the decision-making engine.

```python
from agenticrag import RAGAgent

# Initialize the agent with retrievers and task tools
agent = RAGAgent(
    persistent_dir="./agenticrag_data",
    retrievers=[vector_retriever, table_retriever, sql_retriever],
    tasks=[qa_task, chart_task]
)

# Load data (if provided retriever's stores don't already have, you can load directly through RAGAgent)
agent.load_pdf("data/research.pdf", name="research_paper")
agent.load_csv("data/metrics.csv", name="performance_metrics")

# Run a user query
response = agent.invoke(
    "Generate a report on our Q1 performance including a chart of sales by region"
)

print(response.content)
```

---

### 🔍 What RAGAgent Does (Under the Hood)

The `RAGAgent` uses an LLM to perform tool selection, dataset relevance scoring, and task coordination in a multi-step reasoning loop. Here's a breakdown:

---

#### 1. **Query Understanding & Task Selection**

* The agent sends the query and the list of available tasks (e.g., QA, charting) to the LLM.
* The LLM returns the list of tasks it considers relevant.

#### 2. **Dataset Selection**

* The agent queries the metadata store (`MetaStore`) to find datasets relevant to the input query.
* Metadata includes names, descriptions, format etc.

#### 3. **Retriever Mapping**

* Based on the selected datasets, the agent chooses appropriate retrievers:

  * `VectorRetriever` for PDFs and text
  * `TableRetriever` for structured tabular data
  * `SQLRetriever` for external databases
  or any other custom retrieves for own kind of Data format

#### 4. **Tool Wrapping**

* Each retriever and task is wrapped as a `StructuredTool`, making them callable by the LLM with a schema-based interface.

#### 5. **LLM-Controlled Loop**

* The LLM receives:

  * Tool metadata (descriptions, names, schemas)
  * Dataset metadata
  * The original user query
* It responds with which tool to call and what arguments to use.
* The agent runs the tool and appends the result to the conversation.
* The loop continues until the LLM issues a `final_answer` call.

---

###  Example Decision Flow (Simplified)

```python
def invoke(self, query):
    tasks = self._select_tasks(query)
    datasets = self._select_relevant_data(query)
    retrievers = self._select_retrievers(datasets)
    
    tools_dict = wrap_as_structured_tools(retrievers + tasks)
    
    messages = build_prompt_with_metadata(tools=tools_dict, datasets=datasets, query=query)
    
    for i in range(max_iterations):
        tool_call = llm.invoke(messages)
        
        if tool_call.tool == "final_answer":
            return final_response(tool_call.args["answer"])
        
        output = tools_dict[tool_call.tool].invoke(tool_call.args)
        messages.append_output(tool_call, output)
```

---

### Key Features

* **LLM-Orchestrated Tool Use**: Uses a system prompt + structured tool descriptions to decide what to do.
* **Multi-Step Reasoning**: Iteratively calls tools and updates context.
* **Modular Retrieval**: Supports text, table, and SQL retrievers out of the box.
* **Pluggable Tasks**: Easily add new tasks by implementing the `BaseTask` interface.
