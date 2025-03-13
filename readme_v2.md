# Raspberry Pi Monitor - Dokumentacja

## Opis Projektu
System monitorowania oparty na Raspberry Pi Zero W, łączący:
- Wykonywanie timelapsu w wysokiej rozdzielczości
- Pomiar temperatury i wilgotności (DHT11)
- Wyświetlanie danych na LCD 16x2 z I2C
- Interfejs webowy z wykresami i podglądem na żywo

## Wymagania Sprzętowe
1. Raspberry Pi Zero W
2. Kamera Raspberry Pi ZeroCam OV5647 5MPx
   - Rozdzielczość: 2592 x 1944 px
   - Sensor: OmniVision OV5647
   - Pole widzenia: 160 stopni
3. Czujnik DHT11 (3-pinowy)
4. Wyświetlacz LCD 2x16 z konwerterem I2C

## Struktura Projektu
```
kamera/
├── app_monitor.py      # Główny plik aplikacji
├── requirements.txt    # Zależności projektu
├── readme_v2.md       # Dokumentacja
└── timelapse_nowy/    # Folder na zdjęcia (tworzony automatycznie)
    └── img_*.jpg      # Zdjęcia timelapsu
```

## Podłączenie Komponentów

### Wyświetlacz LCD z I2C
- VCC → Pin 2 (5V)
- GND → Pin 6 (Ground)
- SDA → Pin 3 (GPIO2)
- SCL → Pin 5 (GPIO3)

### Czujnik DHT11
- VCC → Pin 1 (3.3V) lub Pin 2 (5V)
- DATA → Pin 7 (GPIO4)
- GND → Pin 6 (Ground)

## Instalacja

### 1. Przygotowanie systemu
```bash
# Włącz I2C
sudo raspi-config
# Wybierz: Interface Options -> I2C -> Enable

# Zainstaluj wymagane pakiety systemowe
sudo apt-get update
sudo apt-get install -y python3-venv python3-full python3-picamera2 i2c-tools
```

### 2. Przygotowanie środowiska
```bash
# Przejdź do katalogu projektu
cd ~/kamera

# Utwórz wirtualne środowisko
python3 -m venv lcd_env

# Aktywuj środowisko
source lcd_env/bin/activate
```

### 3. Instalacja wymaganych bibliotek
```bash
# Zainstaluj wymagane pakiety Python
pip3 install -r requirements.txt
```

⚠️ UWAGA: Instalacja może potrwać nawet 1-2 godziny na Raspberry Pi Zero W ze względu na kompilację OpenCV!

Alternatywna metoda instalacji (szybsza):
```bash
# Zainstaluj OpenCV przez apt (znacznie szybciej)
sudo apt-get install -y python3-opencv

# Następnie zainstaluj pozostałe pakiety
pip3 install flask==3.0.0 plotly==5.18.0 pandas==2.1.4 smbus2==0.4.3 Adafruit_DHT==1.4.0
```

Zawartość pliku requirements.txt:
```
flask==3.0.0
plotly==5.18.0
pandas==2.1.4
opencv-python==4.8.1.78
smbus2==0.4.3
Adafruit_DHT==1.4.0
```

## Uruchomienie

### 1. Sprawdzenie połączeń
```bash
# Sprawdź czy I2C działa i wykrywa wyświetlacz
sudo i2cdetect -y 1
# Powinien pokazać adres 0x27
```

### 2. Uruchomienie aplikacji
```bash
# Aktywuj środowisko (jeśli nie jest aktywne)
source lcd_env/bin/activate

# Uruchom program
python3 app_monitor.py -o timelapse_nowy -i 60
```

Parametry:
- `-o` lub `--output`: folder na zdjęcia timelapsu (domyślnie: timelapse_nowy)
- `-i` lub `--interval`: interwał między zdjęciami w sekundach (domyślnie: 60)

## Funkcjonalność

### Interfejs Webowy (http://[IP_RASPBERRY]:5000)
- Podgląd na żywo z kamery (800x600)
- Aktualne odczyty temperatury i wilgotności
- Licznik wykonanych zdjęć
- Wykresy temperatury i wilgotności w czasie
- Automatyczne odświeżanie danych

### Wyświetlacz LCD
Wyświetla naprzemiennie (co 3 sekundy):
1. Temperatura i wilgotność
2. Liczba zdjęć i aktualny czas

### Timelapse
- Rozdzielczość zdjęć: 2304x1296
- Nazwy plików: img_001.jpg, img_002.jpg, itd.
- Możliwość ustawienia własnego interwału
- Automatyczne tworzenie folderu na zdjęcia

## Rozwiązywanie Problemów

### Wyświetlacz LCD
- Jeśli tekst jest niewidoczny, wyreguluj kontrast potencjometrem na module I2C
- Sprawdź połączenia SDA i SCL
- Upewnij się, że adres I2C (0x27) jest prawidłowy

### Czujnik DHT11
- Sprawdź, czy pin DATA jest podłączony do GPIO4
- Upewnij się, że czujnik jest zasilany odpowiednim napięciem

### Kamera
- Sprawdź, czy taśma kamery jest prawidłowo podłączona
- Upewnij się, że kamera jest włączona w raspi-config

## Tworzenie Filmu z Timelapsu
Po zebraniu zdjęć, możesz stworzyć film używając ffmpeg na komputerze:
```bash
# Skopiuj zdjęcia na komputer
scp -r pi@[IP_RASPBERRY]:~/kamera/timelapse_nowy .

# Utwórz film (15 klatek na sekundę)
ffmpeg -framerate 15 -i "img_%03d.jpg" -c:v libx264 -preset ultrafast -pix_fmt yuv420p timelapse_final.mp4
```

## Zarządzanie Systemem

### Kopie Zapasowe
```bash
# Tworzenie kopii zapasowej konfiguracji
tar -czf backup_config.tar.gz app_monitor.py requirements.txt

# Archiwizacja zdjęć (wykonuj regularnie)
tar -czf timelapse_backup_$(date +%Y%m%d).tar.gz timelapse_nowy/
```

### Zarządzanie Pamięcią
- System automatycznie monitoruje dostępne miejsce
- Przy zajęciu 90% pamięci wyświetla ostrzeżenie na LCD
- Zalecane czyszczenie starych zdjęć:
```bash
# Usuń zdjęcia starsze niż 30 dni
find timelapse_nowy/ -name "img_*.jpg" -mtime +30 -delete
```

### Logi i Debugowanie
- Logi aplikacji znajdują się w `app_monitor.log`
- Poziom logowania można zmienić w pliku konfiguracyjnym
- Podstawowe polecenia debugowania:
```bash
# Sprawdź status aplikacji
ps aux | grep app_monitor.py

# Zobacz ostatnie logi
tail -f app_monitor.log

# Sprawdź temperaturę CPU
vcgencmd measure_temp
```

## Aktualizacja Systemu
```bash
# Aktualizacja systemu
sudo apt update && sudo apt upgrade -y

# Aktualizacja bibliotek Python
source lcd_env/bin/activate
pip3 install --upgrade -r requirements.txt
```

## Znane Ograniczenia
1. Wykresy pokazują ostatnie 100 pomiarów
2. Podgląd na żywo może mieć opóźnienie przy słabym połączeniu
3. Wysoka temperatura CPU może wpływać na dokładność czujnika DHT11
4. Maksymalny rozmiar pojedynczego pliku zdjęcia: około 4MB
5. Zalecane minimum wolnej przestrzeni dyskowej: 1GB

## Testowane Wersje
- Raspberry Pi OS Bullseye
- Python 3.11
- Picamera2 0.3.12
- Flask 3.0+