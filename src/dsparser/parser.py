import os
from tqdm import tqdm
from bs4 import BeautifulSoup, SoupStrainer
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import re

from dsparser.utils.html_helpers import extract_html_header_footer, parse_message_date


year_queues = {}

queue_lock = threading.Lock()

html_header = None
html_footer = None

def extract_html_parts(input_file):
    """Extracts header and footer from HTML file for use in output files"""
    global html_header, html_footer
    
    with open(input_file, 'r', encoding='utf-8') as file:
        start_content = file.read(100 * 1024)  # 100 KB
    
    html_header, html_footer = extract_html_header_footer(start_content)

def parse_discord_html(input_file, output_dir, workers=4, chunk_size_mb=10):
    os.makedirs(output_dir, exist_ok=True)
    
    extract_html_parts(input_file)
    
    total_size = os.path.getsize(input_file)
    
    global year_queues
    
    only_messages = SoupStrainer("div", class_="chatlog__message-group")
    
    chunk_size = chunk_size_mb * 1024 * 1024  # convert MB to bytes
    buffer = ""
    processed_size = 0
    
    writer_executor = ThreadPoolExecutor(max_workers=8)
    writer_futures = {}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        with open(input_file, 'r', encoding='utf-8') as file, tqdm(total=total_size, unit='B', unit_scale=True, desc='Processing file') as pbar:
            futures = []
            
            try:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        if buffer:
                            soup = BeautifulSoup(buffer, 'html.parser', parse_only=only_messages)
                            future = executor.submit(process_messages_batch, soup)
                            futures.append(future)
                        break
                    
                    chunk_size_bytes = len(chunk.encode('utf-8'))
                    processed_size += chunk_size_bytes
                    pbar.update(chunk_size_bytes)
                    
                    buffer += chunk
                    
                    last_div_pos = buffer.rfind('</div>')
                    if last_div_pos > 0:
                        valid_part = buffer[:last_div_pos+6]  # +6 to include '</div>'
                        
                        soup = BeautifulSoup(valid_part, 'html.parser', parse_only=only_messages)
                        future = executor.submit(process_messages_batch, soup)
                        futures.append(future)
                        
                        buffer = buffer[last_div_pos+6:]
                
                for future in tqdm(as_completed(futures), total=len(futures), desc="Finishing message processing"):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error processing messages: {e}")
                
                with queue_lock:
                    for year in year_queues.keys():
                        if year not in writer_futures:
                            year_path = os.path.join(output_dir, f"{year}.html")
                            writer_futures[year] = writer_executor.submit(year_file_writer, year, year_path)
                
                with queue_lock:
                    for q in year_queues.values():
                        q.put(None)
                
                for year, future in tqdm(writer_futures.items(), desc="Saving files by year"):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error writing file for {year}: {e}")
                
            finally:
                if 'writer_futures' in locals():
                    with queue_lock:
                        for q in year_queues.values():
                            try:
                                q.put(None)
                            except:
                                pass
                    
                    for year, future in writer_futures.items():
                        try:
                            future.result(timeout=5)
                        except:
                            pass
                
                writer_executor.shutdown(wait=False)

def year_file_writer(year, file_path):
    """Function for writing messages to a file for a specific year from the queue"""
    global html_header, html_footer
    
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_header)
        file.write('<div class="chatlog">\n')
        
        while True:
            message = year_queues[year].get()
            if message is None:
                break
            file.write(message)
        
        file.write(html_footer)

def process_messages_batch(soup):
    """Processes a batch of messages from the soup"""
    message_groups = soup.find_all("div", class_="chatlog__message-group")
    
    
    for group in message_groups:
        timestamp_spans = group.find_all("span", class_="chatlog__timestamp")
        
        if not timestamp_spans:
            continue
            
        timestamp_span = timestamp_spans[0]
        timestamp_text = timestamp_span.text.strip()
        
        date_match = re.search(r"(\d{1,2})-(\w+)-(\d{2})", timestamp_text) or re.search(r"(\d{1,2})/(\d{2})/(\d{4})", timestamp_text)
        if date_match:
            day = date_match.group(1)
            month = date_match.group(2)
            short_year = date_match.group(3)
            
            if len(short_year) == 2:
                year_prefix = "20" if int(short_year) < 50 else "19"
                year = year_prefix + short_year
            else:
                year = short_year
            
            
            group_str = str(group)
            
            with queue_lock:
                if year not in year_queues:
                    year_queues[year] = queue.Queue()
                year_queues[year].put(group_str)
        else:
            pass

if __name__ == "__main__":
    from dsparser.cli import main
    main() 