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
            row.append(pixels[y * width + x])
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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Filtry obrazu")
        self.geometry("920x860")
        self.resizable(True, True)

        self.original_image = None
        self.original_preview_tk = None
        self.result_preview_tk = None

        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, padx=16, pady=16)
        top.pack(fill="x")

        btn = tk.Button(top, text="Wczytaj obraz", height=2, command=self.load_image)
        btn.pack(fill="x")

        apply_btn = tk.Button(top, text="Zastosuj filtr", height=2, command=self.apply_filter)
        apply_btn.pack(fill="x", pady=(8, 0))

        panels = tk.Frame(self, padx=16, pady=10)
        panels.pack(fill="x")

        left = tk.Frame(panels)
        left.pack(side="left", padx=(0, 16))

        right = tk.Frame(panels)
        right.pack(side="left")

        self.canvas_left = tk.Canvas(left, width=CANVAS_W, height=CANVAS_H, bg="white", highlightthickness=2)
        self.canvas_left.pack()

        tk.Label(left, text="Oryginał", font=("Helvetica", 18)).pack(pady=(10, 0))

        self.canvas_right = tk.Canvas(right, width=CANVAS_W, height=CANVAS_H, bg="white", highlightthickness=2)
        self.canvas_right.pack()

        tk.Label(right, text="Wynik", font=("Helvetica", 18)).pack(pady=(10, 0))

        controls = tk.Frame(self, padx=16, pady=12)
        controls.pack(fill="both", expand=True)

        tk.Label(controls, text="Filtr:", font=("Helvetica", 20)).grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.filter_var = tk.StringVar(value="mean")

        items = [
            ("Wygładzający (średnia)", "mean"),
            ("Medianowy", "median"),
            ("Sobel", "sobel"),
            ("Binarizacja", "binarize"),
            ("Dylatacja", "dilate"),
            ("Erozja", "erode"),
        ]

        for i, (label, value) in enumerate(items, start=1):
            tk.Radiobutton(
                controls, text=label, value=value, variable=self.filter_var, font=("Helvetica", 18)
            ).grid(row=i, column=0, sticky="w", pady=4)

        params = tk.Frame(controls)
        params.grid(row=1, column=1, rowspan=6, sticky="n", padx=(30, 0))

        tk.Label(params, text="Rozmiar maski:", font=("Helvetica", 18)).grid(row=0, column=0, sticky="e", pady=8)
        self.kernel_size_var = tk.IntVar(value=3)
        tk.Entry(params, textvariable=self.kernel_size_var, width=6, font=("Helvetica", 18)).grid(
            row=0, column=1, sticky="w", padx=(10, 0), pady=8
        )

        tk.Label(params, text="Próg:", font=("Helvetica", 18)).grid(row=1, column=0, sticky="e", pady=8)
        self.threshold_var = tk.IntVar(value=128)
        tk.Entry(params, textvariable=self.threshold_var, width=6, font=("Helvetica", 18)).grid(
            row=1, column=1, sticky="w", padx=(10, 0), pady=8
        )

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Wybierz obraz",
            filetypes=[("Obrazy", "*.png *.jpg *.jpeg *.bmp"), ("Wszystkie pliki", "*.*")],
        )
        if not path:
            return

        img = Image.open(path).convert("RGB")

        self.original_image = img
        self.original_pixels = image_to_pixels(img)

        reconstructed = pixels_to_image(self.original_pixels)

        self._show_on_canvas(self.canvas_left, img, side="left")
        self._show_on_canvas(self.canvas_right, reconstructed, side="right")

    def apply_filter(self):
        if self.original_pixels is None:
            return

        k = self.kernel_size_var.get()
        if k < 1 or k % 2 == 0:
            return

        if self.filter_var.get() == "mean":
            out_pixels = mean_filter(self.original_pixels, k)
        else:
            return

        out_img = pixels_to_image(out_pixels)
        self._show_on_canvas(self.canvas_right, out_img, side="right")

    def _clear_canvas(self, canvas: tk.Canvas):
        canvas.delete("all")

    def _show_on_canvas(self, canvas: tk.Canvas, img: Image.Image, side: str):
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