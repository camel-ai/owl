import importlib.util
import zipfile
from pathlib import Path


def _load_extract_zip():
    module_path = Path(__file__).parents[1] / "owl" / "utils" / "zip_utils.py"
    spec = importlib.util.spec_from_file_location("zip_utils", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract_zip


def test_extract_zip_uses_python_zip_support(tmp_path):
    archive_path = tmp_path / "documents.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/notes.txt", "hello")

    extract_path = tmp_path / "cache" / "documents"
    extracted = _load_extract_zip()(str(archive_path), str(extract_path))

    notes_path = extract_path / "nested" / "notes.txt"
    assert extracted == [str(notes_path)]
    assert notes_path.read_text() == "hello"
