import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import json
import time
import re
from APIClient import APIClient

load_dotenv()

token = os.getenv("TOKEN")
head = {"Authorization": f"Bearer {token}"}
url_star_war = "https://swapi.dev/api/"
url_pokemon = "https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0"


dic_personajes_repositorio = {}
dic_planetas_repositorio = {}
client = APIClient(token)

async def obtener_pokemon_info(nombre_pokemon):
    """ Realiza una petición a la API de Pokémon para obtener detalles. """
    url = f"https://pokeapi.co/api/v2/pokemon/{nombre_pokemon}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "name": data["name"],
                    "base_experience": data["base_experience"],
                    "height": data["height"],
                    "weight": data["weight"]
                }
            else:
                return "Información no disponible"

async def enviar_solucion(datos):
    """ Envía la solución mediante una petición POST. """
    url = "https://recruiting.adere.so/challenge/solution"
    async with aiohttp.ClientSession() as session:
        async with session.post(url,headers=head, json=datos) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": "No se pudo enviar la solución", "status": response.status}




async def request_repository():

    global dic_personajes_repositorio, dic_planetas_repositorio , dic_pokemon_repositorio

    planetas_data, personajes_data= await asyncio.gather(
        client.obtener_planetas_star_war(),
        client.obtener_personajes_star_war(),
    )

    dic_planetas, dic_personajes = await asyncio.gather(
        indexar_repositorio_planeta(planetas_data),
        indexar_repositorio_personaje(personajes_data),
    )
 
    dic_planetas_repositorio = dic_planetas
    dic_personajes_repositorio = dic_personajes

'''
async def verificacion_problema():
    await request_repository()
    start_time = time.time()
    count = 0
    while time.time() - start_time < 180: 
        problema = await client.obtener_problema()
        id = problema['id']
        count += 1
        print(f"Petición {count} - ID problema: {id}")
        respuesta = await extraccion_data_ia(problema)
        
        operacion = respuesta['operacion']
        if isinstance(operacion, list):
            operacion = " ".join(map(str, operacion)) 

        respuesta_buscar = await buscar(respuesta, dic_personajes_repositorio, dic_planetas_repositorio)
        search =  await search_pokemon(respuesta,respuesta_buscar)
        resultado = await evaluar_operacion(search,operacion)
    
        await post_solicitud(id,resultado)

    await asyncio.sleep(6)
'''
async def verificacion_problema():
    await request_repository()
    start_time = time.time()
    count = 0

    while time.time() - start_time < 180:  
        try:
            problema = await client.obtener_problema()
            id = problema['id']
            count += 1
            print(f"Petición {count} - ID problema: {id}")

            respuesta = await extraccion_data_ia(problema)
            operacion = respuesta['operacion']
            if isinstance(operacion, list):
                operacion = " ".join(map(str, operacion)) 

            respuesta_buscar = await buscar(respuesta, dic_personajes_repositorio, dic_planetas_repositorio)
            search = await search_pokemon(respuesta, respuesta_buscar)
            resultado = await evaluar_operacion(search, operacion)

            await post_solicitud(id, resultado)

        except Exception as e:
            print(f" Error en la verificación del problema: {e}")

        await asyncio.sleep(6)  


async def post_solicitud (id,answer):
    data= {
        "problem_id":str(id),
        "answer": float(answer)  
        }
    await enviar_solucion(data)
    respuesta = await enviar_solucion(data)
    print("Respuesta del servidor:", respuesta)    



async def evaluar_operacion(data,operacion):
    try:
        variables = re.findall(r"([\w-]+)\.(\w+)", operacion)
        valores = {}
        for obj, attr in variables:
            
            if obj in data.get("personajes_star_wars", {}) and attr in data["personajes_star_wars"][obj]:
                valores[f"{obj}.{attr}"] = data["personajes_star_wars"][obj][attr]
            elif obj in data.get("planetas_star_wars", {}) and attr in data["planetas_star_wars"][obj]:
               valores[f"{obj}.{attr}"] = data["planetas_star_wars"][obj][attr]

            elif obj in data.get("pokemon", {}) and attr in data["pokemon"][obj]:
                valores[f"{obj}.{attr}"] = data["pokemon"][obj][attr]
        
        for key, value in valores.items():
            value = float(value)
            value = round(value, 10)  

            operacion = operacion.replace(key, f"{value:.10f}")  
             

        resultado = eval(operacion)
        print("esssssssssssssssste es ", resultado)
        return resultado
    
        
    except Exception as e:
        print(f"Error al generar la solución de la evaluacion: {e}")


async def extraccion_data_ia(problema_data):
    
    prompt = await build_prompt(problema_data)    
    resultado_dic = await genera(prompt) 
    
    return resultado_dic



async def indexar_repositorio_planeta (clave):
    return {p["name"].lower().replace(" ", ""): p for p in clave}


async def indexar_repositorio_personaje (clave):
    return {p["name"].lower().replace(" ", ""): p for p in clave}

async def indexar_repositorio_pokemon (clave):
    return {p["name"].lower().replace(" ", ""): p for p in clave}


