# Three.js 打造 3D 设备监控/项目管理看板 — 调研报告

**调研时间**: 2026-03-27
**调研关键词**: three.js IoT dashboard, server monitoring, network topology, data center, device visualization

---

## 一、核心参考项目库

### 🏆 网络拓扑 / 节点关系可视化

#### 1. `3d-force-graph` ⭐ 4k+
- **GitHub**: https://github.com/vasturiano/3d-force-graph
- **描述**: Three.js + D3-force 力导向图，3D/2D/VR 多模式，支持数千节点流畅渲染
- **设备状态展示**: 
  - 节点颜色/大小映射设备属性（在线=绿/离线=灰/告警=红）
  - 节点发光（glow）表示活跃状态
- **数据流动展示**: 
  - `linkDirectionalParticles` 属性：沿连线流动的小球粒子，表示数据传输方向
  - 支持曲线（Curved links）+ 箭头指示方向
  - 连线颜色/透明度映射带宽/负载
- **UI 信息展示**: 
  - 节点点击 → 显示 HTML 信息面板（用 `HTML` 元素或 D3）
  - 节点悬停 → 高亮 + Tooltip
- **动画过渡**: 
  - `nodesUpdate`、`linksUpdate` 自动匹配 D3 力模拟
  - 新增节点从地面缩放升起（`pointsTransitionDuration`）
- **后端集成**: 
  - 纯前端库，数据格式 `graphData = { nodes: [], links: [] }`
  - 配合 WebSocket 推送新数据，调用 `.d3Force()` 热更新力模型
- **可借鉴设计**: 
  - 节点用不同几何体（球体=服务器，立方体=路由器，三角=终端）
  - 连线粒子流动画表示"心跳"/"数据正在传输"

---

#### 2. `react-force-graph` ⭐ 3k+
- **GitHub**: https://github.com/vasturiano/react-force-graph
- **描述**: React 版 3d-force-graph，声明式组件，适合 React 项目
- **可借鉴**: 同 3d-force-graph，React 项目直接使用

---

#### 3. `ngraph.three` (anvaka)
- **GitHub**: https://github.com/anvaka/ngraph.three
- **描述**: 百万级节点高性能图可视化，LOD 策略
- **可借鉴**: 超大规模机器人/设备网络的渲染优化思路

---

### 🌐 数据流动画 / 飞线 / 粒子效果

#### 4. `three-globe` ⭐ 3k+
- **GitHub**: https://github.com/vasturiano/three-globe
- **描述**: 3D 地球数据可视化，但核心能力（弧线/粒子/热力图）适用于任何 3D 场景
- **数据流展示（核心）**:
  - **Arc Layer**: 贝塞尔曲线连接两点，带方向箭头，支持渐变色
  - **Paths Layer**: 沿路径的数据流动（`pathDashAnimateTime` 驱动的虚线流动）
  - **Particles Layer**: GPU 粒子系统，支持自定义纹理
  - **Rings Layer**: 自传播涟漪环，适合"新消息"/"告警"状态
- **动画效果**:
  - `arcDashAnimateTime`: 弧线光点从起点流向终点
  - `arcAltitudeAutoScale`: 弧高自动适配距离
  - `ringsData`: 涟漪扩散动画（`ringPropagationSpeed` 控制速度）
- **后端集成**: 
  - `.arcsData([])` 接收数组，WebSocket 更新时重新设置
  - `.pointsData([])` 驱动点数据变化，有平滑过渡动画
- **可借鉴设计**: 
  - 机器人群组之间用弧线/粒子流表示任务分发
  - 告警设备用 Rings 涟漪动画引起注意
  - 任务流用 Paths 虚线动画

---

#### 5. `threejs-eleFlyLine`
- **GitHub**: https://github.com/RainyNight9/threejs-eleFlyLine
- **描述**: Three.js 飞线效果，地球城市间飞线的代码实现
- **可借鉴**: 
  - 贝塞尔曲线 + 粒子拖尾实现飞线
  - 高度+颜色映射数据权重

---

### 🎛️ 3D UI / 信息面板

#### 6. `three-mesh-ui` ⭐ 2k+
- **GitHub**: https://github.com/felixmariotto/three-mesh-ui
- **描述**: 在 Three.js 场景中构建 VR 风格 UI（Flexbox 布局的 3D Block/Text）
- **特点**:
  - 纯 Three.js 对象（Object3D），可直接加入场景
  - 支持 `width/height/padding/backgroundColor` 等 CSS-like 属性
  - 适合做"贴在场地上的信息面板"
