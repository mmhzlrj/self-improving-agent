#!/usr/bin/env python3
"""
原子任务生成器 - 每个任务是一个不可跳过的具体操作
基于 world.html 实际代码行号和参数，MiniMax 无法偷懒
"""

import json

tasks = []
tid = 0

def add(cat, name, desc, exec_cmd="", edit_info=None, verify_cmd=None):
    """添加一个原子任务"""
    global tid
    tid += 1
    task = {
        "id": f"T-{tid:04d}",
        "category": cat,
        "name": name,
        "status": "pending",
        "description": desc,
        "exec_command": exec_cmd,
        "edit_info": edit_info,
        "verify_command": verify_cmd or "node --check /Users/lr/.openclaw/workspace/harness/robot/world.html"
    }
    tasks.append(task)
    return task["id"]

# ================================================================
# 文件: world.html, 路径: /Users/lr/.openclaw/workspace/harness/robot/world.html
# 简写: W = 上述路径
# ================================================================

W = "/Users/lr/.openclaw/workspace/harness/robot/world.html"

# ================================================================
# 第一组: 路灯亮度 (D-07 拆分)
# 每个 PointLight 参数单独一个任务
# ================================================================

# 城市高路灯 sl1 (行 390)
add("light", "sl1 intensity 6→15",
    "将第390行城市高路灯 sl1 的 PointLight intensity 从 6.0 改为 15.0",
    f"grep -n '_cityLight1.*PointLight' {W}",
    {"file": W, "old": "window._cityLight1 = new THREE.PointLight(0xffcc66, 6.0, 25)", "new": "window._cityLight1 = new THREE.PointLight(0xffcc66, 15.0, 25)"}
)

add("light", "sl1 range 25→45",
    "将第390行城市高路灯 sl1 的 PointLight range 从 25 改为 45",
    f"grep -n '_cityLight1.*PointLight' {W}",
    {"file": W, "old": "window._cityLight1 = new THREE.PointLight(0xffcc66, 15.0, 25)", "new": "window._cityLight1 = new THREE.PointLight(0xffcc66, 15.0, 45)"}
)

add("light", "sl1 color 改为更亮暖白",
    "将 sl1 颜色从 0xffcc66 改为 0xffffaa（更亮的暖白色）",
    f"grep -n '_cityLight1.*PointLight' {W}",
    {"file": W, "old": "window._cityLight1 = new THREE.PointLight(0xffcc66, 15.0, 45)", "new": "window._cityLight1 = new THREE.PointLight(0xffffaa, 15.0, 45)"}
)

# 城市高路灯 sl2 (行 391)
add("light", "sl2 intensity 6→15",
    "将第391行 sl2 的 PointLight intensity 从 6.0 改为 15.0",
    f"grep -n '_cityLight2.*PointLight' {W}",
    {"file": W, "old": "window._cityLight2 = new THREE.PointLight(0xffcc66, 6.0, 25)", "new": "window._cityLight2 = new THREE.PointLight(0xffcc66, 15.0, 25)"}
)

add("light", "sl2 range 25→45",
    "将 sl2 的 range 从 25 改为 45",
    f"grep -n '_cityLight2.*PointLight' {W}",
    {"file": W, "old": "window._cityLight2 = new THREE.PointLight(0xffcc66, 15.0, 25)", "new": "window._cityLight2 = new THREE.PointLight(0xffcc66, 15.0, 45)"}
)

add("light", "sl2 color 改为更亮暖白",
    "将 sl2 颜色从 0xffcc66 改为 0xffffaa",
    f"grep -n '_cityLight2.*PointLight' {W}",
    {"file": W, "old": "window._cityLight2 = new THREE.PointLight(0xffcc66, 15.0, 45)", "new": "window._cityLight2 = new THREE.PointLight(0xffffaa, 15.0, 45)"}
)

# 灯柱 PointLight (行 740)
add("light", "灯柱 PointLight intensity 4→10",
    "将 createStreetLight 函数中灯泡 PointLight 的 intensity 从 4.0 改为 10.0",
    f"grep -n 'const light = new THREE.PointLight(0xffffcc' {W}",
    {"file": W, "old": "const light = new THREE.PointLight(0xffffcc, 4.0, 8);", "new": "const light = new THREE.PointLight(0xffffcc, 10.0, 8);"}
)

