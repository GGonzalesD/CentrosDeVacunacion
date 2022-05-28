from ortools.sat.python import cp_model
from itertools import cycle
from shapely.geometry import Point, Polygon
import pandas as pd
import random, json, time
import threading as thread

import matplotlib.pyplot as plt
import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk

import gui

def get_random_point_in_polygon(poly):
    poly = Polygon(poly)
    minx, miny, maxx, maxy = poly.bounds
    while True:
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if poly.contains(p):
            return p.x, p.y
def get_random_points_in_polygon(poly, n):
    for i in range(n):
        yield get_random_point_in_polygon(poly)

def get_geometries(filename):
    with open(filename) as f:
        jmap = json.loads(f.read())
    for j in jmap['features']:
        if j['properties']['id'] in (17, 32, 26, 27, 28):
            coord = j['geometry']['coordinates'][0][0]
            coord.append(coord[0])
            yield coord

def get_vacunacion_locations(centro_vacunacion, id_, cant):
    locs = []
    cont = 0
    for i in range(len(centro_vacunacion['id_ubigeo'])):
        if centro_vacunacion['id_ubigeo'].get(i) == id_:
            if centro_vacunacion['latitud'].get(i) != 0 and centro_vacunacion['longitud'].get(i) != 0:
                locs.append([centro_vacunacion['longitud'].get(i), centro_vacunacion['latitud'].get(i)])
                cont += 1
        if cont == cant:
            return locs
    return locs

def plot_maps(geometries):
    for g in geometries:
        xs, ys = zip(*g)
        plt.plot(xs, ys, c='k')

def plot_centros(locals):
    plt.scatter(*zip(*locals), s=700, c='black', marker='P', label='Centros de vacunación')

def plot_poblacion(p_locs, ages, vacunado, infected, age):
    p_ge_65 = [ p for i, p in enumerate(p_locs) if ages[i] >= age and not infected[i] and not vacunado[i]]
    p_lt_65 = [ p for i, p in enumerate(p_locs) if ages[i] < age and not infected[i] and not vacunado[i]]
    p_vac = [ p for i, p in enumerate(p_locs) if not infected[i] and vacunado[i]]
    p_if = [ p for i, p in enumerate(p_locs) if infected[i]]
    
    plt.scatter(*zip(*p_ge_65), s=40, c='red', marker='X', label='Mayores')
    plt.scatter(*zip(*p_lt_65), s=30, c='blue', marker='X', label='Adultos')
    plt.scatter(*zip(*p_vac), s=5, c='gray', label='Vacunados')
    plt.scatter(*zip(*p_if), s=5, c='olive', label='Infectados')

def timer_calc(d, obj):
    model = 0
    solver = 0
    t = time.time()
    while obj['step'] == 1:
        model = round(time.time()-t, 1)
        d['timer'].configure(text=f"Model: {model}s | Solver: {solver}s")
        time.sleep(0.1)
    
    t = time.time()
    while obj['step'] == 2:
        solver = round(time.time()-t, 1)
        d['timer'].configure(text=f"Model: {model}s | Solver: {solver}s")
        time.sleep(0.1)

