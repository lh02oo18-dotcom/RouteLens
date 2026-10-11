# 参与 RouteLens 开发

## 工作流

1. 先创建或认领 Issue，写清问题、范围、验收标准和可公开的复现素材。
2. 从最新 `main` 创建短生命周期分支：`feat/<name>`、`fix/<name>`、`docs/<name>`。
3. 小步提交，提交信息使用 Conventional Commits，例如 `feat: add trajectory features`。
4. 推送分支并创建 Pull Request，关联 Issue，填写验证结果和界面变化。
5. CI 通过且评审意见解决后再合并；不要直接推送到受保护的 `main`。

## 本地环境

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## 提交前检查

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

影响 Streamlit、CLI 或视频处理主路径的修改，还要使用短视频完成一次冒烟测试。

## 代码与文档要求

- 不提交模型权重、原始视频、输出视频、缓存、虚拟环境、密钥或私有摄像头地址。
- 算法逻辑与 Streamlit 界面分离，优先编写可独立测试的函数或类。
- 新配置必须同步修改 `config/default.yaml` 和 README。
- 新事件字段必须更新 schema、导出器、接口示例和测试。
- 算法 PR 必须说明数据、指标、阈值、失败案例和已知限制。
- 准确区分上游复用、工程改造和 RouteLens 创新。

## Pull Request 最小内容

- 关联 Issue：`Closes #编号`
- 修改目的和非目标
- 复用接口与新增接口
- 自动测试与人工验证结果
- 界面变化截图或无界面变化说明
- 风险、兼容性和回退方法
