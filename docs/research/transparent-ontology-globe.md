# Bok 透明本体星球：官方方案研究与视觉原则

## 结论

Bok 采用“借鉴 COBE 的轻盈透明感，借鉴 three-globe / react-globe.gl 的球体分层语义，但继续用原生 Canvas2D 实现”的路线。

本体地图不是地理信息系统，也不需要完整 3D 场景。项目、业务场景、动作、业务对象、验证门和来源才是主角；球体只是帮助用户理解“同一业务世界中的前后层次”。因此最终方案保留透明球壳、微弱大气层、前后两层经纬网、深度衰减和外置标签，不引入 Three.js、React 或第三方球体运行时。

## 研究边界与官方来源

本研究只使用以下三个官方仓库及其中的 README、源码、示例和包清单：

- COBE：<https://github.com/shuding/cobe>
- three-globe：<https://github.com/vasturiano/three-globe>
- react-globe.gl：<https://github.com/vasturiano/react-globe.gl>

## 可借鉴设计对比

| 项目 | 透明球体 | 大气层 | 经纬网 | 前后可见性 | 标签设计 |
| --- | --- | --- | --- | --- | --- |
| COBE | Canvas 背景以透明色清除并开启 alpha blending；球面颜色、亮度、透明度和缩放均可配置。适合借鉴“存在感低于数据”的轻薄球壳。 | `glowColor` 配合片元着色器中的边缘项和球外 `glowFactor`，形成连续、柔和的轮廓辉光。 | 没有内建语义化经纬网；其核心纹理是球面 Fibonacci 采样点。Bok 不照搬世界地图点阵，只借鉴稀疏、低噪声的表面纹理感。 | 球面片元只构造面向观察者的半球；marker / arc 还会投影出 `visible` 状态，并暴露 `--cobe-visible-*` CSS 变量，让背面 DOM 标注淡出。 | marker / arc 可用 `id` 绑定 CSS Anchor Positioning；文字留在 DOM 中，可独立控制 opacity、blur、scale 和交互。可借鉴“几何锚点与文字渲染解耦”。 |
| three-globe | 可隐藏球壳 `showGlobe(false)`，也可通过 `globeMaterial` 注入 Three.js 材质来控制透明度、双面和光照。适合借鉴“球壳只是一个可替换层”。 | 内建 `showAtmosphere`、`atmosphereColor`、`atmosphereAltitude`；默认是球体外侧明亮 halo。 | 内建 `showGraticules`，明确为每 10° 一条经纬线。Bok 借鉴其独立图层，而不照搬高密度。 | 作为 Three.js 3D 对象，实体球壳依赖场景深度遮挡；隐藏或透明化球壳后，背面数据会重新进入视觉竞争。因此透明设计必须额外定义背面降权，不能只把材质 opacity 调低。 | 同时提供球面 3D 文字层和 `CSS2DRenderer` HTML 元素层；文字支持经纬度、海拔、字号、颜色、旋转、圆点方向和过渡。适合借鉴“位置、文字、锚点和过渡分别配置”。 |
| react-globe.gl | API 继承相同的球壳能力；官方 hollow-globe 示例使用透明背景、`showGlobe={false}`、关闭大气层，并用 `DoubleSide` 多边形构造可看穿球体。 | 提供与 three-globe 同构的 `showAtmosphere`、颜色和高度属性；React 状态可驱动开关。 | 提供同构的 10° 经纬网开关。 | WebGL 深度关系由底层 globe.gl / Three.js 场景处理；hollow-globe 示例说明看穿球体时必须显式决定背面几何是否双面显示。Bok 借鉴这种“可见性是产品选择，不是透明度副作用”的原则。 | `labelsData` 及一组 accessor 将业务数据直接映射为文字、坐标、大小、颜色和圆点；另有 click / hover 回调。world-cities 示例还用数据量级控制 label 与 dot 大小。 |

### COBE：最值得借鉴的是轻量视觉，而不是运行时

