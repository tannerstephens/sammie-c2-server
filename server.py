import argparse, curses, socket, threading, time

clients = []
lock = threading.Lock()

def get_arguments():
  parser = argparse.ArgumentParser(description='Starts C2 server for Sammie\'s Class')
  parser.add_argument('-p', '--port', type=int, default=12568, help='Listening port (Default: 12568)', dest='port')
  return parser.parse_args()

def new_client(client_socket, addr):
  global clients

  with lock:
    clients.append(dict(socket=client_socket, addr=addr))

def listen_for_clients(port):
  t = threading.currentThread()
  
  s = socket.socket()

  s.bind(("0.0.0.0", port))
  s.listen(5)

  while getattr(t, "running", True):
    c, addr = s.accept()
    new_client(c,addr)

  for client in clients:
    client['socket'].send("gtfo\n".encode())
    client['socket'].close()

  return

def nice_menu_function(stdscr):
  stdscr.clear()
  curses.curs_set(0)
  curses.use_default_colors()
  stdscr.nodelay(True)
  height,width = stdscr.getmaxyx()

  running = True

  selected = 0

  for i in range(0, curses.COLORS):
    curses.init_pair(i + 1, i, -1)

  while running:
    c = stdscr.getch()
    curses.flushinp()
    stdscr.clear()

    if c == ord('q'):
      running = False
    elif curses.KEY_RESIZE == c:
      height,width = stdscr.getmaxyx()
    
    elif c == curses.KEY_DOWN and len(clients) > 0:
      selected = (selected + 1) % len(clients)
    elif c == curses.KEY_UP and len(clients) > 0:
      selected = (selected - 1) % len(clients)

    stdscr.addstr(0, 0, "Sammie C2 Server", curses.color_pair(5))
    stdscr.addstr(1, 0, "Connected Clients", curses.color_pair(3))
    stdscr.addstr(height-1, 0, "Press 'q' to quit server")

    with lock:
      if len(clients) == 0:
        stdscr.addstr(3,0,"No clients connected")
      else:
        for i, client in enumerate(clients):
          if i == selected:
            stdscr.addstr(i+3,0,str(i) + ") " + client['addr'][0], curses.A_REVERSE)
          else:
            stdscr.addstr(i+3,0,str(i) + ") " + client['addr'][0])

    stdscr.refresh()

    time.sleep(0.1)


def main():
  args = get_arguments()

  t = threading.Thread(target=listen_for_clients, args=(args.port,))
  t.start()

  curses.wrapper(nice_menu_function)

  t.running = False

  s = socket.socket()
  s.connect(("localhost", args.port))
  s.close()

  t.join()

  return


if __name__ == "__main__":
  main()
