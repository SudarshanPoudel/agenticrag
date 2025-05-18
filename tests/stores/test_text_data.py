import pytest
import numpy as np
import shutil
from typing import List
from agentic_rag.types.schemas import TextData
import random
from agentic_rag.stores.text_store import TextStore

@pytest.fixture(params=['custom', 'default'])
def text_store(request):
    path = f".test_chroma_{request.param}-{random.randint(0, 10000)}"
    shutil.rmtree(path, ignore_errors=True)
    
    if request.param == 'default':
        store = TextStore(persistent_dir=path)
    else:
        # Custom embedding returns fixed vector
        def simple_embedding(text: str):
            return np.array([0.1, 0.2, 0.3], dtype=np.float32)
        store = TextStore(persistent_dir=path, embedding_function=simple_embedding)
    
    yield store
    shutil.rmtree(path, ignore_errors=True)

def test_store_and_fetch(text_store):
    data = TextData(id="1", name="Test1", text="Hello world")
    text_store.add(data)
    fetched = text_store.fetch("1")
    assert fetched is not None
    assert fetched.id == data.id
    assert fetched.name == data.name
    assert fetched.text == data.text

def test_fetch_nonexistent(text_store):
    assert text_store.fetch("nonexistent") is None

def test_update(text_store):
    data = TextData(id="2", name="Old", text="Old text")
    text_store.add(data)
    text_store.update("2", name="New", text="New text")
    fetched = text_store.fetch("2")
    assert fetched.name == "New"
    assert fetched.text == "New text"

def test_delete(text_store):
    data = TextData(id="3", name="Del", text="Delete me")
    text_store.add(data)
    text_store.delete("3")
    assert text_store.fetch("3") is None

def test_fetch_all(text_store):
    d1 = TextData(id="4", name="F1", text="Text one")
    d2 = TextData(id="5", name="F2", text="Text two")
    text_store.add(d1)
    text_store.add(d2)
    all_items = text_store.fetch_all()
    ids = {item.id for item in all_items}
    assert "4" in ids and "5" in ids

def test_knn_search(text_store):
    text_store.add(TextData(id="6", name="Apple", text="Apple is red"))
    text_store.add(TextData(id="6", name="Apple", text="Banana Information"))
    text_store.add(TextData(id="7", name="Banana", text="Banana is yellow"))
    results = text_store.knn_search("apple", document_name="Apple", top_k=1)
    assert len(results) == 1

def test_index(text_store):
    d1 = TextData(id="8", name="Idx1", text="Tag A text")
    d2 = TextData(id="9", name="Idx2", text="Tag B text")
    text_store.add(d1)
    text_store.add(d2)
    results = text_store.index(name="Idx1")
    assert any(r.id == "8" for r in results)
    assert all(r.name == "Idx1" for r in results)
