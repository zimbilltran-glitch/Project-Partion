import subprocess, sys
result = subprocess.run(
    [sys.executable, 'sub-projects/V6_Excel_Extractor/verify_ground_truth.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd='c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2'
)
output = result.stdout + result.stderr
with open('tmp_audit_result.txt', 'w', encoding='utf-8') as f:
    f.write(output)
print("Done. Exit code:", result.returncode)
print(output[:3000])
