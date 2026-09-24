import os
import zipfile
import time
import subprocess
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

MAX_BACKUPS = 50

base_dir = os.path.dirname(os.path.abspath(__file__))
project_name = os.path.basename(base_dir)
backup_dir = os.path.join(base_dir, "backup")


def open_backup_folder():
    os.makedirs(backup_dir, exist_ok=True)
    subprocess.Popen(f'explorer "{backup_dir}"')


def make_unique_zip_name():
    now = datetime.now()
    date_text = now.strftime("%d%m%Y")
    time_text = now.strftime("%H %M")

    base_name = f"backup {project_name} {date_text} {time_text}"
    zip_path = os.path.join(backup_dir, base_name + ".zip")

    count = 2
    while os.path.exists(zip_path):
        zip_path = os.path.join(backup_dir, f"{base_name} ({count}).zip")
        count += 1

    return zip_path


def cleanup_old_backups():
    zips = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.lower().endswith(".zip")
    ]

    zips.sort(key=os.path.getmtime, reverse=True)

    for old_zip in zips[MAX_BACKUPS:]:
        try:
            os.remove(old_zip)
        except:
            pass


def run_backup():
    try:
        os.makedirs(backup_dir, exist_ok=True)

        all_files = []

        for folder, subfolders, files in os.walk(base_dir):
            if os.path.abspath(folder).startswith(os.path.abspath(backup_dir)):
                continue

            for file in files:
                file_path = os.path.join(folder, file)

                # ไม่ backup ตัวโปรแกรมเองก็ได้ ถ้าอยากเอาด้วยให้ลบบรรทัดนี้ออก
                # if os.path.basename(file_path).lower() == "backup.py":
                #     continue

                all_files.append(file_path)

        total_files = len(all_files)

        if total_files == 0:
            messagebox.showwarning("Backup", "ไม่พบไฟล์สำหรับ Backup")
            root.destroy()
            return

        zip_path = make_unique_zip_name()

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for index, file_path in enumerate(all_files, start=1):
                relative_path = os.path.relpath(file_path, base_dir)

                percent = int((index / total_files) * 100)

                root.after(0, update_ui, percent, index, total_files, relative_path)

                zipf.write(file_path, relative_path)

        cleanup_old_backups()

        root.after(0, finish_ui, zip_path)

    except Exception as e:
        root.after(0, error_ui, str(e))


def update_ui(percent, index, total_files, relative_path):
    progress["value"] = percent
    percent_label.config(text=f"{percent}%")
    count_label.config(text=f"{index} / {total_files} files")
    current_file_label.config(text=f"กำลังบีบอัด:\n{relative_path}")


def finish_ui(zip_path):
    title.config(text="Backup สำเร็จ")
    status_label.config(text=f"ไฟล์ถูกเก็บไว้ที่:\nbackup\\{os.path.basename(zip_path)}")
    open_btn.config(state="normal")

    countdown()


def countdown():
    for i in range(5, -1, -1):
        title.config(text=f"Backup สำเร็จ - ปิดใน {i}")
        root.update()
        time.sleep(1)

    root.destroy()


def error_ui(error_text):
    title.config(text="เกิดข้อผิดพลาด")
    status_label.config(text=error_text)
    open_btn.config(state="normal")
    messagebox.showerror("Backup Error", error_text)


root = tk.Tk()
root.title("Backup System")
root.geometry("620x280")
root.resizable(False, False)

title = tk.Label(root, text="กำลังเริ่ม Backup...", font=("Tahoma", 14, "bold"))
title.pack(pady=10)

progress = ttk.Progressbar(root, orient="horizontal", length=540, mode="determinate")
progress.pack(pady=10)

percent_label = tk.Label(root, text="0%", font=("Tahoma", 11))
percent_label.pack()

count_label = tk.Label(root, text="กำลังตรวจไฟล์...", font=("Tahoma", 10))
count_label.pack()

current_file_label = tk.Label(root, text="", wraplength=560, font=("Consolas", 9), justify="left")
current_file_label.pack(pady=10)

status_label = tk.Label(root, text="", font=("Tahoma", 10), wraplength=560)
status_label.pack()

open_btn = tk.Button(root, text="เปิดโฟลเดอร์ Backup", command=open_backup_folder, state="disabled")
open_btn.pack(pady=5)

threading.Thread(target=run_backup, daemon=True).start()

root.mainloop()
