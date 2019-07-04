#include <sys/select.h>
#include <sys/stat.h>
#include <time.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <unistd.h> // library for fcntl function 
#include <fcntl.h> // library for fcntl function 

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
    fout_fd = open (argv[3], O_WRONLY || O_NONBLOCK || O_ASYNC );
    if (fout_fd < 0)
    {
      fprintf (stderr,"Error opening output file: %s\n", strerror (errno));
      exit (EXIT_FAILURE);
    }
  }


  fd_set fds;


  while (1)					// tutaj poprawic na kontrole wyjscia z read()
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
            clear_buffer = 40;
            write(fout_fd, buf, bytes);
            nanosleep((const struct timespec[]){{0, 50000000L}}, NULL); // 0.05 sec
        } else {
            if (clear_buffer > 0) {
                write(fout_fd, buf, bytes);
                clear_buffer--;
                nanosleep((const struct timespec[]){{0, 10000000L}}, NULL); // 0.01 sec
            }
            
        }
      } else if (bytes == 0) {			// EOF
          return 0;
      } else {
          // select() timed out, but keep reading input...
      }
    }

}
