import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk


CANVAS_W = 420
CANVAS_H = 420


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Filtry obrazu")
        self.geometry("920x760")
        self.resizable(False, False)

        self.original_image = None
        self.original_preview_tk = None
        self.result_preview_tk = None

        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, padx=16, pady=16)
        top.pack(fill="x")

        btn = tk.Button(top, text="Wczytaj obraz", height=2, command=self.load_image)
        btn.pack(fill="x")

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

        self.original_image = Image.open(path).convert("RGB")
        self._show_on_canvas(self.canvas_left, self.original_image, side="left")
        self._clear_canvas(self.canvas_right)

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