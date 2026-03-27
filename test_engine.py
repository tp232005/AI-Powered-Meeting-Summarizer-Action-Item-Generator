"""Quick test for the NLP engine, KB, and report generator."""
from nlp_engine import MeetingAnalyzer
from knowledge_base import KnowledgeBase
from report_generator import ReportGenerator

# Load sample
with open("samples/sample_meeting.txt", encoding="utf-8") as f:
    transcript = f.read()

# Run analysis
print("Running NLP analysis...")
analyzer = MeetingAnalyzer()
result = analyzer.analyze(transcript)

print(f"\n=== SHORT SUMMARY ===\n{result['short_summary'][:200]}")
print(f"\n=== DECISIONS ({len(result['decisions'])}) ===")
for d in result["decisions"]:
    print(f"  - {d[:80]}")
print(f"\n=== TASKS ({len(result['tasks'])}) ===")
for t in result["tasks"][:5]:
    print(f"  [{t['priority']}] {t['task'][:60]}... -> {t['assignee']} by {t['deadline']}")
print(f"\n=== TOPICS ({len(result['topics'])}) ===")
for t in result["topics"]:
    print(f"  {t['topic']}")
print(f"\n=== RISKS ({len(result['risks'])}) ===")
for r in result["risks"]:
    print(f"  [{r['severity']}] {r['description'][:70]}")
print(f"\n=== PARTICIPANTS ({len(result['participants'])}) ===")
for p in result["participants"]:
    print(f"  {p['name']}: {p['word_count']} words ({p['contribution_pct']}%) - {p['sentiment']['label']}")
ps = result["productivity_score"]
print(f"\n=== PRODUCTIVITY SCORE ===\n  Score: {ps['total']}/100 Grade: {ps['grade']} ({ps['label']})")
for k, v in ps["breakdown"].items():
    print(f"  {k}: {v}")

# Test Knowledge Base
print("\n=== KNOWLEDGE BASE TEST ===")
kb = KnowledgeBase(":memory:")
mid = kb.save("Test Meeting", transcript, result)
print(f"  Saved meeting ID: {mid}")
meetings = kb.list_meetings()
print(f"  Listed meetings: {len(meetings)}")
search = kb.search("product")
print(f"  Search 'product': {len(search)} results")

# Test Report
print("\n=== REPORT GENERATION ===")
rg = ReportGenerator()
email = rg.generate_email(result, "Q1 Product Meeting")
print(f"  Email report: {len(email)} chars")
md = rg.generate_markdown(result, "Q1 Product Meeting")
print(f"  MD report: {len(md)} chars")

print("\n✅ ALL TESTS PASSED!")
