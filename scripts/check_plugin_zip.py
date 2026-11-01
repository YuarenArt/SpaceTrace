"""Validate the plugin ZIP before installing or publishing it."""

import argparse
from configparser import ConfigParser
import io
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from build_plugin import PACKAGE_NAME, ROOT, ROOT_FILES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    with ZipFile(args.archive) as archive:
        names = archive.namelist()
        if archive.testzip() is not None or len(names) != len(set(names)):
            raise ValueError("ZIP is corrupt or contains duplicate entries")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != PACKAGE_NAME:
                raise ValueError(f"Unexpected archive path: {name}")
            relative = Path(*path.parts[1:])
            source = ROOT / relative
            if not source.is_file() or not source.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError(f"Unexpected archive file: {name}")
            if archive.read(name) != source.read_bytes():
                raise ValueError(f"Archive file differs from checkout: {name}")
        required = {f"{PACKAGE_NAME}/{name}" for name in ROOT_FILES}
        required.update(f"{PACKAGE_NAME}/{path.relative_to(ROOT).as_posix()}"
                        for path in (ROOT / "src").rglob("*")
                        if path.is_file() and path.suffix in {".py", ".ui"})
        required.update(f"{PACKAGE_NAME}/{path.relative_to(ROOT).as_posix()}"
                        for path in (ROOT / "i18n").glob("*.qm"))
        if set(names) != required:
            raise ValueError(f"Unexpected or missing files: {sorted(set(names) ^ required)}")
        metadata = ConfigParser()
        metadata.read_file(io.StringIO(archive.read(f"{PACKAGE_NAME}/metadata.txt").decode("utf-8")))
        for key in ("name", "version", "qgisMinimumVersion", "qgisMaximumVersion", "about"):
            if not metadata["general"].get(key, "").strip():
                raise ValueError(f"Missing plugin metadata: {key}")
        version = metadata["general"]["version"].strip()
        if args.archive.name != f"{PACKAGE_NAME}-{version}.zip":
            raise ValueError("Archive name and plugin version do not match")
    if args.archive.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Plugin archive exceeds the QGIS repository size limit")
    print(f"Plugin ZIP validated: {args.archive} ({len(names)} files)")


if __name__ == "__main__":
    main()
