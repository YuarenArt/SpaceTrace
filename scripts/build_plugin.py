"""Build a QGIS plugin ZIP from the current working tree."""

import argparse
from configparser import ConfigParser
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "SpaceTrace"
ROOT_FILES = (
    "__init__.py",
    "metadata.txt",
    "LICENSE",
    "README.md",
    "help.html",
    "icon.png",
    "requirements.txt",
    "resources.py",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "zip_build")
    args = parser.parse_args()
    metadata = ConfigParser()
    metadata.read(ROOT / "metadata.txt", encoding="utf-8")
    version = metadata["general"]["version"].strip()
    if not version or any(char not in "0123456789." for char in version):
        raise ValueError("Plugin version must contain only digits and dots")

    files = [ROOT / name for name in ROOT_FILES]
    files.extend(path for path in (ROOT / "src").rglob("*")
                 if path.is_file() and path.suffix in {".py", ".ui"})
    files.extend((ROOT / "i18n").glob("*.qm"))
    for path in files:
        if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError(f"Missing or unsafe plugin file: {path}")

    output = args.output_dir / f"{PACKAGE_NAME}-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, (Path(PACKAGE_NAME) / path.relative_to(ROOT)).as_posix())
    print(f"Created {output}")


if __name__ == "__main__":
    main()