- **Demo**: https://three-mesh-ui.herokuapp.com/
- **可借鉴**: 
  - 设备信息卡片做成 3D 面板，贴在设备旁边
  - 支持按钮交互（`ThreeMeshUI.Block` + 事件监听）

---

#### 7. `@react-three/drei` (drei) — Html / Billboard / ScreenSpace
- **GitHub**: https://github.com/pmndrs/drei
- **描述**: React Three.js 最流行的辅助库，提供了大量可直接使用的组件
- **核心组件**:
  - `<Html>`: 在 3D 空间中渲染 HTML 元素，自动处理遮挡（躲在物体后面时隐藏）
  - `<Billboard>`: 让对象始终面向相机（适合标签/Logo）
  - `<Sparkles>`: 粒子星光效果
  - `<Float>`: 浮动动画（让对象轻轻飘动）
  - `<useIntersect>`: 进入/离开视野检测
- **可借鉴**: 
  - `<Html>` 替代 CSS2DRenderer，实现设备信息气泡
  - `<Float>` 让监控图标产生轻微浮动，科技感更强

---

### 📊 状态颜色 + 告警效果

#### 8. 百度/腾讯云 3D 机房可视化系列文章
- **百度云文章**: https://cloud.baidu.com/article/4085119
- **腾讯云文章**: https://cloud.tencent.com/developer/article/2078923
- **描述**: 中文智慧机房/数据中心实战文章
- **设备状态设计**:
  - **绿色** = 正常/在线（饱和度高，活跃）
  - **灰色** = 离线/停机（饱和度低）
  - **红色** = 告警/故障（脉冲闪烁动画）
  - **黄色/橙色** = 警告/亚健康
- **UI 信息展示**:
  - 机柜利用率 → 柱状图立方体（高度=利用率%）
  - 温湿度 → 云图叠加（热力图）
  - 告警 → 设备红色脉冲 + 弹出详情面板
  - 空调风向 → 粒子流动画
- **可借鉴**: 
  - 机器人状态用颜色+脉冲双重编码
  - 告警用红色 + 涟漪扩散动画引起注意

---

### 🎨 后处理效果（科技感加成）

#### 9. `@pmndrs/postprocessing`
- **GitHub**: https://github.com/pmndrs/postprocessing
- **描述**: Three.js 后处理管线，支持 Bloom/Glow/景深等效果
- **科技感关键效果**:
  - **Bloom/Glow**: 发光物体的光晕效果，让"在线"设备有光晕
  - **ChromaticAberration**: 色差效果（赛博朋克感）
  - **Vignette**: 暗角，聚焦中心
  - **DepthOfField**: 景深，模糊背景突出主体
- **可借鉴**: 
  - 告警设备 → Bloom 红色光晕
  - 正常设备 → Bloom 绿色光晕
  - 背景建筑 → DepthOfField 模糊

---

### 🏗️ 工程化架构参考

#### 10. `Sean-Bradley/Three.js-TypeScript-Boilerplate`
- **GitHub**: https://github.com/Sean-Bradley/Three.js-TypeScript-Boilerplate
- **描述**: TypeScript + Three.js 模块化工程，包含数字孪生示例
- **可借鉴**: 
  - 完整的项目工程结构
  - 三维交互（Raycaster 射线检测）的标准写法
  - Tween.js 做 UI 弹出动画

---

## 二、分维度设计建议

### 1. 设备/节点状态展示

| 状态 | 颜色 | 动画 | 视觉权重 |
|------|------|------|---------|
| 在线/正常 | `#00ff88` 亮绿 | 轻微脉冲（glow）| 高 |
| 离线/停机 | `#666666` 灰 | 无 | 低 |
| 告警/故障 | `#ff3333` 红 | 红色脉冲 + 涟漪扩散 | 最高（闪烁）|
| 警告/亚健康 | `#ffaa00` 黄 | 慢速脉冲 | 中 |
| 任务执行中 | `#00aaff` 蓝 | 粒子流环绕 | 高（动态）|

**实现方式**:
```javascript
// 状态颜色映射
const statusColor = (status) => ({
  online: 0x00ff88,
  offline: 0x666666,
  warning: 0xffaa00,
  alert: 0xff3333,
  running: 0x00aaff,
}[status])

// 发光材质
const material = new THREE.MeshStandardMaterial({
  color: statusColor(device.status),
  emissive: statusColor(device.status),
  emissiveIntensity: device.status === 'alert' ? 2.0 : 0.5,
})
```

---

### 2. 数据流动 / 连接关系展示

**方案 A: 连线 + 粒子流**（`3d-force-graph` 风格）
```javascript
// linkDirectionalParticles: 沿连线流动的小球
graph
  .linkDirectionalParticles(3)  // 3个小球
  .linkDirectionalParticleSpeed(0.05)  // 速度
  .linkDirectionalParticleColor(() => '#00ffff')  // 青色
```

