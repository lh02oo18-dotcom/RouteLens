# CAVIAR 真实数据实验结果

## 结论摘要

RouteLens 在 CAVIAR 官方实拍视频上完成了可复现的小样本验证。Walk1 仅用于固定图像尺寸和置信度阈值，Browse1 与 Browse_WhileWaiting2 作为独立测试集。测试集中共有 2,940 个视频帧、2,118 个有标注帧和 3,312 个人工框。

在相同的 960 像素输入尺寸、0.05 置信度阈值和 IoU=0.50 评价条件下，YOLO11s + BoT-SORT 获得最高框级匹配 F1（0.3958），YOLO11s + ByteTrack 为 0.3880。两者都高于对应的 YOLO11n 组合，视频处理循环吞吐量均超过 60 FPS。YOLO11s + BoT-SORT 的框级匹配 F1 相比 YOLO11n + BoT-SORT 提高 0.0947，约为 31.5% 的相对提升。

两段测试视频包含 2 个由 CAVIAR `role=browser` 或 `situation=browsing` 标签构造的参考徘徊区间，但四种模型/跟踪器组合均未产生徘徊预测，事件 F1 为 0。这个结果说明当前几何徘徊规则与官方“浏览”语义并不等价，而且漏检与轨迹碎片化会进一步削弱事件触发；因此本实验不支持“真实场景徘徊检测有效”的结论。

## 数据与划分

- 数据源：CAVIAR Test Case Scenarios，官方页面声明为实拍、人工标注并采用 CC BY-SA。
- 调参序列：Walk1，594 个有标注帧、1,559 个人工框。
- 独立测试序列：Browse1、Browse_WhileWaiting2。
- 原始数据不提交 Git；下载地址、文件大小和 SHA-256 记录在 `caviar-pilot-manifest.csv`。
- 评价仅针对 XML 中存在标注的帧，避免把未标注帧错误计为假阳性。

## 冻结参数

先在 Walk1 上调参：YOLO11n 比较输入尺寸 640/960 与置信度 0.05/0.10/0.15/0.25；YOLO11s 在 960 输入尺寸下比较同一组四个置信度。两种模型都选择 960 与 0.05，再冻结参数运行两个独立测试序列。跟踪器对比为 ByteTrack 与 BoT-SORT；不在测试集上重新调参。

## 聚合结果

| 模型 | 跟踪器 | Precision | Recall | F1 | 平均 IoU | 质心 RMSE/px | 轨迹覆盖率 | ID 切换 | FPS | 事件 F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| YOLO11n | ByteTrack | 0.7839 | 0.1818 | 0.2951 | 0.8466 | 2.0795 | 0.1665 | 7 | 75.24 | 0.0000 |
| YOLO11n | BoT-SORT | 0.7908 | 0.1860 | 0.3011 | 0.8827 | 2.3447 | 0.1734 | 7 | 67.62 | 0.0000 |
| YOLO11s | ByteTrack | 0.7020 | 0.2681 | 0.3880 | 0.8398 | 3.0193 | 0.2869 | 6 | 66.73 | 0.0000 |
| YOLO11s | BoT-SORT | 0.7177 | 0.2732 | **0.3958** | 0.8713 | 3.1907 | **0.2930** | **5** | 61.58 | 0.0000 |

框级指标按人工框总量汇总。每段视频先对参考轨迹计算宏平均覆盖率，表中再对两个序列等权平均。FPS 为视频读取、检测、跟踪和逐帧评价循环的处理帧数除以循环运行时间，不含后续聚合、绘图与文件导出；每种配置只运行一次，因此不报告置信区间。不同硬件上的 FPS 不应直接与本表比较。

## 分序列结果

| 序列 | YOLO11n + ByteTrack | YOLO11n + BoT-SORT | YOLO11s + ByteTrack | YOLO11s + BoT-SORT |
|---|---:|---:|---:|---:|
| Browse1 F1 | 0.3532 | 0.3570 | 0.4141 | **0.4276** |
| Browse_WhileWaiting2 F1 | 0.1495 | 0.1621 | **0.3431** | 0.3409 |

Browse_WhileWaiting2 上模型提升最明显，但两段视频的最优跟踪器不同，说明仅凭两个序列不能断言某一跟踪器普遍更优。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -m tools.download_caviar_pilot

.\.venv\Scripts\python.exe -m tools.calibrate_caviar `
  --sequence Walk1 --model yolo11s.pt --device 0 `
  --image-sizes 960 `
  --output results\caviar-v1.1\calibration_yolo11s.csv

.\.venv\Scripts\python.exe -m tools.run_caviar_experiment `
  --model yolo11s.pt --confidence 0.05 --image-size 960 `
  --trackers bytetrack botsort `
  --sequences Browse1 Browse_WhileWaiting2 `
  --device 0 --output-dir results\caviar-v1.1\heldout-yolo11s

.\.venv\Scripts\python.exe -m tools.plot_caviar_results
```

CPU 机器可把 `--device 0` 改为 `--device cpu`。模型权重、原始 MPEG 和 XML 不纳入 Git；提交的 CSV、JSON、绘图脚本与校验清单足以审计参数、环境和结果。

## 结论边界

1. 数据年代较早、分辨率仅 384×288，且场景行为经过编排，不能代表开放世界监控分布。
2. 仅有一个调参序列和两个测试序列，结果用于小样本可运行性和比较验证，不支持统计推广。
3. CAVIAR “browser/browsing” 标签描述行为语义，而 RouteLens 徘徊规则依赖时长、活动半径和路径长度；二者只作为可审计的近似映射。
4. 评价使用逐帧贪心 IoU 匹配，不等同于完整 MOTChallenge 评测协议。
5. 当前最明确的实验证据是：真实数据评价链路可复现、YOLO11s 提高了召回与框级匹配 F1、四种配置的视频处理循环吞吐量均高于 25 FPS 源帧率；事件层仍需重新定义标签映射并改善轨迹连续性。
