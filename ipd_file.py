from dataclasses import dataclass
from typing import BinaryIO, Tuple, List, Optional

from PIL import Image, ImagePalette


# pixel formats
def pixel_from565(pixel: int) -> Tuple[int, int, int]:
    return (
        int((pixel >> 11 & 0b11111) * (255 / 0b11111)),
        int((pixel >> 5 & 0b111111) * (255 / 0b111111)),
        int((pixel & 0b11111) * (255 / 0b11111))
    )


def pixel_to565(pixel: Tuple[int, int, int]) -> int:
    return (
            ((
                     (int(0b11111 * (int(pixel[0]) / 255)) << 6) +
                     (int(0b111111 * (int(pixel[1]) / 255)))
             ) << 5) +
            (int(0b11111 * (int(pixel[2]) / 255)))
    )


def pixel_from556(pixel: int) -> Tuple[int, int, int]:
    return (
        int((pixel >> 11 & 0b11111) * (255 / 0b11111)),
        int((pixel >> 6 & 0b11111) * (255 / 0b11111)),
        int((pixel & 0b111111) * (255 / 0b111111))
    )


def pixel_to556(pixel: Tuple[int, int, int]) -> int:
    return (
            ((
                     (int(0b11111 * (int(pixel[0]) / 255)) << 5) +
                     (int(0b11111 * (int(pixel[1]) / 255)))
             ) << 6) +
            (int(0b111111 * (int(pixel[2]) / 255)))
    )


def pixel_from4444(pixel: int) -> Tuple[int, int, int, int]:
    return (
        int(pixel >> 8 & 0b11110000),
        int(pixel >> 4 & 0b11110000),
        int(pixel & 0b11110000),
        int(pixel << 4 & 0b11110000)
    )


# pixel/palette level pixel formats
def palette_from565(stream: BinaryIO, length: int) -> ImagePalette.ImagePalette:
    palette_list = []

    for index in range(length // 2):
        pixel = int.from_bytes(stream.read(2), "little")
        palette_list.extend(pixel_from565(pixel))

    return ImagePalette.ImagePalette(
        mode="RGB",
        palette=palette_list
    )


def pixels_from556(stream: BinaryIO, length: int) -> List[Tuple[int, int, int]]:
    pixels_list = []

    for index in range(length // 2):
        pixel = int.from_bytes(stream.read(2), "little")
        pixels_list.append(pixel_from556(pixel))

    return pixels_list


def pixels_from565(stream: BinaryIO, length: int) -> List[Tuple[int, int, int]]:
    pixels_list = []

    for index in range(length // 2):
        pixel = int.from_bytes(stream.read(2), "little")
        pixels_list.append(pixel_from565(pixel))

    return pixels_list

def pixels_from4444(stream: BinaryIO, length: int) -> List[Tuple[int, int, int, int]]:
    pixels_list = []

    for index in range(length // 2):
        pixel = int.from_bytes(stream.read(2), "little")
        pixels_list.append(pixel_from4444(pixel))

    return pixels_list


# header
@dataclass
class IPDHeader:
    width: int
    height: int
    mode: int
    bits_per_pixel: int


def read_header(stream: BinaryIO):
    width_b = stream.read(4)
    height_b = stream.read(4)
    mode_b = stream.read(1)
    color_depth_b = stream.read(1)
    blank_b = stream.read(6)

    if (
        # fixme! hack alert
        len(width_b) != 4 or
        len(height_b) != 4 or
        len(mode_b) != 1 or
        len(color_depth_b) != 1 or
        len(blank_b) != 6
    ):
        raise ValueError("not enough header data")

    return IPDHeader(
        int.from_bytes(width_b, "little"),
        int.from_bytes(height_b, "little"),
        int.from_bytes(mode_b, "little"),
        int.from_bytes(color_depth_b, "little")
    )


# stream decode
def from_stream(
        stream: BinaryIO,
        *,
        force_flip: Optional[bool] = None
) -> Tuple[IPDHeader, Image.Image]:
    header = read_header(stream)
    width, height, mode, color_depth = header.width, header.height, header.mode, header.bits_per_pixel

    extra_palette = None
    flip_v = False

    if mode == 0x0:
        img_mode = "L"
        decoder_mode = "L"
    elif mode == 0x1:
        """
        special case: RGB in 565 order. this mode isn't supported by Pillow
        """

        image = Image.new("RGB", (width, height))
        image.putdata(pixels_from565(stream, (width * height) * 2))

        if force_flip:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        return header, image
    elif mode == 0x2:
        """
        special case: RGB in 556 order. this mode isn't supported by Pillow
        """
        
        image = Image.new("RGB", (width, height))
        image.putdata(pixels_from556(stream, (width * height) * 2))

        if (force_flip is None) or force_flip:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        return header, image
    elif mode == 0x3:
        """
        special case: RGBA in 4444 order. this mode isn't supported by Pillow
        """
        
        image = Image.new("RGBA", (width, height))
        image.putdata(pixels_from4444(stream, (width * height) * 2))

        if force_flip:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        return header, image
    elif mode == 0x5:
        img_mode = "RGBA"
        decoder_mode = "RGBA"
        flip_v = True
    elif mode == 0x8:
        img_mode = "L"
        decoder_mode = "L;4"
        stream.read(32)
        flip_v = True
    elif mode == 0x9:
        img_mode = "P"
        decoder_mode = "P"
        extra_palette = ImagePalette.raw("RGBA", stream.read(1024))
        flip_v = True
    elif mode == 0xA:
        img_mode = "P"
        decoder_mode = "P"
        extra_palette = palette_from565(stream, 512)
    else:
        raise NotImplementedError(f"mode {mode:08b} not implemented")

    data_length = int((width * height) * (color_depth / 8))
    image_data = stream.read(data_length)
    if len(image_data) != data_length:
        raise ValueError(f"not enough image data! needed {data_length} bytes, got {len(image_data)}")

    image = Image.frombytes(
        img_mode,
        (width, height),
        image_data,
        "raw",
        decoder_mode,
        0,
        (-1 if flip_v else 1) if force_flip is None else (-1 if force_flip else 1)
    )

    if extra_palette:
        image.putpalette(extra_palette)

    return header, image
