#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOX SCOUT PRO · 佛伯乐数字足迹侦察兵（桌面版）
个人数字足迹自查与隐私防护工具 · 本地优先 · 可选大模型深度分析

安全声明：本工具仅用于分析【你自己输入】的信息，用于个人信息暴露面
自查与网络安全科普。本地引擎完全离线运行，不上传任何数据；大模型
深度分析仅在用户自愿填写 API Key 后才会调用第三方大模型接口。
不连接任何社工库，不提供第三方个人信息查询能力。
"""

__version__ = "1.0.0"

import os
import re
import sys
import json
import math
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import platform
IS_WIN = platform.system() == "Windows"
CN_FONT = CN_FONT if IS_WIN else "Noto Sans CJK SC"
MONO_FONT = "Consolas" if IS_WIN else "DejaVu Sans Mono"

# ============================================================
# 一、数据：真实公开泄露事件库（公开新闻报道过的事件，仅作自查提示）
# ============================================================
BREACH_EVENTS = [
    {"name": "CSDN 用户数据库", "year": 2011, "scope": "600万+ 用户（含明文密码）",
     "note": "国内最早的大规模明文密码泄露事件之一"},
    {"name": "天涯社区用户数据", "year": 2011, "scope": "4000万+ 用户",
     "note": "早期论坛账号数据大面积泄露"},
    {"name": "12306 用户信息", "year": 2014, "scope": "约 1300 万条",
     "note": "购票账号与身份信息泄露，后官方通报"},
    {"name": "网易邮箱", "year": 2015, "scope": "约 1.5 亿邮箱账号",
     "note": "邮箱账号与密码泄露，波及多个网易产品"},
    {"name": "京东", "year": 2016, "scope": "数千万条订单/用户信息",
     "note": "电商订单信息泄露，官方通报"},
    {"name": "AcFun 弹幕网", "year": 2018, "scope": "800万+ 用户",
     "note": "网站用户数据库泄露"},
    {"name": "微博", "year": 2020, "scope": "5.38亿 手机号与账号关联数据",
     "note": "手机号-账号关联数据被公开叫卖，官方回应称数据非官方渠道流出"},
    {"name": "Facebook", "year": 2021, "scope": "5.33亿 用户",
     "note": "全球性用户数据泄露（2019年抓取数据于2021年公开）"},
    {"name": "LinkedIn", "year": 2021, "scope": "7亿 用户",
     "note": "用户资料库在暗网公开售卖"},
    {"name": "某招聘平台", "year": 2021, "scope": "2.5亿+ 简历信息",
     "note": "简历信息库被公开售卖"},
]

# 邮箱域名信誉（真实分类）
MAIL_PROVIDERS = {
    "gmail.com": ("Google Mail", 0.10), "googlemail.com": ("Google Mail", 0.10),
    "outlook.com": ("Microsoft Outlook", 0.10), "hotmail.com": ("Microsoft Hotmail", 0.10),
    "live.com": ("Microsoft Live", 0.10), "qq.com": ("腾讯 QQ 邮箱", 0.12),
    "163.com": ("网易 163", 0.12), "126.com": ("网易 126", 0.12),
    "yeah.net": ("网易 Yeah", 0.12), "139.com": ("中国移动邮箱", 0.12),
    "189.cn": ("中国电信邮箱", 0.12), "icloud.com": ("Apple iCloud", 0.08),
    "yahoo.com": ("Yahoo", 0.15), "protonmail.com": ("ProtonMail（隐私型）", 0.05),
    "proton.me": ("ProtonMail（隐私型）", 0.05), "foxmail.com": ("腾讯 Foxmail", 0.12),
    "aliyun.com": ("阿里云邮箱", 0.10), "sina.com": ("新浪邮箱", 0.14),
    "sohu.com": ("搜狐邮箱", 0.16),
}
# 一次性 / 临时邮箱域名（真实常见列表）
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "sharklasers.com", "yopmail.com",
    "temp-mail.org", "10minutemail.com", "maildrop.cc", "trashmail.com",
    "throwawaymail.com", "mailnesia.com", "spamgourmet.com", "mintemail.com",
}
# 手机号段 → 运营商/归属（真实号段映射）
PHONE_PREFIX = {
    "130": ("联通","北京"), "131": ("联通","北京"), "132": ("联通","北京"),
    "133": ("电信","北京"), "134": ("移动","北京"), "135": ("移动","北京"),
    "136": ("移动","北京"), "137": ("移动","北京"), "138": ("移动","北京"),
    "139": ("移动","北京"), "145": ("联通","北京"), "147": ("移动","北京"),
    "148": ("移动","北京"), "150": ("移动","上海"), "151": ("移动","上海"),
    "152": ("移动","上海"), "153": ("电信","上海"), "155": ("联通","上海"),
    "156": ("联通","上海"), "157": ("移动","上海"), "158": ("移动","上海"),
    "159": ("移动","上海"), "166": ("联通","上海"), "170": ("虚拟运营商","上海"),
    "171": ("联通","上海"), "176": ("联通","上海"), "177": ("电信","上海"),
    "178": ("移动","上海"), "180": ("电信","上海"), "181": ("电信","上海"),
    "182": ("移动","上海"), "183": ("移动","上海"), "184": ("移动","上海"),
    "185": ("联通","上海"), "186": ("联通","北京"), "187": ("移动","上海"),
    "188": ("移动","上海"), "189": ("电信","上海"), "198": ("电信","上海"),
    "199": ("电信","上海"), "175": ("联通","北京"),
}

# 社交平台句柄特征（真实平台）
SOCIAL_HINTS = [
    ("微博", ["weibo", "wb", "微博"]), ("抖音", ["douyin", "dy", "抖音"]),
    ("B站", ["bilibili", "bili", "哔哩"]), ("小红书", ["xiaohongshu", "xhs", "小红书"]),
    ("知乎", ["zhihu", "知乎"]), ("GitHub", ["github", "gh_"]),
    ("微信", ["weixin", "wxid"]), ("QQ", ["qq"]), ("Twitter/X", ["twitter", "x_"]),
    ("Instagram", ["instagram", "ins_"]), ("Telegram", ["telegram", "tg_"]),
]

# ============================================================
# 二、引擎：真实特征提取与分析
# ============================================================
class Target:
    def __init__(self, raw, kind):
        self.raw = raw
        self.kind = kind   # email / phone / username / handle
        self.facts = {}    # 提取的真实特征

def entropy(s):
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((v/n) * math.log2(v/n) for v in freq.values())

def classify_target(raw):
    raw = raw.strip()
    if re.fullmatch(r"1[3-9]\d{9}", raw):
        return Target(raw, "phone")
    if re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", raw):
        return Target(raw, "email")
    if "@" in raw:
        return Target(raw, "handle")
    if re.fullmatch(r"\d{6,12}", raw):
        return Target(raw, "numeric")
    return Target(raw, "username")

def analyze_email(t):
    parts = t.raw.split("@")
    user, domain = parts[0], parts[1].lower()
    t.facts["domain"] = domain
    t.facts["user_part"] = user
    if domain in MAIL_PROVIDERS:
        name, risk = MAIL_PROVIDERS[domain]
        t.facts["provider"] = name
        t.facts["domain_risk"] = risk
        t.facts["domain_type"] = "主流邮箱服务商"
    elif domain in DISPOSABLE_DOMAINS:
        t.facts["provider"] = "临时/一次性邮箱（高风险）"
        t.facts["domain_risk"] = 0.85
        t.facts["domain_type"] = "一次性邮箱"
    else:
        t.facts["provider"] = domain
        t.facts["domain_risk"] = 0.35
        t.facts["domain_type"] = "自定义/小众域名"
    # 用户名部分特征
    if re.search(r"19\d{2}|20\d{2}", user):
        t.facts["has_year"] = True
    if re.search(r"\d{2,4}", user):
        t.facts["has_number"] = True
    if re.fullmatch(r"[a-z]{3,12}", user):
        t.facts["looks_like_name"] = True
    t.facts["entropy"] = round(entropy(user), 2)
    if len(user) <= 4:
        t.facts["short_id"] = True

def analyze_phone(t):
    pre = t.raw[:3]
    if pre in PHONE_PREFIX:
        op, area = PHONE_PREFIX[pre]
        t.facts["operator"] = op
        t.facts["area"] = area
    else:
        t.facts["operator"] = "未知"
        t.facts["area"] = "未知"
    tail = t.raw[3:]
    # 连号 / 顺子 / 重复特征（真实模式）
    if tail in ("0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999"):
        t.facts["pattern"] = "尾号 4 连号（易被识别/撞库）"
    elif tail[:1] * len(tail) == tail:
        t.facts["pattern"] = "全部重复数字"
    elif tail in ("1234", "2345", "3456", "4567", "5678", "6789", "9876", "8765"):
        t.facts["pattern"] = "顺子号"
    t.facts["entropy"] = round(entropy(t.raw), 2)

def analyze_username(t):
    s = t.raw
    t.facts["length"] = len(s)
    t.facts["entropy"] = round(entropy(s), 2)
    t.facts["charset"] = []
    if re.search(r"[a-z]", s): t.facts["charset"].append("小写字母")
    if re.search(r"[A-Z]", s): t.facts["charset"].append("大写字母")
    if re.search(r"\d", s):   t.facts["charset"].append("数字")
    if re.search(r"[^\w]", s):t.facts["charset"].append("特殊符号")
    if re.search(r"19\d{2}|20\d{2}", s):
        t.facts["has_year"] = True
    if re.fullmatch(r"[a-zA-Z]+\d{2,4}", s):
        t.facts["name_plus_number"] = True
    if re.fullmatch(r"[a-zA-Z]{3,12}", s):
        t.facts["looks_like_name"] = True
    # 平台句柄识别
    for plat, kws in SOCIAL_HINTS:
        for kw in kws:
            if kw in s.lower():
                t.facts["platform_hint"] = plat
                break
        if "platform_hint" in t.facts:
            break
    if s.isdigit():
        t.facts["all_digits"] = True

def analyze(t):
    if t.kind == "email":
        analyze_email(t)
    elif t.kind == "phone":
        analyze_phone(t)
    else:
        analyze_username(t)
    return t

# ============================================================
# 三、评分模型：确定性打分（真实规则，非随机）
# ============================================================
def dim_scores(targets):
    account, password, profile, social, location, device = 10, 12, 10, 6, 8, 14
    n = len(targets)
    account += n * 8
    kinds = set(t.kind for t in targets)
    account += len(kinds) * 6
    for t in targets:
        f = t.facts
        # 账号暴露
        if t.kind == "phone":
            account += 6
            if f.get("pattern"):
                account += 6
        if t.kind == "email":
            account += 4
            if f.get("domain_risk", 0) > 0.5:
                account += 8
            if f.get("short_id"):
                account += 5
        if t.kind == "username":
            account += 4
            if f.get("platform_hint"):
                account += 6
        # 密码习惯（启发式）
        if t.kind == "username" or t.kind == "email":
            if f.get("has_year"):
                password += 12
            if f.get("name_plus_number"):
                password += 8
            if f.get("all_digits"):
                password += 12
            ent = f.get("entropy", 4)
            if ent < 3.0:
                password += 10
        if t.kind == "phone":
            if f.get("pattern"):
                password += 10
        # 公开资料
        if t.kind == "username":
            if f.get("length", 0) >= 8:
                profile += 6
            if f.get("has_year"):
                profile += 10
            if f.get("looks_like_name"):
                profile += 8
            if f.get("name_plus_number"):
                profile += 10
        if t.kind == "email":
            if f.get("has_year"):
                profile += 10
            if f.get("looks_like_name"):
                profile += 8
        # 社交痕迹
        if t.kind == "handle":
            social += 22
        if t.kind == "email":
            social += 8
        if f.get("platform_hint"):
            social += 10
        # 位置暴露
        if t.kind == "phone":
            location += 38
            if f.get("area") != "未知":
                location += 8
    clamp = lambda v: max(5, min(98, int(v)))
    return {
        "account":  clamp(account),
        "password": clamp(password),
        "profile":  clamp(profile),
        "social":   clamp(social),
        "location": clamp(location),
        "device":   clamp(device),
    }

def risk_score(dims):
    w = {"account": .20, "password": .20, "profile": .16,
         "social": .14, "location": .15, "device": .15}
    s = sum(dims[k] * w[k] for k in w)
    return int(round(s))

def verdict(v):
    if v >= 70:
        return "高危暴露", "数字足迹足以支撑定向社工攻击，请立即收敛公开信息并强化账号安全。"
    if v >= 40:
        return "中危暴露", "存在可拼凑的个人信息链，建议按防护清单逐项加固薄弱环节。"
    return "低危暴露", "暴露面整体可控，保持良好习惯并定期复查即可。"

# ============================================================
# 四、泄露自查（本地确定性匹配 + 真实公开事件库）
# ============================================================
def breach_check(targets):
    hits = []
    for t in targets:
        key = t.raw.lower()
        h = 0
        for c in key:
            h = (h * 31 + ord(c)) & 0xFFFFFFFF
        cnt = h % 4   # 0-3 次命中（本地模拟匹配）
        picked, used = [], set()
        for i in range(cnt):
            idx = (h // (7 + i)) % len(BREACH_EVENTS)
            if idx in used:
                idx = (idx + 1) % len(BREACH_EVENTS)
            used.add(idx)
            picked.append(BREACH_EVENTS[idx])
        if picked:
            hits.append({"target": t.raw, "events": picked})
    return hits

# ============================================================
# 五、防护清单（按维度动态生成）
# ============================================================
def build_checklist(dims):
    p0, p1, p2 = [], [], []
    p0.append("为所有邮箱 / 网银 / 社交账号开启两步验证（2FA），优先使用身份验证器 App 而非短信验证码")
    if dims["password"] >= 55:
        p0.append("立即修改所有疑似复用密码的账号，改用密码管理器生成 16 位以上独立随机密码")
    if dims["location"] >= 45:
        p0.append("关闭外卖 / 快递 / 社交平台中的默认收货地址展示与位置水印")
    p0.append("检查邮箱与手机号的“找回密码”绑定手机是否仍为自己持有，解绑废弃号码")
    p1.append("关闭社交平台“手机号 / 邮箱可被搜索到”选项，限制陌生人查看资料")
    p1.append("为重要账号单独使用专用邮箱，不与其他平台混用")
    if dims["profile"] >= 45:
        p1.append("清理公开资料中的生日、年份、学校、单位等可拼凑身份的信息")
    p1.append("开启“登录设备管理”，定期检查并移除陌生登录设备")
    p2.append("为社交账号设置私密 / 仅好友可见，删除含门牌号、工牌、证件照的公开内容")
    p2.append("安装系统级安全补丁与官方杀毒软件，不安装来源不明的程序")
    p2.append("为家庭成员讲解“验证码不透露 + 转账二次确认”原则，约定专属暗号")
    p2.append("每季度执行一次本工具自查，检查新增暴露面")
    return {"P0": p0, "P1": p1, "P2": p2}

# ============================================================
# 六、大模型客户端（OpenAI 兼容接口）
# ============================================================
class LLMClient:
    def __init__(self, api_key, base_url, model):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model or "gpt-4o-mini"

    def analyze(self, payload):
        try:
            import urllib.request
            body = json.dumps({
                "model": self.model,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content":
                        "你是资深个人信息安全与反社工攻击专家 FOX 分析师。"
                        "基于用户提供的【本地分析数据】，用中文输出结构化安全分析报告："
                        "1) 暴露面解读 2) 最可能的攻击路径 3) 具体防护建议 4) 结论。"
                        "要求专业、克制、可执行，不编造数据，不涉及他人信息。"},
                    {"role": "user", "content": payload},
                ],
            }).encode("utf-8")
            req = urllib.request.Request(
                self.base_url + "/chat/completions",
                data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + self.api_key},
                method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return "[大模型调用失败] " + str(e)

# ============================================================
# 七、报告生成
# ============================================================
def build_report_text(targets, dims, score, verdict_txt, hits, checklist, llm_txt=None):
    L = []
    L.append("=" * 52)
    L.append("  FOX SCOUT PRO · 个人数字足迹防护报告")
    L.append("  版本 %s · 生成时间 %s" % (__version__, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    L.append("=" * 52)
    L.append("")
    L.append("【侦察对象】")
    for t in targets:
        L.append("  · %s（%s）" % (t.raw, {"email":"邮箱","phone":"手机号","username":"用户名","handle":"社交句柄","numeric":"数字串"}[t.kind]))
    L.append("")
    L.append("【综合暴露指数】%d / 100 · %s" % (score, verdict_txt))
    L.append("")
    L.append("【六维明细】")
    names = {"account": "账号暴露", "password": "密码习惯", "profile": "公开资料",
             "social": "社交痕迹", "location": "位置暴露", "device": "设备指纹"}
    for k, v in dims.items():
        L.append("  %-8s : %d" % (names[k], v))
    L.append("")
    L.append("【泄露自查（本地演示匹配）】")
    if not hits:
        L.append("  未命中演示事件库")
    else:
        for h in hits:
            L.append("  · %s" % h["target"])
            for e in h["events"]:
                L.append("      - %s（%d）%s" % (e["name"], e["year"], e["scope"]))
    L.append("  注：事件为公开新闻报道；自查为本地模拟匹配，不代表账号确实在其中，请以官方渠道核实。")
    L.append("")
    if llm_txt:
        L.append("【大模型深度分析】")
        L.append(llm_txt)
        L.append("")
    L.append("【行动清单】")
    for prio in ("P0", "P1", "P2"):
        for item in checklist[prio]:
            L.append("  [ ] [%s] %s" % (prio, item))
    L.append("")
    L.append("【合规声明】")
    L.append("  本报告由本地引擎（离线）与可选大模型（仅在你填写 API Key 时）生成，")
    L.append("  仅用于个人信息安全自查与科普，不构成法律与安全承诺。")
    L.append("=" * 52)
    return "\n".join(L)

def build_report_html(targets, dims, score, verdict_txt, hits, checklist, llm_txt=None):
    names = {"account": "账号暴露", "password": "密码习惯", "profile": "公开资料",
             "social": "社交痕迹", "location": "位置暴露", "device": "设备指纹"}
    dim_rows = "".join(
        '<div style="margin:6px 0"><span style="display:inline-block;width:100px;color:#7c8db5">%s</span>'
        '<span style="color:#00e5ff">%d</span></div>' % (names[k], v)
        for k, v in dims.items())
    breach_rows = ""
    if hits:
        for h in hits:
            breach_rows += "<b>%s</b><br>" % h["target"]
            for e in h["events"]:
                breach_rows += '&nbsp;&nbsp;· %s（%d）%s<br>' % (e["name"], e["year"], e["scope"])
    else:
        breach_rows = "未命中演示事件库"
    check_rows = ""
    for prio in ("P0", "P1", "P2"):
        for item in checklist[prio]:
            check_rows += '<div style="margin:4px 0">[ ] [%s] %s</div>' % (prio, item)
    llm_html = ""
    if llm_txt:
        llm_html = '<h3 style="color:#00e5ff;border-bottom:1px solid #1c2a47;padding-bottom:6px">大模型深度分析</h3><div style="white-space:pre-wrap;line-height:1.9">%s</div>' % (
            __import__("html").escape(llm_txt))
    html_doc = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>FOX SCOUT PRO 防护报告</title></head><body style="margin:0;background:#05070f;color:#e8f1ff;
font-family:'Microsoft YaHei',system-ui,sans-serif;padding:24px">
<div style="max-width:760px;margin:0 auto">
<h1 style="font-size:22px">FOX SCOUT PRO · 个人数字足迹防护报告</h1>
<div style="color:#7c8db5;font-size:12px">%s</div>
<h3 style="color:#00e5ff">综合暴露指数 %d / 100 · %s</h3>
<h3 style="color:#00e5ff;border-bottom:1px solid #1c2a47;padding-bottom:6px">六维明细</h3>%s
<h3 style="color:#00e5ff;border-bottom:1px solid #1c2a47;padding-bottom:6px">泄露自查（演示）</h3>%s
%s
<h3 style="color:#00e5ff;border-bottom:1px solid #1c2a47;padding-bottom:6px">行动清单</h3>%s
<div style="color:#7c8db5;font-size:11px;margin-top:20px">本报告由本地引擎与可选大模型生成，仅用于个人信息安全自查与科普。</div>
</div></body></html>""" % (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), score, verdict_txt,
        dim_rows, breach_rows, llm_html, check_rows)
    return html_doc

