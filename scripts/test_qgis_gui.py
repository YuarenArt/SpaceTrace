"""Run the real QGIS interface scenarios against a built plugin ZIP."""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "offline": {"E2E-01", "E2E-02", "E2E-06", "E2E-07", "E2E-10",
                "E2E-11", "E2E-14", "E2E-16", "E2E-17", "E2E-18"},
    "mock-api": {"E2E-03", "E2E-04", "E2E-05", "E2E-08", "E2E-09",
                 "E2E-12", "E2E-13", "E2E-15", "E2E-19", "E2E-20", "E2E-21"},
    "live": {"E2E-03", "E2E-04"},
}


def redact(text):
    for secret in (os.environ.get("SPACETRACE_LOGIN"), os.environ.get("SPACETRACE_PASSWORD")):
        if secret:
            text = text.replace(secret, "<redacted>")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=EXPECTED, required=True)
    parser.add_argument("--plugin-zip", type=Path, required=True)
    parser.add_argument("--reports-dir", type=Path)
    args = parser.parse_args()

    if args.mode == "live" and not all(os.environ.get(k) for k in ("SPACETRACE_LOGIN", "SPACETRACE_PASSWORD")):
        raise SystemExit("Live mode requires SPACETRACE_LOGIN and SPACETRACE_PASSWORD")
    if args.reports_dir:
        args.reports_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="spacetrace-qgis-e2e-") as tmp:
        work = Path(tmp)
        plugins = work / "profiles" / "test" / "python" / "plugins"
        plugins.mkdir(parents=True)
        with ZipFile(args.plugin_zip) as archive:
            for item in archive.infolist():
                path = PurePosixPath(item.filename)
                if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "SpaceTrace":
                    raise ValueError(f"Unsafe plugin archive member: {item.filename}")
            archive.extractall(plugins)
        if not (plugins / "SpaceTrace" / "metadata.txt").is_file():
            raise ValueError("Plugin archive is missing SpaceTrace/metadata.txt")

        (work / "iss.txt").write_text(
            "1 25544U 98067A   25087.72483446  .00032194  00000-0  56484-3 0  9999\n"
            "2 25544  51.6386 345.5386 0004029  59.5799 332.6073 15.50242233502686\n",
            encoding="ascii",
        )
        env = os.environ.copy()
        env.update({
            "SPACETRACE_E2E_DIR": str(work),
            "SPACETRACE_LOG_PATH": str(work / "plugin.log"),
            "SPACETRACE_REPO_ROOT": str(ROOT),
            "SPACETRACE_E2E_MODE": args.mode,
            "SPACETRACE_EXPECT_PLUGIN_DIR": str(plugins / "SpaceTrace"),
            "SPACETRACE_E2E_DEBUG_HANGS": "1",
            "QGIS_PLUGINPATH": str(plugins),
            "QT_QPA_PLATFORM": env.get("QT_QPA_PLATFORM", "offscreen"),
            "DISPLAY": env.get("DISPLAY", ":99"),
            "PYTHONOPTIMIZE": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        startup = "qgis_startup.py" if args.mode == "offline" else "qgis_spacetrack_startup.py"
        scenarios = [(startup, "result.json")]
        if args.mode == "offline":
            scenarios.append(("qgis_reopen_startup.py", "reopen_result.json"))

        seen = set()
        for script, report_name in scenarios:
            print(f"Running {script} ({args.mode})", flush=True)
            command = ["qgis", "--nologo", "--profiles-path", str(work / "profiles"),
                       "--profile", "test", "--code", str(ROOT / "test" / "e2e" / script)]
            try:
                result = subprocess.run(command, env=env, capture_output=True, text=True,
                                        errors="replace", timeout=180, check=False)
                output = redact(result.stdout + result.stderr)
            except subprocess.TimeoutExpired as error:
                parts = (error.stdout or b"", error.stderr or b"")
                partial = "".join(part.decode("utf-8", errors="replace") if isinstance(part, bytes)
                                  else part for part in parts)
                if args.reports_dir:
                    (args.reports_dir / f"{script}.log").write_text(redact(partial), encoding="utf-8")
                    plugin_log = work / "plugin.log"
                    if plugin_log.exists():
                        (args.reports_dir / "plugin.log").write_text(
                            redact(plugin_log.read_text(encoding="utf-8", errors="replace")), encoding="utf-8"
                        )
                raise RuntimeError(f"QGIS timed out running {script}") from error
            if args.reports_dir:
                (args.reports_dir / f"{script}.log").write_text(output, encoding="utf-8")
            report_path = work / report_name
            if not report_path.exists():
                raise RuntimeError(f"QGIS did not produce {report_name} (exit {result.returncode}):\n{output[-4000:]}")
            report_text = redact(report_path.read_text(encoding="utf-8"))
            if args.reports_dir:
                (args.reports_dir / report_name).write_text(report_text, encoding="utf-8")
            report = json.loads(report_text)
            if result.returncode or not report.get("ok"):
                raise RuntimeError(f"QGIS scenario {script} failed (exit {result.returncode}):\n{report_text}")
            seen.update(item["id"] for item in report["scenarios"])

        if seen != EXPECTED[args.mode]:
            raise RuntimeError(f"Unexpected {args.mode} scenarios: {sorted(seen)}")
        print(f"QGIS {args.mode}: {len(seen)} scenarios passed: {', '.join(sorted(seen))}")


if __name__ == "__main__":
    main()
