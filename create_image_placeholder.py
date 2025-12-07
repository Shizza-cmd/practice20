"""
Скрипт для создания заглушки изображения picture.png
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Создание изображения-заглушки
img = Image.new('RGB', (300, 200), color='lightgray')
draw = ImageDraw.Draw(img)

# Рисование рамки
draw.rectangle([10, 10, 290, 190], outline='gray', width=2)

# Текст
try:
    font = ImageFont.truetype("arial.ttf", 24)
except:
    font = ImageFont.load_default()

text = "Нет изображения"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

x = (300 - text_width) // 2
y = (200 - text_height) // 2

draw.text((x, y), text, fill='gray', font=font)

# Сохранение
os.makedirs("app/static/images", exist_ok=True)
img.save("app/static/images/picture.png")
print("Изображение-заглушка создано: app/static/images/picture.png")

