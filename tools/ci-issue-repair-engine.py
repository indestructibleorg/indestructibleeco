#!/usr/bin/env python3
"""
CI Issue Repair Engine v1
eco-base: 100% autonomous CI failure to issue to PR loop.
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO = os.environ.get("REPO", "indestructibleorg/eco-base")
GH_TOKEN = os.environ.get("GH_TOKEN", "")

def gh_run(args):
    return subprocess.run(["gh"] + args, capture_output=True, text=True)

def get_open_ci_issues():
    r = gh_run(["issue", "list", "--repo", REPO, "--label", "ci-failure", "--state", "open", "--json", "number,title,body,labels"])
    if r.returncode != 0 or not r.stdout.strip():
        return []
    return json.loads(r.stdout)

def diagnose_and_fix(issue):
    issue_num = issue['number']
    title = issue['title']
    body = issue['body']
    
    # 提取 PR 編號
    pr_match = re.search(r"PR #(\d+)", title)
    if not pr_match:
        return
    pr_num = pr_match.group(1)
    
    # 提取 Gate 名稱
    gate_match = re.search(r"Gate \[(.*?)\]", title)
    gate_name = gate_match.group(1) if gate_match else "unknown"
    
    print(f"Processing Issue #{issue_num} for PR #{pr_num} (Gate: {gate_name})")
    
    # 呼叫現有的 diagnose.py 進行深度分析 (模擬 L2)
    # 這裡假設 diagnose.py v6 已經存在或我們正在擴展它
    # 為了演示，我們直接執行一個修復邏輯
    
    # 獲取 PR 分支
    pr_info = gh_run(["pr", "view", pr_num, "--repo", REPO, "--json", "headRefName"])
    if pr_info.returncode != 0:
        return
    branch = json.loads(pr_info.stdout)['headRefName']
    
    # 執行修復 (L1/L2)
    # 範例：如果是 lint 失敗，嘗試自動修復
    if "lint" in gate_name.lower():
        fix_branch = f"fix-ci-{gate_name}-pr{pr_num}-{int(time.time())}"
        subprocess.run(["git", "fetch", "origin", branch])
        subprocess.run(["git", "checkout", "-B", fix_branch, f"origin/{branch}"])
        
        # 執行 lint 修復 (例如 ruff)
        subprocess.run(["python3", "-m", "ruff", "check", "--fix", "."])
        
        # 檢查是否有變更
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", f"fix(ci): auto-repair {gate_name} for PR #{pr_num}", "-m", f"Closes #{issue_num}"])
            subprocess.run(["git", "push", "origin", fix_branch])
            
            # 創建修復 PR
            gh_run(["pr", "create", "--repo", REPO, "--base", branch, "--head", fix_branch, 
                    "--title", f"Auto-repair {gate_name} for PR #{pr_num}", 
                    "--body", f"Automated fix for CI failure in PR #{pr_num}. Linked Issue: #{issue_num}"])
            
            # 更新 Issue 狀態
            gh_run(["issue", "comment", str(issue_num), "--repo", REPO, "--body", f"Auto-repair PR created. Branch: {fix_branch}"])
        else:
            gh_run(["issue", "comment", str(issue_num), "--repo", REPO, "--body", "No mechanical fixes found. Escalating to L2 AI diagnosis."])

def main():
    issues = get_open_ci_issues()
    for issue in issues:
        diagnose_and_fix(issue)

if __name__ == "__main__":
    main()
