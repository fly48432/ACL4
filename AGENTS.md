# ACL4 Maintenance Notes

This repository maintains personal proxy rules for Loon on iOS and Clash/mihomo/OpenClash on router/Mac.

## Rule Source Of Truth

- Maintain custom rules in `Rules/Loon/*.list`.
- Generate matching Clash rules with:

```bash
./scripts/sync_rules.py
```

- Do not hand-edit generated `Rules/Clash/*.yaml` files for synced rule sets unless the change is also applied to the matching Loon source file.

Currently synced rule names are defined in `scripts/sync_rules.py`:

- `Direct`
- `Proxy`
- `ProxyMedia`
- `OpenAI`
- `AISuite`
- `Shopping`
- `US`
- `JP`
- `HK`
- `SG`
- `WiFiCallingUS`
- `WiFiCallingUK`

Clash output format:

```yaml
payload:
  - DOMAIN-SUFFIX,example.com
```

Loon source format:

```text
DOMAIN-SUFFIX,example.com
```

## Custom Rule Placement

Specific custom rules should be placed before general proxy and AI rules.

Preferred order:

1. LAN / Direct
2. Custom rules:
   - `US`
   - `JP`
   - `HK`
   - `SG`
   - Broker
   - `WiFiCallingUS`
   - `WiFiCallingUK`
3. General `Proxy`
4. AI rules:
   - OpenAI / ChatGPT
   - Claude
   - Gemini
   - AISuite
5. Remaining service rules
6. CN / FINAL

Keep this ordering consistent in:

- `MY/Clash.yaml`
- `MY/Subconverter_Loon.ini`
- `MY/Subconverter_Clash.ini`
- local Loon config if edited manually

The `HK`/`SG` rulesets are wired in `MY/Clash.yaml`, `MY/Subconverter_Loon.ini`, AND `MY/Subconverter_Clash.ini` — consistent with the ordering requirement above.

## Current Custom Rule Groups

### US

File: `Rules/Loon/US.list`

Use for domains that should force US nodes, such as US carriers, shopping/account sites, and US-only services.

Current examples:

- `t-mobile.com`
- `att.com`
- `redpocket.com`
- `ebay.com`
- `studentbeans.com`
- `rakuten.com`
- `starlink.com`

Policy:

- Loon: `美国节点`
- Clash: `美国策略`

### JP

File: `Rules/Loon/JP.list`

Use for domains that should force Japan nodes.

Current example:

- `amazon.co.jp`

Policy:

- Loon: `日本节点`
- Clash: `日本自动策略`

### HK

File: `Rules/Loon/HK.list`

Use for domains that should force Hong Kong nodes.

Policy:

- Loon: `香港节点`
- Clash: `香港自动策略`

### SG

File: `Rules/Loon/SG.list`

Use for domains that should force Singapore (狮城) nodes.

Policy:

- Loon: `狮城节点`
- Clash: `狮城自动策略`

### Broker

Uses upstream remote rule:

```text
https://raw.githubusercontent.com/Arthur-vx/broker-rules/main/rule/Shadowrocket/Broker/Broker.list
```

Policy:

- Loon: `美国节点`
- Clash: `美国策略`

Reason: the upstream broker list includes US brokers such as Schwab and IBKR.

For Clash `MY/Clash.yaml`, this provider is `format: text` because the upstream rule is a plain list, not YAML.

### Wi-Fi Calling

US file:

- `Rules/Loon/WiFiCallingUS.list`
- `Rules/Clash/WiFiCallingUS.yaml`

UK file:

- `Rules/Loon/WiFiCallingUK.list`
- `Rules/Clash/WiFiCallingUK.yaml`

Policies:

- US Wi-Fi Calling: `美国节点` / `美国策略`
- UK Wi-Fi Calling: `英国节点` / `英国自动策略`

Do not replace these with broad `DOMAIN-SUFFIX,3gppnetwork.org`. Keep them scoped to specific MCC/MNC ePDG domains.

giffgaff uses the O2 UK network, so it is covered by:

```text
DOMAIN-SUFFIX,epdg.epc.mnc010.mcc234.pub.3gppnetwork.org
```

## AI / ChatGPT Rule Notes

Custom OpenAI/ChatGPT additions belong in:

```text
Rules/Loon/OpenAI.list
```

Then run:

```bash
./scripts/sync_rules.py
```

`login.microsoftonline.com` is intentionally included in OpenAI/ChatGPT rules for this setup.

## Naming Conventions

- Use `AISuite`, not `AISuit`.
- Clash synced rule files use `.yaml`.
- Loon synced rule files use `.list`.
- Avoid adding new one-off local `[Rule]` entries in Loon config when the rule should be reusable. Prefer a remote rule file in this repo.

## Low-rate Node Filtering

Low-rate nodes below 0.5x should be excluded from node groups.

Current pattern:

```regex
0\.[0-4](x|X|倍|倍率)?
```

This filters examples like:

- `0.1`
- `0.2`
- `0.3`
- `0.4`
- `0.1x`
- `0.1倍`
- `0.1倍率`

It should not filter `0.5`.

Keep this filter in:

- `MY/Clash.yaml` region filters
- `MY/Subconverter_Loon.ini` custom proxy groups
- `MY/Subconverter_Clash.ini` custom proxy groups
- manually maintained local Loon configs, if applicable

## Local Loon Config

The user's local Loon config may live outside the repo, for example:

```text
/Users/dorian/Library/Mobile Documents/iCloud~com~ruikq~decar/Documents/Configs/default.lcf
```

When syncing repo decisions into that file:

- Add or update `Remote Filter` entries for regions and low-rate exclusion.
- Add missing policy groups such as `英国节点`.
- Remove stale one-off manual domain rules that have moved into remote rule files.
- Add custom remote rules before Proxy and AI rules.
- Keep `FINAL,FINAL` in `[Rule]`.

Review the file before editing because it is outside git and may contain device-specific local proxy definitions.

## Tooling

Scripts and artifacts that automate the workflows above:

- `scripts/sync_rules.py` — generate `Rules/Clash/*.yaml` from `Rules/Loon/*.list`. Run after editing any synced Loon list. Also runs automatically in CI (see below).
- `.github/workflows/sync-rules.yml` — on push touching `Rules/Loon/**`, regenerates Clash rules, commits as bot, and purges the affected `Rules/Clash/*.yaml` jsDelivr caches. Lets phone-side edits reach the router without a computer.
- `scripts/gen_shortcut.py` + `shortcut/ACL4加规则.shortcut` — the iOS Shortcut that appends rules via the GitHub Contents API. Generator is the source of truth (regenerate + `shortcuts sign --mode anyone`); build/verify method and menu→file mapping in `docs/shortcut-add-rule.md`.
- `scripts/reflow_loon_rules.py` — reflow local `[Rule]` entries from `default.lcf` into repo lists. `--dry-run` (default) prints the migration plan; `--apply` writes+syncs+commits; `--push` optional. Read-only on `default.lcf`; cleanup of migrated local rules is manual in the Loon UI. Design: `docs/superpowers/specs/2026-07-08-loon-local-rules-reflow-design.md`.

Reflow policy→file map (Loon local policy → repo list): `DIRECT`→Direct, `节点选择`→Proxy, `美国节点`→US, `日本节点`→JP, `香港节点`→HK, `狮城节点`→SG. Non-domain rule types and unmapped policies are reported and skipped, not migrated.
