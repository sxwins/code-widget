# CodeWidget

[English](../README.md) | **[日本語]**

UNIPA などの LMS を利用する大学教員向けの、出席コード管理・表示デスクトップツールです。
授業中の手動操作なしに、出席コードを自動表示します。

## 概要

CodeWidget は授業時間中にデスクトップへフローティングウィンドウを表示し、
学生が LMS（学習管理システム）への出席登録に使用する 4 桁の出席コードをランダム生成して表示します。

ウィンドウは各コマの開始時刻に自動表示され、終了後に自動的に消えます。
授業中の手動操作は不要です。

![CodeWidget 表示例](time_slot.png)

## 主な機能

- **スケジュール自動追跡** — 時間割を読み込み、補講・振替を含む正しいコードを正しい時間に表示
- **コマ別出席コード** — 各授業回に固有の出席コードを事前割当；いつでも編集・一括生成可能
- **フローティングオーバーレイ** — 常に最前面に表示されるコンパクトなウィンドウ；位置は再起動後も保持
- **設定ダイアログ** — コース管理、学期スケジュールのプレビュー、日程調整の追加、外観カスタマイズをすべて GUI で操作
- **複数教員設定対応** — 教員ごとに独立した JSON ファイルを使用；ワンクリックで切替可能
- **外観カスタマイズ** — フォント・色・ウィンドウサイズを `settings.json` にグローバル保存（教員データとは独立）

## 動作環境

- Windows 10 / 11
- macOS 12 Monterey 以降

## はじめに

**Windows**

1. [Releases](../../releases) から `CodeWidget.exe` をダウンロード
2. 任意のフォルダに配置 — 初回起動時に `config/` サブフォルダが自動作成されます
3. 設定ダイアログ（トレイアイコン → **設定**）を開いてコースを登録

**macOS**

1. [Releases](../../releases) から `CodeWidget.app.zip` をダウンロードして解凍
2. **CodeWidget.app** を Applications フォルダへドラッグ
3. 初回起動時は右クリック → **開く** で Gatekeeper の警告を回避
4. 設定ダイアログ（メニューバーアイコン → **設定**）を開いてコースを登録

## 設定ファイル

| ファイル | 用途 |
|----------|------|
| `config/settings.json` | グローバル外観設定および使用する教員設定ファイルのパス |
| `config/teacher_config.json` | デフォルトの空教員テンプレート |
| `config/school_config.json` | 学校カレンダー：学期日程・休日・時限時刻 |

すべてプレーン JSON 形式です。手動編集や年度更新が可能です。

## ソースからビルド

### Windows EXE

本プロジェクトの開発環境は Docker（Linux）で、ホスト Windows とワーキングディレクトリを共有しています。
Docker 側の `.venv` を上書きしないよう、パッケージング時は独立した `.venv-win` 環境を使用します。

Windows PowerShell でプロジェクトディレクトリから実行してください：

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
uv sync --dev
uv run pyinstaller CodeWidget.spec --clean
# 出力：dist/CodeWidget.exe
```

> `$env:UV_PROJECT_ENVIRONMENT` は現在の PowerShell セッションのみ有効で、
> 他のプロジェクトや Docker 環境には影響しません。

### macOS アプリバンドル

Mac 上で実行してください（Xcode Command Line Tools が必要です）：

```bash
# 前提条件：Python 3.12、uv
uv sync --dev
uv run pyinstaller CodeWidget.spec --clean
# 出力：dist/CodeWidget.app
# 配布用に圧縮：zip -r CodeWidget.app.zip dist/CodeWidget.app
```

### テストの実行

```bash
uv run pytest -v
```

## ライセンス

[MIT](../LICENSE)

> 本ソフトウェアは [PySide6](https://doc.qt.io/qtforpython/) を使用しています。
> PySide6 は [LGPL v3](https://www.gnu.org/licenses/lgpl-3.0.html) に基づきライセンスされています。
> 詳細は [NOTICE](../NOTICE) をご参照ください。
