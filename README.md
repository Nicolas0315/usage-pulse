# usage-pulse

**Mac / Windows / Linux 対応 AI ツール使用量モニター**

tmux ステータスライン・OS ネイティブシステムトレイ・通知・モデル選択補助を統合した OSS ツール。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 概要

| 機能 | Mac | Windows | Linux |
|------|-----|---------|-------|
| tmux ステータスライン | ✅ | ✅ (WSL2) | ✅ |
| システムトレイ | ✅ | ✅ | ✅ |
| デスクトップ通知 | ✅ osascript | ✅ PowerShell | ✅ notify-send |
| codexbar 連携 | ✅ (TTY あり) | ❌ | ❌ |
| Claude Code フック | ✅ | ✅ | ✅ |
| モデル選択 Skill | ✅ | ✅ | ✅ |

---

## インストール

### 前提条件

- Python 3.11+
- [ccusage](https://github.com/ryoppippi/ccusage) (`bun add -g ccusage`)
- [codexbar](https://codexbar.app/) (macOS のみ・オプション)
- tmux 3.0+

### uv でインストール（推奨）

```bash
git clone https://github.com/<your-org>/usage-pulse ~/work/usage-pulse
cd ~/work/usage-pulse
uv sync
```

### tmux ステータスライン

```bash
./scripts/install-tmux.sh
```

### Claude Code フック統合

```bash
./scripts/install-claude-hook.sh
```

---

## コマンド

```bash
# tmux ステータスライン文字列を出力（キャッシュあり）
usage-pulse statusline

# システムトレイデーモン起動
usage-pulse tray

# 今日の使用量サマリー表示
usage-pulse summary

# モデル別トークン ROI 表示
usage-pulse roi

# 使用量状態ファイルを更新（エージェントハンドシェイク）
usage-pulse sync

# 設定補助（インタラクティブ）
usage-pulse setup
```

---

## モデル選択 Skill

Claude Code に Skill として組み込むことで、現在の使用量に基づくモデル選択補助が使えます。

```bash
# Skill をインストール
./scripts/install-skill.sh
```

インストール後、Claude Code で `/model-advisor` を実行するとリアルタイムの使用量とコスト予測に基づいたモデル推奨が得られます。

---

## アーキテクチャ

```
usage-pulse
├── providers/          データ取得層
│   ├── ccusage.py      ccusage daily --json (全 OS 共通)
│   └── codexbar.py     codexbar usage --json (Mac TTY あり時のみ)
├── display/            表示層
│   ├── tmux.py         tmux status-right 文字列
│   ├── tray.py         pystray システムトレイ (Win/Linux)
│   └── notify.py       OS 別デスクトップ通知
├── analysis/           分析層
│   ├── roi.py          モデル別トークン ROI
│   └── advisor.py      使用量ベースモデル選択推奨
└── handshake.py        エージェント向け状態ファイル出力
```

### バッテリー効率設計

- SQLite 直読みによる ccusage CLI 起動ゼロ（`~/.claude/` / `~/.codex/` を直接クエリ）
- ファイル変更監視 (`inotify`/`kqueue`/`ReadDirectoryChangesW`) でポーリングを廃止
- キャッシュ TTL はアクティブ使用中 30 秒、アイドル時 5 分に自動切替

---

## エージェントハンドシェイク

`usage-pulse sync` は `~/.local/state/usage-pulse/current.json` を更新します。  
AI エージェントはこのファイルを読んで現在の使用量状況を把握できます。

```json
{
  "updated_at": "2026-06-19T10:00:00Z",
  "today": {
    "cost_usd": 12.50,
    "tokens": 2200000,
    "top_models": ["claude-sonnet-4-6", "gpt-5.5"]
  },
  "rate_windows": {
    "claude_5min_pct": 22,
    "claude_weekly_pct": 35
  },
  "recommendation": {
    "model": "claude-haiku-4-5",
    "reason": "claude_5min_pct=22% — sonnet/opus は残量十分"
  }
}
```

---

## アップデート体制

各プロバイダーの仕様変更を追いかけるための仕組みを用意しています。

- `providers/VERSION_PINS.json`: 各ツールの対応バージョンを記録
- `scripts/check-provider-updates.sh`: ccusage/codexbar の最新版とスキーマ変更を確認
- GitHub Actions: 週次で各プロバイダーの CHANGELOG を確認し差分を Issue 登録

---

## 参考・謝辞

このプロジェクトは以下のツールのコンセプトとデータソース設計から多くを学んでいます:

- **[ccusage](https://github.com/ryoppippi/ccusage)** by ryoppippi — Claude Code / Codex CLI の使用量を集計する OSS ツール。MIT License。usage-pulse の ccusage プロバイダーは `ccusage daily --json` API を利用しています。
- **[CodexBar](https://codexbar.app/)** by steipete — macOS メニューバー向け Codex/Claude 使用量モニター。usage-pulse の Mac 統合は codexbar CLI を補完的に利用しています。

バグ報告・機能要望は GitHub Issues へ。プルリクエスト歓迎します。

---

## ライセンス

MIT License — 詳細は [LICENSE](./LICENSE) を参照してください。
