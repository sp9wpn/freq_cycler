## Jak ustawić stację, by odbierała zarówno sondy, jak i APRS na 432.500 ##

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

   IGFILTER m/10
   ```

3. Stwórz potok (FIFO):

   `$ mkfifo /home/pi/direwolf.fifo`

4. Skompiluj programik do filtrowania potoku dołączony do freq_cycler:

   `$ gcc aprs_stream_copy.c -o aprs_stream_copy`

5. Zrestartuj sondeudp z dodatkowym parametrem `-D /home/pi/direwolf.fifo`.
   Pamiętaj, że sondeudp **_zawiesi się_** dopóki inny proces nie zacznie czytać potoku!

6. Uruchom direwolfa z filtrem do potoku:

   `$ freq_cycler/aprs_stream_copy /tmp/freq_cycler_aprs_cycle.tmp /home/pi/direwolf.fifo - | \
   direwolf -c /home/pi/direwolf.conf -L /var/log/direwolf/direwolf.log -r 24000 -qhd -t 0`

   Upewnij się, że częstotliwość próbkowania (tutaj 24000) jest taka sama jak w sdrtst oraz sondeudp.

7. W sekcji `[aprs_cycles]` config_pl.cfg ustaw parametry według swojego upodobania.

8. Zrestartuj  freq_cycler.py z dodatkowym argumentem `-aprsscan`.

9. Do normalnej pracy, nanieś powyższe zmiany do skryptu startowego.
