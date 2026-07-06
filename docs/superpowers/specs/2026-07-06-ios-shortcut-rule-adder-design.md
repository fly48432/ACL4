# iOS 快捷指令加规则 · 设计文档

日期：2026-07-06
状态：待评审

## 背景

本仓库是 Loon（iPhone）与 OpenClash（路由器）两端代理规则的唯一真相源，两端配置均通过远程 URL 引用仓库内的规则文件。当前痛点：遇到需要调整分流的域名时，必须回电脑改 `Rules/Loon/*.list`、跑 `scripts/sync_rules.py`、提交推送；在 Loon UI 或 OpenClash Web 界面上临时加的本地规则不会回流仓库，造成多端漂移。

本设计实现一条**纯手机操作**的加规则通道：iOS 快捷指令 → GitHub API → 仓库规则文件 → 两端自动分发。

## 范围

本次交付（v1）：

1. iOS 快捷指令「添加代理规则」
2. 新建 HK / SG 规则组并在两端配置接线（快捷指令菜单需要）
3. GitHub Actions 自动运行 `sync_rules.py`（快捷指令的硬依赖：否则手机提交 Loon 规则后，Clash 端规则不会生成）

明确不在本次范围（已有共识，后续阶段再做）：

- 兜底策略切换为白名单模式（FINAL 默认走代理）
- 规则源 URL 标准化（jsDelivr → raw + 经代理拉取）
- Loon 本地规则回流机制
- AGENTS.md 维护哲学改写、第三方订阅标准流程文档

## 一、iOS 快捷指令设计

### 输入获取

- **分享表单入口**：接受 URL 或纯文本。URL 提取 host；文本去首尾空白后直接使用。
- **直接运行入口**：弹出文本输入框，默认填入剪贴板内容（适配「从 Loon 日志里看到域名」的场景）。

### 规则类型选择

菜单三选一：

1. `DOMAIN-SUFFIX`（默认）
2. `DOMAIN`
3. `DOMAIN-KEYWORD`

选择 `DOMAIN-SUFFIX` 且输入为多级域名时，生成后缀候选供选择。例如输入 `a.b.example.com`，候选：`example.com` / `b.example.com` / `a.b.example.com`。

### 分类选择（两级菜单）

| 菜单项 | 目标文件 | Loon 策略 | Clash 策略 |
|---|---|---|---|
| 直连 | `Rules/Loon/Direct.list` | DIRECT | DIRECT |
| 代理 → 默认代理 | `Rules/Loon/Proxy.list` | 节点选择 | 节点选择 |
| 代理 → 美国 | `Rules/Loon/US.list` | 美国节点 | 美国策略 |
| 代理 → 日本 | `Rules/Loon/JP.list` | 日本节点 | 日本自动策略 |
| 代理 → 香港 | `Rules/Loon/HK.list`（新建） | 香港节点 | 香港自动策略 |
| 代理 → 新加坡 | `Rules/Loon/SG.list`（新建） | 狮城节点 | 狮城自动策略 |
| 代理 → AI | `Rules/Loon/AISuite.list` | 美国节点（现状映射） | AI |

### 写入逻辑（GitHub REST API）

1. `GET /repos/fly48432/ACL4/contents/Rules/Loon/{file}?ref=main`，base64 解码。
2. **查重**：若文件中已存在相同规则值，通知「已存在」并终止。
3. 追加一行，格式统一为无空格的 `TYPE,value`（如 `DOMAIN-SUFFIX,example.com`）。
4. `PUT` 同一路径，带原 `sha`，提交信息形如 `Add DOMAIN-SUFFIX,example.com to US.list (Shortcut)`，直接提交到 `main`。
5. 提交成功后调用 `https://purge.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Loon/{file}` 清除 CDN 缓存（两端拉取的都是 jsDelivr URL，不清缓存最长要等约 12 小时才能拉到新内容）。
6. 成功/失败均弹通知；`PUT` 因 sha 冲突失败时自动重试一次（重新 GET 后再 PUT）。

### 凭证

使用 GitHub fine-grained PAT，权限最小化：仅 `fly48432/ACL4` 仓库、仅 Contents 读写。Token 以文本形式存放在快捷指令内部（快捷指令不共享则不外泄）。

### 输入校验

- 空输入、含空格或非法字符（非域名/关键词字符集）→ 提示并终止。
- URL 提取失败时回退为手动输入框。

## 二、HK / SG 规则组接线

1. 新建空文件 `Rules/Loon/HK.list`、`Rules/Loon/SG.list`。
2. `scripts/sync_rules.py` 的 `RULE_NAMES` 增加 `"HK"`、`"SG"`，生成 `Rules/Clash/HK.yaml`、`SG.yaml`。
3. `MY/Clash.yaml`：新增 `DorianHK`、`DorianSG` 两个 rule-provider（复用 `&RuleProviders` 锚点），`rules:` 中紧邻 `DorianUS` / `DorianJP` 插入：
   - `RULE-SET, DorianHK, 香港自动策略`
   - `RULE-SET, DorianSG, 狮城自动策略`
4. `MY/Subconverter_Loon.ini`：在自定义规则区（现有 US/JP 行附近、Proxy 与 AI 规则之前）插入，URL 沿用该文件现有的 jsDelivr 模式：
   - `ruleset=香港节点,https://cdn.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Loon/HK.list`
   - `ruleset=狮城节点,https://cdn.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Loon/SG.list`
5. 插入顺序遵循 AGENTS.md 既定次序：LAN/Direct → 自定义地区规则 → 通用 Proxy → AI → 其余服务 → CN/FINAL。

## 三、GitHub Actions 自动同步

新增 `.github/workflows/sync-rules.yml`：

- 触发：push 到 `main` 且改动路径含 `Rules/Loon/**`。
- 步骤：checkout → 运行 `./scripts/sync_rules.py` → 若 `Rules/Clash/*.yaml` 有变化则以 bot 身份提交回 `main`。
- 防循环：生成的提交只改 `Rules/Clash/**`，与触发路径 `Rules/Loon/**` 不相交，不会再次触发。

## 生效路径与时延

- **Loon**：快捷指令提交并 purge Loon 规则文件缓存后，在 Loon 里手动刷新对应远程规则即时生效；否则按 Loon 的远程规则刷新周期生效。
- **OpenClash**：拉取的是生成的 `Rules/Clash/*.yaml`，由 GitHub Actions 在 bot 提交后 purge 其 jsDelivr 缓存；rule-provider 每 3600 秒自动拉取，最迟一小时内生效。
- 两端引用的都是 `cdn.jsdelivr.net`；Loon 文件由快捷指令 purge、Clash 文件由 workflow purge，均为缓解手段，根治（换 raw + 经代理拉取）由后续「URL 标准化」阶段处理。

## 验证方式

1. 用测试域名对每个分类各走一遍快捷指令，确认写入正确文件、格式正确、无重复追加。
2. 确认 push 后 Actions 自动生成对应 `Rules/Clash/*.yaml` 且不产生循环触发。
3. 重复添加同一域名，确认查重生效。
4. Loon 刷新远程规则后，测试域名按所选策略分流；OpenClash 等待自动刷新后同样验证。

## 风险与取舍

- PAT 泄露风险：权限已收敛到单仓库 Contents；若泄露仅影响本仓库内容，可随时吊销。
- 快捷指令直接提交 `main`：无评审环节，但仓库本身就是个人单人维护，出错可用 git 回滚。
- 查重仅做精确匹配：不识别「已被更宽后缀覆盖」的情况（如已有 `example.com` 再加 `a.example.com`），可接受，后续回流机制可清理冗余。