**方案 B: 贝塞尔弧线飞线**（`three-globe` 风格）
```javascript
globe
  .arcsData(robotConnections)
  .arcColor(['#00ffff', '#ff00ff'])  // 渐变色
  .arcDashAnimateTime(2000)  // 2秒飞完
  .arcAltitudeAutoScale(0.5)  // 弧高
```

**方案 C: 虚线流动 + Shader**（自实现）
- 用 `LineDashedMaterial` + 动态 `dashSize` 实现"数据跑动"效果
- 或用 `TubeGeometry` + 沿曲线移动的粒子

**推荐**: 对于 0-1 机器人项目，方案 A 最简单（`3d-force-graph` 自带），方案 B 最炫酷（弧线适合展示任务分发路径）。

---

### 3. UI 信息展示方式

| 方式 | 适用场景 | 库/工具 |
|------|---------|---------|
| **Sprite + Canvas 文字** | 大量标签（性能好）| `three-spritetext` |
| **CSS2DRenderer** | 复杂 HTML 内容（表格/图表）| Three.js 内置 |
| **three-mesh-ui** | 3D 空间中的按钮/面板 | `three-mesh-ui` |
| **@react-three/drei Html** | React 项目 | `drei` |
| **Sprite 贴图** | 简单图标+数字 | Canvas 绘制 |

**推荐组合**:
- 设备名称 → `three-spritetext`（轻量，大量也不卡）
- 设备详情弹窗 → `CSS2DRenderer`（支持 HTML 复杂样式）
- 3D 操作按钮 → `three-mesh-ui`

**代码示例（CSS2DRenderer）**:
```javascript
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'

const label = new CSS2DObject(divElement)
label.position.set(x, y, z)
scene.add(label)

// 在 divElement 中写任意 HTML
divElement.innerHTML = `
  <div class="device-label">
    <div class="title">${device.name}</div>
    <div class="status">${device.status}</div>
    <div class="metric">CPU: ${device.cpu}%</div>
  </div>
`
```

---

### 4. 动画和过渡效果

| 动画 | 用途 | 实现 |
|------|------|------|
| 设备脉冲 | 告警/活跃状态 | `emissiveIntensity` 随时间 sin 波动 |
| 涟漪扩散 | 新消息/新任务 | `ringPropagationSpeed` + `ringMaxRadius` |
| 粒子飞线 | 数据传输 | `linkDirectionalParticles` 或 Shader |
| 缩放升起 | 新设备加入 | `pointsTransitionDuration: 1000` |
| 颜色渐变 | 状态切换 | TWEEN.js 或 gsap 插值颜色 |
| 相机飞入 | 点击设备跳转 | `camera.position.set()` + TWEEN |

**推荐动画库**: `gsap`（性能好，API 简洁）或 Three.js 内置 `TWEEN`

---

### 5. 与后端数据集成

**推荐架构**: WebSocket + 状态管理

```
后端服务 → WebSocket 推送 → 前端状态存储 → Three.js 渲染更新
                    ↓
            设备状态/任务数据/告警
```

**实现模式**:
```javascript
// WebSocket 接收数据
const ws = new WebSocket('ws://your-server/robots')

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  // 更新设备状态
  data.devices.forEach(d => {
    updateDeviceStatus(d.id, d.status)
    updateDevicePosition(d.id, d.position)  // 位置变化动画
  })
  
  // 更新任务流（连线数据）
  updateTaskFlows(data.tasks)
}

// 在 render loop 中驱动动画
function animate() {
  requestAnimationFrame(animate)
  
  // 更新粒子流
  graph
    .nodes(newNodes)
    .links(newLinks)
  
  renderer.render(scene, camera)
}
```

**轮询备选方案**: REST API + `setInterval` 轮询（适合小规模设备）
```javascript
setInterval(async () => {
  const data = await fetch('/api/devices').then(r => r.json())
  syncToScene(data)
}, 5000)
```

---

### 6. 可借鉴的设计模式和代码结构

#### 模式 1: 数据驱动渲染
```javascript
// 核心：将 Three.js 对象与数据 ID 绑定
const meshMap = new Map() // deviceId → THREE.Mesh

function updateDevice(id, data) {
  const mesh = meshMap.get(id)
  if (!mesh) return
  
  // 颜色变化
  mesh.material.color.setHex(statusColor(data.status))
  mesh.material.emissive.setHex(statusColor(data.status))
  
  // 位置变化（平滑插值）
  gsap.to(mesh.position, {
    x: data.x, y: data.y, z: data.z,
    duration: 0.5,
    ease: 'power2.out'
  })
}
```

