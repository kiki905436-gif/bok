# Bok Personal Operating Model v1

## 当前状态

- 2026-08-24：v1.1 将“保存用户说过什么”收紧为“保存有依据的抽象理解”，并加入可事务恢复的彻底忘记。
- 已实现 Phase 1：Conversation Ledger、逐轮幂等收据、崩溃补投、分片捕获队列、短期正文保留和入口隔离。
- 已实现 Phase 2：独立 Personal Core、显式 Personal Claim、确认/纠正/拒绝/替代/解释/回滚和带引用的最小上下文。
- 已实现 Phase 3/4：Observation/Hypothesis 保守投影、Impact/Outcome、清理治理和“关于我”可视化。
- 已实现本机 Agent 哈希凭证、范围与撤销，并已注册 Codex MCP；Boujoy Harness/WorkBuddy 的客户端启用、真实 Windows、磁盘满和长期运行仍待验收。10K 临时 Claim 的写入、去重和列表基线已完成，长期运行样本仍未完成。

实现边界必须如实显示。v0.4 只能证明“对话能可靠落账、保守形成候选、由用户确认并按范围召回”，不能声称 Bok 已经完全理解用户；长期真实使用仍是必要证据。

## 产品定义

Bok 维护的是可验证、可纠正、会过期、按场景生效的个人运行模型，而不是扁平用户画像。

产品承诺：**理解你，但不定义你；记住过去，继续工作。**

任何关于用户的理解都必须回答：

1. 用户明确说过，还是系统推断？
2. 依据来自哪里？
3. 在什么场景生效？
4. 什么时候开始、何时可能失效？
5. 哪些相反证据存在？
6. 哪次回答使用过它？
7. 用户如何纠正、降级、撤销或遗忘？

## 模型分层

| 层 | 内容 | 默认生命周期 | 写入策略 |
|---|---|---:|---|
| Personal Core | 身份、长期目标、价值边界、稳定偏好、公开身份 | 长期 | 身份/目标/边界受保护；低风险偏好可按证据形成 learned |
| Work Model | 工作方式、验收习惯、沟通偏好、授权边界 | 长期但带场景 | 低风险模式达标后 learned；授权边界必须确认 |
| Project History | 项目状态、决策、原因、结果、踩坑、下一步 | 跟随项目 | 普通状态可自动，重要决策确认 |
| Knowledge & Capability | 掌握、实践、学习中、待验证的知识与能力 | 可更新 | 证据分级，不因单次提及升级能力 |
| Current State | 当前任务、阻塞、资源限制、临时优先级 | 短期 | 自动过期 |
| Relationship Contract | Agent 可以做什么、何时必须确认、完成标准 | 长期 | 必须确认 |

## 存储边界

### Session Buffer

- 位于 `.bok/state/conversations/`，属于可清理的本机运行状态。
- 正文默认保留 14 天，可配置 1～90 天。
- `session_only` 不进入长期分析。
- `do_not_remember` 不保存正文，只保留不可还原的幂等收据元数据。
- 到期清理正文后仍可保留不含正文的处理收据，用于证明是否收到、是否处理。

### Project Vault

- 保存可共享的项目事实、决策、状态和成果。
- Markdown 是唯一事实源。
- 项目 Agent 只应获得当前项目相关内容。

### Personal Core Vault

- 已支持配置公开/共享项目 Vault 之外的独立绝对路径；未配置时保持禁用，不退回共享 Vault。
- 不能只依赖 API 权限，同时又把私人 Markdown 直接挂载给同一个 Agent 工作区；那会绕过权限层。
- Personal Core 默认不进入 Git、不进入公开包、不保存密码和密钥。
- 跨 Agent 只返回任务需要的最小主张包，不能返回完整个人库。
- 文件系统根、Home、项目 Vault 内部或外包围路径、Git 仓库、符号链接目录和非空未标记目录全部拒绝。

首版不在当前项目 Vault 自动创建 `08-Person`。正式主张、观察、结果与影响分别位于 `<Personal Core>/Claims/`、`Observations/`、`Outcomes/` 和 `Impacts/`；恢复历史和独立备份位于 `<Personal Core>/.bok/versions/` 与 `.bok/backups/`。完整路径见 [Personal Core 实现路径](PERSONAL-CORE-IMPLEMENTATION.md)。