COBE 官方定位为约 5 KB、zero-dependency 的 WebGL globe。它把球体、点、弧线和辉光压缩到少量 shader 与原生 WebGL 调用中，说明“通透球体”不需要厚重写实纹理。其片元着色器以内外两段 glow 构造轮廓，球内透明度与球外 halo 连续；其 v2 标签方案则把 Canvas 几何位置转换为 CSS anchor 和前后可见性变量。

Bok 应借鉴两点：第一，球壳只提供轮廓、光感和方向，不抢夺节点；第二，背面标签必须获得明确的可见性信号。Bok 不直接采用 COBE，是因为 COBE 仍是 WebGL shader 运行时，且它的世界地图点阵、marker / arc 模型并不对应 Bok 的本体节点、带类型关系和外置中文标签。

直接证据：

- README 与标签锚点：<https://github.com/shuding/cobe/blob/main/README.md>
- 无运行时 dependencies 的包清单：<https://github.com/shuding/cobe/blob/main/package.json>
- 球面透明度、边缘辉光和球外 glow：<https://github.com/shuding/cobe/blob/main/src/globe.frag.glslx>
- 透明清屏、alpha blending 与分层绘制：<https://github.com/shuding/cobe/blob/main/src/index.js>
- DOM anchor 与前后可见性变量：<https://github.com/shuding/cobe/blob/main/src/anchor.js>

### three-globe：最值得借鉴的是显式分层

three-globe 把球壳、经纬网、大气层、点、弧、标签、HTML 和自定义对象拆成独立图层。这个 API 结构适合 Bok：透明球体不应是一张合成图片，而应是可以分别调节的语义层。尤其是 `showGlobe`、`showGraticules` 和 `showAtmosphere` 三个独立开关，提醒我们不要用一套透明度同时控制球壳、网格和光晕。

它也给出一个重要反例：Three.js 的透明材质并不会自动解决信息层级。球壳变透明后，背面节点、连线和文字会与正面竞争；Bok 必须主动使用深度排序、alpha 衰减、虚线和标签策略表达背面，而不是依赖 3D 引擎默认行为。

直接证据：

- Globe、Atmosphere、Graticules、Labels 与 HTML layer API：<https://github.com/vasturiano/three-globe/blob/master/README.md>
- Three.js peer dependency 与直接依赖清单：<https://github.com/vasturiano/three-globe/blob/master/package.json>
- 自定义球体材质示例：<https://github.com/vasturiano/three-globe/blob/master/example/custom-material/index.html>
- 球面标签示例：<https://github.com/vasturiano/three-globe/blob/master/example/labels/index.html>

### react-globe.gl：最值得借鉴的是数据映射接口

react-globe.gl 将球体能力封装为 React props，使数据、视觉 accessor 和交互回调保持一致。对 Bok 最有价值的不是 React 组件本身，而是它把标签拆成 `labelText`、`labelSize`、`labelColor`、`labelAltitude`、dot 和 transition 等独立映射。这说明标签不能只是节点旁的一段固定文本，而应按节点类型、重要性、深度和状态决定样式。

hollow-globe 官方示例尤其有参考意义：透明背景、隐藏球壳和双面多边形是三个独立决定。Bok 对应地也应分别控制画布背景、球面填充和背面图形，避免“整个球一起变淡”的粗糙方案。

直接证据：

- React / Three.js WebGL 定位及完整 props：<https://github.com/vasturiano/react-globe.gl/blob/master/README.md>
- React、globe.gl 与包装层依赖：<https://github.com/vasturiano/react-globe.gl/blob/master/package.json>
- 透明 hollow globe 示例：<https://github.com/vasturiano/react-globe.gl/blob/master/example/hollow-globe/index.html>
- 数据驱动标签示例：<https://github.com/vasturiano/react-globe.gl/blob/master/example/world-cities/index.html>

## Bok 为什么保持 dependency-free Canvas2D

