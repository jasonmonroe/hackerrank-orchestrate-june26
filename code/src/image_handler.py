# code/src/image_handler.py

# Python Libraries
import base64
import mimetypes
import os
from PIL import Image

# Local Libraries
from src.constants import DATASET_DIR

class ImageHandler:
    def __init__(self, eda_flag: bool):

        # Initialize any necessary attributes here
        self.filenames = []
        self.images = []

        self._base_dir = DATASET_DIR
        self._eda_flag = eda_flag

    def load(self, image_paths: list) -> None:
        """
        Load images and encode them, set the filenames.

        :param image_paths:
        :return:
        """

        if image_paths:
            self.images, self.filenames = self.encode(image_paths)


    def encode(self, image_paths: list) -> tuple:
        """
        Encodes images to base64 data URLs and extracts clean filenames.

        :param image_paths: List of relative paths from the CSV (e.g. ['images/test/case_001/img_1.jpg'])
        :return: A tuple of (encoded_images_list, filenames_list)
        """
        encoded_images = []
        filenames = []

        for path in image_paths:
            if self._eda_flag:
                self.describe(path)

            full_path = os.path.normpath(os.path.join(self._base_dir, path))

            if not os.path.exists(full_path):
                print(f"⚠️ Warning: Image file not found: {full_path}. Skipping this image.")
                continue

            filenames.append(os.path.basename(full_path))
            mime_type, _ = mimetypes.guess_type(full_path)

            if not mime_type:
                mime_type = "image/jpeg"

            with open(full_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")

            image_data = f"data:{mime_type};base64,{base64_image}"
            encoded_images.append(image_data)

        return encoded_images, filenames

    def describe(self, relative_path: str) -> tuple:
        """
        Safely inspects an image file to extract width, height, and channels
        without crashing the pipeline or using huge amounts of memory.
        """
        full_path = os.path.normpath(os.path.join(self._base_dir, relative_path))

        if not os.path.exists(full_path):
            print(f"⚠️ Image not found for description: {full_path}")
            return 0, 0, 0

        with Image.open(full_path) as img:
            width, height = img.size
            # Get channels (e.g., RGB = 3, RGBA = 4, L = 1)
            channels = len(img.getbands())

            print('\n--- 🏞️ Describing Image 🏞 ---')
            print(f"File: {os.path.basename(relative_path)}")
            print(f"Width: {width}, Height: {height}, Channels: {channels}")

            return width, height, channels
