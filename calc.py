import math
import tkinter as tk


class Calculator(tk.Tk):
    ALLOWED = set("0123456789.+-*/")

    def __init__(self):
        super().__init__()
        self.title("Калькулятор")
        self.resizable(False, False)

        self.var = tk.StringVar()
        vcmd = (self.register(self.validate), "%P")
        self.entry = tk.Entry(self, textvariable=self.var, font=("Arial", 18),
                              justify="right", validate="key", validatecommand=vcmd)
        self.entry.grid(row=0, column=0, columnspan=4, sticky="we", padx=5, pady=(5, 0))

        self.result = tk.Label(self, text="", font=("Arial", 14), anchor="e",
                               fg="blue", height=2)
        self.result.grid(row=1, column=0, columnspan=4, sticky="we", padx=5)

        buttons = [
            ("C", 2, 0), ("⌫", 2, 1), ("√", 2, 2), ("/", 2, 3),
            ("7", 3, 0), ("8", 3, 1), ("9", 3, 2), ("*", 3, 3),
            ("4", 4, 0), ("5", 4, 1), ("6", 4, 2), ("-", 4, 3),
            ("1", 5, 0), ("2", 5, 1), ("3", 5, 2), ("+", 5, 3),
            ("0", 6, 0), (".", 6, 1), ("=", 6, 2, 2),
        ]
        for b in buttons:
            text, r, c = b[0], b[1], b[2]
            span = b[3] if len(b) > 3 else 1
            tk.Button(self, text=text, font=("Arial", 14), width=5, height=2,
                      relief="solid", bd=1, bg="#f0f0f0", fg="black",
                      activebackground="#f0f0f0", activeforeground="black",
                      highlightthickness=0, takefocus=0,
                      command=lambda t=text: self.on_button(t)
                      ).grid(row=r, column=c, columnspan=span, sticky="nsew",
                             padx=1, pady=1)

        # Клавиатура
        self.entry.bind("<Return>", lambda e: self.calculate())
        self.entry.bind("<KP_Enter>", lambda e: self.calculate())
        self.entry.bind("<Escape>", lambda e: self.clear())
        self.entry.bind("r", lambda e: self.sqrt() or "break")
        self.entry.bind("R", lambda e: self.sqrt() or "break")
        self.entry.bind("<comma>", self.on_comma)
        self.entry.focus_set()

    # ---------- Валидация ----------
    def validate(self, new_text):
        """Разрешены только цифры, точка и знаки + - * /"""
        return all(ch in self.ALLOWED for ch in new_text) and len(new_text) <= 50

    def on_comma(self, event):
        self.entry.insert(tk.INSERT, ".")
        return "break"

    # ---------- Кнопки ----------
    def on_button(self, t):
        if t == "C":
            self.clear()
        elif t == "⌫":
            self.var.set(self.var.get()[:-1])
        elif t == "=":
            self.calculate()
        elif t == "√":
            self.sqrt()
        else:
            self.entry.insert(tk.END, t)
        self.entry.focus_set()

    def clear(self):
        self.var.set("")
        self.show("")

    def show(self, text, error=False):
        self.result.config(text=text, fg="red" if error else "blue")
    @staticmethod
    def fmt(x):
        if x == int(x) and abs(x) < 1e15:
            return str(int(x))
        return f"{x:.10g}"

    def parse(self, s):
        """Разбор выражения вида: [-]число оператор [-]число (или одно число)."""
        s = s.strip().replace(" ", "")
        if not s:
            raise ValueError("Введите выражение")
        for i in range(1, len(s)):
            if s[i] in "+-*/" and s[i - 1] not in "+-*/":
                a, op, b = s[:i], s[i], s[i + 1:]
                return self.num(a), op, self.num(b)
        return self.num(s), None, None

    @staticmethod
    def num(s):
        if s in ("", "+", "-", "."):
            raise ValueError("Некорректное число")
        if s.count(".") > 1 or s.lstrip("+-").count("+") or s.lstrip("+-").count("-"):
            raise ValueError("Некорректное число")
        try:
            return float(s)
        except ValueError:
            raise ValueError("Некорректное число")

    def calculate(self):
        try:
            a, op, b = self.parse(self.var.get())
            if op is None:
                res = a
            elif op == "+":
                res = a + b
            elif op == "-":
                res = a - b
            elif op == "*":
                res = a * b
            else:
                if b == 0:
                    raise ZeroDivisionError
                res = a / b
            if math.isinf(res) or math.isnan(res):
                raise OverflowError
            self.show(self.fmt(res))
            self.var.set(self.fmt(res))
            self.entry.icursor(tk.END)
        except ZeroDivisionError:
            self.show("Ошибка: деление на 0", True)
        except OverflowError:
            self.show("Ошибка: переполнение", True)
        except ValueError as e:
            self.show(f"Ошибка: {e}", True)

    def sqrt(self):
        try:
            a, op, _ = self.parse(self.var.get())
            if op is not None:
                raise ValueError("Для √ введите одно число")
            if a < 0:
                raise ValueError("корень из отрицательного числа")
            res = math.sqrt(a)
            self.show(self.fmt(res))
            self.var.set(self.fmt(res))
            self.entry.icursor(tk.END)
        except ValueError as e:
            self.show(f"Ошибка: {e}", True)


if __name__ == "__main__":
    Calculator().mainloop()