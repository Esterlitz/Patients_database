import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FILE = "patients.json"


# ---------- Модель данных ----------
def calc_bmi(height_cm, weight_kg):
    """ИМТ = масса (кг) / рост (м)^2"""
    return round(weight_kg / (height_cm / 100) ** 2, 1)


def load_data():
    if os.path.exists(FILE):
        try:
            with open(FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning("Файл", "Не удалось прочитать файл данных. Начинаем с пустого списка.")
    return []


def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- Окно добавления/редактирования ----------
class PatientDialog(tk.Toplevel):
    def __init__(self, parent, patient=None):
        super().__init__(parent)
        self.title("Пациент")
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        p = patient or {}
        self.name = tk.StringVar(value=p.get("name", ""))
        self.age = tk.StringVar(value=p.get("age", ""))
        self.sex = tk.StringVar(value=p.get("sex", "Мужской"))
        self.height = tk.StringVar(value=p.get("height", ""))
        self.weight = tk.StringVar(value=p.get("weight", ""))

        rows = [("ФИО", self.name), ("Возраст (лет)", self.age),
                ("Рост (см)", self.height), ("Вес (кг)", self.weight)]
        for i, (label, var) in enumerate(rows):
            ttk.Label(self, text=label).grid(row=i, column=0, padx=8, pady=4, sticky="w")
            ttk.Entry(self, textvariable=var, width=30).grid(row=i, column=1, padx=8, pady=4)

        ttk.Label(self, text="Пол").grid(row=4, column=0, padx=8, pady=4, sticky="w")
        ttk.Combobox(self, textvariable=self.sex, values=["Мужской", "Женский"],
                     state="readonly", width=27).grid(row=4, column=1, padx=8, pady=4)

        btns = ttk.Frame(self)
        btns.grid(row=5, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Сохранить", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(btns, text="Отмена", command=self.destroy).pack(side="left", padx=5)
        self.wait_window()

    def on_ok(self):
        name = self.name.get().strip()
        try:
            age = int(self.age.get())
            height = float(self.height.get().replace(",", "."))
            weight = float(self.weight.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Возраст, рост и вес должны быть числами.", parent=self)
            return
        if not name:
            messagebox.showerror("Ошибка", "Введите ФИО.", parent=self)
            return
        if not (0 <= age <= 120 and 30 <= height <= 250 and 2 <= weight <= 400):
            messagebox.showerror("Ошибка", "Значения вне допустимого диапазона.", parent=self)
            return
        self.result = {"name": name, "age": age, "sex": self.sex.get(),
                       "height": height, "weight": weight}
        self.destroy()


# ---------- Окно статистики ----------
class StatsWindow(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title("Сводная статистика")
        self.geometry("1100x800")

        fig = Figure(figsize=(11, 8), dpi=100)
        ax1, ax2, ax3, ax4 = (fig.add_subplot(2, 2, i) for i in range(1, 5))

        men = [p for p in data if p["sex"] == "Мужской"]
        women = [p for p in data if p["sex"] == "Женский"]

        # 1. Распределение по полу
        ax1.pie([len(men), len(women)], labels=["Мужчины", "Женщины"],
                autopct="%1.0f%%", colors=["#5b9bd5", "#ed7d9a"])
        ax1.set_title("Распределение пациентов по полу")

        # 2. Распределение по возрасту
        ax2.hist([p["age"] for p in data], bins=range(0, 105, 10),
                 color="#70ad47", edgecolor="black")
        ax2.set_title("Распределение пациентов по возрасту")
        ax2.set_xlabel("Возраст, лет")
        ax2.set_ylabel("Число пациентов")

        # 3. Распределение ИМТ с учётом пола
        bins = range(10, 51, 2)
        ax3.hist([[p["bmi"] for p in men], [p["bmi"] for p in women]], bins=bins,
                 label=["Мужчины", "Женщины"], color=["#5b9bd5", "#ed7d9a"])
        ax3.set_title("Распределение ИМТ по полу")
        ax3.set_xlabel("ИМТ, кг/м²")
        ax3.set_ylabel("Число пациентов")
        ax3.legend()

        # 4. Зависимость ИМТ от возраста
        for group, color, label in ((men, "#5b9bd5", "Мужчины"), (women, "#ed7d9a", "Женщины")):
            ax4.scatter([p["age"] for p in group], [p["bmi"] for p in group],
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
    COLUMNS = (("name", "ФИО", 250), ("age", "Возраст", 80), ("sex", "Пол", 100),
               ("height", "Рост, см", 90), ("weight", "Вес, кг", 90), ("bmi", "ИМТ", 80))

    def __init__(self):
        super().__init__()
        self.title("Учёт пациентов")
        self.geometry("750x450")
        self.data = load_data()

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="Добавить", command=self.add).pack(side="left", padx=3)
        ttk.Button(bar, text="Редактировать", command=self.edit).pack(side="left", padx=3)
        ttk.Button(bar, text="Сводная статистика", command=self.stats).pack(side="left", padx=3)

        self.tree = ttk.Treeview(self, columns=[c[0] for c in self.COLUMNS], show="headings")
        for key, title, width in self.COLUMNS:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="center" if key != "name" else "w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<Double-1>", lambda e: self.edit())
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(self.data):
            self.tree.insert("", "end", iid=str(i), values=(
                p["name"], p["age"], p["sex"], p["height"], p["weight"], p["bmi"]))

    def add(self):
        res = PatientDialog(self).result
        if res:
            res["bmi"] = calc_bmi(res["height"], res["weight"])
            self.data.append(res)
            save_data(self.data)
            self.refresh()

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
            save_data(self.data)
            self.refresh()

    def stats(self):
        if not self.data:
            messagebox.showinfo("Статистика", "Нет данных для построения графиков.")
            return
        StatsWindow(self, self.data)


if __name__ == "__main__":
    App().mainloop()