import os
import tempfile
import pytest
from agenticrag.loaders import TableLoader
from agenticrag.types import DataFormat
from agenticrag.types import TableData, MetaData
from agenticrag.stores import TableStore, MetaStore

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
    persistence_dir = tmp_path / "saved_csvs"
    return TableLoader(
        persistence_dir=str(persistence_dir),
        store=real_table_store,
        meta_store=real_meta_store
    )

def test_load_csv(temp_csv_file, table_loader):
    table_loader.load_csv(temp_csv_file)

    table_data = table_loader.store.get_all()
    meta_data = table_loader.meta_store.get_all()

    assert any(isinstance(td, TableData) and td.structure_summary for td in table_data)
    assert any(isinstance(md, MetaData) and md.format == DataFormat.TABLE for md in meta_data)

    paths = [td.path for td in table_data]
    for path in paths:
        assert os.path.exists(path)
