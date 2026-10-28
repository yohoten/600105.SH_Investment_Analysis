# -*- coding: utf-8 -*-
"""执行 Notebook 并回写输出（nbclient）"""
import os
import sys
import nbformat
from nbclient import NotebookClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = os.path.join(ROOT, "永鼎股份投资分析.ipynb")

nb = nbformat.read(NB, as_version=4)
client = NotebookClient(
    nb,
    timeout=600,
    kernel_name="python3",
    resources={"metadata": {"path": ROOT}},
    allow_errors=True,
)
client.execute()

errs = []
for i, c in enumerate(nb.cells):
    if c.cell_type != "code":
        continue
    for o in c.get("outputs", []):
        if o.get("output_type") == "error":
            errs.append((i, o.get("ename"), o.get("evalue")))
        if o.get("output_type") == "stream" and o.get("name") == "stderr":
            txt = o.get("text", "")
            if txt.strip():
                errs.append((i, "stderr", txt[:300]))

nbformat.write(nb, NB)
print("执行完成，单元格", len(nb.cells), "错误", len(errs))
for e in errs:
    print("  ", e)