add("light", "灯柱 PointLight range 8→18",
    "将灯泡 PointLight 的 range 从 8 改为 18",
    f"grep -n 'const light = new THREE.PointLight(0xffffcc' {W}",
    {"file": W, "old": "const light = new THREE.PointLight(0xffffcc, 10.0, 8);", "new": "const light = new THREE.PointLight(0xffffcc, 10.0, 18);"}
)

# 动画循环覆盖值 (行 809-819)
add("light", "动画循环 ambient 强制值 1→2",
    "将动画循环中深夜 ambient 强制覆盖值从 1.0 改为 2.0",
    f"sed -n '809,812p' {W}",
    {"file": W, "old": "window._ambientLight.intensity = 1.0;", "new": "window._ambientLight.intensity = 2.0;"}
)

add("light", "动画循环 sun 强制值 1→2",
    "将动画循环中深夜 sun 强制覆盖值从 1.0 改为 2.0",
    f"sed -n '812,816p' {W}",
    {"file": W, "old": "window._sunLight.intensity = 1.0;", "new": "window._sunLight.intensity = 2.0;"}
)

add("light", "动画循环 cityLight1 强制值 6→15",
    "将动画循环中 _cityLight1 强制覆盖值从 6.0 改为 15.0",
    f"sed -n '815,817p' {W}",
    {"file": W, "old": "if (window._cityLight1) { window._cityLight1.intensity = 6.0; }", "new": "if (window._cityLight1) { window._cityLight1.intensity = 15.0; }"}
)

add("light", "动画循环 cityLight2 强制值 6→15",
    "将动画循环中 _cityLight2 强制覆盖值从 6.0 改为 15.0",
    f"sed -n '816,818p' {W}",
    {"file": W, "old": "if (window._cityLight2) { window._cityLight2.intensity = 6.0; }", "new": "if (window._cityLight2) { window._cityLight2.intensity = 15.0; }"}
)

add("light", "动画循环灯柱强制值 4→10",
    "将动画循环中 scene.children.forEach 里灯柱 intensity 从 4.0 改为 10.0",
    f"sed -n '818,820p' {W}",
    {"file": W, "old": "c.intensity = 4.0;", "new": "c.intensity = 10.0;"}
)

# ================================================================
# 第二组: 台式机布局修复 (D-09 拆分)
# ================================================================

add("layout", "Ubuntu 桌面 y 值检查",
    "用 exec 读取 buildUbuntu 函数，列出所有子部件的 y 值，检查哪些不合理",
    f"sed -n '591,620p' {W} | grep -o 'y[^,)]*[0-9.]*'"
)

add("layout", "Ubuntu 显示器底座 y 修正",
    "将显示器底座 y 从 1.705 改为 1.63（桌面1.58+0.05）",
    f"grep -n '底座.*position.*1.705' {W}",
    {"file": W, "old": "var _m=new THREE.Mesh(new THREE.BoxGeometry(1.5,0.1,0.8), pxMat(0x2a2a2a)); _m.position.set(0,1.705,-0.6);", "new": "var _m=new THREE.Mesh(new THREE.BoxGeometry(1.5,0.1,0.8), pxMat(0x2a2a2a)); _m.position.set(0,1.63,-0.6);"}
)

add("layout", "Ubuntu 显示器支架 y 修正",
    "将支架立柱 y 从 2.255 改为 2.13",
    f"grep -n '立柱.*position.*2.255' {W}",
    {"file": W, "old": "var _m=new THREE.Mesh(new THREE.BoxGeometry(0.3,1.0,0.3), pxMat(0x2a2a2a)); _m.position.set(0,2.255,-0.6);", "new": "var _m=new THREE.Mesh(new THREE.BoxGeometry(0.3,1.0,0.3), pxMat(0x2a2a2a)); _m.position.set(0,2.13,-0.6);"}
)

add("layout", "Ubuntu 显示器外壳 y 修正",
    "将显示器外壳 y 从 4.005 改为 3.38（支架顶2.13+外壳半高1.25）",
    f"grep -n '外壳.*position.*4.005' {W}",
    {"file": W, "old": "var _m=new THREE.Mesh(new THREE.BoxGeometry(3.5,2.5,0.3), pxMat(0x2a2a2a)); _m.position.set(0,4.005,-0.6);", "new": "var _m=new THREE.Mesh(new THREE.BoxGeometry(3.5,2.5,0.3), pxMat(0x2a2a2a)); _m.position.set(0,3.38,-0.6);"}
)

