import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import main

matplotlib.rcParams["font.family"] = "Yu Gothic"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("フォロータイミング最適化")
        self.geometry("1180x700")
        self.df = None
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        plt.close("all")
        self.quit()
        self.destroy()

    def _build(self):
        top = ttk.Frame(self, padding=4)
        top.pack(fill=tk.X)
        ttk.Button(top, text="サンプル読込", command=lambda: self._load(main.default_data_path())).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="CSVを開く", command=self._open).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="結果を保存", command=self._save).pack(side=tk.LEFT, padx=4)
        self.info = tk.StringVar(value="データ未読込")
        ttk.Label(top, textvariable=self.info, foreground="gray").pack(side=tk.LEFT, padx=8)

        self.labels = {}
        summary = ttk.Frame(self, padding=6)
        summary.pack(fill=tk.X)
        for key in ["即連絡", "今週中", "様子見"]:
            f = ttk.Frame(summary)
            f.pack(side=tk.LEFT, padx=14)
            ttk.Label(f, text=key, foreground="gray").pack()
            lbl = ttk.Label(f, text="0", font=("Yu Gothic", 14, "bold"))
            lbl.pack()
            self.labels[key] = lbl

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=3)
        pane.add(right, weight=2)

        cols = ("顧客名", "フェーズ", "温度感", "未接触日数", "推奨間隔", "判定")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, w in zip(cols, (180, 110, 80, 90, 90, 90)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.column("顧客名", anchor=tk.W)
        self.tree.tag_configure("即連絡", background="#f8d7da")
        self.tree.tag_configure("今週中", background="#fff3cd")
        self.tree.tag_configure("様子見", background="#d4edda")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(5.2, 5.6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _open(self):
        path = filedialog.askopenfilename(initialdir=str(main.DATA_DIR), filetypes=[("CSV files", "*.csv")])
        if path:
            self._load(Path(path))

    def _load(self, path: Path):
        try:
            self.df = main.analyze(path)
            for k, v in main.get_summary(self.df).items():
                self.labels[k].configure(text=str(v))
            self.tree.delete(*self.tree.get_children())
            for _, r in self.df.iterrows():
                self.tree.insert("", tk.END, values=(r["顧客名"], r["フェーズ"], r["温度感"], int(r["未接触日数"]), int(r["推奨間隔"]), r["判定"]), tags=(r["判定"],))
            self.ax.clear()
            counts = self.df.groupby("判定").size().reindex(["即連絡", "今週中", "様子見"], fill_value=0)
            bars = self.ax.bar(counts.index, counts.values, color=["#d9534f", "#f0ad4e", "#5cb85c"])
            self.ax.bar_label(bars)
            self.ax.set_title("フォロー判定件数")
            self.fig.tight_layout()
            self.canvas.draw()
            self.info.set(path.name)
        except Exception as exc:
            messagebox.showerror("読み込みエラー", str(exc))

    def _save(self):
        if self.df is None:
            return
        messagebox.showinfo("保存完了", str(main.save_results(self.df)))


if __name__ == "__main__":
    app = App()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            plt.close("all")
            app.destroy()
        except tk.TclError:
            pass
