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
        self.title("見積粗利チェッカー")
        self.geometry("1180x700")
        self.df = None
        self._sort_col = ""
        self._sort_reverse = False
        self._order_maps = {'承認判定': {'要承認': 0, '注意': 1, 'OK': 2}}
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
        cols = ("案件名", "提示価格", "粗利額", "粗利率", "値引率", "承認判定")
        self._cols = cols
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, w in zip(cols, (180, 100, 100, 90, 80, 90)):
            self.tree.heading(c, text=c, command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.column("案件名", anchor=tk.W)
        self.tree.tag_configure("要承認", background="#f8d7da")
        self.tree.tag_configure("注意", background="#fff3cd")
        self.tree.tag_configure("OK", background="#d4edda")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.fig, self.ax = plt.subplots(figsize=(5.2, 5.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _sort_by(self, col):
        self._sort_reverse = (self._sort_col == col) and not self._sort_reverse
        self._sort_col = col
        self._apply_sort()

    def _coerce_sort_value(self, value, col=None):
        text = str(value).strip()
        order_map = self._order_maps.get(col or self._sort_col, {})
        if text in order_map:
            return order_map[text]
        compact = text.replace(',', '').replace('%', '').replace('¥', '').replace('k', '').strip()
        if compact in {'', '-', '—'}:
            return float('-inf') if not self._sort_reverse else float('inf')
        try:
            return float(compact)
        except ValueError:
            return text

    def _apply_sort(self):
        if not getattr(self, '_sort_col', ''):
            return
        children = list(self.tree.get_children(''))
        children.sort(key=lambda item: self._coerce_sort_value(self.tree.set(item, self._sort_col), self._sort_col), reverse=self._sort_reverse)
        for index, item in enumerate(children):
            self.tree.move(item, '', index)
        indicator = ' ▼' if self._sort_reverse else ' ▲'
        for col in self._cols:
            base = col.rstrip(' ▲▼')
            self.tree.heading(col, text=base + (indicator if col == self._sort_col else ''), command=lambda c=col: self._sort_by(c))

    def _open(self):
        path = filedialog.askopenfilename(initialdir=str(main.DATA_DIR), filetypes=[("CSV files", "*.csv")])
        if path:
            self._load(Path(path))

    def _load(self, path: Path):
        try:
            self.df = main.analyze(path)
            self.tree.delete(*self.tree.get_children())
            for _, r in self.df.iterrows():
                self.tree.insert("", tk.END, values=(r["案件名"], f"{int(r['提示価格']):,}", f"{int(r['粗利額']):,}", f"{r['粗利率']:.1f}%", f"{r['値引率']:.1f}%", r["承認判定"]), tags=(r["承認判定"],))
            self.ax.clear()
            bars = self.ax.bar(self.df["案件名"], self.df["粗利率"], color=["#d9534f" if x == "要承認" else "#f0ad4e" if x == "注意" else "#5cb85c" for x in self.df["承認判定"]])
            self.ax.bar_label(bars, fmt="%.1f%%", fontsize=8)
            self.ax.set_title("案件別 粗利率")
            plt.setp(self.ax.get_xticklabels(), rotation=35, ha="right", fontsize=8)
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
