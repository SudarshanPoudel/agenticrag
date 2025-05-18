import os
import tempfile
import pytest
from agentic_rag.loaders import TableLoader
from agentic_rag.types.core import DataFormat
from agentic_rag.types.schemas import TableData, MetaData
from agentic_rag.stores import TableStore, MetaStore

@pytest.fixture
def real_table_store():
    return TableStore()

@pytest.fixture
def real_meta_store():
    return MetaStore()

@pytest.fixture
def temp_csv_file():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".csv") as tmp:
        tmp.write("col1,col2\nval1,val2\n")
        tmp.flush()
        yield tmp.name
    os.remove(tmp.name)

@pytest.fixture
def table_loader(tmp_path, real_table_store, real_meta_store):
    persistence_folder = tmp_path / "saved_csvs"
    return TableLoader(
        persistence_folder=str(persistence_folder),
        store=real_table_store,
        meta_store=real_meta_store
    )

def test_load_csv(temp_csv_file, table_loader):
    table_loader.load_csv(temp_csv_file)

    table_data = table_loader.store.fetch_all()
    meta_data = table_loader.meta_store.fetch_all()

    assert any(isinstance(td, TableData) and td.structure_summary for td in table_data)
    assert any(isinstance(md, MetaData) and md.format == DataFormat.TABLE for md in meta_data)

    paths = [td.path for td in table_data]
    for path in paths:
        assert os.path.exists(path)
