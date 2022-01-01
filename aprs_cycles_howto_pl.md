## Jak ustawić stację, by odbierała zarówno sondy, jak i APRS na 432.500 ##
### Wprowadzenie ###
Typowy odbiornik radiosond ma wszystko co potrzeba, by odbierać również APRS na 432,500MHz.
Oczywiście jeśli zastosowano filtr SAW na 400MHz, to stacja będzie bezużyteczna na paśmie 433, ale
normalnie cały sprzęt jest gotowy. Potrzeba tylko trochę oprogramowania.

Pomysł polega na podziale czasu pracy odbiornika pomiędzy sondy i częstotliwość APRS. Normalnie jest to podział
mniej więcej pół na pół, ale jeśli zostanie wykryta aktywność na APRS, freq_cycler wydłuży czasy jego odbioru.
I odwrotnie, sondy w trakcie lądowania otrzymują odbiornik na wyłączność. Wszystkie te czasy można ustawiaćw pliku
konfiguracyjnym.

### Jak to poustawiać ###
1. Na początku potrzebujesz programowego dekodera APRS. Ja polecam direwolf. Jest dostępny w Raspbianie jako
pakiet, więc wystarczy uruchomić:
   ```
   $ sudo apt-get update
   $ sudo apt-get install direwolf
   ```
   Możesz także skompilować direwolfa ze źródeł: https://github.com/wb2osz/direwolf

2. Przygotuj plik konfiguracyjny direwolfa. Ponieważ będzie to tylko stacja odbiorcza, konfig jest bardzo
prosty. Zapisz go jako direwolf.conf w katalogu domowym (np. /home/pi/direwolf.conf):
  
   (zamień `N0CALL` na swój znak oraz wpisz swoje hasło APRS-IS w miejsce `00000`)

   ```
   MYCALL N0CALL-10

   ADEVICE0 stdin null
   ACHANNELS 1
   CHANNEL 0
   MODEM 1200

   KISSPORT 0
   AGWPORT 0

   IGSERVER euro.aprs2.net
   IGLOGIN N0CALL 00000
   ```
  
3. Przygotuj katalog na logi direwolfa:
   ```
   $ sudo mkdir -p /var/log/direwolf
   $ sudo chmod 777 /var/log/direwolf
   ```
   
4. Stwórz potok (FIFO):

   `$ mkfifo /home/pi/direwolf.fifo`
   
   Pamiętaj, żeby utworzyć potok **_zanim_** uruchomisz sondeudp z parametrem `-D` (zob. pkt 6)

5. Skompiluj programik do filtrowania potoku dołączony do freq_cycler:

   `$ gcc aprs_stream_copy.c -o aprs_stream_copy`

6. Zrestartuj sondeudp z dodatkowym parametrem `-D /home/pi/direwolf.fifo`.
   Pamiętaj, że sondeudp **_zawiesi się_** dopóki inny proces nie zacznie czytać potoku!

7. Uruchom direwolfa z filtrem do potoku (jedna długa linia):

   ```
   $ ./aprs_stream_copy /tmp/freq_cycler_aprs_cycle.tmp /home/pi/direwolf.fifo - | direwolf -c /home/pi/direwolf.conf -l /var/log/direwolf -r 24000 -qhd -t 0
   ```

   Upewnij się, że częstotliwość próbkowania (tutaj 24000) jest taka sama jak w sdrtst oraz sondeudp.

8. W sekcji `[aprs_cycles]` config_pl.cfg ustaw parametry według swojego upodobania.

9. Opcja AprsGPIO w tym pliku pozwala sterować pinem GPIO Raspberry Pi zgodnie z aktywnością trybu APRS.
   Jest to przydatne do przełączania anten i filtrów.

10. Zrestartuj freq_cycler.py z dodatkowym argumentem `-aprsscan`.

11. Do normalnej pracy, umieść zmiany i operacje z kroków 3, 4, 6, 7, 10 w skrypcie startowym.
