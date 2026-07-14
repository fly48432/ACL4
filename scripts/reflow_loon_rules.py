#!/usr/bin/env python3
"""把 Loon 本地 [Rule] 段的临时规则回流进仓库 Rules/Loon/*.list。

半自动、对 default.lcf 严格只读；--apply 前打印迁移计划供确认。
设计见 docs/superpowers/specs/2026-07-08-loon-local-rules-reflow-design.md。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOON_DIR = ROOT / "Rules" / "Loon"
DEFAULT_LCF = (
    Path.home()
    / "Library/Mobile Documents/iCloud~com~ruikq~decar/Documents/Configs/default.lcf"
)

# 策略名 → 目标文件（设计文档「策略名 → 目标文件映射」）
POLICY_TO_FILE = {
    "DIRECT": "Direct.list",
    "节点选择": "Proxy.list",
    "美国节点": "US.list",
    "日本节点": "JP.list",
    "香港节点": "HK.list",
    "狮城节点": "SG.list",
}
MIGRATABLE_TYPES = {"DOMAIN-SUFFIX", "DOMAIN", "DOMAIN-KEYWORD"}


class Candidate:
    __slots__ = ("type", "value", "policy", "target", "status", "reason")

    def __init__(self, rtype, value, policy):
        self.type = rtype
        self.value = value
        self.policy = policy
        self.target = None      # 目标文件名
        self.status = None      # migrate | skip | duplicate
        self.reason = None

    @property
    def line(self) -> str:
        return f"{self.type},{self.value}"


def read_rule_section(lcf_path: Path) -> list[str]:
    """返回 [Rule] 段的原始非注释、非空行（不含 FINAL,FINAL）。只读。"""
    lines = lcf_path.read_text(encoding="utf-8").splitlines()
    out, in_rule = [], False
    for raw in lines:
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            in_rule = s.lower() == "[rule]"
            continue
        if not in_rule or not s or s.startswith("#"):
            continue
        if s.upper() == "FINAL,FINAL":
            continue
        out.append(s)
    return out


def parse_candidates(rule_lines: list[str]) -> list[Candidate]:
    cands = []
    for s in rule_lines:
        fields = [f.strip() for f in s.split(",")]
        if len(fields) < 3:
            c = Candidate(fields[0] if fields else s, "", "")
            c.status, c.reason = "skip", f"无法解析（字段数 {len(fields)}）：{s}"
            cands.append(c)
            continue
        cands.append(Candidate(fields[0].upper(), fields[1], fields[-1]))
    return cands


def load_existing_values() -> dict[str, set[str]]:
    """仓库各 .list 里已存在的 TYPE,value 行（用于查重）。返回 {文件名: {规则行}}。"""
    existing = {}
    for path in sorted(LOON_DIR.glob("*.list")):
        vals = set()
        for raw in path.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if s and not s.startswith("#"):
                vals.add(s)
        existing[path.name] = vals
    return existing


def build_plan(cands: list[Candidate], existing: dict[str, set[str]]) -> list[Candidate]:
    all_lines = set().union(*existing.values()) if existing else set()
    for c in cands:
        if c.status == "skip":  # 解析失败的保持原样
            continue
        if c.type not in MIGRATABLE_TYPES:
            c.status, c.reason = "skip", f"非域名规则（{c.type}），不自动迁移"
            continue
        target = POLICY_TO_FILE.get(c.policy)
        if target is None:
            c.status, c.reason = "skip", f"策略「{c.policy}」无映射，需人工决定"
            continue
        c.target = target
        if c.line in all_lines:
            c.status, c.reason = "duplicate", "仓库已存在，仅需在 Loon 里删除"
        else:
            c.status = "migrate"
    return cands


def print_plan(cands: list[Candidate]) -> None:
    migrate = [c for c in cands if c.status == "migrate"]
    dup = [c for c in cands if c.status == "duplicate"]
    skip = [c for c in cands if c.status == "skip"]

    print("=" * 56)
    print(f"Loon 本地规则回流计划（共 {len(cands)} 条）")
    print("=" * 56)

    if migrate:
        print(f"\n▶ 待迁移（{len(migrate)}）：")
        for c in migrate:
            print(f"    {c.line:<45} → {c.target}  （策略 {c.policy}）")
    if dup:
        print(f"\n▷ 已存在，仅需在 Loon 删除（{len(dup)}）：")
        for c in dup:
            print(f"    {c.line:<45} （{c.target}）")
    if skip:
        print(f"\n✗ 跳过（{len(skip)}）：")
        for c in skip:
            print(f"    {c.line or c.reason:<45} {c.reason}")

    if not migrate:
        print("\n无待迁移规则。")


def apply_plan(cands: list[Candidate], do_push: bool) -> None:
    migrate = [c for c in cands if c.status == "migrate"]
    if not migrate:
        print("\n没有待迁移规则，未做任何改动。")
        return

    by_file: dict[str, list[Candidate]] = {}
    for c in migrate:
        by_file.setdefault(c.target, []).append(c)

    changed = []
    for fname, items in sorted(by_file.items()):
        path = LOON_DIR / fname
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        text += "".join(f"{c.line}\n" for c in items)
        path.write_text(text, encoding="utf-8")
        changed.append(str(path.relative_to(ROOT)))
        print(f"  追加 {len(items)} 条 → {path.relative_to(ROOT)}")

    print("\n生成 Clash 规则（sync_rules.py）...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_rules.py")], check=True)

    subprocess.run(["git", "-C", str(ROOT), "add", "Rules/Loon", "Rules/Clash"], check=True)
    msg = f"Reflow {len(migrate)} rules from Loon local config"
    subprocess.run(["git", "-C", str(ROOT), "commit", "-m", msg], check=True)
    if do_push:
        subprocess.run(["git", "-C", str(ROOT), "push", "origin", "main"], check=True)
        print("已提交并推送。")
    else:
        print("已提交（未推送；加 --push 或手动 git push）。")

    cleanup = migrate + [c for c in cands if c.status == "duplicate"]
    print("\n⚠ 请在 Loon UI 手动删除以下本地规则（本脚本不改 default.lcf）：")
    for c in cleanup:
        print(f"    {c.type},{c.value},{c.policy}")


def main() -> None:
    ap = argparse.ArgumentParser(description="回流 Loon 本地规则到仓库")
    ap.add_argument("--lcf", type=Path, default=DEFAULT_LCF, help="Loon 配置路径")
    ap.add_argument("--apply", action="store_true", help="写入并提交（默认仅打印计划）")
    ap.add_argument("--push", action="store_true", help="--apply 后推送到 origin/main")
    args = ap.parse_args()

    if not args.lcf.exists():
        sys.exit(f"找不到 Loon 配置：{args.lcf}")

    cands = build_plan(parse_candidates(read_rule_section(args.lcf)), load_existing_values())
    print_plan(cands)

    if args.apply:
        apply_plan(cands, args.push)
    else:
        print("\n（dry-run：加 --apply 执行迁移）")


if __name__ == "__main__":
    main()
