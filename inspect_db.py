import sqlite3, json

conn = sqlite3.connect(r'meeting_knowledge_base.db')
conn.row_factory = sqlite3.Row

print('=== DATABASE TABLES ===')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    print(' -', t[0])

print()
print('=== meetings TABLE SCHEMA ===')
schema = conn.execute("PRAGMA table_info(meetings)").fetchall()
for col in schema:
    print(f'  Column: {col[1]:25s} Type: {col[2]}')

print()
print('=== STORED MEETINGS COUNT ===')
count = conn.execute('SELECT COUNT(*) as c FROM meetings').fetchone()
print(f'  Total meetings in database: {count[0]}')

print()
if count[0] > 0:
    print('=== STORED MEETING RECORDS ===')
    rows = conn.execute('''SELECT id, title, date, decisions_count, tasks_count,
                                  speakers_count, sentiment, productivity_score, word_count, created_at
                           FROM meetings ORDER BY created_at DESC LIMIT 5''').fetchall()
    for r in rows:
        print(f'  ID: {r["id"]} | Title: {r["title"][:50]}')
        print(f'        Date: {r["date"][:10]} | Decisions: {r["decisions_count"]} | Tasks: {r["tasks_count"]}')
        print(f'        Speakers: {r["speakers_count"]} | Sentiment: {r["sentiment"]} | Score: {r["productivity_score"]}/100')
        print(f'        Words: {r["word_count"]} | Saved At: {r["created_at"]}')
        print()

    print('=== STORED ANALYSIS JSON (Latest Record Preview) ===')
    first = conn.execute('SELECT title, analysis FROM meetings ORDER BY created_at DESC LIMIT 1').fetchone()
    analysis = json.loads(first['analysis'])
    print(f'  Meeting: {first["title"]}')
    print(f'  JSON Keys stored: {list(analysis.keys())}')
    print()

    tasks = analysis.get('tasks', [])
    print(f'  Tasks extracted ({len(tasks)} total):')
    for i, t in enumerate(tasks[:3]):
        print(f'    Task {i+1}: {t}')

    print()
    decisions = analysis.get('decisions', [])
    print(f'  Decisions extracted ({len(decisions)} total):')
    for i, d in enumerate(decisions[:3]):
        print(f'    Decision {i+1}: {str(d)[:120]}')

    print()
    risks = analysis.get('risks', [])
    print(f'  Risks detected ({len(risks)} total):')
    for i, r in enumerate(risks[:3]):
        print(f'    Risk {i+1}: {str(r)[:120]}')

    print()
    sentiment = analysis.get('sentiment', {})
    print(f'  Sentiment: {sentiment}')

    print()
    score = analysis.get('productivity_score', {})
    print(f'  Productivity Score: {score}')

else:
    print('  No meetings saved yet in the database.')

conn.close()
