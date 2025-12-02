# AWS SAM デプロイ手順ガイド

このドキュメントでは、AWS SAM (Serverless Application Model) を使用したLearning Path Agentのデプロイ手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [プロジェクト構成](#プロジェクト構成)
3. [環境設定](#環境設定)
4. [ローカル開発](#ローカル開発)
5. [デプロイ手順](#デプロイ手順)
6. [環境別デプロイ](#環境別デプロイ)
7. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要なツール

以下のツールがインストールされていることを確認してください：

```bash
# AWS CLI のインストール確認
aws --version

# AWS SAM CLI のインストール確認
sam --version

# Python 3.12 のインストール確認
python3.12 --version
```

### インストール方法

```bash
# AWS CLI (macOS)
brew install awscli

# AWS SAM CLI (macOS)
brew install aws-sam-cli

# Python 3.12 (macOS)
brew install python@3.12
```

### AWS認証設定

```bash
# AWS認証情報の設定
aws configure

# 設定内容の確認
aws sts get-caller-identity
```

---

## プロジェクト構成

### SAM関連ファイル

| ファイル | 説明 |
|---------|------|
| `template.yaml` | SAMテンプレート（インフラ定義） |
| `samconfig.toml` | SAM CLI設定ファイル |
| `handler.py` | Lambda エントリポイント |
| `requirements.txt` | Python依存関係 |

### アーキテクチャ概要

```
AWS Lambda (Python 3.12, ARM64)
    │
    ├── handler.py (Mangum)
    │       │
    │       └── FastAPI Application
    │
    └── HTTP API Gateway
            │
            └── エンドポイント: /{proxy+}
```

---

## 環境設定

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `APP_ENV` | 環境名 | development |
| `DEBUG` | デバッグモード | false |
| `LLM_PROVIDER` | LLMプロバイダー | openai |
| `DATA_DIR` | データディレクトリ | /tmp/data |
| `MEMORIES_DIR` | メモリディレクトリ | /tmp/data/memories |
| `SESSIONS_DIR` | セッションディレクトリ | /tmp/data/sessions |

### APIキーの設定

本番環境では、APIキーをAWS Systems Manager Parameter Storeに保存することを推奨します：

```bash
# Anthropic APIキーの設定
aws ssm put-parameter \
  --name "/learning-path-agent/production/anthropic-api-key" \
  --value "your-api-key-here" \
  --type SecureString

# OpenAI APIキーの設定
aws ssm put-parameter \
  --name "/learning-path-agent/production/openai-api-key" \
  --value "your-api-key-here" \
  --type SecureString
```

---

## ローカル開発

### ローカルAPIの起動

```bash
# SAMでローカルAPIサーバーを起動
sam local start-api

# 環境変数ファイルを指定して起動
sam local start-api --env-vars env.json
```

### ローカルでの関数呼び出し

```bash
# 単一の関数を呼び出し
sam local invoke FastApiFunction

# イベントファイルを指定して呼び出し
sam local invoke FastApiFunction --event events/test-event.json
```

### ホットリロード

```bash
# ファイル変更を監視して自動リロード
sam sync --watch
```

---

## デプロイ手順

### Step 1: ビルド

```bash
# アプリケーションをビルド
sam build

# キャッシュを使用してビルド（高速化）
sam build --cached --parallel
```

ビルドが成功すると、`.aws-sam/build/` ディレクトリに成果物が生成されます。

### Step 2: テンプレートの検証

```bash
# テンプレートの検証
sam validate

# Lintを含めた検証
sam validate --lint
```

### Step 3: デプロイ

```bash
# 対話形式でデプロイ（初回推奨）
sam deploy --guided

# 設定ファイルを使用してデプロイ
sam deploy

# 変更セットの確認をスキップ（CI/CD向け）
sam deploy --no-confirm-changeset
```

### デプロイの流れ

```
sam build → sam validate → sam deploy
    │            │             │
    ▼            ▼             ▼
 ビルド成果物   テンプレート   CloudFormation
 生成          検証          スタック作成/更新
```

---

## 環境別デプロイ

### Development環境（デフォルト）

```bash
# ビルド
sam build

# デプロイ
sam deploy
```

設定内容（`samconfig.toml`より）：
- スタック名: `learning-path-agent`
- リージョン: `ap-northeast-1`
- 環境: `development`

### Staging環境

```bash
# ビルド
sam build

# Staging環境へデプロイ
sam deploy --config-env staging
```

設定内容：
- スタック名: `learning-path-agent-staging`
- 環境: `staging`

### Production環境

```bash
# ビルド
sam build

# Production環境へデプロイ
sam deploy --config-env production
```

設定内容：
- スタック名: `learning-path-agent-prod`
- 環境: `production`

---

## デプロイ後の確認

### エンドポイントの確認

```bash
# スタックの出力を確認
aws cloudformation describe-stacks \
  --stack-name learning-path-agent \
  --query 'Stacks[0].Outputs'
```

### ヘルスチェック

```bash
# APIエンドポイントにアクセス
curl https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/health
```

### ログの確認

```bash
# Lambda関数のログを表示
sam logs -n FastApiFunction --stack-name learning-path-agent --tail

# 特定期間のログを表示
sam logs -n FastApiFunction --stack-name learning-path-agent --start-time '10min ago'
```

---

## スタックの削除

```bash
# Development環境の削除
sam delete --stack-name learning-path-agent

# Staging環境の削除
sam delete --stack-name learning-path-agent-staging

# Production環境の削除
sam delete --stack-name learning-path-agent-prod
```

---

## トラブルシューティング

### よくあるエラー

#### 1. ビルドエラー

```bash
# キャッシュをクリアしてリビルド
sam build --no-cached
```

#### 2. デプロイ権限エラー

IAMユーザー/ロールに以下の権限が必要です：
- `cloudformation:*`
- `lambda:*`
- `apigateway:*`
- `s3:*`
- `iam:*`

#### 3. タイムアウトエラー

`template.yaml`でタイムアウト値を調整：
```yaml
Globals:
  Function:
    Timeout: 60  # 秒単位で調整
```

#### 4. メモリ不足エラー

`template.yaml`でメモリサイズを調整：
```yaml
Properties:
  MemorySize: 2048  # MB単位で調整
```

### デバッグ方法

```bash
# 詳細なログを有効化
sam build --debug
sam deploy --debug

# CloudFormationイベントの確認
aws cloudformation describe-stack-events \
  --stack-name learning-path-agent
```

---

## CI/CD統合

### GitHub Actions例

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: aws-actions/setup-sam@v2
      
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
      
      - run: sam build
      - run: sam deploy --no-confirm-changeset
```

---

## 参考リンク

- [AWS SAM 開発者ガイド](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)
- [SAM CLI コマンドリファレンス](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
- [Mangum - FastAPI + Lambda](https://mangum.io/)

