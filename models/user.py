"""
職員マスターデータモデル
"""
from dataclasses import dataclass
from typing import List, Dict
import csv
import os

from utils.file_lock import file_lock


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


def update_master_user(filepath: str, old_dept: str, old_name: str,
                       new_dept: str, new_name: str):
    """
    職員マスターの1件を修正する（共有フォルダ対応のためロック内で読み直して保存）。
    該当が見つからない場合は新規として追加する。
    """
    new_dept = new_dept.strip()
    new_name = new_name.strip()
    with file_lock(filepath):
        users = load_master_users(filepath)
        found = False
        for u in users:
            if u.department == old_dept and u.name == old_name:
                u.department = new_dept
                u.name = new_name
                found = True
                break
        if not found:
            users.append(StaffMember(department=new_dept, name=new_name))
        save_master_users(filepath, users)
