# 行動履歴 - Learning Path Agent 実装

## 実装日: 2025年12月1日

---

## Phase 1: プロジェクト基盤セットアップ ✅

### 実施内容
1. **プロジェクト初期化**
   - `uv init --name learning-path-agent` でプロジェクト作成
   - Python 3.12 を使用

2. **依存関係の追加**
   ```bash
   uv add fastapi uvicorn langchain langchain-anthropic pydantic python-dotenv aiofiles pydantic-settings
   ```

3. **ディレクトリ構造の作成**
   - `app/` - アプリケーションコード
   - `app/api/routes/` - APIエンドポイント
   - `app/agents/middleware/` - ミドルウェア
   - `app/agents/subagents/` - サブエージェント
   - `app/tools/` - LangChainツール
   - `app/storage/` - ストレージ層
   - `app/models/` - Pydanticモデル
   - `data/memories/` - 永続化データ
   - `data/sessions/` - セッションデータ
   - `tests/` - テストコード
   - `docs/` - ドキュメント

4. **設定ファイルの作成**
   - `.env.example` - 環境変数テンプレート
   - `app/config.py` - Pydantic Settings による設定管理

---

## Phase 2: ストレージ層の実装 ✅

### 実施内容
1. **データスキーマ定義** (`app/storage/schemas.py`)
   - `LearnerProfile` - 学習者プロファイル
   - `SkillHistory` - スキル履歴
   - `CompletedCourse` - 完了コース
   - `AssessmentResult` - 診断結果
   - `LearningPreferences` - 学習設定
   - `LearningRoadmap` - 学習ロードマップ

2. **ファイルバックエンド実装** (`app/storage/file_backend.py`)
   - 短期ストレージ (`/sessions/`)
   - 長期ストレージ (`/memories/`)
   - CRUD操作の実装
   - JSON/Markdown ファイルのサポート

---

## Phase 3: ツール層の実装 ✅

### 実施内容
1. **診断ツール** (`app/tools/assessment.py`)
   - `assess_foundation_skills` - 基礎スキル診断
   - `assess_domain_aptitude` - 領域適性評価
   - `assess_technical_depth` - 技術深度測定
   - `fetch_learning_resources` - 学習リソース検索

2. **ロードマップ生成ツール** (`app/tools/roadmap.py`)
   - `generate_learning_roadmap` - 12ヶ月の学習計画生成
   - 4フェーズ（四半期ごと）の計画
   - 週間スケジュール提案

---

## Phase 4: ミドルウェア層の実装 ✅

### 実施内容
1. **TodoListMiddleware** (`app/agents/middleware/todolist.py`)
   - 5フェーズの診断進行管理
   - `write_todos`, `edit_todo` 機能
   - 進捗表示フォーマット

2. **FilesystemMiddleware** (`app/agents/middleware/filesystem.py`)
   - `ls`, `read_file`, `write_file`, `edit_file` 機能
   - 短期/長期メモリルーティング
   - ユーザーコンテキストの読み込み

3. **SubAgentMiddleware** (`app/agents/middleware/subagent.py`)
   - サブエージェント登録・管理
   - 委譲機能の実装
   - オーケストレーター

---

## Phase 5: サブエージェントの実装 ✅

### 実施内容
1. **FoundationAssessorAgent** (`app/agents/subagents/foundation.py`)
   - プログラミング基礎の評価
   - アルゴリズム・データ構造の診断
   - スコアリング機能

2. **DomainMatcherAgent** (`app/agents/subagents/domain.py`)
   - 5領域（Frontend/Backend/DevOps/ML/Mobile）の適性評価
   - 推奨領域の決定

3. **TechnicalAnalyzerAgent** (`app/agents/subagents/technical.py`)
   - 技術スタックの詳細評価
   - 学習優先度の決定
   - プロジェクト提案

---

## Phase 6: 統合エージェントの実装 ✅

### 実施内容
1. **LearningPathAgent** (`app/agents/main_agent.py`)
   - 3つのミドルウェアの統合
   - セッション管理
   - フェーズごとのハンドリング
   - ロードマップ生成の統合

---

## Phase 7: API層の実装 ✅

