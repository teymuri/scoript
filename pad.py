
"""
smtpad: the text editor for smt
"""

import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
# # import score
# # import cmn
# from lang import *
from lang import *
from cmn import *
from engine import render



s="""
[note [pitch [list 123 4 5 6 7]]]
[! F5 [note [pitch 65]]]
[pitch F5]
[? F5 pitch]


"""




# def render_toplevel():
    # D = SW.drawing.Drawing(filename="/tmp/smt.svg", size=(pgw,pgh), debug=True)
    # """
    # for obj in _smtns:if obj.toplevel:
    # """
    # for obj in smt_toplevel:
        # if obj.toplevel:
            # obj._apply_rules()
            # # Form's packsvglst will call packsvglst on descendants recursively
            # obj._pack_svg_list()
            # for elem in obj._svg_list:
                # D.add(elem)
    # D.save(pretty=True)




def open_file():
    """Open a file for editing."""
    filepath = askopenfilename(
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not filepath:
        return
    txt_edit.delete(1.0, tk.END)
    with open(filepath, "r") as input_file:
        text = input_file.read()
        txt_edit.insert(tk.END, text)
    window.title(f"{CAPTION} - {filepath}")

def save_file():
    """Save the current file as a new file."""
    filepath = asksaveasfilename(
        defaultextension="txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
    )
    if not filepath:
        return
    with open(filepath, "w") as output_file:
        text = txt_edit.get(1.0, tk.END)
        output_file.write(text)
    window.title(f"{CAPTION} - {filepath}")


def evalsrc(e):
    with open("etude.txt", "w") as output_file:
        text = txt_edit.get(1.0, tk.END)
        output_file.write(text)
    # window.title(f"{CAPTION} - {filepath}")
    with open("etude.txt", "r") as src:
        for toplevel_expr in toplevels(index_tokens(tokenize_source(src.read()))):
            evalexp(read_from_tokens(toplevel_expr))

# paredit
def insert_rbracket(_):
    txt_edit.mark_gravity(tk.INSERT, tk.LEFT)
    txt_edit.insert(txt_edit.index(tk.INSERT), CLOSE)
    txt_edit.mark_gravity(tk.INSERT, tk.RIGHT)

CAPTION = "SMTPad"

window = tk.Tk()
window.title(CAPTION)
window.rowconfigure(0, minsize=300, weight=1)
window.columnconfigure(1, minsize=250, weight=1)

txt_edit = tk.Text(window)
fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
btn_open = tk.Button(fr_buttons, text="Open", command=open_file)
btn_save = tk.Button(fr_buttons, text="Save As", command=save_file)

window.bind("<Control_L>e", evalsrc)
# window.bind("[", lambda e: txt_edit.insert(tk.INSERT-1, "]"))
window.bind(OPEN, insert_rbracket)
# btn_eval = tk.Button(fr_buttons, text="eval", command=evalsrc)


btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
btn_save.grid(row=1, column=0, sticky="ew", padx=5)
# btn_eval.grid(row=2, column=0, sticky="ew", padx=5)

fr_buttons.grid(row=0, column=0, sticky="ns")
txt_edit.grid(row=0, column=1, sticky="nsew")

window.mainloop()
