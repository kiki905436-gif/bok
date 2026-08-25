# Bok Personal Core 实现路径

## 我们想做成的东西

Bok 最终不是“把聊天原文全存下来”，而是一名长期跟随用户的本地管家：它能从长期协作中逐步形成对用户稳定偏好、工作方式、项目经历、知识与能力边界的抽象理解；Claim 保存的是有证据的理解，不是聊天原句。每条理解都有来源、范围、时间和状态，用户随时能确认、纠正、拒绝、替代、查看影响或彻底忘记。

它必须同时满足四个条件：

1. **越用越了解，但不擅自定义用户。** 明确事实、观察、假设和用户确认永久分层。
2. **省算力。** 每轮前台只做本地收据；普通召回只读少量有效 `learned` / `confirmed` Claim，不逐轮调用强模型。
3. **不制造垃圾库。** 精确重复、历史错误和已拒绝主张有守卫；临时状态可过期；错误范围能纠正或替代。
4. **可解释、可视化、可恢复。** Markdown 是事实源；每条 Claim 有来源、版本、替代链和有效原因。

产品承诺仍是：**理解你，但不定义你；记住过去，继续工作。**

## 已完成的四层闭环

### Phase 1：可靠接收

```text
对话客户端
  → POST /v1/conversations/observe
  → .bok/state/conversations/<event-id>.json 原子收据
  → .bok/state/captures/<capture-id>.json 后台捕获
  → reconcile / 保留期 / 丢弃策略
```

同一 `conversation_id + turn_id` 幂等；篡改返回冲突；外部材料、临时会话和不记忆请求不会进入长期分析。

### Phase 2：独立 Personal Core 与受保护 Claim

```text
受保护的身份 / 长期目标 / 授权规则
  → explicit Claim（未生效）
  → 用户介入确认内容
  → confirmed Claim（仍仅私人可见）
  → 单独授权 Agent / 项目范围后召回
  → 纠正 / 拒绝 / 替代 / 回滚
```

Phase 2 已实现。受保护 Claim 必须由用户确认后才会影响回答；普通低风险理解走 Phase 3 的 `learned` 路径。

### Phase 3：Observation、Outcome 与影响学习

```text
用户原生回合
  → Conversation Ledger 原子收据
  → 第三人称结构化 Observation Ledger
  → 原句相似度、推断依据、临时范围守卫
  → concept_key 聚合同类含义
  → 明确高置信表达，或跨会话、跨日期/场景的保守聚合
  → 低风险理解进入 learned 并安静用于本机回答
  → 身份 / 规则 / 敏感 / 冲突 / 低置信判断等待介入
  → Impact / Outcome 记录实际影响和结果
```

外部材料、临时会话和不记忆内容在入口隔离。一次观察不会直接升级为稳定偏好；身份、长期目标、授权规则、敏感、冲突和低置信判断保持待介入。旧版本遗留的高置信低风险 explicit 卡会在升级处理时安全迁移为 `learned`，不让用户逐条补点确认。

### Phase 4：可视化、清理与跨 Agent 权限

现有 UI 已展示画像、候选、证据、结果、影响、时间线和清理建议；错误理解可在单独确认后彻底忘记。逐 Agent 凭证只保存哈希，可限制范围并撤销。知识库和 Personal Core 使用两套独立备份，恢复前自动创建安全快照。

## 物理目录

### 项目 Vault

项目、知识、内容和普通长期记忆继续留在当前 Vault。运行状态位于：

```text
<Project Vault>/.bok/
  config.json
  auth-token
  state/
    conversations/
    captures/
```

### Personal Core

Personal Core 必须是项目 Vault 之外、Git 仓库之外的独立绝对路径。系统不会在共享 Vault 偷建 `08-Person`。

```text
<Personal Core>/
  PERSONAL-CORE.md
  .gitignore
  Claims/
    person-<uuid>.md          # 正式事实源
  Observations/
    obs-<uuid>.md             # 单次证据与投影状态
  Outcomes/
    outcome-<uuid>.md         # 选择后的实际结果
  Impacts/
    impact-<uuid>.md          # 哪些 Claim 影响过回答，不含回答正文
  Archive/
  .bok/
    activity.jsonl            # 不含主张正文的操作摘要
    versions/
      <version-id>/
        before.md             # 可恢复前一版
        meta.json             # pending / committed / aborted
    backups/
      personal-backup-*.zip   # 独立哈希清单备份
```

