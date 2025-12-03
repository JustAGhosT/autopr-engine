import json
import os
import subprocess
import sys

def main():
    analysis_json = sys.argv[1]
    file_path = sys.argv[2]
    analysis = json.loads(analysis_json)

    if analysis.get('fix_code'):
        print("Auto-fixable action detected. Applying fix...")
        apply_fix(analysis['fix_code'], file_path)
        commit_changes(file_path)
    else:
        print("No auto-fixable action detected.")

def apply_fix(fix_code, file_path):
    if not file_path:
        print("Error: file_path is not defined.")
        sys.exit(1)

    with open(file_path, 'w') as f:
        f.write(fix_code)

def commit_changes(file_path):
    subprocess.run(['git', 'config', '--global', 'user.name', 'github-actions[bot]'], check=True)
    subprocess.run(['git', 'config', '--global', 'user.email', 'github-actions[bot]@users.noreply.github.com'], check=True)
    subprocess.run(['git', 'checkout', os.environ["GITHUB_HEAD_REF"]], check=True)
    subprocess.run(['git', 'add', file_path], check=True)
    subprocess.run(['git', 'commit', '-m', f'Fix: Apply auto-fix to {file_path}'], check=True)
    subprocess.run(['git', 'push'], check=True)

if __name__ == "__main__":
    main()
