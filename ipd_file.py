from typing import BinaryIO, Tuple, List, Optional

from PIL import Image, ImagePalette
from PIL.Image import FLIP_TOP_BOTTOM


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
    # I hate myself
    return (
            ((
                    (int(0b11111 * (int(pixel[0]) / 255)) << 5) +
                    (int(0b11111 * (int(pixel[1]) / 255)))
            ) << 6) +
            (int(0b111111 * (int(pixel[2]) / 255)))
    )


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


def from_stream(
        stream: BinaryIO,
        *,
        force_flip: Optional[bool] = None
):
    width = int.from_bytes(stream.read(4), "little")
    height = int.from_bytes(stream.read(4), "little")
    flags = int.from_bytes(stream.read(1), "little")
    color_depth = int.from_bytes(stream.read(1), "little")
    stream.seek(6, 1)

    extra_palette = None
    flip_v = False

    if flags == 0b00001000:
        img_mode = "L"
        decoder_mode = "L;4"
        stream.read(32)
        flip_v = True
    elif flags == 0b00000010:
        """
        
        This mode is SPECIAL CASED
        It's 556 ordered RGB data and needs to be flipped
        This can't be done with the raw mode
        
        """

        image = Image.new("RGB", (width, height))
        image.putdata(pixels_from556(stream, (width * height) * 2))
        image = image.transpose(FLIP_TOP_BOTTOM)
        return image
    elif flags == 0b00001010:
        img_mode = "P"
        decoder_mode = "P"
        extra_palette = palette_from565(stream, 512)
        # extra_palette = ImagePalette.raw("RGB;16", stream.read(512))
    elif flags == 0b00000000:
        img_mode = "L"
        decoder_mode = "L"
    elif flags == 0b00000101:
        img_mode = "RGBA"
        decoder_mode = "RGBA"
        flip_v = True
    elif flags == 0b00001001:
        img_mode = "P"
        decoder_mode = "P"
        extra_palette = ImagePalette.raw("RGBA", stream.read(1024))
        flip_v = True
    elif flags == 0b00000001:
        """

        This mode is SPECIAL CASED
        It's **565** ordered RGB data and needs to be flipped
        This can't be done with the raw mode

        """

        image = Image.new("RGB", (width, height))
        image.putdata(pixels_from565(stream, (width * height) * 2))

        return image
    elif flags == 0b00000011:
        img_mode = "L"
        decoder_mode = "L;16"
    else:
        raise NotImplementedError("img not implemented")

    image_data = stream.read(int((width * height) * (color_depth / 8)))

    image = Image.frombytes(
        img_mode,
        (width, height),
        image_data,
        "raw",
        decoder_mode,
        0,
        (-1 if flip_v else 1) if force_flip is None else force_flip  # orientation
    )

    if extra_palette:
        image.putpalette(extra_palette)

    return image


