import cv2
import numpy as np
import math
import argparse
import os
from PIL import Image

# To Eric: set these to True or False to enable color and/or crop corrections
# \/ \/ \/ \/
DO_COLOR = True
DO_CROP = True
# /\ /\ /\ /\

def apply_mask(matrix, mask, fill_value):
    masked = np.ma.array(matrix, mask=mask, fill_value=fill_value)
    return masked.filled()

def apply_threshold(matrix, low_value, high_value):
    low_mask = matrix < low_value
    matrix = apply_mask(matrix, low_mask, low_value)

    high_mask = matrix > high_value
    matrix = apply_mask(matrix, high_mask, high_value)

    return matrix

def simplest_cb(img, percent):
    assert img.shape[2] == 3
    assert percent > 0 and percent < 100

    half_percent = percent / 200.0

    channels = cv2.split(img)

    out_channels = []
    for channel in channels:
        assert len(channel.shape) == 2
        # find the low and high precentile values (based on the input percentile)
        height, width = channel.shape
        vec_size = width * height
        flat = channel.reshape(vec_size)

        assert len(flat.shape) == 1

        flat = np.sort(flat)

        n_cols = flat.shape[0]

        low_val  = flat[math.floor(n_cols * half_percent)]
        # Extremely evil bandaid
        try:
            high_val = flat[math.ceil( n_cols * (1.0 - half_percent))]
        except:
            high_val = flat[math.ceil( n_cols * (1.0 - half_percent)) - 1]

        # saturate below the low percentile and above the high percentile
        thresholded = apply_threshold(channel, low_val, high_val)
        # scale the channel
        normalized = cv2.normalize(thresholded, thresholded.copy(), 0, 255, cv2.NORM_MINMAX)
        out_channels.append(normalized)

    return cv2.merge(out_channels)


# TODO: Fix this to do necessary rotations + flips here
def order_points(pts):
    # Sort the points by x and y to determine top-left, top-right, bottom-right, and bottom-left
    rect = np.zeros((4, 2), dtype="float32")
    
    # Sum the x and y coordinates to find the top-left and bottom-right points
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left point has the smallest sum
    rect[2] = pts[np.argmax(s)]  # bottom-right point has the largest sum

    # Subtract the x and y coordinates to find the top-right and bottom-left points
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right point has the smallest difference (x - y)
    rect[3] = pts[np.argmax(diff)]  # bottom-left point has the largest difference (x - y)
    
    return rect
    

# Returns the 
def correct_slide(from_path: str, to_dir: str) -> str:
    """
    Crops and color-corrects an image of a slide, then saves it to a folder.

    :param from_path: The path to the slide image to correct
    :param to_dir: the directory to save the corrected image to

    :returns: The name of the path saved to.
    """
    file_name = from_path.split("/")[-1]
    to_path = f"{to_dir}/{file_name}"
    
    image = cv2.imread(from_path)
    pil_image = Image.open(from_path)
    dpi = pil_image.info.get("dpi", (None, None))[0]

    if(DO_CROP):
        height, width, _ = image.shape

        offset = 10
        bg_colors = [
            tuple(image[height - offset, width // 2]),
            tuple(image[height // 2, width - offset]),
            tuple(image[offset, width // 2]),
            tuple(image[height // 2, offset])
        ]
        threshhold = 20

        output_image = np.ones_like(image) * 0

        for color in bg_colors:
            distance = np.linalg.norm(image - np.array(color), axis=2)
            mask = distance < threshhold
            output_image[mask] = (255, 255, 255)

        kernel = np.ones((8, 8), np.float32)
        output_image = cv2.filter2D(output_image, -1, kernel)

        output_image = cv2.bitwise_not(output_image)

        gray_output = cv2.cvtColor(output_image, cv2.COLOR_BGR2GRAY)
        _, binary_output = cv2.threshold(gray_output, 1, 255, cv2.THRESH_BINARY)

        (contours, _) = cv2.findContours(binary_output, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Variables to store the largest rotated rectangle
        largest_area = 0
        largest_box = None

        # Loop through the contours to find the largest rotated rectangle
        for contour in contours:
            rect = cv2.minAreaRect(contour)  # Get the rotated rectangle
            box = cv2.boxPoints(rect)       # Get the 4 corner points of the rectangle
            box = np.int32(box)              # Convert to integer coordinates

            # Calculate the area of the rectangle
            width, height = rect[1]
            area = width * height

            # Check if this is the largest rectangle so far
            if area > largest_area:
                largest_area = area
                largest_box = box

        if largest_box is None:
            print(f"Could not box {from_path}!")
            return

        ordered_box = order_points(largest_box)

        pt_A, pt_B, pt_C, pt_D = ordered_box
        width_AD = np.sqrt(((pt_A[0] - pt_D[0]) ** 2) + ((pt_A[1] - pt_D[1]) ** 2))
        width_BC = np.sqrt(((pt_B[0] - pt_C[0]) ** 2) + ((pt_B[1] - pt_C[1]) ** 2))
        max_width = max(int(width_AD), int(width_BC))

        height_AB = np.sqrt(((pt_A[0] - pt_B[0]) ** 2) + ((pt_A[1] - pt_B[1]) ** 2))
        height_CD = np.sqrt(((pt_C[0] - pt_D[0]) ** 2) + ((pt_C[1] - pt_D[1]) ** 2))
        max_height = max(int(height_AB), int(height_CD))

        input_pts = np.float32([pt_A, pt_B, pt_C, pt_D])

        endY = int(max_height * 1.04)
        endX = int(max_width * 1.04)
        startY = int(endY - max_height)
        startX = int(endX - max_width)
        output_pts = np.float32([[-startX, -startY],
                                [-startX, endY],
                                [endX, endY],
                                [endX, -startX]])

        # Compute the perspective transform M (stretches image to fit rectangle)
        M = cv2.getPerspectiveTransform(input_pts,output_pts)
        
        # Warp image by perspective transform
        out = cv2.warpPerspective(image, M, (max_width, max_height),flags=cv2.INTER_LINEAR)

        # Could probably skip doing this by rewriting order_points but whatever
        out = cv2.flip(out, 0)
        out = cv2.rotate(out, 0)
    else:
        out = image     # Shitty implementation for do_color/do_crop to make functional, refactor later

    if(DO_COLOR):
        out = simplest_cb(out, 1)

    # Save image to to_path
    cv2.imwrite(to_path, out)

    # Finally, fix DPI of exported image
    pil_image_after = Image.open(to_path)
    pil_image_after.save(to_path, dpi=(dpi, dpi))

    return to_path


def correct_all_slides_in_folder(from_folder_path: str, to_folder_path: str):
    all_files = sorted(os.listdir(from_folder_path))
    print(all_files)
    for i, file in enumerate(all_files):
        path = f"{from_folder_path}/{file}"
        saved_to_path = correct_slide(path, to_folder_path)
        print(f"Corrected {i + 1}/{len(all_files)} (Saved to {saved_to_path})")


'''
parser = argparse.ArgumentParser()
parser.add_argument("from_folder", type=str, help="path to uncorrected slide image file")
parser.add_argument("to_folder", type=str, help="path to folder to which corrected image file will be stored")
args = parser.parse_args()
print(args.from_folder)
print(args.to_folder)
correct_all_slides_in_folder(args.from_folder, args.to_folder)
'''