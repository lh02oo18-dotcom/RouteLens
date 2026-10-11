# RouteLens GitHub 发布清单

公开仓库已经创建：`https://github.com/lh02oo18-dotcom/RouteLens`。原作者仓库保留为只读 `upstream`，RouteLens 仓库使用 `origin`。不要向原作者仓库推送修改。

## 1. 公开仓库

仓库使用公开可见性，创建时未自动生成 README、LICENSE 或 `.gitignore`，因此不会与本地文件冲突。

## 2. 保留上游并设置个人远程

远程配置应为：

```powershell
git remote rename origin upstream
git remote add origin https://github.com/lh02oo18-dotcom/RouteLens.git
git remote -v
```

推送前用 `git remote -v` 确认两个地址没有写反。

## 3. 首次推送和 Pull Request

```powershell
git push -u origin feature/routelens-baseline
```

在 GitHub 创建从 `feature/routelens-baseline` 到 `main` 的 Pull Request，填写模板并关联基线 Issue。CI 通过后合并。

## 4. 仓库设置

- 启用 Issues 和 Discussions。
- 为 `main` 设置分支保护：必须通过 Pull Request 和 CI。
- 启用 Dependency graph、Dependabot alerts 和 private vulnerability reporting。
- 禁止强制推送和删除受保护分支。

## 5. 首个 Release

合并基线 PR 后创建带注释标签 `v0.1.0`，再从标签发布 GitHub Release。Release Notes 应包括运行环境、复用来源、已实现功能、验证结果和已知问题。

发布前确认：

- README 中的 clone 地址已替换为真实公开仓库地址。
- Actions 在 Python 3.10 和 3.12 上通过。
- LICENSE、NOTICE、CHANGELOG、CONTRIBUTING 和 SECURITY 可访问。
- 至少一个 Issue 与一个已合并 PR 构成可追溯记录。
- 模型、视频、输出、密钥和本地配置未进入提交。
