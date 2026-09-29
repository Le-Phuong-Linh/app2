import streamlit as st
import os
import sys
import requests
import regex as re
from bs4 import BeautifulSoup
import time
import random
import shutil

# --- HEADERS ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
}

def get_chapters_list(index_url, status_text):
    """Получает список ссылок на все главы со страницы оглавления"""
    try:
        response = requests.get(index_url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if index_url.replace('.html', '') in href or (href.startswith('/') and href.endswith('.html') and '_' in href):
                full_url = href if href.startswith('http') else f"https://www.52shuku.net{href}"
                if full_url not in links and full_url != index_url:
                    links.append((a.text.strip(), full_url))
        
        if not links:
            main_content = soup.find('article') or soup.find('div', class_='content')
            if main_content:
                for a in main_content.find_all('a', href=True):
                    full_url = a['href'] if a['href'].startswith('http') else f"https://www.52shuku.net{a['href']}"
                    links.append((a.text.strip(), full_url))
                    
        return links
    except Exception as e:
        status_text.error(f"Ошибка при получении оглавления: {e}")
        return []

def download_and_split(index_url, output_dir, status_container):
    status_container.write("Сканирую страницу книги...")
    chapters = get_chapters_list(index_url, status_container)
    
    if not chapters:
        status_container.error("Не удалось найти ссылки на главы. Проверьте правильность URL.")
        return False

    status_container.write(f"Найдено страниц/глав для скачивания: {len(chapters)}")
    
    os.makedirs(output_dir, exist_ok=True)

    progress_bar = st.progress(0)
    total_chapters = len(chapters)

    for idx, (title, url) in enumerate(chapters, 1):
        status_container.text(f"Скачиваю [{idx}/{total_chapters}]: {title}...")
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            content_div = soup.find('article') or soup.find('div', class_='content') or soup.find('div', id='content')
            
            if content_div:
                for s in content_div(['script', 'style', 'a']):
                    s.decompose()
                
                text = content_div.get_text(separator="\n").strip()
                full_chapter_text = f"{title}\n\n{text}"
                
                safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:40]
                file_name = f"{idx:03d}_{safe_title}.txt"
                file_out_path = os.path.join(output_dir, file_name)
                
                with open(file_out_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(full_chapter_text)
            
            progress_bar.progress(idx / total_chapters)
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            continue

    status_container.success("Все готово! Главы сохранены.")
    return True

# --- STREAMLIT UI ---
st.title("📥 Shuku Book Downloader")
st.write("Enter a 52shuku book index URL to download all chapters into an `input/` folder.")

url_input = st.text_input("52shuku Index URL", "https://www.52shuku.net/yanqing/h1fY.html")

if st.button("Start Download"):
    output_folder = "input"
    status_box = st.empty()
    
    success = download_and_split(url_input, output_folder, status_box)
    
    if success:
        shutil.make_archive("downloaded_chapters", 'zip', output_folder)
        
        with open("downloaded_chapters.zip", "rb") as fp:
            st.download_button(
                label="📦 Download Chapters ZIP",
                data=fp,
                file_name="chapters.zip",
                mime="application/zip"
            )