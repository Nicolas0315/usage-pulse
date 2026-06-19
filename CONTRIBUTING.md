# Contributing to usage-pulse

## 開発環境セットアップ

```bash
git clone https://github.com/Nicolas0315/usage-pulse
cd usage-pulse
uv sync --dev
```

## テスト

```bash
python -m pytest tests/ -v
```

## ブランチ戦略

- `main`: リリースブランチ
- `feat/<name>`: 新機能
- `fix/<name>`: バグ修正
- `docs/<name>`: ドキュメント

## コミットメッセージ

`feat:` / `fix:` / `docs:` / `refactor:` / `test:` プレフィックスを使用。

## プロバイダースキーマ変更の対応

`providers/VERSION_PINS.json` を更新し、変更内容をコミットメッセージに明記してください。
