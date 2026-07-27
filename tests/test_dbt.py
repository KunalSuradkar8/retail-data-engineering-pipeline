import os
import sys
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest

def test_dbt_project_debug():
    dbt_project_dir = os.path.join(PROJECT_ROOT, "dbt_project")
    dbt_exe = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "dbt.exe")
    
    if os.path.exists(dbt_exe):
        res = subprocess.run([dbt_exe, "debug", "--project-dir", dbt_project_dir, "--profiles-dir", dbt_project_dir], capture_output=True, text=True)
        assert res.returncode == 0
        assert "All checks passed!" in res.stdout
