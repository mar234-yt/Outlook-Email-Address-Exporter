Outlook Email Address Exporter
================================
Автоматизирано извличане и санитизиране на кореспондентски данни
от Microsoft Outlook PST архиви

Автор: Мариян Димитров, 2474
Курс: Програмиране на Python, УниБИТ
GitHub: https://github.com/mar234-yt/Outlook-Email-Address-Exporter


1. ОПИСАНИЕ НА ПРОЕКТА
----------------------
Проектът представлява конзолно приложение за обработка на данни,
което извлича валидни имейл адреси на реални хора от архивни PST
файлове на Microsoft Outlook, филтрира системните и автоматизираните
записи и експортира резултата в стандартизиран CSV формат.

Тема: Обработване на данни (Data Processing)


2. СТРУКТУРА НА ПРОЕКТА
-----------------------
.
├── models.py              # Модул с бизнес логика (клас EmailProcessor)
├── main.py                # Главен модул за изпълнение
├── requirements.txt       # Зависимости (стандартна библиотека на Python)
├── readme.txt             # Настоящ файл
├── .gitignore             # Изключване на PST файлове и временни директории
└── addresses_clean.csv    # Примерен изход от обработка (демонстрационни данни)


3. ИЗИСКВАНИЯ ЗА СРЕДАТА
------------------------
- Windows 10/11 с WSL (Windows Subsystem for Linux)
- Ubuntu под WSL
- Python 3.x
- libpst-tools (readpst)


4. ИНСТАЛАЦИЯ
-------------
4.1. Инсталиране на WSL (в PowerShell с администраторски права):
     wsl --install -d Ubuntu

4.2. Инсталиране на зависимости в Ubuntu:
     sudo apt-get update
     sudo apt-get install software-properties-common -y
     sudo add-apt-repository universe -y
     sudo apt-get update
     sudo apt-get install libpst-tools python3 -y

4.3. Проверка:
     readpst -V


5. ИЗПОЛЗВАНИ БИБЛИОТЕКИ
------------------------
Проектът използва изключително стандартната библиотека на Python 3:

- os          : Работа с файловата система и обхождане на директории
- re          : Регулярни изрази за извличане и филтриране на имейли
- csv         : Запис на структурирани данни в CSV формат
- subprocess  : Извикване на външния инструмент readpst
- tempfile    : Създаване на временни директории за извлечените съобщения
- shutil      : Изтриване на временни директории след обработка
- sys         : Четене на аргументи от командния ред

Външна системна зависимост:
- readpst (libpst-tools) : Парсиране на двоичния PST формат


6. КАК ДА СЕ СТАРТИРА
---------------------
6.1. Поставете PST файла в папката на проекта.

6.2. От WSL терминал, навигирайте до проекта:
     cd /mnt/c/Users/[USERNAME]/Documents/Outlook-Email-Address-Exporter

6.3. Стартирайте главния модул:
     python3 main.py backup.pst addresses_clean.csv

6.4. Очакван изход:
     - Създава се файл addresses_clean.csv
     - В конзолата се извежда статистика за броя обработени записи


7. АРХИТЕКТУРА И БИЗНЕС ЛОГИКА
------------------------------
Клас EmailProcessor (models.py):
- __init__(pst_path, output_dir) : Инициализира обекта с път към PST файл
- extract_from_pst()             : Извлича имейли чрез readpst; обхожда
                                     извлечените файлове в цикъл и прилага
                                     regex с условна валидация
- filter_and_sort()              : Филтрира системни адреси с регулярни
                                     изрази и условия; сортира резултата
- save_to_csv(filename)            : Записва обработените данни в CSV
- get_stats()                    : Връща речник с метрики (raw, clean)

Главен модул main.py:
- Създава обект от клас EmailProcessor
- Предава входните параметри от командния ред
- Последователно извиква методите за извличане, филтриране,
  сортиране и запис на данните


8. ПРИМЕРЕН УЪРКФЛОУ
-------------------------
$ python3 main.py backup.pst output.csv
Extracting PST to temporary directory...
Scanning extracted emails...
  Processed 1000 files...
  Processed 2000 files...

Done! Found 142 unique addresses
Output saved to: output.csv
Stats: {'raw': 2150, 'unique_clean': 142}
