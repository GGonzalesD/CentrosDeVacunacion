print("Importando")
import pandas as pd
import json, random
from shapely.geometry import Point, Polygon
import geopy.distance

def get_random_point_in_polygon(poly):
    poly = Polygon(poly)
    minx, miny, maxx, maxy = poly.bounds
    while True:
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if poly.contains(p):
            return p.x, p.y
def get_random_points_in_polygon(poly, n, j):
    x = 0
    print(f"Calculando posiciones del distrito #{j+1}")
    for i in range(n):
        x += 1
        xd = int(100 * x / n)
        print(end=f"\r[{'█'*xd}{' '*(100-xd)}] - {xd}%\r")
        yield get_random_point_in_polygon(poly)
    print("\n")


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

def get_geometries(filename):
    with open(filename) as f:
        jmap = json.loads(f.read())
    for j in jmap['features']:
        if j['properties']['id'] in (17, 32, 26, 27, 28):
            coord = j['geometry']['coordinates'][0][0]
            coord.append(coord[0])
            yield coord

file_vacunacion = "TB_CENTRO_VACUNACION.csv"
file_mapa = "lima_distrital.geojson"
n_poblacion = 10000


print(f"Leyendo {file_vacunacion}")
df_vac = pd.read_csv(file_vacunacion)


print("Localizaciones de los centros")
v_locs = []
for a in (1320, 1313, 1323, 1322, 1288):
    v_locs.extend(get_vacunacion_locations(df_vac, a, 6))

print(f"Leyendo {file_mapa}")
n_localizaciones = len(v_locs)
geometries = list(get_geometries(file_mapa))

### CAPACIDAD DE VACUNAS DE LOS CENTROS DE VACUNACION
print("Capacidad de los centros")
firstweek_09_2021 = [497857, 464598, 603584, 492091, 491793, 578100, 486107] # CANTIDAD DE VACUNACIONES POR DIA DE LA PRIMERA SEMANA DE SEPTIEMBRE DEL 2021
avrg_firstweek_09_2021 = int(sum(firstweek_09_2021)/len(firstweek_09_2021))
cnt_centros_de_vacunacion = 32766
num_proporcion = (n_poblacion/10000)*5
n_capacidad_de_centros = [ int( (random.random()*num_proporcion + num_proporcion)*(avrg_firstweek_09_2021/cnt_centros_de_vacunacion) ) for _ in range(n_localizaciones) ]

# POBLACION DEL 2017 DE LOS DISTRITOS USADOS
print("Crear población")
poblacion = [329152, 355219, 398433, 393254, 314241] 
# POBLACION TOTAL DE LOS DISTRITOS USADOS DEL 2017
poblacion_t = sum(poblacion)
poblacion_p = [round(i/poblacion_t, 2) for i in poblacion] 
# Poblacion por distrito
poblacion_d = [int(n_poblacion*i) for i in poblacion_p]


print("Proporción de edades")
## (0-14, 15-63, 64-mas)
P_age2017 = [(56001, 228574, 44577), (75338 , 249631, 30250), (96755 , 272322, 29356), (94770 , 270813, 27671), (67293, 219925, 27023)]
# PORCENTAJEs DE PERSONAS EN CIERTO RANGO DE EDAD POR DISTRITO
P_age2017PORCENT = []
for i in range(len(poblacion)):
    # PROPORCION DE PERSONAS MAYORES DE 64 AÑOS EN NUESTRA CANTIDAD DE PERSONAS POR DISTRITO
    P_age2017PORCENT.append((round(P_age2017[i][0]/poblacion[i], 2), round(P_age2017[i][1]/poblacion[i], 2), round(P_age2017[i][2]/poblacion[i], 2)))

print("Crendo edades")
ages = []
for i, cantD in enumerate(poblacion_d):
    cnt_personas_mayores_64 = int(cantD*P_age2017PORCENT[i][2])
    cnt_personas_15_63 = int(cantD*P_age2017PORCENT[i][1])
    cnt_personas_0_14 = int(cantD*P_age2017PORCENT[i][0])
    suma = cnt_personas_mayores_64 + cnt_personas_15_63 + cnt_personas_0_14
    
    if suma > cantD:
        dif = suma - cantD
        cnt_personas_0_14 = cnt_personas_0_14 - dif
    elif suma < cantD:
        dif = cantD - suma
        cnt_personas_mayores_64 = cnt_personas_mayores_64 + dif

    for _ in range(cnt_personas_mayores_64):
        ages.append(random.randint(64, 95))
    for _ in range(cnt_personas_15_63):
        ages.append(random.randint(15, 63))
    for _ in range(cnt_personas_0_14):
        ages.append(random.randint(0, 14))

print("Correción de errores")
while len(ages) < n_poblacion:
    ages.append( random.randint(0, 95) )



## INFECCION DE LAS PERSONAS
print("Personas infectadas")
infected = [1 if random.randint(0,100) < 30 else 0 for _ in range(n_poblacion)]

## NUMERO DE DOSIS POR PERSONA:
print("Personas Vacunadas")
vacunado = []
for i in range(n_poblacion):
    if ages[i] < 64:
        vacunado.append(0)
    else:
        vacunado.append(1 if random.randint(0,100) < 50 else 0)

print("Calculando posiciones")
p_locs = []
for i, poly in enumerate(geometries):
    p_locs += list(get_random_points_in_polygon(poly, int(n_poblacion*poblacion_p[i]), i))
print("Correción de error de posiciones")
while len(p_locs) < n_poblacion:
    for i, poly in enumerate(geometries):
        p_locs.append(get_random_point_in_polygon(poly))
        if len(p_locs) >= n_poblacion:
            break

print("Calculando distancias")
distances = []
max_distance = []
for i in range(len(v_locs)):
    distances.append(list())
    x = 0
    print(f"Distancias del Centro #{i+1}")
    for k in range(n_poblacion):
        x += 1
        xd = int(100 * x / n_poblacion)
        print(end=f"\r[{'█'*xd}{' '*(100-xd)}] - {xd}%\r")
        distances[i].append( int(geopy.distance.geodesic(p_locs[k], v_locs[i]).m) )
    print("\n")
    max_distance.append(max(distances[i]))
max_distance = max(max_distance)


print("-"*20)
print("Centros:",len(n_capacidad_de_centros))
print("Capacidad:",sum(n_capacidad_de_centros))
print("-"*20)
print("Edades:",len(ages))
print("-"*20)
print("Vacunados:", 100*sum(vacunado)/n_poblacion)
print("-"*20)
print("Localizaciones:", len(p_locs))
print("-"*20)
print("Distances:", len(distances))
print("MaxDistance:", max_distance)

print("-"*20)
print("\nRandomizando")
data = list(zip(p_locs, infected, vacunado, ages, zip(*distances)))
random.shuffle(data)

print("Escribiendo Archivo")
with open("extra_data.json", "w") as file:
    file.write(json.dumps({
        "max_distance": max_distance,
        "n_capacidad_de_centros": n_capacidad_de_centros
    }, indent='\t'))
with open("data.csv", "w") as file:
    x = 0
    file.write('px,py,inf,vac,age,'+",".join(map(lambda x: f"d{x+1}", range(30)))+"\n")
    for p, i, v, a, d in data:
        x += 1
        xd = int(100 * x / n_poblacion)
        print(end=f"\r[{'█'*xd}{' '*(100-xd)}] - {xd}%\r")
        txt = ",".join(map(str, d))
        file.write("%5f,%5f,%d,%d,%d,%s\n"%(p[0], p[1], i, v, a, txt))
print()