`Claims/*.md` 是个人主张事实源。`.bok/versions` 是不可替代的本机恢复历史，但不是事实源；内存缓存不落盘，关闭服务即可丢弃。

未配置 Personal Core 时，个人 Claim 接口保持 `503 personal_core_not_configured`，不会退回当前项目 Vault。首次配置必须显式确认，只允许空目录或已有 `PERSONAL-CORE.md` 的 Bok Personal Core；文件系统根、用户 Home、项目 Vault 内外包围关系、Git 仓库和符号链接目录全部拒绝。

## 代码职责

| 路径 | 单一职责 |
|---|---|
| `Bok/bok_core/person_claim.py` | Claim 类型、Markdown 编解码、字段校验、时间与有效性判定 |
| `Bok/bok_core/person.py` | 独立存储、版本日志、状态迁移、替代链修复、最小上下文与健康检查 |
| `Bok/bok_core/person_learning.py` | Observation、批处理投影、Impact、Outcome、清理候选与可视化数据 |
| `Bok/bok_core/auth.py` | 逐 Agent 哈希凭证、范围和撤销 |
| `Bok/bok_core/config.py` | Personal Core 路径配置与物理隔离校验 |
| `Bok/bok_core/service.py` | 业务服务门面和配置持久化 |
| `Bok/bok_core/api.py` | 本机认证 HTTP 路由与幂等调用 |
| `Bok/bok_core/mcp.py` | 跨 Agent 搜索、上下文、观察、影响、Outcome、随手记和收件箱工具 |
| `Bok/bok_core/cli.py` | `bok person ...` 本机管理命令 |
| `Bok/bok_core/ui_bridge.py` | 现有 UI 同源桥；浏览器禁止修改 Personal Core 路径 |
| `Bok/tests/test_bok_core.py` | 核心、HTTP、MCP、UI bridge、破坏与恢复合同 |

格式层、存储状态机、学习投影和凭证层已经拆开；后续扩展不得把模型推断、批处理和 Outcome 逻辑重新塞进 Claim 存储文件。

## Claim 状态与动作

当前状态集合：

- `explicit`：用户明确表达形成的受保护候选；安全高置信类型会由学习层直接转为 `learned`。
- `observed`：单次行为证据，不直接影响回答。
- `hypothesis`：跨会话、跨场景证据形成但尚未达到安全生效门槛的候选理解。
- `learned`：低风险且证据达标的可更新理解；不冒充用户确认。
- `confirmed`：用户确认并可生效。
- `contradicted`：出现实质反证，等待复核。
- `superseded`：被新主张替代。
- `expired`：超出有效期。
- `rejected`：用户否认，禁止相同主张静默重建。

当前已实现动作：

- `propose`：创建 explicit Claim；精确重复只返回原 Claim。
- `confirm`：只确认这条理解是否准确；确认后仍保持 `personal-core`，不会顺手授权任何 Agent。
- `authorize`：可对有效 `learned` 或已确认 Claim 单独设置 `personal-core / all-agents / agent:<id> / project:<path>` 可见范围；改回 `personal-core` 即收回显式 Agent 授权，内容本身不被删除。
- `correct`：原 ID 纠正，旧表述进入 `statement_history`，阻止历史错误被静默重建。
- `reject`：停止生效并建立拒绝守卫。
- `supersede`：新建 confirmed 后继，旧 Claim 进入 superseded；启动时修复中断造成的半条替代链。
- `explain`：返回来源、范围、状态、反例和有效原因。
- `rollback`：明确确认后回退独立 Claim；有替代关系的 Claim 禁止单边回滚。
- `observe/project`：对话回合原子落账后生成保守观察；低风险信号达到跨会话/场景门槛后形成 `learned`，其余继续积累或进入受保护候选。
- `impact/outcome`：分别记录记忆对回答的影响与选择后的实际结果。
- `cleanup`：列出重复、过期、冲突、低置信、负向结果和长期未使用候选；重要记忆不自动删除。
- `backup/verify/restore`：Personal Core 独立备份、哈希校验和恢复前安全快照。

