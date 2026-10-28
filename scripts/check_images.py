from PIL import Image
import numpy as np

for i in range(1, 7):
    img_path = f"D:\\AICTE\\deck\\final\\slides\\slide_{i}.png"
    with Image.open(img_path) as im:
        arr = np.array(im)
        print(f"Slide {i}: size={im.size}, mean_rgb={arr.mean(axis=(0,1))}")

