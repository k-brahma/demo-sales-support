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
        self.title("顧客離反シグナル監視")
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
        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=3)
        pane.add(right, weight=2)
        cols = ("顧客名", "契約金額", "経過日数", "利用頻度増減率", "リスクスコア", "判定")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, w in zip(cols, (180, 100, 90, 110, 90, 80)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.column("顧客名", anchor=tk.W)
        self.tree.tag_configure("高", background="#f8d7da")
        self.tree.tag_configure("中", background="#fff3cd")
        self.tree.tag_configure("低", background="#d4edda")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.fig, self.ax = plt.subplots(figsize=(5.2, 5.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _open(self):
        path = filedialog.askopenfilename(initialdir=str(main.DATA_DIR), filetypes=[("CSV files", "*.csv")])
        if path:
            self._load(Path(path))

    def _load(self, path: Path):
        try:
            self.df = main.analyze(path)
            self.tree.delete(*self.tree.get_children())
            for _, r in self.df.iterrows():
                self.tree.insert("", tk.END, values=(r["顧客名"], f"{int(r['契約金額']):,}", int(r["経過日数"]), f"{r['利用頻度増減率']:.0f}%", f"{r['リスクスコア']:.1f}", r["判定"]), tags=(r["判定"],))
            self.ax.clear()
            top = self.df.head(5).iloc[::-1]
            bars = self.ax.barh(top["顧客名"], top["リスクスコア"], color="#d9534f")
            self.ax.bar_label(bars, fmt="%.1f", padding=3)
            self.ax.set_title("離反リスク 上位5社")
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as exc:
            messagebox.showerror("読み込みエラー", str(exc))

    def _save(self):
        if self.df is not None:
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