## Conversation Event v1

每个事件使用 `(conversation_id, turn_id)` 形成稳定 ID。相同 ID 与相同内容是幂等重放；相同 ID 但正文或策略不同必须返回冲突。

```json
{
  "conversation_id": "chat-123",
  "turn_id": "turn-456",
  "role": "user",
  "content": "本轮正文",
  "memory_mode": "default",
  "external_content": false,
  "client": "boujoy-harness",
  "agent": "coding-agent",
  "project": "02-Projects/example.md",
  "cloud_consent": false
}
```

`memory_mode`：

- `default`：用户正文进入后台记忆判断。
- `session_only`：只在短期会话缓冲中保留，不进入长期分析。
- `do_not_remember`：不保存正文，不进入分析。

入口隔离：

- 只有 `role=user`、`memory_mode=default`、`external_content=false` 的正文能够进入记忆队列。
- `assistant/tool/system` 事件只做运行收据；结果学习走独立 Outcome API，不从 Agent 自己的回答反推用户。
- 引用网页、附件、外部文档和转发对话必须标记 `external_content=true`，不能直接形成用户身份或偏好。

状态：

- `received`：已原子落账，尚未加入下游队列。
- `queued_for_analysis`：已进入分片捕获队列。
- `received_unqueued`：下游暂不可写，可由 reconcile 补投。
- `excluded_external_content`：外部材料，不参与个人理解。
- `session_only`：短期保留。
- `excluded_do_not_remember`：没有保存正文。
- `recorded_non_user`：非用户事件。
- `expired_unprocessed`：正文到期清理时仍未进入正式处理。

公开状态接口不得返回正文、云端授权标记或请求指纹。

## Personal Claim v1

长期个人理解不按“每轮一张卡”保存，而按可验证主张合并。

```yaml
claim_id: person-<uuid>
statement: 在维护已有产品时，优先最小范围、低侵入改动。
claim_type: work_preference
epistemic_status: hypothesis
scope:
  kind: task_type
  value: existing_product_maintenance
confidence: 0.72
importance: important
sensitivity: private
access_scope:
  - personal-core
support_count: 3
contradiction_count: 0
source_refs:
  - conversation:chat-123:turn-4
statement_history: []
first_seen: 2026-08-20T00:00:00Z
last_seen: 2026-08-23T00:00:00Z
valid_from: 2026-08-20T00:00:00Z
valid_to: null
expires_at: null
confirmed_by_user: false
supersedes: null
superseded_by: null
positive_outcomes: []
negative_outcomes: []
last_used: null
last_influenced_answer: null
version: 1
```

当前实际 Markdown 使用扁平 frontmatter 表示 `scope_kind / scope_value`，以兼容 Bok 的轻量解析器；语义与上面嵌套示意相同。`statement_history` 保存被用户纠正过的旧表述，用于阻止历史错误被静默重建。

允许的 `epistemic_status`：

- `explicit`：用户明确表达，但尚未确认长期化。
- `observed`：只发生过一次的行为证据。
- `hypothesis`：多次证据形成的系统假设。
- `learned`：低风险且证据达到门槛的可更新理解；可以服务受信本机回答，但不冒充用户确认。
- `confirmed`：用户确认。
- `contradicted`：存在实质相反证据。
- `superseded`：已被新主张替代。
- `expired`：过去有效，现在默认不参与上下文。
- `rejected`：用户否认，禁止再次静默形成相同主张。

建议的 `claim_type`：

- `identity`
- `long_term_goal`
- `communication_preference`
- `work_preference`
- `decision_pattern`
- `authority_rule`
- `public_identity`
- `capability_claim`
- `project_experience`
- `knowledge_claim`
- `negative_preference`
- `temporary_state`
- `behavior_hypothesis`

`identity`、`authority_rule`、`public_identity`、稳定偏好、敏感内容和跨项目行为判断不得自动进入 `confirmed`。

## 证据与推断规则

