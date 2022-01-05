#!/usr/bin/env python

# ============================================================================ #
#                                                                              #
#                               Indicator Applet                               #
#                                                                              #
# ============================================================================ #


# Gtk for menus.
from gi.repository import Gtk
# AppIndicator3 for the indicator APIs.
from gi.repository import AppIndicator3
# JavaScript Object Notation tools for importing and exporting data.
import json
# getcwd() for finding the working directory.
from os import getcwd
# shlex.split sh commands to pass into other commands.
import shlex
# Allows ctrl + c to terminate (for command line testing).
import signal
# subprocess.popen for running commands.
import subprocess
# Using for CLI arguments.
import sys


# Icon used by indicator.
ICON_PATH = '\
/usr/share/icons/ubuntu-mono-dark/actions/24/system-shutdown-panel.svg'

# What the menu displays and what the buttons do. (Handled in build_menu)
# [Type, Label, Action]
MENU_ITEMS_SETTINGS = \
                [
                    ['button', 'System Settings...', 'unity-control-center'],
                    #['Nonsense', 'Test'],
                    #['button', 'TEST', 'shutdown -h now'],
                    ['separator', 'NULL', 'NULL'],
                    ['button', 'Lock', 'dm-tool lock'],
                    ['button', 'Logout', 'bspc quit'],
                    ['separator', 'NULL', 'NULL'],
                    ['button', 'Restart', 'shutdown -r now'],
                    ['button', 'Shutdown', 'shutdown -h now']
                ]

SEPARATOR_STRING = \
                '- - - - - - - - - - - - - - - - - - - - - - - - - - - -'

HELP_MESSAGE = \
                'Usage:     '+str(sys.argv[0])+' {options} {config file}\n'+\
                'Options:   -h: Display this message.\n'+\
                '           -g: Generate default config file.\n'+\
                '           -c: Specify config file to use.\n'+\
                '           -i: Specify image file to use.\n'+\
                SEPARATOR_STRING+'\n\n'

# exit(ERRMSG) for maximum lazy. 
ERRMSG = 1

