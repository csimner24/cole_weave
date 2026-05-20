import json

issues = json.load(open("data/raw/issues.json"))
closed = [i for i in issues if i["state"] == "CLOSED"]
bugs = [i for i in closed if "bug" in i["labels"]]
priority = [i for i in closed if any(l in ["P0","P1","P2","P3++"] for l in i["labels"])]
bug_and_p = [i for i in bugs if any(l in ["P0","P1","P2","P3++"] for l in i["labels"])]

print(f"Total issues: {len(issues)}")
print(f"Closed issues: {len(closed)}")
print(f"Closed with 'bug' label: {len(bugs)}")
print(f"Closed with priority label (P0-P3++): {len(priority)}")
print(f"Closed with BOTH bug AND priority: {len(bug_and_p)}")
print()

print("--- Sample closed bugs (first 15) ---")
for b in bugs[:15]:
    print(f"  #{b['number']} labels={b['labels']} closer={b['closer']}")

print()
print("--- All closed with priority ---")
for p in priority[:20]:
    print(f"  #{p['number']} labels={p['labels']} closer={p['closer']}")

print()
all_labels = set()
for i in closed:
    for l in i["labels"]:
        all_labels.add(l)
print(f"--- All unique labels on closed issues ({len(all_labels)}) ---")
for l in sorted(all_labels):
    count = sum(1 for i in closed if l in i["labels"])
    print(f"  {l}: {count}")
