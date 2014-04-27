from Tkconstants import END
import os
import subprocess
import tkFileDialog
import tkMessageBox
import sys

from coilsnake.model.common.blocks import Rom


ROM_FILETYPES = [('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')]


def expand_rom(root, ex=False):
    rom = Rom()
    filename = tkFileDialog.askopenfilename(
        parent=root,
        title="Select a ROM to expand",
        filetypes=ROM_FILETYPES)
    if filename:
        rom.load(filename)
        if (not ex and len(rom) >= 0x400000) or (ex and (len(rom) >= 0x600000)):
            tkMessageBox.showerror(
                parent=root,
                title="Error",
                message="This ROM is already expanded.")
        else:
            if ex:
                rom.expand(0x600000)
            else:
                rom.expand(0x400000)
            rom.save(filename)
            del rom
            tkMessageBox.showinfo(
                parent=root,
                title="Expansion Successful",
                message="Your ROM was expanded.")


def expand_rom_ex(root):
    expand_rom(root=root, ex=True)


def add_header_to_rom(root):
    filename = tkFileDialog.askopenfilename(
        parent=root,
        title="Select a ROM to which to add a header",
        filetypes=ROM_FILETYPES)
    if filename:
        with Rom() as rom:
            rom.from_file(filename)
            rom.add_header()
            rom.to_file(filename)
        tkMessageBox.showinfo(
            parent=root,
            title="Header Addition Successful",
            message="Your ROM was given a header.")


def strip_header_from_rom(root):
    filename = tkFileDialog.askopenfilename(
        parent=root,
        title="Select a ROM from which to remove a header",
        filetypes=ROM_FILETYPES)
    if filename:
        with Rom() as rom:
            rom.from_file(filename)
            rom.to_file(filename)
        tkMessageBox.showinfo(
            parent=root,
            title="Header Removal Successful",
            message="Your ROM's header was removed.")


def set_entry_text(entry, text):
    entry.delete(0, END)
    entry.insert(0, text)
    entry.xview(END)


def browse_for_rom(root, entry, save=False):
    if save:
        filename = tkFileDialog.asksaveasfilename(
            parent=root,
            initialdir=os.path.dirname(entry.get()),
            title="Select an output ROM",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
    else:
        filename = tkFileDialog.askopenfilename(
            parent=root,
            initialdir=os.path.dirname(entry.get()),
            title="Select a ROM",
            filetypes=[('SNES ROMs', '*.smc'), ('SNES ROMs', '*.sfc'), ('All files', '*.*')])
    if filename:
        set_entry_text(entry, filename)
        entry.xview(END)


def browse_for_project(root, entry, save=False):
    filename = tkFileDialog.askdirectory(
        parent=root,
        initialdir=os.path.dirname(entry.get()),
        title="Select a Project Directory",
        mustexist=(not save))
    if filename:
        set_entry_text(entry, filename)
        entry.xview(END)


def open_folder(entry):
    path = entry.get()
    if not path:
        return

    if sys.platform == 'darwin':
        subprocess.check_call(['open', path])
    elif sys.platform == 'linux2':
        subprocess.check_call(['gnome-open', path])
    elif sys.platform == 'win32':
        subprocess.check_call(['explorer', path])