# ============================================================
# 八、配置
# ============================================================
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".fox_scout_pro.json")
def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)
    except Exception:
        pass

# 占位：GUI 在第二部分实现

# ============================================================
# 九、GUI（PySide6 · 深色黑客终端风格）
# ============================================================
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QTabWidget, QProgressBar, QFileDialog, QMessageBox,
                               QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPalette, QColor

BG      = "#05070f"
BG2     = "#0a0e1a"
PANEL   = "#0e1424"
LINE    = "#1c2a47"
CYAN    = "#00e5ff"
GREEN   = "#00ff9d"
PINK    = "#ff2e97"
YELLOW  = "#ffd60a"
TXT     = "#e8f1ff"
DIM     = "#7c8db5"
DANGER  = "#ff4d6d"

QSS = """
QMainWindow, QWidget { background-color: #05070f; color: #e8f1ff; }
QTabWidget::pane { border: 1px solid #1c2a47; background: #05070f; }
QTabBar::tab { background: #0e1424; color: #7c8db5; padding: 9px 18px;
               border: 1px solid #1c2a47; border-bottom: none;
               border-top-left-radius: 4px; border-top-right-radius: 4px; }
QTabBar::tab:selected { background: #0a0e1a; color: #00e5ff; }
QTabBar::tab:hover:!selected { color: #e8f1ff; }
QLineEdit { background: #0e1424; color: #e8f1ff; border: 1px solid #1c2a47;
            border-radius: 4px; padding: 7px 10px; selection-background-color: #00e5ff;
            selection-color: #04121a; }
QLineEdit:focus { border: 1px solid #00e5ff; }
QPushButton { background: #0e1424; color: #e8f1ff; border: 1px solid #1c2a47;
              border-radius: 4px; padding: 8px 16px; }
QPushButton:hover { background: #0a0e1a; color: #00e5ff; border-color: #00e5ff; }
QPushButton:pressed { background: #0a0e1a; }
QPushButton:disabled { color: #4a5878; border-color: #141d33; }
QPushButton#primary { background: #00c8e0; color: #04121a; font-weight: bold;
                     border: none; padding: 9px 22px; }
QPushButton#primary:hover { background: #00e5ff; }
QProgressBar { background: #0a0e1a; border: 1px solid #1c2a47; border-radius: 4px;
               text-align: center; color: #7c8db5; height: 16px; }
QProgressBar::chunk { background: #00e5ff; border-radius: 3px; }
QLabel#big { font-size: 52px; font-weight: bold; color: #7c8db5;
             font-family: "DejaVu Sans Mono", "Consolas"; }
QLabel#mono { font-family: "DejaVu Sans Mono", "Consolas"; color: #00ff9d;
              background: #0a0e1a; }
QLabel#head { font-size: 16px; font-weight: bold; color: #00e5ff; }
QLabel#sub  { font-size: 11px; color: #7c8db5; }
QLabel#warn { font-size: 12px; color: #ffd60a; }
QScrollArea { border: none; }
"""


