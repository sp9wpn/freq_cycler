#include <sys/select.h>
#include <sys/stat.h>
#include <time.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <unistd.h> // library for fcntl function
#include <fcntl.h> // library for fcntl function

/*
############################################

Compile with:
gcc aprs_stream_copy.c -o aprs_stream_copy

Program copies datastreams from input to output using a file as a switch.

The purpose is to stop APRS decoder (eg. direwolf) from deconding multi-channel
a sound stream from non-APRS frequencies. This saves a lot of CPU.

Usage:
./aprs_stream_copy <flagfile> <input> <output>
	<flagfile>     if this file does NOT exists, pause copying data to output
                       (while still reading input)
        <input>        input file (usually pipe), use "-" for stdin
        <output>       output file (usually pipe), use "-" for stdout

Example:
./aprs_stream_copy /tmp/freq_cycler_aprs_cycle.tmp /tmp/sound.fifo -


############################################

Kompilacja:

gcc aprs_stream_copy.c -o aprs_stream_copy

Program kopiuje strumień danych z wejścia na wyjście używając pliku jako przełącznika.

Celem jest uniknięcie dekodowania wielokanałowego strumienia z innych częstotliwości
przez dekoder APRS (np. direwolf). Oszczędza to sporo zasobów CPU.

Użycie:
./aprs_stream_copy <plik_flagi> <wejscie> <wyjscie>
	<flagfile>     jeśli ten plik NIE istnieje, nie kopiuj danych na wyjście
                       (wejście jest nadal odczytywane)
        <input>        plik wejściowy (zwykle potok), "-" oznacza standardowe wejście
        <output>       plik wyjściowy (zwykle potok), "-" oznacza standardowe wyjście

Przykład:
./aprs_stream_copy /tmp/freq_cycler_aprs_cycle.tmp /tmp/sound.fifo -


############################################
*/

#define BUFSIZE (20*1024)

int clear_buffer = 0;



int file_exist (char *filename)
{
  struct stat   buffer;
  return (stat (filename, &buffer) == 0);
}


int main(int argc, char **argv)
{
  char buf[BUFSIZE];
  ssize_t bytes;

  int fin_fd;
  int fout_fd;


  if (strcmp(argv[2],"-")==0) {
    fin_fd = STDIN_FILENO;
  } else {
    fin_fd = open (argv[2], O_RDONLY );
    if (fin_fd < 0) {
      fprintf (stderr,"Error opening input file: %s\n", strerror (errno));
      exit (EXIT_FAILURE);
    }
  }

  fcntl(fin_fd, F_SETFL, fcntl(fin_fd, F_GETFL) | O_NONBLOCK);

  if (argc == 2 || strcmp(argv[3],"-")==0)
      fout_fd = STDOUT_FILENO;
  else {
    fout_fd = open (argv[3], O_WRONLY || O_NONBLOCK );
    if (fout_fd < 0)
    {
      fprintf (stderr,"Error opening output file: %s\n", strerror (errno));
      exit (EXIT_FAILURE);
    }
  }


  fd_set fds;


  while (1)
    {
      FD_ZERO(&fds);				// Clear FD set for select
      FD_SET(fin_fd, &fds);

      struct timeval tv;
      tv.tv_sec = 1;
      tv.tv_usec = 0;

      select(fin_fd + 1, &fds, NULL, NULL, &tv);

      bytes = read (fin_fd, buf, sizeof(buf));
      if (bytes > 0) {
        if( file_exist(argv[1]) ) {
            clear_buffer = 8;
            write(fout_fd, buf, bytes);
            if (bytes % 4 != 0)
                write(fout_fd, buf, bytes % 4);				// make sure there were 32 bits written
            nanosleep((const struct timespec[]){{0, 50000000L}}, NULL); // 0.05 sec
        } else {
            if (clear_buffer > 0) {
                write(fout_fd, buf, bytes);
                if (bytes % 4 != 0)
                    write(fout_fd, buf, bytes % 4);
                clear_buffer--;
            }
            nanosleep((const struct timespec[]){{0, 10000000L}}, NULL); // 0.05 sec
        }
      } else if (bytes == 0) {			// EOF
          return 0;
      } else {
          // select() timed out, but keep reading input...
      }
    }

}
