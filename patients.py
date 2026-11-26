import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FILE = "patients.json"
SEXES = ("Мужской", "Женский", "Не определён")
DEFAULT_SEX = "Не определён"
LATIN = re.compile(r"[A-Za-z]")

# (значение в данных, подпись на графиках, цвет)
SEX_STYLE = [("Мужской", "Мужчины", "#5b9bd5"),
             ("Женский", "Женщины", "#ed7d9a"),
             ("Не определён", "Не определён", "#a5a5a5")]


# ---------- Данные ----------
def calc_bmi(height_cm, weight_kg):
    """ИМТ = масса (кг) / рост (м)^2"""
    return round(weight_kg / (height_cm / 100) ** 2, 1)


def valid_patient(p):
    try:
        return (isinstance(p["name"], str) and p["name"].strip() != ""
                and not LATIN.search(p["name"])
                and 0 <= int(p["age"]) <= 120
                and p["sex"] in SEXES
                and 30 <= float(p["height"]) <= 250
                and 2 <= float(p["weight"]) <= 400)
    except (KeyError, TypeError, ValueError):
        return False


def load_data():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        messagebox.showwarning("Файл", "Не удалось прочитать файл данных. Список будет пустым.")
        return []
    if not isinstance(raw, list):
        return []
    data = []
    for p in raw:
        if valid_patient(p):
            p = dict(p)
            p["age"] = int(p["age"])
            p["height"] = float(p["height"])
            p["weight"] = float(p["weight"])
            p["bmi"] = calc_bmi(p["height"], p["weight"])
            data.append(p)
    return data


def save_data(data):
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE)


def fmt(x):
    return int(x) if float(x).is_integer() else x


