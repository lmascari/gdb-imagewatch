#!/usr/bin/python3

import sys
import os
import ctypes
from ctypes import cdll
import pysigset, signal
import threading
import time

##
# Load imagewatch library and set up its API
script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)
lib = cdll.LoadLibrary(script_path+'/libgdb-imagewatch.so')
lib.plot_binary.argtypes = [ctypes.py_object, # Buffer ptr
                            ctypes.py_object, # Variable name
                            ctypes.c_int, # Buffer width
                            ctypes.c_int, # Buffer height
                            ctypes.c_int, # Number of channels
                            ctypes.c_int, # Type (0=float32, 1=uint8)
                            ctypes.c_int] # Step size (in pixels)
lib.update_plot.argtypes = [ctypes.py_object, # Buffer ptr
                            ctypes.py_object, # Variable name
                            ctypes.c_int, # Buffer width
                            ctypes.c_int, # Buffer height
                            ctypes.c_int, # Number of channels
                            ctypes.c_int, # Type (0=float32, 1=uint8)
                            ctypes.c_int] # Step size (in pixels)
lib.get_observed_variables.argtypes = [ctypes.py_object] # Observed variables
                                                         # set
FETCH_BUFFER_CBK_TYPE = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)
lib.initialize_window.argtypes = [
                              FETCH_BUFFER_CBK_TYPE # Python function to be called
                              ]                # when the user requests a symbol
                                               # name from the viewer interface
lib.update_plot.rettype = ctypes.c_bool # Buffer ptr
lib.update_available_variables.argtypes = [
                              ctypes.py_object # List of available variables in
                              ]                # the current context

def request_buffer_update(variable):
    picked_obj = gdb.parse_and_eval(variable)

    buffer, width, height, channels, type, step = gdbiwtype.get_buffer_info(picked_obj)

    bytes = get_buffer_size(width, height, channels, type, step)
    inferior = gdb.selected_inferior()
    mem = inferior.read_memory(buffer, bytes)

    lib.update_plot(mem, variable, width, height, channels, type, step)
    pass

class MainThreadPlotVariableRunner():
    def __init__(self, variable):
        self.variable = variable;
        pass
    def __call__(self):
        request_buffer_update(self.variable)
        pass
    pass

def plot_variable_cbk(requested_symbol):
    variable = requested_symbol.decode('utf-8')
    gdb.post_event(MainThreadPlotVariableRunner(variable))

    return 0

def initialize_window():
    ##
    # Initialize imagewatch window
    with pysigset.suspended_signals(signal.SIGCHLD):
        # By default, my new threads will be the ones receiving the precious
        # signals from the operating system. These signals should go to GDB so
        # it could do its thing, and since it doesnt get them, my thread will
        # make gdb hang. The solution is to configure the new thread to forward
        # the signal back to the main thread, which is done by pysigset.
        wnd_thread_instance=threading.Thread(target=lib.initialize_window, args=(FETCH_BUFFER_CBK_TYPE(plot_variable_cbk),))
        wnd_thread_instance.daemon=True
        wnd_thread_instance.start()
        pass
    pass

import gdbiwtype

##
# Test application
if len(sys.argv)==2 and sys.argv[1] == '--test':
    import numpy
    import math

    initialize_window()

    width=40
    height=20
    channels=3
    tex = [None]*width*height*channels
    tex2 = [None]*width*height*channels
    for y in range(0,height):
        for x in range(0,width):
            for c in range(0, channels):
                tex[y*channels*width+channels*x+c] = math.cos(x/width*math.pi+
                                                   c/channels*math.pi/4.0)*255
                tex2[y*channels*width+channels*x+c] = 10*x+y
                pass
            pass
        pass

    tex_arr = numpy.asarray(tex, numpy.uint8)
    tex_arr2 = numpy.asarray(tex2, numpy.uint8)
    mem = memoryview(tex_arr)
    mem2 = memoryview(tex_arr2)
    step = width
    lib.plot_binary(mem, 'python_test', width, height, channels, gdbiwtype.GIW_TYPES_UINT8, step)
    lib.plot_binary(mem2, 'python_test2', width, height, channels, gdbiwtype.GIW_TYPES_UINT8, step)

    lib.update_available_variables(['test', 'sample', 'variable', 'hello_world'])

    while lib.is_running():
        time.sleep(0.5)

    lib.terminate()
    exit()
    pass

import gdb

def get_buffer_size(width, height, channels, type, step):
    channel_size = 1
    if type == gdbiwtype.GIW_TYPES_UINT16 or \
       type == gdbiwtype.GIW_TYPES_INT16:
        channel_size = 2 # 2 bytes per element
    elif type == gdbiwtype.GIW_TYPES_INT32 or \
         type == gdbiwtype.GIW_TYPES_UINT32 or \
         type == gdbiwtype.GIW_TYPES_FLOAT32:
        channel_size = 4 # 4 bytes per element
        pass

    return channel_size * channels * step*height

class PlotterCommand(gdb.Command):
    def __init__(self):
        super(PlotterCommand, self).__init__("plot",
                                             gdb.COMMAND_DATA,
                                             gdb.COMPLETE_SYMBOL)
        pass

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        var_name = str(args[0])

        picked_obj = gdb.parse_and_eval(args[0])

        buffer, width, height, channels, type, step = gdbiwtype.get_buffer_info(picked_obj)
      
        bytes = get_buffer_size(width, height, channels, type, step)
        inferior = gdb.selected_inferior()
        mem = inferior.read_memory(buffer, bytes)

        lib.plot_binary(mem, var_name, width, height, channels, type, step)
        pass

    pass

def update_observable_suggestions():
    frame = gdb.selected_frame()
    block = frame.block()
    observable_symbols = list()
    while not block is None:
        for symbol in block:
            if (symbol.is_argument or symbol.is_variable):
                name = symbol.name
                # Get struct/class fields
                if name == 'this':
                    # The GDB API is a bit convoluted, so I have to do some contortion in order
                    # to get the class type from the this object so I can iterate over its fields
                    this_type = gdb.parse_and_eval(symbol.name).dereference().type
                    for field_name, field_val in this_type.iteritems():
                        if (not field_name in observable_symbols) and (gdbiwtype.is_symbol_observable(field_val)):
                            observable_symbols.append(field_name)
                elif (not name in observable_symbols) and (gdbiwtype.is_symbol_observable(symbol)):
                    observable_symbols.append(name)
                    pass
                pass
            pass

        block = block.superblock
        pass

    if lib.is_running():
        lib.update_available_variables(observable_symbols)

    pass

# Update all buffers on each stop event
def stop_event_handler(event):
    if not lib.is_running():
        initialize_window()
        while not lib.is_running():
            time.sleep(0.1)
            pass
        pass

    update_observable_suggestions()

    observed_variables = set()
    lib.get_observed_variables(observed_variables)
    for variable in observed_variables:
        try:
            request_buffer_update(variable)
        except:
            pass
        pass
    pass

##
# Setup GDB interface
PlotterCommand()
gdb.events.stop.connect(stop_event_handler)
