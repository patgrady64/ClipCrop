import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageGrab, ImageTk

class CropBox:
    def __init__(self, canvas, img_width, img_height):
        self.canvas = canvas
        self.rect = None
        # 0: TL, 1: TR, 2: BR, 3: BL (corners)
        # 4: Top, 5: Right, 6: Bottom, 7: Left (sides)
        self.handles = [None] * 8
        self.handle_size = 6
        self.coords = [0, 0, img_width, img_height]
        self.active_handle = None

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
        # 0: TL, 1: TR, 2: BR, 3: BL
        # 4: Top-Mid, 5: Right-Mid, 6: Bottom-Mid, 7: Left-Mid
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
            # Corners: 0(TL), 1(TR), 2(BR), 3(BL)
            if self.active_handle == 0: self.coords[0], self.coords[1] = x, y
            elif self.active_handle == 1: self.coords[2], self.coords[1] = x, y
            elif self.active_handle == 2: self.coords[2], self.coords[3] = x, y
            elif self.active_handle == 3: self.coords[0], self.coords[3] = x, y
            # Sides: 4(Top), 5(Right), 6(Bottom), 7(Left)
            elif self.active_handle == 4: self.coords[1] = y
            elif self.active_handle == 5: self.coords[2] = x
            elif self.active_handle == 6: self.coords[3] = y
            elif self.active_handle == 7: self.coords[0] = x
            
            self.update_handles()

    def on_release(self, event):
        self.active_handle = None

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipCrop Pro")
        self.root.geometry("800x600")
        
        self.canvas = tk.Canvas(root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        control_frame = tk.Frame(root)
        control_frame.pack(fill=tk.X)
        
        tk.Button(control_frame, text="Paste Image", command=self.load_image).pack(side=tk.LEFT)
        tk.Button(control_frame, text="Save Crop", command=self.save_crop).pack(side=tk.LEFT)
        
        self.original_image = None
        self.scale_factor = 1.0

    def load_image(self):
        img = ImageGrab.grabclipboard()
        if not img: return
        self.original_image = img
        w, h = img.size
        max_w, max_h = 800, 600
        if w > max_w or h > max_h:
            self.scale_factor = min(max_w/w, max_h/h)
            display_img = img.resize((int(w * self.scale_factor), int(h * self.scale_factor)), Image.Resampling.LANCZOS)
        else:
            self.scale_factor = 1.0
            display_img = img
            
        self.tk_img = ImageTk.PhotoImage(display_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        self.crop_box = CropBox(self.canvas, display_img.width, display_img.height)
        self.crop_box.create()

    def save_crop(self):
        if not self.original_image: return
        x1, y1, x2, y2 = self.crop_box.coords
        left = int(min(x1, x2) / self.scale_factor)
        top = int(min(y1, y2) / self.scale_factor)
        right = int(max(x1, x2) / self.scale_factor)
        bottom = int(max(y1, y2) / self.scale_factor)
        cropped = self.original_image.crop((left, top, right, bottom))
        file_path = filedialog.asksaveasfilename(defaultextension=".png")
        if file_path: cropped.save(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()