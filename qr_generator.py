import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont
import qrcode


class QRGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор QR-кодов")
        self.root.geometry("500x550")

        # Ссылка
        tk.Label(root, text="Ссылка или текст:").pack(pady=5)

        self.data_entry = tk.Entry(root, width=50)
        self.data_entry.pack(pady=5)

        # Размер
        tk.Label(root, text="Размер QR:").pack(pady=5)

        self.size_spin = tk.Spinbox(root, from_=2, to=20, width=10)
        self.size_spin.pack(pady=5)

        self.size_spin.delete(0, "end")
        self.size_spin.insert(0, "10")

        # Подпись
        tk.Label(root, text="Текст под QR:").pack(pady=5)

        self.caption_entry = tk.Entry(root, width=50)
        self.caption_entry.pack(pady=5)

        # Имя файла
        tk.Label(root, text="Имя файла:").pack(pady=5)

        self.filename_entry = tk.Entry(root, width=50)
        self.filename_entry.pack(pady=5)

        # Кнопка
        tk.Button(
            root,
            text="Создать QR-код",
            command=self.generate_single_qr,
            bg="#4CAF50",
            fg="white",
            width=25,
            height=2
        ).pack(pady=15)

        # Пакетная генерация
        tk.Label(root, text="Пакетная генерация из TXT").pack(pady=10)

        tk.Button(
            root,
            text="Выбрать TXT файл",
            command=self.batch_generate,
            bg="#2196F3",
            fg="white",
            width=25,
            height=2
        ).pack(pady=10)

    def create_qr_image(self, data, caption, box_size=10):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=4,
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color="black",
            back_color="white"
        ).convert("RGB")

        if caption.strip():
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), caption, font=font)

            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            new_img = Image.new(
                "RGB",
                (img.width, img.height + text_height + 20),
                "white"
            )

            new_img.paste(img, (0, 0))

            draw = ImageDraw.Draw(new_img)

            text_x = (img.width - text_width) // 2
            text_y = img.height + 10

            draw.text(
                (text_x, text_y),
                caption,
                fill="black",
                font=font
            )

            img = new_img

        return img



    def generate_single_qr(self):
        print("КНОПКА РАБОТАЕТ")

        data = self.data_entry.get().strip()
        caption = self.caption_entry.get().strip()
        filename = self.filename_entry.get().strip()

        if not data:
            messagebox.showerror("Ошибка", "Введите текст")
            return

        try:
            box_size = int(self.size_spin.get())
        except:
            messagebox.showerror("Ошибка", "Неверный размер")
            return

        if not filename:
            filename = "qr_code"

        img = self.create_qr_image(data, caption, box_size)

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"{filename}.png"
        )

        if save_path:
            img.save(save_path)
            messagebox.showinfo("Успех", "QR сохранён")

    def batch_generate(self):
        txt_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")]
        )

        if not txt_path:
            return

        output_folder = filedialog.askdirectory(
            title="Выберите папку"
        )

        if not output_folder:
            return


        with open(txt_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        count = 0

        for index, line in enumerate(lines, start=1):
            data = line.strip()

            if not data:
                continue

            caption = f"QR {index}"

            img = self.create_qr_image(
                data,
                caption,
                box_size
            )

            filename = f"qr_{index}.png"

            save_path = os.path.join(
                output_folder,
                filename
            )

            img.save(save_path)

            count += 1

        messagebox.showinfo(
            "Готово",
            f"Создано QR-кодов: {count}"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = QRGeneratorApp(root)
    root.mainloop()