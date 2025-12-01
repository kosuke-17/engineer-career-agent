# 学習パス自動カスタマイズサービス - Deep Agent実装設計

## 全体アーキテクチャ

このサービスはDeep Agentの3つのコア機能を完全に活用して構成されます：

```
┌─────────────────────────────────────────────────────────────┐
│         Learning Path Customization Deep Agent             │
├─────────────────────────────────────────────────────────────┤
│  1️⃣ TodoList Middleware    → 学習診断の進行状況管理        │
│  2️⃣ Filesystem Middleware  → 学習者プロファイル記憶        │
│  3️⃣ SubAgent Middleware    → 段階的な深掘り診断分割       │
└─────────────────────────────────────────────────────────────┘
```

---

## 実装の3つのレイヤー

### **レイヤー1：TodoListMiddleware - 学習診断パイプライン**

段階的な深掘り診断を構造化します。

```python
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from deepagents.middleware import FilesystemMiddleware, SubAgentMiddleware
import json

# 診断フェーズの定義
diagnosis_phases = [
    {
        "phase": 1,
        "name": "基礎スキル診断",
        "description": "プログラミング基礎、アルゴリズム、データ構造を診断"
    },
    {
        "phase": 2,
        "name": "専攻領域選定",
        "description": "フロントエンド/バックエンド/インフラなど適性を判定"
    },
    {
        "phase": 3,
        "name": "詳細技術診断",
        "description": "選定領域の具体的な技術スタック適性を評価"
    },
    {
        "phase": 4,
        "name": "アーキテクチャ適性",
        "description": "システム設計・アーキテクチャ思考能力を診断"
    },
    {
        "phase": 5,
        "name": "学習ロードマップ生成",
        "description": "全ての診断結果から最適な学習パスを生成"
    }
]

planning_middleware = TodoListMiddleware(
    system_prompt=f"""
    You are a Learning Path Advisor. You will conduct a comprehensive skill assessment 
    to create a personalized learning path for the engineer.
    
    Follow these phases in order:
    {json.dumps(diagnosis_phases, ensure_ascii=False, indent=2)}
    
    Use the write_todos tool to:
    1. Initialize the diagnosis plan before starting
    2. Mark phases as completed after thorough assessment
    3. Adapt subsequent phases based on findings from previous ones
    
    Be thorough and ask follow-up questions to understand each aspect deeply.
    """
)
```

**実装のコツ：**
- エンジニアは`write_todos`ツールで診断進捗をリアルタイム表示可能
- 各フェーズ完了時に`Edit`で内容を動的に調整
- 学習者の理解度に応じてフェーズ内容を自動修正

---

### **レイヤー2：FilesystemMiddleware - 学習者プロファイルメモリ**

短期（セッション内）と長期（永続）メモリの二層構造で学習プロファイルを構築します。

```python
from deepagents.middleware import FilesystemMiddleware
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

filesystem_middleware = FilesystemMiddleware(
    backend=lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)}  # 永続保存パス
    ),
    system_prompt="""
    You have access to a filesystem for storing and retrieving information:
    
    SHORT-TERM FILES (ephemeral, current session):
    - /current_session/diagnosis_results.md: 現在の診断中間結果
    - /current_session/questions.md: 質問履歴
    - /current_session/answers.md: 回答と推論
    
    LONG-TERM FILES (persistent, /memories/ prefix):
    - /memories/profile.json: エンジニアの基本情報・目標
    - /memories/skill_history.md: スキルレベルの履歴推移
    - /memories/completed_courses.json: 完了した学習コース
    - /memories/learning_preferences.json: 学習スタイル・得意分野
    - /memories/assessment_history.json: 過去の診断結果
    
    USAGE:
    1. Use ls to check what files exist
    2. Use read_file to retrieve previous learning history
    3. Use write_file to save new findings
    4. Use edit_file to update ongoing assessments
    
    Always reference previous learning history when providing recommendations.
    """,
    custom_tool_descriptions={
        "ls": "List files in current session (/current_session) or long-term memories (/memories)",
        "read_file": "Read skill history, completed courses, or previous assessments to understand the learner's journey",
        "write_file": "Create new diagnosis files or save learning progress",
        "edit_file": "Update current diagnosis results or learning recommendations as new information emerges"
    }
)
```

