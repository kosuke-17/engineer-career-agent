# DDDレイヤードアーキテクチャへのリファクタリング計画

## 現在の構造と問題点

```
app/
├── api/routes/      # Presentation（一部）
├── agents/          # Application + Domain 混在
├── storage/         # Infrastructure（一部）
├── models/          # Domain（一部）
├── tools/           # Domain/Application 混在
└── llm/             # Infrastructure
```

**問題点:**

- 層の境界が曖昧
- ドメインロジックがInfrastructure層に依存
- リポジトリパターン未適用
- ユースケースが明確でない

## 新しいディレクトリ構造

```
app/
├── domain/                    # ドメイン層（最内層）
│   ├── entities/              # エンティティ
│   │   ├── learner.py         # 学習者エンティティ
│   │   ├── diagnosis.py       # 診断セッションエンティティ
│   │   └── roadmap.py         # ロードマップエンティティ
│   ├── value_objects/         # 値オブジェクト
│   │   ├── skill_score.py     # スキルスコア
│   │   ├── phase.py           # 診断フェーズ
│   │   └── domain_aptitude.py # 領域適性
│   ├── repositories/          # リポジトリインターフェース
│   │   ├── learner_repository.py
│   │   └── diagnosis_repository.py
│   └── services/              # ドメインサービス
│       ├── skill_assessment.py
│       └── roadmap_generator.py
│
├── application/               # アプリケーション層
│   ├── use_cases/             # ユースケース
│   │   ├── diagnosis/
│   │   │   ├── start_diagnosis.py
│   │   │   ├── process_message.py
│   │   │   └── get_diagnosis_result.py
│   │   └── profile/
│   │       ├── create_profile.py
│   │       ├── update_profile.py
│   │       └── get_profile.py
│   ├── services/              # アプリケーションサービス
│   │   └── diagnosis_service.py
│   └── dto/                   # データ転送オブジェクト
│       ├── diagnosis_dto.py
│       └── profile_dto.py
│
├── infrastructure/            # インフラストラクチャ層
│   ├── persistence/           # 永続化実装
│   │   ├── file_learner_repository.py
│   │   └── file_diagnosis_repository.py
│   ├── llm/                   # LLMプロバイダー
│   │   ├── factory.py
│   │   └── agents/
│   │       ├── main_agent.py
│   │       └── subagents/
│   └── config.py
│
└── presentation/              # プレゼンテーション層
    ├── api/
    │   ├── routes/
    │   │   ├── diagnosis_router.py
    │   │   └── profile_router.py
    │   └── dependencies.py
    └── main.py
```

## 依存関係の方向

```
Presentation → Application → Domain ← Infrastructure
                    ↓
              Domain (中心)
```

- Domain層は他の層に依存しない
- Application層はDomain層のみに依存
- Infrastructure層はDomain層のインターフェースを実装
- Presentation層はApplication層を呼び出す

## 実装フェーズ

### Phase 1: Domain層の構築

1. エンティティの定義（Learner, DiagnosisSession, Roadmap）
2. 値オブジェクトの定義（SkillScore, Phase, DomainAptitude）
3. リポジトリインターフェースの定義
4. ドメインサービスの実装

### Phase 2: Application層の構築

1. DTOの定義
2. ユースケースの実装

   - StartDiagnosisUseCase
   - ProcessMessageUseCase
   - GetDiagnosisResultUseCase
   - CreateProfileUseCase 等

3. アプリケーションサービスの実装

### Phase 3: Infrastructure層の移行

1. リポジトリ実装（FileBackend → FileLearnerRepository等）
2. LLMエージェントの移行
3. 設定の移行

### Phase 4: Presentation層の移行

1. APIルーターのリファクタリング
2. 依存性注入の更新
3. エントリーポイントの更新

### Phase 5: 統合とテスト

1. 依存性注入コンテナの設定
2. 既存テストの更新
3. 統合テストの追加

## 主要な変更ポイント

### リポジトリパターンの導入

```python
# domain/repositories/learner_repository.py
class LearnerRepository(ABC):
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[Learner]: ...
    
    @abstractmethod
    async def save(self, learner: Learner) -> None: ...

# infrastructure/persistence/file_learner_repository.py
class FileLearnerRepository(LearnerRepository):
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    async def find_by_id(self, user_id: str) -> Optional[Learner]:
        # ファイルから読み込み、エンティティに変換
        ...
```

### ユースケースパターン

```python
# application/use_cases/diagnosis/start_diagnosis.py
class StartDiagnosisUseCase:
    def __init__(
        self,
        learner_repo: LearnerRepository,
        diagnosis_repo: DiagnosisRepository,
        llm_service: LLMService,
    ):
        self.learner_repo = learner_repo
        self.diagnosis_repo = diagnosis_repo
        self.llm_service = llm_service
    
    async def execute(self, request: StartDiagnosisRequest) -> StartDiagnosisResponse:
        learner = await self.learner_repo.find_by_id(request.user_id)
        session = DiagnosisSession.create(learner)
        response = await self.llm_service.generate_initial_response(session)
        await self.diagnosis_repo.save(session)
        return StartDiagnosisResponse(session_id=session.id, message=response)
```
