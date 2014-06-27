import socket, struct, sys, screen
from random import randint

si = struct.Struct('!I')

def recv_all(sock, length):
    """
    recieves the message until
    the given length is
    recieved
    """
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('socket closed %d bytes into a %d-byte message' % (len(data), length))
        data += more
    return data

def get(sock):
    """
    decides the length
    of the message
    """
    lendata = recv_all(sock, si.size)
    (length,) = si.unpack(lendata)
    return recv_all(sock, length)

def put(sock, message):
    """
    adds message length 
    and sends to the server
    """
    sock.send(si.pack(len(message)) + message.encode('utf-8'))

def relay_msg(clients, port, client, message):
    """
    sends message to multiple clients
    """
    for cli in clients:
        if cli[1] != port:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((cli[2], int(cli[1])))
            put(s, client)
            put(s, message)
            s.close()

def shutdown(stdscr, cliadd, cli, port):
    """
    helps to shutdown when client threads safely
    """
    sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sc.connect((cliadd, port))
    cmd = 'ser:dis`' + cli.get_clientname()
    put(sc, cmd)
    sc.close()
    cli.close()
    screen.stop_screen(stdscr)
    print 'Thank you for using PyGp'
    print 'Contribute --> https://github.com/leosartaj/PyGp'

def server_thread(sc, ser):
    """
    New server thread created
    when connected to a client
    """
    info = sc.getsockname()
    client = get(sc)
    port = get(sc)
    cliadd = sc.getpeername()[0]
    list_clients = ', '.join(str(cli[0]) for cli in ser.get_clients())
    put(sc, list_clients)
    print 'Connected server', info, 'and', client, sc.getpeername(), 'listening on', port
    ser.list_cli.append((client, port, cliadd))
    print 'Clients', ser.get_clients()
    relay_msg(ser.get_clients(), port, client, 'has connected')
    while True:
        try:
            message = get(sc)
        except EOFError:
            print '>>>', client, 'has been disconnected >>>', sc.getpeername()
            relay_msg(ser.get_clients(), port, client, 'has been disconnected')
            sc.close()
            index = ser.list_cli.index((client, port, cliadd))
            del ser.list_cli[index]
            return
        relay_msg(ser.get_clients(), port, client, message)
        print client, port, '>>>', repr(message)

def sendbycli(s, cli, port, stdscr, win_recv):
    """
    Sends the messages
    to the server
    """
    client = cli.get_clientname()
    host = s.getsockname()[0]
    put(s, client)
    put(s, port)
    active = get(s)
    # setting up window
    height, width = cli.get_height(), cli.get_width()
    win = screen.new_window(5, width, height - 5, 0)
    screen.addstr(win, '\n')
    screen.border(win)
    screen.refresh(win)
    if len(active) != 0:
        screen.addstr(win, '  Active users --> ' + active + '\n')
    prev = ''
    while True:
        key = ''
        send = ''
        leng = 0
        if prev != '':
            screen.addstr(win, '  Sent >>> ' + prev + '\n')
        screen.addstr(win, '  Me >>> ', 'bold')
        screen.border(win)
        screen.refresh(win)
        while True:
            key = screen.getch(win)
            if key == '\x7f':
                if send == '':
                    continue
                send = send[:-1]
                leng -= 1
                screen.backspace(win, width)
            elif key == '\n':
                if send == '':
                    continue
                screen.addstr(win, key)
                cli.lines += 1
                break
            elif key == '\x04':
                # shutting down when ctrl+d pressed
                cliadd = s.getsockname()[0]
                shutdown(stdscr, cliadd,  cli, int(port))
                return
            else:
                if leng != (width - 12):
                    screen.addstr(win, key)
                    send += key
                    leng += 1
            screen.refresh(win)
        screen.clear(win)
        screen.addstr(win, '\n')
        screen.uprecv_win(win_recv, 'Me', send)
        screen.overflow_recv(win_recv, cli, height, 13)
        prev = send
        put(s, send)


def recvbycli(host, cli, port, height, win_recv):
    """
    listens on an assigned port
    for messages from other
    clients
    """
    clientname = cli.get_clientname()
    # begin listening
    sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sc.bind((host, port))
    sc.listen(128)
    while True:
        s, sockname = sc.accept()
        client = get(s)
        if client == 'ser:dis`' + clientname:
            s.close()
            sc.close()
            return
        message = get(s)
        cli.lines += 1
        screen.uprecv_win(win_recv, client, message)
        screen.overflow_recv(win_recv, cli, height, 13)
        s.close()

class server:
    """
    implements the server
    """
    def __init__(self, hostname):
        self.port = 8001
        self.hostname = hostname
        self.list_cli = []

    def setup(self, host):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((host, self.port))
        self.s.listen(128)
        self.host = host
        return self.s

    def get_clients(self):
        return self.list_cli

    def get_hostname(self):
        return self.hostname

    def get_host(sefl):
        return self.host

    def get_port(self):
        return self.port

    def close(self):
        self.s.close()

class client:
    """
    Sets up a basic client
    """
    def __init__(self, clientname):
        self.clientname = clientname
        self.ports = []
        self.width = 0
        self.height = 0
        # number of lines written or recieved by client
        self.lines = 0

    def connect(self, host, port):
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        return self.s

    def get_port(self):
        #generates random port for a client
        random_port = randint(9000, 60000)
        while random_port in self.ports:
            random_port = randint(9000, 60000)
        self.ports.append(random_port)
        return (random_port, str(random_port))

    def get_clientname(self):
        return self.clientname

    def get_host(self):
        return self.host

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_lines(self):
        return self.lines

    def close(self):
        self.s.close()
