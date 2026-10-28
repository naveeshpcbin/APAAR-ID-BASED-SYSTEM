from PIL import Image

slide_paths = [f"D:\\AICTE\\deck\\final\\slides\\slide_{i}.png" for i in range(1, 7)]
images = [Image.open(p) for p in slide_paths]

# Create a 3 cols x 2 rows contact sheet
thumb_w, thumb_h = 640, 360
sheet = Image.new("RGB", (thumb_w * 3 + 40, thumb_h * 2 + 30), (240, 243, 246))

for idx, img in enumerate(images):
    col = idx % 3
    row = idx // 3
    x = 10 + col * (thumb_w + 10)
    y = 10 + row * (thumb_h + 10)
    resized = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    sheet.paste(resized, (x, y))

contact_path = r"D:\AICTE\deck\final\contact_sheet.png"
sheet.save(contact_path)
print(f"Saved contact sheet to {contact_path}")

