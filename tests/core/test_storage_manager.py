import os
import shutil
import pytest
from agenticrag.core import StorageManager  

TEST_DIR = "test_storage"


@pytest.fixture(autouse=True)
def cleanup():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    shutil.rmtree(TEST_DIR)


@pytest.fixture
def storage_manager():
    return StorageManager(local_dir=TEST_DIR)


def test_save_and_load(storage_manager):
    key = "folder1/test.txt"
    data = b"hello world"
    storage_manager.save(key, data)
    
    loaded = storage_manager.load(key)
    assert loaded == data

    # file should exist
    assert os.path.exists(os.path.join(TEST_DIR, key))


def test_delete(storage_manager):
    key = "delete_me.txt"
    data = b"bye"
    storage_manager.save(key, data)
    storage_manager.delete(key)
    
    assert not os.path.exists(os.path.join(TEST_DIR, key))


def test_copy_file(storage_manager):
    src = os.path.join(TEST_DIR, "src.txt")
    with open(src, "wb") as f:
        f.write(b"copy test")
    
    storage_manager.copy(src, "dest_folder")
    
    copied_path = os.path.join(TEST_DIR, "dest_folder", "src.txt")
    assert os.path.exists(copied_path)
    with open(copied_path, "rb") as f:
        assert f.read() == b"copy test"


def test_copy_folder(storage_manager):
    folder = os.path.join(TEST_DIR, "myfolder")
    os.makedirs(folder)
    with open(os.path.join(folder, "a.txt"), "wb") as f:
        f.write(b"a")
    with open(os.path.join(folder, "b.txt"), "wb") as f:
        f.write(b"b")
    
    storage_manager.copy(folder, "backup_folder")
    
    assert os.path.exists(os.path.join(TEST_DIR, "backup_folder", "a.txt"))
    assert os.path.exists(os.path.join(TEST_DIR, "backup_folder", "b.txt"))


@pytest.mark.asyncio
async def test_async_methods(storage_manager):
    key = "async_test.txt"
    data = b"async hello"
    
    await storage_manager.asave(key, data)
    loaded = await storage_manager.aload(key)
    assert loaded == data

    url = await storage_manager.aget_url(key)
    assert isinstance(url, str)

    await storage_manager.adelete(key)
    assert not os.path.exists(os.path.join(TEST_DIR, key))


@pytest.mark.asyncio
async def test_acopy_file(storage_manager):
    src = os.path.join(TEST_DIR, "async_src.txt")
    with open(src, "wb") as f:
        f.write(b"async copy")
    
    await storage_manager.acopy(src, "async_dest")
    
    copied_path = os.path.join(TEST_DIR, "async_dest", "async_src.txt")
    assert os.path.exists(copied_path)
    with open(copied_path, "rb") as f:
        assert f.read() == b"async copy"
