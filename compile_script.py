import os
import sys
import subprocess
import argparse

def check_nuitka_installed():
    """Проверяет, установлен ли Nuitka"""
    try:
        import nuitka
        return True
    except ImportError:
        return False

def install_nuitka():
    """Устанавливает Nuitka и необходимые зависимости"""
    print("Установка Nuitka...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka"])
    
    # Проверяем, какой компилятор C++ доступен
    if os.name == 'nt':  # Windows
        # На Windows проверяем наличие MSVC
        try:
            result = subprocess.run(["cl"], shell=True, capture_output=True, text=True)
            if "Microsoft" not in result.stderr:
                print("Установка MinGW64 для компиляции C++...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "mingw"])
        except FileNotFoundError:
            # MSVC не найден, устанавливаем MinGW
            print("Установка MinGW64 для компиляции C++...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mingw"])
    
    print("Nuitka успешно установлен!")

def compile_script(script_path, output_name=None, standalone=False, onefile=False):
    """Компилирует Python-скрипт с помощью Nuitka"""
    
    if not output_name:
        output_name = os.path.splitext(os.path.basename(script_path))[0]
    
    cmd = [sys.executable, "-m", "nuitka", "--show-progress"]
    
    # Добавляем опции компиляции
    if standalone:
        cmd.append("--standalone")
    if onefile:
        cmd.append("--onefile")
    
    # Включаем оптимизацию
    cmd.append("--lto=yes")  # Link Time Optimization
    cmd.append("--clang")    # Используем clang, если доступен
    
    # Имя выходного файла
    cmd.extend(["--output-dir=dist", f"--output-filename={output_name}"])
    
    # Добавляем путь к скрипту
    cmd.append(script_path)
    
    print(f"Запуск компиляции: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    output_path = os.path.join("dist", output_name)
    if os.name == 'nt':
        output_path += '.exe'
    
    if os.path.exists(output_path) or os.path.exists(output_path + '.exe'):
        print(f"Компиляция успешно завершена! Исполняемый файл: {output_path}")
    else:
        print("Ошибка компиляции. Проверьте вывод выше на наличие ошибок.")

def main():
    parser = argparse.ArgumentParser(description="Компилирует Python-скрипт в исполняемый файл с помощью Nuitka")
    parser.add_argument('--script', required=True, help='Путь к скрипту для компиляции')
    parser.add_argument('--output', help='Имя выходного файла (без расширения)')
    parser.add_argument('--standalone', action='store_true', help='Создать автономное приложение со всеми зависимостями')
    parser.add_argument('--onefile', action='store_true', help='Создать один исполняемый файл (требуется --standalone)')
    
    args = parser.parse_args()
    
    # Проверяем наличие Nuitka
    if not check_nuitka_installed():
        install_nuitka()
    
    # Создаем директорию для выходных файлов
    os.makedirs("dist", exist_ok=True)
    
    # Компилируем скрипт
    compile_script(args.script, args.output, args.standalone, args.onefile)

if __name__ == "__main__":
    main() 