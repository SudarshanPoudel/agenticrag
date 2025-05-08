import shutil
import os
from dotenv import load_dotenv

from .base import BaseDataLoader
from ..datastores import TableStore
from ..types.core import TableData, MetaData
from .utils.text_to_desc import csv_to_desc
from .utils.csv_summary import summarize_csv

from ..utils.logging_config import setup_logger

load_dotenv()
logger = setup_logger(__name__)

class TableLoader(BaseDataLoader):
    def __init__(self):
        super().__init__()

    @property
    def data_store(self):
        return TableStore()
    
    def load_csv(self, source:str, name:str = None, description:str = None):
        save_dir = os.getenv("SAVE_FILES_AT") or "files"
        os.makedirs(save_dir, exist_ok=True)
        destination_path = os.path.join(save_dir, os.path.basename(source))
        shutil.copy(source, destination_path)

        if name is None:
            name = os.path.basename(source)
        if description is None:
            description = csv_to_desc(destination_path)
        
        summary = summarize_csv(file_path=destination_path)
        
        data = TableData(name=name, description=description, path=destination_path, source=source, summary=summary)
        self.data_store.store(data=data)

        metadata = MetaData(type=self.data_store.source_data_type, name=name, description=description)
        self.meta_store.store(data=metadata)
    