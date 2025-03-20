from typing import List
import cv2
import numpy as np
import math
import argparse
import os
from PIL import Image

from corr.color_balance import simplest_cb

# How far will colors be considered to be background?
# Should be set somewhere between 15-25
BACKGROUND_CROPPING_AGGRESSION = 16
SAMPLING_OFFSET_DISTANCE = 10
ACCEPTABLE_ASPECT_RATIOS = [
    1.5,
    1.33,
    1
]
ACCEPTABLE_ASPECT_RATIO_LENIENCE = 0.04
ACCEPTABLE_TILT = 5
NEGATIVE_PADDING_FACTOR = 1.05


def estimate_tilt_with_min_area_rect(points) -> float:
    # Compute the minimum area rectangle that encloses the points
    rect = cv2.minAreaRect(points)
    # rect returns ((center_x, center_y), (width, height), angle)
    # The angle returned is the rotation of the rectangle
    _, _, angle = rect
    return angle


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
    

def correct_slide(from_path: str, to_dir: str) -> List[str]:
    """
    Crops and color-corrects an image of a slide, then saves it to a folder.

    :param from_path: The path to the slide image to correct
    :param to_dir: the directory to save the corrected image to

    :returns: The name of the path saved to.
    """
    file_name, file_extension = os.path.splitext(os.path.basename(from_path))
    to_path = os.path.join(to_dir, f"{file_name}{file_extension}")
    # to_path = f"{to_dir}/{file_name}"
    
    image = cv2.imread(from_path)
    pil_image = Image.open(from_path)
    
    dpi = pil_image.info.get("dpi", (None, None))[0]

    height, width, _ = image.shape

    offset = SAMPLING_OFFSET_DISTANCE
    bg_colors = [
        tuple(image[height - offset, width // 2]),
        tuple(image[height // 2, width - offset]),
        tuple(image[offset, width // 2]),
        tuple(image[height // 2, offset])
    ]

    could_crop_correctly = False
    for threshhold_offset in [0, 1, -1, 2, -2, 4, -4]:
        threshhold = BACKGROUND_CROPPING_AGGRESSION + threshhold_offset
        
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

        # Compute the difference for the top edge (A -> B)
        delta_x = pt_B[0] - pt_A[0]
        delta_y = pt_B[1] - pt_A[1]

        # Calculate the angle in radians and convert to degrees
        angle_radians = math.atan2(delta_y, delta_x)
        angle_degrees = math.degrees(angle_radians)

        if abs(angle_degrees) > ACCEPTABLE_TILT:
            print(f"Detected tilt on {to_path}: {angle_degrees:.2f}°")
            continue

        width_AD = np.sqrt(((pt_A[0] - pt_D[0]) ** 2) + ((pt_A[1] - pt_D[1]) ** 2))
        width_BC = np.sqrt(((pt_B[0] - pt_C[0]) ** 2) + ((pt_B[1] - pt_C[1]) ** 2))
        max_width = max(int(width_AD), int(width_BC))

        height_AB = np.sqrt(((pt_A[0] - pt_B[0]) ** 2) + ((pt_A[1] - pt_B[1]) ** 2))
        height_CD = np.sqrt(((pt_C[0] - pt_D[0]) ** 2) + ((pt_C[1] - pt_D[1]) ** 2))
        max_height = max(int(height_AB), int(height_CD))

        input_pts = np.float32([pt_A, pt_B, pt_C, pt_D])

        endY = int(max_height * NEGATIVE_PADDING_FACTOR)
        endX = int(max_width * NEGATIVE_PADDING_FACTOR)
        startY = int(endY - max_height)
        startX = int(endX - max_width)

        aspect_ratio = max(max_width, max_height) / min(max_width, max_height)
        
        for acceptable_aspect_ratio in ACCEPTABLE_ASPECT_RATIOS:
            lower_bound = acceptable_aspect_ratio * (1 - ACCEPTABLE_ASPECT_RATIO_LENIENCE)
            upper_bound = acceptable_aspect_ratio * (1 + ACCEPTABLE_ASPECT_RATIO_LENIENCE)
            if aspect_ratio < upper_bound and aspect_ratio > lower_bound:
                could_crop_correctly = True
                break

        if could_crop_correctly:
            output_pts = np.float32([[-startX, -startY],
                                [-startX, endY],
                                [endX, endY],
                                [endX, -startX]])
            break

            # tilt = estimate_tilt_with_min_area_rect(output_pts)
            # tilt %= 90
            # if abs(tilt - 90) < abs(tilt):
            #     tilt = tilt - 90
            # if abs(tilt) > ACCEPTABLE_TILT:
            #     print(f"Tilt of {tilt} was too high!")
            #     continue
            # print(tilt)
    
    if could_crop_correctly:

        # Compute the perspective transform M (stretches image to fit rectangle)
        M = cv2.getPerspectiveTransform(input_pts, output_pts)
        
        # Warp image by perspective transform
        out = cv2.warpPerspective(image, M, (max_width, max_height),flags=cv2.INTER_LINEAR)

        # Could probably skip doing this by rewriting order_points but whatever
        out = cv2.flip(out, 0)
        out = cv2.rotate(out, 0)

        # Apply color balance
        out = simplest_cb(out, 1)
    else:
        print(f"{max_height} {max_width} {aspect_ratio}")
        print("Could not match to a known aspect ratio!")
        out = image

    # Save image to to_path
    cv2.imwrite(to_path, out)

    # Finally, fix DPI of exported image
    pil_image_after = Image.open(to_path)
    pil_image_after.save(to_path, dpi=(dpi, dpi), subsampling=0, quality=95)

    return [to_path]