1. Conversation Ledger 只负责可靠收据；没有模型/Agent 给出的结构化理解时，不靠关键词猜测个人语义，也不生成长期观察。
2. 每条非敏感 Observation 必须包含第三人称 `candidate_statement`、不含原话的 `inference_basis` 和稳定 `concept_key`；近似照抄用户原句直接拒绝且不落盘。
3. 一次行为只生成 observation，不形成长期偏好；“这次、现在、先别、明天、当前项目”等临时指令不能冒充全局规则。
4. 两次相似行为最多继续积累；默认至少三个独立会话，并跨两个时间点或上下文，低风险类型达到置信阈值后才进入 `learned`。决策/行为模式采用至少四次证据和更高置信门槛；未达标只继续积累。
5. `concept_key` 只表达概念类别，不保存用户措辞；同一含义换一种表述仍可低成本聚合。
6. 用户明确表达可形成 explicit 候选，但重要规则仍需确认；用户纠正一次必须立即停止旧主张影响回答。
7. 相反行为优先检查是否是不同项目、任务类型或风险等级，不直接互相抵消；系统必须保留反例，不能只累计支持证据。
8. 心理、健康、政治、宗教、性取向等敏感推断不自动生成；外部材料、模型回答和工具输出不能成为个人主张的唯一证据。

## 低算力处理链

```text
每轮本地收据
  → 本地策略过滤 / 精确去重（不负责猜语义）
  → 空闲窗口批量生成结构化抽象理解
  → schema / 原句相似度 / 临时范围守卫
  → concept_key 聚合同类证据
  → 仅冲突、重要、跨场景判断升级强模型
  → 用户确认后进入可召回 Personal Core
```

预算目标：

- 前台只做本地原子写入，不等待模型。
- 至少 95% 的轮次不调用强模型。
- 普通对话不扫描整个 Vault。
- 个性化上下文建议默认 1,500 Token，硬上限沿用 2,500 Token。
- Personal Claim 解析只保留进程内缓存，按文件签名自动失效，不生成第二份持久化个人画像。
- Embedding 按文本 hash、Provider 和模型缓存。
- 高强度使用时按 10～20 轮或空闲窗口批处理，不逐轮调用模型。

## 垃圾记忆治理

候选问题包括：精确重复、语义重复、临时状态、错误推断、过期判断、错误范围、无来源低置信、冲突、孤立来源、负向结果和敏感内容。

当前产品动作：

- `dismiss`：驳回本次清理建议，不改 Claim。
- `keep`：明确保留当前 Claim，不改正文。
- `expire`：停止默认召回，保留历史；重要 Claim 必须再次确认。
- `correct / reject / supersede`：修正文义、否认错误判断或由新主张替代。
- `forget`：不可撤销地清除 Claim、关联 Observation/Impact/Outcome、版本、命中它的私人备份、仍保留的来源对话正文和关联运行态/幂等响应；执行前必须单独确认，中断后回滚或在启动时完成。同一来源若已独立提交成项目知识卡，只返回待复核路径，不用个人画像操作越权删除另一事实源。

不能仅因“长期未使用”自动删除重要边界。身份、稳定偏好、决策、政策和项目里程碑不自动删除。

## 上下文与影响审计

Agent 获取的不是完整 Personal Core，而是当前任务相关主张包。每条主张至少带：

- 主张文本
- 状态：明确 / 推断 / 确认
- 适用范围
- 置信度
- 更新时间
- 引用 ID

每次个性化回答要记录 `response_id → claim_id[]`。用户问“为什么这样回答”时，系统能够展示使用了哪些主张；纠正后旧主张下一轮不得继续影响回答。

## 结果反馈

重要任务完成后记录：决定、原因、实际结果、是否返工、用户是否满意、哪些主张影响了选择。个性化不能只学习用户当时选择了什么，还要学习这种选择后来是否有效。

个性化与风险判断必须分离。Agent 可以遵守用户偏好，但在安全、质量、公开发布和不可逆操作上必须保留独立反方判断，不能演变成讨好型回音壁。

## 分阶段实现

### Phase 1：可靠接收——已实现

- Conversation Ledger
- 分片事件与捕获记录
- 幂等 turn ID
- 内容/策略冲突保护
- reconcile 崩溃补投
- 外部材料、临时会话、不记忆隔离
- 1～90 天短期正文保留