# ---------- Диалог добавления/редактирования ----------
class PatientDialog(tk.Toplevel):
    def __init__(self, parent, patient=None):
        super().__init__(parent)
        self.title("Пациент")
        self.resizable(False, False)
        self.result = None
        self.transient(parent)

        p = patient or {}
        self.name = tk.StringVar(value=p.get("name", ""))
        self.age = tk.StringVar(value=p.get("age", ""))
        self.sex = tk.StringVar(value=p.get("sex", DEFAULT_SEX))
        self.height = tk.StringVar(value=fmt(p["height"]) if "height" in p else "")
        self.weight = tk.StringVar(value=fmt(p["weight"]) if "weight" in p else "")

        rows = [("ФИО", self.name), ("Возраст (лет)", self.age),
                ("Рост (см)", self.height), ("Вес (кг)", self.weight)]
        for i, (label, var) in enumerate(rows):
            ttk.Label(self, text=label).grid(row=i, column=0, padx=8, pady=4, sticky="w")
            ttk.Entry(self, textvariable=var, width=30).grid(row=i, column=1, padx=8, pady=4)

        ttk.Label(self, text="Пол").grid(row=4, column=0, padx=8, pady=4, sticky="w")
        ttk.Combobox(self, textvariable=self.sex, values=SEXES,
                     state="readonly", width=27).grid(row=4, column=1, padx=8, pady=4)

        btns = ttk.Frame(self)
        btns.grid(row=5, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Сохранить", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side="left", padx=5)

        self.wait_visibility()
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите ФИО.", parent=self)
            return
        if LATIN.search(name):
            messagebox.showerror("Ошибка",
                                 "ФИО не должно содержать латинские буквы. Используйте кириллицу.",
                                 parent=self)
            return
        try:
            age = int(self.age.get())
            height = float(self.height.get().replace(",", "."))
            weight = float(self.weight.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Возраст, рост и вес должны быть числами.", parent=self)
            return
        if not (0 <= age <= 120 and 30 <= height <= 250 and 2 <= weight <= 400):
            messagebox.showerror("Ошибка",
                                 "Допустимо: возраст 0-120, рост 30-250 см, вес 2-400 кг.",
                                 parent=self)
            return
        self.result = {"name": name, "age": age, "sex": self.sex.get(),
                       "height": height, "weight": weight}
        self.destroy()


# ---------- Сводная статистика ----------
class StatsWindow(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title("Сводная статистика")
        self.geometry("1100x800")

        fig = Figure(figsize=(11, 8), dpi=100)
        ax1, ax2, ax3, ax4 = (fig.add_subplot(2, 2, i) for i in range(1, 5))

        groups = [(label, color, [p for p in data if p["sex"] == key])
                  for key, label, color in SEX_STYLE]
        groups = [g for g in groups if g[2]]

        # 1. Распределение по полу
        ax1.pie([len(g[2]) for g in groups], labels=[g[0] for g in groups],
                colors=[g[1] for g in groups], autopct=lambda v: f"{v:.0f}%")
        ax1.set_title("Распределение пациентов по полу")

        # 2. Распределение по возрасту
        ages = [p["age"] for p in data]
        top = (max(ages) // 10 + 1) * 10
        ax2.hist(ages, bins=list(range(0, top + 10, 10)), color="#70ad47", edgecolor="black")
        ax2.set_title("Распределение пациентов по возрасту")
        ax2.set_xlabel("Возраст, лет")
        ax2.set_ylabel("Число пациентов")

        # 3. Распределение ИМТ с учётом пола
        all_bmi = [p["bmi"] for p in data]
        lo = int(min(all_bmi) // 2 * 2)
        hi = int(max(all_bmi) // 2 * 2) + 4
        ax3.hist([[p["bmi"] for p in g[2]] for g in groups],
                 bins=list(range(lo, hi + 1, 2)),
                 color=[g[1] for g in groups], label=[g[0] for g in groups],
                 edgecolor="black")
        ax3.set_title("Распределение ИМТ по полу")
        ax3.set_xlabel("ИМТ, кг/м²")
        ax3.set_ylabel("Число пациентов")
        ax3.legend()

        # 4. Зависимость ИМТ от возраста
        for label, color, grp in groups:
            ax4.scatter([p["age"] for p in grp], [p["bmi"] for p in grp],
                        c=color, label=label, edgecolor="black")
        ax4.set_title("Зависимость ИМТ от возраста")
        ax4.set_xlabel("Возраст, лет")
        ax4.set_ylabel("ИМТ, кг/м²")
        ax4.legend()

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


# ---------- Главное окно ----------
class App(tk.Tk):
    COLUMNS = (("name", "ФИО", 250), ("age", "Возраст", 80), ("sex", "Пол", 110),
               ("height", "Рост, см", 90), ("weight", "Вес, кг", 90), ("bmi", "ИМТ", 80))

    def __init__(self):
        super().__init__()
        self.title("Учёт пациентов")
        self.geometry("780x450")
        self.data = load_data()

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="Добавить", command=self.add).pack(side="left", padx=3)
        ttk.Button(bar, text="Редактировать", command=self.edit).pack(side="left", padx=3)
        ttk.Button(bar, text="Сводная статистика", command=self.stats).pack(side="left", padx=3)

        self.tree = ttk.Treeview(self, columns=[c[0] for c in self.COLUMNS], show="headings")
        for key, title, width in self.COLUMNS:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w" if key == "name" else "center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<Double-1>", lambda e: self.edit())
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(self.data):
            self.tree.insert("", "end", iid=str(i), values=(
                p["name"], p["age"], p["sex"], fmt(p["height"]), fmt(p["weight"]), p["bmi"]))

    def add(self):
        res = PatientDialog(self).result
        if res:
            res["bmi"] = calc_bmi(res["height"], res["weight"])
            self.data.append(res)
            self.commit()

    def edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Редактирование", "Выберите пациента в таблице.")
            return
        idx = int(sel[0])
        res = PatientDialog(self, self.data[idx]).result
        if res:
            res["bmi"] = calc_bmi(res["height"], res["weight"])
            self.data[idx] = res
            self.commit()

    def commit(self):
        try:
            save_data(self.data)
        except OSError as e:
            messagebox.showerror("Ошибка записи", str(e))
        self.refresh()

    def stats(self):
        if not self.data:
            messagebox.showinfo("Статистика", "Нет данных для построения графиков.")
            return
        StatsWindow(self, self.data)


if __name__ == "__main__":
    App().mainloop()