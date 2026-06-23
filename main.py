import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageGrab, ImageTk # pyright: ignore[reportMissingImports]
import os
import datetime
import sys
import socket

class CropBox:
    def __init__(self, canvas, img_x, img_y, img_w, img_h):
        self.canvas = canvas
        self.rect = None
        self.handles = [None] * 8
        self.handle_size = 6
        self.coords = [img_x, img_y, img_x + img_w, img_y + img_h]
        self.active_handle = None
        self.mask_img = None # Reference for the dimmed overlay

        # Dimming mask: Create a single image item on the canvas
        self.mask_item = self.canvas.create_image(0, 0, anchor="nw", tags="mask")

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def create(self):
        self.rect = self.canvas.create_rectangle(*self.coords, outline="red", width=2, tags="crop")
        for i in range(8):
            h = self.canvas.create_oval(0, 0, 0, 0, fill="red", tags="handle")
            self.handles[i] = h
        self.update_handles()

    def update_handles(self):
        x1, y1, x2, y2 = self.coords
        
        self.update_mask() # Refresh the overlay

        points = [
            (x1, y1), (x2, y1), (x2, y2), (x1, y2),
            ((x1+x2)/2, y1), (x2, (y1+y2)/2), ((x1+x2)/2, y2), (x1, (y1+y2)/2)
        ]
        for i, (x, y) in enumerate(points):
            self.canvas.coords(self.handles[i], x-self.handle_size, y-self.handle_size, 
                               x+self.handle_size, y+self.handle_size)
        self.canvas.coords(self.rect, x1, y1, x2, y2)

    def on_press(self, event):
        item = self.canvas.find_withtag("current")
        if item:
            for i, h in enumerate(self.handles):
                if h == item[0]:
                    self.active_handle = i
                    break

    def on_drag(self, event):
        if self.active_handle is not None:
            x, y = event.x, event.y
            x1, y1, x2, y2 = self.coords

            img_x1, img_y1 = self.canvas.bbox(self.canvas.find_withtag("all")[0])[:2]
            img_x2 = img_x1 + (x2 - x1)
            img_y2 = img_y1 + (y2 - y1)

            x = max(img_x1, min(x, self.canvas.winfo_width()))
            y = max(img_y1, min(y, self.canvas.winfo_height()))
            
            if self.active_handle == 0: self.coords[0], self.coords[1] = x, y
            elif self.active_handle == 1: self.coords[2], self.coords[1] = x, y
            elif self.active_handle == 2: self.coords[2], self.coords[3] = x, y
            elif self.active_handle == 3: self.coords[0], self.coords[3] = x, y
            elif self.active_handle == 4: self.coords[1] = y
            elif self.active_handle == 5: self.coords[2] = x
            elif self.active_handle == 6: self.coords[3] = y
            elif self.active_handle == 7: self.coords[0] = x
            self.update_handles()

    def on_release(self, event):
        self.active_handle = None

    def update_mask(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        # full dim overlay (transparent black)
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        # ONLY dim the image area (important)
        ix1, iy1, ix2, iy2 = self.canvas.bbox("all")  # fallback-safe

        # fallback if bbox fails
        if ix1 is None:
            return

        # crop box coords
        x1, y1, x2, y2 = map(int, self.coords)
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))

        # clamp to screen
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        # STEP 1: dim EVERYTHING
        dim = Image.new("RGBA", (w, h), (0, 0, 0, 120))
        overlay = Image.alpha_composite(overlay, dim)

        # STEP 2: punch out crop area (make it clear again)
        if x2 > x1 and y2 > y1:
            hole = Image.new("RGBA", (x2 - x1, y2 - y1), (0, 0, 0, 0))
            overlay.paste(hole, (x1, y1))

        # apply to canvas
        self.mask_img = ImageTk.PhotoImage(overlay)
        self.canvas.itemconfig(self.mask_item, image=self.mask_img)

        # IMPORTANT: layering order
        self.canvas.tag_raise(self.mask_item)
        if self.rect:
            self.canvas.tag_raise(self.rect)

        for h in self.handles:
            if h:
                self.canvas.tag_raise(h)

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipCrop")
        self.root.state('zoomed')
        
        self.padding = 50
        self.canvas = tk.Canvas(root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Shortcuts
        self.root.bind_all("<Control-v>", lambda event: self.load_image())
        self.root.bind_all("<Control-s>", lambda event: self.save_crop())
        self.root.bind_all("<Control-x>", lambda event: self.clear_canvas())
        self.root.bind_all("<Escape>", self.minimize)
        # Change quit to Ctrl+Shift+X
        self.root.bind_all("<Control-Shift-x>", lambda event: self.quit_app())
        
        control_frame = tk.Frame(root)
        control_frame.pack(fill=tk.X)
        
        tk.Button(control_frame, text="Paste (Ctrl+V)", command=self.load_image).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(control_frame, text="Save (Ctrl+S)", command=self.save_crop).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(control_frame, text="Clear (Ctrl+X)", command=self.clear_canvas).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(control_frame, text="Quit (Ctrl+Shift+X)", command=self.quit_app).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.original_image = None
        self.scale_factor = 1.0
        self.img_pos = (0, 0)
        self.crop_box = None

    def load_image(self):
        img = ImageGrab.grabclipboard()
        if not img: return
        self.original_image = img
        self.root.update()
        avail_w = self.root.winfo_width() - (self.padding * 2)
        avail_h = self.root.winfo_height() - (self.padding * 2) - 50
        
        w, h = img.size
        self.scale_factor = min(avail_w/w, avail_h/h)
        display_w, display_h = int(w * self.scale_factor), int(h * self.scale_factor)
        display_img = img.resize((display_w, display_h), Image.Resampling.LANCZOS)
        
        x = (self.root.winfo_width() - display_w) // 2
        y = (self.root.winfo_height() - display_h - 50) // 2
        self.img_pos = (x, y)
        
        self.tk_img = ImageTk.PhotoImage(display_img)
        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(x, y, image=self.tk_img, anchor="nw")
        self.canvas.tag_lower(self.image_id)

        self.crop_box = CropBox(self.canvas, x, y, display_w, display_h)
        self.crop_box.create()

    def clear_canvas(self):
        self.canvas.delete("all")
        self.original_image = None
        self.crop_box = None

    def save_crop(self):
        if not self.original_image or not self.crop_box: return
        x1, y1, x2, y2 = self.crop_box.coords
        x1 -= self.img_pos[0]; y1 -= self.img_pos[1]
        x2 -= self.img_pos[0]; y2 -= self.img_pos[1]
        
        left = int(min(x1, x2) / self.scale_factor)
        top = int(min(y1, y2) / self.scale_factor)
        right = int(max(x1, x2) / self.scale_factor)
        bottom = int(max(y1, y2) / self.scale_factor)
        
        cropped = self.original_image.crop((left, top, right, bottom))
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = filedialog.asksaveasfilename(
            initialfile=f"{timestamp}.png",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")]
        )
        if file_path: cropped.save(file_path)

    def minimize(self, event=None):
        self.root.iconify()

    def quit_app(self):
        self.root.quit()
        self.root.destroy()
        sys.exit()

def start_app():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 54321))
        s.listen(1)
    except socket.error:
        sys.exit()

    root = tk.Tk()
    try: root.iconbitmap("icon.ico")
    except: pass
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    start_app()