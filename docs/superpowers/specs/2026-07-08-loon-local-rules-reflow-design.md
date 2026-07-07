# Loon 本地规则回流机制 · 设计文档

日期：2026-07-08
状态：设计完成，待实现

## 背景与动机

日常在 Loon UI 里直接添加本地规则是最快的应急路径（即时生效、零等待），但这些规则只存在于 iPhone 的 Loon 配置里，不会进入仓库（唯一真相源），造成多端漂移：手机上生效的分流，路由器（OpenClash）上没有；仓库里也查不到。

加规则的"正门"是 iOS 快捷指令（见 `2026-07-06-ios-shortcut-rule-adder-design.md`）；本机制是"应急后门"的收拢手段——允许在 Loon 上临时加规则，事后把它们归拢进仓库，漂移不累积。

## 机制基础（已验证）

Loon 的配置文件通过 iCloud Drive 同步，在 Mac 上的路径：

```
~/Library/Mobile Documents/iCloud~com~ruikq~decar/Documents/Configs/default.lcf
```

- iPhone 上在 Loon UI 添加的本地规则写入该文件的 `[Rule]` 段，iCloud 自动同步到 Mac（已验证：文件存在且随手机端修改更新）。
- 该文件在 git 之外，可能包含设备特定配置（本地代理定义、注释掉的实验规则等）。

## 数据流

```
iPhone Loon UI 加规则
   → default.lcf [Rule] 段（iCloud 同步到 Mac）
   → 回流工具（Mac）：解析 → 映射 → 查重 → 迁移
   → Rules/Loon/*.list → sync_rules.py → Rules/Clash/*.yaml
   → git commit + push → 两端自动分发
   → 提醒用户在 Loon 里删除已迁移的本地规则
```

## 策略名 → 目标文件映射

| Loon 本地规则的策略 | 目标文件 |
|---|---|
| `DIRECT` | `Rules/Loon/Direct.list` |
| `节点选择` | `Rules/Loon/Proxy.list` |
| `美国节点` | `Rules/Loon/US.list` |
| `日本节点` | `Rules/Loon/JP.list` |
| `香港节点` | `Rules/Loon/HK.list` |
| `狮城节点` | `Rules/Loon/SG.list` |
| 其他策略（`REJECT`、未列出的组） | 不自动处理，报告给用户人工决定 |

注：`美国节点` 统一回流到 `US.list`，不猜测是否属于 AI 类（`AISuite.list` 在 Loon 端同样映射美国节点，无法自动区分）；需要归入 AI 组的由用户在报告环节指出。

## 回流流程（半自动）

1. **解析**：读取 `default.lcf` 的 `[Rule]` 段，跳过注释行（`#` 开头）和 `FINAL,FINAL`；只处理 `DOMAIN-SUFFIX` / `DOMAIN` / `DOMAIN-KEYWORD` 三类；`IP-CIDR`、`GEOIP`、`URL-REGEX` 等列入报告但不自动迁移。
2. **查重**：对每条候选规则，检查其规则值是否已存在于仓库任意 `Rules/Loon/*.list` 中；已存在的标记为「仅需本地清理」。
3. **生成迁移计划**：按映射表归类，输出一份 diff 风格的报告（哪条 → 哪个文件；哪些跳过及原因），**先给用户确认再写入**。
4. **写入与同步**：确认后追加到对应 `.list`（格式统一 `TYPE,value` 无空格），运行 `./scripts/sync_rules.py`，一次 commit 提交（示例信息：`Reflow N rules from Loon local config`），push。
5. **清理提示**：列出需要在 Loon UI 里手动删除的本地规则清单。**不回写 `default.lcf`**。

## 安全约束

- 对 `default.lcf` **严格只读**——它在 git 之外、无回滚手段、可能含设备特定内容；清理一律由用户在 Loon UI 完成。
- 保留 `[Rule]` 段中的 `FINAL,FINAL` 与全部注释不动。
- 迁移前必须有用户确认环节（半自动定位），不做无人值守自动提交。

## 触发方式

- **v1（本设计）**：手动触发。两种形态任选：
  - 对话式：让 Claude 按本文档执行一次回流；
  - 脚本：`scripts/reflow_loon_rules.py --dry-run`（打印迁移计划）/ `--apply`（写入+同步+提交）。
- **未来可选**：launchd 定时任务做 `--dry-run` 并在有漂移时通知（ntfy/系统通知），仍由人工确认后 apply；确认流程跑顺后再考虑全自动。

## 验收标准

1. 在 Loon 上手动加一条测试规则（如 `DOMAIN-SUFFIX,reflow-test.invalid,香港节点`），等 iCloud 同步后运行回流：规则出现在 `HK.list`，Actions 生成 `HK.yaml`，报告提示删除本地规则。
2. 重复运行：查重生效，无重复追加。
3. `IP-CIDR` 类本地规则只出现在报告中，文件未被改动。
4. `default.lcf` 内容在整个流程前后逐字节一致。

## 当前漂移快照（2026-07-08，待首次回流处理）

| 本地规则 | 目标 |
|---|---|
| `DOMAIN-SUFFIX,pages.dev,节点选择` | `Proxy.list` |
| `DOMAIN-SUFFIX,hstong.com,香港节点` | `HK.list` |
| `DOMAIN-SUFFIX,push.apple.com,节点选择` | `Proxy.list` |
