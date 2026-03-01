# CodeWidget — Claude Code 项目配置

## 项目简介

出勤码展示工具（CodeWidget）— 教师课堂出勤码展示桌面应用。
Python 3.12 + PySide6 + UV 包管理器。

## 工作目录

所有命令在 `C:/Temp/Claude/CodeWidget` 下执行。无需 `cd` 或 `-C` 前缀。

## 常用命令（自动允许，无需确认）

```bash
# 测试
uv run pytest -v
uv run pytest tests/<file> -v

# Git（只读）
git status
git log --oneline -10
git diff
git diff <sha1>..<sha2>
git diff --stat

# Git（写入）
git add <file>
git commit -m "..."
```

## 技术栈

- Python 3.12.10
- PySide6 6.10.2（LGPL v3）
- UV 包管理器（使用 `uv run`，不直接用 `pip`）
- pytest + pytest-qt

## 代码规范

- Conventional Commits（feat/fix/docs/chore/test/refactor）
- 测试目录：`tests/`，`pythonpath = ["src"]` 已在 pyproject.toml 配置
- 不要 `git push`（无远程仓库）
