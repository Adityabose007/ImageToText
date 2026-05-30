import cv2
import easyocr
import matplotlib.pyplot as plt
import os
import difflib
from deep_translator import GoogleTranslator


# ===== 1️⃣ Load Image =====
image_path = r'D:\projects\Intern Project\data\test6.jpg'
img = cv2.imread(image_path)

if img is None:
    print("❌ Failed to load image. Check path or file name.")
    exit()

# ===== Preprocess for better OCR accuracy =====
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.bilateralFilter(gray, 9, 75, 75)  # noise reduction
gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)  # increase contrast

# ===== 2️⃣ Initialize EasyOCR for English + Hindi =====
reader = easyocr.Reader(['en', 'hi'], gpu=True)

# ===== 3️⃣ Read text =====
results = reader.readtext(gray)
threshold = 0.4  # higher confidence threshold
detected_texts = []

# ===== 4️⃣ Create output folder for cropped text images =====
output_crops_folder = os.path.join(os.path.dirname(image_path), "cropped_texts")
os.makedirs(output_crops_folder, exist_ok=True)

# ===== Overlay for transparent text =====
overlay = img.copy()

# ===== Hindi variants of "Chinchpokli" =====
hindi_variants = ["चिंचपोकळी", "चिंचपोकली", "चिंचपोकळि", "चिंचपोकळ", "चिनचपोकली"]

# ===== 5️⃣ Process Detected Text =====
for idx, (bbox, text, score) in enumerate(results):
    if score > threshold:
        text_clean = text.strip()

        # Detect Hindi vs English
        if any('\u0900' <= ch <= '\u097F' for ch in text_clean):
            lang_name = "Hindi"
        else:
            lang_name = "English"

        translated_text = None
        if lang_name == "Hindi":
            try:
                # Fuzzy match for "Chinchpokli"
                for variant in hindi_variants:
                    similarity = difflib.SequenceMatcher(None, text_clean, variant).ratio()
                    if similarity > 0.75:
                        translated_text = "CHINCHPOKLI"
                        break
                # Normal translation if not Chinchpokli
                if not translated_text:
                    translated_text = GoogleTranslator(source='hi', target='en').translate(text_clean)
            except Exception as e:
                print(f"⚠ Translation failed for '{text_clean}': {e}")

        # Save to log
        if translated_text:
            detected_texts.append(f"{text_clean} | Language: {lang_name} | Translated: {translated_text}")
        else:
            detected_texts.append(f"{text_clean} | Language: {lang_name}")

        # Coordinates
        x_min = min(int(pt[0]) for pt in bbox)
        y_min = min(int(pt[1]) for pt in bbox)
        x_max = max(int(pt[0]) for pt in bbox)
        y_max = max(int(pt[1]) for pt in bbox)

        # Draw only for English in blue, Hindi replaced by translation in blue
        display_text = translated_text if translated_text else text_clean
        cv2.putText(overlay, display_text, (x_min, y_min - 5),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 0, 0), 2)  # blue

        # Save cropped text image
        cropped_img = img[y_min:y_max, x_min:x_max]
        crop_filename = os.path.join(output_crops_folder, f"text_crop_{idx+1}_{lang_name}.png")
        cv2.imwrite(crop_filename, cropped_img)

# ===== 6️⃣ Blend overlay for transparency =====
alpha = 0.8  # transparency level
img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

# ===== 7️⃣ Save detected text to file =====
output_txt_path = os.path.join(os.path.dirname(image_path), "detected_text.txt")
with open(output_txt_path, "w", encoding="utf-8") as f:
    for line in detected_texts:
        f.write(line + "\n")

print(f"✅ Processed text saved to: {output_txt_path}")
print(f"✅ Cropped text images saved in: {output_crops_folder}")

# ===== 8️⃣ Show Image =====
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.axis('off')
plt.show()