Sprytny zmieniacz częstotliwości do dekodera radiosond spdxl/dxlAPRS
Autor: Wojtek SP9WPN
Licencja: BSD

UWAGA: Domyślna konfiguracja jest dla spdxl, jeśli używasz oryginalnego dxlAPRS
koniecznie przeczytaj odpowiednią sekcję niżej.

Skrypt czyta /tmp/sonde.csv, dane APRS oraz pliki csv ze stron monitorujących
sondy, na podstawie tego generuje konfigi sdrtst z częstotliwościami
okolicznych sond.
Jednocześnie skanuje na ślepo cały zakres częstotliwości w poszukiwaniu
nieznanych sygnałów.
Jeśli sonda ląduje w pobliżu, włącza się "tryb lądowania": skanowanie jest
zatrzymane i system pozostaje na stałym nasłuchu lądującej sondy.

Zajrzyj do przykładowego pliku konfiguracyjnego (config_pl.cfg) i wyedytuj
według potrzeb.


Użycie: freq_cycler.py [-h] [-csv <url> | -no-external-csv] [-udplog <plik>]
                       [-aprslog <IP:port>] [-slave] [-c <num>]
                       [-bc <num|procent%>] [-no-blind] [-f <kHz> <kHz>]
                       [-ppm <ppm>] [-agc <0|1>] [-gain <wzmoc|auto>]
                       [-bw <kHz>] [-v | -q]
                       konfig wyjście

argumenty obowiązkowe:
  konfig            plik konfiguracyjny (wejściowy)
  wyjscie           plik dla sdrtst, do którego nastąpi zapis

argumenty opcjonalne:
  -h, --help          pokaż tę instrukcję i zakończ
  -csv <url>          URL z danymi na zewnętrznym serwerze (szczegóły poniżej)
  -no-external-csv    wyłącz pobieranie danych CSV z zewnętrznych stron
  -aprslog <IP:port>  czytaj dane APRS z połączenia TCP
  -udplog <file>      czytaj dane APRS z logu udpgate4
  -slave              nie czytaj danych z pliku/strony/APRS (dla pracy z wieloma
                      SDR, szczegóły poniżej)
  -aprsscan           dodatkowe cykle odbioru APRS 70cm, szczegóły w readme
  -c <num>            maksymalna ilość kanałów jednego SDR (domyślnie: 4)
  -bc <num|procent%>  ilość kanałów zarezerwowana dla ślepego skanowania
                      (domyślnie: 25% max. ilości kanałów)
  -no-blind           wyłącz ślepe skanowanie
  -f <kHz> <kHz>      zakres częstotliwości (dla pracy z wieloma SDR, domyślnie
                      400000 406000)
  -ppm <ppm>          poprawka PPM dla RTL
  -agc <0|1>          przełącznik RTL AGC (domyślnie: 1 - włączony)
  -gain <wzmoc|auto>  ustawienie wzmocnienia odbiornika
                      ('auto' lub 0.0, 0.9, 1.4 ... 48.0, 49.6)
  -bw <kHz>           max szerokość pasma RTL (domyślnie: 1900)
  -v                  tryb szczegółowego opisu akcji
  -q                  tryb cichy (pokazuje tylko błędy)



                     * * *  Używanie z oryginalnym dxlAPRS  * * *

Jeśli używasz oryginalnego dxlAPRS, musisz wykonać trzy dodatkowe czynności:

1. dxlAPRS nie udostępnia /tmp/sonde.csv, zatem aby odbierać informacje o
odebranych lokalnie sondach, freq_cycler potrzebuje czytać log lokalnego
udpgate4. Włącz logowanie na co najmniej 2 poziom, tj. -l 2:/tmp/udpgate.log
Następnie parametrem -udplog <plik> wskaż freq_cycler właśnie ten log.

2. Ponieważ dxlAPRS nie dekoduje sond M10 oraz PilotSonde, usuń całkowicie
odpowiadające im sekcje z pliku konfiguracyjnego, zostawiając tylko
"sonde_standard".

3. Oryginalny sdrtst nie używa parametru "AFC offset", zatem musisz usunąć
DRUGI element z linii SdrtstTemplate w pliku konfiguracyjnym.



                     * * *  Czytanie danych CSV ze stron  * * *

Aby wymieniać dane między stacjami, skrypt czyta listę wykrytych sond
w formacie CSV ze stron poświęconym sondom. Nowe dane są pobierane co 3 minuty.
Argument -csv wskazuje URL ze źródłem danych. Można go użyć więcej niż raz, aby
pobierać dane z kilku źródeł.
Jeśli -csv nie zostanie użyte, domyślna lista adresów jest następująca:
 * http://radiosondy.info/export/csv_live.php
 * http://skp.wodzislaw.pl/sondy/last.php

Aby całkowicie wyłączyć tę funkcję, użyj -no-external-csv



                     * * *  Wskazówki do pracy z wieloma SDR  * * *

