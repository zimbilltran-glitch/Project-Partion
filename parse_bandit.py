import json
import sys

def main():
    try:
        data = json.load(open('bandit_report.json', encoding='utf-8'))
        results = data.get('results', [])
        found = False
        for r in results:
            if r['issue_severity'] in ['HIGH', 'MEDIUM']:
                print(f"{r['issue_severity']}: {r['filename']}:{r['line_number']} - {r['issue_text']}")
                found = True
        
        if not found:
            print("No HIGH or MEDIUM severity issues found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
