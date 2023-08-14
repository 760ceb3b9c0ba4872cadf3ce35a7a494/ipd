# ipd
python library for parsing the ipd format, an image format used in [iPod games](https://en.wikipedia.org/wiki/IPod_game).

# example
read an .ipd image and convert it to .png:
```py
from pathlib import Path
import ipd_file

input_path = Path("/path/to/input.ipd")
output_path = Path("/path/to/output.png")

with open(input_path, "rb") as stream:
    header, image = ipd_file.from_stream(stream)
    image.save(output_path)
```

# format
ipd is a fully little-endian format.

an .ipd image starts with a 16-byte header containing:
- `width`: 4 byte unsigned integer
- `height`: 4 byte unsigned integer
- `mode`: 1 byte
- `color_depth`: 1 byte unsigned integer
- 6 null bytes

`mode` determines how to parse the rest of the data, including the number of bits per pixel (making the color_depth field redundant)

## mode table
if you encounter an ipd image with a mode that isnt listed here, make an issue!
|  mode | palette color count | palette color format      | bits per pixel | pixel format       | flip vertically? |
| ----: | ------------------: | :------------------------ | -------------: | :----------------- | :--------------- |
| `0x0` |                     |                           |              8 | grayscale          | no               |
| `0x1` |                     |                           |             16 | RGB in 565 order   | sometimes        |
| `0x2` |                     |                           |             16 | RGB in 556 order   | yes              |
| `0x3` |                     |                           |             16 | RGBA in 4444 order | sometimes        |
| `0x5` |                     |                           |             32 | RGBA in 8888 order | yes              |
| `0x8` |                  16 | 32 bytes (can be ignored) |              4 | grayscale          | yes              |
| `0x9` |                 256 | RGBA in 8888 order        |              8 | indexed            | yes              |
| `0xA` |                 256 | RGB in 565 order          |              8 | indexed            | no               |
