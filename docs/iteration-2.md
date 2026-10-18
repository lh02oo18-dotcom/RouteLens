# 迭代 2：主路线聚类与偏离评分

## 目标与边界

本轮将检测与跟踪得到的轨迹转换为可比较向量，自动发现主要通行路线，并对远离主路线的轨迹给出可解释分数。它复用上游轨迹记录接口，不改动 YOLO、ByteTrack、BoT-SORT 或 CSRT。

本版本完成算法、接口、导出、单元测试和合成参数实验。由于仓库中没有可合法公开且已人工标注的真实视频，本版本不声称真实准确率。

## 计算流程

1. 按 `track_id` 分组并按时间、帧号排序。
2. 排除少于 `route_min_points` 个点的轨迹和零路径长度轨迹。
3. 按累计行进距离等间隔重采样为 `route_resample_points` 个点。
4. 使用本次会话所有有效轨迹的共享边界，把坐标缩放到场景归一化空间。
5. 以逐点欧氏距离的均方根作为轨迹距离，使用 DBSCAN 形成主路线簇。
6. 对每个簇求平均轨迹原型；计算每条轨迹到所属或最近原型的偏离分数。
7. 仅在至少存在一个受支持路线簇且分数达到阈值时生成 `route_deviation` 事件。

## 默认参数

| 参数 | 默认值 | 含义 |
|---|---:|---|
| `route_min_points` | 5 | 进入挖掘的最少轨迹点数 |
| `route_resample_points` | 16 | 每条轨迹的重采样点数 |
| `route_dbscan_eps` | 0.08 | 归一化空间中的邻域半径 |
| `route_dbscan_min_samples` | 3 | 形成路线簇的最少轨迹数 |
| `route_deviation_threshold` | 0.12 | 产生偏离事件的最小分数 |

这些参数是可运行默认值，不是跨场景通用最优值。真实场景必须用独立标注集选参，不能同时用测试集调参和报告结果。

## 输出接口

- `route_assignments.csv`：轨迹簇、噪声标记、最近簇、偏离分数、阈值和结论。
- `route_prototypes.csv`：各簇原型的归一化坐标和回映射像素坐标。
- `route_summary.json`：状态、参数、有效轨迹数、静止轨迹数、簇数和偏离事件数。
- `anomaly_events.csv/json`：新增 `route_deviation` 事件，保留时间、帧号、指标、阈值和证据引用。

## 可复现的合成参数实验

```powershell
.\.venv\Scripts\python.exe -m tools.route_mining_demo `
  --output-dir outputs\route_mining_demo
```

脚本生成 5 条主路线邻近轨迹、1 条中等偏移轨迹和 1 条人工标记偏离轨迹，并扫描 4 个 DBSCAN 半径与 3 个偏离阈值。输出 `parameter_sweep.csv` 记录每组参数的簇数、噪声数、TP、FP、FN、Precision、Recall 和 F1。`metadata.json` 明确标记数据为 `synthetic_demonstration_only`。

## 真实数据评价协议

1. 选取固定机位且允许用于课程展示的视频，划分调参集与独立测试集。
2. 两人独立标注事件类型、轨迹 ID、开始时间和结束时间，再解决分歧。
3. 在调参集确定聚类半径与偏离阈值，冻结配置后运行测试集。
4. 使用 `tools.evaluate_events` 按事件类型、轨迹 ID 和时间交并比进行一对一匹配。
5. 报告 TP、FP、FN、Precision、Recall、F1，并单独记录 ID 切换、遮挡和不完整轨迹失败案例。

## 已知限制

- 共享边界归一化适合同一固定场景，不应直接比较不同摄像机的分数。
- DBSCAN 距离矩阵为 O(n²)，面向课程演示和小型离线批次。
- 跟踪 ID 切换会把一条真实路线拆成多条短轨迹。
- 没有主路线簇时系统选择“不判定”，这是减少误报的安全策略，不等于场景没有异常。
