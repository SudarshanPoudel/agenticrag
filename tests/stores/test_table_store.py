import pytest
from agenticrag.stores.table_store import TableStore
from agenticrag.types.core import TableData

@pytest.fixture
def store():
    return TableStore(connection_url="sqlite:///:memory:")

@pytest.fixture
def sample_data():
    return TableData(
        id=1,
        name="Sales Table",
        path="/data/sales.csv",
        structure_summary="Date, Product, Revenue"
    )

def test_store_and_fetch(store, sample_data):
    store.add(sample_data)
    fetched = store.fetch(sample_data.id)
    assert fetched == sample_data

def test_update(store, sample_data):
    store.add(sample_data)
    store.update(sample_data.id, name="Updated Table")
    fetched = store.fetch(sample_data.id)
    assert fetched.name == "Updated Table"
    assert fetched.path == sample_data.path
    assert fetched.structure_summary == sample_data.structure_summary

def test_delete(store, sample_data):
    store.add(sample_data)
    store.delete(sample_data.id)
    assert store.fetch(sample_data.id) is None

def test_fetch_all(store, sample_data):
    store.add(sample_data)
    all_data = store.fetch_all()
    assert len(all_data) == 1
    assert all_data[0] == sample_data

def test_index(store, sample_data):
    store.add(sample_data)
    result = store.index(name="Sales Table")
    assert len(result) == 1
    assert result[0] == store.fetch(sample_data.id)  
    empty = store.index(name="Nonexistent")
    assert empty == []
