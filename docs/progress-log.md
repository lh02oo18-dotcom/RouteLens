# 渐进式实施记录

## 2026-10-11：开源基线接入

### 本轮目标

选择与方案接近的开源底座，在目标电脑上跑通检测、跟踪、导出和 Web 界面，并建立后续创新的清晰边界。

### 完成内容

- 选择 `Youssef-Azzam/Crowd_Counter@126f5c5` 作为底座。
- 创建 `feature/routelens-baseline` 分支。
- 建立 Python 3.12 虚拟环境并安装 CUDA 版 PyTorch。
- 验证 RTX 4060、YOLO11n、ByteTrack、CSV/JSON/MP4 导出和 Streamlit。
- 把自动发现的 `lap` 运行依赖显式写入 requirements。
- 将 Ultralytics 和 Pytest 的运行目录移到项目内 `.runtime`，规避 Windows 用户目录权限问题。
- 建立 RouteLens README、复用决策、路线图、评分矩阵和 GitHub 协作配置。
- 创建公开仓库，并按配置、核心流水线、跟踪器、文档、测试和工具拆分提交。
- 创建功能 Issue #1 与基线 Pull Request #2，由 GitHub Actions 验证 Python 3.10/3.12。

### 遇到的问题与解决

1. Git HTTPS 后端无法加载：改用系统 Git 并指定 OpenSSL 后端完成克隆。
2. Ultralytics 尝试写入用户配置目录：通过 `YOLO_CONFIG_DIR` 使用项目本地运行目录。
3. ByteTrack 首次运行自动安装 `lap`：将其加入 requirements，避免其他机器首次运行产生隐式变更。
4. Pytest 偶发无法访问 AppData 临时目录：在 `pyproject.toml` 中固定项目本地临时目录和缓存。

### 验证结果

- 8 项单元测试通过。
- Ruff 通过。
- `pip check` 无依赖冲突。
- Streamlit 健康端点返回 HTTP 200。
- 30 帧 GPU 冒烟测试识别 4 个轨迹 ID，并生成完整输出。

### 当前阶段

- 公开仓库、Issue、Pull Request 和 Actions 记录已经建立。
- `v0.1.0` 将在 PR 检查通过并合并后发布。
- RouteLens 轨迹特征、异常检测和证据卡已记录在 Issue #1，属于后续迭代。
