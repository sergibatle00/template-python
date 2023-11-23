from pathlib import Path
import uvicorn
import requests
import json

from fastapi import FastAPI
from fastapi.responses import JSONResponse 
from fastapi import HTTPException, status
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
router = APIRouter()
security = HTTPBasic()
router = APIRouter()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path('./static')
static_dir.mkdir(parents=True, exist_ok=True)  # Si no existe lo crea
app.mount("/static", StaticFiles(directory="static"), name="static")


path_condenados = 'https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/CON239?nult=999'
path_mujer_defunciones = 'https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/ECM349?nult=999'
path_hombre_defunciones = 'https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/ECM350?nult=999'


def ine_request(path):
    response = requests.get(path)
    if response.status_code == 200:
        json_request = response.json()
        return json_request
    else:
        return None


def obtener_datos_con(datos):
    if datos is not None:
        # Extraer la información del JSON
        info = datos['Data']
        # Encontrar el valor máximo y su año para 'Anyo' y 'Valor'
        max_valor = float('-inf')
        anyo_max_valor = None
        for item in info:
            valor_actual = float(item['Valor'])
            if valor_actual > max_valor:
                max_valor = valor_actual
                anyo_max_valor = item['Anyo']


        resultado = {
            "anyo": anyo_max_valor,
            "valor": max_valor
        }
        return json.dumps(resultado, indent=2)
    
    
def get_condenados():    
    datos = ine_request(path_condenados)
    return obtener_datos_con(datos)


def obtener_valor_mas_alto():
    datos_mujer = ine_request(path_mujer_defunciones)
    datos_hombre = ine_request(path_hombre_defunciones)

    max_valor_mujer = max(float(item['Valor']) for item in datos_mujer['Data'])
    max_valor_hombre = max(float(item['Valor']) for item in datos_hombre['Data'])

    anyo_max_valor_mujer = next(item['Anyo'] for item in datos_mujer['Data'] if float(item['Valor']) == max_valor_mujer)
    anyo_max_valor_hombre = next(item['Anyo'] for item in datos_hombre['Data'] if float(item['Valor']) == max_valor_hombre)

    genero_max_valor = "mujeres" if anyo_max_valor_mujer > anyo_max_valor_hombre else "hombres"

    resultado = {
        "anyo": anyo_max_valor_mujer if anyo_max_valor_mujer > anyo_max_valor_hombre else anyo_max_valor_hombre,
        "valor": max_valor_mujer if max_valor_mujer > max_valor_hombre else max_valor_hombre,
        "genero": genero_max_valor
    }

    return json.dumps(resultado, indent=2)


def obtener_diferencia_porcentual(anyo, datos_mujer, datos_hombre):
    valor_mujer = next(float(item['Valor']) for item in datos_mujer if item['Anyo'] == anyo)
    valor_hombre = next(float(item['Valor']) for item in datos_hombre if item['Anyo'] == anyo)

    diferencia_porcentual_mujer = ((valor_mujer - valor_hombre) / valor_hombre) * 100
    diferencia_porcentual_hombre = ((valor_hombre - valor_mujer) / valor_mujer) * 100

    genero_mas = "mujeres" if valor_mujer > valor_hombre else "hombres"
    genero_menos = "hombres" if genero_mas == "mujeres" else "mujeres"
    diferencia_porcentual = abs(diferencia_porcentual_mujer) if genero_mas == "mujeres" else abs(diferencia_porcentual_hombre)

    resultado = {
        "genero_mas": genero_mas,
        "porcentaje": diferencia_porcentual,
        "genero_menos": genero_menos
    }

    return json.dumps(resultado, indent=2)


def obtener_diferencia(anyo):
    datos_mujer = ine_request(path_mujer_defunciones)['Data']
    datos_hombre = ine_request(path_hombre_defunciones)['Data']
    return obtener_diferencia_porcentual(anyo, datos_mujer, datos_hombre)


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/defunciones")
async def redireccionar_def():
    return RedirectResponse("static/defunciones.html", status_code=status.HTTP_302_FOUND)


@app.get("/condenados")
async def redireccionar_con():
     return RedirectResponse(url="static/condenados.html", status_code=status.HTTP_302_FOUND)


@app.get("/defunciones/{anyo}")
async def get_path_parameters(anyo: int): 
    return JSONResponse(content=obtener_diferencia(anyo), status_code=200)


@app.get("/masdefunciones")
async def get_mas_defunciones(): 
    return JSONResponse(content=obtener_valor_mas_alto(), status_code=200)


@app.get("/condenados/result")
async def get_condenados_result(): 
    return JSONResponse(content=get_condenados(), status_code=200)


# if __name__ == "__main__":
#     print("-> Inicio integrado de servicio web")
#     uvicorn.run(app, host="0.0.0.0", port=8000)
# else:
#     print("=> Iniciado desde el servidor web")
#     print("   Módulo python iniciado:", __name__)
