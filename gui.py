import tkinter as tk
from tkinter import ttk
import PIL.Image
import PIL.ImageTk
import PIL.ImageFilter

def create_gui(title:str, font:tuple) -> dict:

    app = tk.Tk()

    fr_title = tk.Frame(app)
    lb_title = tk.Label(fr_title, text=title, font=font)
    lb_title.pack()

    fr_main = tk.Frame(app)

    im = PIL.Image.open("img.png")
    im = im.resize((600, 600))
    im = im.filter(PIL.ImageFilter.GaussianBlur(8))
    photo = PIL.ImageTk.PhotoImage(im, master=app)

    lb_image = tk.Label(fr_main, image=photo)
    lb_image.image = photo
    fr_options = tk.Frame(fr_main)

    tk.Label(fr_options, text="Población").pack()
    vr_poblacion = tk.IntVar(app)
    sc_poblacion = tk.Scale(fr_options, variable=vr_poblacion, orient=tk.HORIZONTAL, from_=100, to=10000,)
    sc_poblacion.pack(side=tk.TOP)

    ttk.Separator(fr_options, orient=tk.HORIZONTAL).pack(side=tk.TOP, fill=tk.X)

    tk.Label(fr_options, text="Edad").pack()
    vr_edad = tk.IntVar(app)
    vr_edad.set(65)
    sc_edad = tk.Scale(fr_options, variable=vr_edad, orient=tk.HORIZONTAL, from_=30, to=80)
    sc_edad.pack(side=tk.TOP)

    ttk.Separator(fr_options, orient=tk.HORIZONTAL).pack(side=tk.TOP, fill=tk.X)

    btn_calcular = tk.Button(fr_options, text="Calcular")
    btn_calcular.pack(side=tk.TOP)

    lb_image.grid(row=0, column=0)
    fr_options.grid(row=0, column=1, sticky=tk.S+tk.N)

    fr_status = tk.Frame(app)
    lb_status = tk.Label(fr_status, text="Status: OK!")
    lb_status.grid(row=0, column=0)
    lb_timer = tk.Label(fr_status, text="0.00s")
    lb_timer.grid(row=0, column=1)

    # Pack Frames
    fr_title.grid(row=0)
    fr_main.grid(row=1)
    fr_status.grid(row=2)

    return {
        "app": app,
        "btn": btn_calcular,
        "img": lb_image,
        "status": lb_status,
        "timer": lb_timer,
        "vars":{
            "poblacion": vr_poblacion,
            "edad": vr_edad
        }
    }

if __name__ == "__main__":
    d = create_gui("Hola", ("Consolas", 20))

    d['app'].mainloop()