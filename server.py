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
  stdscr.nodelay(True)

  running = True

  while running:
    c = stdscr.getch()
    curses.flushinp()
    # Store the key value in the variable `c`
    # Clear the terminal
    stdscr.clear()
    
    for i, client in enumerate(clients):
      stdscr.addstr(i,0,client['addr'][0])

    if c == ord('q'):
      running = False

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
