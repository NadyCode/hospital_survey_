"""
アンケートのデータモデル
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import uuid

# 設問タイプ
QUESTION_TYPES = {
    "radio": "単一選択（ラジオボタン）",
    "checkbox": "複数選択（チェックボックス）",
    "dropdown": "ドロップダウンリスト",
    "text": "短文テキスト",
    "textarea": "長文テキスト",
    "scale": "評価スケール",
    "name_selector": "部署・氏名選択",
}


@dataclass
class BranchRule:
    """分岐ルール: condition_value の回答をした場合、jump_to_id の設問にジャンプ"""
    condition_value: str   # この値が回答された場合に分岐（checkboxの場合はカンマ区切り不可、値の1つ）
    jump_to_id: str        # ジャンプ先の設問ID（空文字列 = アンケート終了）

    def to_dict(self) -> dict:
        return {"condition_value": self.condition_value, "jump_to_id": self.jump_to_id}

    @staticmethod
    def from_dict(d: dict) -> "BranchRule":
        return BranchRule(
            condition_value=d.get("condition_value", ""),
            jump_to_id=d.get("jump_to_id", ""),
        )


@dataclass
class Question:
    """アンケートの1設問"""
    id: str
    type: str                      # QUESTION_TYPES のキー
    text: str                      # 設問文
    required: bool = False
    options: List[str] = field(default_factory=list)   # radio/checkbox/dropdown 用選択肢
    scale_min: int = 1
    scale_max: int = 5
    scale_min_label: str = ""
    scale_max_label: str = ""
    reference_file: str = ""       # 参照ファイル（PDFなど）のパス
    # テストモード用
    correct_answers: List[str] = field(default_factory=list)  # 正解（複数可）
    points: int = 1                # 配点
    # 分岐
    branches: List[BranchRule] = field(default_factory=list)
    # 表示条件（この設問が表示される条件。空ならば常に表示）
    show_if_question_id: str = ""
    show_if_value: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "required": self.required,
            "options": self.options,
            "scale_min": self.scale_min,
            "scale_max": self.scale_max,
            "scale_min_label": self.scale_min_label,
            "scale_max_label": self.scale_max_label,
            "reference_file": self.reference_file,
            "correct_answers": self.correct_answers,
            "points": self.points,
            "branches": [b.to_dict() for b in self.branches],
            "show_if_question_id": self.show_if_question_id,
            "show_if_value": self.show_if_value,
        }

    @staticmethod
    def from_dict(d: dict) -> "Question":
        return Question(
            id=d.get("id", str(uuid.uuid4())),
            type=d.get("type", "radio"),
            text=d.get("text", ""),
            required=d.get("required", False),
            options=d.get("options", []),
            scale_min=d.get("scale_min", 1),
            scale_max=d.get("scale_max", 5),
            scale_min_label=d.get("scale_min_label", ""),
            scale_max_label=d.get("scale_max_label", ""),
            reference_file=d.get("reference_file", ""),
            correct_answers=d.get("correct_answers", []),
            points=d.get("points", 1),
            branches=[BranchRule.from_dict(b) for b in d.get("branches", [])],
            show_if_question_id=d.get("show_if_question_id", ""),
            show_if_value=d.get("show_if_value", ""),
        )

    def new_id():
        return str(uuid.uuid4())[:8]


@dataclass
class Survey:
    """アンケート全体"""
    id: str
    title: str
    description: str = ""
    is_test_mode: bool = False
    pass_score: int = 60           # 合格点（%）
    show_correct_after: bool = True  # 終了後に正解を表示するか
    allow_multiple_answers: bool = False  # 同一ユーザーの複数回答を許可
    questions: List[Question] = field(default_factory=list)

    @property
    def total_points(self) -> int:
        return sum(q.points for q in self.questions if q.type not in ("name_selector",))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_test_mode": self.is_test_mode,
            "pass_score": self.pass_score,
            "show_correct_after": self.show_correct_after,
            "allow_multiple_answers": self.allow_multiple_answers,
            "questions": [q.to_dict() for q in self.questions],
        }

    @staticmethod
    def from_dict(d: dict) -> "Survey":
        return Survey(
            id=d.get("id", str(uuid.uuid4())),
            title=d.get("title", "無題のアンケート"),
            description=d.get("description", ""),
            is_test_mode=d.get("is_test_mode", False),
            pass_score=d.get("pass_score", 60),
            show_correct_after=d.get("show_correct_after", True),
            allow_multiple_answers=d.get("allow_multiple_answers", False),
            questions=[Question.from_dict(q) for q in d.get("questions", [])],
        )

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(path: str) -> "Survey":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return Survey.from_dict(d)

    def new_id():
        return str(uuid.uuid4())[:8]