### 実施内容
1. **診断APIエンドポイント** (`app/api/routes/diagnosis.py`)
   - `POST /diagnosis/start` - 診断開始
   - `POST /diagnosis/{session_id}/message` - メッセージ送信
   - `GET /diagnosis/{session_id}/status` - 進行状況取得
   - `GET /diagnosis/{session_id}/result` - 結果取得
   - `POST /diagnosis/{session_id}/advance-phase` - フェーズ進行
   - `GET /diagnosis/{session_id}/todos` - Todo取得

2. **プロファイルAPIエンドポイント** (`app/api/routes/profile.py`)
   - `POST /profile/` - プロファイル作成
   - `GET /profile/{user_id}` - プロファイル取得
   - `PUT /profile/{user_id}` - プロファイル更新
   - `DELETE /profile/{user_id}` - プロファイル削除
   - `GET /profile/{user_id}/history` - 診断履歴取得

---

## Phase 8: テストとドキュメントの作成 ✅

### 実施内容
1. **テストコード**
   - `tests/conftest.py` - pytest設定・フィクスチャ
   - `tests/test_tools/test_assessment.py` - 診断ツールテスト
   - `tests/test_tools/test_roadmap.py` - ロードマップテスト
   - `tests/test_api/test_health.py` - ヘルスチェックテスト
   - `tests/test_storage/test_file_backend.py` - ストレージテスト

2. **ドキュメント**
   - `README.md` - プロジェクト説明
   - `docs/action_history.md` - 行動履歴（本ファイル）

---

## セキュリティレビュー

### 発見された問題点
1. **パストラバーサル脆弱性** - `_get_path` メソッドでの検証不足
2. **認証・認可の欠如** - APIエンドポイントに認証なし
3. **CORS設定** - `allow_origins=["*"]` は本番環境で危険
4. **エラー情報の漏洩** - 例外メッセージがそのまま返される
5. **デフォルト設定** - `debug=True` がデフォルト
6. **入力検証の不足** - UUID形式の検証なし
7. **レート制限の欠如** - DoS対策なし

### 推奨対応
- 本番デプロイ前に上記問題点を修正する
- セキュリティ監査を実施する

---

## Phase 9: 診断レスポンス構造化 ✅

### 実装日: 2025年12月2日

### 背景
- 診断の対話が長すぎる問題を解決
- 自由記述チャット形式から構造化された選択式質問形式に変更

### 実施内容

1. **DTO層の拡張** (`app/application/dto/diagnosis_dto.py`)
   - `QuestionOption` - 選択肢データクラス
   - `Question` - 構造化質問データクラス（単一/複数選択対応）
   - `Answer` - 回答データクラス
   - `StructuredResponse` - LLMからの構造化レスポンス
   - `StartDiagnosisResponse`, `SendMessageRequest`, `SendMessageResponse` を新構造に変更

2. **Messageエンティティの拡張** (`app/domain/entities/diagnosis.py`)
   - `questions` フィールド追加（AIからの質問を保存）
   - `answers` フィールド追加（ユーザーの回答を保存）
   - `add_message` メソッドを拡張

3. **LLMServiceインターフェースの変更** (`app/application/services/llm_service.py`)
   - `generate_initial_message` → `generate_initial_response` に変更
   - `process_message` → `process_answers` に変更
   - 戻り値を `StructuredResponse` に変更

4. **LLMService実装の変更** (`app/infrastructure/llm/llm_service.py`)
   - システムプロンプトをJSON出力形式に変更
   - 各フェーズの質問を2-3問のセットで効率化
   - `_parse_structured_response` メソッド追加
   - `_format_answers` メソッド追加

5. **UseCase層の更新**
   - `StartDiagnosisUseCase` - 構造化レスポンス対応
   - `ProcessMessageUseCase` - 回答ベースの処理に変更

6. **APIルーターの更新** (`app/presentation/api/routes/diagnosis_router.py`)
   - `QuestionOptionModel`, `QuestionModel`, `AnswerModel` Pydanticモデル追加
   - リクエスト/レスポンス形式を新構造に変更

7. **永続化層の更新** (`app/infrastructure/persistence/file_diagnosis_repository.py`)
   - `questions`/`answers` フィールドの永続化対応

### 新しいAPI構造

