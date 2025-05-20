import argparse
import csv
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

from requests import Session
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT = """You are simulating a junior developer who has:
- **Basic knowledge of Java (syntax, classes, functions, control structures, basic OOP)**
- **No prior knowledge of Apache Hive or its libraries**

I will give you a piece of Java code that uses Apache Hive.
Estimate, as precisely as possible, how many **seconds** this junior developer would need to fully understand the code.
"Understanding" means:
- They can explain what the code does overall
- They can follow what each class/method does

Here is the code:
```java
{code}
```

DO NOT GREET, THINK, OR REASON. NO OTHER TEXT.
Return **only** a json object. Do not output anything else."""


def read_source(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.exception("Error reading source code %s: %s", path, e)
        sys.exit(1)


def read_input_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logger.exception("Error reading input CSV %s: %s", path, e)
        sys.exit(1)


def ask_ollama_via_http(session: Session, prompt: str, model: str, timeout: int) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "seconds": {"type": "integer"},
            },
            "required": ["seconds"],
        },
    }
    resp = session.post(OLLAMA_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["response"].strip()


def process_row(
    row: dict[str, Any],
    session: Session,
    model: str,
    timeout: int,
    cache_dir: Path,
    ask_repeats: int,
) -> list[int]:
    file_hash = hashlib.sha256(row["file_path"].encode()).hexdigest()
    code = read_source(cache_dir / f"{file_hash}.txt")
    seconds = []
    for _ in range(ask_repeats):
        try:
            output_raw = ask_ollama_via_http(session, PROMPT.format(code=code), model, timeout)
            output = json.loads(output_raw.strip())
            seconds.append(int(output["seconds"]))
        except Exception as e:
            logger.exception("Unexpected output from model for file %s: %s", row["file_path"], e)
            seconds.append(-1)
    return seconds


def process_rows(
    input_csv: Path,
    output_csv: Path,
    session: Session,
    model: str,
    timeout: int,
    cache_dir: Path,
    ask_repeats: int,
) -> None:
    input_rows = read_input_csv(input_csv)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "our_seconds"] + [f"llm_seconds_{i}" for i in range(ask_repeats)])

        for row in tqdm(input_rows, desc="Processing files"):
            file_path = row["file_path"]
            try:
                seconds = process_row(
                    row,
                    session,
                    model,
                    timeout,
                    cache_dir,
                    ask_repeats,
                )
                writer.writerow([file_path, row["measures"]] + seconds)
            except KeyboardInterrupt:
                logger.info("Interrupted at %s", file_path)
                sys.exit(1)
            except Exception as e:
                logger.exception("Error processing %s: %s", file_path, e)
                sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Batch estimate times for Java files listed in a CSV")
    parser.add_argument(
        "--input-csv",
        "-i",
        type=Path,
        required=True,
        help="Path to input CSV file with file_path column",
    )
    parser.add_argument(
        "--output-csv",
        "-o",
        type=Path,
        required=True,
        help="Path to output CSV to write file_path and estimated seconds",
    )
    parser.add_argument("--model", "-m", required=True, help="Model to use")
    parser.add_argument("--timeout", "-t", type=int, default=3 * 60, help="Timeout for the model")
    parser.add_argument("--cache-dir", "-c", type=Path, default="./code_cache", help="Directory to cached code")
    parser.add_argument("--ask-repeats", "-r", type=int, default=5, help="Number of times to ask the model")
    args = parser.parse_args()

    logger.info("It could take some time to initialize the model...")

    session = Session()
    process_rows(
        args.input_csv,
        args.output_csv,
        session,
        args.model,
        args.timeout,
        args.cache_dir,
        args.ask_repeats,
    )
    session.close()


if __name__ == "__main__":
    main()
