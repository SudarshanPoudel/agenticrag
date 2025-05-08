from src.controller import ControllerAgent
from src.tasks import ChartGenerationTask, QATask
from src.retrievers import VectorRetriever, TableDataRetriever
from src.dataloaders import TableLoader, TextLoader


controller = ControllerAgent(
    tasks=[ChartGenerationTask(), QATask()],
    retrievers=[VectorRetriever(), TableDataRetriever()]
)


# table_loader = TableLoader()
# text_loader = TextLoader()

# table_loader.load_csv(source="files/movies_data.csv")

controller.invoke("List out top 10 movies with highest budget and make bar graph of showing it.")