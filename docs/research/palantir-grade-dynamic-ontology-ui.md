# Palantir 级动态本体 UI：从“漂亮星球”到可操作的业务闭环

> 研究日期：2026-08-31
>
> 研究范围：Palantir 与开源项目的官方文档、官方仓库和官方源码；不使用二手评测、博客或社区帖子。
>
> 结论口径：文中“官方事实”均逐项附官方链接；“对 Bok 的建议”是基于这些事实和 Bok 当前数据/UI 的设计推论，不冒充官方结论。

## 一句话结论

**保留星球，但把它降级为“全局态势与入口”，不要把它当主工作台。**

Bok 的星球只负责回答三个问题：现在有哪 3 个项目、24 个业务场景分别在哪里、哪个场景存在证据缺口。用户一旦选择场景，界面应进入稳定的二维场景工作台，按“结果/目标 → 差距 → 驱动因素 → 动作 → 验证门禁 → 来源证据”展开。图的价值不是节点会动，而是用户能沿关系缩小对象集、查看对象事实、执行受约束动作、打开来源证据，并确认执行后的业务读回。

当前 Bok 不应展示 619 个节点的“宇宙全景”。总览只展示 1 个本体、3 个项目和 24 个场景；场景聚焦页只加载该场景相关的对象、动作、验证门禁和来源。超出可读预算时应聚合、筛选或转到列表，不能依靠缩小文字和增加光效解决。

---

## 1. Palantir 如何让本体可探索，而不是把图当装饰

### 1.1 Foundry 的基础不是“图”，而是语义层、动作层和证据链

Foundry 把 Ontology 描述为组织的操作层：对象、属性和链接表达现实世界，Actions 和 Functions 让用户把决策写回系统。对象图只是这一操作层的一种投影；真正闭环还包括权限、校验、事务、来源和执行结果。