add("layout", "Ubuntu 显示器屏幕 y 修正",
    "将显示器屏幕 y 从 4.005 改为 3.38（与外壳对齐）",
    f"grep -n 'ms.position.*4.005' {W}",
    {"file": W, "old": "ms.position.set(0,4.005,-0.44);", "new": "ms.position.set(0,3.38,-0.44);"}
)

add("layout", "Ubuntu 主机箱位置修正（桌面下方）",
    "将主机箱 y 从 1.75 改为 0.75（放在桌面下方，地面0+半高0.75）",
    f"grep -n '主机箱.*position.*1.75' {W}",
    {"file": W, "old": "var _m=new THREE.Mesh(new THREE.BoxGeometry(1.2,3.5,2.5), pxMat(0x3a3a3a)); _m.position.set(2.0,1.75,0.5);", "new": "var _m=new THREE.Mesh(new THREE.BoxGeometry(1.2,1.5,2.5), pxMat(0x3a3a3a)); _m.position.set(2.0,0.75,0.5);"}
)

add("layout", "Ubuntu 光驱 y 修正（跟随主机箱）",
    "将光驱 y 从 2.5 改为 1.4（主机箱顶部附近）",
    f"grep -n 'd1.*position.*2.5.*1.76' {W}",
    {"file": W, "old": "const d1 = new THREE.Mesh(new THREE.BoxGeometry(1,0.3,0.1), pxMat(0x222222)); d1.position.set(2.0,2.5,1.76);", "new": "const d1 = new THREE.Mesh(new THREE.BoxGeometry(1,0.3,0.1), pxMat(0x222222)); d1.position.set(2.0,1.4,1.76);"}
)

add("layout", "Ubuntu 第二光驱 y 修正",
    "将第二光驱 y 从 2.1 改为 1.1",
    f"grep -n 'd2.*position.*2.1.*1.76' {W}",
    {"file": W, "old": "const d2 = new THREE.Mesh(new THREE.BoxGeometry(1,0.3,0.1), pxMat(0x222222)); d2.position.set(2.0,2.1,1.76);", "new": "const d2 = new THREE.Mesh(new THREE.BoxGeometry(1,0.3,0.1), pxMat(0x222222)); d2.position.set(2.0,1.1,1.76);"}
)

add("layout", "Ubuntu 电源按钮 y 修正",
    "将电源按钮 y 从 3.3 改为 1.35",
    f"grep -n 'pb.*position.*3.3.*1.76' {W}",
    {"file": W, "old": "const pb = new THREE.Mesh(new THREE.BoxGeometry(0.3,0.15,0.1), pxMat(0x441111)); pb.position.set(2.0,3.3,1.76);", "new": "const pb = new THREE.Mesh(new THREE.BoxGeometry(0.3,0.15,0.1), pxMat(0x441111)); pb.position.set(2.0,1.35,1.76);"}
)

add("layout", "Ubuntu 状态灯 y 修正",
    "将状态灯 y 从 5.6 改为 1.55（主机箱顶部）",
    f"grep -n 'ubStatus.*position.*5.6' {W}",
    {"file": W, "old": "ubStatus.position.set(0,5.6,0);", "new": "ubStatus.position.set(0,1.55,0);"}
)

add("layout", "Ubuntu Label y 修正",
    "将 ubuntuLabel y 从 4.8 改为 3.8（跟随显示器顶部）",
    f"grep -n 'ubuntuLabel.*position.*4.8' {W}",
    {"file": W, "old": "ubuntuLabel.position.set(0, 4.8, -0.44);", "new": "ubuntuLabel.position.set(0, 3.8, -0.44);"}
)

add("layout", "MacBook 布局合理性检查",
    "用 exec 读取 buildMacbook 函数，列出所有子部件 y 值，判断是否合理",
    f"sed -n '524,570p' {W} | grep -oP 'y\\)?[:,\\s][\\d.]+'"
)

# ================================================================
# 第三组: NPC 模拟人生行为 (D-08 拆分)
# ================================================================

add("npc", "NPC 代码现状导出",
    "用 exec 导出当前 NPC 相关代码（行681-720），分析现有逻辑",
    f"sed -n '681,720p' {W}"
)

