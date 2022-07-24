# ipd
Parser for .ipd, an image format used in [iPod games](https://en.wikipedia.org/wiki/IPod_game).

# Format
ipd is a fully little-endian format.

An .ipd image starts with a 16-byte header containing:
- `width`: 4-byte unsigned integer
- `height`: 4-byte unsigned integer
- `flags`: 1-byte
- `color_depth`: 1-byte unsigned integer
- 6 NUL bytes

`flags` determines how to continue parsing the image.
Despite the fact that `ipd` encodes color depth information, it appears that color depth can be determined solely from `flags` alone.

| Flag         | Palette                         | Image                                                 | Flip vertically |
| ------------ | ------------------------------- | ----------------------------------------------------- | --------------- |
| `0b00001000` | 32-byte palette                 | 4-bpp                                                 | Yes             |
| `0b00000010` | Not indexed                     | 16-bpp, 556 order                                     | Yes             |
| `0b00001010` | 512-byte, 16-bpp, 565 order     | 8-bpp                                                 | No              |
| `0b00000000` | Not indexed                     | 8-bpp                                                 | No              |
| `0b00000101` | Not indexed                     | 32-bpp, 8-bpc, RGBA                                   | Yes             |
| `0b00001001` | 1024-byte, 32-bpp, 8-bpc, RGBA  | 8-bpp                                                 | Yes             |
| `0b00000001` | Not indexed                     | 16-bpp, 565 order, RGB                                | Sometimes       |
| `0b00000011` | ?                               | ?                                                     | ?               |

If the image is indexed (ie, the colors map to a palette), read the palette first. Use the table above to determine how much to read.
Next, read ((width*height)*bpp)/8 bytes.
