﻿Sprytny zmieniacz częstotliwości do dekodera radiosond spdxl/dxlAPRS
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
                       [-aprslog <IP:port>] [-remote <url>] [-slave]
                       [-aprsscan] [-c <num>] [-bc <num|procent%>] [-no-blind]
                       [-f <kHz> <kHz>] [-bflush] [-ppm <ppm>] [-agc <0|1>]
                       [-gain <wzmoc|auto>] [-bw <kHz>] [-v | -vv | -q]
                       konfig wyjście

argumenty obowiązkowe:
  konfig            plik konfiguracyjny (wejściowy)
  wyjscie           plik dla sdrtst, do którego nastąpi zapis

argumenty opcjonalne:
  -h, --help          pokaż instrukcję i zakończ
  -csv <url>          URL z danymi na zewnętrznym serwerze (szczegóły poniżej)
  -no-external-csv    wyłącz pobieranie danych CSV z zewnętrznych stron
  -udplog <file>      czytaj dane APRS z logu udpgate4
  -aprslog <IP:port>  czytaj dane APRS z połączenia TCP
  -remote <url>       URL z plikiem zdalnej kontroli (wymuszenie parametrów)
  -slave              nie czytaj danych z pliku/strony/APRS (dla pracy z wieloma
                      SDR, szczegóły poniżej)
  -aprsscan           dodatkowe cykle odbioru APRS 70cm
  -c <num>            maksymalna ilość kanałów jednego SDR (domyślnie: 4)
  -bc <num|procent%>  ilość kanałów zarezerwowana dla ślepego skanowania
                      (domyślnie: 25% max. ilości kanałów)
  -no-blind           wyłącz ślepe skanowanie
  -f <kHz> <kHz>      zakres częstotliwości (dla pracy z wieloma SDR, domyślnie
                      400000 406000)
  -bflush             włącz cykle czyszczenia buforów (szczegóły poniżej)
  -ppm <ppm>          poprawka PPM dla RTL
  -agc <0|1>          przełącznik RTL AGC (domyślnie: 1 - włączony)
  -gain <wzmoc|auto>  ustawienie wzmocnienia odbiornika
                      ('auto' lub 0.0, 0.9, 1.4 ... 48.0, 49.6)
  -bw <kHz>           max szerokość pasma RTL (domyślnie: 1900)
  -v                  tryb szczegółowego opisu akcji
  -vv                 tryb szczegółowy ze znacznikami czasu
  -q                  tryb cichy (pokazuje tylko błędy)



                     * * *  Tryb lądowania  * * *

Jedną z głównych funkcji freq_cycler jest tryb lądowania. Jeśli opadająca sonda
zostanie wykryta w zasięgu zdefiniowanym w pliku konfiguracyjnym, uruchomi się
tryb lądowania. W tym trybie:
 - zmiany częstotliwości są wstrzymane, chyba że zostanie wykryte inne lądowanie,
 - liczba kanałów określana automatycznie (zobacz niżej) jest zredukowana,
   aby zapobiec przeciążeniu procesora
 - mogą być zastosowane alternatywne definicje dla sdrtst, jeśli zostały
   określone jako LdgSdrtstTemplate. W ten sposób można zmniejszyć AFC (i użyć
   rozrzutu opisanego poniżej), wyłączyć squelch itp.
 - może zostać dodany dodatkowy rozrzut częstotliwości (wokół pierwotnej QRG)
   do skorygowania dryftu nadajnika, np. "LdgModeFreqSpread="-2 6 2" dla
   403.000 MHz doda dodatkowe częstotliwości oidobioru co 2 kHz od -2 do +6 kHz,
   czyli: 402.998, 403.002, 403.004, 403.006

Tryb lądowania kończy się, kiedy sonda nie jest odbierana lub przestała opadać
przez czas określony jako SignalTimeout.



                     * * *  Używanie z oryginalnym dxlAPRS  * * *

Jeśli używasz oryginalnego dxlAPRS, musisz wykonać trzy dodatkowe czynności:

1. dxlAPRS nie udostępnia /tmp/sonde.csv, zatem aby odbierać informacje o
odebranych lokalnie sondach, freq_cycler potrzebuje czytać log lokalnego
udpgate4. Włącz logowanie na poziom 0, tj. -l 0:/tmp/udpgate.log
Następnie parametrem -udplog <plik> wskaż freq_cycler właśnie ten plik.

