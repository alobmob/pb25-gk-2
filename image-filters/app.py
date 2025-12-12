import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

CANVAS_W = 420
CANVAS_H = 420


def image_to_pixels(img):
    width, height = img.size
    pixels = list(img.getdata())
    data = []

    for y in range(height):
        row = []
        for x in range(width):
            row.append(list(pixels[y * width + x]))
        data.append(row)

    return data


def pixels_to_image(data):
    height = len(data)
    width = len(data[0])

    img = Image.new("RGB", (width, height))
    flat = []

    for y in range(height):
        for x in range(width):
            flat.append(tuple(data[y][x]))

    img.putdata(flat)
    return img


def clamp(v, lo, hi):
    return max(lo, min(v, hi))


def mean_filter(pixels, kernel_size):
    h = len(pixels)
    w = len(pixels[0])
    k = kernel_size // 2

    result = [[[0, 0, 0] for _ in range(w)] for _ in range(h)]

    for y in range(h):
        for x in range(w):
            rs = gs = bs = count = 0

            for dy in range(-k, k + 1):
                for dx in range(-k, k + 1):
                    yy = clamp(y + dy, 0, h - 1)
                    xx = clamp(x + dx, 0, w - 1)

                    r, g, b = pixels[yy][xx]
                    rs += r
                    gs += g
                    bs += b
                    count += 1

            result[y][x][0] = rs // count
            result[y][x][1] = gs // count
            result[y][x][2] = bs // count

    return result


def median_filter(pixels, kernel_size):
    h = len(pixels)
    w = len(pixels[0])
    k = kernel_size // 2

    result = [[[0, 0, 0] for _ in range(w)] for _ in range(h)]

    for y in range(h):
        for x in range(w):
            rs, gs, bs = [], [], []

            for dy in range(-k, k + 1):
                for dx in range(-k, k + 1):
                    yy = clamp(y + dy, 0, h - 1)
                    xx = clamp(x + dx, 0, w - 1)

                    r, g, b = pixels[yy][xx]
                    rs.append(r)
                    gs.append(g)
                    bs.append(b)

            rs.sort()
            gs.sort()
            bs.sort()
            m = len(rs) // 2

            result[y][x] = [rs[m], gs[m], bs[m]]

    return result


def to_grayscale(pixels):
    h = len(pixels)
    w = len(pixels[0])
    gray = [[0 for _ in range(w)] for _ in range(h)]

    for y in range(h):
        for x in range(w):
            r, g, b = pixels[y][x]
            gray[y][x] = int(0.299 * r + 0.587 * g + 0.114 * b)

    return gray


def sobel_filter(pixels):
    h = len(pixels)
    w = len(pixels[0])

    gray = to_grayscale(pixels)
    result = [[[0, 0, 0] for _ in range(w)] for _ in range(h)]

    gx_kernel = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    gy_kernel = [[1, 2, 1], [0, 0, 0], [-1, -2, -1]]

    for y in range(h):
        for x in range(w):
            gx = gy = 0

            for ky in range(-1, 2):
                for kx in range(-1, 2):
                    yy = clamp(y + ky, 0, h - 1)
                    xx = clamp(x + kx, 0, w - 1)
                    p = gray[yy][xx]

                    gx += p * gx_kernel[ky + 1][kx + 1]
                    gy += p * gy_kernel[ky + 1][kx + 1]

            mag = clamp(abs(gx) + abs(gy), 0, 255)
            result[y][x] = [mag, mag, mag]

    return result


def binarize_filter(pixels, threshold, invert):
    gray = to_grayscale(pixels)
    h = len(gray)
    w = len(gray[0])

    result = [[[0, 0, 0] for _ in range(w)] for _ in range(h)]

    for y in range(h):
        for x in range(w):
            if not invert:
                v = 255 if gray[y][x] >= threshold else 0
            else:
                v = 0 if gray[y][x] >= threshold else 255
            result[y][x] = [v, v, v]

    return result


DEFAULT_STRUCT_ELEMENT = [
    [1, 1, 1],
    [1, 1, 1],
    [1, 1, 1],
]


def dilate(pixels, struct):
    h = len(pixels)
    w = len(pixels[0])
    sh = len(struct)
    sw = len(struct[0])
    cy = sh // 2
    cx = sw // 2

    result = [[[0, 0, 0] for _ in range(w)] for _ in range(h)]

    for y in range(h):
        for x in range(w):
            found = False
            for sy in range(sh):
                for sx in range(sw):
                    if struct[sy][sx] == 0:
                        continue
                    yy = y + sy - cy
                    xx = x + sx - cx
                    if 0 <= yy < h and 0 <= xx < w:
                        if pixels[yy][xx][0] == 255:
                            found = True
                            break
                if found:
                    break
            v = 255 if found else 0
            result[y][x] = [v, v, v]

    return result


