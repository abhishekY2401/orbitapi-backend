import subprocess
import tempfile
from pathlib import Path
import shutil


async def clone_repo(git_url: str) -> Path:
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir) / 'repo'

    # clone the repository using subprocess
    subprocess.run(['git', 'clone', git_url, str(repo_path)], check=True)
    return repo_path


async def clean_up_repo(repo_path: Path):
    shutil.rmtree(repo_path)