**レスポンス形式:**
```json
{
  "session_id": "xxx",
  "message": "AIからの説明・コメント",
  "questions": [
    {
      "id": "q1",
      "text": "質問文",
      "type": "single | multiple",
      "options": [
        { "id": "opt1", "label": "選択肢1" },
        { "id": "opt2", "label": "選択肢2" }
      ]
    }
  ],
  "current_phase": "foundation",
  "phase_changed": false,
  "is_completed": false,
  "progress_percentage": 20.0
}
```

**リクエスト形式:**
```json
{
  "answers": [
    { "question_id": "q1", "selected_options": ["opt1"] }
  ],
  "supplement": "補足テキスト（任意）"
}
```

---

## Phase 10: V2診断API - 定数管理質問とロードマップ生成 ✅

### 実装日: 2025年12月2日

### 背景
- 診断質問をAIの動的生成ではなく、定数で管理したい要望
- フロントエンド・バックエンド・インフラの3領域から1つを選択して深掘り
- ゴールを定数一覧から選択（例：転職先でXXX領域で活躍するため）
- 全コンテキストを元にAIがJSON構造化ロードマップを生成

### 設計方針
- 新規API作成 (`/api/v2/diagnosis`) - 既存APIと並行運用可能
- 既存の5フェーズ構造とは異なる新フロー

### 新しい診断フロー
```
1. 領域選択 → 2. ゴール選択 → 3. 共通質問 → 4. 領域別質問 → 5. ロードマップ生成(AI)
```

### 実施内容

1. **定数定義** (`app/domain/constants/diagnosis_questions.py`)
   - `Domain` - 3領域の定義（frontend/backend/infrastructure）
   - `DOMAINS` - 領域選択用データ
   - `GOALS` - 領域ごとのゴール一覧（計12個）
   - `COMMON_QUESTIONS` - 共通質問6問（経験年数、学習時間、スタイル等）
   - `DOMAIN_QUESTIONS` - 領域別深掘り質問
     - フロントエンド: 8問（HTML/CSS、JS、TS、フレームワーク等）
     - バックエンド: 9問（言語、フレームワーク、DB、API設計等）
     - インフラ: 9問（クラウド、コンテナ、IaC、CI/CD等）

2. **エンティティ** (`app/domain/entities/structured_diagnosis.py`)
   - `StructuredDiagnosisPhase` - 6フェーズ定義
   - `QuestionAnswer` - 質問・回答ペア
   - `StructuredDiagnosisSession` - セッションエンティティ
     - 領域・ゴール・回答の保持
     - ロードマップの保持
     - 進捗計算

3. **リポジトリ**
   - `StructuredDiagnosisRepository` - インターフェース
   - `FileStructuredDiagnosisRepository` - ファイル永続化実装

4. **ユースケース** (`app/application/use_cases/v2_diagnosis/`)
   - `StartV2DiagnosisUseCase` - セッション開始、領域選択肢返却
   - `SelectDomainUseCase` - 領域選択、ゴール選択肢返却
   - `SelectGoalUseCase` - ゴール選択、共通質問返却
   - `SubmitAnswersUseCase` - 回答処理、次質問 or ロードマップ生成
   - `GetRoadmapUseCase` - ロードマップ取得

5. **APIルーター** (`app/presentation/api/routes/v2_diagnosis_router.py`)
   | エンドポイント | 説明 |
   |---|---|
   | `POST /api/v2/diagnosis/start` | セッション開始、領域選択肢を返す |
   | `POST /api/v2/diagnosis/{id}/domain` | 領域選択 → ゴール選択肢を返す |
   | `POST /api/v2/diagnosis/{id}/goal` | ゴール選択 → 共通質問を返す |
   | `POST /api/v2/diagnosis/{id}/answers` | 質問回答 → 次の質問 or ロードマップ |
   | `GET /api/v2/diagnosis/{id}/roadmap` | 生成されたロードマップを取得 |

6. **LLMService拡張** (`app/infrastructure/llm/llm_service.py`)
   - `generate_structured_roadmap` メソッド追加
   - 入力: 領域、ゴール、全質問・回答コンテキスト
   - 出力: JSON構造化ロードマップ（フェーズ、マイルストーン、最終プロジェクト等）

