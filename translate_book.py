import os
import glob
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from deep_translator import GoogleTranslator

MYBOOK_DIR = "/home/fkt/Downloads/repo/shap/mybook"

print_lock = Lock()
def safe_print(*a, **k):
    with print_lock:
        print(*a, **k)

def translate_text(text):
    if not text.strip():
        return text
    translator = GoogleTranslator(source='auto', target='ko')
    try:
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            translated = ""
            for p in parts:
                translated += translator.translate(p) + " "
            return translated
        return translator.translate(text)
    except Exception as e:
        safe_print(f"Translation failed: {e}")
        return text

def translate_markdown(content):
    lines = content.split('\n')
    translated_lines = []
    in_code_block = False
    in_front_matter = False
    buffer = []
    
    def flush_buffer():
        if not buffer:
            return ""
        text = "\n".join(buffer)
        t_text = translate_text(text)
        buffer.clear()
        return t_text
        
    for i, line in enumerate(lines):
        if i == 0 and line.startswith('---'):
            in_front_matter = True
            translated_lines.append(line)
            continue
            
        if in_front_matter:
            translated_lines.append(line)
            if line.startswith('---'):
                in_front_matter = False
            continue
            
        if line.startswith('```') or line.startswith('~~~'):
            if buffer:
                translated_lines.append(flush_buffer())
            in_code_block = not in_code_block
            translated_lines.append(line)
            continue
            
        if in_code_block:
            translated_lines.append(line)
            continue
            
        if line.strip() == "" or line.startswith('<') or line.startswith('!['):
            if buffer:
                translated_lines.append(flush_buffer())
            translated_lines.append(line)
            continue
            
        buffer.append(line)
        
    if buffer:
        translated_lines.append(flush_buffer())
        
    return '\n'.join(translated_lines)

def translate_ipynb(file_path):
    safe_print(f"Translating {file_path} ...")
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            nb = json.load(f)
        except:
            return
            
    modified = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "markdown":
            source = cell.get("source", [])
            if not source:
                continue
            text = "".join(source)
            translated_text = translate_markdown(text)
            new_source = [line + '\n' for line in translated_text.split('\n')]
            if new_source and source and not source[-1].endswith('\n'):
                new_source[-1] = new_source[-1].rstrip('\n')
            cell["source"] = new_source
            modified = True
            
    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)

def translate_qmd(file_path):
    safe_print(f"Translating {file_path} ...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    translated = translate_markdown(content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(translated)

def process_file(file_path):
    if file_path.endswith('.qmd'):
        translate_qmd(file_path)
    elif file_path.endswith('.ipynb'):
        translate_ipynb(file_path)

def main():
    qmd_files = glob.glob(os.path.join(MYBOOK_DIR, "**/*.qmd"), recursive=True)
    ipynb_files = glob.glob(os.path.join(MYBOOK_DIR, "**/*.ipynb"), recursive=True)
    all_files = qmd_files + ipynb_files
    
    safe_print(f"Translating {len(all_files)} files concurrently...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_file, f) for f in all_files]
        for idx, future in enumerate(as_completed(futures)):
            future.result()
            safe_print(f"Done {idx+1}/{len(all_files)}")
            
    safe_print("Translation completed.")

if __name__ == "__main__":
    main()
