import os
import pytest
import tempfile
import shutil


@pytest.fixture
def temp_db_path():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_error_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_data_dir():
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture
def icbc_test_file(test_data_dir):
    return os.path.join(test_data_dir, "icbc_test.csv")


@pytest.fixture
def cmb_test_file(test_data_dir):
    return os.path.join(test_data_dir, "cmb_test.csv")


@pytest.fixture
def icbc_with_errors_file(test_data_dir):
    return os.path.join(test_data_dir, "icbc_with_errors.csv")
