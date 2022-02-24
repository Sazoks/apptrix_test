from PIL import Image
from typing import Tuple


def set_watermark(input_image_path: str,
                  watermark_image_path: str,
                  position: Tuple[int, int]) -> None:
    """
    Функция для наложения водяного знака.

    :param input_image_path: Путь до исходного изображения.
    :param watermark_image_path: Путь до водяного знака.
    :param position: Координаты левого верхнего угла вотермарки.
    """

    base_image = Image.open(input_image_path)
    watermark = Image.open(watermark_image_path)

    base_image.paste(watermark, position)
    base_image.save(input_image_path)