**ファイル構造の詳細：**

```
/current_session/
├── diagnosis_results.md
│   # 段階別診断結果
│   ## フェーズ1：基礎スキル
│   - Python: 中級 (7/10)
│   - アルゴリズム: 初級 (4/10)
│   - データ構造: 中級 (6/10)
│   
│   ## フェーズ2：適性領域
│   - バックエンド志向: 8/10
│   - フロントエンド志向: 5/10

├── questions.md
│   # 現在の診断質問
│   
└── answers.md
    # 学習者の回答と分析

/memories/
├── profile.json
│   {
│     "name": "田中太郎",
│     "years_of_experience": 2,
│     "goal": "フルスタックエンジニアからバックエンド特化へ",
│     "learning_hours_per_week": 15,
│     "preferred_learning_style": "実践プロジェクトベース"
│   }

├── skill_history.md
│   # 過去6ヶ月のスキル推移グラフ

├── completed_courses.json
│   [
│     {"course": "Python基礎", "completed": "2024-01", "score": 85},
│     {"course": "REST API設計", "completed": "2024-02", "score": 92}
│   ]

├── learning_preferences.json
│   {
│     "difficulty_level": "gradual",  # 段階的が好き
│     "project_based": true,
│     "community_learning": false
│   }

└── assessment_history.json
    [
      {"date": "2024-01", "overall_level": 5.2},
      {"date": "2024-02", "overall_level": 5.8}
    ]
```

---

### **レイヤー3：SubAgentMiddleware - 段階的な深掘り診断**

複数の専門サブエージェントが各診断フェーズを担当します。

```python
from langchain.tools import tool
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain.agents import create_agent
import json

# ツール定義
@tool
def assess_foundation_skills(assessment_type: str) -> str:
    """
    基礎スキル領域の詳細診断を実施
    - programming: プログラミング言語の理解度
    - algorithms: アルゴリズム・計算量の理解
    - data_structures: データ構造の理解
    """
    # 実装: 対話的な診断質問を返す
    return f"Assessing {assessment_type}..."

@tool
def assess_domain_aptitude(domains: str) -> str:
    """
    複数領域への適性を評価
    - frontend, backend, devops, ml-engineering, etc
    """
    return f"Evaluating aptitude for: {domains}"

@tool
def assess_technical_depth(domain: str, technologies: str) -> str:
    """
    選定領域の技術スタックでの深さを測定
    """
    return f"Assessing technical depth in {domain}: {technologies}"

@tool
def fetch_learning_resources(skill_level: str, topic: str, preferred_format: str) -> str:
    """
    学習者レベルに合わせたリソースを検索
    - skill_level: beginner, intermediate, advanced
    - preferred_format: video, text, interactive, project
    """
    return f"Found resources for {skill_level} in {topic}"

# サブエージェント定義
foundation_subagent = {
    "name": "foundation-assessor",
    "description": "Conducts in-depth assessment of programming fundamentals",
    "system_prompt": """
    You are a Foundation Skills Assessor. Your role is to:
    1. Ask targeted questions about programming fundamentals
    2. Assess understanding of algorithms and data structures
    3. Identify strengths and gaps
    4. Provide a foundation skills score (0-10)
    
    Always ask follow-up questions to understand the depth of knowledge.
    """,
    "tools": [assess_foundation_skills],
    "model": "claude-sonnet-4-5-20250929",
    "middleware": []
}

domain_subagent = {
    "name": "domain-matcher",
    "description": "Evaluates aptitude for different engineering domains",
    "system_prompt": """
    You are a Domain Aptitude Evaluator. Based on:
    - Their foundation skills
    - Their interests
    - Problem-solving patterns
    
    Rate aptitude for: Frontend, Backend, DevOps, ML Engineering, Systems Design
    Scale: 0-10 for each domain
    """,
    "tools": [assess_domain_aptitude],
    "model": "claude-sonnet-4-5-20250929",
    "middleware": []
}

technical_subagent = {
    "name": "technical-analyzer",
    "description": "Analyzes technical skills in specific domain",
    "system_prompt": """
    You are a Technical Skills Analyzer. For the selected domain:
    1. Identify key technologies to master
    2. Assess current knowledge of each
    3. Recommend learning sequence
    4. Suggest hands-on projects
    """,
    "tools": [assess_technical_depth, fetch_learning_resources],
    "model": "claude-sonnet-4-5-20250929",
    "middleware": []
}

subagent_middleware = SubAgentMiddleware(
    default_model="claude-sonnet-4-5-20250929",
    default_tools=[],
    subagents=[
        foundation_subagent,
        domain_subagent,
        technical_subagent
    ]
)
```

