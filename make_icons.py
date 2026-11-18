"""產生 PWA 圖示(只需執行一次,已附上產生好的 PNG)"""
from PIL import Image, ImageDraw

TEAL_TOP, TEAL_BOTTOM = (20, 184, 166), (13, 148, 136)


def gradient(size):
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(TEAL_TOP[i] + (TEAL_BOTTOM[i] - TEAL_TOP[i]) * t) for i in range(3))
        for x in range(size):
            px[x, y] = c
    return img


def draw_glyph(img, scale):
    """白色資料表圖示;scale 控制佔畫面的比例(maskable 需留安全區)"""
    s = img.size[0]
    d = ImageDraw.Draw(img)
    w = s * scale
    x0 = y0 = (s - w) / 2
    x1 = y1 = x0 + w
    r = w * 0.12
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill="white")
    header_h = w * 0.24
    d.rounded_rectangle([x0, y0, x1, y0 + header_h], radius=r, fill=(15, 118, 110))
    d.rectangle([x0, y0 + header_h - r, x1, y0 + header_h], fill=(15, 118, 110))
    line = max(2, int(w * 0.025))
    grey = (148, 163, 184)
    rows = 3
    for i in range(1, rows + 1):
        y = y0 + header_h + (w - header_h) * i / (rows + 0.0) - (w - header_h) / rows * 0.0
        if i < rows:
            d.line([x0 + w * 0.06, y, x1 - w * 0.06, y], fill=grey, width=line)
    for i in (1, 2):
        x = x0 + w * i / 3
        d.line([x, y0 + header_h, x, y1 - w * 0.06], fill=grey, width=line)
    return img


def make(size, name, scale, rounded):
    img = draw_glyph(gradient(size), scale)
    if rounded:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=size * 0.22, fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(img, (0, 0), mask)
        img = out
    img.save(f"pwa/icons/{name}")


make(192, "icon-192.png", 0.56, True)
make(512, "icon-512.png", 0.56, True)
make(512, "icon-maskable-512.png", 0.46, False)   # 滿版背景 + 安全區內圖案
make(180, "apple-touch-icon.png", 0.50, False)    # iOS 自動套圓角
print("icons done")
