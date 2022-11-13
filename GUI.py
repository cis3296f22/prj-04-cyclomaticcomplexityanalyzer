import tkinter as tk
from tkinter import Entry, Label


def show_result(dataframe):
    result = tk.Tk()

    text_box = tk.Text(result, height=10, width=50)

    result.mainloop()


def start_gui():
    # GUI starts here
    root = tk.Tk()
    root.title("Cyclomatic Complexity Analyzer")

    def error_invaild(label):
        label.set("Please enter a valid Github URL")

    # when user click on the browse button it will take them here
    # as soon as they click the browse button it will change to loading
    def get_url():
        submit_text.set("Loading...")
        url = input_box.get()

        # Given GitHub URL is not valid then we prompt the user NEED TO TEST
        # if not check_github_url(url):
        #    error_invalid(instruction)

        # TODO: call the backend here!!!
        #  dataframe = some_function(url)
        #  show_result(dataframe)

        submit_text.set("Enter")

    # background page
    canvas = tk.Canvas(root, width=600, height=400)
    canvas.grid(columnspan=5)

    # instruction
    instruction = tk.StringVar()
    instruction.set("To start please enter a valid GitHub URL")

    instruction_label = Label(textvariable=instruction)
    instruction_label.grid(column=1, row=0)

    # input box
    input_box = Entry(root, borderwidth=5)
    input_box.grid(column=0, row=1)

    # setting the initial text in the button
    submit_text = tk.StringVar()
    submit_text.set("Enter")

    # browse button -> when user loaded in the file it will say loading not browse
    browse_button = tk.Button(root, command=lambda: get_url(), textvariable=submitt_text)
    browse_button.grid(column=1, row=2)

    # end of the GUI
    root.mainloop()
