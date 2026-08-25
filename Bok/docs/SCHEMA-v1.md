# Bok Markdown Schema v1

## 正式记忆卡

```yaml
---
id: bok-<uuid>
title: 标题
memory_type: knowledge
importance: ordinary
status: active
created: 2026-08-21T00:00:00Z
updated: 2026-08-21T00:00:00Z
tags:
  - Bok
source_type: conversation
source_ref: turn-123
expires_at: null
---
```

正文至少包含：

```markdown
# 标题

## 一句话结论

压缩后的长期判断。

## 保存依据

- 原因
- 来源
- 置信度

## 后续行动

- 可执行行动
```

允许的 `memory_type`：

- 普通：`knowledge`、`method`、`project_status`、`action`、`reference`。
- 重要：`decision`、`preference`、`identity`、`policy`、`sensitive`、`conflict`。

重要类型不得由 AI 未经确认修改。普通更新不覆盖旧正文，而是追加带时间和来源的 Bok 更新记录。

## 旧 Vault 兼容与 Schema-on-read

Bok 不要求项目、知识卡、长文案、提示词和工程说明套用同一正文模板。读取时把 frontmatter 与旧卡正文段落统一成最小运行时元数据：`type / role / status / source / tags / updated`。类型优先读取显式 `type` 或 `memory_type`，否则按根目录派生；旧卡的“相关标签 / 来源类型 / 更新时间”段落也会被解析。缺少声明时间时才使用文件修改时间，并标记 `updated_source: filesystem`。

`03-Knowledge` 直接维护的一级知识卡必须具有 `role / status / updated / source(或 source_type) / tags`、一句话结论和后续行动，并在 `Memory-Index.md` 登记。`tools/sync-index-status.ps1 -Check` 与 Git pre-commit 会阻止缺字段、漏登记、断链或主题计数漂移进入提交。嵌套工程文档不受这条知识卡门禁约束。

Doctor 只检查各根目录直接维护的核心卡：项目卡看状态/下一步/更新时间，知识卡执行上述严格门禁，内容资产和提示词使用各自规则。嵌套工程文档、基准数据和完整文案不套知识卡模板。

## 随手记

```yaml
---
id: <uuid>
type: quick-note
status: inbox
created: 2026-08-21T00:00:00Z
updated: 2026-08-21T00:00:00Z
source: desktop
promoted_to: null
---
```

状态只使用：

- `inbox`：待整理。
- `promoted`：已沉淀，`promoted_to` 指向正式卡片。
- `archived`：保留但不再处理。

## Personal Claim

Personal Claim 只写入独立 Personal Core 的 `Claims/person-<uuid>.md`，不写入项目 Vault。frontmatter 采用扁平字段，正文保留人可读主张、适用范围、来源和更新记录。

```yaml
---
id: person-<uuid>
type: personal-claim
claim_type: communication_preference
epistemic_status: confirmed
scope_kind: global
scope_value: null
confidence: 1.0
importance: important
sensitivity: private
access_scope:
  - agent:codex
support_count: 2
contradiction_count: 0
source_refs:
  - conversation:chat-123:turn-4
contradiction_refs: []
statement_history:
  - 旧的、已被纠正的表述
first_seen: 2026-08-23T00:00:00Z
last_seen: 2026-08-23T00:00:00Z
valid_from: 2026-08-23T00:00:00Z
valid_to: null
expires_at: null
confirmed_by_user: true
supersedes: null
superseded_by: null
version: 2
created: 2026-08-23T00:00:00Z
updated: 2026-08-23T00:00:00Z
---
```

`claim_type`、状态和证据规则见 [Personal Operating Model v1](PERSON-MODEL-v1.md)。解析时对类型、状态、时间、来源、ID/文件名、计数、范围和 confirmed 一致性执行失败关闭；`importance` 根据 Claim 类型重新推导，不能靠手改 Markdown 降级重要保护。

## Personal Observation、Impact 与 Outcome

三类记录都位于独立 Personal Core，一条一文件：

- `Observations/obs-<hash>.md`：`type: personal-observation`，包含状态、短候选表述、信号/反证、范围、来源、对话/回合 ID、场景和投影到的 Claim ID。敏感信号只保留无正文排除收据。
- `Impacts/impact-<hash>.md`：`type: personal-impact`，包含回答引用、任务摘要/哈希、Agent、项目和实际使用的 Claim ID；不保存回答正文。
- `Outcomes/outcome-<hash>.md`：`type: personal-outcome`，包含 positive / negative / neutral、1～5 可选评分、是否返工、短注释、来源、Agent、项目和 Claim ID。

文件 ID 由稳定输入哈希生成，重复调用返回原记录。解析器校验类型、ID/文件名、时间、范围和列表上限；符号链接或损坏记录不会进入画像与清理判断。

## 运行状态

项目 Vault 的 `.bok/` 不是事实源：删除后会丢失未提交提议、缓存和历史快照，但不会丢失正式 Markdown。Personal Core 的 `.bok/versions/`、`.bok/backups/` 和清理决策同样不是 Claim 事实源，但删除会失去本机恢复历史、备份或待处理决策，因此不能把“可派生缓存”和“不可重建恢复状态”混为一谈。Embedding 缓存按 Provider、模型和文本哈希寻址，永远可以重建。

对话正文只进入 `.bok/state/conversations/` 的短期 Session Buffer；捕获队列使用 `.bok/state/captures/<capture-id>.json` 分片记录。它们都不是长期事实源。逐轮事件、个人主张状态、来源隔离和保留期契约见 [Personal Operating Model v1](PERSON-MODEL-v1.md)。
