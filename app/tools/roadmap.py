"""Roadmap generation tool for Learning Path Agent."""

import json
from typing import Optional
from datetime import datetime

from langchain_core.tools import tool


@tool
def generate_learning_roadmap(
    foundation_score: float,
    recommended_domain: str,
    technical_assessment: str,
    learning_style: str,
    available_hours_per_week: int,
) -> str:
    """
    全ての診断結果から最適な学習ロードマップを生成するツール。

    Args:
        foundation_score: 基礎スキルスコア（0-10）
        recommended_domain: 推奨されるエンジニアリング領域
        technical_assessment: 技術評価結果（JSON文字列）
        learning_style: 学習スタイル（project_based, video, text, interactive）
        available_hours_per_week: 週あたりの利用可能な学習時間

    Returns:
        - 3段階（短期3ヶ月、中期6ヶ月、長期1年）の学習計画
        - 各段階でのプロジェクト課題
        - 習得すべき技術スタック
        - 推奨学習リソース
    """
    # Parse technical assessment if it's a string
    try:
        tech_data = (
            json.loads(technical_assessment)
            if isinstance(technical_assessment, str)
            else technical_assessment
        )
    except json.JSONDecodeError:
        tech_data = {}

    # 領域ごとの技術スタック定義
    domain_stacks = {
        "backend": {
            "core": ["Python", "SQL", "REST API設計"],
            "intermediate": ["FastAPI/Django", "PostgreSQL", "Redis", "Docker"],
            "advanced": ["Kubernetes", "マイクロサービス", "システム設計", "パフォーマンス最適化"],
        },
        "frontend": {
            "core": ["HTML/CSS", "JavaScript", "TypeScript"],
            "intermediate": ["React/Vue", "状態管理", "テスト", "Tailwind CSS"],
            "advanced": ["Next.js", "パフォーマンス最適化", "アクセシビリティ", "モノレポ"],
        },
        "fullstack": {
            "core": ["HTML/CSS/JS", "Python/Node.js", "SQL"],
            "intermediate": ["React", "FastAPI/Express", "Docker"],
            "advanced": ["Next.js", "クラウド", "CI/CD"],
        },
        "devops": {
            "core": ["Linux", "シェルスクリプト", "Git"],
            "intermediate": ["Docker", "CI/CD", "クラウド基礎"],
            "advanced": ["Kubernetes", "IaC", "監視・ロギング", "セキュリティ"],
        },
        "ml_engineering": {
            "core": ["Python", "NumPy/Pandas", "統計基礎"],
            "intermediate": ["scikit-learn", "TensorFlow/PyTorch", "データ可視化"],
            "advanced": ["MLOps", "分散学習", "モデル最適化"],
        },
    }

    # 学習スタイルに応じたリソースタイプ
    resource_types = {
        "project_based": "ハンズオンプロジェクト中心",
        "video": "動画講座中心",
        "text": "ドキュメント・書籍中心",
        "interactive": "インタラクティブ演習中心",
    }

    # 基礎スコアに応じた開始レベル決定
    if foundation_score < 4:
        start_level = "beginner"
        focus_foundation = True
    elif foundation_score < 7:
        start_level = "intermediate"
        focus_foundation = False
    else:
        start_level = "advanced"
        focus_foundation = False

    # 週あたりの時間に応じた学習ペース調整
    if available_hours_per_week < 5:
        pace = "slow"
        duration_multiplier = 1.5
    elif available_hours_per_week < 15:
        pace = "moderate"
        duration_multiplier = 1.0
    else:
        pace = "intensive"
        duration_multiplier = 0.75

    # 領域の技術スタックを取得
    domain_key = recommended_domain.lower().replace(" ", "_")
    if domain_key not in domain_stacks:
        domain_key = "backend"  # デフォルト

    stack = domain_stacks[domain_key]

    # ロードマップ生成
    roadmap = {
        "summary": f"{recommended_domain}エンジニアを目指す学習ロードマップ",
        "created_at": datetime.now().isoformat(),
        "learner_profile": {
            "foundation_score": foundation_score,
            "start_level": start_level,
            "recommended_domain": recommended_domain,
            "learning_style": learning_style,
            "weekly_hours": available_hours_per_week,
            "pace": pace,
        },
        "phases": [
            {
                "phase": 1,
                "name": "基礎固め期間（1-3ヶ月目）",
                "duration_weeks": int(12 * duration_multiplier),
                "focus": stack["core"]
                if not focus_foundation
                else ["プログラミング基礎", "アルゴリズム", "データ構造"],
                "goals": [
                    "基礎的な概念の確実な理解",
                    "小規模なプロジェクトの完成",
                    "日常的なコーディング習慣の確立",
                ],
                "projects": [
                    {
                        "name": "基礎プロジェクト1",
                        "description": f"{recommended_domain}の基礎を学ぶシンプルなプロジェクト",
                        "skills": stack["core"][:2],
                        "duration": "2週間",
                    },
                    {
                        "name": "基礎プロジェクト2",
                        "description": "学んだ概念を組み合わせた小規模アプリ",
                        "skills": stack["core"],
                        "duration": "3週間",
                    },
                ],
                "milestones": [
                    "基礎文法とパラダイムの理解",
                    "バージョン管理（Git）の習得",
                    "最初のプロジェクト完成",
                ],
                "resources": [
                    {"type": resource_types.get(learning_style, "ハンズオン"), "priority": "high"},
                    {"type": "公式ドキュメント", "priority": "medium"},
                ],
            },
            {
                "phase": 2,
                "name": "実践力強化期間（4-6ヶ月目）",
                "duration_weeks": int(12 * duration_multiplier),
                "focus": stack["intermediate"],
                "goals": [
                    "実践的なフレームワーク・ツールの習得",
                    "中規模プロジェクトの設計と実装",
                    "テストの習慣化",
                ],
                "projects": [
                    {
                        "name": "実践プロジェクト",
                        "description": f"実際のユースケースを想定した{recommended_domain}アプリケーション",
                        "skills": stack["intermediate"],
                        "duration": "6週間",
                    },
                ],
                "milestones": [
                    "主要フレームワークの習得",
                    "データベース設計・操作のスキル獲得",
                    "ポートフォリオ作品の完成",
                ],
                "resources": [
                    {"type": "実践的なチュートリアル", "priority": "high"},
                    {"type": "オープンソースプロジェクトへの貢献", "priority": "medium"},
                ],
            },
            {
                "phase": 3,
                "name": "専門性深化期間（7-9ヶ月目）",
                "duration_weeks": int(12 * duration_multiplier),
                "focus": stack["advanced"][:2],
                "goals": [
                    "高度な技術スタックの習得",
                    "システム設計能力の向上",
                    "パフォーマンス最適化スキルの獲得",
                ],
                "projects": [
                    {
                        "name": "高度なプロジェクト",
                        "description": "スケーラブルで本番品質のアプリケーション",
                        "skills": stack["advanced"][:2],
                        "duration": "8週間",
                    },
                ],
                "milestones": [
                    "高度な設計パターンの理解と適用",
                    "本番環境を意識した開発",
                    "技術的な意思決定能力の向上",
                ],
                "resources": [
                    {"type": "技術書・アーキテクチャ関連", "priority": "high"},
                    {"type": "技術ブログ執筆", "priority": "medium"},
                ],
            },
            {
                "phase": 4,
                "name": "キャリア準備期間（10-12ヶ月目）",
                "duration_weeks": int(12 * duration_multiplier),
                "focus": stack["advanced"][1:] + ["面接準備", "ポートフォリオ強化"],
                "goals": [
                    "エキスパートレベルのスキル証明",
                    "強力なポートフォリオの構築",
                    "面接・技術試験への準備",
                ],
                "projects": [
                    {
                        "name": "キャップストーンプロジェクト",
                        "description": "すべてのスキルを統合した本格的なプロジェクト",
                        "skills": stack["core"] + stack["intermediate"] + stack["advanced"],
                        "duration": "継続的",
                    },
                ],
                "milestones": [
                    "完成度の高いポートフォリオ",
                    "技術面接での自信",
                    "継続的な学習習慣の確立",
                ],
                "resources": [
                    {"type": "面接対策・システム設計", "priority": "high"},
                    {"type": "コミュニティ活動", "priority": "medium"},
                ],
            },
        ],
        "weekly_schedule_suggestion": {
            "total_hours": available_hours_per_week,
            "distribution": {
                "理論学習": int(available_hours_per_week * 0.3),
                "コーディング演習": int(available_hours_per_week * 0.4),
                "プロジェクト開発": int(available_hours_per_week * 0.2),
                "復習・振り返り": int(available_hours_per_week * 0.1),
            },
        },
        "success_tips": [
            "毎日少しでもコードを書く習慣をつける",
            "わからないことは積極的に調べ、記録する",
            "他者のコードを読んで学ぶ",
            "完璧を求めすぎず、まず動くものを作る",
            "コミュニティに参加して仲間を見つける",
        ],
    }

    return json.dumps(roadmap, ensure_ascii=False, indent=2)
