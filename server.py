import argparse, curses, socket, threading, time, uuid

clients = []
lock = threading.Lock()

def get_arguments():
  parser = argparse.ArgumentParser(description='Starts C2 server for Sammie\'s Class')
  parser.add_argument('-p', '--port', type=int, default=12568, help='Listening port (Default: 12568)', dest='port')
  return parser.parse_args()


def read_until_eod(c):
  data = c.recv(4096).decode()

  while data[-4:] != "EOD\n":
    data += c.recv(4096).decode()

  data = data.strip()[:-3]

  return data

def new_client(client_socket, addr):
  global clients
  
  data = read_until_eod(client_socket)

  with lock:
    cid = str(uuid.uuid4())
    client_socket.send(("id " + cid + "\n").encode())
    clients.append(dict(socket=client_socket, addr=addr, data=data, cid=cid))

  

def listen_for_clients(port):
  t = threading.currentThread()
  
  s = socket.socket()

  s.bind(("0.0.0.0", port))
  s.listen(5)

  while getattr(t, "running", True):
    c, addr = s.accept()
    threading.Thread(target=new_client, args=(c,addr,)).start()

  for client in clients:
    client['socket'].send("gtfo\n".encode())
    client['socket'].close()

  return

def client_menu(stdscr, c_num):
  with lock:
    client = clients[c_num]

  c_menu = True

  selected = 0

  while c_menu:
    c = stdscr.getch()
    curses.flushinp()

    if (c == curses.KEY_ENTER or c == 10 or c == 13):
      if selected == 0:
        c_menu = False
      elif selected == 1: # Disconnect
        client["socket"].send(b"gtfo\n")
        with lock:
          client["socket"].close()
          clients.remove(client)
        c_menu = False
      elif selected == 2: # Execute Command
        pass
      elif selected == 3: # Download File
        pass
      elif selected == 4: # Upload File
        pass
      elif selected == 5: # Open Shell
        pass
    elif c == curses.KEY_DOWN:
      selected = (selected + 1)%6
    elif c == curses.KEY_UP:
      selected = (selected - 1)%6


    stdscr.clear()

    stdscr.addstr(0,0,"Connected to client", curses.color_pair(5))
    stdscr.addstr(1,0,client["data"],curses.color_pair(3))

    stdscr.addstr(3,0,"<- Back", curses.A_REVERSE if selected == 0 else 0)
    stdscr.addstr(4,0,"Disconnect Client", curses.A_REVERSE if selected == 1 else 0)
    stdscr.addstr(5,0,"Execute Command", curses.A_REVERSE if selected == 2 else 0)
    stdscr.addstr(6,0,"Download File from Client", curses.A_REVERSE if selected == 3 else 0)
    stdscr.addstr(7,0,"Upload File to Client", curses.A_REVERSE if selected == 4 else 0)
    stdscr.addstr(8,0,"Open Shell", curses.A_REVERSE if selected == 5 else 0)

    time.sleep(0.1)



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
    

    if c == ord('q'):
      running = False
    elif curses.KEY_RESIZE == c:
      height,width = stdscr.getmaxyx()
    
    elif c == curses.KEY_DOWN and len(clients) > 0:
      selected = (selected + 1) % len(clients)
    elif c == curses.KEY_UP and len(clients) > 0:
      selected = (selected - 1) % len(clients)

    elif (c == curses.KEY_ENTER or c == 10 or c == 13) and len(clients) > 0:
      client_menu(stdscr, selected)

    stdscr.clear()

    stdscr.addstr(0, 0, "Sammie C2 Server", curses.color_pair(5))
    stdscr.addstr(1, 0, "Connected Clients", curses.color_pair(3))
    stdscr.addstr(height-1, 0, "Press 'q' to quit server")

    with lock:
      if len(clients) == 0:
        stdscr.addstr(3,0,"No clients connected")
      else:
        for i, client in enumerate(clients):
          if i == selected:
            stdscr.addstr(i+3,0,str(i) + ") " + client['data'], curses.A_REVERSE)
          else:
            stdscr.addstr(i+3,0,str(i) + ") " + client['data'])

    stdscr.refresh()

    time.sleep(0.1)


def main():
  args = get_arguments()

  t = threading.Thread(target=listen_for_clients, args=(args.port,))
  t.start()


  try:
    curses.wrapper(nice_menu_function)
  except KeyboardInterrupt:
    pass

  t.running = False

  s = socket.socket()
  s.connect(("127.0.0.1", args.port))
  s.send("EOD\n".encode())
  s.close()

  t.join()

  return


if __name__ == "__main__":
  main()