#### 模式 2: 组件化 3D 对象
```javascript
class Device3D {
  constructor(id, type) {
    this.id = id
    this.mesh = this.createMesh(type)
    this.label = this.createLabel()
    this.isAlert = false
  }
  
  createMesh(type) {
    const geometry = {
      robot: new THREE.SphereGeometry(0.5),
      server: new THREE.BoxGeometry(1, 1, 1),
      router: new THREE.TorusGeometry(0.5, 0.2),
    }[type]
    
    return new THREE.Mesh(geometry, new THREE.MeshStandardMaterial())
  }
  
  setStatus(status) {
    this.mesh.material.color.setHex(statusColor(status))
    this.isAlert = status === 'alert'
  }
}
```

#### 模式 3: 交互管理层（Raycaster）
```javascript
const raycaster = new THREE.Raycaster()
const mouse = new THREE.Vector2()

function onClick(event) {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1
  
  raycaster.setFromCamera(mouse, camera)
  const intersects = raycaster.intersectObjects(scene.children)
  
  // 找到有 deviceId 的对象
  const target = intersects.find(i => i.object.userData.deviceId)
  if (target) {
    showDevicePanel(target.object.userData.deviceId)
  }
}

window.addEventListener('click', onClick)
```

---

## 三、0-1 机器人项目具体建议

### 🎯 视觉升级建议（按优先级）

**P0 — 必须有（基础体验）**
1. **设备状态颜色编码**: 绿/灰/红/黄 对应 在线/离线/告警/警告
2. **设备名称 3D 标签**: 用 Sprite 或 CSS2DRenderer，悬停/选中高亮
3. **WebSocket 实时数据**: 设备状态变化时自动更新场景
4. **点击设备弹出详情面板**: 设备名、状态、运行数据、任务历史

**P1 — 体验提升（更好看）**
5. **设备脉冲动画**: 告警设备红色闪烁，正常设备轻微呼吸
6. **任务分发连线 + 粒子流**: 展示机器人间的任务分配关系
7. **科技感后处理**: Bloom Glow 效果 + 暗角
8. **相机动画**: 点击设备后平滑飞入

**P2 — 高级效果（更炫酷）**
9. **热力云图**: 根据设备 CPU/温度显示颜色热力图
10. **路径轨迹**: 机器人运动轨迹用渐变线表示
11. **Rings 涟漪动画**: 新任务到达时设备周围扩散涟漪
12. **3D 拓扑布局**: 用力导向图自动布局机器人网络拓扑

---

### 🛠️ 推荐技术栈组合

| 层级 | 技术 | 说明 |
|------|------|------|
| 3D 引擎 | Three.js (r150+) | 核心 |
| 框架 | React + @react-three/fiber | 如果用 React |
| 拓扑图 | 3d-force-graph | 节点+连线+粒子流 |
| 球体标签 | @react-three/drei Html | 3D 空间 HTML |
| 后处理 | @pmndrs/postprocessing | Bloom/Glow |
| 动画 | gsap | 颜色/位置插值 |
| 状态管理 | Zustand | 轻量状态存储 |
| 数据推送 | WebSocket | 实时数据 |

**纯原生方案**（不用 React）:
```
Three.js + CSS2DRenderer + 3d-force-graph + gsap + 原生 WebSocket
```

---

### 📁 推荐参考的 GitHub 仓库

| 仓库 | Stars | 用途 |
|------|-------|------|
| vasturiano/3d-force-graph | 4k | 网络拓扑首选 |
| vasturiano/three-globe | 3k | 弧线/粒子效果 |
| pmndrs/drei | 9k+ | 3D UI 组件 |
| pmndrs/postprocessing | 1k+ | 科技感后处理 |
| felixmariotto/three-mesh-ui | 2k | 3D 空间 UI |
| Sean-Bradley/Three.js-TypeScript-Boilerplate | — | 工程结构参考 |

---

### 🔑 关键成功因素

1. **状态编码要直观**: 颜色 + 动画双重编码，告警必须能第一时间抓住注意力
2. **数据流可视化**: 连线上的粒子流是最直接的数据"正在传输"的表达
3. **信息层次分明**: 3D 场景承载视觉，HTML 面板承载信息，不要混用
4. **性能要稳**: 用 `InstancedMesh` 处理大量同类设备，用 `LOD` 处理复杂模型
5. **实时性**: WebSocket 推送优先，轮询作为降级方案

---

*报告生成时间: 2026-03-27*
*数据来源: GitHub, 百度开发者社区, 腾讯云开发者社区, 各项目官方文档*
