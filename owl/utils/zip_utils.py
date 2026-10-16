import os
import zipfile


def extract_zip(zip_path: str, extract_path: str) -> list[str]:
    """Extract a zip archive with Python's cross-platform standard library."""
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_path)
    except zipfile.BadZipFile as e:
        raise RuntimeError(f"Failed to unzip file: {e}") from e

    extracted_files = []
    for root, _, files in os.walk(extract_path):
        for file in files:
            extracted_files.append(os.path.join(root, file))
    return extracted_files
