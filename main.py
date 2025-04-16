from src.dataloaders import TextLoader, TableLoader
# from src.datastores import TextStore, MetaStore, TableStore
# from src.controller import ControllerAgent

# store = TableStore()
# res = store.fetch('name', 'movies_data.csv')
# print(res)
# store.delete()
# meta_store = MetaStore()
# meta_store.delete()

# loader = TableLoader()
# loader.load_csv('data/movies_data.csv')


from src.tasks import TableQueryTask

task = TableQueryTask()
print(task.execute('movies_data.csv', 'What are top 10 highest earning movies of all time'))
