from PIL import Image


def set_watermark(input_image_path: str,
                  watermark_image_path: str) -> None:
    """
    Функция для наложения водяного знака.

    :param input_image_path: Путь до исходного изображения.
    :param watermark_image_path: Путь до водяного знака.
    """

    base_image = Image.open(input_image_path)
    watermark = Image.open(watermark_image_path)

    # Позиция для наложения водяного знака в px.
    position = (0, 0)

    base_image.paste(watermark, position)
    base_image.save(input_image_path)


if __name__ == '__main__':
    set_watermark('/')
