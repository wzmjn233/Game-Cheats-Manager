import os
import sys
import requests
from bs4 import BeautifulSoup
import zipfile
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import threading
import shutil
import sv_ttk
import tempfile
import json
import time


class GameCheatsManager(tk.Tk):

    def __init__(self):
        super().__init__()

        self.SETTINGS_FILE = os.path.join(
            os.environ["APPDATA"], "GCM Settings/", "settings.json")

        setting_path = os.path.join(
            os.environ["APPDATA"], "GCM Settings/")
        if not os.path.exists(setting_path):
            os.makedirs(setting_path)

        self.title("Game Cheats Manager")
        self.iconbitmap(self.resource_path("assets/logo.ico"))
        sv_ttk.set_theme("dark")
        # key = trainer name, value = trainer path
        self.settings = self.load_settings()
        self.trainers = {}
        self.trainer_urls = {}
        self.trainerPath = os.path.normpath(
            os.path.abspath(self.load_settings()["downloadPath"]))
        os.makedirs(self.trainerPath, exist_ok=True)
        self.tempDir = os.path.join(
            tempfile.gettempdir(), "GameCheatsManagerTemp")
        self.trainerSearchEntryPrompt = "Search for installed"
        self.downloadSearchEntryPrompt = "Search to download"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

        self.frame = ttk.Frame(self, padding="30")
        self.frame.grid(row=0, column=0)

        # ================================================================
        # column 1 - trainers
        # ================================================================
        self.flingFrame = ttk.Frame(self.frame)
        self.flingFrame.grid(row=0, column=0)

        self.trainerSearchFrame = ttk.Frame(self.flingFrame)
        self.trainerSearchFrame.grid(row=0, column=0, pady=(0, 20))

        self.searchPhoto = tk.PhotoImage(
            file=self.resource_path("assets/search.png"))
        search_width = 19
        search_height = 19
        search_width_ratio = self.searchPhoto.width() // search_width
        search_height_ratio = self.searchPhoto.height() // search_height
        self.searchPhoto = self.searchPhoto.subsample(
            search_width_ratio, search_height_ratio)
        self.searchLabel = ttk.Label(
            self.trainerSearchFrame, image=self.searchPhoto)
        self.searchLabel.pack(side=tk.LEFT, padx=(0, 10))

        self.trainerSearch_var = tk.StringVar()
        self.trainerSearchEntry = ttk.Entry(
            self.trainerSearchFrame, textvariable=self.trainerSearch_var)
        self.trainerSearchEntry.pack()
        self.trainerSearchEntry.insert(0, self.trainerSearchEntryPrompt)
        self.trainerSearchEntry.config(foreground="grey")
        self.trainerSearch_var.trace('w', self.update_list)

        self.flingScrollbar = ttk.Scrollbar(self.flingFrame)
        self.flingScrollbar.grid(row=1, column=1, sticky='ns')

        self.flingListbox = tk.Listbox(self.flingFrame, highlightthickness=0,
                                       activestyle="none", width=40, height=15, yscrollcommand=self.flingScrollbar.set)
        self.flingListbox.grid(row=1, column=0)
        self.flingScrollbar.config(command=self.flingListbox.yview)

        self.bottomFrame = ttk.Frame(self.flingFrame)
        self.bottomFrame.grid(row=2, column=0, pady=(20, 0))

        self.launchButton = ttk.Button(
            self.bottomFrame, text="Launch", width=11, command=self.launch_trainer)
        self.launchButton.grid(row=0, column=0, padx=(0, 9))

        self.deleteButton = ttk.Button(
            self.bottomFrame, text="Delete", width=11, command=self.delete_trainer)
        self.deleteButton.grid(row=0, column=1, padx=(9, 0))

        # ================================================================
        # column 2 - downloads
        # ================================================================
        self.downloadFrame = ttk.Frame(self.frame)
        self.downloadFrame.grid(row=0, column=1, padx=(30, 0))

        self.downloadSearchFrame = ttk.Frame(self.downloadFrame)
        self.downloadSearchFrame.grid(row=0, column=0, pady=(0, 20))

        self.downloadSearchLabel = ttk.Label(
            self.downloadSearchFrame, image=self.searchPhoto)
        self.downloadSearchLabel.pack(side=tk.LEFT, padx=(0, 10))

        self.downloadSearch_var = tk.StringVar()
        self.downloadSearchEntry = ttk.Entry(
            self.downloadSearchFrame, textvariable=self.downloadSearch_var)
        self.downloadSearchEntry.pack()
        self.downloadSearchEntry.insert(0, self.downloadSearchEntryPrompt)
        self.downloadSearchEntry.config(foreground="grey")

        self.downloadScrollBar = ttk.Scrollbar(self.downloadFrame)
        self.downloadScrollBar.grid(row=1, column=1, sticky='ns')

        self.downloadListBox = tk.Listbox(
            self.downloadFrame, width=40, height=15, yscrollcommand=self.downloadScrollBar.set)
        self.downloadListBox.grid(row=1, column=0)
        self.downloadListBox.config(activestyle="none", highlightthickness=0)
        self.downloadScrollBar.config(command=self.downloadListBox.yview)

        self.changeDownloadPath = ttk.Frame(self.downloadFrame)
        self.changeDownloadPath.grid(row=2, column=0, pady=(20, 0))

        self.downloadPathText = tk.StringVar()
        self.downloadPathText.set(self.trainerPath)
        self.downloadPathEntry = ttk.Entry(
            self.changeDownloadPath, width=21, state="readonly", textvariable=self.downloadPathText)
        self.downloadPathEntry.pack(side=tk.LEFT, padx=(0, 15))

        self.fileDialogButton = ttk.Button(
            self.changeDownloadPath, text="...", width=2, command=self.create_migration_thread)
        self.fileDialogButton.pack(side=tk.LEFT)

        self.trainerSearchEntry.bind('<FocusIn>', self.on_trainer_entry_click)
        self.trainerSearchEntry.bind(
            '<FocusOut>', self.on_trainer_entry_focusout)
        self.flingListbox.bind('<Double-Button-1>', self.launch_trainer)
        self.downloadSearchEntry.bind(
            '<FocusIn>', self.on_download_entry_click)
        self.downloadSearchEntry.bind(
            '<FocusOut>', self.on_download_entry_focusout)
        self.downloadSearchEntry.bind('<Return>', self.on_enter_press)
        self.downloadListBox.bind(
            '<Double-Button-1>', self.on_download_double_click)

        self.show_cheats()
        self.mainloop()

    def on_trainer_entry_click(self, event):
        if self.trainerSearchEntry.get() == self.trainerSearchEntryPrompt:
            self.trainerSearchEntry.delete(0, tk.END)
            self.trainerSearchEntry.insert(0, "")
            self.trainerSearchEntry.config(foreground="white")

    def on_trainer_entry_focusout(self, event):
        if self.trainerSearchEntry.get() == "":
            self.trainerSearchEntry.insert(0, self.trainerSearchEntryPrompt)
            self.trainerSearchEntry.config(foreground="grey")

    def on_download_entry_click(self, event):
        if self.downloadSearchEntry.get() == self.downloadSearchEntryPrompt:
            self.downloadSearchEntry.delete(0, tk.END)
            self.downloadSearchEntry.insert(0, "")
            self.downloadSearchEntry.config(foreground="white")

    def on_download_entry_focusout(self, event):
        if self.downloadSearchEntry.get() == "":
            self.downloadSearchEntry.insert(0, self.downloadSearchEntryPrompt)
            self.downloadSearchEntry.config(foreground="grey")

    def update_list(self, *args):
        search_text = self.trainerSearch_var.get().lower()
        if search_text == self.trainerSearchEntryPrompt.lower() or search_text == "":
            self.show_cheats()
            return

        self.flingListbox.delete(0, tk.END)
        for trainerName in self.trainers.keys():
            if search_text in trainerName.lower():
                self.flingListbox.insert(tk.END, trainerName)

    def change_path(self, event=None):
        self.disable_all_widgets()
        self.downloadListBox.unbind('<Double-Button-1>')
        folder = filedialog.askdirectory(title="Change trainer download path")
        if folder:
            self.downloadPathText.set(os.path.normpath(
                os.path.join(folder, "Trainers/")))
            self.downloadListBox.delete(0, tk.END)
            self.downloadListBox.insert(
                tk.END, "Trainer download directory changed!")
            self.downloadListBox.insert(
                tk.END, "Migrating existing trainers...")

            dst = os.path.join(folder, "Trainers/")
            if not os.path.exists(dst):
                os.makedirs(dst)
            for filename in os.listdir(self.trainerPath):
                src_file = os.path.join(self.trainerPath, filename)
                dst_file = os.path.join(dst, filename)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.move(src_file, dst_file)
            shutil.rmtree(self.trainerPath)
            self.trainerPath = dst
            self.settings["downloadPath"] = self.trainerPath
            self.apply_settings(self.settings)
            self.show_cheats()
            self.downloadListBox.insert(tk.END, "Migration complete!")

        self.enable_all_widgets()

    def on_enter_press(self, event=None):
        keyword = self.downloadSearchEntry.get()
        if keyword:
            self.create_download_thread1(keyword)

    def on_download_double_click(self, event=None):
        selected_index = self.downloadListBox.curselection()[0]
        self.create_download_thread2(selected_index)

    def resource_path(self, relative_path):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def create_download_thread1(self, keyword):
        download_thread1 = threading.Thread(
            target=self.download_display, args=(keyword,))
        download_thread1.start()

    def create_download_thread2(self, index):
        download_thread2 = threading.Thread(
            target=self.download_trainer, args=(index,))
        download_thread2.start()

    def create_migration_thread(self):
        migration_thread = threading.Thread(target=self.change_path)
        migration_thread.start()

    def launch_trainer(self, event=None):
        index = self.flingListbox.curselection()[0]
        trainerName = self.flingListbox.get(index)
        os.startfile(os.path.normpath(self.trainers[trainerName]))

    def delete_trainer(self):
        index = self.flingListbox.curselection()[0]
        trainerName = self.flingListbox.get(index)
        os.remove(self.trainers[trainerName])
        self.flingListbox.delete(index)
        self.show_cheats()

    def disable_download_widgets(self):
        self.downloadSearchEntry.config(state="disabled")
        self.fileDialogButton.config(state="disabled")

    def enable_download_widgets(self):
        self.downloadSearchEntry.config(state="enabled")
        self.fileDialogButton.config(state="enabled")

    def disable_all_widgets(self):
        self.downloadSearchEntry.config(state="disabled")
        self.fileDialogButton.config(state="disabled")
        self.trainerSearchEntry.config(state="disabled")
        self.launchButton.config(state="disabled")
        self.deleteButton.config(state="disabled")

    def enable_all_widgets(self):
        self.downloadSearchEntry.config(state="enabled")
        self.fileDialogButton.config(state="enabled")
        self.trainerSearchEntry.config(state="enabled")
        self.launchButton.config(state="enabled")
        self.deleteButton.config(state="enabled")

    def apply_settings(self, settings):
        with open(self.SETTINGS_FILE, "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open(self.SETTINGS_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # If the settings file doesn't exist, create it with default settings
            default_settings = {
                "downloadPath": "Trainers/"
            }
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(default_settings, f)
            return default_settings

    def show_cheats(self):
        self.flingListbox.delete(0, tk.END)
        self.trainers = {}
        for trainer in sorted(os.scandir(self.trainerPath), key=lambda dirent: dirent.name):
            trainerName = os.path.splitext(os.path.basename(trainer.path))[0]
            if trainer.is_file() and os.path.getsize(trainer) != 0:
                if "Trainer" in trainerName:
                    self.flingListbox.insert(tk.END, trainerName)
                    self.trainers[trainerName] = trainer.path
            else:
                shutil.rmtree(trainer.path)

    def download_display(self, keyword):
        self.disable_download_widgets()
        self.downloadListBox.delete(0, tk.END)
        self.downloadListBox.unbind('<Double-Button-1>')
        self.downloadListBox.insert(tk.END, "Searching...")
        self.trainer_urls = {}

        # Search for results
        url = "https://flingtrainer.com/?s=" + keyword.replace(" ", "+")
        reqs = requests.get(url, headers=self.headers)
        soup1 = BeautifulSoup(reqs.text, 'html.parser')
        count = 0

        # Check if the request was successful
        if reqs.status_code == 200:
            self.downloadListBox.insert(tk.END, "Request successful!")
        else:
            self.downloadListBox.insert(tk.END, "Request failed with status code: " + str(reqs.status_code))

        # Generate and store search results
        for link in soup1.find_all(rel="bookmark"):
            trainerName = link.get_text()
            if "My Trainers Archive" in trainerName:
                continue
            if count == 0:
                self.enable_download_widgets()
                self.downloadListBox.bind(
                    '<Double-Button-1>', self.on_download_double_click)
                self.downloadListBox.delete(0, tk.END)

            self.trainer_urls[trainerName] = link.get("href")
            self.downloadListBox.insert(tk.END, f"{str(count)}. {trainerName}")
            count += 1
        if len(self.trainer_urls) == 0:
            self.downloadListBox.unbind('<Double-Button-1>')
            self.downloadListBox.insert(tk.END, "No results found.")
            self.enable_download_widgets()
            return

    def download_trainer(self, index):
        self.disable_download_widgets()
        self.downloadListBox.unbind('<Double-Button-1>')
        self.downloadListBox.delete(0, tk.END)
        self.downloadListBox.insert(tk.END, "Downloading...")
        if os.path.exists(self.tempDir):
            shutil.rmtree(self.tempDir)

        # Extract final file link
        trainer_list = list(self.trainer_urls.items())
        filename = trainer_list[index][0]
        mFilename = filename.replace(':', ' -')
        if "/" in mFilename:
            mFilename = mFilename.split("/")[1]
        zFilename = mFilename + ".zip"
        for trainerPath in self.trainers.keys():
            if mFilename in trainerPath:
                self.downloadListBox.delete(0, tk.END)
                self.downloadListBox.insert(
                    tk.END, "Trainer already exists, aborted download.")
                self.enable_download_widgets()
                return
        gamereqs = requests.get(self.trainer_urls[filename], headers=self.headers)
        soup2 = BeautifulSoup(gamereqs.text, 'html.parser')
        targeturl = soup2.find(target="_self").get("href")

        # Download file
        try:
            finalreqs = requests.get(targeturl, headers=self.headers)
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred while getting trainer url: {e}")
            self.enable_download_widgets()
            return
        trainerTemp = os.path.join(self.tempDir, zFilename)
        if not os.path.exists(self.tempDir):
            os.mkdir(self.tempDir)
        with open(trainerTemp, "wb") as f:
            f.write(finalreqs.content)
        time.sleep(2)

        # Extract .zip file and rename
        try:
            with zipfile.ZipFile(trainerTemp, 'r') as zip_ref:
                zip_ref.extractall(self.tempDir)

                # Rename extracted file
                cnt = 0
                for t in zip_ref.namelist():
                    cnt += 1
                    if "Trainer" in t:
                        gameRawName = t
                if cnt > 1:
                    messagebox.showinfo(
                        "Attention", "Additional actions required\nPlease check folder for details!")
                    os.startfile(self.tempDir)
        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred while extracting downloaded trainer: {e}")
            self.enable_download_widgets()
            return

        os.makedirs(self.trainerPath, exist_ok=True)
        trainer_name = mFilename + ".exe"
        source_file = os.path.join(self.tempDir, gameRawName)
        destination_file = os.path.join(self.trainerPath, trainer_name)
        shutil.move(source_file, destination_file)
        os.remove(trainerTemp)

        self.downloadListBox.insert(tk.END, "Download success!")
        self.enable_download_widgets()
        self.show_cheats()


if __name__ == "__main__":
    GameCheatsManager()