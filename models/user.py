"""
職員マスターデータモデル
"""
from dataclasses import dataclass
from typing import List, Dict
import csv
import os


@dataclass
class StaffMember:
    department: str
    name: str


def load_master_users(filepath: str) -> List[StaffMember]:
    """master_user.csv を読み込む"""
    users = []
    if not os.path.exists(filepath):
        return users
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dept = row.get("部署", row.get("department", "")).strip()
            name = row.get("氏名", row.get("name", "")).strip()
            if dept and name:
                users.append(StaffMember(department=dept, name=name))
    return users


def save_master_users(filepath: str, users: List[StaffMember]):
    """master_user.csv を保存する"""
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["部署", "氏名"])
        for u in users:
            writer.writerow([u.department, u.name])


def get_departments(users: List[StaffMember]) -> List[str]:
    seen = []
    for u in users:
        if u.department not in seen:
            seen.append(u.department)
    return seen


def get_names_for_department(users: List[StaffMember], department: str) -> List[str]:
    return [u.name for u in users if u.department == department]