有效 Claim 有两条路径：一是低风险、证据达标且状态为 `learned` 的理解，可由受信本机 MCP/loopback Agent 按任务最小召回；二是 `confirmed_by_user=true`、状态为 `confirmed` 的受保护 Claim，仍需另行授权给当前 Agent/项目。两类 Claim 都必须未过期、未被替代、无未处理冲突。待介入 Claim 不能预授权；旧客户端留下的范围在确认或迁移时收紧为 `personal-core`。手改 Markdown 伪造 confirmed/learned、非法时间、非法类型、文件名/ID 不一致、符号链接或损坏文件全部失败关闭，健康状态变为不就绪。

## 最小上下文

`POST /v1/person/context` 和 MCP `bok_person_context` 只返回：

- 当前任务真正命中的有效 Claim（安全 `learned` 或已确认并授权的受保护 Claim）；
- `[P1]` 稳定引用；
- Claim ID、类型、范围、置信度、更新时间和命中原因；
- 默认最多 6 条、1,500 Token，硬上限沿用系统上下文预算。

任务类型和 context 范围没有语义重叠时不召回；project / agent 范围必须精确匹配。`learned + personal-core` 仅对启动它的受信本机进程域按任务开放；受保护的 confirmed Claim 仍不会因 `personal-core` 默认范围自动提供给 Agent。

当前 `agent` 和 `project` 既用于最小披露，也可由 loopback HTTP 的独立 Agent 凭证绑定身份、范围和撤销。MCP stdio 仍属于启动它的本机受信进程域，不是跨机器多租户安全边界。

## 低算力与非冗余策略

- 前台对话收据不调用模型。
- MCP 自动观察只返回不含正文、ID 和哈希的紧凑确认；完整收据继续保留在本机状态与认证 API，实测同一示例的工具结果从 1,456 字节降到 214 字节（减少 85.3%）。
- 普通记忆分析按 10～20 条或约 30 秒空闲窗口共用一次 Provider 请求；每条材料仍保持独立 capture、独立来源和独立分析，不用摘要替代原始证据。
- 批量输出缺项或格式不合格时只对缺失项回退原逐条分析；Provider 离线、Local Only、重要确认和原有 API/CLI 手动处理语义不变。
- 强 Agent 给出的明确纠正、稳定偏好和重要决定仍通过 `personal_signals` 实时进入保守 Observation；批处理只负责普通后台判断，不能静默把重要 Claim 变为 confirmed。
- Claim 上下文不扫描项目 Vault，只读取独立 `Claims/`。
- 解析结果只做进程内缓存，不生成第二份持久化 Claim 数据。
- 每次读取先用文件名、mtime、大小和符号链接状态校验缓存；外部手改会自动失效并重读 Markdown。
- 1000 份 Claim 的本轮临时性能样本：冷读约 `106.6ms`，缓存命中约 `9.6ms`，返回 6 条；这是当前开发机样本，不替代后续 10K/长期运行基准。
- 版本 journal 先写 `pending`，Claim 原子替换后改为 `committed`；重启按哈希把中断 journal 判为 `committed` 或 `aborted`，不猜测成功。

## 使用路径

首次选择一个独立空目录：

```bash
PYTHONPATH=Bok python3 -m bok_core --vault "$PWD" \
  person setup "/absolute/path/Bok-Personal-Core" --confirm
```

创建并确认一条明确偏好：

```bash
PYTHONPATH=Bok python3 -m bok_core --vault "$PWD" \
  person propose "回答先给结论，再给必要依据。" \
  --type communication_preference \
  --source conversation:chat-id:turn-id

PYTHONPATH=Bok python3 -m bok_core --vault "$PWD" \
  person confirm person-<uuid>

PYTHONPATH=Bok python3 -m bok_core --vault "$PWD" \
  person authorize person-<uuid> --access agent:codex
```

