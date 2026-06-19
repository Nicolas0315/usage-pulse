# model-advisor: 使用量ベースのモデル選択補助

このスキルは usage-pulse の handshake ファイルを読み、現在の AI ツール使用量に基づいてモデル選択を推奨します。

## 前提条件

- `usage-pulse` がインストールされていること
- `usage-pulse sync` が定期的に実行されていること（Claude Code hook で自動化推奨）

## 使用方法

タスク開始時や長いセッションの途中でこのスキルを呼び出すと、現在の使用量状況に応じたモデル推奨が得られます。

## スキルの動作

1. `~/.local/state/usage-pulse/current.json` を読み込む
2. 使用量・レートウィンドウ・コストを確認する
3. 現在の状況に最適なモデルを推奨する
4. 緊急度に応じてアラートを表示する

## 判断基準

| 状況 | 推奨モデル | 緊急度 |
|------|-----------|--------|
| 5分レート ≥ 90% | claude-haiku-4-5 | 🔴 critical |
| 5分レート ≥ 80% | claude-haiku-4-5 | 🟠 warning |
| 5分レート ≥ 50% | claude-sonnet-4-6 | ⚠️ caution |
| 日コスト ≥ 90% of threshold | claude-haiku-4-5 | 🟠 warning |
| 日コスト ≥ 70% of threshold | claude-sonnet-4-6 | ⚠️ caution |
| 週次レート ≥ 80% | claude-sonnet-4-6 | ⚠️ caution |
| 正常 | claude-sonnet-4-6 | ✅ ok |

## 実装

```python
# このスキルを呼び出す際の実装例
import json
from pathlib import Path

state_file = Path.home() / ".local/state/usage-pulse/current.json"

if state_file.exists():
    state = json.loads(state_file.read_text())
    rec = state.get("recommendation", {})
    print(f"推奨モデル: {rec.get('model')}")
    print(f"理由: {rec.get('reason')}")
    print(f"緊急度: {rec.get('urgency')}")
else:
    print("状態ファイルが見つかりません。usage-pulse sync を実行してください。")
```

## 手動実行

```bash
usage-pulse summary     # 今日の使用量サマリー
usage-pulse summary --json  # 機械可読サマリー
usage-pulse doctor      # ローカル診断
usage-pulse roi         # モデル別 ROI テーブル
cat ~/.local/state/usage-pulse/current.json  # 生の状態データ
```
