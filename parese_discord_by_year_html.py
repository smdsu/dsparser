import argparse
import re
import os
from tqdm import tqdm
from bs4 import BeautifulSoup, SoupStrainer
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue

# Глобальные очереди для хранения сообщений каждого года
year_queues = {}
# Блокировка для безопасной работы с очередями
queue_lock = threading.Lock()
# Хранение HTML-заголовка и футера
html_header = None
html_footer = None

def extract_html_parts(input_file):
    """Извлекает заголовок и конец HTML файла для использования в выходных файлах"""
    global html_header, html_footer
    
    # Читаем начало файла для получения заголовка (первые 100 Кб должно хватить)
    with open(input_file, 'r', encoding='utf-8') as file:
        start_content = file.read(100 * 1024)  # 100 Кб
    
    # Находим позицию начала блока с сообщениями
    chatlog_div_start = start_content.find('<div class="chatlog">')
    if chatlog_div_start != -1:
        html_header = start_content[:chatlog_div_start]
    else:
        # Если не найден специфичный div, используем простой заголовок
        html_header = "<!DOCTYPE html><html><head><title>Discord Messages</title><meta charset='utf-8'></head><body>"
    
    # Формируем футер HTML
    html_footer = "</div></body></html>"  # Закрываем div class="chatlog" и body, html

def parse_discord_html(input_file, output_dir, workers=4, chunk_size_mb=10):
    # Создаем директорию для выходных файлов
    os.makedirs(output_dir, exist_ok=True)
    
    # Извлекаем заголовок и футер HTML
    extract_html_parts(input_file)
    
    # Получаем размер файла для прогресс-бара
    total_size = os.path.getsize(input_file)
    
    # Создаем словарь очередей для каждого года
    global year_queues
    
    # Создаем фильтр для ускорения парсинга - нам нужны только div с классом chatlog__message-container
    only_messages = SoupStrainer("div", class_="chatlog__message-container")
    
    chunk_size = chunk_size_mb * 1024 * 1024  # перевод МБ в байты
    buffer = ""
    processed_size = 0
    
    # Запускаем потоки записи для каждого года, которые будут создаваться по мере обнаружения
    writer_executor = ThreadPoolExecutor(max_workers=8)
    writer_futures = {}
    
    # Создаем пул потоков для обработки сообщений
    with ThreadPoolExecutor(max_workers=workers) as executor:
        with open(input_file, 'r', encoding='utf-8') as file, tqdm(total=total_size, unit='B', unit_scale=True, desc='Обработка файла') as pbar:
            futures = []
            
            try:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        # Обрабатываем оставшийся буфер
                        if buffer:
                            soup = BeautifulSoup(buffer, 'html.parser', parse_only=only_messages)
                            future = executor.submit(process_messages_batch, soup)
                            futures.append(future)
                        break
                    
                    # Обновляем прогресс-бар
                    chunk_size_bytes = len(chunk.encode('utf-8'))
                    processed_size += chunk_size_bytes
                    pbar.update(chunk_size_bytes)
                    
                    # Добавляем чанк к буферу
                    buffer += chunk
                    
                    # Находим полные блоки сообщений в буфере
                    # Ищем последний закрывающий тег div полного блока сообщения
                    last_div_pos = buffer.rfind('</div>')
                    if last_div_pos > 0:
                        # Находим открывающий тег для этого div
                        # Предполагаем, что это полный блок сообщения
                        valid_part = buffer[:last_div_pos+6]  # +6 для включения '</div>'
                        
                        # Парсим и запускаем параллельную обработку полных блоков
                        soup = BeautifulSoup(valid_part, 'html.parser', parse_only=only_messages)
                        future = executor.submit(process_messages_batch, soup)
                        futures.append(future)
                        
                        # Оставляем в буфере неполные блоки для следующей итерации
                        buffer = buffer[last_div_pos+6:]
                
                # Ждем завершения всех задач обработки сообщений
                for future in tqdm(as_completed(futures), total=len(futures), desc="Завершение обработки сообщений"):
                    try:
                        future.result()  # Получаем результат для проверки исключений
                    except Exception as e:
                        print(f"Ошибка при обработке сообщений: {e}")
                
                # Запускаем потоки записи для каждого года
                with queue_lock:
                    for year in year_queues.keys():
                        if year not in writer_futures:
                            year_path = os.path.join(output_dir, f"{year}.html")
                            writer_futures[year] = writer_executor.submit(year_file_writer, year, year_path)
                
                # Сигнализируем о завершении
                with queue_lock:
                    for q in year_queues.values():
                        q.put(None)  # Сигнал завершения для каждой очереди
                
                # Ждем завершения всех потоков записи
                for year, future in tqdm(writer_futures.items(), desc="Сохранение файлов по годам"):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Ошибка при записи файла для {year}: {e}")
                
            finally:
                # Остановка всех потоков в случае ошибки
                if 'writer_futures' in locals():
                    with queue_lock:
                        for q in year_queues.values():
                            try:
                                q.put(None)  # Сигнал завершения
                            except:
                                pass
                    
                    # Ждем завершения всех потоков записи
                    for year, future in writer_futures.items():
                        try:
                            future.result(timeout=5)  # Добавляем таймаут
                        except:
                            pass
                
                writer_executor.shutdown(wait=False)

def year_file_writer(year, file_path):
    """Функция для записи сообщений в файл определенного года из очереди"""
    global html_header, html_footer
    
    with open(file_path, "w", encoding="utf-8") as file:
        # Записываем заголовок HTML
        file.write(html_header)
        # Открываем div для chatlog
        file.write('<div class="chatlog">\n')
        
        # Записываем все сообщения из очереди
        while True:
            message = year_queues[year].get()
            if message is None:  # Сигнал завершения
                break
            file.write(message)
        
        # Записываем футер HTML
        file.write(html_footer)

def process_messages_batch(soup):
    """Обрабатывает пакет сообщений из супа"""
    messages = soup.find_all("div", class_="chatlog__message-container")
    
    for msg in messages:
        timestamp = msg.find("span", class_="chatlog__timestamp")
        if not timestamp or "title" not in timestamp.attrs:
            continue
        
        date_match = re.search(r"(\d{1,2}) (\w+) (\d{4})", timestamp["title"])
        if not date_match:
            continue
        
        year = date_match.group(3)
        msg_str = str(msg)
        
        # Безопасно добавляем сообщение в соответствующую очередь года
        with queue_lock:
            if year not in year_queues:
                year_queues[year] = queue.Queue()
            year_queues[year].put(msg_str)

def main():
    parser = argparse.ArgumentParser(
        description="Параллельный парсинг HTML файла с сообщениями Discord и разделение по годам."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Путь к входному HTML файлу."
    )
    parser.add_argument(
        "--output", "-o", default="output",
        help="Папка для сохранения выходных файлов (по умолчанию: output)."
    )
    parser.add_argument(
        "--chunk-size", "-c", type=int, default=10,
        help="Размер обрабатываемого чанка в MB (по умолчанию: 10)."
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=4,
        help="Количество рабочих потоков для параллельной обработки (по умолчанию: 4)."
    )
    args = parser.parse_args()
    
    parse_discord_html(args.input, args.output, args.workers, args.chunk_size)

if __name__ == "__main__":
    main()
