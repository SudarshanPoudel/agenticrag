# 5. Tasks

Tasks are the components that perform operations on retrieved data to accomplish user goals, such as answering questions, generating reports etc.


### QuestionAnsweringTask

Answers questions based on retrieved context.

```python
from agenticrag.tasks import QuestionAnsweringTask

# Initialize
qa_task = QuestionAnsweringTask()

# Execute task with retrieved context
answer = qa_task.execute(
    question="What are the key benefits of transformer architectures?",
    context_file="./retrieved_data/text_data.txt",
)

print(answer)
```

### ChartGenerationTask

Creates data visualizations from retrieved data.

```python
from agenticrag.tasks import ChartGenerationTask

# Initialize
chart_task = ChartGenerationTask(save_charts_at="./charts")

# Generate chart from retrieved data
result = chart_task.execute(
    query="Create a bar chart showing sales by region",
    file_file="./retrieved_data/table_data.csv",
)

print(result)
```

### Custom Task Example

```python
from agenticrag.tasks import BaseTask
from agenticrag.utils.llm import get_default_llm()

class SentimentAnalysisTask(BaseTask):
    def __init__(self):
        pass

    @property
    def name(self):
        return "sentiment_analysis"

    @property
    def description(self):
        return (
            "This task takes a Text file path and returns if file content is positive or negative"
        )
        
    def execute(self, context_file):
        # Read context
        with open(context_file, 'r') as f:
            text = f.read()
            
        # Perform sentiment analysis
        # (Implementation depends on your preferred NLP approach)
        is_positive = True # Let's just assume this

        if is_positive:
            return "Provided file has positive sentiment with 95% score"
        
        else:
            return "Provided file has negative sentiment with 10%  positive score"
```

**NOTE:**
*Similar to retrieve's .retrieve() method, .execute() should be clear, so much so no llm should be confused when calling this method and when value is returned get clear idea what has been done*