### Phase 2：个人主张——已实现

- Personal Core 独立路径与访问控制
- Claim schema、状态机、来源与时间范围
- 明确表达候选
- 确认、纠正、拒绝、替代、解释
- 最小个人上下文组装

### Phase 3：行为理解与结果学习——已实现

- Observation Ledger
- 跨时间证据累积
- 场景切分和冲突检测
- Outcome API
- 误判降权和独立风险通道

### Phase 4：可视化与清理——已实现

- “我”页面
- 理解、能力、项目经历、协作契约、变化历史
- 影响审计
- 记忆健康、清理计划、回滚

### Phase 5：跨 Agent——本机协议已实现，客户端与压力验收未完成

- `context → observe → impact/outcome` 接入协议
- Agent 身份与读取范围
- Codex MCP 已注册；Boujoy Harness、WorkBuddy 和其他客户端仍需分别启用
- 压力、断电、Windows 和长期运行验收

## Phase 3～4 验收

- 同一观察幂等；敏感与外部内容不会保存可还原个人正文。
- 单次行为不直接形成 hypothesis；至少跨 3 次会话、2 个场景才生成未确认候选。
- 影响记录不保存回答正文；Outcome 与选择分层，并能反馈到清理候选。
- 重要 Claim 不会因为低频被自动过期或归档。
- “关于我”展示 Claim、Observation、Outcome、影响、时间线、权限和清理建议。
- Personal Core 备份与项目 Vault 备份物理分开，均有清单校验；Personal Core 恢复前创建安全备份。
- 逐 Agent token 只返回一次，磁盘只保存哈希，身份不能靠请求体冒充。

## Phase 1 验收

- 同一轮重复发送只产生一个收据和一个捕获。
- 相同 turn ID 的不同正文或策略返回 `409`。
- 收据先于分析队列落盘。
- 收据落盘后下游失败可由 reconcile 补投。
- 状态接口不返回原始正文。
- `external_content` 不进入个人分析。
- `session_only` 不进入长期分析。
- `do_not_remember` 事件文件不保存正文。
- 到期正文清理后收据仍可审计。
- 捕获记录一条一文件，不因队列增长反复重写单个大 JSON。
- 捕获正文 hash 使用派生指针直接查重，不随历史数量线性扫描；后台只读取真正待处理的 marker。
- 模型离线使用有上限的指数退避，不能让最早失败项持续占满处理批次。
- v0.1 单文件捕获队列启动时迁入分片，确认分片落盘后原子清空旧文件中的重复正文。
- 现有记忆、检索、写入、回滚、备份、API 和 UI bridge 契约保持通过。

## Phase 2 验收

- 未配置独立目录时 Claim 写入返回 `503`，共享 Vault 不产生 `08-Person`。
- 路径配置必须显式确认，并拒绝 Git、符号链接、项目内外包围关系和非空陌生目录。
- Claim 以一条一文件 Markdown 保存；只有用户确认、未过期、未替代的 Claim 能进入上下文。
- `personal-core / all-agents / agent:<id> / project:<path>` 范围过滤生效；默认 `personal-core` 不交给 Agent。
- 纠正保留旧表述和来源；拒绝、历史错误和精确重复不能静默重建新 Claim。
- 替代关系双向可解释；中断造成的半条链可在启动时修复；带替代关系的 Claim 禁止单边回滚。
- 版本 journal 使用 pending / committed / aborted，重启按内容哈希收敛，不猜测写入结果。
- 非法类型、伪造 confirmed、无来源、坏时间、ID/文件名不一致、损坏 Markdown 和符号链接全部失败关闭。
- HTTP、CLI、MCP 和 UI bridge 保留各自安全边界；浏览器不能选择 Personal Core 路径。
- 1000 Claim 临时样本的最小上下文冷读约 106.6ms、缓存命中约 9.6ms；10K 临时 Claim 创建平均约 1.629ms/条、重复命中约 0.65ms、全量列表约 0.994s，磁盘约 16.9MB。长期运行与真实用户数据分布仍待 Phase 5。
