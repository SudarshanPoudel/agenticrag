from src.controller import ControllerAgent
from src.tasks import ChartGenerationTask, QATask
from src.retrievers import VectorRetriever, TableDataRetriever
from src.retrievers.sql_retriever import SQLRetriever
from src.dataconnectors import DBConnector

# connect = DBConnector()
# connect.connect_db(
#     name="movie_db",
#     connection_url="postgresql://postgres:sudarshan@localhost:5432/dvdrental",
# )

# from src.dataloaders import TableLoader

# loader = TableLoader()
# loader.load_csv(source="files/movies_data.csv")

controller = ControllerAgent(
    tasks=[ChartGenerationTask(), QATask()],
    retrievers=[VectorRetriever(), TableDataRetriever(), SQLRetriever()]
)

controller.invoke("Generate a histogram showing average runtime of each movies (from file, not db)")

