import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import json
import time
import re


load_dotenv()

token = os.getenv("TOKEN")
head = {"Authorization": f"Bearer {token}"}
url_star_war = "https://swapi.dev/api/"
url_pokemon = "https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0"


dic_personajes_repositorio = {}
dic_planetas_repositorio = {}
dic_pokemon_repositorio = {}


async def obtener_personajes_star_war():
    url = url_star_war + "people/"
    personajes = []

    async with aiohttp.ClientSession() as session:
        while url:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f" Error en la solicitud: {response.status}")
                        return []

                    data = await response.json()
                    personajes.extend(data.get("results", []))
                    url = data.get("next")  

            except aiohttp.ClientError as e:
                print(f" Error de conexión: {e}")
                return []

    return personajes

async def obtener_planetas_star_war():
    url = url_star_war + "planets/"
    planetas = []

    async with aiohttp.ClientSession() as session:
        while url:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f" Error en la solicitud: {response.status}")
                        return []

                    data = await response.json()
                    planetas.extend(data.get("results", []))
                    url = data.get("next")  

            except aiohttp.ClientError as e:
                print(f" Error de conexión: {e}")
                return []

    return planetas
        


async def obtener_pokemon():
    async with aiohttp.ClientSession() as session:
        async with session.get(url_pokemon) as response:
            data = await response.json(content_type=None)
            return data.get("results", [])
        
        
async def obtener_problema():
    url = "https://recruiting.adere.so/challenge/test"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=head) as response:
            data = await response.json(content_type=None)
            print(data)
            return data
        

async def obtener_pokemon_info(url):
    """ Realiza una petición a la API de Pokémon para obtener detalles. """
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


async def request_repository():

    global dic_personajes_repositorio, dic_planetas_repositorio , dic_pokemon_repositorio

    planetas_data, personajes_data, pokemon_data= await asyncio.gather(
        obtener_planetas_star_war(),
        obtener_personajes_star_war(),
        obtener_pokemon()
    )

    dic_planetas, dic_personajes,dic_pokemon = await asyncio.gather(
        indexar_repositorio_planeta(planetas_data),
        indexar_repositorio_personaje(personajes_data),
        indexar_repositorio_pokemon(pokemon_data)
    )
    dic_planetas_repositorio = dic_planetas
    dic_personajes_repositorio = dic_personajes
    dic_pokemon_repositorio = dic_pokemon


 
async def verificacion_problema():
    await request_repository()

    problema = await obtener_problema()

    id = problema['id']
    solucion =problema['solution']

    print(solucion)

    respuesta = await extraccion_data_ia(problema)
    operacion = respuesta['operacion']
    print("esta es la operacion ============>",operacion)
    
    task_buscar = asyncio.create_task(buscar(respuesta, dic_personajes_repositorio, dic_planetas_repositorio, dic_pokemon_repositorio))
    
    search = await task_buscar

    search_poke = await search_pokemon(search) 
    resultado = await evaluar_operacion(search_poke, operacion)

    #print(resultado)



async def evaluar_operacion_async(search_poke, operacion):
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        return await loop.run_in_executor(pool, evaluar_operacion, search_poke, operacion)



async def evaluar_operacion(data,operacion):
    try:
      
        variables = re.findall(r"([\w-]+)\.(\w+)", operacion)

        valores = {}
        for obj, attr in variables:
            # Buscar en personajes
            if obj in data["personajes_star_wars"] and attr in data["personajes_star_wars"][obj]:
                valores[f"{obj}.{attr}"] = data["personajes_star_wars"][obj][attr]
            
            # Buscar en planetas
            elif obj in data["planetas_star_wars"] and attr in data["planetas_star_wars"][obj]:
                valores[f"{obj}.{attr}"] = data["planetas_star_wars"][obj][attr]


            elif obj in data["pokemon"] and attr in data["pokemon"][obj]:
                valores[f"{obj}.{attr}"] = data["pokemon"][obj][attr]
        
        print("esto son los valores   ====",valores)
        print("esto son las variables  ====",variables)
         
     
        # Reemplazar en la operación los valores encontrados
        for key, value in valores.items():
            #if isinstance(value, str) and value.isdigit():  # Convertir strings numéricos
            value = float(value)
            value = round(value, 10)  

            operacion = operacion.replace(key, f"{value:.10f}")  
             #operacion = operacion.replace(key, str(value))


        # Evaluar la operación
        resultado = eval(operacion)
        print("esssssssssssssssste es ", resultado)
        return resultado
    
        
    except Exception as e:
        return f"Error al evaluar la operación: {e}"




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
    print("Tipo de texto recibido:", type(texto))
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


async def buscar(respuesta_dic, dic_personajes_repositorio, dic_planetas_repositorio, dic_pokemon_repositorio):
    categorias = {
        "personajes_star_wars": dic_personajes_repositorio,
        "planetas_star_wars": dic_planetas_repositorio,
        "pokemon": dic_pokemon_repositorio,
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



async def search_pokemon(resultado):
    """ Busca la URL del Pokémon en el diccionario y obtiene su información. """
    if "pokemon" in resultado:
        pokemon_data = resultado["pokemon"]
        tareas = []

        for nombre, datos in pokemon_data.items():
            if isinstance(datos, dict) and "url" in datos:
                tareas.append(obtener_pokemon_info(datos["url"]))
        
        resultados_pokemon = await asyncio.gather(*tareas)

        for (nombre, datos), info in zip(pokemon_data.items(), resultados_pokemon):
            if isinstance(datos, dict) and "url" in datos:
                resultado["pokemon"][nombre] = info

    return resultado




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
            print("esta es la respuesta", response_text)
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