### 生成されるロードマップ構造
```json
{
  "goal": "学習のゴール",
  "domain": "専門領域",
  "duration_months": 6,
  "weekly_hours_recommended": 10,
  "phases": [
    {
      "phase": 1,
      "title": "フェーズ名",
      "duration_weeks": 4,
      "topics": [...],
      "hands_on_project": {...}
    }
  ],
  "milestones": [...],
  "final_project": {...},
  "career_advice": "アドバイス",
  "next_steps": [...]
}
```

### 変更ファイル一覧
- 新規: `app/domain/constants/__init__.py`
- 新規: `app/domain/constants/diagnosis_questions.py`
- 新規: `app/domain/entities/structured_diagnosis.py`
- 新規: `app/domain/repositories/structured_diagnosis_repository.py`
- 新規: `app/infrastructure/persistence/file_structured_diagnosis_repository.py`
- 新規: `app/application/use_cases/v2_diagnosis/__init__.py`
- 新規: `app/application/use_cases/v2_diagnosis/start_diagnosis.py`
- 新規: `app/application/use_cases/v2_diagnosis/select_domain.py`
- 新規: `app/application/use_cases/v2_diagnosis/select_goal.py`
- 新規: `app/application/use_cases/v2_diagnosis/submit_answers.py`
- 新規: `app/application/use_cases/v2_diagnosis/get_roadmap.py`
- 新規: `app/presentation/api/routes/v2_diagnosis_router.py`
- 更新: `app/domain/entities/__init__.py`
- 更新: `app/domain/repositories/__init__.py`
- 更新: `app/infrastructure/persistence/__init__.py`
- 更新: `app/application/use_cases/__init__.py`
- 更新: `app/application/services/llm_service.py`
- 更新: `app/infrastructure/llm/llm_service.py`
- 更新: `app/presentation/api/dependencies.py`
- 更新: `app/presentation/main.py`

---

## Phase 11: Deprecated Router & 未使用コードの削除 ✅

### 実装日: 2025年12月2日

### 背景
- V1診断API (`diagnosis_router`) と Profile API (`profile_router`) が deprecated
- `eng_career_diagnosis_router` に移行完了
- 未使用コードの整理・削除

### 削除内容

1. **Router ファイル**
   - `app/presentation/api/routes/diagnosis_router.py`
   - `app/presentation/api/routes/profile_router.py`

2. **Use Cases ディレクトリ**
   - `app/application/use_cases/diagnosis/` (ディレクトリ全体)
   - `app/application/use_cases/profile/` (ディレクトリ全体)

3. **DTO**
   - `app/application/dto/profile_dto.py`

4. **Domain / Infrastructure (Learner関連)**
   - `app/domain/entities/learner.py`
   - `app/domain/repositories/learner_repository.py`
   - `app/infrastructure/persistence/file_learner_repository.py`

5. **Domain / Infrastructure (Roadmap関連 - 未使用)**
   - `app/domain/entities/roadmap.py`
   - `app/domain/repositories/roadmap_repository.py`
   - `app/infrastructure/persistence/file_roadmap_repository.py`

### 更新内容

1. **__init__.py ファイルのエクスポート整理**
   - `app/presentation/api/routes/__init__.py`
   - `app/application/use_cases/__init__.py`
   - `app/application/dto/__init__.py`
   - `app/domain/entities/__init__.py`
   - `app/domain/repositories/__init__.py`
   - `app/infrastructure/persistence/__init__.py`

2. **dependencies.py の依存関係削除**
   - 不要なリポジトリ・ユースケースの依存関係を削除
   - `eng_career_diagnosis` 関連のみ残存

3. **main.py**
   - deprecated コメント行を削除

### 残存ファイル（LLMService で使用）
- `app/application/dto/diagnosis_dto.py`
- `app/domain/entities/diagnosis.py`
- `app/domain/repositories/diagnosis_repository.py`
- `app/infrastructure/persistence/file_diagnosis_repository.py`

---

## 今後の拡張案

1. **認証システム**
   - JWT認証の実装
   - OAuth2対応

2. **データベース移行**
   - PostgreSQL/MongoDB への移行
   - 検索機能の強化

3. **UI/フロントエンド**
   - React/Next.js によるWebUI
   - リアルタイムチャット機能

4. **機能拡張**
   - 学習進捗のトラッキング
   - コミュニティ機能
   - 外部学習プラットフォーム連携


