"""Assessment tools for Learning Path Agent."""

import json
from typing import Literal

from langchain_core.tools import tool


@tool
def assess_foundation_skills(
    assessment_type: Literal["programming", "algorithms", "data_structures"],
) -> str:
    """
    基礎スキル領域の詳細診断を実施するツール。

    Args:
        assessment_type: 診断タイプ
            - programming: プログラミング言語の理解度
            - algorithms: アルゴリズム・計算量の理解
            - data_structures: データ構造の理解

    Returns:
        診断用の質問と評価基準
    """
    questions = {
        "programming": {
            "questions": [
                "主に使用しているプログラミング言語は何ですか？その言語で何年の経験がありますか？",
                "オブジェクト指向プログラミングの3つの原則（カプセル化、継承、ポリモーフィズム）を説明できますか？",
                "関数型プログラミングの概念（純粋関数、イミュータビリティ、高階関数）について説明してください。",
                "最近取り組んだプロジェクトで、どのようなデザインパターンを使用しましたか？",
            ],
            "evaluation_criteria": {
                "beginner": "基本的な構文を理解している",
                "intermediate": "OOPの概念を理解し実践できる",
                "advanced": "複数のパラダイムを使い分けられる",
                "expert": "言語の内部実装まで理解している",
            },
        },
        "algorithms": {
            "questions": [
                "Big O記法について説明してください。O(n)とO(n^2)の違いは何ですか？",
                "二分探索アルゴリズムを説明してください。どのような状況で使用しますか？",
                "ソートアルゴリズムで知っているものを挙げてください。それぞれの時間計算量は？",
                "動的計画法（DP）について説明してください。具体的な問題例はありますか？",
            ],
            "evaluation_criteria": {
                "beginner": "基本的なソートと検索を理解している",
                "intermediate": "計算量を意識したコードが書ける",
                "advanced": "複雑なアルゴリズムを実装できる",
                "expert": "最適化やカスタムアルゴリズムを設計できる",
            },
        },
        "data_structures": {
            "questions": [
                "配列とリンクリストの違いは何ですか？それぞれの長所と短所は？",
                "スタックとキューの違いを説明してください。実際のユースケースは？",
                "ハッシュテーブル（辞書/Map）の仕組みを説明してください。",
                "ツリー構造（二分木、B木など）について説明してください。",
            ],
            "evaluation_criteria": {
                "beginner": "基本的なデータ構造を使用できる",
                "intermediate": "適切なデータ構造を選択できる",
                "advanced": "カスタムデータ構造を実装できる",
                "expert": "パフォーマンスを考慮した設計ができる",
            },
        },
    }

    if assessment_type not in questions:
        return json.dumps({"error": f"Unknown assessment type: {assessment_type}"})

    return json.dumps(questions[assessment_type], ensure_ascii=False, indent=2)


