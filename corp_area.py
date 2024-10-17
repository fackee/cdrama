import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class VideoCropper(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Cropper")
        self.geometry("1000x1000")

        self.canvas = tk.Canvas(self, width=540, height=960)
        self.canvas.pack()

        self.btn_open = tk.Button(self, text="Open Video", command=self.open_video)
        self.btn_open.pack()

        self.btn_crop = tk.Button(self, text="Crop Area", command=self.calculate_crop_area_ratio)
        self.btn_crop.pack()

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.crop_area = None
        self.video_path = None
        self.cap = None
        self.frame = None
        self.frame_tk = None
        self.paused = False

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def open_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        if not self.video_path:
            return
        self.cap = cv2.VideoCapture(self.video_path)
        self.paused = False
        self.show_frame()

    def show_frame(self):
        if not self.paused:
            ret, self.frame = self.cap.read()
            if ret:
                self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                self.frame = Image.fromarray(self.frame)
                self.frame = self.frame.resize((540, 960), Image.Resampling.LANCZOS)
                self.frame_tk = ImageTk.PhotoImage(self.frame)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.frame_tk)
        self.after(30, self.show_frame)

    def on_button_press(self, event):
        self.paused = True
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        self.crop_area = (self.start_x, self.start_y, end_x, end_y)
        print(f"Crop area: {self.crop_area}")
        self.paused = False

    def calculate_crop_area_ratio(self):
        if self.crop_area:
            x1, y1, x2, y2 = self.crop_area
            frame_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            frame_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            x_ratio1 = x1 / 540
            y_ratio1 = y1 / 960
            x_ratio2 = x2 / 540
            y_ratio2 = y2 / 960
            crop_area_ratio = (x_ratio1, y_ratio1, x_ratio2 - x_ratio1, y_ratio2 - y_ratio1)
            print(f"Crop area ratio: {crop_area_ratio}")
            return crop_area_ratio

if __name__ == "__main__":
    app = VideoCropper()
    app.mainloop()