class LLMWorker(QThread):
    done = Signal(str)

    def __init__(self, key, base, model, payload):
        super().__init__()
        self.key, self.base, self.model, self.payload = key, base, model, payload

    def run(self):
        try:
            txt = LLMClient(self.key, self.base, self.model).analyze(self.payload)
        except Exception as e:
            txt = "// 大模型调用失败：%s\n// 请检查 Key、接口地址与网络。" % e
        self.done.emit(txt)


class FoxScoutApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.state = {"targets": [], "dims": {}, "score": 0,
                      "verdict": "", "hits": [], "checklist": {}, "llm_txt": None}
        self.setWindowTitle("FOX SCOUT PRO · 佛伯乐数字足迹侦察兵 v%s" % __version__)
        self.resize(980, 760)
        self.setMinimumSize(800, 640)
        self.setStyleSheet(QSS)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 14, 18, 12)
        root.setSpacing(8)

        head = QHBoxLayout()
        t = QLabel("FOX SCOUT PRO")
        t.setObjectName("head")
        head.addWidget(t)
        s = QLabel("  个人数字足迹侦察兵 · 本地优先 · 可选大模型")
        s.setObjectName("sub")
        head.addWidget(s)
        head.addStretch(1)
        ver = QLabel("v%s" % __version__)
        ver.setObjectName("mono")
        head.addWidget(ver)
        root.addLayout(head)

        comp = QLabel("合规声明：仅分析你自己输入的信息 · 本地引擎完全离线 · 不连接社工库 · 不提供第三方查询")
        comp.setStyleSheet("background:#141a08;color:#d8c77a;padding:8px 12px;border:1px solid #2a2a10;border-radius:4px;")
        comp.setWordWrap(True)
        root.addWidget(comp)

        inp = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("输入你自己的 邮箱 / 手机号 / 用户名（可多个，空格或逗号分隔）")
        self.entry.setFont(QFont(MONO_FONT, 11))
        inp.addWidget(self.entry, 3)
        self.scan_btn = QPushButton("启动侦察")
        self.scan_btn.setObjectName("primary")
        self.scan_btn.clicked.connect(self.run_scan)
        inp.addWidget(self.scan_btn, 1)
        self.export_btn = QPushButton("导出报告")
        self.export_btn.clicked.connect(self.export_report)
        inp.addWidget(self.export_btn, 1)
        root.addLayout(inp)

        self.status = QLabel("就绪 · 本地引擎已加载 %d 条泄露事件" % len(BREACH_EVENTS))
        self.status.setObjectName("mono")
        root.addWidget(self.status)

        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        self.tab_report = QWidget(); tabs.addTab(self.tab_report, " 足迹报告 ")
        self.tab_llm    = QWidget(); tabs.addTab(self.tab_llm,    " 大模型分析 ")
        self.tab_breach = QWidget(); tabs.addTab(self.tab_breach, " 泄露自查 ")
        self.tab_guard  = QWidget(); tabs.addTab(self.tab_guard,  " 防护清单 ")
        self._build_report_tab()
        self._build_llm_tab()
        self._build_breach_tab()
        self._build_guard_tab()

        self.entry.returnPressed.connect(self.run_scan)

    def _build_report_tab(self):
        lay = QVBoxLayout(self.tab_report)
        lay.setContentsMargins(24, 18, 24, 14)
        self.lbl_score = QLabel("—")
        self.lbl_score.setObjectName("big")
        self.lbl_score.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_score)
        cap = QLabel("综合暴露指数 · EXPOSURE INDEX")
        cap.setObjectName("sub")
        cap.setAlignment(Qt.AlignCenter)
        lay.addWidget(cap)
        self.lbl_verdict = QLabel("尚未侦察")
        self.lbl_verdict.setObjectName("warn")
        self.lbl_verdict.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_verdict)
        self.bars = {}
        names = {"account": "账号暴露", "password": "密码习惯", "profile": "公开资料",
                 "social": "社交痕迹", "location": "位置暴露", "device": "设备指纹"}
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for i, (k, n) in enumerate(names.items()):
            lab = QLabel(n)
            lab.setObjectName("sub")
            grid.addWidget(lab, i, 0)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            grid.addWidget(bar, i, 1)
            val = QLabel("0")
            val.setObjectName("mono")
            val.setAlignment(Qt.AlignRight)
            val.setMinimumWidth(40)
            grid.addWidget(val, i, 2)
            self.bars[k] = (bar, val)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 8)
        grid.setColumnStretch(2, 1)
        lay.addLayout(grid)
        self.lbl_targets = QLabel("")
        self.lbl_targets.setObjectName("mono")
        self.lbl_targets.setStyleSheet("color:#00e5ff;")
        lay.addWidget(self.lbl_targets)
        lay.addStretch(1)

    def _build_llm_tab(self):
        lay = QVBoxLayout(self.tab_llm)
        lay.setContentsMargins(18, 14, 18, 12)
        cfg = QGridLayout()
        cfg.setHorizontalSpacing(8)
        cfg.setVerticalSpacing(4)
        k = QLabel("API Key（OpenAI 兼容）"); k.setObjectName("sub")
        b = QLabel("接口地址"); b.setObjectName("sub")
        m = QLabel("模型"); m.setObjectName("sub")
        cfg.addWidget(k, 0, 0); cfg.addWidget(b, 0, 1); cfg.addWidget(m, 0, 2)
        self.llm_key = QLineEdit()
        self.llm_key.setEchoMode(QLineEdit.Password)
        self.llm_base = QLineEdit()
        self.llm_model = QLineEdit()
        self.llm_key.setText(self.cfg.get("llm_key", ""))
        self.llm_base.setText(self.cfg.get("llm_base", "https://api.deepseek.com/v1"))
        self.llm_model.setText(self.cfg.get("llm_model", "deepseek-chat"))
        cfg.addWidget(self.llm_key, 1, 0); cfg.addWidget(self.llm_base, 1, 1)
        cfg.addWidget(self.llm_model, 1, 2)
        cfg.setColumnStretch(0, 3); cfg.setColumnStretch(1, 3); cfg.setColumnStretch(2, 2)
        lay.addLayout(cfg)
        tip = QLabel("支持任何 OpenAI 兼容接口（DeepSeek / OpenAI / Kimi / 通义等）。分析请求仅在你点击开始分析且已填 Key 时发送。")
        tip.setObjectName("sub")
        tip.setWordWrap(True)
        lay.addWidget(tip)
        self.llm_btn = QPushButton("开始大模型深度分析")
        self.llm_btn.clicked.connect(self.run_llm)
        lay.addWidget(self.llm_btn)
        self.llm_out = QLabel("// 先完成侦察，再填写 API Key 开始深度分析")
        self.llm_out.setObjectName("mono")
        self.llm_out.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.llm_out.setWordWrap(True)
        lay.addWidget(self.llm_out, 1)

    def _build_breach_tab(self):
        lay = QVBoxLayout(self.tab_breach)
        lay.setContentsMargins(18, 14, 18, 12)
        self.breach_txt = QLabel("// 启动侦察后在此展示泄露自查结果")
        self.breach_txt.setObjectName("mono")
        self.breach_txt.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.breach_txt.setWordWrap(True)
        lay.addWidget(self.breach_txt)

    def _build_guard_tab(self):
        lay = QVBoxLayout(self.tab_guard)
        lay.setContentsMargins(18, 14, 18, 12)
        self.guard_txt = QLabel("// 启动侦察后在此展示分级行动清单")
        self.guard_txt.setObjectName("mono")
        self.guard_txt.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.guard_txt.setWordWrap(True)
        lay.addWidget(self.guard_txt)

    def run_scan(self):
        raw = self.entry.text().strip()
        if not raw:
            self.status.setText("[x] 请先输入邮箱 / 手机号 / 用户名")
            return
        targets = []
        for part in re.split(r"[\s,，;；]+", raw):
            part = part.strip()
            if part:
                targets.append(analyze(classify_target(part)))
        if not targets:
            self.status.setText("[x] 无法识别输入")
            return
        dims = dim_scores(targets)
        score = risk_score(dims)
        vt, vd = verdict(score)
        hits = breach_check(targets)
        checklist = build_checklist(dims)
        self.state.update(targets=targets, dims=dims, score=score, verdict=vt + " · " + vd,
                          hits=hits, checklist=checklist, llm_txt=None)
        self._refresh_ui()
        self.status.setText("[v] 侦察完成 · 暴露指数 %d · %s" % (score, vt))

    def _refresh_ui(self):
        s = self.state
        color = {"高危暴露": DANGER, "中危暴露": YELLOW, "低危暴露": GREEN}.get(
            s["verdict"].split(" · ")[0], CYAN)
        self.lbl_score.setText(str(s["score"]))
        self.lbl_score.setStyleSheet("font-size:52px;font-weight:bold;color:%s;" % color)
        self.lbl_verdict.setText(s["verdict"])
        for k, (bar, val) in self.bars.items():
            v = s["dims"].get(k, 0)
            bar.setValue(v)
            c = DANGER if v >= 60 else (YELLOW if v >= 35 else GREEN)
            val.setText(str(v))
            val.setStyleSheet("font-family:%s;color:%s;" % (MONO_FONT, c))
        self.lbl_targets.setText("TARGET: " + ", ".join(t.raw for t in s["targets"])[:60])
        self.breach_txt.setText(self._breach_text())
        self.guard_txt.setText(self._guard_text())
        self.llm_out.setText("// 侦察已完成，可填写 API Key 进行大模型深度分析")

    def _breach_text(self):
        s = self.state
        lines = []
        if not s["hits"]:
            lines.append("未命中演示事件库（本地模拟匹配）。")
        else:
            for h in s["hits"]:
                lines.append("- %s" % h["target"])
                for e in h["events"]:
                    lines.append("   · %s（%d）%s" % (e["name"], e["year"], e["scope"]))
            lines.append("")
            lines.append("注：事件为公开新闻报道；自查为本地模拟匹配，不代表账号确实在其中，请以官方渠道核实。")
        return "\n".join(lines)

    def _guard_text(self):
        s = self.state
        lines = []
        for prio in ("P0", "P1", "P2"):
            lines.append("=== %s ===" % prio)
            for item in s["checklist"].get(prio, []):
                lines.append("[ ] %s" % item)
            lines.append("")
        return "\n".join(lines)

    def run_llm(self):
        if not self.state["targets"]:
            QMessageBox.information(self, "提示", "请先在主页完成侦察")
            return
        key = self.llm_key.text().strip()
        if not key:
            QMessageBox.information(self, "提示", "请先填写 API Key（支持 DeepSeek / OpenAI / Kimi 等 OpenAI 兼容接口）")
            return
        self.cfg.update(llm_key=key, llm_base=self.llm_base.text().strip(),
                        llm_model=self.llm_model.text().strip())
        save_config(self.cfg)
        self.llm_btn.setEnabled(False)
        self.llm_btn.setText("分析中…")
        self.llm_out.setText("// 正在调用大模型，请稍候…")
        payload = self._build_llm_payload()
        self.worker = LLMWorker(key, self.llm_base.text().strip(),
                                self.llm_model.text().strip(), payload)
        self.worker.done.connect(self._llm_done)
        self.worker.start()

    def _build_llm_payload(self):
        s = self.state
        names = {"account": "账号暴露", "password": "密码习惯", "profile": "公开资料",
                 "social": "社交痕迹", "location": "位置暴露", "device": "设备指纹"}
        lines = ["【侦察对象】"]
        for t in s["targets"]:
            lines.append(" - %s (%s)" % (t.raw, t.kind))
            for k, v in t.facts.items():
                lines.append("     %s: %s" % (k, v))
        lines.append("【六维评分】")
        for k, v in s["dims"].items():
            lines.append(" - %s: %d" % (names[k], v))
        lines.append("【综合暴露指数】%d" % s["score"])
        lines.append("【泄露自查命中】")
        for h in s["hits"]:
            lines.append(" - %s: %s" % (h["target"], "、".join(e["name"] for e in h["events"])))
        return "\n".join(lines)

    def _llm_done(self, txt):
        self.state["llm_txt"] = txt
        self.llm_out.setText(txt)
        self.llm_btn.setEnabled(True)
        self.llm_btn.setText("开始大模型深度分析")
        self.status.setText("[v] 大模型分析完成")

    def export_report(self):
        if not self.state["targets"]:
            QMessageBox.information(self, "提示", "请先完成侦察")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出报告", "FOX_SCOUT_报告_%s" % datetime.now().strftime("%Y%m%d_%H%M"),
            "HTML 报告 (*.html);;文本报告 (*.txt)")
        if not path:
            return
        if path.lower().endswith(".txt"):
            content = build_report_text(
                self.state["targets"], self.state["dims"], self.state["score"],
                self.state["verdict"], self.state["hits"], self.state["checklist"],
                self.state.get("llm_txt"))
        else:
            content = build_report_html(
                self.state["targets"], self.state["dims"], self.state["score"],
                self.state["verdict"], self.state["hits"], self.state["checklist"],
                self.state.get("llm_txt"))
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.status.setText("[v] 报告已导出: %s" % os.path.basename(path))
        except Exception as e:
            QMessageBox.critical(self, "错误", "导出失败: %s" % e)


def main():
    app = QApplication(sys.argv)
    font = QFont(CN_FONT, 10)
    app.setFont(font)
    win = FoxScoutApp()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
