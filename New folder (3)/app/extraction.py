import os
import cv2
import pytesseract
import json
import numpy as np

# Set Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Directory paths
UPLOAD_FOLDER = 'app/uploads/'
RESULTS_FOLDER = 'app/results/'

# Preprocessing function
def preprocess_image(image_path):
    original_image = cv2.imread(image_path)
    if original_image is None:
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    high_contrast = cv2.equalizeHist(denoised)
    binarized = cv2.adaptiveThreshold(
        high_contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    coords = np.column_stack(np.where(binarized > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    else:
        angle = -angle

    if abs(angle) > 1:
        (h, w) = binarized.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(binarized, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    else:
        deskewed = binarized

    return original_image, deskewed

# Text extraction function
def extract_text(image, lang='eng'):
    return pytesseract.image_to_string(image, lang=lang)

# Main function
def main(image_path):
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)
    
    original_img, processed_img = preprocess_image(image_path)
    extracted_text = extract_text(processed_img, lang='eng+tam')

    # Save as text file
    text_file_path = os.path.join(RESULTS_FOLDER, 'extracted_text.txt')
    with open(text_file_path, 'w') as text_file:
        text_file.write(extracted_text)

    # Save as JSON file
    json_file_path = os.path.join(RESULTS_FOLDER, 'extracted_text.json')
    with open(json_file_path, 'w') as json_file:
        json.dump({"extracted_text": extracted_text}, json_file)

    print(f"Text saved to {text_file_path} and {json_file_path}")
    return json_file_path

if __name__ == '__main__':
    test_image = f'{UPLOAD_FOLDER}/sample_image.png'  # Replace with the actual file path
    main(test_image)