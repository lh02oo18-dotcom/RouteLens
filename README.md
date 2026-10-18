# RouteLens：可解释人群轨迹分析系统

RouteLens 是一个本地运行的可解释人群轨迹分析项目。项目复用开源 Crowd Counter 的 YOLO 人员检测、目标跟踪、越线计数和导出接口，并在此基础上逐步加入轨迹特征、路线聚类、逆行/徘徊/偏离检测及可解释异常证据卡。

> 当前版本：`0.3.0`。检测、跟踪、计数和轨迹导出复用开源底座；RouteLens 已新增轨迹特征、持续逆行与徘徊规则、DBSCAN 主路线聚类、偏离评分和可复现评价入口。项目不会把上游已有功能标记为本项目创新。

## 功能状态

| 能力 | 状态 | 来源/计划 |
|---|---|---|
| YOLO 人员检测 | 已跑通 | 复用上游接口 |
| ByteTrack、BoT-SORT、CSRT 跟踪 | 已跑通 | 复用上游接口 |
| 越线、占用、停留和轨迹导出 | 已跑通 | 复用上游接口 |
| Streamlit 与 CLI | 已跑通 | 复用并重新组织 |
| 轨迹速度、方向、转向角、路径和活动半径 | 已实现 | RouteLens 迭代 1 |
| DBSCAN 主路线聚类与偏离检测 | 已实现 | RouteLens 迭代 2 |
| 持续逆行与徘徊事件 | 已实现 | RouteLens 迭代 1 |
| 异常证据卡与结果解释 | 待实现 | RouteLens 迭代 3 |

## 设计亮点与差异化

上游项目回答“画面里有多少人、是否越线”；RouteLens 进一步回答“人沿什么路线移动、行为为什么被判为异常、证据在哪里”。计划采用分层结构：

```text
视频/摄像头
  -> YOLO 检测（复用）
  -> 多目标跟踪（复用）
  -> 统一轨迹记录（扩展接口）
  -> 轨迹重采样、路线聚类与偏离评分（新增）
  -> 规则 + 数据驱动异常检测（新增）
  -> 证据卡、表格、视频与 JSON（新增/扩展）
```

详细复用边界见 `docs/decisions/0001-upstream-reuse.md`，质量检查清单见 `docs/project-quality.md`。

## 环境要求

- Windows 10/11、Linux 或 macOS
- Python 3.10–3.12
- 16 GB 内存建议值
- CPU 可以运行；NVIDIA GPU + CUDA PyTorch 可明显加速
- 首次运行会下载约 5.4 MB 的 `yolo11n.pt`

已验证环境：Python 3.12.4、RTX 4060 Laptop 8 GB、PyTorch 2.14.1+cu126。

## Windows 快速开始

```powershell
git clone https://github.com/lh02oo18-dotcom/RouteLens.git
cd RouteLens
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

打开 `http://localhost:8501`，上传 MP4/AVI/MOV/MKV 视频，选择模型和跟踪器，再点击 **Run analysis**。

NVIDIA GPU 用户需要按本机 CUDA 环境安装合适的 PyTorch。CPU 环境无需这一步，配置中的设备留空即可。

## 可复现实验命令

```powershell
.\.venv\Scripts\python.exe CLI.py `
  --source data\videos\example.mp4 `
  --tracker bytetrack `
  --model yolo11n.pt `
  --device 0 `
  --output-dir outputs\example `
  --save-video
```

主要输出：

- `frame_metrics.csv`：逐帧人数、占用、FPS 和延迟
- `crossing_events.csv`：越线事件
- `trajectories.csv`：轨迹点、时间、边界框和置信度
- `trajectory_features.csv`：速度、方向、路径长度、位移比、转向角和活动半径
- `route_assignments.csv`：轨迹所属路线、噪声标记、最近主路线和偏离分数
- `route_prototypes.csv`：每个主路线簇的重采样原型点
- `route_summary.json`：聚类状态、参数、样本计数和安全规则
- `anomaly_events.csv` / `anomaly_events.json`：异常类型、轨迹 ID、时间段、指标、阈值和证据引用
- `summary.json`：会话汇总
- `annotated_output.mp4`：可选标注视频