add("npc", "添加 NPC workTarget 属性",
    "在 createNPC 函数中，为 npc.userData 添加 workTarget 属性。MacBook NPC 目标 (0,0,1)，Ubuntu NPC 目标 (10,0,-0.5)。在 createNPC(-6,3) 和 createNPC(6,5) 之后分别设置。",
    f"grep -n 'createNPC.*-6.*3' {W}",
    {"file": W, "old": "createNPC(-6, 3);\ncreateNPC(6, 5);", "new": "createNPC(-6, 3); npcs[0].userData.workTarget = {x:0, z:1}; npcs[0].userData.workType = 'coding';\ncreateNPC(6, 5); npcs[1].userData.workTarget = {x:10, z:-0.5}; npcs[1].userData.workType = 'standby';"}
)

add("npc", "添加 NPC lerp 移动函数",
    "在 createNPC 函数之后、createTree 函数之前，添加 moveNPCToWork(npc) 函数：\nfunction moveNPCToWork(npc) {\n  if (!npc.userData.workTarget) return;\n  const t = npc.userData.workTarget;\n  const dx = t.x - npc.position.x;\n  const dz = t.z - npc.position.z;\n  const dist = Math.sqrt(dx*dx + dz*dz);\n  if (dist > 0.1) {\n    npc.position.x += dx * 0.02;\n    npc.position.z += dz * 0.02;\n    // 面向移动方向\n    npc.rotation.y = Math.atan2(dx, dz);\n  }\n}",
    f"grep -n 'createTree' {W} | head -1"
)

add("npc", "NPC 面向设备（lookAt）",
    "在 moveNPCToWork 函数中添加：当 dist <= 0.1 时，用 Math.atan2(dx, dz) 设置 rotation.y 面向设备方向",
    f"grep -n 'moveNPCToWork' {W}"
)

add("npc", "NPC 打字手臂动画",
    "在 animate 循环的 NPC 区块中，添加手臂打字动画：当 NPC 距离 workTarget < 0.5 且 workType=coding 时，左右手臂 rotation.x 交替 sin 波动",
    f"sed -n '831,838p' {W}"
)

add("npc", "NPC 腿部行走动画",
    "当 NPC 正在移动（dist > 0.1）时，左右腿 position.z 交替前后移动",
    f"sed -n '831,838p' {W}"
)

add("npc", "NPC 修改状态文字",
    "将 updateNPCStatus 中的'Dashboard 运维'改为'编码中...'，'待接入'保持不变，'巡检中'改为'前往工作站'",
    f"grep -n 'Dashboard 运维' {W}",
    {"file": W, "old": "text = 'Dashboard 运维'; color = '#44ff88';", "new": "text = '编码中...'; color = '#44ff88';"}
)

add("npc", "在 animate 中调用 moveNPCToWork",
    "在 animate 循环的 npcs.forEach 中添加 moveNPCToWork(npc) 调用，在 updateNPCStatus 之前",
    f"sed -n '831,838p' {W}"
)

# ================================================================
# 第四组: LED 幕墙修复 (D-10 拆分)
# ================================================================

add("led", "LED 幕墙 fetch 路径修复",
    "将 updateLEDScreen 中的 fetch URL 从 '/api/open?file=harness/robot/project-board.json' 改为直接读取 task-queue.json：fetch('harness/robot/night-build/task-queue.json')",
    f"grep -n 'fetch.*project-board' {W}",
    {"file": W, "old": "fetch('/api/open?file=harness/robot/project-board.json')", "new": "fetch('harness/robot/night-build/task-queue.json')"}
)

add("led", "LED 添加 drawTaskQueue 函数",
    "在 updateLEDScreen 之前添加 drawTaskQueue(ctx, data) 函数：读取 task-queue.json 的 tasks 数组，在 Canvas 上绘制任务列表（名称 + 状态颜色 + 进度条）",
    f"grep -n 'function updateLEDScreen' {W}"
)

add("led", "drawTaskQueue 绘制标题",
    "在 drawTaskQueue 中绘制标题 '0-1 项目任务看板'，字体 bold 48px monospace，颜色 #00ddff，居中在 y=80",
    f"grep -n 'drawTaskQueue' {W}"
)

add("led", "drawTaskQueue 绘制任务列表",
    "遍历 data.tasks，每行绘制：序号 + 名称（28px）+ 状态色圆点（success=绿 pending=黄 failed=红）",
    f"grep -n 'drawTaskQueue' {W}"
)

