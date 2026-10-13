#!/usr/bin/env python3
"""Render task3 alone without writing to the parent Quarto book."""
from pathlib import Path
import shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='.standalone-',dir=ROOT) as tmp:
 work=Path(tmp)
 (work/'task3.qmd').write_text('---\nlang: de\nformat:\n  html:\n    toc: true\n    embed-resources: true\n---\n\n'+(ROOT/'task3.qmd').read_text())
 for folder in ('a','b','c','simulation'):(work/folder).symlink_to(ROOT/folder,target_is_directory=True)
 (work/'_quarto.yml').write_text('project:\n  type: default\nlang: de\nformat:\n  html:\n    toc: true\n    embed-resources: true\nexecute:\n  enabled: false\n')
 subprocess.run(['quarto','render','task3.qmd','--no-execute'],cwd=work,check=True)
 shutil.copyfile(work/'task3.html',ROOT/'task3.html')
print(ROOT/'task3.html')
