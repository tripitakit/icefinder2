#!/usr/bin/env python3
import argparse
import copy
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
ICEFINDER_PY = ROOT_DIR / "ICEfinder2.py"


def ensure_local_python():
    if VENV_PYTHON.exists():
        current_python = Path(sys.executable).resolve()
        if current_python != VENV_PYTHON.resolve():
            os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])


ensure_local_python()

try:
    from Bio import SeqIO
except ImportError as exc:
    sys.stderr.write("Biopython is required to run run-single.py.\n")
    sys.stderr.write("Install the local environment first with requirements.txt.\n")
    raise SystemExit(1) from exc


def sanitize_name(value):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = cleaned.strip("._")
    return cleaned[:48] or "record"


def build_analysis_stem(input_stem, index):
    base = sanitize_name(input_stem)[:10] or "single"
    return f"{base}_{index:04d}"


def detect_records(input_path):
    parsers = (("fasta", ".fasta"), ("genbank", ".gbk"))
    for file_format, default_suffix in parsers:
        with input_path.open() as handle:
            records = list(SeqIO.parse(handle, file_format))
        if records:
            return file_format, default_suffix, records
    raise ValueError("Input file is not a standard FASTA/GenBank format")


def build_output_dir(input_path):
    stem = sanitize_name(input_path.stem)
    base_dir = ROOT_DIR / "result" / f"{stem}__single_wrapper"
    if not base_dir.exists():
        return base_dir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return ROOT_DIR / "result" / f"{stem}__single_wrapper_{timestamp}"


def setup_logger(log_path):
    logger = logging.getLogger("run-single")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def prepare_work_inputs(records, file_format, suffix, work_dir, input_stem, logger):
    run_entries = []
    for index, record in enumerate(records, start=1):
        record_id = sanitize_name(record.id or f"record_{index:03d}")
        split_stem = f"{sanitize_name(input_stem)}__contig_{index:03d}__{record_id}"
        analysis_stem = build_analysis_stem(input_stem, index)

        work_record = copy.deepcopy(record)
        work_record.id = analysis_stem
        work_record.name = analysis_stem
        if file_format == "fasta":
            work_record.description = analysis_stem
        else:
            work_record.description = ""

        work_path = work_dir / f"{analysis_stem}{suffix}"
        with work_path.open("w") as handle:
            SeqIO.write(work_record, handle, file_format)
        logger.info(
            "Prepared ICEfinder work input %s for source record '%s' (output label: %s)",
            work_path,
            record.id,
            split_stem,
        )

        run_entries.append(
            {
                "index": index,
                "source_record_id": record.id,
                "split_stem": split_stem,
                "analysis_stem": analysis_stem,
                "work_input": str(work_path),
            }
        )
    return run_entries


def write_no_hits_marker(result_dir, entry, logger):
    icesum_files = sorted(result_dir.glob("*_ICEsum.json"))
    if not icesum_files:
        return None

    for icesum_file in icesum_files:
        try:
            payload = json.loads(icesum_file.read_text())
        except json.JSONDecodeError:
            return None
        if payload:
            return None

    marker_path = result_dir / "no_hits.txt"
    message = (
        f"No ICE/IME regions were reported for source record '{entry['source_record_id']}' "
        f"(internal run id: {entry['analysis_stem']}).\n"
        f"See {icesum_files[0].name} for the empty summary emitted by ICEfinder.\n"
    )
    marker_path.write_text(message)
    logger.info("Wrote no-hit marker %s", marker_path)
    return str(marker_path)


def run_single(run_entries, extra_args, runs_dir, logger):
    manifest_runs = []
    expects_results = not any(arg in {"-h", "--help", "-v", "--version"} for arg in extra_args)
    for entry in run_entries:
        work_input = Path(entry["work_input"])
        split_stem = entry["split_stem"]
        analysis_stem = entry["analysis_stem"]
        run_cmd = [sys.executable, str(ICEFINDER_PY), "-i", str(work_input), "-t", "Single", *extra_args]
        logger.info(
            "Launching SINGLE flow for record '%s' using internal run id %s",
            entry["source_record_id"],
            analysis_stem,
        )
        try:
            subprocess.run(run_cmd, cwd=ROOT_DIR, check=True)
        except subprocess.CalledProcessError as exc:
            logger.error("SINGLE flow failed for record '%s' (run id %s)", entry["source_record_id"], analysis_stem)
            logger.error("Failed command: %s", " ".join(run_cmd))
            raise SystemExit(exc.returncode) from exc

        source_result_dir = ROOT_DIR / "result" / analysis_stem
        target_result_dir = runs_dir / split_stem
        if expects_results:
            if target_result_dir.exists():
                shutil.rmtree(target_result_dir)
            if source_result_dir.exists():
                shutil.move(str(source_result_dir), str(target_result_dir))
                logger.info("Stored result directory in %s", target_result_dir)
                no_hits_marker = write_no_hits_marker(target_result_dir, entry, logger)
            else:
                logger.warning("Expected result directory %s was not found", source_result_dir)
                no_hits_marker = None
        else:
            no_hits_marker = None

        manifest_runs.append(
            {
                **entry,
                "result_dir": str(target_result_dir),
                "no_hits_marker": no_hits_marker,
            }
        )
    return manifest_runs


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run ICEfinder in Single mode, splitting multi-record FASTA/GenBank inputs into one Single run per record."
    )
    parser.add_argument("input_file", help="Input FASTA or GenBank file")
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Extra ICEfinder arguments passed through after the fixed Single mode flags",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input_file).expanduser().resolve()
    extra_args = args.extra_args

    if any(arg in {"-i", "--input", "-t", "--type"} for arg in extra_args):
        sys.stderr.write("run-single.py manages -i/--input and -t/--type itself.\n")
        return 1

    if not input_path.is_file():
        sys.stderr.write(f"Input file not found: {input_path}\n")
        return 1

    try:
        file_format, suffix, records = detect_records(input_path)
    except ValueError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1

    output_dir = build_output_dir(input_path)
    work_dir = output_dir / "work_inputs"
    runs_dir = output_dir / "runs"
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(output_dir / "run-single.log")
    logger.info("Input file: %s", input_path)
    logger.info("Detected format: %s", file_format)
    logger.info("Detected %d record(s)", len(records))
    logger.info("Output directory: %s", output_dir)

    run_entries = prepare_work_inputs(records, file_format, suffix, work_dir, input_path.stem, logger)
    manifest_runs = run_single(run_entries, extra_args, runs_dir, logger)

    manifest = {
        "input_file": str(input_path),
        "format": file_format,
        "record_count": len(records),
        "output_dir": str(output_dir),
        "runs": manifest_runs,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info("Wrote manifest to %s", manifest_path)
    logger.info("Completed %d Single run(s)", len(manifest_runs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
