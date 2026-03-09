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
        self.title("売上見込みシミュレーター")
        self.geometry("1240x760")
        self.df = None
        self._sort_col = ""
        self._sort_reverse = False
        self._order_maps = {}
        self.monthly = None
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

        self.summary = ttk.Frame(self, padding=6)
        self.summary.pack(fill=tk.X)
        self.summary_labels = {}
        for key in ["対象月数", "案件数", "標準合計", "目標合計"]:
            frame = ttk.Frame(self.summary)
            frame.pack(side=tk.LEFT, padx=14)
            ttk.Label(frame, text=key, foreground="gray").pack()
            label = ttk.Label(frame, text="-", font=("Yu Gothic", 14, "bold"))
            label.pack()
            self.summary_labels[key] = label

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=3)
        pane.add(right, weight=2)

        cols = ("案件名", "受注予定月", "金額", "悲観", "標準", "楽観")
        self._cols = cols
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, w in zip(cols, (190, 90, 105, 105, 105, 105)):
            self.tree.heading(c, text=c, command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.column("案件名", anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6.2, 5.8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._draw_empty()

    def _draw_empty(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, "データを読み込んでください", transform=self.ax.transAxes, ha="center", va="center", color="gray")
        self.ax.set_axis_off()
        self.canvas.draw()

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
            self.df, self.monthly = main.analyze(path)
            self._refresh_summary()
            self._refresh_table()
            self._refresh_chart()
        except Exception as exc:
            messagebox.showerror("読み込みエラー", str(exc))

    def _refresh_summary(self):
        self.summary_labels["対象月数"].configure(text=str(len(self.monthly)))
        self.summary_labels["案件数"].configure(text=str(len(self.df)))
        self.summary_labels["標準合計"].configure(text=f"{int(self.monthly['標準'].sum()):,}")
        self.summary_labels["目標合計"].configure(text=f"{int(self.monthly['目標'].sum()):,}")

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for _, r in self.df.iterrows():
            self.tree.insert(
                "",
                tk.END,
                values=(
                    r["案件名"],
                    r["受注予定月"],
                    f"{int(r['金額']):,}",
                    f"{int(r['悲観']):,}",
                    f"{int(r['標準']):,}",
                    f"{int(r['楽観']):,}",
                ),
            )

    def _refresh_chart(self):
        self.ax.clear()
        x = range(len(self.monthly))
        labels = self.monthly["受注予定月"].tolist()

        bars1 = self.ax.bar(x, self.monthly["悲観"], color="#9bb7d4", label="悲観")
        bars2 = self.ax.bar(x, self.monthly["標準上積み"], bottom=self.monthly["悲観"], color="#4f81bd", label="標準までの上積み")
        self.ax.bar(x, self.monthly["楽観上積み"], bottom=self.monthly["標準"], color="#f0ad4e", label="楽観までの上積み")

        self.ax.plot(x, self.monthly["標準"], color="#1f4e79", marker="o", linewidth=2.2, label="標準見込み")
        self.ax.plot(x, self.monthly["目標"], color="#c0392b", marker="D", linestyle="--", linewidth=2.0, label="月間目標")

        self.ax.bar_label(bars1, labels=[f"{int(v/1000):,}k" if v > 0 else "" for v in self.monthly["悲観"]], padding=2, fontsize=7)
        self.ax.bar_label(bars2, labels=[f"{int(v/1000):,}k" if v > 0 else "" for v in self.monthly["標準上積み"]], padding=2, fontsize=7)

        self.ax.set_xticks(list(x), labels)
        self.ax.set_title("月次着地見込み: 積み上げシナリオと目標")
        self.ax.set_ylabel("金額")
        self.ax.grid(axis="y", alpha=0.25)
        self.ax.legend(fontsize=8, loc="upper left")
        plt.setp(self.ax.get_xticklabels(), rotation=30, ha="right")
        self.fig.tight_layout()
        self.canvas.draw()

    def _save(self):
        if self.df is not None:
            messagebox.showinfo("保存完了", str(main.save_results(self.df, self.monthly)))


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