def convertir_dic(texto):
    if not isinstance(texto, str):
        raise ValueError("El texto proporcionado no es una cadena válida.")

    # Buscar la primera aparición de "{" y la última aparición de "}"
    start_index = texto.find("{")
    end_index = texto.rfind("}")
    
    if start_index == -1 or end_index == -1:
        raise ValueError("No se encontró un objeto JSON válido en el texto.")

    texto_json = texto[start_index:end_index + 1]
    
    try:
        return json.loads(texto_json)
    except json.JSONDecodeError:
        raise ValueError("Error al convertir el texto en un diccionario JSON.")


async def buscar(respuesta_dic, dic_personajes_repositorio, dic_planetas_repositorio):
    categorias = {
        "personajes_star_wars": dic_personajes_repositorio,
        "planetas_star_wars": dic_planetas_repositorio,
    }

    resultado = {}

    for clave, repositorio in categorias.items():
        if clave in respuesta_dic:
            nombres = set(respuesta_dic[clave])  
            resultado[clave] = {
                nombre: repositorio.get(nombre.lower().replace(" ", ""), "Información no disponible")  
                for nombre in nombres
            }

    return resultado 



async def search_pokemon(resultado, data):
    if "pokemon" in resultado and resultado["pokemon"]:
        pokemon_nombres = resultado["pokemon"]
        peticion = [obtener_pokemon_info(nombre) for nombre in pokemon_nombres]
        
        resultados_pokemon = await asyncio.gather(*peticion)

        data["pokemon"] = {
            nombre: info for nombre, info in zip(pokemon_nombres, resultados_pokemon)
        }
    ''' 
       
    
    # Unir con data
    data.update(resultado)
    '''
  

    return data



async def resultado_search(respuesta_dic):
    personajes = await obtener_personajes_star_war()
    indice = await indexar_personajes(personajes)
    search(respuesta_dic,indice)


async def genera(prompt):
    """
    Envía el 'prompt' al endpoint de IA generativa y retorna la respuesta generada.
    """
    url = "https://recruiting.adere.so/chat_completion"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=head, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Error en la petición: {response.status}")

            data = await response.json()
            response_text = data["choices"][0]["message"]["content"]
            return convertir_dic(response_text)
        

async def build_prompt(description):
    
    return f"""
     Tarea: Extraer palabras clave del siguiente texto y clasificarlas en tres categorías:
        - Planetas de Star Wars (Ejemplos: Tatooine, Endor, Coruscant, Hoth, Naboo, etc.).
        - Personajes de Star Wars (Ejemplos: Luke Skywalker, Darth Vader, Yoda, Leia Organa, Han Solo, etc.).
        - Pokémon (Ejemplos: Pikachu, Charizard, Bulbasaur, Mewtwo, etc.).

        Cada objeto identificado debe estructurarse con sus atributos clave.  
        Ejemplo de datos:  
        Planetas de Star Wars:  
    
        "name": "Tatooine",
        "rotation_period": 23,
        "orbital_period": 304,
        "diameter": 10465,
        "surface_water": 1,
        "population": 200000
    
        Personajes de Star Wars:  
        
        "name": "Luke Skywalker",
        "height": 172,
        "mass": 77,
        "homeworld": "Tatooine"
    
        Pokémon  
    
        "name": "Vulpix",
        "base_experience": 60,
        "height": 6,
        "weight": 99
        
        Ejemplo de problema:  

        En una galaxia muy, muy lejana, Luke Skywalker
        se encuentra en el planeta Tatooine, donde ha decidido entrenar 
        a su nuevo compañero Pokémon, Vulpix. Mientras Luke mueve su sable de luz,
        se pregunta cuánta experiencia ganará al entrenar con Vulpix si su masa 
        se multiplica por la experiencia base que este Pokémon puede alcanzar.  

        Este enunciado se puede sacar esta palabras claves
        luke.mass , vulpix.base_experience

        La salida debe estar en formato JSON con tres listas:  
        - "planetas_star_wars" → Contiene los nombres de los planetas encontrados en miniscula y sin espacio . . 
        - "personajes_star_wars" → Contiene los nombres de los personajes encontrados en miniscula y sin espacio.  
        - "pokemon" → Contiene los nombres de los Pokémon encontrados en miniscula y sin espacio.  
        - "operacion" → Contiene la operacion aritmetica que esta solicitando para responder para el ejemplo era lukeskywalker.mass * vulpix.base_experience

        Si no se encuentra ningún elemento en una categoría, la lista debe estar vacía.  

        Ejemplo de respuesta:
        La respuesta debe estar en formato diccionario con la siguiente estructura:
        {{
            "planetas_star_wars": ["tatooine"],
            "personajes_star_wars": ["owenlars", "lukeskywalker"],
            "pokemon": ["infernape"],
            "operacion": ["infernape.height / owenlars.height + lukeskywalker.height"]
        }}

        
        Descripción:
        {description}    

    """



async def main():
    try:

        inicio = time.perf_counter() 
        await verificacion_problema() 
        fin = time.perf_counter() 
        print(f"Tiempo transcurrido: {fin - inicio:.4f} segundos") 

        
    except Exception as e:
        print(f"Error al generar la solución del problema: {e}")

if __name__ == "__main__":
    asyncio.run(main())