add("led", "drawTaskQueue 绘制进度条",
    "在底部 y=1000 处绘制进度条：计算 success/total 比例，绘制绿色填充条",
    f"grep -n 'drawTaskQueue' {W}"
)

add("led", "drawTaskQueue 绘制时间戳",
    "在右下角 y=1060 绘制当前时间戳，20px monospace，灰色",
    f"grep -n 'drawTaskQueue' {W}"
)

add("led", "LED 幕墙遮挡物检查",
    "用 exec 列出所有物体的坐标，找出 z>-12 且 x 在 0-10 之间的物体（LED 屏幕前方区域）",
    f"grep -n 'position.set' {W} | grep -v '//'"
)

add("led", "移除 LED 前方遮挡的树",
    "如果发现 createTree(-4,-5) 或 createTree(0,-8) 的 z 值遮挡 LED 屏幕，将其 z 值改为 -20（移到屏幕后方）",
    f"grep -n 'createTree' {W}"
)

add("led", "LED updateLEDScreen 改用 drawTaskQueue",
    "将 updateLEDScreen 的 .then 回调中 drawDashboard(ledCtx, data) 改为 drawTaskQueue(ledCtx, data)",
    f"grep -n 'drawDashboard' {W}",
    {"file": W, "old": "drawDashboard(ledCtx, data);", "new": "drawTaskQueue(ledCtx, data);"}
)

add("led", "LED 幕墙位置微调",
    "将 ledScreen.position.set(5, 5, -12) 的 y 从 5 改为 4（降低到更容易看到的高度）",
    f"grep -n 'ledScreen.position' {W}",
    {"file": W, "old": "ledScreen.position.set(5, 5, -12);", "new": "ledScreen.position.set(5, 4, -12);"}
)

# ================================================================
# 第五组: 天空系统 (D-13 拆分)
# ================================================================

add("sky", "添加星星变量声明",
    "在 buildStars 函数之后添加：let starField = null;",
    f"grep -n 'function buildStars' {W}"
)

add("sky", "添加 createStarField 函数",
    "添加函数：function createStarField() { const geo = new THREE.BufferGeometry(); const positions = []; for (let i=0; i<200; i++) { positions.push((Math.random()-0.5)*100, Math.random()*40+10, (Math.random()-0.5)*100); } geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3)); const mat = new THREE.PointsMaterial({color:0xffffff, size:0.3, transparent:true, opacity:0.8}); starField = new THREE.Points(geo, mat); starField.visible = false; scene.add(starField); }",
    f"grep -n 'buildStars' {W}"
)

add("sky", "在 animate 中控制星星可见性",
    "在动画循环中添加：if (starField) starField.visible = (h < 6 || h >= 19);",
    f"sed -n '800,810p' {W}"
)

add("sky", "添加云层数组声明",
    "在 starField 声明之后添加：const clouds = [];",
    f"grep -n 'starField' {W}"
)

add("sky", "添加 createClouds 函数",
    "添加函数创建 4 朵云：function createClouds() { for (let i=0; i<4; i++) { const geo = new THREE.PlaneGeometry(8+Math.random()*6, 2+Math.random()*2); const mat = new THREE.MeshBasicMaterial({color:0xffffff, transparent:true, opacity:0.6, side:THREE.DoubleSide}); const cloud = new THREE.Mesh(geo, mat); cloud.position.set((Math.random()-0.5)*40, 12+Math.random()*5, -15-Math.random()*20); cloud.rotation.x = -Math.PI/2; clouds.push(cloud); scene.add(cloud); } }",
    f"grep -n 'createStarField' {W}"
)

add("sky", "在 animate 中移动云层",
    "在动画循环中添加：clouds.forEach((c,i) => { c.position.x += 0.005 * (i%2===0 ? 1 : -1); if (Math.abs(c.position.x) > 30) c.position.x *= -1; });",
    f"sed -n '828,830p' {W}"
)

add("sky", "添加月亮变量和函数",
    "添加：let moonMesh = null; function createMoon() { const geo = new THREE.CircleGeometry(1.5, 32); const mat = new THREE.MeshBasicMaterial({color:0xffffee, side:THREE.DoubleSide}); moonMesh = new THREE.Mesh(geo, mat); moonMesh.position.set(20, 25, -30); moonMesh.visible = false; scene.add(moonMesh); }",
    f"grep -n 'clouds' {W}"
)

