import tkinter as tk
from tkinter.filedialog import askopenfilename

# GUI starts here
root = tk.Tk()


# when user click on the browse button it will take them here
# as soon as they click the browse button it will change to loading
def open_file() -> str:
    browse_text.set("Loading")
    file = askopenfilename(parent=root, title='choose a file')

    if file:
        print("file successfully loaded")
        browse_text.set("Browse")

    return file


# background page
canvas = tk.Canvas(root, width=600, height=400)
canvas.grid(columnspan=3)

# instruction
instruction = tk.Label(root, text="Click Browse to select the project that you want to analyze")
instruction.grid(columnspan=3, column=0, row=1)

# browse button -> when user loaded in the file it will say loading not browse
browse_text = tk.StringVar()
browse_button = tk.Button(root, command=lambda: open_file(), textvariable=browse_text)

# setting the initial text in the button
browse_text.set("Browse")
browse_button.grid(column=1, row=2)

# end of the GUI
root.mainloop()
