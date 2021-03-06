# gdb-imagewatch
An OpenGL based advanced buffer visualization tool for GDB.

![](https://raw.githubusercontent.com/csantosbh/gdb-imagewatch/master/doc/sample_window.png)

## Features

* GUI interactivity: Scroll to zoom, left click+drag to move the buffer around.
* Buffer values: Zoom in close enough to see the numerical values of the
  buffer.
* Auto update: Whenever a breakpoint is hit, the buffer view is automatically
  updated.
* Auto contrast
* Editable contrast clamp values, useful when inspecting a buffer that contains
  uninitialized values.
* Link views together, moving all watched buffers when a single buffer is moved
  on the screen
* GPU accelerated
* Supported buffer types: uint8_t, int16_t, uint16_t, int32_t, uint32_t and float
* Supported buffer channels: Grayscale, two-channels, RGB and RGBA
* Supports big buffers whose dimensions exceed GL_MAX_TEXTURE_SIZE.
* Supports data structures that map to a ROI of a bigger buffer.
* Exports buffers as png images (with auto contrast) or octave matrix files
  (unprocessed).
* Rotate buffers 90&deg; clockwise or counterclockwise.

## Requirements

 * An OpenGL 4.0+ compliant GPU
 * A C++11 compliant compiler (gcc-4.9 or later is recommended)

## Installation

### Dependencies

GDB-ImageWatch requires python 3+, lib freetype 2, Qt SDK, GLEW, GLFW, Qt 4.8+ and GDB 7.10+
(which must be compiled with python 3 support). On Ubuntu:

    sudo apt-get install libpython3-dev libglew-dev python3-numpy python3-pip qt-sdk texinfo libfreetype6-dev
    sudo pip3 install pysigset

Download and install the latest GDB (if you already don't have it):

    wget http://ftp.gnu.org/gnu/gdb/gdb-7.10.tar.gz
    tar -zxvf gdb-7.10.tar.gz
    cd gdb-7.10
    ./configure --with-python=python3 --disable-werror
    make -j8
    sudo make install

Finally, download and install [GLFW3][1].

### Build plugin and configure GDB

To build this plugin, create a `build` folder, open a terminal window inside it
and run:

    qmake ..
    make -j4
    make install

The `make install` step is absolutely required, and will only copy the
dependencies to the build folder (thus, it doesn't require any special user
privileges).

Now edit the `~/.gdbinit` file and append the following line: 

    source /path/to/gdb-imagewatch/build/gdb-imagewatch.py



## Advanced configuration

By default, the plugin works with OpenCV `Mat` structures, i.e. it assumes that
your buffer data structure has the following signature:

```cpp
struct Buffer {
    void* data;
    int cols; // Width
    int rows; // Height
    int flags; // OpenCV flags
    struct {
       int buf[2]; // Buf[0] = width of the containing
                   // buffer*channels; buff[1] = channels
    } step;
};
```

If you use a different buffer type, you need to adapt the file
`resources/gdbiwtype.py` to your needs. This is actually pretty simple and only
involves editing the functions `get_buffer_info()` and
`is_symbol_observable()`.

The function `get_buffer_info()` must return a tuple with the following fields,
in order:

 * **buffer** Pointer to the buffer
 * **width**  Width of the ROI
 * **height** Height of the ROI 
 * **channels** Number of color channels (currently, only 1 and 3 are
   supported)
 * **type** Identifier for the type of the underlying buffer. The supported
   values are:
   * `GIW_TYPES_UINT8` = 0
   * `GIW_TYPES_UINT16` = 2
   * `GIW_TYPES_INT16` = 3
   * `GIW_TYPES_INT32` = 4
   * `GIW_TYPES_FLOAT32` = 5
   * `GIW_TYPES_UINT32` = 6

 * **step** Width, in pixels, of the underlying containing buffer. If the ROI
   is the total buffer size, this is the same of the buffer width.

The function `is_symbol_observable()` receives a gdb symbol and only returns
`True` if that symbol is of the observable type (the buffer you are dealing
with). By default, it works well with the `cv::Mat` type.

For more information on how to customize this file, check out this [more
detailed blog post](https://csantosbh.wordpress.com/2016/10/15/configuring-gdb-imagewatch-to-visualize-custom-buffer-types/).

## Using plugin

When GDB hits a breakpoint, the imagewatch window will be opened. You only need
to type the name of the buffer to be watched in the "add symbols" input, and
press `<enter>`.

Alternatively, you can also invoke the imagewatch window from GDB with the
following command:

    plot variable_name

### Loading Octave/Matlab buffers
Buffers exported in the `Octave matrix` format can be loaded with the function
`giw_load.m`, which is installed in the binary folder. To use it, add this
folder to Octave/Matlab `path` variable and call `giw_load('/path/to/buffer')`.

### Configure your IDE to use GDB 7.10

If you're not using gdb from the command line, make sure that your IDE is
correctly configured to use GDB 7.10. On QtCreator, go to
`Tools`->`Options`->`Build & Run`->`Debuggers` and make sure that the
configured path references a compatible GDB version.


[1]: http://www.glfw.org/