add("sky", "在 animate 中控制月亮可见性",
    "在星星控制之后添加：if (moonMesh) moonMesh.visible = (h < 6 || h >= 19);",
    f"sed -n '808,812p' {W}"
)

add("sky", "调用初始化函数",
    "在 buildMacbook(); buildUbuntu(); 之前添加：createStarField(); createClouds(); createMoon();",
    f"grep -n 'buildMacbook(); buildUbuntu' {W}",
    {"file": W, "old": "buildMacbook(); buildUbuntu();", "new": "createStarField(); createClouds(); createMoon();\nbuildMacbook(); buildUbuntu();"}
)

# ================================================================
# 第六组: 调研 + 文档任务
# ================================================================

research_items = [
    "QQ养虾空间 UI 设计（布局、配色、交互风格、功能列表）",
    "Animal Crossing 虚拟房屋 UI（等距视角、可爱风格、状态显示方式）",
    "The Sims 网页版/像素版 UI（NPC 行为系统、工作动画、状态气泡）",
    "Monument Valley Low Poly 3D 设计（几何风格、色彩搭配、光影处理）",
    "Cyberpunk 2077 UI 设计（霓虹光效、全息面板、暗色主题）",
    "Homescapes/Gardenscapes UI（2D 游戏化工作空间、进度系统）",
    "Cozy Grove 游戏世界设计（温馨像素风、环境氛围）",
    "macOS 桌面 Widget 设计（glassmorphism、小组件布局）",
    "Windows 11 Widget Board 设计（卡片式布局、动态信息）",
    "Nintendo Switch 主菜单 UI（简洁大方、图标设计）",
    "Notion 页面设计（简洁文档+任务管理融合）",
    "Linear 项目管理 UI（深色主题、任务列表、进度）",
    "Figma Dashboard 设计趋势（2025-2026 UI/UX）",
    "低多边形 3D 城市构建游戏（世界布局、建筑风格参考）",
    "像素艺术 3D 游戏（Stardew Valley / Octopath Traveler 风格）",
]

for i, item in enumerate(research_items):
    add("research", f"调研 {i+1}/15: {item[:40]}",
        f"用 webauth 工具调研：{item}\n要求：\n1. 用至少 2 个平台搜索（DeepSeek/Kimi/豆包）\n2. 描述关键设计元素（色彩、布局、动画、交互）\n3. 列出来源链接\n4. 给出对 0-1 项目 3D 世界的借鉴建议\n5. 不要编造，搜索不到就标注\n输出到 night-build/output/research-{i+1:02d}.md")

# ROBOT-SOP 补充文档
sop_sections = [
    ("Phase 0", "Gateway 对接", ["OpenClaw 安装步骤", "Node 配置步骤", "WebSocket 连接验证", "DM 配对流程", "常见错误排查"]),
    ("Phase 1", "语音陪伴", ["ESP32 引脚分配表", "音频硬件选型", "Whisper 安装配置", "Edge-TTS 配置", "语音识别代码框架", "TTS 代码框架", "端到端测试步骤", "延迟优化方案"]),
    ("Phase 2", "视觉记录", ["ESP32-Cam 固件结构", "WiFi 配置流程", "JPEG 捕获代码", "RTSP 推流代码", "Jetson 接收端代码", "YOLOv8n 配置", "检测结果格式", "带宽估算"]),
    ("Phase 3", "iPhone 感知", ["ARKit 基础框架", "深度数据获取", "OpenClaw bridge 协议", "数据格式设计", "延迟测试方法"]),
    ("Phase 4", "运动控制", ["MQTT 主题设计", "Cyber Bricks 固件结构", "运动指令格式", "速度/方向控制", "安全停止机制", "避障逻辑"]),
    ("贵庚系统", "记忆架构", ["数据结构设计", "存储格式（JSON/SQLite）", "检索算法", "时间线索引", "隐私加密方案", "备份恢复流程", "数据导入导出"]),
]

for phase, section, items in sop_sections:
    for item in items:
        add("doc", f"SOP 补充：{phase} {section} - {item}",
            f"用 exec+sed 读取 ROBOT-SOP.md 中 {phase} {section} 章节。\n补充 {item} 的详细内容。\n追加到 night-build/reports/sop-{phase}-{section}-supplement.md。\n如果信息不足，用 webauth 搜索官方文档。")

