#!/usr/bin/env python2

##
# PyGp
# https://github.com/leosartaj/PyGp.git
#
# Copyright (c) 2014 Sartaj Singh
# Licensed under the MIT license.
##

"""
This file initializes the server or the client
"""
import chat, sys, threading, screen

HOST = sys.argv.pop() if len(sys.argv) == 4 else '127.0.0.1'

if sys.argv[1:2] == ['server']:
    ser = chat.server(sys.argv.pop())
    s = ser.setup(HOST)
    print 'Listening at', s.getsockname()
    threads = []
    while True:
        threads_copy = threads
        # remove dead threads
        for thread in threads_copy:
            if not thread.isAlive():
                index = threads.index(thread)
                del threads[index]
        try:
            sc, sockname = s.accept()
            # start a new server thread
            thr = threading.Thread(target=chat.server_thread, args=(sc, ser))
            threads.append(thr)
            thr.start()
        except:
            print '\nPyGp --> Server Has been shutdown'
            for thread in threads:
                thread.join()
            sys.exit()

elif sys.argv[1:2] == ['client']:
    # connecting to server
    cli = chat.client(sys.argv.pop())
    s = cli.connect(HOST, 8001)
    client = cli.get_clientname()
    port =chat.get(s)
    port_int = int(port)
    name = ' '.join(str(name) for name in s.getsockname())
    # setting up the window
    stdscr = screen.setup_screen()
    cli.height, cli.width = stdscr.getmaxyx()
    height, width = cli.get_height(), cli.get_width()
    screen.info_screen(width, name, port)
    win_recv = screen.new_window(height - 12, width, 6, 0)
    # new client thread for sending
    threading.Thread(target=chat.sendbycli, args=(s, cli, port_int, stdscr, win_recv)).start()
    # new client thread for listening
    threading.Thread(target=chat.recvbycli, args=(s.getsockname()[0], cli, port_int, height, win_recv)).start()

else:
    print >>sys.stderr, 'usage: ./ChatCli.py server|client [username] [host]'
