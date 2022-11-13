import tkinter as tk
from tkinter import Entry, Label


def start_gui():
    # GUI starts here
    root = tk.Tk()
    root.title("Cyclomatic Complexity Analyzer")

    def error_invaild(label):
        label.set("Please enter a vaild Github URL")

    # when user click on the browse button it will take them here
    # as soon as they click the browse button it will change to loading
    def open_file() -> str:
        submitt_text.set("Loading...")
        url = input_box.get()

        # Given GitHub URL is not vaild then we prompt the user NEED TO TEST
        # if not check_github_url(url):
        #    error_invaild(instraction)

        # TODO: call the backend here!!!

        submitt_text.set("Enter")

    # background page
    canvas = tk.Canvas(root, width=600, height=400)
    canvas.grid(columnspan=5)

    # instraction
    instraction = tk.StringVar()
    instraction.set("To start please enter a vaild GitHub URL")

    instraction_label = Label(textvariable=instraction)
    instraction_label.grid(column=1, row=0)

    # input box
    input_box = Entry(root, borderwidth=5)
    input_box.grid(column=0, row=1)

    # setting the initial text in the button
    submitt_text = tk.StringVar()
    submitt_text.set("Enter")

    # browse button -> when user loaded in the file it will say loading not browse
    browse_button = tk.Button(root, command=lambda: open_file(), textvariable=submitt_text)
    browse_button.grid(column=1, row=2)

    # end of the GUI
    root.mainloop()