# Menu class
class Menu:
    # Initializing variables for init args.
    menu_items_settings = []
    icon_path_setting = ''

    # Initialize Menu object instance.
    def __init__(self, iconpath, menuitemssettings = []):
        self.menu_items_settings = menuitemssettings
        self.icon_path_setting = iconpath
        self.parse_arguments()
        # Create indicator.
        # For some reason this does not throw an error when a non image file is
        #+provided to it, it just displays no image. This try: does nothing.
        try:
            indicator = AppIndicator3.Indicator.new('AppIndicator3Instance', \
                                                    self.icon_path_setting, 0)
        except:
            ERRMSG = 1
            for i in sys.argv:
                if i == '-i':
                    print "Indicator creation failed, try checking icon file."
                    exit(ERRMSG)
            print "Indicator creation failed."
            exit(ERRMSG)
        # Needs activating to appear.
        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        # Couldn't get this to work with stalonetray.
        #indicator.set_ordering_index(1)
        # Call he menu creation function and get a pointer to the menu.
        indicator.set_menu(self.build_menu())
        # Start main loop.
        self.main()

    # Import config file and store in self.menu_items_settings.
    def do_config_import(self, configfile):
        # Import a config file.
        print 'Attempting import of config file located at: '+configfile
        # Attmpt to open json file and read, otherwise use default settings.
        try:
            fd = open(configfile, 'r')
        except:
            # If the file could not be opened then use the default.
            print 'Opening config file failed, using default settings.'
        else:
            # Attempt to parse and save the contents.
            try:
                self.menu_items_settings = json.loads(fd.read())
            except:
                print 'Config import failed, using default settings.'
            else:
                print 'Config import success, using imported settings.'
            finally:
                # Always close the file afterward.
                fd.close()

    # Parse CLI arguments.
    def parse_arguments(self):
        # Make pretty separator in CLI.
        print '\n\n'+SEPARATOR_STRING
        # Are there any arguments? If so, parse them.
        if len(sys.argv) > 1:
            # Increment this on failiure of loop, decrement whenever an argument
            #+which has a trailing argument is used.
            # Don't bother if the argument makes the program exit immediately.
            invalid_options = 0
            # Check for options first.
            for i in range(len(sys.argv)):
                # Help screen.
                if sys.argv[i] == '-h':
                    print HELP_MESSAGE
                    ERRMSG = 0
                    exit(ERRMSG)
                # Generate config file.
                if sys.argv[i] == '-g':
                    print 'Generating default config file in '+\
                          'current working directory.'
                    # Create, write to and close the new config file.
                    try:
                        # Open/create the file in the current working directory.
                        new_config_file_fd = \
                        open(getcwd()+'/.SystemMenuSettings.json', 'w')
                        new_config_file_fd.write\
                        (json.dumps(self.menu_items_settings))
                    except:
                        print 'File creation failed.'
                        # Set the error message for use in finally.
                        ERRMSG = 1
                    else:
                        print 'File creation success.'
                        # Set the error message for use in finally.
                        ERRMSG = 0
                    finally:
                        # Always close this file.
                        # Doesn't matter if it fails because sometimes this file
                        #+descriptor doesn't exist as it was never created.
                        try:
                            new_config_file_fd.close()
                        except:
                            pass
                        # Make pretty separator in CLI.
                        print SEPARATOR_STRING+'\n\n'
                        # Program always exits here but with different message
                        #+depending on whether the file was successfuly created.
                        exit(ERRMSG)
                # Import config file.
                elif sys.argv[i] == '-c':
                    self.do_config_import(str(sys.argv[i+1]))
                    invalid_options = invalid_options - 1
                # Import icon file.
                elif sys.argv[i] == '-i':
                    # Open the file to check it exists and there is read access.
                    # There is no check for if it is the correct file type, but
                    #+there is a try: around the use of this file to handle
                    #+incorrect files being given to the program.
                    try:
                        # Opening with read perms doesn't allow file creation.
                        icon = open(str(sys.argv[i+1]), 'r')
                        # Close here because if we got this far it must exist
                        #+and if we can't close then there is a problem.
                        icon.close()
                    except:
                        print 'Icon file inaccessable.'
                        ERRMSG = 1
                        exit(ERRMSG)
                    else:
                        # Set the icon.
                        self.icon_path_setting = str(sys.argv[i+1])
                        invalid_options = invalid_options - 1
                else:
                    invalid_options = invalid_options + 1
            if invalid_options > 0:
                print 'Some invalid CLI arguments, '+\
                      'defaults used where appropriate.'
        else:
            print 'No CLI arguments, using default settings.'
        # Make pretty separator in CLI.
        print SEPARATOR_STRING+'\n\n'

    # Creates the menu items.
    # *arguments to ignore the arguments passed to it by setmenu() since they're
    #+not used in this function.
    def build_menu(self, *arguments):
        # New menu object.
        menu = Gtk.Menu()
        # Empty list of menu items.
        menu_item = []
        # Empty list of separators.
        menu_item_separator = []

        # Execute the command, has menu_item argument for compatability.
        # GTK insists that it send an argument containing the menu item ID.
        def execute_this(menu_item, command):
            subprocess.Popen(shlex.split(command))
        # Appends a menu item to menu_item.
        def append_menu_item(menuitem, menuname, name, command):
                menuitem.append(Gtk.MenuItem(name))
                menuitem[-1].connect('activate', execute_this, command)
                menuname.append(menu_item[-1])
        # Creates a separator.
        def append_menu_item_separator(menuitemseparator, menuname):
            menuitemseparator.append(Gtk.SeparatorMenuItem())
            menuname.append(menu_item_separator[-1])

        # Parse menu_items_settings to populate the menu.
        for i in self.menu_items_settings:
            # Check if the items are all there.
            try:
                tmp = i[0]
                tmp = i[1]
                tmp = i[2]
            except:
                print   "One or more of the required "+\
                        "values for a menu item does "+\
                        "not exist, ignoring."
            else:
                # Check the menu item type is valid.
                valid = ['button', 'separator']
                assert(i[0] in valid), \
                        "\'%s\' is not a valid menu item type." % i[0]

                # Create menu items and append them.
                if i[0] == 'button':
                    append_menu_item(menu_item, menu, i[1], i[2])
                # Don't check again if a previous check was successful.
                elif i[0] == 'separator':
                    append_menu_item_separator(menu_item_separator, menu)
                #else
                    # If something unexpected is here just ignore it.

        # Show it all.
        menu.show_all()
        # Returning the menu to the indicator.set_menu function that calls this.
        return menu

    # Main program loop.
    def main(self):
        # GTK main function will loop for us, no need for more code.
        Gtk.main()


if __name__ == '__main__':
    # Recognize ctrl + c input for testing in command line.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    # create instance of appmenu.
    system_menu_instance = Menu(ICON_PATH, MENU_ITEMS_SETTINGS)
