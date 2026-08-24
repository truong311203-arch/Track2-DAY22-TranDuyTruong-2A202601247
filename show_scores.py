import json
from pathlib import Path

report_path = Path("data/ragas_report.json")
if not report_path.exists():
    print("❌ Chưa tìm thấy file data/ragas_report.json")
    exit(1)

report = json.loads(report_path.read_text(encoding="utf-8"))
v1 = report["prompt_v1_scores"]
v2 = report["prompt_v2_scores"]

print("=" * 65)
print(f"  {'Metric':30s}  {'V1':>8}  {'V2':>8}  Winner")
print("=" * 65)
for metric in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
    s1, s2 = v1[metric], v2[metric]
    winner = "← V1" if s1 >= s2 else "← V2"
    print(f"  {metric:30s}  {s1:>8.4f}  {s2:>8.4f}  {winner}")
print("=" * 65)

best_faith = max(v1["faithfulness"], v2["faithfulness"])
if best_faith >= 0.8:
    print(f"\n✅ Đạt mục tiêu: faithfulness = {best_faith:.4f} ≥ 0.8")
else:
    print(f"\n⚠️  Chưa đạt mục tiêu ({best_faith:.4f} < 0.8)")

print(f"💾 Báo cáo đã lưu tại: data/ragas_report.json và evidence/03_ragas_report.json\n")
