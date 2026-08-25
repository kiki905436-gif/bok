# Bok UI 实现与验收清单

`AI-Second-Brain-UI` 已完成 Bok 工作台接入，继续复用原来的预览服务、视觉体系和 `/api/bok/v1/...` 同源 bridge。浏览器不保存 bearer token，不启动第二套前端服务，也不直接读取 `.bok/`。

## 已完成页面

1. **今天**：当前项目、下一步、最近变化和待处理数量。
2. **语义搜索**：默认范围与“搜索全部”，展示命中原因、来源和直接阅读入口。
3. **阅读与版本编辑**：读取 Markdown 后携带 `expected_hash` 保存；重要文件要求明确确认，外部并发修改返回冲突而不是覆盖。
4. **随手记**：悬浮入口、`Cmd/Ctrl + Shift + N`、本地草稿恢复和 `Cmd/Ctrl + Enter` 保存；不强迫填写标题、分类或标签。
5. **记忆收件箱**：待处理提议可确认、拒绝和回滚，普通后台状态不弹窗阻断。
6. **活动与撤销**：展示最近动作与可撤销版本。
7. **设置与备份**：展示 Local Only、Provider、索引和 Agent 凭证状态；知识库与 Personal Core 分开创建、校验和恢复备份。
8. **我 / Personal Core**：健康概览、待确认 Claim、已确认理解、观察证据、Outcome、影响记录、变化时间线和垃圾记忆清理候选。

Personal Core 路径选择仍不能从普通网页 bridge 提交。首次设置由受信宿主的原生文件夹选择器完成，或使用 `bok person setup ... --confirm`；页面只显示健康状态和路径是否已经配置。

## 交互口径

- 普通自动记忆、随手记成功、模型离线但已排队、待处理重要记忆只使用 Toast、状态点或角标。
- 云端授权、重要记忆提交、知识库恢复和 Personal Core 恢复使用明确确认。
- Personal Core 恢复要求输入准确目录名；恢复前自动创建安全备份。
- 编辑保存始终携带内容哈希；冲突时保留外部新版本，让用户重新打开再处理。

## 状态映射

| 后端状态 | 用户文案 |
|---|---|
| `queued` | 已安全排队 |
| `waiting_for_model` | 等待本地模型，内容不会丢失 |
| `completed` + `auto_committed` | 已自动整理，可撤销 |
| `completed` + `pending` | 有一条重要变化待查看 |
| `needs_attention` | 需要处理，但不阻断当前工作 |
| `conflict` | 发现两个不同判断，旧版本保持不变 |
| Personal Core `configured=false` | 尚未选择私人记忆目录，不会写入共享知识库 |
| Claim `explicit` | 你明确说过，等待确认是否长期使用 |
| Claim `observed` | 单次证据，不能直接当成稳定偏好 |
| Claim `hypothesis` | 多次证据形成的候选理解，尚未确认 |
| Claim `confirmed` | 已确认；按任务和范围使用 |
| Claim `contradicted` | 出现实质反证，等待复核 |
| Claim `rejected` | 已否认；不会静默重新形成同一判断 |
| Claim `superseded` | 已由新判断替代 |

## 客户端责任

- 写操作生成稳定 `Idempotency-Key`。
- 编辑前保存 `content_hash`，写入时作为 `expected_hash`。
- 浏览器不保存、不读取、不记录 Bok Token；同源 bridge 在服务端认证。
- bridge 写请求保留 `Origin`、`Referer` 与 `Sec-Fetch-Site` 同源证明。
- 不读取 `.bok/` 文件，不自行拼接版本、提议、Claim、观察或备份状态。
- 不因模型失败改调云端，只显示排队状态。
- 普通浏览功能不因 Bok 状态异常失效；Bok 区域单独降级并给出明确提示。

## 本轮验收

- 后端、HTTP、MCP 与 bridge 合同由 `Bok/tests/test_bok_core.py` 覆盖。
- UI 服务契约、真实 Chrome 桌面与 390px 窄屏、键盘入口、搜索、便签、重要确认、编辑、双备份、Personal Core 页面和原有浏览/删除路径由 `AI-Second-Brain-UI/tests/run-product-tests.ps1` 覆盖。
- 任何测试结果必须以本轮真实运行输出为准，不能用本文数字替代实时验收。