2. Ponieważ dxlAPRS nie dekoduje sond PilotSonde, usuń odpowiadającą im sekcję
z pliku konfiguracyjnego, czyli [sonde_pilotsonde].

3. Oryginalny sdrtst nie używa parametru "AFC offset", zatem musisz usunąć
DRUGI element z linii SdrtstTemplate w pliku konfiguracyjnym.



                     * * *  Czytanie danych CSV ze stron  * * *

Aby wymieniać dane między stacjami, skrypt czyta listę wykrytych sond
w formacie CSV ze stron poświęconym sondom. Nowe dane są pobierane co 3 minuty.
Argument -csv wskazuje URL ze źródłem danych. Można go użyć więcej niż raz, aby
pobierać dane z kilku źródeł.
Jeśli -csv nie zostanie użyte, domyślna lista adresów jest następująca:
 * http://api.wettersonde.net/sonde_csv.php

Aby całkowicie wyłączyć tę funkcję, użyj -no-external-csv



                     * * *  Zdalna kontrola  * * *

Argument -remote wskazuje URL, który będzie sprawdzany co 90 sekund. Jeśli znajdzie
się tam niepusty plik, jego zawartość zostanie bezpośrednio zapisana w pliku
dla sdrtst. W tym czasie freq_cycler nie wykonuje swoich normalnych cyklów. Ważność
pliku wygasa po 60 minutach.
W pliku zdalnej kontroli mogą znaleść się dwie specjalne linie. Pierwsza to np. 
"#E:1562511131" i zawiera czas utworzenia pliku (jako czas UNIX), od którego jest
liczona ważność pliku. Drugi typ to np. "#G:52.1,17.4,150", który ogranicza
geograficzny zasięg pliku zdalnej kontroli do 150km promienia od współrzędnych
52.1 017.4.



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
W trybie lądowania ilość kanałów jest zmniejszana o 33%.



                     * * *  Skanowanie APRS  * * *

Ta funkcja pozwala Twojej stacji odbieranie zarówno sond, jak i APRS 70cm.
Pojawiają się dodatkowe "cykle APRS", w czasie których SDR jest ustawiany do
odbioru częstotliwości 432.500. Musisz przekierować strumień dźwięku do
programowego dekodera APRS (np. direwolf).
Takie przekierowanie można zrobić z użyciem opcji sondeudp -D wskazując
nazwaną kolejkę (FIFO), która z kolei będzie odbierana przez modem. W czasie
cyklu APRS jest to surowy, jednokanałowy (mono) strumień.
Skrypt monitoruje log APRS i jeśli cokolwiek zostanie odebrane, mogą być
ustawione dłuższe cykle APRS.
Instrukcja instalacji jest w pliku aprs_cycles_howto_pl.md



                     * * *  Cykle czyszczenia buforów sondeudp  * * *

W starszych wersjach dxlAPRS i spdxl (przed 22.04.2020), kiedy ilość 
kanałów odbiorczych się zmniejszała, dane z usuniętych kanałów
pozostawały w buforach sondeudp do czasu, kiedy dany kanał ponownie zaczął
odbierać dane. Powodowało to dekodowanie ramek dużo później względem
rzeczywistego czasu odbioru i zaburzanie ich kolejności.

Jeśli nie możesz zainstalować najnowszego dxlAPRS lub spdxl, użyj opcji -bflush
która za każdym razem gdy ilość kanałów spada, doda krótki (1,3 sekundy) "cykl
czyszczący" używając częstotliwości spoza zakresu sond.



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
 - 'p' oznacza PilotSonde, 'm' - M10/M20, 'a' - ATMS. Wszystkie pozostałe (RS41,
RS92, DFM, MP3 i inne) nie mają końcówki.

Gwiazdka z liczbą na końcu informacji o częstotliwości oznacza, że zostały dla
niej utworzone więcej niż jeden wpis w sdrtst, z powodu kilku szablonów lub
"rozrzutu" w trybie lądowania.



                     * * *  Podziękowania  * * *

Połączenie i czytanie APRS - oryginalny kod autorstwa Tomasza SQ7BR.

