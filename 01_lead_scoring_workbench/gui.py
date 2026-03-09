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
        self.title("見込み顧客スコアリング")
        self.geometry("1200x720")
        self.df = None
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        plt.close("all")
        self.quit()
        self.destroy()

    def _build(self):
        bar = ttk.Frame(self, padding=4)
        bar.pack(fill=tk.X)
        ttk.Button(bar, text="サンプル読込", command=lambda: self._load(main.default_data_path())).pack(side=tk.LEFT, padx=4)
        ttk.Button(bar, text="CSVを開く", command=self._open).pack(side=tk.LEFT, padx=4)
        ttk.Button(bar, text="結果を保存", command=self._save).pack(side=tk.LEFT, padx=4)
        self.status = tk.StringVar(value="データを読み込んでください")
        ttk.Label(bar, textvariable=self.status, foreground="gray").pack(side=tk.LEFT, padx=8)

        self.summary = ttk.Frame(self, padding=6)
        self.summary.pack(fill=tk.X)
        self.summary_labels = {}
        for key in ["総リード数", "Aランク", "Bランク", "Cランク", "平均スコア"]:
            f = ttk.Frame(self.summary)
            f.pack(side=tk.LEFT, padx=12)
            ttk.Label(f, text=key, foreground="gray").pack()
            lbl = ttk.Label(f, text="—", font=("Yu Gothic", 14, "bold"))
            lbl.pack()
            self.summary_labels[key] = lbl

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=3)
        pane.add(right, weight=2)

        cols = ("会社名", "業種", "未接触日数", "合計スコア", "優先度", "推奨アクション")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, w in zip(cols, (190, 90, 90, 90, 70, 170)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.column("会社名", anchor=tk.W)
        self.tree.column("推奨アクション", anchor=tk.W)
        self.tree.tag_configure("A", background="#f8d7da")
        self.tree.tag_configure("B", background="#fff3cd")
        self.tree.tag_configure("C", background="#d4edda")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5.4, 6.2))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._empty()

    def _empty(self):
        self.ax1.clear()
        self.ax2.clear()
        self.ax1.text(0.5, 0.5, "データを読み込んでください", transform=self.ax1.transAxes, ha="center", va="center")
        self.ax1.set_axis_off()
        self.ax2.set_axis_off()
        self.canvas.draw()

    def _open(self):
        path = filedialog.askopenfilename(initialdir=str(main.DATA_DIR), filetypes=[("CSV files", "*.csv")])
        if path:
            self._load(Path(path))

    def _load(self, path: Path):
        try:
            self.df = main.analyze(path)
            for key, value in main.get_summary(self.df).items():
                self.summary_labels[key].configure(text=str(value))
            self.tree.delete(*self.tree.get_children())
            for _, r in self.df.iterrows():
                self.tree.insert("", tk.END, values=(r["会社名"], r["業種"], int(r["未接触日数"]), int(r["合計スコア"]), r["優先度"], r["推奨アクション"]), tags=(r["優先度"],))
            self.ax1.clear()
            counts = self.df.groupby("優先度").size().reindex(["A", "B", "C"], fill_value=0)
            bars = self.ax1.bar(counts.index, counts.values, color=["#d9534f", "#f0ad4e", "#5cb85c"])
            self.ax1.bar_label(bars)
            self.ax1.set_title("優先度別件数")
            self.ax2.clear()
            top = self.df.head(5).iloc[::-1]
            bars = self.ax2.barh(top["会社名"], top["合計スコア"], color="#5b8fd1")
            self.ax2.bar_label(bars, padding=3)
            self.ax2.set_title("上位5件スコア")
            self.fig.tight_layout()
            self.canvas.draw()
            self.status.set(path.name)
        except Exception as exc:
            messagebox.showerror("読み込みエラー", str(exc))

    def _save(self):
        if self.df is None:
            return
        out = main.save_results(self.df)
        messagebox.showinfo("保存完了", str(out))


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
