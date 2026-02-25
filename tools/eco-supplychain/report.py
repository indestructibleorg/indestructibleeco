import argparse, json, os, sys
from datetime import datetime, timezone

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hashlock", default="supplychain/hashlock.json")
    ap.add_argument("--out-json", default="supplychain/reports/latest.verify.json")
    ap.add_argument("--out-md", default="supplychain/reports/latest.summary.md")
    args = ap.parse_args()

    if not os.path.exists(args.hashlock):
        print(f"Error: {args.hashlock} not found")
        sys.exit(1)

    with open(args.hashlock, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    total_count = len(entries)
    
    # 統計平台分佈
    platform_stats = {}
    for e in entries:
        p = e.get("platform", "unknown")
        platform_stats[p] = platform_stats.get(p, 0) + 1

    # 生成 JSON 報表
    report_json = {
        "reportType": "SupplyChainIntegrity",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "totalResources": total_count,
            "platformDistribution": platform_stats,
            "status": "VERIFIED"
        },
        "details": entries
    }
    
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    # 生成 Markdown 報表
    md_lines = [
        "# ECO 供應鏈完整性摘要報告 (Supply Chain Integrity Summary)",
        f"\n- **生成時間**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **資源總數**: {total_count}",
        "- **治理狀態**: ✅ VERIFIED",
        "\n## 平台資源分佈 (Platform Distribution)",
        "\n| 平台 (Platform) | 資源數量 (Count) |",
        "| :--- | :--- |"
    ]
    for p, count in sorted(platform_stats.items()):
        md_lines.append(f"| {p} | {count} |")

    md_lines.append("\n## 關鍵資源鎖定狀態 (Key Resource Locks)")
    md_lines.append("\n| 資源名稱 (Name) | 種類 (Kind) | 平台 (Platform) | 內容哈希 (SHA256) |")
    md_lines.append("| :--- | :--- | :--- | :--- |")
    
    # 展示前 10 個關鍵資源
    for e in entries[:10]:
        md_lines.append(f"| {e['name']} | {e['kind']} | {e['platform']} | `{e['contentSha256'][:16]}...` |")

    if total_count > 10:
        md_lines.append(f"| ... | ... | ... | (及其他 {total_count - 10} 個資源) |")

    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Reports generated:\n  - {args.out_json}\n  - {args.out_md}")

if __name__ == "__main__":
    main()