- **对象、关系、动作是同一操作模型。** Objects/links 表达现实业务，Actions 捕获决策并将变化写回底层系统。[Foundry introductory concepts（官方）](https://www.palantir.com/docs/foundry/getting-started/introductory-concepts)
- **Ontology 同时包含 semantic 与 kinetic elements。** 前者是对象、属性、链接和对象集，后者是 Actions、Functions 与动态安全能力。[Object Backend overview（官方）](https://www.palantir.com/docs/foundry/object-backend/overview)
- **Ontology Manager 不只管理类型定义。** 对象类型页面同时呈现属性、Actions、链接图、依赖、数据与使用情况，并提供 Action/Function 可观测性。[Ontology Manager overview（官方）](https://www.palantir.com/docs/foundry/ontology-manager/overview/index.html)
- **来源和依赖可沿 lineage 打开。** Data Lineage 把数据源、数据集、对象类型和分析产物作为可选节点；选中后显示定义、同步、问题和属性信息。[Data Lineage elements reference（官方）](https://www.palantir.com/docs/foundry/data-lineage/elements-reference)；[Explore artifacts（官方）](https://www.palantir.com/docs/foundry/data-lineage/explore-artifacts)

对 Bok 的含义：关系线不能只表示“有关联”。每一条关系至少应有稳定类型、方向和可打开的依据；每个动作必须显示适用对象、前置条件、预计影响、执行状态和读回证据。

### 1.2 Object Explorer：先形成对象集，再检查、比较、行动和交接

Object Explorer 的主语不是单个炫酷节点，而是可搜索、过滤、比较、保存和交接的 **object set**。

- 首页提供全局搜索、对象类型分组和链接图；点击对象类型或链接用于开始探索，图承担导航和理解模式的职责。[Object Explorer getting started（官方）](https://www.palantir.com/docs/foundry/object-explorer/getting-started)
- 用户可以跨本体搜索对象，并从命中对象继续 **Search Around**，沿已定义关系扩展邻域。[Search objects（官方）](https://www.palantir.com/docs/foundry/object-explorer/search-objects)
- 过滤器不只支持属性，还支持 linked object、Has Link、嵌套 AND/OR 与关联对象属性，因此关系是可查询条件，不只是视觉连线。[Filter results（官方）](https://www.palantir.com/docs/foundry/object-explorer/filter-results)
- 探索结果可以切换表格或可视化、选中对象打开 Object View、比较对象集、批量执行 Actions、导出或交给兼容应用继续处理。[Object Explorer overview（官方）](https://www.palantir.com/docs/foundry/object-explorer/overview)
- 保存的 Exploration 保留查询参数、过滤器和布局，并在重新打开时计算最新结果；共享仍服从接收者的对象权限。[Save explorations（官方）](https://www.palantir.com/docs/foundry/object-explorer/save-explorations)
- Apply Actions 会把当前选择带入动作表单；存在对象歧义时要求用户消解，不能假装所有选择都可安全执行。[Apply Actions（官方）](https://www.palantir.com/docs/foundry/object-explorer/apply-actions/)

对 Bok 的含义：点击星球上的场景后，不能只放大节点。必须生成一个明确的“当前对象集”，显示筛选条件、数量、来源时间和证据状态，并允许保存/复制链接、交给动作或打开来源。

### 1.3 Object View：选择节点后进入稳定、可复用的事实面板

Palantir 把 Object View 作为对象的中心入口，并让同一面板在多个产品中复用。

- Object View 是属性、链接、相关应用和操作的集中入口，可使用标准视图或 Workshop 配置的定制视图。[Object Views overview（官方）](https://www.palantir.com/docs/foundry/object-views/overview)
- 标准视图突出关键属性，并按 link type 分组关联对象；用户可预览关联对象或把其子集送入新的探索。[Standard Object Views（官方）](https://www.palantir.com/docs/foundry/object-views/standard-object-views)
- Panel Object Views 可复用于 Vertex、Map、Gaia 和 Workshop，避免每个可视化重新发明对象详情。[Panel views in platform（官方）](https://www.palantir.com/docs/foundry/object-views/use-panel-views-in-platform)
- 历史视图只记录通过 Actions 发生的对象编辑；这说明“可追溯”需要明确的写入通道，不能由一张静态图推断出来。[Properties and Links widgets（官方）](https://www.palantir.com/docs/foundry/object-views/widgets-properties-links)

对 Bok 的含义：右侧检查器应是事实主界面，Canvas/星球只是选择器。项目、场景、业务对象、动作、门禁、来源都应共用一套稳定详情框架：名称、类型、定义、状态、所属范围、关系、证据路径、更新时间与可执行动作。

### 1.4 Workshop：关系探索之后必须能驱动运营流程

Workshop 把对象集、变量、事件和 Actions 组合成操作应用，而不是把最终体验停在图上。

- Workshop 以对象层为基础，用 Actions 写回、Functions 表达逻辑、derived properties 计算状态，并用事件连接复杂交互。[Workshop overview（官方）](https://www.palantir.com/docs/foundry/workshop/overview)
- Object Set 变量可由过滤器或 Search Around 形成；变量 lineage graph 用于理解依赖和重算关系。[Workshop variables（官方）](https://www.palantir.com/docs/foundry/workshop/concepts-variables)
- 事件可以顺序执行，但变量更新与依赖重算有明确时序边界，应用不能假设所有组件立即同步。[Workshop events（官方）](https://www.palantir.com/docs/foundry/workshop/concepts-events)
- Workshop Map 让地图选择写入变量，支持绘制、搜索本体/地理对象、时间轴，并可将当前状态带入完整 Map 应用。[Workshop Map widget（官方）](https://www.palantir.com/docs/foundry/workshop/widgets-map)
- Action 表单先验证，只有有效时才可提交；提交生命周期有开始/成功状态，成功后显示反馈并刷新对象数据。[Use Actions in Workshop（官方）](https://www.palantir.com/docs/foundry/workshop/actions-use/index.html)

对 Bok 的含义：场景工作台应该围绕“用户当前要完成的业务判断”组织，而不是围绕节点类型组织。动作成功后必须刷新对象和门禁状态；HTTP 200、按钮变绿或动画结束都不能替代业务读回。

### 1.5 Actions：把前置条件、影响预览、事务和读回做成一等公民

- 一个 Action 可在单次事务中修改属性、增删链接、创建或删除对象，并可由 Foundry 应用或 API 调用。[Object edits overview（官方）](https://www.palantir.com/docs/foundry/object-edits/overview)
- Action rules 将输入参数映射为对象/链接变更，也可触发通知、Webhook 或调度等副作用。[Action rules（官方）](https://www.palantir.com/docs/foundry/action-types/rules)
- Submission criteria 可引用对象、关系和用户上下文；失败信息会直接显示在 Object Explorer、Workshop、Quiver 等消费端，并可在 Ontology Manager 测试。[Submission criteria（官方）](https://www.palantir.com/docs/foundry/action-types/submission-criteria)
- Test run 显示 current 与 proposed changes 和执行日志；副作用默认不真正执行，但必要外部调用会要求明确确认。[Test an Action（官方）](https://www.palantir.com/docs/foundry/action-types/test-run)
- Action 执行同时受类型权限、数据权限、编辑权限和 submission criteria 约束；官方建议默认只允许通过 Actions 编辑对象。[Action permissions（官方）](https://www.palantir.com/docs/foundry/action-types/permissions/)

对 Bok 的含义：每个 Action 节点点击后至少要有“为什么现在可/不可执行”“将改哪些对象/关系”“如何验证”“成功后读回什么”四段信息。若 Bok 暂时不能执行动作，也应把节点明确标成“建议/待执行”，不能营造已经闭环的视觉错觉。

### 1.6 Vertex：图的价值来自 Search Around、筛选、事件和场景比较

- Vertex 从搜索到的业务对象开始，选择对象后可查看属性/派生属性，并通过 Search Around 沿关系扩展；每一步都有对象数量与过滤条件。[Explore object relationships（官方）](https://www.palantir.com/docs/foundry/vertex/explore-object-relationships)
- 节点/边标签可以显示关键属性；事件以徽标和详情呈现；用户可按类型、属性、时间序列或事件样式化，并对选择对象执行 Actions 或继续 Search Around。[Explore graphs（官方）](https://www.palantir.com/docs/foundry/vertex/graphs-explore)
- 图布局可调整；用户可以保存带名称、颜色和边框的 selection，之后快速重新选择。[Graph display options（官方）](https://www.palantir.com/docs/foundry/vertex/graphs-display-options)
- 场景工具把 Actions 与模型用于基线/覆盖参数运行，并比较场景输出，因此“what-if”结果可与原始状态区分。[Scenarios getting started（官方）](https://www.palantir.com/docs/foundry/vertex/scenarios-getting-started)

对 Bok 的含义：动态关系图必须显示用户当前是从哪个集合、通过哪种关系、经过哪一层筛选来到这里。视觉布局变化不应改变业务含义；选择集、筛选和场景状态应可保存、恢复和分享。

### 1.7 Map：空间位置只是一个维度，选择面板和时间控制才形成工作流

- Map 把 base/object/link/overlay/annotation 组织成独立图层，并允许时间属性影响显示和透明度。[Map core concepts（官方）](https://www.palantir.com/docs/foundry/map/core-concepts)
- 用户可以点击、组合键多选、框选和清空选择；Selection Panel 承担详情和 Actions。[Map selection（官方）](https://www.palantir.com/docs/foundry/map/selection)
- 时间轴支持时点、范围、过滤与播放；匹配对象保持完全不透明，不匹配对象被淡化，且播放由用户控制。[Map timeline（官方）](https://www.palantir.com/docs/foundry/map/timeline)
- Map 主界面同时暴露 Layers、Find、Histogram、Info，以及 Select、Search Around、Draw、Measure、Annotate 等工具。[Map getting started（官方）](https://www.palantir.com/docs/foundry/map/getting-started)

对 Bok 的含义：星球上的前后景、光照和位置必须服务于范围、状态或时间，不应被误读成真实地理距离。若位置没有业务语义，就应明确称为“语义星球”，并让图例解释每一种编码。

### 1.8 Palantir 产品共同模式

Palantir 的图之所以不是装饰，原因可归纳为：

1. 从搜索或已知对象集开始，而不是从随机全图开始。
2. 关系有类型、方向、数量和过滤条件，且可 Search Around。
3. 选择节点后进入稳定 Object View，不把 hover tooltip 当事实主界面。
4. 当前对象集可保存、比较、分享、交给其他应用或 Actions。
5. Actions 有输入、权限、submission criteria、影响预览、事务和刷新读回。
6. 来源、lineage、更新时间、问题和权限可检查。
7. 图、地图、表格和工作台是同一语义模型的不同投影，状态可以交接。

---

## 2. Palantir Blueprint：交互、动效与信息密度

### 2.1 Blueprint 官方能直接支持的结论

Blueprint 是面向 **complex, data-dense desktop applications** 的 React UI toolkit，而不是移动优先的展示组件库。这与 Bok 的操作台定位一致，但它并不替 Bok 定义业务状态机或图谱语义。

- 官方定位明确强调复杂、数据密集的桌面 Web 界面。[Blueprint 官方文档](https://blueprintjs.com/docs/)；[Blueprint 官方仓库](https://github.com/palantir/blueprint)
- 官方变量源码使用 4px 基础网格，基础字号 14px、小字号 12px，常规控件高度 30px、小控件 24px，默认 transition duration 为 100ms。[Blueprint `_variables.scss`（官方源码）](https://github.com/palantir/blueprint/blob/develop/packages/core/src/common/_variables.scss)
- 官方公共状态类明确区分 active、compact、disabled、interactive、loading、selected、small，并提供 primary/success/warning/danger intents 和 focus/text 状态类。[Blueprint `classes.ts`（官方源码）](https://github.com/palantir/blueprint/blob/develop/packages/core/src/common/classes.ts)
- Button 样式源码为 disabled、hover、active、loading 和不同尺寸提供独立反馈，说明微交互的职责是让状态清楚，而不是制造持续运动。[Blueprint Button styles（官方源码）](https://github.com/palantir/blueprint/blob/develop/packages/core/src/components/button/_button.scss)
- Blueprint 4.0 的官方迁移说明提高了输入边界等可见性，并以 WCAG 2.0 最低对比度为目标。[Blueprint 4.0 wiki（官方）](https://github.com/palantir/blueprint/wiki/Blueprint-4.0)
- 近期官方变更持续补充 Tooltip 的 Escape 行为、只读输入焦点、导航 aria-label 和 Select 的屏幕阅读器支持。[Blueprint 6.x changelog（官方）](https://github.com/palantir/blueprint/wiki/6.x-changelog)

因此，Bok 可以采用如下 Blueprint 风格边界：

- 4px 网格，操作台默认 8/12/16px 间距；密集区域用 compact，而不是无边界压缩。
- 100ms 左右只用于 hover、pressed、selection outline 等微状态。
- success/warning/danger 只编码真实业务状态；`needs_evidence` 应是缺证状态，不能用成功绿色掩盖。
- disabled、loading、selected 与 keyboard focus 必须视觉可分，且不能只靠颜色。

### 2.2 产品级信息密度应参考 Workshop 官方最佳实践，而非把它误称为 Blueprint 规范

Workshop 的官方应用设计建议补足了 Blueprint 未规定的页面级约束：

- 优先 clarity 与 cohesion，限制同屏可执行项；顶层 primary actions 建议不超过 5 个。
- 使用明确视觉层级，常见场景选择 Compact padding 和 16px 组件间距。
- 页面约 30%–40% 留白，同一视图可见组件建议不超过 10 个。
- 避免横向滚动，筛选器位置保持一致，并使用符合阅读顺序的层级。

官方来源：[Workshop application design best practices](https://www.palantir.com/docs/foundry/workshop/application-design-best-practices)

这些数字不是要求 Bok 机械照抄，而是提醒：数据密集不等于把所有数据同时放进一个 Canvas。Bok 的 24 个场景可以同时作为总览入口，但 619 个节点、1,081 条边必须按场景、类型和任务逐步披露。

### 2.3 Blueprint 没有替 Bok 决定的事项

以下必须由 Bok 自己建立产品规则：

- Canvas/WebGL 节点的键盘与屏幕阅读器替代界面。
- `prefers-reduced-motion` 下相机、惯性、脉冲和边动画的降级方式。
- 图谱标签碰撞的业务优先级。
- Action 的业务前置条件、证据等级和执行读回。
- 何时从图切换到表格、树或详情面板。

---

## 3. 成熟开源球体/图谱的官方能力与边界

### 3.1 对比结论

| 引擎 | 惯性/相机 | 前后景与层级 | 标签 | 选择/聚焦 | 可访问性与 Bok 适用性 |
| --- | --- | --- | --- | --- | --- |
| COBE | `onRender` 每帧由应用更新 `phi`；惯性需应用实现 | anchor 源码暴露前/后可见度，可驱动 DOM opacity/blur/scale | 适合少量 DOM 外置标签；无内建碰撞策略 | 无完整业务 selection/focus 模型 | 极轻，适合首页装饰或小规模总览；不宜独自承担 Bok 工作台 |
| react-globe.gl / three-globe | OrbitControls、`pointOfView()`、暂停/恢复；相机和过渡可编程 | globe、points、arcs、labels、HTML 等分层；HTML 可按前后景控制 | 有 labels/HTML layer，但没有业务优先级碰撞体系 | 各图层 click/hover；可程序化聚焦 | 适合真正 3D 总览，但 DOM 镜像、键盘和标签策略仍需自建 |
| Sigma.js | Camera 支持 pan/zoom/rotation 与动画；Settings 有 inertia 参数 | WebGL edges/nodes + Canvas labels/hover 分层，节点可用 zIndex | `labelDensity`、grid、threshold、`forceLabel`；不是完整语义碰撞求解 | typed node/edge/stage events、reducers、saved app state 可自建 | 适合二维大图探索；Canvas/WebGL 节点需要独立无障碍列表 |
| Cytoscape.js | 内建 pan/zoom、节点拖动、框选；没有以“物理惯性”为核心的官方模型 | Canvas 样式与选择器成熟 | `min-zoomed-font-size`、事件与性能建议；无自动业务优先级碰撞 | tap/select、multi-select、box select、fit/center/animate | 适合关系编辑/分析；应避免把节点拖动与浏览旋转混为一谈 |
| deck.gl | Controller 支持键盘、drag pan/rotate、可配 inertia；view transition 默认可关闭 | GPU 图层和 picking；GlobeView 仍标为 experimental | CollisionFilterExtension 可按优先级实时隐藏重叠对象 | GPU picking 提供 hover/click/drag；相机与对象事件分离 | 适合大规模地理/空间图层；不应只为 Bok 语义星球引入实验 GlobeView |

### 3.2 COBE：视觉轻盈，但交互语义由应用负责

- COBE 官方定位是约 5KB、零依赖的 WebGL globe；应用在 `onRender` 中逐帧修改 `phi`，因此自动旋转、拖动和惯性都不是不可更改的引擎行为。[COBE 官方仓库](https://github.com/shuding/cobe)
- anchor 官方源码计算锚点投影，并暴露前后景可见量；示例可让 DOM 标签随背面状态调整透明度、模糊和缩放。[COBE `anchor.js`（官方源码）](https://github.com/shuding/cobe/blob/main/src/anchor.js)
- 渲染循环和 shader 分别位于官方 `index.js` 与 globe fragment shader，可确认其核心关注是球体渲染，不包含对象集、选择、标签碰撞或无障碍语义。[COBE `index.js`（官方源码）](https://github.com/shuding/cobe/blob/main/src/index.js)；[COBE globe shader（官方源码）](https://github.com/shuding/cobe/blob/main/src/globe.frag.glslx)

对 Bok：可以借鉴 COBE 的轻量球体、前后景衰减和外置 DOM 标签，但不能把 COBE 本身当作 FDE 交互方案。24 个场景已接近需要显式标签布局的规模，应使用两侧标签列/引导线或切换到列表，而不是把文字贴满球面。

### 3.3 react-globe.gl / three-globe：分层和聚焦成熟，但标签与无障碍仍需产品层治理

- three-globe 把 globe、points、arcs、polygons、labels、HTML/custom objects 做成独立层，可单独开关球体、经纬线和 atmosphere；点合并与几何参数用于性能取舍。[three-globe 官方仓库/API](https://github.com/vasturiano/three-globe)
- react-globe.gl 暴露 OrbitControls、`pointOfView({lat,lng,altitude}, ms)`、`pauseAnimation()`、`resumeAnimation()` 和 `onZoom`，因此选择节点后可执行受控相机聚焦，而不需要持续自动旋转。[react-globe.gl 官方仓库/API](https://github.com/vasturiano/react-globe.gl)
- 其 labels 与 HTML layer 支持内容、颜色、尺寸和可见度控制；HTML layer 可根据 front/back 计算隐藏背面内容。[react-globe.gl 官方 API](https://github.com/vasturiano/react-globe.gl)
- pointer interaction 可全局关闭以换取性能；官方说明对象 picking 会带来成本，并提供最近对象优先和 `pointerEventsFilter`。[react-globe.gl 官方 API](https://github.com/vasturiano/react-globe.gl)
- 类型定义列出图层 click/hover、相机和 pointer API，可用于核对交互能力边界。[react-globe.gl `index.d.ts`（官方源码）](https://github.com/vasturiano/react-globe.gl/blob/master/src/index.d.ts)

对 Bok：若未来需要真正 3D 旋转和更复杂图层，react-globe.gl 比手写 Canvas 更省相机工作；但它不会自动决定哪些证据节点优先显示，也不会给 WebGL 节点生成可访问名称。无障碍 DOM 导航器和业务标签优先级仍是必需品。

### 3.4 Sigma.js：适合大规模二维探索，惯性、标签密度和事件边界清楚

- Sigma 数据模型允许节点设置 label、forceLabel 和 zIndex；reducers 可在不修改原图的情况下动态强调选择节点及其邻域。[Sigma graph data（官方）](https://www.sigmajs.org/docs/advanced/data/)
- 官方 customization 文档说明 labels/hover 使用 Canvas，并展示以 reducers 降低非邻居可见度的模式。[Sigma customization（官方）](https://www.sigmajs.org/docs/advanced/customization/)
- 官方事件包含 node/edge/stage 的 enter、leave、down、click、rightClick、doubleClick、wheel 等，并携带原始 MouseEvent/TouchEvent。[Sigma events（官方）](https://www.sigmajs.org/docs/advanced/events/)
- Settings 明确提供 `inertiaDuration`、`inertiaRatio`、`labelDensity`、`labelGridCellSize`、label threshold、移动时隐藏 labels/edges，以及 pan/zoom/rotation 开关。[Sigma Settings（官方）](https://www.sigmajs.org/docs/typedoc/sigma/src/settings/interfaces/Settings/)
- Camera 提供 animate/reset/zoom/unzoom；图层文档说明 edges、nodes、labels、hovers 和 mouse layer 的渲染顺序与技术栈。[Sigma Camera（官方）](https://www.sigmajs.org/docs/typedoc/sigma/src/classes/Camera/)；[Sigma layers（官方）](https://www.sigmajs.org/docs/advanced/layers/)

对 Bok：Sigma 的最大启发不是“能画更多节点”，而是把相机、标签密度、hover、selection 和 stage events 分开。Bok 也应把 hover 预览、点击选择、拖动视口和程序化聚焦设为正交状态，避免一次 pointer gesture 触发多种含义。

### 3.5 Cytoscape.js：成熟的图操作手势和性能约束

- Cytoscape.js 官方交互模型支持背景拖动平移、滚轮/捏合缩放、tap 选择、背景取消、组合键多选、框选和节点拖动，并允许分别配置 panning、zooming、box selection 等能力。[Cytoscape.js 官方文档](https://js.cytoscape.org/)
- 样式系统提供 `min-zoomed-font-size`、`text-events` 等标签控制；官方性能建议指出 labels 尤其是 edge labels 成本较高，可在低缩放隐藏或只在交互时显示。[Cytoscape.js 官方文档：Labels / Performance](https://js.cytoscape.org/)
- 选择器、classes、events 与 `fit`/`center`/animation API 让 selection 与 viewport 可以分别管理。[Cytoscape.js 官方文档](https://js.cytoscape.org/)
- 官方文档定义源码可用于追踪具体 option、style property 与手势说明。[Cytoscape.js `docmaker.json`（官方源码）](https://github.com/cytoscape/cytoscape.js/blob/unstable/documentation/docmaker.json)

对 Bok：默认浏览模式不应允许用户任意拖动语义节点，否则用户会误以为位置本身可编辑或具有业务含义。若未来提供布局编辑，应进入明确的“编辑布局”模式；普通拖动只控制视口/星球。

### 3.6 deck.gl：碰撞优先级和输入控制值得借鉴，GlobeView 不宜作为当前核心依赖

- Controller 支持 scroll zoom、drag pan/rotate、键盘方向键与 +/-，并可配置 inertia；键盘能力属于相机控制，不等于对象本身已可访问。[deck.gl Controller（官方）](https://deck.gl/docs/api-reference/core/controller)
- GPU picking 为 pickable layer 提供 `onHover`、`onClick`、`onDrag` 等对象事件，并能返回像素位置上的 object/layer 信息。[deck.gl Interactivity（官方）](https://deck.gl/docs/developer-guide/interactivity)
- CollisionFilterExtension 在 GPU 上实时隐藏重叠对象，支持 collision group 和 -1000 到 1000 的优先级，但也有几何测试限制。[CollisionFilterExtension（官方）](https://deck.gl/docs/api-reference/extensions/collision-filter-extension)
- view/layer transitions 默认可以是 0，并可指定 fly-to 与 interruption 策略，说明运动应由应用按任务触发。[Animations and transitions（官方）](https://deck.gl/docs/developer-guide/animations-and-transitions)
- deck.gl 官方仍将 GlobeView 标为 experimental。[deck.gl Views（官方）](https://deck.gl/docs/developer-guide/views)

对 Bok：应借鉴其 collision priority 和输入取消模型，不建议仅为语义星球迁移到 deck.gl GlobeView。Bok 没有真实地理投影需求，稳定二维工作台比实验性三维投影更重要。

### 3.7 开源库共同没有解决的问题

上述引擎都能渲染、拾取或移动节点，但没有任何一个库自动知道：

- 哪个 Bok 节点是业务结果、动作、验证门禁还是证据；
- 哪个标签因 `needs_evidence` 应优先于普通对象；
- Action 是否满足前置条件、执行后应该读回什么；
- 屏幕阅读器用户如何遍历 24 个场景并打开同一详情；
- 缺失证据应显示 `— / 来源未提供` 还是业务零值。

这些必须由 Bok 的本体契约、状态机和 DOM 工作台解决，不能外包给图形引擎。

---

## 4. Bok 当前范围与真实业务闭环

### 4.1 当前事实基线

本研究在 2026-08-31 直接读取 Bok 正式 Vault 的当前 Operational Ontology，基线为：

- 3 个项目：Adpilot、GeoLook、tiktok-creator-crm。
- 24 个业务场景：Adpilot 20、GeoLook 2、tiktok-creator-crm 2。
- 136 个业务对象、238 个动作、171 个验证门禁、46 个来源会话。
- typed graph 共 619 个节点、1,081 条边。
- 24 个场景当前全部为 `needs_evidence`。
- 当前投影指纹：`9853ebbef067891ef8b1b6216be2d384b1813a8daf5ff9481637a658c8df66fe`。

这意味着“全景星球看起来完整”与“业务已经闭环”是两回事。节点和边已形成结构，但所有场景仍有证据缺口；UI 必须把缺口显式展示出来，而不是用完整的几何形态制造完成感。

### 4.2 当前 Bok UI 已经做对的部分

当前实现具有以下正确基础，应保留：

- 总览限制为 1 个 ontology、3 个项目、24 个场景，没有直接渲染 619 节点全图。
- 场景聚焦后按业务对象、动作、验证门禁、来源会话分区，而不是只显示通用圆点。
- 项目/场景使用真实业务名称；场景标签放在两侧列并以引导线连接，比贴满球面稳定。
- 前后景通过深度透明度和虚线关系区分；DPR 已封顶为 2。
- 固定布局时不持续 requestAnimationFrame；已读取 `prefers-reduced-motion`。
- Canvas 之外已有项目树、场景检查器和节点列表，具备无障碍镜像的雏形。

### 4.3 当前仍不足以称为 FDE 工作面的部分

- 总览中的拖动目前更接近二维 camera pan，不是真正语义明确的球体旋转；节点按下与拖动边界还不统一。
- hover tooltip 只能预览，尚不能代替稳定 Object View。
- DOM 导航器虽可点击，但尚未形成完整 roving focus、键盘邻域浏览和 live announcement 契约。
- 标签“全部画出”在当前 24 场景尚可，进入更大对象集后会失去碰撞优先级。
- `needs_evidence` 尚未成为总览的第一视觉信号和场景内的可操作缺口队列。
- Action、验证门禁和来源之间还需要明确的“执行前条件 → 执行 → 读回 → 证据”状态链。

### 4.4 什么是 FDE 可用，什么只是漂亮

| 维度 | FDE 可用 | 只是漂亮 |
| --- | --- | --- |
| 进入方式 | 搜索、项目/类型/状态/时间筛选、深链接、保存的对象集 | 打开即看到自动旋转全图 |
| 节点 | 稳定 ID、业务名称、类型、状态、来源时间 | 无文字光点、随机位置、只靠颜色猜类型 |
| 关系 | 有名称、方向、数量、过滤条件，可 Search Around | 大量发光弧线但无法解释“为什么相连” |
| 详情 | 点击进入稳定 Object View，属性、关系、证据和动作同屏 | 只有 hover 气泡，移开即消失 |
| 动作 | 显示前置条件、影响预览、权限、执行状态和业务读回 | 点击后播放成功动画或立即变绿 |
| 证据 | 可打开来源路径，显示更新时间、覆盖、缺口和验证门禁 | “有来源节点”但打不开或无法核对 |
| 缺失值 | `— / 来源未提供`，未知与零严格区分 | 为了图表完整补零或补成功态 |
| 性能 | 按场景加载、聚合、虚拟列表、静止时停帧 | 为展示规模一次绘制 619 节点/1,081 边 |
| 可访问性 | DOM 同步树/列表、键盘激活、焦点可见、状态播报 | 只有鼠标 hover 和 Canvas 像素命中 |
| 动效 | 只表达输入反馈、相机聚焦、状态变化 | 无限自转、脉冲、粒子流、呼吸光环 |

---

## 5. 建议的 Bok 信息架构

### 5.1 三层工作面

#### A. 全局总览：语义星球

固定展示 1 个本体、3 个项目、24 个场景。回答：

- 哪些项目和场景存在；
- 当前选择在哪里；
- 哪些场景 `needs_evidence`、阻塞或已验证；
- 数据截至何时、当前筛选是什么。

不在此层展示 136 个业务对象、238 个动作和 171 个门禁。

#### B. 项目/场景选择：稳定目录与筛选

星球旁的 DOM 导航器是同等重要的主入口，而非“辅助模式”。支持搜索、按状态/类型筛选、项目分组、键盘遍历、深链接和结果数量。星球与目录共享同一 selection，不维护两套事实。

#### C. 场景工作台：二维、可读、可行动

选中场景后，主视图切换到稳定二维布局：

1. 结果/目标与当前差距；
2. 驱动因素与业务对象；
3. 有序 Actions；
4. 每个 Action 对应的 verification gates；
5. 每个门禁对应的 source/evidence；
6. 负责人、状态、最近读回与下一步。

图用于显示当前路径和邻域，右侧详情/底部证据区用于读取完整事实。默认只展示完成当前判断所需的局部子图。

### 5.2 是否保留星球：明确决策

**保留，前提是满足以下硬边界：**

- 名称改为“业务本体总览”或“语义星球”，不暗示真实地理位置。
- 仅用于 3 项目/24 场景的范围与状态导航。
- 不自动无限旋转；首次加载也不做长时间 animate-in。
- 每个场景始终有稳定可见文字，且 DOM 导航器提供等价操作。
- 选择场景后进入二维工作台；不要在球面上继续堆完整业务图。
- 若 WebGL/Canvas 不可用、减少动态开启或性能不足，目录/工作台仍可完成全部任务。

如果产品不愿承担这些约束，应删除星球，直接使用项目 × 场景状态矩阵。一个无法稳定阅读、选择和追证据的星球不会提高 FDE 能力。

---

## 6. 稳定文字标识与标签碰撞

### 6.1 每个节点的文字契约

每个可交互节点必须同时具备：

- `id`：跨刷新稳定，不使用数组位置或临时布局 ID；
- `label`：直接来自正式 Markdown 标题/本体名称，不生成含糊简称；
- `type`：project、scenario、business-object、action、verification-gate、source；
- `status`：至少区分 unknown、needs_evidence、blocked、ready、verified；
- `accessibleName`：默认“类型 + 名称 + 状态”，与 DOM 节点一致；
- `sourcePath` 或证据引用：若不存在就显示明确缺口。

**不可接受的降级：**点可点击但没有稳定文字；文字只在 hover 出现；用颜色代替名称；因碰撞静默隐藏当前选择。

### 6.2 总览标签布局

- 3 个项目标签固定锚定在项目节点旁。
- 24 个场景继续使用左右两列稳定标签 + 引导线；列内按项目、业务顺序或显式排序，不随物理模拟漂移。
- 星球上的点作为空间锚，侧列文字才是主标签；文字点击与点点击完全等价。
- 背面节点可降至 35%–45% 透明度，关系线使用虚线；背面点不抢占前景 pointer picking。
- 选中背面节点时，先将其带到可读前景，再打开稳定详情；不能让用户对着半透明背面猜测。

### 6.3 场景工作台标签优先级

碰撞优先级从高到低：

1. keyboard focus；
2. selected；
3. hovered；
4. 当前场景和结果/目标；
5. failed、blocked、needs_evidence 的门禁；
6. 当前有序 Action；
7. 关键业务对象；
8. 来源节点；
9. 其余邻域。

focus/selected 标签必须强制可见。低优先级发生碰撞时应聚合为“类型 + 数量”或转入相邻列表，不能只留下无名圆点。边标签默认只显示当前路径与选中邻域，其他边可在 hover/selection 后显示。

---

## 7. 点击、拖动、悬停状态机

### 7.1 正交状态

不要用一个 `isDragging` 统管全部交互。建议保存四组正交状态：

```text
scope      = overview | scenario-focus
pointer    = idle | hover(node) | pressed(target) | dragging | inertia
selection  = none | selected(node)
camera     = steady | programmatic-focus
```

任何时刻只有一个 pointer 状态和一个 camera 状态。selection 可跨 hover 和相机变化保持。

### 7.2 事件规则

| 输入 | overview | scenario-focus |
| --- | --- | --- |
| hover（仅 fine pointer） | 临时突出节点、标签和一跳关系；显示简短预览，不改变 selection/camera | 临时突出当前路径；不打开详情、不触发数据加载 |
| pointerdown | 记录起点、目标和 pointer capture | 同左 |
| 移动 ≤ 6px 后释放 | 视为 click | 视为 click |
| 移动 > 6px | 进入 dragging，取消 click；拖动整个总览球体 | 平移工作台视口；默认不拖动语义节点 |
| click project | 过滤/突出该项目场景并保持总览 | 不适用 |
| click scenario | 设为 selection，取消惯性，受控聚焦后进入场景工作台 | 切换场景前保留/提示未完成动作状态 |
| click detail node | 固定 selection，打开 Object View/Action/Gate/Evidence 检查器 | 同左 |
| click background | 清除临时 detail selection，不清除当前场景 | 清除 detail selection，不直接退出场景 |
| wheel/pinch | 受限缩放；任何新输入取消程序化聚焦和惯性 | 受限缩放；取消相机过渡 |
| Escape | 先清 detail selection；第二次返回全局总览 | 同左 |

额外规则：

- hover 永不提交动作、改变筛选或永久改变相机。
- pointer 进入拖动后，本次释放必须 suppress click。
- 程序化聚焦开始前取消惯性；新的 pointer/wheel/key 输入立即中断聚焦。
- 默认浏览模式中节点位置不可拖动。只有显式进入“编辑布局”模式才允许拖节点，并说明布局变化不改变业务关系。
- Back/“返回总览”始终可见，不依赖 Escape。

### 7.3 键盘与屏幕阅读器

- DOM 项目树/场景列表使用 roving tabindex；方向键在同级移动，左右键展开/折叠，Enter/Space 与 click 等价。
- Canvas 控件获得焦点时，方向键旋转/平移，+/- 缩放，Escape 按上述层级返回；不能劫持页面普通滚动焦点。
- 选中节点后把焦点移到稳定检查器标题，而不是留在不可读 Canvas 坐标。
- `aria-live="polite"` 只播报 scope、selection、Action 成功/失败和证据状态变化；不播报每次 hover 或每一帧旋转。
- DOM 中保留完整节点名称、类型、状态和关系数量；Canvas/WebGL 只设整体说明，不伪造数百个无法定位的像素级 tab stop。
- 高对比模式和非颜色编码下，selected/focus/needs_evidence 仍分别由轮廓、图标、文字和形状可辨。

---

## 8. 动效边界

### 8.1 保留的动效

| 动效 | 建议时长 | 用途 | 中断规则 |
| --- | ---: | --- | --- |
| hover/pressed/selection 微反馈 | 80–120ms | 对齐 Blueprint 约 100ms 微状态，让输入反馈清楚 | 新状态立即覆盖 |
| 场景程序化聚焦 | 180–240ms ease-out | 让用户理解“从总览进入该场景” | 任意 pointer/wheel/key 立即取消 |
| 用户拖动后的短惯性 | 220–320ms，上限约 300ms 为宜 | 保留自然手感，但不让内容持续漂移 | 新输入、选择节点、失焦、页面隐藏立即停止 |
| 数据更新 cross-fade | 120–160ms | 表示同一位置的数据被刷新 | 不移动布局，不延迟结果文本 |
| Action loading | 与真实请求同步 | 防重复提交，显示执行中 | 成功/失败必须进入明确终态并读回 |

### 8.2 删除的动效

- 无限自动旋转或空闲时恢复自转；
- 每个节点持续呼吸、脉冲、粒子流；
- 没有业务含义的流动虚线和发光弧线；
- 首次进入长达 1 秒以上的球体登场动画；
- 选中后反复弹跳或 overshoot；
- 数据刷新时重新随机布局；
- Action 尚未读回就播放完成庆祝动画。

### 8.3 `prefers-reduced-motion` 硬边界

当 `prefers-reduced-motion: reduce` 时：

- 关闭 auto-rotation、惯性、animate-in、脉冲、粒子和流动边；
- 程序化相机与滚动立即到达目标，持续时间为 0；
- 数据刷新直接替换或使用不超过一次绘制的静态状态切换；
- hover/selection 通过轮廓、颜色、粗细和文字变化表达，不依赖位移/缩放；
- loading 使用静态文字/进度状态；若必须使用 spinner，应提供文本且避免大面积运动；
- 所有功能与信息保持完整，不能把 reduced-motion 当成“简化版只读模式”。

---

## 9. 性能边界与降级策略

以下是 Bok 的产品预算，不是开源库宣称的硬上限：

### 9.1 可视规模

- 总览固定不超过 28 个业务入口节点（1 ontology + 3 projects + 24 scenarios）。
- 场景图建议同时可视不超过约 80 个节点、120 条边；超出时按类型/步骤聚合或分页，DOM 检查器仍可访问完整内容。
- 永不默认一次渲染 619 节点/1,081 边；“全部”只能是明确、可取消的分析模式，并优先采用二维专用图引擎。

### 9.2 帧预算

- 目标 60fps，单帧主线程预算约 16.7ms；最近 10 帧平均绘制超过 12ms 时开始降级装饰效果。
- DPR 上限继续保持 2；大屏/高 DPR 不按物理像素无限扩张 Canvas。
- 只在 dragging、inertia、programmatic-focus 或数据过渡期间请求下一帧；steady 状态停止 RAF。
- 页面隐藏、组件离屏或标签页失焦时暂停动画和 picking。
- 缓存球面投影、文字测量、路径和碰撞网格；不在每帧重新测量 619 个标签。
- pointer picking 只针对当前前景、当前图层和可交互节点；背面/隐藏节点不参与命中。

### 9.3 分级降级

1. 先关闭 atmosphere、halo、动态边和模糊；
2. 再降低背面边数量、标签更新频率和 DPR；
3. 再聚合非关键节点，保留 selected/focus/needs_evidence；
4. Canvas/WebGL 不可用时使用 DOM 项目树、场景列表、关系表和检查器，完整完成搜索、选择、动作与证据查看。

任何降级都不能隐藏当前选择、失败门禁、证据缺口或 Action 结果。

---

## 10. FDE 可用性的最小验收清单

只有以下项目全部通过，才能把动态本体 UI 称为“FDE 可用”；否则只是视觉候选：

### 总览与范围

- [ ] 总览只显示 3 项目/24 场景，数量和当前 Vault 一致。
- [ ] `needs_evidence`、blocked、verified 有文字和非颜色状态编码。
- [ ] 项目树/搜索/筛选与星球 selection 双向同步。
- [ ] URL 或保存状态可恢复项目、场景、筛选和 selection。

### 对象与关系

- [ ] 每个可交互节点有稳定 ID、稳定中文名称、类型和状态。
- [ ] 每条可探索关系有类型、方向、数量和来源解释。
- [ ] selected/focus 标签永不因碰撞消失。
- [ ] 可从节点执行 Search Around/局部展开，并看见当前路径与过滤条件。

### 动作与证据

- [ ] Action 展示前置条件、输入、影响对象/关系、权限和验证方式。
- [ ] 执行前可预览 proposed changes；不可执行时显示具体原因。
- [ ] 执行后刷新对象与门禁，并展示业务读回，不以 HTTP 200 代替成功。
- [ ] 每个门禁可打开对应来源；缺失时明确显示 `— / 来源未提供`。
- [ ] unknown、zero、failed、needs_evidence 和 verified 不互相混淆。

### 交互与可访问性

- [ ] click、drag、hover、wheel、keyboard 不发生手势串扰。
- [ ] 拖动阈值超过 6px 后不会误触 click。
- [ ] hover 不是获得关键事实的唯一方式。
- [ ] DOM 导航器可完成 Canvas 的全部选择和激活任务。
- [ ] reduced-motion 下没有惯性/自转/相机动画，功能与信息不丢失。

### 性能

- [ ] steady 状态没有持续 RAF。
- [ ] 低性能降级后 selected、缺证门禁和 Action 结果仍可见。
- [ ] 场景超出可视预算时聚合/分页，不缩成无名点云。
- [ ] WebGL/Canvas 失败时可回退到可操作 DOM 工作台。

---

## 11. 推荐实施顺序

1. **先补闭环，不先换引擎：**稳定 Object View、证据路径、Action/Gate 状态和读回。
2. **把 `needs_evidence` 提升为一等状态：**总览可筛选，场景内形成缺证队列。
3. **完成统一 selection 与状态机：**星球、项目树、场景工作台和 URL 共享状态。
4. **完善稳定标签与键盘导航：**总览侧列、场景碰撞优先级、DOM roving focus。
5. **再实现短惯性和受控球体旋转：**先满足 reduced-motion 和中断规则。
6. **最后评估是否换图引擎：**若二维大图分析成为真实需求，优先评估 Sigma.js/Cytoscape.js；若总览确实需要真 3D，再评估 react-globe.gl。COBE 适合视觉外壳，deck.gl GlobeView 当前不作为核心方案。

最终判断标准很简单：用户能否从“这个场景有问题”一路走到“哪些对象造成问题、该执行什么动作、动作是否满足条件、执行后什么数据证明它有效”。如果不能，星球再顺滑也只是漂亮。

---

## 12. Bok 本地事实来源

以下为本研究读取的 Bok 正式事实与当前实现，仅用于建立现状基线，不属于外部官方来源：

- `/Users/lijiashuo/Library/Application Support/com.boujoy.bok/Vault/06-Business/Operational-Ontology.md`
- `AI-Second-Brain-UI/index.html`
- `AI-Second-Brain-UI/app.js`
- `AI-Second-Brain-UI/styles.css`
- `docs/research/transparent-ontology-globe.md`
