# Learning Path Customization Agent

AIを活用したエンジニア向け学習パス自動カスタマイズサービスです。Deep Agentアーキテクチャを採用し、段階的な診断を通じてパーソナライズされた学習ロードマップを生成します。

## 機能概要

- **5段階の診断プロセス**: 基礎スキル → 領域適性 → 技術詳細 → アーキテクチャ → ロードマップ生成
- **パーソナライズされた学習パス**: 学習者のスキルレベル、目標、利用可能時間に基づいた最適化
- **進捗追跡**: TodoListによる診断フェーズの可視化
- **学習者プロファイル管理**: 長期的な学習履歴の保存と参照

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│         Learning Path Customization Deep Agent              │
├─────────────────────────────────────────────────────────────┤
│  1️⃣ TodoListMiddleware    → 診断進行状況管理               │
│  2️⃣ FilesystemMiddleware  → 学習者プロファイル記憶         │
│  3️⃣ SubAgentMiddleware    → 専門診断の委譲                 │
└─────────────────────────────────────────────────────────────┘
```

## 技術スタック

- **言語**: Python 3.12+
- **パッケージ管理**: uv
- **フレームワーク**: FastAPI + Uvicorn
- **LLM**: LangChain + Anthropic Claude / Ollama（切り替え可能）
- **データ検証**: Pydantic v2
- **ストレージ**: ファイルシステム (JSON/Markdown)

## セットアップ

### 前提条件

- Python 3.12以上
- uv (パッケージマネージャー)
- Anthropic API Key または Ollama

### インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd enginner-career-agent

# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してANTHROPIC_API_KEYを設定
```

### 環境変数

`.env`ファイルに以下の環境変数を設定してください：

#### Anthropicを使用する場合

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

#### Ollama（ローカルLLM）を使用する場合

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

#### 共通オプション

```env
APP_ENV=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### Ollamaのセットアップ

ローカルLLMを使用する場合は、事前にOllamaをインストールしてモデルをダウンロードしてください：

```bash
# Ollamaのインストール（macOS）
brew install ollama

# Ollamaサーバーの起動
ollama serve

# モデルのダウンロード（別ターミナルで）
ollama pull llama3
```

## 起動方法

### 開発サーバー

```bash
uv run uvicorn app.main:app --reload
```

### 本番サーバー

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

サーバー起動後、以下のURLにアクセスできます：

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API エンドポイント

### 診断 API

| Method | Endpoint | 説明 |
|--------|----------|------|
| POST | `/diagnosis/start` | 新しい診断セッションを開始 |
| POST | `/diagnosis/{session_id}/message` | メッセージを送信 |
| GET | `/diagnosis/{session_id}/status` | 診断状況を取得 |
| GET | `/diagnosis/{session_id}/result` | 診断結果を取得 |
| POST | `/diagnosis/{session_id}/advance-phase` | 次のフェーズに進む |
| GET | `/diagnosis/{session_id}/todos` | Todo一覧を取得 |

### プロファイル API

| Method | Endpoint | 説明 |
|--------|----------|------|
| POST | `/profile/` | プロファイルを作成 |
| GET | `/profile/{user_id}` | プロファイルを取得 |
| PUT | `/profile/{user_id}` | プロファイルを更新 |
| DELETE | `/profile/{user_id}` | プロファイルを削除 |
| GET | `/profile/{user_id}/history` | 診断履歴を取得 |

## 使用例

### 診断セッションの開始

```bash
curl -X POST "http://localhost:8000/diagnosis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "initial_message": "バックエンド開発を学びたいです"
  }'
```

### メッセージの送信

```bash
curl -X POST "http://localhost:8000/diagnosis/{session_id}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Pythonを3年間使っています"
  }'
```

## 診断フロー

1. **Phase 1: 基礎スキル診断**
   - プログラミング言語の理解度
   - アルゴリズム・計算量の理解
   - データ構造の理解

2. **Phase 2: 専攻領域選定**
   - フロントエンド/バックエンド/DevOps等の適性判定
   - 興味・関心の分析

3. **Phase 3: 詳細技術診断**
   - 選定領域の技術スタック適性評価
   - 具体的な技術の習熟度測定

4. **Phase 4: アーキテクチャ適性**
   - システム設計能力の診断
   - トレードオフ判断力の評価

5. **Phase 5: 学習ロードマップ生成**
   - 12ヶ月の学習計画
   - 推奨プロジェクトとリソース

## プロジェクト構造

```
enginner-career-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIエントリーポイント
│   ├── config.py            # 設定管理
│   ├── api/
│   │   └── routes/          # APIエンドポイント
│   ├── agents/
│   │   ├── main_agent.py    # 統合Deep Agent
│   │   ├── middleware/      # ミドルウェア層
│   │   └── subagents/       # サブエージェント
│   ├── tools/               # LangChainツール
│   ├── storage/             # ストレージ層
│   └── models/              # Pydanticモデル
├── data/
│   ├── memories/            # 永続化データ
│   └── sessions/            # セッションデータ
├── tests/                   # テストコード
├── docs/                    # ドキュメント
└── pyproject.toml           # プロジェクト設定
```

## テスト

```bash
# テストの実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=app

# 特定のテストファイル
uv run pytest tests/test_tools/test_assessment.py
```

## 開発

### コードフォーマット

```bash
# Ruffによるフォーマット
uv run ruff format .

# リントチェック
uv run ruff check .
```

## セキュリティに関する注意

本番環境にデプロイする際は、以下の点に注意してください：

1. **CORS設定**: 特定のオリジンのみを許可する
2. **認証**: JWT等の認証機構を実装する
3. **入力検証**: パストラバーサル対策を強化する
4. **エラーハンドリング**: 内部エラーの詳細を隠蔽する
5. **レート制限**: DoS対策を実装する

## ライセンス

MIT License

## 貢献

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

