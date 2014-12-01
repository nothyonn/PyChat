#!/usr/bin/env python2

##
# PyChat
# https://github.com/leosartaj/PyChat.git
# Copyright (c) 2014 Sartaj Singh
# Licensed under the MIT license.
##

"""
Contains the main GUI Class
"""

# twisted imports
from twisted.python import log
from twisted.internet import reactor

# system imports
from random import choice

# For the GUI
import gtk
from connectBoxClass import connectBoxClass

# Connections
from clientClass import clientClass

# helper modules
from helper import helperFunc as hf
from helper.stack import stack
from helper import markup # functions for formatting text
from helper import notebook # functions for handling notebook

class clientGUIClass:
    """ 
    Sets up the GUI interface
    """
    def __init__(self, name):

        self.name = name # save the client name

        self.builder = hf.load_interface(__file__, 'glade/clientGUI.glade') # load the interface
        self.save_objects() # save objects
        self.builder.connect_signals(self.setup_signals()) # setup signals

        self.chatbox.grab_focus() # focus here
        self.init_variables()
        self.setup_page()
        self.stack = stack() # for upper key and lower key functionality
        self.objects = {} # list of active connections

        self.window.show_all() # display widgets

    def setup_signals(self):
        """
        Sets up the signals
        """
        sig = { 'on_MainWindow_destroy'     : self.close
              , 'on_exit_button_press_event': self.close
              , 'on_chatbox_activate'       : self.sendButton
              , 'on_sendButton_clicked'     : self.sendButton 
              , 'on_connectedusers_toggled' : self.toggleUsersPanel
              , 'on_connect_activate'       : self.set_connect_box
              , 'on_addtab_clicked'         : self.set_connect_box
              , 'on_key_press'              : self.handleKeys 
              , 'on_switch_page'            : self.switch_page }

        return sig


    def save_objects(self):
        """
        Get the required objects
        """
        self.window = self.builder.get_object('MainWindow')
        self.notebook = self.builder.get_object('notebook')
        self.chatbox = self.builder.get_object('chatbox') 

    def init_variables(self):
        """
        initializes various variables
        """
        self.dummypage = True # dummy page
        self.showusers = False
        self.control = False # True if control pressed

    def setup_page(self):
        """
        sets up a new notebook page
        returns the loaded widgets
        """
        builder = hf.load_interface(__file__, 'glade/chatarea.glade')
        widgets = hf.load_chatarea_widgets(self, builder) # get the widgets

        pages = self.notebook.get_n_pages()
        labeltext = 'Tab ' + str(pages)
        label = hf.label(labeltext) # generate a label

        page = notebook.add_page(self.notebook, widgets[1], label)
        notebook.show_tabs(self.notebook) # toggle tabs visibility

        markup.basic_markup(widgets[3], widgets[5]) # set the colors

        widgets.insert(1, page)

        return widgets

    def switch_page(self, *args):
        """
        Focus chatbox when page changed
        """
        gtk.idle_add(self.chatbox.grab_focus) # grab focus after page change

    def toggleUsersPanel(self, widget):
        """
        Toggles the connected users panel
        """
        if self.showusers:
            self.showusers = False
        else:
            self.showusers = True

        def toggle(userPanel):
            """
            Toggle the userpanel
            """
            if self.showusers:
                userPanel.show()
                obj.updateConnUsers('me')
            else:
                userPanel.hide()

        # does not toggle dummy page
        for keys in self.objects:
            obj = self.objects[keys]
            toggle(obj.scrollusers)

    def set_connect_box(self, *args):
        """
        sets up the connection box
        """
        connectBoxClass(self)

    def connect(self, host, port):
        """
        Loads the chatarea
        makes a new notebook page
        Makes a new client object
        saves refrence to the object
        and invokes its connect method
        """
        if self.dummypage:
            self.notebook.remove_page(0) # delete the dummy page
            self.dummypage = False 
        widgets = self.setup_page() # setup a new page
        clientobj = clientClass(self.name, widgets)
        clientobj.connect(host, port)

        self.objects[self.notebook.current_page()] = clientobj # save a reference finally

    def connectionLost(self, clientobj):
        """
        Removes the refrence of the disconnected clientobj
        """
        del self.objects[clientobj.page]
        del clientobj

    def find_clientobj(self):
        """
        Find The current client object
        """
        page = self.notebook.current_page()
        return self.objects[page]

    def sendButton(self, button):
        """
        When the button is clicked
        """
        text = self.chatbox.get_text()
        if text:
            self.stack.push(text) # push the text on stack
            if len(self.objects) != 0:
                self.chatbox.set_text('') # clear the textbox
                obj = self.find_clientobj() # current cliient object
                obj.send(text)
        self.chatbox.grab_focus() # focus the textbox

    def handleKeys(self, widget, key):
        """
        Handles key press
        event in chatbox
        returns last entered text when up key is pressed
        cycles up the stack when down key is pressed
        """
        keyname = gtk.gdk.keyval_name(key.keyval)

        text = None
        if keyname == 'Control_R' or keyname == 'Control_L':
            self.control = True
        elif keyname == 'Left' and self.control:
            self.notebook.prev_page()
        elif keyname == 'Right' and self.control:
            self.notebook.next_page()
        else:
            self.control = False
            if keyname == 'Up':
                text = self.stack.pop()
            elif keyname == 'Down':
                text = self.stack.up()
            else:
                self.stack.reset_point() # reset the pointer

        if text != None:
            self.chatbox.set_text(text)
            self.chatbox.set_position(len(text)) # set the cursor position

    def close(self, *args):
        """
        Handles Destroy Event
        """
        msg = 'Disconnected from server at ' # template for log
        for key in self.objects:
            obj = self.objects[key]
            obj.loseConnection() # lose connection with all servers
            host, port = obj.get_host(), obj.get_port()
            if host != None and port != None:
                address = host + ':' + str(port)
                log.msg(msg + address)
        gtk.main_quit()