def erode(pixels, struct):
    h = len(pixels)
    w = len(pixels[0])
    sh = len(struct)
    sw = len(struct[0])
    cy = sh // 2
    cx = sw // 2

    result = [[[0, 0, 0] for _ in range(w)] for _ in range(h)]

    for y in range(h):
        for x in range(w):
            ok = True
            for sy in range(sh):
                for sx in range(sw):
                    if struct[sy][sx] == 0:
                        continue
                    yy = y + sy - cy
                    xx = x + sx - cx
                    if not (0 <= yy < h and 0 <= xx < w):
                        ok = False
                        break
                    if pixels[yy][xx][0] != 255:
                        ok = False
                        break
                if not ok:
                    break
            v = 255 if ok else 0
            result[y][x] = [v, v, v]

    return result


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Filtry obrazu")
        self.geometry("920x860")
        self.resizable(True, True)

        self.original_pixels = None
        self.original_preview_tk = None
        self.result_preview_tk = None

        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, padx=16, pady=16)
        top.pack(fill="x")

        tk.Button(top, text="Wczytaj obraz", height=2, command=self.load_image).pack(fill="x")
        tk.Button(top, text="Zastosuj filtr", height=2, command=self.apply_filter).pack(fill="x", pady=(8, 0))

        panels = tk.Frame(self, padx=16, pady=10)
        panels.pack(fill="x")

        self.canvas_left = tk.Canvas(panels, width=CANVAS_W, height=CANVAS_H, bg="white")
        self.canvas_left.pack(side="left", padx=8)

        self.canvas_right = tk.Canvas(panels, width=CANVAS_W, height=CANVAS_H, bg="white")
        self.canvas_right.pack(side="left", padx=8)

        controls = tk.Frame(self, padx=16, pady=12)
        controls.pack(fill="both", expand=True)

        self.filter_var = tk.StringVar(value="mean")

        for text, val in [
            ("Wygładzający", "mean"),
            ("Medianowy", "median"),
            ("Sobel", "sobel"),
            ("Binarizacja", "binarize"),
            ("Dylatacja", "dilate"),
            ("Erozja", "erode"),
        ]:
            tk.Radiobutton(controls, text=text, variable=self.filter_var, value=val).pack(anchor="w")

        self.kernel_size_var = tk.IntVar(value=3)
        self.threshold_var = tk.IntVar(value=128)
        self.invert_var = tk.BooleanVar(value=False)

        tk.Label(controls, text="Rozmiar maski").pack(anchor="w")
        tk.Entry(controls, textvariable=self.kernel_size_var).pack(anchor="w")

        tk.Label(controls, text="Próg").pack(anchor="w")
        tk.Entry(controls, textvariable=self.threshold_var).pack(anchor="w")

        tk.Checkbutton(controls, text="Odwróć binarizację", variable=self.invert_var).pack(anchor="w")

    def load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        img = Image.open(path).convert("RGB")
        self.original_pixels = image_to_pixels(img)

        self._show(self.canvas_left, img, "left")
        self._show(self.canvas_right, img, "right")

    def apply_filter(self):
        if self.original_pixels is None:
            return

        mode = self.filter_var.get()
        k = self.kernel_size_var.get()
        t = self.threshold_var.get()
        inv = self.invert_var.get()

        if mode in ("mean", "median") and (k < 1 or k % 2 == 0):
            return

        if mode == "mean":
            out = mean_filter(self.original_pixels, k)
        elif mode == "median":
            out = median_filter(self.original_pixels, k)
        elif mode == "sobel":
            out = sobel_filter(self.original_pixels)
        elif mode == "binarize":
            out = binarize_filter(self.original_pixels, t, inv)
        elif mode == "dilate":
            out = dilate(binarize_filter(self.original_pixels, t, inv), DEFAULT_STRUCT_ELEMENT)
        elif mode == "erode":
            out = erode(binarize_filter(self.original_pixels, t, inv), DEFAULT_STRUCT_ELEMENT)
        else:
            return

        self._show(self.canvas_right, pixels_to_image(out), "right")

    def _show(self, canvas, img, side):
        preview = img.copy()
        preview.thumbnail((CANVAS_W, CANVAS_H))
        tk_img = ImageTk.PhotoImage(preview)
        canvas.delete("all")
        canvas.create_image(CANVAS_W // 2, CANVAS_H // 2, image=tk_img)
        if side == "left":
            self.original_preview_tk = tk_img
        else:
            self.result_preview_tk = tk_img


if __name__ == "__main__":
    App().mainloop()