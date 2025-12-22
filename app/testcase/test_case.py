from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Step:
    line_no: int
    text: str


@dataclass
class TestCase:
    name: str
    config: Dict[str, int]
    steps: List[Step]

def load_testcase(path: str) -> TestCase:
    name = None
    config = {}
    steps = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            # Skip empty lines
            if not line:
                continue

            # Comment
            if line.startswith("#"):
                continue

            # Testcase name
            if line.startswith("@testcase"):
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid @testcase at line {line_no}")
                name = parts[1]
                continue

            # Config
            if line.startswith("@"):
                key_value = line[1:].split(maxsplit=1)
                if len(key_value) != 2:
                    raise ValueError(f"Invalid config at line {line_no}")
                key, value = key_value
                config[key] = int(value)
                continue

            # Step
            steps.append(Step(line_no=line_no, text=line))

    if not name:
        raise ValueError("Missing @testcase name")

    return TestCase(name=name, config=config, steps=steps)