@tool
def assess_domain_aptitude(
    domains: str,
) -> str:
    """
    複数のエンジニアリング領域への適性を評価するツール。

    Args:
        domains: 評価する領域（カンマ区切り）
            例: "frontend,backend,devops,ml_engineering"

    Returns:
        各領域の評価質問と基準
    """
    domain_list = [d.strip() for d in domains.split(",")]

    domain_info = {
        "frontend": {
            "name": "フロントエンド開発",
            "questions": [
                "UIコンポーネントの設計で重視することは何ですか？",
                "ユーザー体験（UX）を向上させるためにどのような工夫をしますか？",
                "レスポンシブデザインの実装経験はありますか？",
                "フロントエンドのパフォーマンス最適化で行ったことは？",
            ],
            "key_skills": [
                "HTML/CSS",
                "JavaScript/TypeScript",
                "React/Vue/Angular",
                "状態管理",
            ],
            "aptitude_indicators": [
                "ビジュアルデザインへの関心",
                "ユーザー視点での思考",
                "細部へのこだわり",
            ],
        },
        "backend": {
            "name": "バックエンド開発",
            "questions": [
                "APIの設計で重視することは何ですか？",
                "データベースの設計経験について教えてください。",
                "マイクロサービスアーキテクチャについてどう思いますか？",
                "スケーラビリティを考慮した設計をしたことはありますか？",
            ],
            "key_skills": ["Python/Java/Go", "SQL/NoSQL", "API設計", "システム設計"],
            "aptitude_indicators": [
                "論理的思考力",
                "システム全体の理解",
                "パフォーマンスへの関心",
            ],
        },
        "devops": {
            "name": "DevOps/インフラ",
            "questions": [
                "CI/CDパイプラインの構築経験はありますか？",
                "コンテナ技術（Docker, Kubernetes）の経験は？",
                "クラウドサービス（AWS, GCP, Azure）の使用経験は？",
                "インフラのコード化（IaC）についてどう思いますか？",
            ],
            "key_skills": ["Docker/Kubernetes", "CI/CD", "クラウド", "自動化"],
            "aptitude_indicators": [
                "自動化への関心",
                "システム運用の理解",
                "セキュリティ意識",
            ],
        },
        "ml_engineering": {
            "name": "機械学習エンジニアリング",
            "questions": [
                "機械学習モデルの構築経験はありますか？",
                "データ前処理で重視することは何ですか？",
                "モデルの評価指標について説明してください。",
                "MLOpsについて知っていることを教えてください。",
            ],
            "key_skills": ["Python", "TensorFlow/PyTorch", "データ分析", "MLOps"],
            "aptitude_indicators": [
                "数学・統計への関心",
                "データドリブンな思考",
                "実験的なアプローチ",
            ],
        },
    }

    result = {}
    for domain in domain_list:
        if domain in domain_info:
            result[domain] = domain_info[domain]
        else:
            result[domain] = {"error": f"Unknown domain: {domain}"}

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def assess_technical_depth(
    domain: str,
    technologies: str,
) -> str:
    """
    選定領域の技術スタックでの深さを測定するツール。

    Args:
        domain: 評価対象の領域（frontend, backend, devops, ml_engineering）
        technologies: 評価する技術（カンマ区切り）
            例: "React,TypeScript,Next.js"

    Returns:
        各技術の詳細評価質問
    """
    tech_list = [t.strip() for t in technologies.split(",")]

    # 技術ごとの詳細評価
    tech_assessments = {
        # Frontend Technologies
        "React": {
            "category": "frontend",
            "questions": [
                "React Hooksをどのように活用していますか？useEffectの依存配列について説明してください。",
                "コンポーネントの再レンダリングを最適化する方法は？",
                "状態管理（Context API, Redux, Zustand等）の選択基準は？",
                "Server ComponentsとClient Componentsの違いは？",
            ],
            "levels": {
                "beginner": "基本的なコンポーネントを作成できる",
                "intermediate": "カスタムフックを作成し、状態管理ができる",
                "advanced": "パフォーマンス最適化、アーキテクチャ設計ができる",
            },
        },
        "TypeScript": {
            "category": "frontend/backend",
            "questions": [
                "ジェネリクスの使用例を説明してください。",
                "型ガードと型アサーションの違いは？",
                "ユーティリティ型（Partial, Pick, Omit等）の活用方法は？",
                "strictモードで特に重要な設定は何ですか？",
            ],
            "levels": {
                "beginner": "基本的な型定義ができる",
                "intermediate": "ジェネリクスと高度な型を使いこなせる",
                "advanced": "型システムを駆使した設計ができる",
            },
        },
        # Backend Technologies
        "Python": {
            "category": "backend",
            "questions": [
                "デコレータの仕組みを説明してください。",
                "非同期処理（asyncio）の使用経験は？",
                "型ヒントとmypyの活用について教えてください。",
                "メモリ管理とGCについて説明してください。",
            ],
            "levels": {
                "beginner": "基本的なスクリプトを書ける",
                "intermediate": "OOPとパッケージ管理ができる",
                "advanced": "非同期処理とパフォーマンス最適化ができる",
            },
        },
        "FastAPI": {
            "category": "backend",
            "questions": [
                "依存性注入（Depends）の使用方法を説明してください。",
                "Pydanticモデルのバリデーション機能について教えてください。",
                "バックグラウンドタスクの実装方法は？",
                "OpenAPI自動生成の仕組みについて説明してください。",
            ],
            "levels": {
                "beginner": "基本的なCRUD APIを作成できる",
                "intermediate": "認証・認可、ミドルウェアを実装できる",
                "advanced": "プロダクション品質のAPI設計ができる",
            },
        },
        # DevOps Technologies
        "Docker": {
            "category": "devops",
            "questions": [
                "マルチステージビルドの利点を説明してください。",
                "Docker Composeでの複数コンテナ管理の経験は？",
                "イメージサイズ最適化のテクニックは？",
                "コンテナのセキュリティベストプラクティスは？",
            ],
            "levels": {
                "beginner": "Dockerfileを書いてビルドできる",
                "intermediate": "Composeで複数サービスを管理できる",
                "advanced": "最適化されたプロダクション環境を構築できる",
            },
        },
        "Kubernetes": {
            "category": "devops",
            "questions": [
                "Pod、Deployment、Serviceの関係を説明してください。",
                "ConfigMapとSecretの使い分けは？",
                "水平スケーリング（HPA）の設定経験は？",
                "Helmチャートの作成経験はありますか？",
            ],
            "levels": {
                "beginner": "基本的なリソースをデプロイできる",
                "intermediate": "本番環境での運用ができる",
                "advanced": "クラスタ設計と最適化ができる",
            },
        },
    }

    result = {"domain": domain, "technologies": {}}

    for tech in tech_list:
        if tech in tech_assessments:
            result["technologies"][tech] = tech_assessments[tech]
        else:
            result["technologies"][tech] = {
                "category": "unknown",
                "questions": [
                    f"{tech}の使用経験年数を教えてください。",
                    f"{tech}で最も複雑なプロジェクトは何でしたか？",
                    f"{tech}のベストプラクティスで重視していることは？",
                ],
                "levels": {
                    "beginner": "基本的な使用ができる",
                    "intermediate": "実践的なプロジェクトで使用できる",
                    "advanced": "エキスパートレベルの知識がある",
                },
            }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def fetch_learning_resources(
    skill_level: Literal["beginner", "intermediate", "advanced"],
    topic: str,
    preferred_format: Literal["video", "text", "interactive", "project"],
) -> str:
    """
    学習者レベルに合わせたリソースを検索するツール。

    Args:
        skill_level: スキルレベル（beginner, intermediate, advanced）
        topic: 学習トピック
        preferred_format: 希望する学習形式（video, text, interactive, project）

    Returns:
        推奨学習リソースのリスト
    """
    # リソースデータベース（実際のプロダクションではDBや外部APIから取得）
    resources = {
        "Python": {
            "beginner": {
                "video": [
                    {
                        "name": "Python入門講座",
                        "provider": "Udemy",
                        "duration": "20時間",
                    },
                    {"name": "Python基礎", "provider": "YouTube", "duration": "10時間"},
                ],
                "text": [
                    {
                        "name": "Python公式チュートリアル",
                        "provider": "python.org",
                        "type": "documentation",
                    },
                    {"name": "みんなのPython", "provider": "書籍", "type": "book"},
                ],
                "interactive": [
                    {
                        "name": "Codecademy Python",
                        "provider": "Codecademy",
                        "type": "course",
                    },
                    {
                        "name": "Python Track",
                        "provider": "Exercism",
                        "type": "exercises",
                    },
                ],
                "project": [
                    {
                        "name": "TODO管理アプリ",
                        "difficulty": "easy",
                        "duration": "1週間",
                    },
                    {"name": "電卓アプリ", "difficulty": "easy", "duration": "3日"},
                ],
            },
            "intermediate": {
                "video": [
                    {
                        "name": "Python中級講座",
                        "provider": "Udemy",
                        "duration": "30時間",
                    },
                ],
                "text": [
                    {"name": "Effective Python", "provider": "書籍", "type": "book"},
                ],
                "interactive": [
                    {"name": "Python Koans", "provider": "GitHub", "type": "exercises"},
                ],
                "project": [
                    {
                        "name": "Web スクレイピングツール",
                        "difficulty": "medium",
                        "duration": "2週間",
                    },
                    {
                        "name": "REST API構築",
                        "difficulty": "medium",
                        "duration": "2週間",
                    },
                ],
            },
            "advanced": {
                "video": [
                    {
                        "name": "Python並行処理",
                        "provider": "PyCon",
                        "duration": "5時間",
                    },
                ],
                "text": [
                    {"name": "Fluent Python", "provider": "書籍", "type": "book"},
                ],
                "project": [
                    {
                        "name": "分散システム構築",
                        "difficulty": "hard",
                        "duration": "1ヶ月",
                    },
                ],
            },
        },
        "React": {
            "beginner": {
                "video": [
                    {
                        "name": "React完全入門",
                        "provider": "Udemy",
                        "duration": "25時間",
                    },
                ],
                "text": [
                    {
                        "name": "React公式ドキュメント",
                        "provider": "react.dev",
                        "type": "documentation",
                    },
                ],
                "interactive": [
                    {"name": "React Tutorial", "provider": "Scrimba", "type": "course"},
                ],
                "project": [
                    {
                        "name": "カウンターアプリ",
                        "difficulty": "easy",
                        "duration": "1日",
                    },
                    {"name": "TODOリスト", "difficulty": "easy", "duration": "3日"},
                ],
            },
            "intermediate": {
                "project": [
                    {
                        "name": "ECサイト構築",
                        "difficulty": "medium",
                        "duration": "3週間",
                    },
                ],
            },
            "advanced": {
                "project": [
                    {
                        "name": "リアルタイムチャットアプリ",
                        "difficulty": "hard",
                        "duration": "1ヶ月",
                    },
                ],
            },
        },
    }

    # デフォルトリソース
    default_resources = {
        "video": [
            {
                "name": f"{topic}入門動画",
                "provider": "YouTube/Udemy",
                "duration": "10-20時間",
            },
        ],
        "text": [
            {
                "name": f"{topic}公式ドキュメント",
                "provider": "Official",
                "type": "documentation",
            },
        ],
        "interactive": [
            {
                "name": f"{topic}インタラクティブコース",
                "provider": "Various",
                "type": "course",
            },
        ],
        "project": [
            {
                "name": f"{topic}実践プロジェクト",
                "difficulty": skill_level,
                "duration": "2週間",
            },
        ],
    }

    if topic in resources and skill_level in resources[topic]:
        topic_resources = resources[topic][skill_level]
        if preferred_format in topic_resources:
            result = {
                "topic": topic,
                "skill_level": skill_level,
                "format": preferred_format,
                "resources": topic_resources[preferred_format],
            }
        else:
            result = {
                "topic": topic,
                "skill_level": skill_level,
                "format": preferred_format,
                "resources": default_resources[preferred_format],
                "note": f"{preferred_format}形式のリソースが限られているため、一般的な推奨を表示しています。",
            }
    else:
        result = {
            "topic": topic,
            "skill_level": skill_level,
            "format": preferred_format,
            "resources": default_resources[preferred_format],
            "note": "特定のリソースが見つからないため、一般的な推奨を表示しています。",
        }

    return json.dumps(result, ensure_ascii=False, indent=2)