---

## 統合：Deep Agent設定

```python
from langchain.agents import create_agent
from langchain.tools import tool
import json

@tool
def generate_learning_roadmap(
    foundation_score: float,
    recommended_domain: str,
    technical_assessment: dict,
    learning_style: str,
    available_hours_per_week: int
) -> str:
    """
    全ての診断結果から最適な学習ロードマップを生成
    
    Returns:
        - 3段階（短期3ヶ月、中期6ヶ月、長期1年）の学習計画
        - 各段階でのプロジェクト課題
        - 習得すべき技術スタック
        - 推奨学習リソース
    """
    roadmap = {
        "summary": f"Personalized roadmap for {recommended_domain} engineering",
        "foundation": foundation_score,
        "recommended_path": [
            {
                "quarter": 1,
                "focus": ["技術1", "技術2"],
                "project": "プロジェクト1",
                "expected_hours": available_hours_per_week * 12
            },
            {
                "quarter": 2,
                "focus": ["技術3", "技術4"],
                "project": "プロジェクト2",
                "expected_hours": available_hours_per_week * 12
            }
        ]
    }
    return json.dumps(roadmap, ensure_ascii=False, indent=2)

# Deep Agent統合
learning_path_agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[
        # 最終出力ツール
        generate_learning_roadmap
    ],
    system_prompt="""
    You are an Advanced Learning Path Advisor powered by Deep Agent.
    
    Your mission:
    1. Conduct comprehensive skill assessment through multiple phases
    2. Maintain detailed learner profile using filesystem memory
    3. Delegate specialized assessments to appropriate subagents
    4. Generate personalized learning roadmap
    
    WORKFLOW:
    1. Use TodoList to track assessment phases (基礎診断 → 領域適性 → 技術詳細 → アーキテクチャ → ロードマップ生成)
    2. Use Filesystem to:
       - Read /memories/ to understand learner history
       - Write /current_session/ during diagnosis
       - Save final results to /memories/
    3. Delegate to SubAgents:
       - foundation-assessor for fundamentals
       - domain-matcher for career direction
       - technical-analyzer for technology stacks
    
    4. Generate comprehensive learning roadmap
    
    IMPORTANT:
    - Ask clarifying questions
    - Show reasoning in todo updates
    - Adapt based on learner responses
    - Always reference previous learning history
    """,
    middleware=[
        planning_middleware,          # フェーズ管理
        filesystem_middleware,        # プロファイル記憶
        subagent_middleware,         # 専門診断の委譲
    ]
)
```

---

## 実際の使用フロー

### **初回診断**

```python
# 初回ユーザー
result = await learning_path_agent.invoke({
    "messages": [{
        "role": "user",
        "content": """
        こんにちは。私は2年間のPython経験があり、
        フルスタックからバックエンド特化へシフトしたいです。
        週15時間の学習時間が取れます。
        """
    }]
})

# 出力：
# - TodoList表示：🔄 基礎スキル診断 (進行中)
# - 対話的な診断質問
# - /current_session/diagnosis_results.md に中間
