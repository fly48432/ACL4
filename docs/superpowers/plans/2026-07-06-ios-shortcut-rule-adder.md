# iOS 快捷指令加规则 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现纯手机操作的加规则通道：iOS 快捷指令 → GitHub API 写入仓库规则文件 → GitHub Actions 自动生成 Clash 格式 → Loon 与 OpenClash 自动分发。

**Architecture:** 仓库保持「`Rules/Loon/*.list` 为源、`scripts/sync_rules.py` 生成 `Rules/Clash/*.yaml`」的现有模式。新增 HK/SG 规则组并在两端配置接线；新增 GitHub Actions 在 push 时自动跑生成脚本；快捷指令通过 GitHub Contents API 直接提交 main，提交后 purge jsDelivr 缓存。

**Tech Stack:** Python 3（仅标准库）、GitHub Actions、GitHub REST API（Contents）、iOS 快捷指令、jsDelivr purge API。

**Spec:** `docs/superpowers/specs/2026-07-06-ios-shortcut-rule-adder-design.md`

## Global Constraints

- 新增规则行格式统一为无空格的 `TYPE,value`（如 `DOMAIN-SUFFIX,example.com`）。
- 规则插入顺序遵循 AGENTS.md 既定次序：LAN/Direct → 自定义地区规则 → 通用 Proxy → AI → 其余服务 → CN/FINAL。
- 策略名对照：香港 = Loon `香港节点` / Clash `香港自动策略`；新加坡 = Loon `狮城节点` / Clash `狮城自动策略`。
- `Rules/Clash/*.yaml` 是生成产物，一律不手改，只通过 `./scripts/sync_rules.py` 生成。
- 本仓库为个人单人仓库，提交直接进 `main`，无需分支/PR。
- 仓库内指向自身的 URL 沿用现有 jsDelivr 模式：`https://cdn.jsdelivr.net/gh/fly48432/ACL4@main/...`。

---

### Task 1: 新建 HK / SG 规则组并纳入生成脚本

**Files:**
- Create: `Rules/Loon/HK.list`
- Create: `Rules/Loon/SG.list`
- Modify: `scripts/sync_rules.py:7-18`（`RULE_NAMES` 元组）
- Modify: `AGENTS.md`（"Currently synced rule names" 列表，约第 16-27 行）
- 生成: `Rules/Clash/HK.yaml`、`Rules/Clash/SG.yaml`（由脚本产出，不手写）

**Interfaces:**
- Produces: `Rules/Loon/HK.list`、`Rules/Loon/SG.list` 及对应生成的 `Rules/Clash/HK.yaml`、`Rules/Clash/SG.yaml`——Task 2 的配置接线和 Task 4 的快捷指令菜单都引用这四个文件路径。

- [ ] **Step 1: 创建两个种子规则文件**

写入 `Rules/Loon/HK.list`（内容如下，含一条占位规则——mihomo 对空 payload 的 rule-provider 可能报错，`.invalid` 顶级域永不解析，无副作用）：

```text
# 走香港节点的规则（快捷指令追加）
DOMAIN-SUFFIX,placeholder-hk.invalid
```

写入 `Rules/Loon/SG.list`：

```text
# 走新加坡（狮城）节点的规则（快捷指令追加）
DOMAIN-SUFFIX,placeholder-sg.invalid
```

- [ ] **Step 2: 把 HK、SG 加进 RULE_NAMES**

`scripts/sync_rules.py` 中：

```python
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
```

- [ ] **Step 3: 运行生成脚本并验证**

```bash
cd /Users/dorian/work/github/ACL4 && ./scripts/sync_rules.py
```

预期输出包含：

```text
Rules/Loon/HK.list -> Rules/Clash/HK.yaml
Rules/Loon/SG.list -> Rules/Clash/SG.yaml
```

再确认生成内容：

```bash
cat Rules/Clash/HK.yaml
```

预期：

```yaml
payload:
  # 走香港节点的规则（快捷指令追加）
  - DOMAIN-SUFFIX,placeholder-hk.invalid
```

- [ ] **Step 4: 更新 AGENTS.md 的同步规则清单**

