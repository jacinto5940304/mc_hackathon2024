import tkinter as tk
from PIL import Image, ImageTk

class Vpet(tk.Label):
    def __init__(self, master, gif_path, size=(250,250), delay=5):
        super().__init__(master)
        self.master = master
        self.delay = delay  # Delay in milliseconds between frames
        self.frames = []    # Store the frames of the GIF

        # Open the GIF and extract frames
        gif = Image.open(gif_path)
        try:
            while True:
                frame = gif.copy()
                frame.thumbnail(size, Image.LANCZOS)
                frame = ImageTk.PhotoImage(frame)
                self.frames.append(frame)
                gif.seek(len(self.frames))  # Move to the next frame
        except EOFError:
            pass  # Stop when there are no more frames

        # Start the animation
        self.current_frame = 0
        self.config(image=self.frames[self.current_frame])
        self.after(self.delay, self.animate)

    def animate(self):
        """Update the frame in the GIF animation."""
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.config(image=self.frames[self.current_frame])
        self.after(self.delay, self.animate)

# Create the Tkinter window
# root = tk.Tk()
# root.title("GIF Viewer")

# Load and display the GIF
# gif_viewer = Vpet(root, "../src/vpet.gif")
# gif_viewer.pack()

# Run the Tkinter event loop
# root.mainloop()