Użyj jednego pliku konfiguracyjnego, ale uruchom freq_cycler.py osobno na
każdy odbiornik. Wszystkie instancje skryptu powinny być wywołane z opcją
-slave, poza jedną, która będzie pełniła rolę nadrzędną.

Użyj osobnych plików wyjściowych dla każdego procesu sdrtst.

Musisz użyć parametru "Database" w pliku konfiguracyjnym, aby wszystkie
instancje freq_cycler używały wspólnej bazy danych. Zalecane jest umieszczenie
jej na ramdysku.

Możesz użyć opcji -f aby ograniczyć zakres częstotliwości dla każdego SDR,
poprawi to optymalizację pokrycia częstotliwości. Zakresy mogą się nakładać.

Skrypt w trybie -slave ignoruje parametry -csv, -udplog i -aprslog



                     * * *  Automatyczna ilość kanałów  * * *

Ta eksperymentalna funkcja ustawia ilość dostępnych kanałów (częstotliwości) w
zależności od temperatury rdzenia Raspberry Pi. "Sensor" określa źródło danych.
Jeśli jest to plik wykonywalny (jak /opt/vc/bin/vcgencmd measure_temp),
zostanie uruchomiony i temperatura odczytana z jego wyjścia. Zwykłe pliki (jak
/sys/class/thermal/thermal_zone0/temp) są odczytywane bezpośrednio. Ilość
kanałów jest ustawiana proporcjonalnie pomiędzy LowTemp (niska temperatura)
oraz HighTemp (wysoka).



                     * * *  Skanowanie APRS * * *

Ta funkcja pozwala Twojej stacji odbieranie zarówno sond, jak i APRS 70cm.
Pojawiają się dodatkowe "cykle APRS", w czasie których SDR jest ustawiany do
odbioru częstotliwości 432.500. Musisz przekierować strumień dźwięku do
programowego dekodera APRS (np. direwolf).
Takie przekierowanie można zrobić z użyciem opcji sondeudp -D wskazując
nazwaną kolejkę (FIFO), która z kolei będzie odbierana przez modem. W czasie
cyklu APRS jest to surowy, jednokanałowy (mono) strumień.
Skrypt monitoruje log APRS i jeśli cokolwiek zostanie odebrane, mogą być
ustawione dłuższe cykle APRS.
Ustawienia znajdują się w pliku konfiguracyjnym.



                     * * *  Przykłady  * * *

Jeden SDR, wymuszona poprawka PPM -20, 5 kanałów:
  freq_cycler.py -ppm -20 -c 5 config_pl.cfg /tmp/sdrcfg.txt

Jeden SDR, oryginalny dxlAPRS:
  freq_cycler.py -c 5 -udplog /tmp/dxlAPRS/log/gate.log config_pl.cfg /tmp/sdrcfg.txt

Dwa SDR, po 10 kanałów na każdym, podział pasma na dwie części:
  freq_cycler.py -c 10 -f 400000 403000        config_pl.cfg /tmp/sdrcfg0.txt
  freq_cycler.py -c 10 -f 403000 406000 -slave config_pl.cfg /tmp/sdrcfg1.txt

Cztery SDR, po 5 kanałów na każdym, tylko jeden dedykowany do ślepego skanowania:
  freq_cycler.py -c 5 -no-blind -f 400000 402000        config_pl.cfg /tmp/sdrcfg0.txt
  freq_cycler.py -c 5 -no-blind -f 402000 404000 -slave config_pl.cfg /tmp/sdrcfg1.txt
  freq_cycler.py -c 5 -no-blind -f 404000 406000 -slave config_pl.cfg /tmp/sdrcfg2.txt
  freq_cycler.py -c 5 -bc 5     -f 400000 406000 -slave config_pl.cfg /tmp/sdrcfg3.txt



                     * * *  Oznaczenia na wyjściu  * * *

Skrypt wypisuje na ekranie każdy nowy zestaw częstotliwości (chyba, że użyto
parametru -q). Stosowane są następujące prefiksy: plus (+) oznacza
częstotliwość, którą wskazałeś jako "znaną" w pliku konfiguracyjnym. Krzyżyk
(#) to częstotliwość, na której została faktycznie odebrana lecąca sonda przez
inne stacje (zobacz "Czytanie danych CSV..."), a daszek (^) oznacza sondę
odebraną przez twoją stację.  Wykrzyknik (!) oznacza, że dla danej
częstotliwości jest aktywny tryb lądowania - częstotliwości nie będą zmieniane
dopóki sygnał sondy nie zostanie uznany za utracony. Częstotliwość bez prefiksu
to częstotliwość ślepego skanowania.

Drukowane częstotliwości mają również końcówki oznaczające specjalne typy sond
 - 'p' oznacza PilotSonde, a 'm' M10. Wszystkie pozostałe (RS41, RS92, DFM i
inne) nie mają końcówki.



                     * * *  Podziękowania  * * *

Połączenie i czytanie APRS - oryginalny kod autorstwa Tomasza SQ7BR.

