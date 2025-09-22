# 簡単に使えるタスク管理アプリケーション

このリポジトリは、コマンドラインで手軽に利用できるタスク管理ツールです。Python の標準ライブラリのみで構成されており、インストール作業を最小限に抑えています。

## 主な特徴

- **シンプルな操作**: `python -m task_manager` コマンドでタスクの追加・一覧・更新・完了・削除を行えます。
- **ファイル保存**: タスクは JSON 形式で保存されるため、バックアップや他ツールとの連携が容易です。
- **柔軟な表示**: 未完了タスクのみの表示や詳細情報の確認に対応しています。
- **日本語メッセージ**: すべての CLI メッセージを日本語化し、直感的に利用できます。

## セットアップ

Python 3.11 以上がインストールされていれば追加ライブラリは不要です。ソースコードを取得後、そのまま利用できます。

```
python -m venv .venv
source .venv/bin/activate  # Windows の場合は .venv\Scripts\activate
pip install --upgrade pip
pip install pytest  # テストを実行したい場合
```

## 使い方

### タスクの追加

```
python -m task_manager add "レポート作成" --description "図表を更新" --due-date 2024-12-01 --priority high
```

### タスクの一覧表示

```
python -m task_manager list            # すべてのタスク
python -m task_manager list --status pending   # 未完了のみ
python -m task_manager list --detailed         # 詳細情報表示
```

### タスクの更新・完了・削除

```
python -m task_manager update 1 --title "企画書作成" --due-date 2024-11-20
python -m task_manager complete 1      # 完了にする
python -m task_manager complete 1 --undo  # 完了を取り消す
python -m task_manager delete 1        # 削除
```

## 保存先の変更

既定では `~/.simple_task_manager/tasks.json` に保存されます。環境変数 `TASK_MANAGER_DB` もしくは `--database` オプションで保存先を変更できます。

```
export TASK_MANAGER_DB=/path/to/tasks.json
python -m task_manager list
```

## テスト

pytest を利用してロジックのテストを行えます。

```
pytest
```

## ライセンス

このプロジェクトは MIT ライセンスで公開されています。
