# Changelog

## [0.1.0] - 2026-06-19

### Added
- `usage-pulse statusline`: tmux status-right 用キャッシュ付きステータス出力
- `usage-pulse summary`: 今日の使用量サマリー表示
- `usage-pulse roi`: モデル別トークン ROI テーブル
- `usage-pulse sync`: エージェントハンドシェイク状態ファイル更新
- `usage-pulse tray`: クロスプラットフォームシステムトレイデーモン (pystray)
- `usage-pulse setup`: インタラクティブセットアップ
- `CcusageProvider`: ccusage daily --json ベースのデータ取得（全 OS 対応）
- `CodexbarProvider`: codexbar レートウィンドウ取得（Mac、pseudo-TTY 経由）
- `ModelAdvisor`: 使用量ベースのモデル選択推奨
- `ModelROI`: モデル別コスト効率・キャッシュ効率計算
- `Notifier`: OS 別デスクトップ通知（Mac/Linux/WSL/Windows）
- `handshake.py`: AI エージェント向け状態ファイル (`~/.local/state/usage-pulse/current.json`)
- `skills/model-advisor/SKILL.md`: Claude Code Skill
- `providers/VERSION_PINS.json`: プロバイダースキーマのバージョン管理
- GitHub Actions: CI（Mac/Win/Linux × Python 3.11/3.12）
- GitHub Actions: 週次プロバイダー更新チェック

### Known Issues
- codexbar は TTY なしでハング (upstream issue #1329)。`script(1)` で回避。
- ccusage `statusline` コマンドはスタンドアロン実行不可（Claude Code フック専用）。