这里的 dependency-free 只指 `AI-Second-Brain-UI` 本体地图渲染层，不代表整个 Bok 产品没有依赖。

1. **现有运行时一致。** 本体地图已经由原生 HTML / CSS / JavaScript 和同一个 Canvas2D 状态机承担布局、缩放、拖拽、命中检测、选中、聚焦与详情展开。引入 Three.js 会再建立 scene、camera、renderer、controls、材质和拾取体系；引入 react-globe.gl 还会增加 React 根节点及组件生命周期，形成第二套 UI 状态模型。
2. **问题规模不要求通用 3D 引擎。** Bok 展示的是有限数量、强语义的业务节点和关系，不是地形、卫星、海量粒子或任意 3D 模型。正交投影得到的 `x / y / depth` 已足以表达球面位置、前后层次和交互命中。
3. **文字可读性高于空间真实感。** 中文业务标签需要保持水平、可测量、可截断、可避让，并能与 leader line 和点击区域共用边界。Canvas2D 可让标签、节点和命中检测使用同一套坐标；3D 几何文字或 CSS2D overlay 都会引入另一层同步与遮挡管理。
4. **依赖成本与收益不匹配。** three-globe 本身有多项直接依赖，并要求 Three.js peer dependency；react-globe.gl 再依赖 React、globe.gl 和包装层。对一个透明球壳而言，这会扩大下载、构建、升级、兼容和调试面，却没有带来当前业务所需的新能力。
5. **离线和桌面壳更稳。** 原生 Canvas2D 不需要 CDN、纹理、字体模型或 WebGL shader 编译，降低本地预览、桌面壳和受限图形环境中的失败面。
6. **未来仍保留升级门槛。** 只有当需求出现大规模粒子/轨迹、真实 3D 模型、复杂相机、GPU shader、地理纹理或 Canvas2D 明确达不到的帧率时，才重新评估 COBE 或 Three.js 系方案。

## 最终采用的视觉原则

1. **语义星球，不做地球。** 不加载国界、地形或写实纹理；经纬线只表达球面方向和深度。
2. **数据比球壳重要。** 球面使用低饱和青绿色透明渐变；中心、项目、场景节点的颜色和对比度始终更高。
3. **大气层只描边。** 采用窄而柔和的径向 halo，亮度集中在轮廓附近，不制造霓虹光球。
4. **经纬网分前后两遍绘制。** 背面线更淡、可用短虚线；球面填充位于两层之间；正面线稍清晰。网格保持稀疏，不机械复制 10° 密度。
5. **背面可感知，但不与正面争夺。** 依据 depth 连续降低节点与边的 alpha；背面连线改为虚线。不要突然隐藏所有背面关系，也不要让透明球体导致前后同权。
6. **标签脱离球面拥挤区。** 场景标签优先排到球体左右两列，以 leader line 回连节点；文字保持水平、最多两行并截断。选中/悬停时提高卡片、描边和连线对比度。
7. **球体与交互共用一套投影。** 绘制、深度排序、命中检测、标签锚点和边线都使用同一组 Canvas2D 坐标，避免视觉位置与点击位置漂移。
8. **克制运动。** 保留用户驱动的拖拽、缩放和聚焦；尊重 reduced motion，不以持续自转制造装饰性噪声。
9. **透明不等于模糊。** 每一层都要有明确职责：大气层说明边界，经纬网说明曲率，深度说明前后，标签说明业务含义。

## 决策摘要

- **采用：** 透明 Canvas2D 球壳、轻量 halo、前后分层经纬网、基于 depth 的排序/透明度/虚线、外置中文标签与 leader line。
- **借鉴但不引入：** COBE 的辉光与可见性信号；three-globe 的独立球壳/网格/大气/标签层；react-globe.gl 的数据 accessor 与 hollow-globe 分层思路。
- **不采用：** 写实地球纹理、持续自转、3D 几何文字、React 组件树、Three.js scene/camera/material/controls 运行时。