在 "Currently synced rule names" 列表中 `JP` 之后加两行：

```markdown
- `HK`
- `SG`
```

- [ ] **Step 5: Commit**

```bash
git add Rules/Loon/HK.list Rules/Loon/SG.list Rules/Clash/HK.yaml Rules/Clash/SG.yaml scripts/sync_rules.py AGENTS.md
git commit -m "Add HK and SG rule groups"
```

---

### Task 2: 两端配置接线（Clash + Loon）

**Files:**
- Modify: `MY/Clash.yaml:184-188`（rule-providers 区，DorianJP 之后）
- Modify: `MY/Clash.yaml:381`（rules 区，`RULE-SET, DorianJP` 之后）
- Modify: `MY/Subconverter_Loon.ini:30`（`ruleset=日本节点` 行之后）

**Interfaces:**
- Consumes: Task 1 生成的 `Rules/Clash/HK.yaml`、`SG.yaml` 和 `Rules/Loon/HK.list`、`SG.list` 的 jsDelivr URL。
- Produces: Clash 端策略组名 `香港自动策略`、`狮城自动策略` 与 Loon 端 `香港节点`、`狮城节点` 的规则映射（两组策略在两端配置中已存在，无需新建）。

- [ ] **Step 1: Clash.yaml 增加两个 rule-provider**

在 `DorianJP` 块（约 184-187 行）之后、`Broker` 块之前插入：

```yaml
  DorianHK:
    <<: *RuleProviders
    path: './rules/HK.yaml'
    url: 'https://cdn.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Clash/HK.yaml'

  DorianSG:
    <<: *RuleProviders
    path: './rules/SG.yaml'
    url: 'https://cdn.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Clash/SG.yaml'
```

- [ ] **Step 2: Clash.yaml 增加两条 RULE-SET**

在 `- RULE-SET, DorianJP, 日本自动策略`（约 381 行）之后插入：

```yaml
  - RULE-SET, DorianHK, 香港自动策略
  - RULE-SET, DorianSG, 狮城自动策略
```

- [ ] **Step 3: Subconverter_Loon.ini 增加两条 ruleset**

在 `ruleset=日本节点,...JP.list`（第 30 行）之后插入：

```ini
ruleset=香港节点,https://cdn.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Loon/HK.list
ruleset=狮城节点,https://cdn.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Loon/SG.list
```

- [ ] **Step 4: 验证 YAML 语法与策略组存在**

```bash
python3 -c "import yaml; yaml.safe_load(open('MY/Clash.yaml')); print('YAML OK')"
```

预期：`YAML OK`（若报 `ModuleNotFoundError: yaml`，先执行 `pip3 install --user pyyaml` 再跑）。

```bash
grep -c "name: 香港自动策略\|name: 狮城自动策略" MY/Clash.yaml
```

预期：`2`（两个策略组都已存在于 proxy-groups）。

```bash
grep -n "香港节点\`\|狮城节点\`" MY/Subconverter_Loon.ini | head -2
```

预期：能看到 `custom_proxy_group=香港节点` 和 `custom_proxy_group=狮城节点` 的定义行（说明 ini 端策略组存在）。

- [ ] **Step 5: Commit**

```bash
git add MY/Clash.yaml MY/Subconverter_Loon.ini
git commit -m "Wire HK/SG rule groups into Clash and Loon configs"
```

---

### Task 3: GitHub Actions 自动同步 workflow

**Files:**
- Create: `.github/workflows/sync-rules.yml`

**Interfaces:**
- Consumes: `scripts/sync_rules.py`（Task 1 已更新 RULE_NAMES）。
- Produces: push 改动 `Rules/Loon/**` 后，`Rules/Clash/*.yaml` 由 bot 自动生成提交——Task 4 的快捷指令依赖此机制让 Clash 端拿到新规则。

- [ ] **Step 1: 写 workflow 文件**

`.github/workflows/sync-rules.yml`：

