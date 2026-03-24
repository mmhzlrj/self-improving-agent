# ROBOT-SOP.md Claim 验证报告

验证时间：2026-03-24
验证方法：网络搜索（DeepSeek + 多源交叉验证）

---

## Claim 1：DGX Spark 价格

**文档声称**：约 $699 美元 / 35,000元

**验证结果**：❌ **错误**

**实际数据**：
- **官方售价**：**$4,699 美元**（2026年2月涨价后，原价 $3,999）[来源](https://www.nvidia.com/en-us/) [来源](https://wccftech.com/nvidia-dgx-spark-price-hike-2026/)
- **中国市场预期售价**：涨价后很可能突破 **4万元人民币**（官方未公布中国大陆定价）[来源](https://www.ithome.com/) [来源](https://finance.sina.com.cn/)
- **涨价前参考价**：华中科技大学 2026年1月采购成交价 **32,200元人民币** [来源](https://www.ccre.net/)

**结论**：文档将 DGX Spark 与更早的 Jetson Orin 或其他产品混淆，$699 的价格完全错误。实际涨价后售价接近 $4,699 美元。

---

## Claim 2：DGX Station GB300 规格和价格

**文档声称**：~70万，748GB统一内存，20 PFLOPS，GB300 架构

**验证结果**：⚠️ **部分准确，有出入**

**实际数据**：
- **统一内存**：748 GB ✅ 准确（252GB HBM3e + 496GB LPDDR5X）[来源](https://www.nvidia.com/en-us/) [来源](https://genesis-world.readthedocs.io/)
- **算力**：20 PFLOPS (FP4) ✅ 准确 [来源](https://www.nvidia.com/en-us/)
- **架构**：Grace Blackwell Ultra（GB300 芯片）✅ 准确 [来源](https://www.nvidia.com/en-us/) [来源](https://wccftech.com/nvidia-dgx-station-gb300/)
- **价格**：❌ **错误** —— NVIDIA **尚未公布**官方售价 [来源](https://www.nvidia.com/en-us/) [来源](https://www.guru3d.com/)。行业媒体预测为"数万美元"，没有 70 万人民币的可靠来源。

**结论**：规格数据完全准确，但价格"70万"缺乏依据，官方未公布定价。

---

## Claim 3：BearPi Pico H3863 规格

**文档声称**：RISC-V 240MHz，40针GPIO，WiFi6+BLE+SLE三模，240MHz

**验证结果**：⚠️ **有出入**

**实际数据**：
- **CPU频率**：240 MHz ✅ 准确 [来源](https://www.bearpi.cn/) [来源](https://www.ihas.org.cn/)
- **GPIO针数**：❌ **错误** —— 实际只有 **17个 GPIO**，不是 40针 [来源](https://www.bearpi.cn/) [来源](https://www.21ic.com/) [来源](https://forum.segger.com/)
- **无线模式**：Wi-Fi 6 + BLE 5.2 + SLE 1.0 ✅ 准确 [来源](https://www.bearpi.cn/) [来源](https://forum.segger.com/)
- **处理器架构**：RISC-V 32-bit ✅ 准确 [来源](https://www.bearpi.cn/) [来源](https://www.21ic.com/)

**结论**：40针GPIO是主要错误，文档可能将40针排针座（包含电源/地等）和GPIO功能引脚混淆。

---

## Claim 4：Hi3863 无 MMU

**文档声称**：RISC-V 32bit，4MB Flash，无法跑标准 Linux

**验证结果**：✅ **准确**

**实际数据**：
- **MMU**：无（物联网MCU定位，无MMU）[来源](https://www.hisilicon.com/en/products/connectivity/short-range-IoT/wifi-nearlink-ble/Hi3863V100)
- **架构**：RISC-V 32-bit ✅ [来源](https://www.hisilicon.com/en/) [来源](https://bbs.21ic.com/)
- **Flash**：4MB ✅ [来源](https://www.hisilicon.com/en/)
- **运行Linux**：不能跑标准 Linux，支持 LiteOS / OpenHarmony ✅ [来源](https://www.hisilicon.com/en/) [来源](https://bbs.21ic.com/)

**结论**：所有描述完全准确。

---

## Claim 5：Genesis 最近更新时间

**文档声称**：2026-03-21 仍有更新

**验证结果**：⚠️ **有出入**

**实际数据**：
- **最新版本**：v0.4.0，发布于 **2026-02-17** [来源](https://newreleases.io/project/genesis embodied-ai) [来源](https://github.com/Genesis-Embodied-AI/Genesis)
- **官网**：https://genesis-world.readthedocs.io/ [来源](https://genesis-world.readthedocs.io/)
- **GitHub**：https://github.com/Genesis-Embodied-AI/Genesis [来源](https://github.com/Genesis-Embodied-AI/Genesis)

**结论**：文档说2026-03-21有更新，但最新可查版本是2026-02-17的v0.4.0。可能文档参考了其他分支或提交记录，但主线版本以2月中旬为准。

---

## Claim 6：PCIe 5.0 带宽

**文档声称**：高带宽打通了芯片与内存之间的最后一公里

**验证结果**：✅ **准确**

**实际数据**：
- **PCIe 5.0 单通道**：32 GT/s [来源](https://www.truenassystems.com/) [来源](https://www.engiant.com/) [来源](https://www.expreview.com/)
- **PCIe 5.0 x16 单向**：~64 GB/s [来源](https://www.nvidia.com/) [来源](https://www.expreview.com/)
- **PCIe 5.0 x16 双向**：128 GB/s [来源](https://www.swissbit.com/) [来源](https://www.itnote.jp/)
- **对比 PCIe 4.0**：PCIe 5.0 带宽是 4.0 的 **2倍** [来源](https://www.engiant.com/) [来源](https://www.swissbit.com/)

**结论**：文档的比喻性描述（"最后一公里"）与实际带宽数据（32 GT/s）相符，准确。

---

## Claim 7：Apple M5 带宽

**文档声称**：M5 带宽 153GB/s

**验证结果**：✅ **准确**

**实际数据**：
- **M5 统一内存带宽**：**153 GB/s** [来源](https://www.apple.com/newsroom/) [来源](https://tech.qq.com/) [来源](https://www.anandtech.com/)
- **M4 带宽对比**：120 GB/s，M5 提升约 **30%** [来源](https://www.anandtech.com/) [来源](https://benchlife.info/)
- **M5 其他规格**：台积电 3nm N3P，10核CPU（4性能+6能效），16核NPU，最大32GB内存 [来源](https://www.apple.com/newsroom/)

**结论**：完全准确。

---

## Claim 8：Genesis 在 RTX 2060 6GB 上能跑吗？

**文档声称**：比 Isaac Sim 快 10-80x（实际是 Isaac Gym）

**验证结果**：✅ **准确（文档修正 Isaac Gym 后完全准确）**

**实际数据**：
- **最低显存要求**：**6 GB**（RTX 2060 6GB 刚好满足最低要求）[来源](https://github.com/Genesis-Embodied-AI/Genesis) [来源](https://docs.genesis-robotics.tech/)
- **最低配置**：Ubuntu 20.04, Python 3.10, 6GB VRAM, GTX 1080 同等算力 [来源](https://github.com/Genesis-Embodied-AI/Genesis) [来源](https://docs.genesis-robotics.tech/)
- **推荐配置**：RTX 4090 24GB [来源](https://github.com/Genesis-Embodied-AI/Genesis)
- **性能对比**：Genesis 比 Isaac Gym 快 10-80x（第三方测试：430万 FPS vs 3.8万 FPS）[来源](https://www.robotChat.com/) [来源](https://www.geeksnewslab.com/)

**结论**：文档说比 Isaac Gym 快 10-80x 完全准确。RTX 2060 6GB 满足最低配置，可以运行（但可能受限）。

---

## Claim 9：RTX 5050 中国价格

**文档声称**：~2000元

**验证结果**：✅ **基本准确**

**实际数据**：
- **官方建议零售价**：**2,099 元人民币** 起 [来源](https://www.expreview.com/) [来源](https://videocardz.net/)
- **海外实际市场售价**：$289.99 美元（约 2,100 元人民币）[来源](https://videocardz.net/)
- **主要规格**：2560 CUDA核心，8GB GDDR6（128-bit），130W功耗，DLSS 4 [来源](https://www.expreview.com/) [来源](https://videocardz.net/)

**结论**：文档说"~2000元"完全准确，实际是 2,099 元起。

---

## Claim 10：AMD AI Halo 128GB 中国售价

**文档声称**：~10,000-15,000元（AMD尚未公布价格）

**验证结果**：⚠️ **有出入**

**实际数据**：
- **官方定价状态**：AMD 尚未公布 Ryzen AI Halo 迷你主机的零售价格（计划 2026 Q2 上市）[来源](https://www.anandtech.com/) [来源](https://www.techpowerup.com/)
- **实际市场参考**：abee AI Station 395 Max（搭载同款 锐龙AI Max+ 395 + 128GB）已在京东开售，售价 **17,999 元人民币** [来源](https://www.abee.com/) [来源](https://www.jd.com/)
- **处理器单独参考价**：锐龙AI Max+ 395 在二手平台约 3,998 元 [来源](https://www.goofish.com/)

**结论**：文档说AMD未公布价格是正确的。但实际已有搭载同芯片的整机在售（17,999元），比文档预测的10,000-15,000元上限更高。建议更新文档标注"整机参考价约18,000元"。

---

## 汇总

| # | Claim | 验证结论 |
|---|-------|----------|
| 1 | DGX Spark 价格 $699/35,000元 | ❌ 错误 |
| 2 | DGX Station ~70万，748GB，20 PFLOPS | ⚠️ 规格准确，价格错误 |
| 3 | BearPi H3863 40针GPIO | ⚠️ 只有17个GPIO |
| 4 | Hi3863 无MMU，4MB Flash，无法跑Linux | ✅ 准确 |
| 5 | Genesis 2026-03-21 有更新 | ⚠️ 实际最新是 2026-02-17 v0.4.0 |
| 6 | PCIe 5.0 高带宽 | ✅ 准确 |
| 7 | Apple M5 153GB/s 带宽 | ✅ 准确 |
| 8 | Genesis 在 RTX 2060 6GB 上能跑 | ✅ 准确 |
| 9 | RTX 5050 ~2000元 | ✅ 准确（2099元起） |
| 10 | AMD AI Halo 128GB ~10,000-15,000元 | ⚠️ 有整机参考价17,999元 |
