"""
回答データの読み書き・集計
"""
import os
import csv
import uuid
import datetime
from typing import List, Dict, Optional
from utils.file_lock import file_lock

ANSWER_HEADER_PREFIX = ["回答ID", "タイムスタンプ", "部署", "氏名", "端末名", "IPアドレス", "アンケートID"]


def _answers_file(shared_folder: str, survey_id: str) -> str:
    return os.path.join(shared_folder, f"answers_{survey_id}.csv")


def save_answer(shared_folder: str, survey_id: str, department: str, name: str,
                hostname: str, ip: str, answers: Dict[str, str]):
    """
    回答をCSVに追記する（排他制御付き）
    answers: {question_id: answer_value, ...}
    """
    filepath = _answers_file(shared_folder, survey_id)
    answer_id = str(uuid.uuid4())[:8]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with file_lock(filepath):
        file_exists = os.path.exists(filepath)
        existing_q_ids = []
        if file_exists:
            with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                existing_q_ids = header[len(ANSWER_HEADER_PREFIX):]

        # 設問IDを既存 + 新規でマージ
        all_q_ids = list(existing_q_ids)
        for qid in answers:
            if qid not in all_q_ids:
                all_q_ids.append(qid)

        new_header = ANSWER_HEADER_PREFIX + all_q_ids

        # 既存データを読み込み
        rows = []
        if file_exists and existing_q_ids:
            with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        # 新しい行
        new_row = {
            "回答ID": answer_id,
            "タイムスタンプ": now,
            "部署": department,
            "氏名": name,
            "端末名": hostname,
            "IPアドレス": ip,
            "アンケートID": survey_id,
        }
        for qid in all_q_ids:
            new_row[qid] = answers.get(qid, "")

        rows.append(new_row)

        # 全データを書き直す
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=new_header, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                # 不足フィールドは空文字
                for col in new_header:
                    row.setdefault(col, "")
                writer.writerow({col: row.get(col, "") for col in new_header})

    return answer_id


def load_answers(shared_folder: str, survey_id: str) -> List[Dict]:
    """回答データを全件読み込む"""
    filepath = _answers_file(shared_folder, survey_id)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def has_answered(shared_folder: str, survey_id: str, department: str, name: str) -> bool:
    """指定ユーザーが既に回答済みか確認"""
    answers = load_answers(shared_folder, survey_id)
    for row in answers:
        if row.get("部署") == department and row.get("氏名") == name:
            return True
    return False


def get_answered_users(shared_folder: str, survey_id: str) -> List[Dict]:
    """回答済みユーザーの一覧を返す"""
    answers = load_answers(shared_folder, survey_id)
    seen = {}
    for row in answers:
        key = (row.get("部署", ""), row.get("氏名", ""))
        seen[key] = row.get("タイムスタンプ", "")
    return [{"部署": k[0], "氏名": k[1], "回答日時": v} for k, v in seen.items()]


def aggregate_answers(shared_folder: str, survey_id: str, questions) -> Dict:
    """
    回答データを集計する
    戻り値: {question_id: {"type": ..., "text": ..., "counts": {...} or "values": [...]}}
    """
    answers = load_answers(shared_folder, survey_id)
    result = {}

    for q in questions:
        qid = q.id
        qtype = q.type
        col_values = [row.get(qid, "") for row in answers if row.get(qid, "") != ""]

        if qtype in ("radio", "dropdown"):
            counts = {}
            for v in col_values:
                counts[v] = counts.get(v, 0) + 1
            result[qid] = {"type": qtype, "text": q.text, "counts": counts,
                           "total": len(col_values), "options": q.options}

        elif qtype == "checkbox":
            counts = {}
            for v in col_values:
                for item in v.split("|||"):
                    item = item.strip()
                    if item:
                        counts[item] = counts.get(item, 0) + 1
            result[qid] = {"type": qtype, "text": q.text, "counts": counts,
                           "total": len(col_values), "options": q.options}

        elif qtype == "scale":
            numeric = []
            counts = {}
            for v in col_values:
                try:
                    n = int(v)
                    numeric.append(n)
                    counts[str(n)] = counts.get(str(n), 0) + 1
                except ValueError:
                    pass
            avg = sum(numeric) / len(numeric) if numeric else 0
            result[qid] = {"type": qtype, "text": q.text, "counts": counts,
                           "average": round(avg, 2), "total": len(numeric),
                           "scale_min": q.scale_min, "scale_max": q.scale_max}

        elif qtype in ("text", "textarea"):
            result[qid] = {"type": qtype, "text": q.text, "values": col_values,
                           "total": len(col_values)}

        elif qtype == "name_selector":
            counts = {}
            for v in col_values:
                counts[v] = counts.get(v, 0) + 1
            result[qid] = {"type": qtype, "text": q.text, "counts": counts,
                           "total": len(col_values)}

    return result


def export_answers_csv(shared_folder: str, survey_id: str, export_path: str):
    """回答データをエクスポート用CSVに書き出す"""
    import shutil
    src = _answers_file(shared_folder, survey_id)
    if os.path.exists(src):
        shutil.copy2(src, export_path)
        return True
    return False