## 配置与接口

默认配置位于 `config/default.yaml`。核心模块：

- `people_counter/detector.py`：人员检测适配器
- `people_counter/trackers/`：跟踪后端
- `people_counter/analytics.py`：现有统计逻辑及后续扩展入口
- `people_counter/trajectory_analysis.py`：轨迹特征和规则异常
- `people_counter/route_mining.py`：重采样、DBSCAN、路线原型和偏离评分
- `people_counter/evaluation.py`：事件级匹配及精确率、召回率和 F1
- `people_counter/schema.py`：跨模块数据结构
- `people_counter/exporters.py`：结果导出
- `people_counter/counter.py`：主处理流水线
- `app.py`、`CLI.py`：交互与可复现实验入口

轨迹规则见 `docs/iteration-1.md`，路线挖掘参数、实验入口和风险边界见 `docs/iteration-2.md`。扩展时优先增加数据结构、纯计算模块和单元测试，再接入主流水线，避免算法与界面耦合。

## 路线挖掘与评价

系统先按行进距离把每条轨迹重采样为 16 个点，再用同一场景边界归一化，通过 DBSCAN 发现重复出现的主路线。偏离分数是轨迹与最近路线原型的归一化均方根距离。若样本不足或没有形成受支持的路线簇，系统不会产生路线偏离事件。

运行不依赖视频的合成参数对比：

```powershell
.\.venv\Scripts\python.exe -m tools.route_mining_demo `
  --output-dir outputs\route_mining_demo
```

用人工标注 JSON 评价真实预测：

```powershell
.\.venv\Scripts\python.exe -m tools.evaluate_events `
  --predictions outputs\anomaly_events.json `
  --references data\annotations\events.json
```

合成实验只验证计算链路和阈值变化，不作为真实准确率。真实视频结论必须使用独立人工标注集。

## 测试与质量检查

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

GitHub Actions 会在 push 和 Pull Request 时执行依赖检查、Ruff 与 Pytest。迭代 2 本机结果为 21 项测试通过。

## 迭代和版本

- `v0.1.0`：本机可运行基线、文档与仓库规范
- `v0.2.0`：轨迹特征、持续逆行、徘徊检测和异常列表
- `v0.3.0`：DBSCAN 路线聚类、偏离检测和实验评估
- `v1.0.0`：证据卡、完整演示数据和稳定 Release

具体任务拆分见 `docs/roadmap.md`，已知问题见 `docs/known-issues.md`，版本变化见 `CHANGELOG.md`。

## 贡献与协作

请先用 Issue 描述问题、验收条件和复现素材，再从功能分支提交 Pull Request。提交信息采用 `feat:`、`fix:`、`docs:`、`test:`、`chore:` 等前缀。完整流程见 `CONTRIBUTING.md`。

## 开源来源与许可

本项目基于 [Youssef-Azzam/Crowd_Counter](https://github.com/Youssef-Azzam/Crowd_Counter) 的 MIT 许可代码继续开发；原作者版权声明保留在 `LICENSE` 中，具体复用关系记录在 `NOTICE.md`。本仓库代码沿用 MIT License。Ultralytics 等第三方组件适用其各自许可证，公开发布或部署前应分别核对。

## 当前限制

- 密集遮挡、低照度、抖动镜头会降低检测和跟踪稳定性。
- 冒烟测试使用重复静态图像，只验证主路径，不代表真实性能或异常检测精度。
- 暂未建立真实视频标注集；当前路线挖掘仅完成合成链路验证，不代表已经验证的真实精度。
- 当前 DBSCAN 距离矩阵为 O(n²)，适合课程演示和小型离线数据，不适合直接处理超大规模轨迹库。