查看当前健康和最小上下文：

```bash
PYTHONPATH=Bok python3 -m bok_core --vault "$PWD" person health
PYTHONPATH=Bok python3 -m bok_core --vault "$PWD" \
  person context "当前任务" --agent codex --project "02-Projects/example.md"
```

完整 HTTP 路由见 `Bok/docs/API-v1.md`。浏览器同源 bridge 可以管理 Claim，但不能选择或更换 Personal Core 路径；路径配置只允许 CLI 或受信本机 API。

## 当前完成状态与后续验证

### 已完成：行为理解与结果学习

1. Observation Ledger 不把一次行为升级成偏好。
2. 批处理只读取尚未投影的新证据。
3. 至少三个独立会话、跨两个场景后才形成 hypothesis 候选。
4. 冲突按 project、task type、risk 等场景切分，不直接覆盖。
5. Outcome API 把返工、满意度和实际结果与“用户做过什么选择”分开。
6. 重要、敏感、身份、授权和跨项目判断始终进入非阻断确认。

### 已完成：“我”页面与清理

- 可视化身份、目标、工作方式、项目经历、知识与能力、协作契约和变化时间线。
- 展示“为什么这样回答”、Claim 使用记录、来源和替代链。
- 提供重复、过期、冲突、低置信、负向结果和长期未使用候选；重要记忆不因低频自动删除。

### 已完成：本机跨 Agent 接口

- 可为每个 loopback Agent 发放独立身份与可撤销范围凭证。
- 已完成 `context → observe → impact/outcome` API/MCP 协议，并把 Codex MCP 注册到本机配置。
- 工作区规则要求 Codex/WorkBuddy 在工具可用时静默观察用户原生回合；Boujoy Harness 的独立客户端凭证接入留在 Harness 项目内处理。
- 10K 临时 Claim 的写入、指纹去重和列表基线已完成；仍需完成磁盘满、真实 Windows、Obsidian 往返和长期运行验收。

## 本阶段实测

- Bok Python 合同 116/116 通过，包含真实 loopback HTTP 生命周期、MCP 紧凑回执、普通回合批处理/空闲窗口/缺项回退、跨进程写锁、结构化理解/原句拒绝、低风险安静学习、升级迁移、内容确认/Agent 授权分离、Observation/Outcome/权限、彻底忘记及崩溃恢复、双备份、精确/合并恢复、真实问题检索回归、损坏备份结构化失败与破坏性边界测试。
- UI 产品合同 28/28 通过；Chrome 自动逐页覆盖 13 个主页面/分类、Bok 六个工作台标签和个人记忆五个标签的桌面、390px 窄屏，包含独立随手记、搜索、编辑、彻底忘记、双备份、大文件按需加载、双平台依赖启动路径、阅读器、删除和清理残留核验。
- 1000 个临时 Claim 的最小上下文冷读约 106.6ms，进程内缓存命中约 9.6ms；10K 临时 Claim 创建平均约 1.629ms/条、重复命中约 0.65ms、全量列表约 0.994s，磁盘约 16.9MB。样本未写入当前 Vault。
- 测试只使用模拟 Provider，没有调用用户本地模型或云端模型。

## 当前边界

- Personal Core 必须由用户选择独立目录并确认；当前本机已经配置，但公开包不会携带用户私人目录或数据。
- 当前正在运行的旧 Codex 任务不会热加载刚注册的 MCP；新任务或重启 Codex 后才使用 Bok 工具。
- MCP stdio 继承本机进程信任；逐 Agent 强身份只覆盖认证 loopback HTTP，不等于跨机器多租户安全。
- 自动提取只接受模型/Agent 的第三人称结构化理解；没有合格理解时保持无信号或本地排队，不用关键词拼装原句，也不用虚假的“完全了解用户”承诺代替长期真实反馈。
- 已完成 10K 临时存储基线；仍未完成真实 Windows、Obsidian 往返、磁盘满和持续运行验收。
- 本轮自动测试没有调用用户本地模型或任何云端模型。

这些边界不得在 README、界面或发布说明中包装成已完成。