# 代码生成任务
code_tasks = [
    ("esp32-cam-rtsp", [
        ("platformio.ini", "PlatformIO 配置文件"),
        ("main.cpp", "主入口 + WiFi 连接 + setup/loop"),
        ("camera.cpp", "摄像头初始化 + JPEG 捕获"),
        ("rtsp_server.cpp", "RTSP 服务器实现"),
        ("led_status.cpp", "LED 状态指示"),
        ("config.h", "配置头文件（WiFi/分辨率/帧率）"),
        ("README.md", "项目说明和使用指南"),
    ]),
    ("mqtt-router", [
        ("mqtt_router.py", "MQTT 连接 + 消息路由主逻辑"),
        ("topics.py", "消息主题定义"),
        ("bridge.py", "OpenClaw HTTP bridge"),
        ("config.yaml", "配置文件模板"),
        ("Dockerfile", "Docker 部署文件"),
        ("README.md", "项目说明"),
    ]),
    ("jetson-yolo", [
        ("detect.py", "YOLO 检测主脚本"),
        ("stream_reader.py", "RTSP 流接收"),
        ("mqtt_publisher.py", "检测结果 MQTT 发布"),
        ("config.yaml", "配置文件"),
        ("start.sh", "启动脚本"),
        ("README.md", "项目说明"),
    ]),
    ("whisper-tts", [
        ("stt_service.py", "语音识别服务"),
        ("tts_service.py", "语音合成服务"),
        ("audio_capture.py", "音频录制"),
        ("vad.py", "静音检测"),
        ("ws_interface.py", "WebSocket 接口"),
        ("config.yaml", "配置文件"),
        ("README.md", "项目说明"),
    ]),
    ("node-setup", [
        ("install.sh", "主安装脚本"),
        ("detect_os.sh", "系统检测"),
        ("install_nodejs.sh", "Node.js 安装"),
        ("install_openclaw.sh", "OpenClaw 安装"),
        ("configure_gateway.sh", "Gateway 配置"),
        ("pair.sh", "自动配对"),
        ("verify.sh", "连接验证"),
        ("uninstall.sh", "卸载脚本"),
        ("README.md", "使用说明"),
    ]),
]

for proj_id, files in code_tasks:
    for filename, desc in files:
        add("code", f"代码：{proj_id}/{filename} - {desc}",
            f"生成 {proj_id} 项目的 {filename}（{desc}）。\n输出到 harness/robot/services/{proj_id}/{filename}\n代码要有注释和错误处理。\n用标准库，不要编造不存在的 API。")

# 竞品分析
competitors = [
    "宇树科技 Unitree Go2 机器人（功能、价格、技术参数）",
    "小米 CyberDog 2（功能拆解、价格、技术架构）",
    "Amazon Astro（功能、价格、上市时间）",
    "三星 Ballie（功能、规格、发布状态）",
    "乐森 Robosen（产品线、价格、核心技术）",
    "Sony Aibo（历代对比、价格、情感交互功能）",
    "Anki Vector（功能评价、停产原因、社区替代方案）",
    "Elephant Robotics MarsCat（功能、价格、AI 能力）",
    "国内桌面陪伴机器人品牌汇总（2024-2026）",
    "日本陪伴机器人市场分析（产品、价格趋势）",
    "OpenClaw vs Home Assistant 全面对比",
    "开源机器人框架汇总（ROS2/Isaac Sim/Cyberdog SDK）",
]

for comp in competitors:
    add("competitor", f"竞品分析：{comp[:50]}",
        f"用 webauth 工具调研 {comp}。\n要求：\n1. 至少 2 个平台搜索\n2. 列出关键参数（价格、功能、技术）\n3. 给出与 0-1 项目的差异化分析\n4. 不要编造数据\n输出到 night-build/reports/competitor-*.md")

# ================================================================
# 第七组: Demo 创建任务（每个 demo 拆成 20-30 个原子步骤）
# ================================================================

demo_atomic_steps = [
    "创建 {demo}.html 基础 HTML 框架（DOCTYPE + head + body + script import map）",
    "添加 Three.js 场景初始化（Scene, Camera, Renderer, OrbitControls）",
    "设置渲染器参数（antialias:false, background color）",
    "添加地面（PlaneGeometry + MeshLambertMaterial）",
    "添加环境光（AmbientLight, intensity 0.5）",
    "添加方向光（DirectionalLight, intensity 0.8）",
    "添加雾气效果（FogExp2）",
    "创建 {style} 风格的桌子模型（BoxGeometry 组合）",
    "创建 {style} 风格的显示器模型",
    "创建 {style} 风格的键盘模型",
    "创建 {style} 风格的椅子模型",
    "创建 {style} 风格的 NPC 身体",
    "创建 {style} 风格的 NPC 头部",
    "添加 NPC 状态气泡（Sprite + Canvas）",
    "添加 1 盏路灯（灯柱 + 灯泡 + PointLight）",
    "添加 1 棵树（树干 + 树冠）",
    "添加相机初始位置和动画",
    "添加窗口 resize 处理",
    "添加 animate 循环",
    "node --check 语法验证",
]

