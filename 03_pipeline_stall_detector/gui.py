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
        self.title("商談停滞検知")
        self.geometry("1200x720")
        self.df = None
        self._sort_col = ""
        self._sort_reverse = False
        self._order_maps = {'停滞判定': {'重度停滞': 0, '停滞': 1, '正常': 2}}
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        plt.close("all")
        self.quit()
        self.destroy()

    def _build(self):
        t = ttk.Frame(self, padding=4)
        t.pack(fill=tk.X)
        ttk.Button(t, text="サンプル読込", command=lambda: self._load(main.default_data_path())).pack(side=tk.LEFT, padx=4)
        ttk.Button(t, text="CSVを開く", command=self._open).pack(side=tk.LEFT, padx=4)
        ttk.Button(t, text="結果を保存", command=self._save).pack(side=tk.LEFT, padx=4)
        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=3)
        pane.add(right, weight=2)
        cols = ("案件名", "フェーズ", "金額", "滞留日数", "基準日数", "停滞判定")
        self._cols = cols
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, w in zip(cols, (200, 100, 110, 90, 90, 100)):
            self.tree.heading(c, text=c, command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.column("案件名", anchor=tk.W)
        self.tree.tag_configure("重度停滞", background="#f8d7da")
        self.tree.tag_configure("停滞", background="#fff3cd")
        self.tree.tag_configure("正常", background="#d4edda")
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
                self.tree.insert("", tk.END, values=(r["案件名"], r["フェーズ"], f"{int(r['金額']):,}", int(r["滞留日数"]), int(r["基準日数"]), r["停滞判定"]), tags=(r["停滞判定"],))
            summary = main.get_phase_summary(self.df)
            self.ax.clear()
            bars = self.ax.barh(summary["フェーズ"], summary["滞留日数"], color="#5b8fd1")
            self.ax.bar_label(bars, fmt="%.1f", padding=3)
            self.ax.set_title("フェーズ別 平均滞留日数")
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
