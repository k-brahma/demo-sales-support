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
        self.title("訪問優先順位ボード")
        self.geometry("1280x760")
        self.df = None
        self._sort_col = ""
        self._sort_reverse = False
        self._order_maps = {'訪問優先度': {'今週必須': 0, '優先': 1, '候補': 2}}
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

        self.summary_labels = {}
        summary = ttk.Frame(self, padding=6)
        summary.pack(fill=tk.X)
        for key in ["今週必須", "優先", "候補", "平均スコア"]:
            frame = ttk.Frame(summary)
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

        cols = ("企業名", "エリア", "案件フェーズ", "優先スコア", "訪問優先度", "主な理由", "推奨アクション")
        self._cols = cols
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, w in zip(cols, (170, 90, 100, 90, 90, 250, 160)):
            self.tree.heading(c, text=c, command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=w, anchor=tk.CENTER)
        self.tree.column("企業名", anchor=tk.W)
        self.tree.column("主な理由", anchor=tk.W)
        self.tree.column("推奨アクション", anchor=tk.W)
        self.tree.tag_configure("今週必須", background="#f8d7da")
        self.tree.tag_configure("優先", background="#fff3cd")
        self.tree.tag_configure("候補", background="#d4edda")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6.0, 5.8))
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
            self.df = main.analyze(path)
            for key, value in main.get_summary(self.df).items():
                self.summary_labels[key].configure(text=str(value))
            self.tree.delete(*self.tree.get_children())
            for _, r in self.df.iterrows():
                self.tree.insert(
                    "",
                    tk.END,
                    values=(r["企業名"], r["エリア"], r["案件フェーズ"], f"{r['優先スコア']:.1f}", r["訪問優先度"], r["主な理由"], r["推奨アクション"]),
                    tags=(r["訪問優先度"],),
                )
            self._refresh_chart()
        except Exception as exc:
            messagebox.showerror("読み込みエラー", str(exc))

    def _refresh_chart(self):
        top = main.get_top_reason_breakdown(self.df)
        names = top["企業名"]
        left = [0] * len(top)
        series = [
            ("未訪問", "未訪問スコア", "#9bb7d4"),
            ("更新接近", "更新接近スコア", "#4f81bd"),
            ("失注兆候", "失注兆候スコア", "#d9534f"),
            ("案件金額", "案件金額スコア", "#f0ad4e"),
            ("役員商談", "役員商談スコア", "#7cb342"),
        ]
        self.ax.clear()
        for label, col, color in series:
            bars = self.ax.barh(names, top[col], left=left, color=color, label=label)
            left = [l + v for l, v in zip(left, top[col])]
            self.ax.bar_label(bars, labels=[f"{v:.0f}" if v >= 8 else "" for v in top[col]], label_type="center", fontsize=7)
        self.ax.set_title("上位訪問先の優先理由内訳")
        self.ax.set_xlabel("優先スコア")
        self.ax.legend(fontsize=8, loc="lower right")
        self.ax.grid(axis="x", alpha=0.2)
        self.fig.tight_layout()
        self.canvas.draw()

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
