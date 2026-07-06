#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RULE_NAMES = (
    "Direct",
    "Proxy",
    "ProxyMedia",
    "OpenAI",
    "AISuite",
    "Shopping",
    "US",
    "JP",
    "HK",
    "SG",
    "WiFiCallingUS",
    "WiFiCallingUK",
)


def convert_loon_to_clash(source: Path) -> str:
    output = ["payload:"]

    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            output.append("")
        elif line.startswith("#"):
            output.append(f"  {line}")
        else:
            output.append(f"  - {line}")

    return "\n".join(output).rstrip() + "\n"


def main() -> None:
    loon_dir = ROOT / "Rules" / "Loon"
    clash_dir = ROOT / "Rules" / "Clash"

    for name in RULE_NAMES:
        source = loon_dir / f"{name}.list"
        target = clash_dir / f"{name}.yaml"

        if not source.exists():
            raise FileNotFoundError(f"Missing source rule: {source.relative_to(ROOT)}")

        target.write_text(convert_loon_to_clash(source), encoding="utf-8")
        print(f"{source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
