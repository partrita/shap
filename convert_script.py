import os
import glob
import subprocess
import shutil
import re

REPO_DIR = "/home/fkt/Downloads/repo/shap"
DOCS_DIR = os.path.join(REPO_DIR, "docs")
NOTEBOOKS_DIR = os.path.join(REPO_DIR, "notebooks")
MYBOOK_DIR = os.path.join(REPO_DIR, "mybook")

def main():
    os.makedirs(MYBOOK_DIR, exist_ok=True)
    
    qmd_files = []
    
    # 1. Convert .rst files in docs to .qmd in mybook
    rst_files = glob.glob(os.path.join(DOCS_DIR, "*.rst"))
    for rst_file in rst_files:
        basename = os.path.basename(rst_file)
        name, _ = os.path.splitext(basename)
        if name in ["conf", "make"]:
            continue
        qmd_file = f"{name}.qmd"
        out_path = os.path.join(MYBOOK_DIR, qmd_file)
        
        print(f"Converting {rst_file} to {out_path}")
        subprocess.run(
            ["pixi", "run", "pandoc", "-f", "rst", "-t", "markdown", rst_file, "-o", out_path],
            cwd=REPO_DIR,
            check=True
        )
        qmd_files.append(qmd_file)
        
    # 2. Move .ipynb files from notebooks to mybook
    ipynb_files_dest = []
    
    for root, dirs, files in os.walk(NOTEBOOKS_DIR):
        for file in files:
            if file.endswith(".ipynb"):
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, NOTEBOOKS_DIR)
                dest_path = os.path.join(MYBOOK_DIR, rel_path)
                
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                print(f"Copying {src_path} to {dest_path}")
                shutil.copy2(src_path, dest_path)
                ipynb_files_dest.append(rel_path)
                
    # 3. Update mybook/_quarto.yml
    quarto_yml_path = os.path.join(MYBOOK_DIR, "_quarto.yml")
    if os.path.exists(quarto_yml_path):
        with open(quarto_yml_path, "r") as f:
            content = f.read()
    else:
        content = ""
        
    # Find existing chapters list
    new_chapters = []
    for qmd in sorted(qmd_files):
        new_chapters.append(f"    - {qmd}")
    for ipynb in sorted(ipynb_files_dest):
        new_chapters.append(f"    - {ipynb}")
        
    chapters_str = "\n".join(new_chapters)
    
    if "chapters:" in content:
        # insert below the last item of chapters
        # we will just replace the chapters: block
        # Actually safer to append
        content = re.sub(r'chapters:\n(?:.+(?:\n|$))*', f'chapters:\n    - index.qmd\n    - references.qmd\n{chapters_str}\n\n', content)
    else:
        content += f"\nbook:\n  chapters:\n    - index.qmd\n    - references.qmd\n{chapters_str}\n"

    with open(quarto_yml_path, "w") as f:
        f.write(content)
        
    print("Done generating chapters.")

if __name__ == "__main__":
    main()