def calculate(g:dict, locals, geometries, df):
    
    obj = {
        "step": 0
    }
    
    g['btn']['state'] = gui.tk.DISABLED
    age = g['vars']['edad'].get()

    im = PIL.Image.open("img.png")
    im = im.filter(PIL.ImageFilter.GaussianBlur(4))
    im = im.resize((600, 600))
    imd = PIL.ImageDraw.Draw(im)
    imd.text((5, 5), "Calculando...", align ="center") 
    photo = PIL.ImageTk.PhotoImage(im, master=g['app'])
    g['img'].configure(image=photo)
    g['img'].image = photo

    g['status'].configure(text="Calculando población")

    n_localizaciones = len(locals)
    n_poblacion = g['vars']['poblacion'].get()

    firstweek_09_2021 = [497857, 464598, 603584, 492091, 491793, 578100, 486107] # CANTIDAD DE VACUNACIONES POR DIA DE LA PRIMERA SEMANA DE SEPTIEMBRE DEL 2021
    avrg_firstweek_09_2021 = int(sum(firstweek_09_2021)/len(firstweek_09_2021))
    cnt_centros_de_vacunacion = 32766
    num_proporcion = (n_poblacion/10000)*5
    n_capacidad_de_centros = [ int( (random.random()*num_proporcion + num_proporcion)*(avrg_firstweek_09_2021/cnt_centros_de_vacunacion) ) for _ in range(n_localizaciones) ]
    
    df = df.head(n_poblacion)

    p_locs = df[['px', 'py']].values
    infected = df[['inf']].values
    vacunado = df[['vac']].values
    ages = df[['age']].values
    distances = df[[f"d{i+1}" for i in range(30)]].transpose().values


    max_distance = max([max(a) for a in distances])

    obj['step'] = 1
    thread.Thread(target=timer_calc, args=(d, obj)).start()


    g['status'].configure(text="Creando Modelo")
    model:cp_model.CpModel = cp_model.CpModel()

    # Variables y dominios
    x = {}
    g['status'].configure(text="Creando Variables")
    for i in range(n_localizaciones):
        for j in range(n_capacidad_de_centros[i]):
            for k in range(n_poblacion):
                x[(i, j, k)] = model.NewBoolVar(f"x_{i}_{j}_{k}")

    g['status'].configure(text="Hard Constraints")
    # Hard Constraints
    # Each vaccine must be applied to at most a person.
    for i in range(n_localizaciones):
        for j in range(n_capacidad_de_centros[i]):
            model.Add( sum([x[(i,j,k)] for k in range(n_poblacion)]) <= 1 )

    # There must be at most a single center assigned to every person.
    # Vaccinated people must not be asigned to any center.
    # People that have been infected should not receive the vaccine, up to 3 months later
    for k in range(n_poblacion):
        n_persona_vacuna_centro = []
        for i in range(n_localizaciones):
            n_persona_vacuna_centro.append( 
                sum(x[(i, j, k)] for j in range(n_capacidad_de_centros[i])))
        model.Add(sum(n_persona_vacuna_centro) <= (not vacunado[k])*(not infected[k]))

    g['status'].configure(text="Soft Constraints")
    # Soft Constraint
    # Atender atodos
    pref = []
    for i in range(n_localizaciones):
        for j in range(n_capacidad_de_centros[i]):
            for k in range(n_poblacion):
                # Every person should be handled by the nearest center.
                # Older people should be assigned first

                pref.append(x[(i,j,k)] * int(max_distance - distances[i][k] + ages[k]*max_distance/20 ))

    g['status'].configure(text="Maximize")
    model.Maximize( sum(pref) )

    obj['step'] = 2
    g['status'].configure(text="Solver")
    solver:cp_model.CpSolver = cp_model.CpSolver()
    status = solver.Solve(model)

    obj['step'] = 3
    if status == cp_model.OPTIMAL:
        g['status'].configure(text="Calculando Lineas")
        plot_lineas = [list() for _ in range(n_localizaciones)]
        for i in range(n_localizaciones):
            for j in range(n_capacidad_de_centros[i]):
                for k in range(n_poblacion):
                    if solver.Value(x[(i,j,k)]):
                        linea_abcisa = [locals[i][0], p_locs[k][0]]
                        linea_ordenada = [locals[i][1], p_locs[k][1]]
                        plot_lineas[i].append( [linea_abcisa, linea_ordenada] )

        fig = plt.figure(figsize=(17, 17))
        plot_maps(geometries)
        plot_centros(locals)
        plot_poblacion(p_locs, ages, vacunado, infected, age)
        colores = cycle('bgrcmyk')
        for i in range(n_localizaciones):
            c = next(colores)
            for x_, y_ in plot_lineas[i]:
                plt.plot(x_, y_, c=c, linewidth=1)
        plt.legend()
        plt.axis("off")
        plt.savefig('img.png')
        
        # Load image
        im = PIL.Image.open("img.png")
        im = im.resize((600, 600))
        photo = PIL.ImageTk.PhotoImage(im, master=g['app'])
        g['img'].configure(image=photo)
        g['img'].image = photo

        g['btn']['state'] = gui.tk.NORMAL
        g['status'].configure(text="OK")
    else:
        g['status'].configure(text="Sin Solucion")


    g['btn']['state'] = gui.tk.NORMAL

if __name__ == "__main__":
    file_vacunacion = "TB_CENTRO_VACUNACION.csv"
    file_mapa = "lima_distrital.geojson"

    
    ## UBICACIONES EN LOS 5 DISTRITOS ESCOGIDOS
    df_vac = pd.read_csv(file_vacunacion)
    locals = []
    for a in (1320, 1313, 1323, 1322, 1288):
        locals.extend(get_vacunacion_locations(df_vac, a, 6))

    geometries = list(get_geometries(file_mapa))
    
    
    df = pd.read_csv("data.csv")

    d = gui.create_gui("Centros de Vacunación", ("Consolas", 20))

    tr = lambda : thread.Thread(target=calculate, args=(d, locals, geometries, df)).start()
    btn:gui.tk.Button = d['btn']
    btn.configure(command=tr)

    d['app'].mainloop()
