import pytest
import shutil
import os
import random
from agenticrag.loaders import TextLoader
from agenticrag.types.core import TextData, MetaData
from agenticrag.types.core import DataFormat
from agenticrag.stores import TextStore, MetaStore

@pytest.fixture
def real_text_store():
    path = f".chroma-{random.randint(0, 100000)}"
    shutil.rmtree(path, ignore_errors=True)
    store = TextStore(persistent_dir=path)
    yield store
    shutil.rmtree(path, ignore_errors=True)

@pytest.fixture
def real_meta_store():
    db_path = f"sqlite{random.randint(0, 100000)}.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    store = MetaStore(connection_url=f"sqlite:///{db_path}")
    yield store
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def text_loader(real_text_store, real_meta_store):
    return TextLoader(
        text_store=real_text_store,
        meta_store=real_meta_store,
    )

def test_load_text(text_loader):
    text_loader.load_text(text="This is a test paragraph repeated. " * 3, name="sample")

    chunks = text_loader.text_store.fetch_all()
    metas = text_loader.meta_store.fetch_all()

    assert len(chunks) > 0
    assert all(isinstance(chunk, TextData) for chunk in chunks)

    assert len(metas) >= 1
    meta = next((m for m in metas if m.name == "sample"), None)
    assert meta is not None
    assert isinstance(meta, MetaData)
    assert meta.format == DataFormat.TEXT

def test_load_web(text_loader):
    text_loader.load_web("https://en.wikipedia.org/wiki/Example")

    chunks = text_loader.text_store.fetch_all()
    metas = text_loader.meta_store.fetch_all()

    assert len(chunks) > 0
    assert any(isinstance(chunk, TextData) for chunk in chunks)
    assert any(meta.source == "https://en.wikipedia.org/wiki/Example" for meta in metas)
