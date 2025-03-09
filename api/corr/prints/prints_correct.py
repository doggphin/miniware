import os
from typing import List, Tuple
import cv2
from PIL import Image

from corr.color_balance import simplest_cb

PERCENT_TO_CROP = 1


def correct_print(from_path: str, to_dir: str) -> List[str]:
    file_name, file_extension = os.path.splitext(os.path.basename(from_path))
    to_path = os.path.join(to_dir, f"{file_name}{file_extension}")

    # Save DPI for later
    pil_image = Image.open(from_path)
    dpi : Tuple[int, int] = pil_image.info.get("dpi", (None, None))[0]

    image = cv2.imread(from_path)
    
    height, width = image.shape[:2]

    min_dimension = min(width, height)

    crop_amount = int(min_dimension * PERCENT_TO_CROP * 0.01)

    cropped_image = image[crop_amount:height-crop_amount, crop_amount:width-crop_amount]

    color_corrected_and_cropped_image = simplest_cb(cropped_image, 1)

    cv2.imwrite(to_path, color_corrected_and_cropped_image)

    pil_image = Image.open(to_path)
    pil_image.save(to_path, dpi=(dpi, dpi), subsampling=0, quality=95)

    return [to_path]