demo_configs = [
    ("demo1", "像素艺术", "#1a1a2e", "#e94560", "#16213e"),
    ("demo2", "Low Poly", "#f0f0f0", "#a8d8ea", "#dcedc1"),
    ("demo3", "赛博朋克", "#0a0a0f", "#ff00ff", "#00ffff"),
    ("demo4", "等距可爱", "#87CEEB", "#FFB6C1", "#98FB98"),
    ("demo5", "纯 2D", "#ffffff", "#f0f0f0", "#e0e0e0"),
]

for demo_id, style, bg, accent, accent2 in demo_configs:
    for step in demo_atomic_steps:
        step_text = step.format(demo=demo_id, style=style)
        add("demo", f"{demo_id}: {step_text[:60]}",
            f"执行: {step_text}\n文件: harness/robot/{demo_id}.html\n背景色: {bg}, 强调色: {accent}\n风格: {style}\n如果文件不存在，先创建基础框架。",
            f"ls harness/robot/{demo_id}.html 2>/dev/null"
        )

# ================================================================
# 第八组: 测试和验证任务
# ================================================================

test_tasks = [
    "验证所有 PointLight intensity > 0（grep 检查）",
    "验证所有 Mesh y 值 >= 0（接地检查）",
    "验证 antialias 为 false",
    "验证 shadowMap.enabled 为 true",
    "验证 fog 使用 FogExp2",
    "验证所有 new THREE.Mesh 后有 castShadow 或 receiveShadow",
    "验证 OrbitControls 有 minDistance 和 maxDistance",
    "验证 Canvas 1920x1080 尺寸",
    "验证没有 NaN 或 Infinity 值",
    "验证所有 color 格式为 0x 开头的 hex",
    "验证 requestAnimationFrame 只调用一次",
    "验证 setDayMode 函数存在",
    "验证 updateClock 函数存在",
    "验证 animate 循环中调用了 controls.update()",
    "验证 animate 循环中调用了 renderer.render()",
    "列出所有全局变量（检查命名冲突）",
    "统计 scene.children 数量（检查内存泄漏）",
    "验证 window resize 事件处理存在",
    "验证所有 addEventListener 的 count",
    "检查是否有 eval 或 innerHTML（安全风险）",
]

for task in test_tasks:
    add("test", f"测试：{task[:55]}",
        f"对 world.html 执行：{task}\n用 exec+grep/sed 工具检查。\n输出结果到 night-build/output/test-{tid:04d}.txt")

# ================================================================
# 生成最终 JSON
# ================================================================

queue = {
    "version": 6,
    "date": "2026-03-27",
    "phase": "continuous-pipeline-v6",
    "description": f"原子任务管道 - {len(tasks)} 个不可跳过的精确任务",
    "调度规则": {
        "核心原则": "每个任务是一个具体的代码修改/验证操作，MiniMax 无法偷懒",
        "执行流程": [
            "1. 查询 MiniMax 额度",
            "2. 检查活跃 subagent",
            "3. 额度 > 30：派下一个 pending",
            "4. 额度 <= 30：等下一周期",
            "5. 无 pending：报告完成"
        ],
        "关键要求": [
            "用 exec+grep/sed 读取文件，不用 read 工具",
            "用 edit 工具精确修改，不要重写整个文件",
            "每次 node --check 验证",
            "完成后 python3 -c 更新 task-queue.json 状态"
        ]
    },
    "stats": {
        "total": len(tasks),
        "estimated_calls": len(tasks) * 5,  # 每个原子任务约 3-5 次调用
        "categories": {}
    }
}

for t in tasks:
    cat = t["category"]
    queue["stats"]["categories"][cat] = queue["stats"]["categories"].get(cat, 0) + 1

queue["tasks"] = tasks

print(json.dumps(queue, ensure_ascii=False, indent=2))
