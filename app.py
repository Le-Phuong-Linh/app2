import streamlit as st
import os
import re
import shutil

def clean_content(text):
    text = re.sub(r'^\s*第\d+页\s*', '', text)
    footer_marker = "哦豁，小伙伴们如果觉得52书库不错"
    if footer_marker in text:
        text = text.split(footer_marker)[0]
    return text.strip()

def process_books(status_container):
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, "input")
    output_dir = os.path.join(base_dir, "Output_Chapters")
    
    if not os.path.exists(input_dir):
        status_container.error(f"Error: Could not find the folder named 'input' at: {input_dir}")
        return False

    os.makedirs(output_dir, exist_ok=True)
    
    all_files = [f for f in os.listdir(input_dir) if f.endswith('.txt') and '_' in f]
    
    if not all_files:
        status_container.error("No valid .txt files found inside the 'input' folder.")
        return False
        
    def get_file_num(filename):
        try:
            return int(filename.split('_')[0])
        except ValueError:
            return float('inf')
            
    all_files.sort(key=get_file_num)
    status_container.write(f"Found {len(all_files)} files in 'input' to process...")
    
    combined_text = []
    for filename in all_files:
        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                cleaned = clean_content(content)
                if cleaned:
                    combined_text.append(cleaned)
        except Exception as e:
            continue

    full_novel = "\n\n".join(combined_text)
    chapter_regex = r'(第[0-9一二三四五六七八九十百千万]+章[^\n]*)'
    parts = re.split(chapter_regex, full_novel)
    
    prologue = parts[0].strip()
    if prologue:
        with open(os.path.join(output_dir, "0000_前言.txt"), 'w', encoding='utf-8') as f:
            f.write(prologue)
            
    chapter_count = 0
    for i in range(1, len(parts), 2):
        chap_title = parts[i].strip()
        chap_content = parts[i+1].strip()
        
        safe_title = re.sub(r'[\\/*?:"<>|]', "", chap_title)[:50]
        clean_filename_title = re.sub(r'^第[0-9一二三四五六七八九十百千万]+章\s*', '', safe_title)
        
        if not clean_filename_title.strip():
            clean_filename_title = safe_title
            
        filename = f"{str(chapter_count+1).zfill(4)}_{clean_filename_title}.txt"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chap_title + "\n\n" + chap_content)
            
        chapter_count += 1

    status_container.success(f"Success! Cleaned and generated {chapter_count} real chapters inside 'Output_Chapters'.")
    return True

# --- STREAMLIT UI ---
st.title("✂️ Shuku Chapter Splitter")
st.write("Upload your raw chapter text files below to clean them and split them into real, structured chapters.")

uploaded_files = st.file_uploader("Upload raw chapter .txt files", accept_multiple_files=True, type=["txt"])

if uploaded_files:
    os.makedirs("input", exist_ok=True)
    for uploaded_file in uploaded_files:
        with open(os.path.join("input", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
    st.success(f"Successfully loaded {len(uploaded_files)} files ready for processing!")

if st.button("Start Splitting Chapters"):
    status_box = st.empty()
    success = process_books(status_box)
    
    if success:
        shutil.make_archive("real_chapters_output", 'zip', "Output_Chapters")
        with open("real_chapters_output.zip", "rb") as fp:
            st.download_button(
                label="📦 Download Real Chapters ZIP",
                data=fp,
                file_name="real_chapters.zip",
                mime="application/zip"
            )
