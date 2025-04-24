import os
from typing import Dict, List, Tuple
import cv2
from PIL import Image

from corr.color_balance import simplest_cb

PERCENT_TO_CROP = 1


def correct_print(from_path: str, to_dir: str, options: Dict[str, any] = None) -> List[str]:
    """
    Crops and color-corrects an image of a print, then saves it to a folder.

    :param from_path: The path to the print image to correct
    :param to_dir: the directory to save the corrected image to
    :param options: Dictionary of options that can control the correction process
        - printsDisableCrop: If True, image cropping is not performed
        - printsDisableColorCorrection: If True, color correction is not performed

    :returns: The name of the path saved to.
    """
    # Initialize options if None
    if options is None:
        options = {}
    
    # Get options with default values and ensure they are boolean
    disable_crop = bool(options.get("printsDisableCrop", False))
    disable_color_correction = bool(options.get("printsDisableColorCorrection", False))
    
    file_name, file_extension = os.path.splitext(os.path.basename(from_path))
    to_path = os.path.join(to_dir, f"{file_name}{file_extension}")

    # Save DPI for later
    pil_image = Image.open(from_path)
    dpi = pil_image.info.get("dpi", (None, None))[0]

    image = cv2.imread(from_path)
    
    # Initialize output image
    out = image
    
    # Perform cropping if not disabled
    if not disable_crop:
        height, width = image.shape[:2]
        min_dimension = min(width, height)
        crop_amount = int(min_dimension * PERCENT_TO_CROP * 0.01)
        out = image[crop_amount:height-crop_amount, crop_amount:width-crop_amount]
    
    # Apply color correction if not disabled
    if not disable_color_correction:
        out = simplest_cb(out, 1)

    # Convert OpenCV image (BGR) to PIL Image (RGB) and save with DPI information
    out_rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    pil_image_out = Image.fromarray(out_rgb)
    pil_image_out.save(to_path, dpi=(dpi, dpi), subsampling=0, quality=95)

    return [to_path]