```yaml
name: Sync Loon rules to Clash

on:
  push:
    branches: [main]
    paths:
      - 'Rules/Loon/**'

permissions:
  contents: write

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate Clash rules
        run: python3 scripts/sync_rules.py

      - name: Commit and push if changed
        run: |
          if git diff --quiet -- Rules/Clash; then
            echo "No changes to commit"
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add Rules/Clash
          git commit -m "chore: sync Clash rules from Loon lists"
          git pull --rebase origin main
          git push origin main
```

防循环说明：bot 提交只改 `Rules/Clash/**`，触发条件只看 `Rules/Loon/**`，不会再次触发；`git pull --rebase` 处理快捷指令连续提交时的并发 push。

- [ ] **Step 2: 验证 YAML 语法**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/sync-rules.yml')); print('YAML OK')"
```

预期：`YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/sync-rules.yml
git commit -m "Add workflow to auto-sync Clash rules"
```

---

### Task 4: 快捷指令搭建指南 + PAT 设置文档

**Files:**
- Create: `docs/shortcut-add-rule.md`

**Interfaces:**
- Consumes: Task 1 的七个目标文件名（Direct/Proxy/US/JP/HK/SG/AISuite `.list`）；Task 3 的自动同步机制（指南中说明生效路径）。
- Produces: 用户照做即可完成 PAT 创建与快捷指令搭建的完整操作手册。

- [ ] **Step 1: 写指南文档**

`docs/shortcut-add-rule.md` 完整内容如下（原样写入）：

````markdown
# 快捷指令「添加代理规则」搭建指南

在 iPhone 上通过快捷指令把域名规则直接提交到本仓库，无需电脑。
提交后：Loon 手动刷新对应远程规则即时生效；OpenClash 最迟 1 小时自动生效。

## 第一步：创建 GitHub Fine-grained PAT（一次性）

1. 打开 <https://github.com/settings/personal-access-tokens/new>
2. Token name：`ACL4-Shortcut`；Expiration：选 1 年（到期后重新生成并替换到快捷指令里）
3. Repository access：选 **Only select repositories** → 只勾 `fly48432/ACL4`
4. Permissions → Repository permissions → **Contents：Read and write**，其余保持 No access
5. Generate token，复制以 `github_pat_` 开头的字符串（只显示一次）

> 安全提示：此 token 只能读写 ACL4 仓库内容。不要把含 token 的快捷指令分享给任何人；怀疑泄露时到同一页面 Revoke。

## 第二步：搭建快捷指令

打开「快捷指令」App → 新建快捷指令，命名「添加代理规则」。
在快捷指令设置（右上角 ⓘ）中开启 **在共享表单中显示**，接收类型勾选 **URL** 和 **文本**。

按顺序添加以下动作（`【】` 内是动作名，缩进表示嵌套在分支里）：

### 1. 输入获取与域名提取

1. 【如果】快捷指令输入 没有任何值
   - 【要求输入】文本，提示语「输入域名 / 关键词或粘贴网址」（可长按输入框粘贴剪贴板）
   - 【设定变量】`原始输入` = 要求输入的结果
2. 【否则】
   - 【设定变量】`原始输入` = 快捷指令输入（以文本形式）
3. 【结束如果】
4. 【匹配文本】对 `原始输入`，正则：
   `^(?:[a-zA-Z][a-zA-Z0-9+.\-]*://)?(?:[^/@\s]+@)?([^/:?#\s]+)`
5. 【获取匹配文本的组】组 1 → 【设定变量】`域名`
   （这个正则对裸域名、完整 URL、带端口/路径的地址都能取出主机名）

### 2. 选择规则类型

6. 【从菜单中选取】提示「规则类型」，选项：`DOMAIN-SUFFIX`、`DOMAIN`、`DOMAIN-KEYWORD`
   - 分支 DOMAIN-SUFFIX：
     - 【匹配文本】对 `域名`，正则 `[^.]+\.[^.]+$` → 【设定变量】`候选2`（主域名，如 example.com）
     - 【匹配文本】对 `域名`，正则 `[^.]+\.[^.]+\.[^.]+$` → 【设定变量】`候选3`（三级形式，可能为空）
     - 【从列表中选取】列表项：`候选2`、`候选3`、`域名` → 【设定变量】`规则值`
     - 【设定变量】`规则类型` = `DOMAIN-SUFFIX`
   - 分支 DOMAIN：
     - 【设定变量】`规则值` = `域名`；【设定变量】`规则类型` = `DOMAIN`
   - 分支 DOMAIN-KEYWORD：
     - 【要求输入】文本，提示「输入关键词」，默认值 = `域名`
     - 【设定变量】`规则值` = 输入结果；【设定变量】`规则类型` = `DOMAIN-KEYWORD`
7. 【结束菜单】

### 3. 选择分类（两级菜单）

8. 【从菜单中选取】提示「分流到」，选项：`直连`、`代理`
   - 分支 直连：【设定变量】`目标文件` = `Direct.list`
   - 分支 代理：
     - 【从菜单中选取】提示「代理策略」，选项：`默认代理`、`美国`、`日本`、`香港`、`新加坡`、`AI`
       - 默认代理 → 【设定变量】`目标文件` = `Proxy.list`
       - 美国 → `US.list`；日本 → `JP.list`；香港 → `HK.list`；新加坡 → `SG.list`；AI → `AISuite.list`
     - 【结束菜单】
9. 【结束菜单】
10. 【文本】内容 `规则类型,规则值`（两个变量之间一个英文逗号，无空格）→ 【设定变量】`规则行`

### 4. 读取现有文件（GET）

11. 【文本】内容 `github_pat_xxxx…`（粘贴第一步的 token）→ 【设定变量】`Token`
12. 【文本】内容 `https://api.github.com/repos/fly48432/ACL4/contents/Rules/Loon/目标文件?ref=main`（`目标文件` 用变量插入）→ 【设定变量】`API地址`
13. 【获取 URL 内容】URL = `API地址`，方法 GET，头部：
    - `Authorization`: `Bearer Token`（Token 用变量插入）
    - `Accept`: `application/vnd.github+json`
14. 【获取词典值】键 `sha` → 【设定变量】`文件SHA`
15. 【获取词典值】键 `content` → 【Base64 编码】选「解码」→ 【设定变量】`旧内容`

### 5. 查重与追加

16. 【如果】`旧内容` 包含 `规则值`
    - 【显示通知】「规则已存在：规则值」
    - 【停止此快捷指令】
17. 【结束如果】
18. 【文本】内容为（第一行插入变量 `旧内容`，第二行插入变量 `规则行`）：

    ```
    旧内容
    规则行
    ```

19. 【Base64 编码】上一步文本，选「编码」→ 【设定变量】`新内容B64`

### 6. 提交（PUT）+ 清缓存

20. 【词典】：
    - `message`（文本）= `Add 规则行 to 目标文件 (Shortcut)`
    - `content`（文本）= `新内容B64`
    - `sha`（文本）= `文件SHA`
    - `branch`（文本）= `main`
21. 【获取 URL 内容】URL = `API地址`（去掉 `?ref=main` 也可，PUT 不需要），方法 PUT，头部同第 13 步，请求体 = 上一步词典（JSON）
22. 【获取词典值】对 PUT 响应取键 `commit.sha` → 【如果】没有任何值
    - 【显示提醒】「提交失败，请重试」，正文放 PUT 响应
    - 【停止此快捷指令】
23. 【结束如果】
24. 【获取 URL 内容】GET `https://purge.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Loon/目标文件`（清 jsDelivr 缓存）
25. 【显示通知】「已添加 规则行 → 目标文件」

> 提交偶发 409 冲突（比如 Actions 恰好同时在提交）时，重新运行一次快捷指令即可——第 13 步会重新拿到最新 sha。

## 使用方式

- **分享入口**：Safari / App 里点分享 → 「添加代理规则」→ 选类型 → 选分类 → 完成
- **直接运行**：从 Loon 日志等处看到域名后，复制 → 运行快捷指令 → 粘贴 → 选类型 → 选分类

## 生效路径

| 端 | 生效方式 | 时延 |
|---|---|---|
| Loon | 配置 → 远程规则 → 下拉刷新 | 即时（已 purge CDN） |
| OpenClash | rule-provider 自动拉取 | ≤ 1 小时 |

Clash 格式规则由 GitHub Actions 在提交后约 1 分钟内自动生成，无需人工干预。

## 验证清单（搭完后逐项过）

1. 分享一个网页 → 加到「香港」→ GitHub 上 `Rules/Loon/HK.list` 出现新行，约 1 分钟后 bot 提交更新 `Rules/Clash/HK.yaml`
2. 复制一个裸域名直接运行 → 加到「直连」→ `Direct.list` 出现新行
3. 重复添加同一域名 → 弹「规则已存在」且文件无重复行
4. Loon 刷新远程规则 → 测试域名按所选策略分流
5. 测试完把测试域名从对应 `.list` 里删掉（GitHub App 或电脑均可）
````

- [ ] **Step 2: 自查文档**

通读一遍，确认：菜单七个分类与 Task 1/2 的文件名一致；API 路径中的仓库名、分支名正确；无占位符。

- [ ] **Step 3: Commit**

```bash
git add docs/shortcut-add-rule.md
git commit -m "Add iOS Shortcut build guide"
```

---

### Task 5: 端到端验证

**Files:** 无新增文件（推送 + 验证 + 清理测试数据）

**Interfaces:**
- Consumes: Task 1-4 的全部产物；本机已认证的 `gh` CLI（模拟快捷指令的 API 调用）。

- [ ] **Step 1: 推送全部提交**

```bash
git push origin main
```

- [ ] **Step 2: 用 gh api 模拟快捷指令写入（验证 Contents API 流程）**

```bash
cd /Users/dorian/work/github/ACL4
SHA=$(gh api repos/fly48432/ACL4/contents/Rules/Loon/SG.list?ref=main --jq .sha)
OLD=$(gh api repos/fly48432/ACL4/contents/Rules/Loon/SG.list?ref=main --jq .content | base64 -d)
NEW=$(printf '%s\nDOMAIN-SUFFIX,e2e-test.invalid\n' "$OLD" | base64)
gh api -X PUT repos/fly48432/ACL4/contents/Rules/Loon/SG.list \
  -f message="Add DOMAIN-SUFFIX,e2e-test.invalid to SG.list (e2e test)" \
  -f content="$NEW" -f sha="$SHA" -f branch=main --jq .commit.sha
```

预期：输出一个 commit sha（40 位十六进制）。

- [ ] **Step 3: 验证 Actions 自动同步**

```bash
sleep 60 && gh run list --workflow=sync-rules.yml --limit 3
```

预期：最近一条 run 状态为 `completed` / `success`。

```bash
git pull --rebase origin main && grep e2e-test Rules/Clash/SG.yaml
```

预期：`  - DOMAIN-SUFFIX,e2e-test.invalid`（bot 已生成 Clash 规则）。

- [ ] **Step 4: 清理测试规则**

从 `Rules/Loon/SG.list` 删除 `DOMAIN-SUFFIX,e2e-test.invalid` 行，运行 `./scripts/sync_rules.py`，然后：

```bash
git add Rules/Loon/SG.list Rules/Clash/SG.yaml
git commit -m "Remove e2e test rule"
git push origin main
```

预期：Actions 再跑一次且无新 bot 提交（Clash 文件已本地同步，`No changes to commit`）。

- [ ] **Step 5: 用户验收（手机端，照指南操作）**

按 `docs/shortcut-add-rule.md` 创建 PAT、搭建快捷指令，走一遍文档末尾的验证清单。此步由用户完成，完成前不算交付。

---

## Self-Review 记录

- **Spec 覆盖**：快捷指令（Task 4 指南）、HK/SG 接线（Task 1/2）、Actions 同步（Task 3）、PAT（Task 4 第一步）、purge（指南第 24 步）、查重（指南第 16 步）、验证（Task 5 + 指南清单）——全覆盖。
- **Spec 偏差**：sha 冲突「自动重试一次」简化为「提示后重跑快捷指令」——快捷指令里复制整段 GET+PUT 动作代价高于收益，冲突概率极低且重跑等效。
- **一致性**：七个目标文件名、策略组名、jsDelivr URL 模式在各 Task 间一致；`DorianHK`/`DorianSG` 命名沿用 `DorianUS`/`DorianJP` 惯例。
