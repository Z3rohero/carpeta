import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import json

load_dotenv()

token = os.getenv("TOKEN")
head = {"Authorization": f"Bearer {token}"}
url_star_war = "https://swapi.dev/api/"

async def obtener_personajes_star_war():
    async with aiohttp.ClientSession() as session:
        url = url_star_war + "people"
        async with session.get(url, headers=head) as response:
            data = await response.json(content_type=None)
            return data.get("results", [])

async def indexar_personajes(personajes):
    return {p["name"].lower(): p for p in personajes}

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

async def obtener_problema():
    url = "https://recruiting.adere.so/challenge/test"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=head) as response:
            return await response.json(content_type=None)

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
        
            print("Respuesta de la IA:", response_text)
            return convertir_dic(response_text)
        

async def build_prompt(description):
    return f"""
        Tarea: Extrae las palabras clave del siguiente texto que correspondan a estos tres tipos de objetos:
        - Planetas de Star Wars (Ejemplos: Tatooine, Endor, Coruscant, Hoth, Naboo, etc.)
        - Personajes de Star Wars (Ejemplos: Luke Skywalker, Darth Vader, Yoda, Leia Organa, Han Solo, etc.)
        - Pokémon (Ejemplos: Pikachu, Charizard, Bulbasaur, Mewtwo, etc.)

        La respuesta debe estar en formato diccionario con la siguiente estructura:

        Ejemplo de respuesta:
        
        {{
            "planetas_star_wars": ["Bestine IV"],
            "personajes_star_wars": ["Nien Nunb", "Luminara Unduli"],
            "pokemon": "No se mencionan Pokémon en el texto dado."
        }}
        
        Descripción:
        {description}
    """

async def main():
    try:
        problema = await obtener_problema()
        print("Problema recibido:", problema)
        
        personajes = await obtener_personajes_star_war()
        indice = await indexar_personajes(personajes)

        print("Expresión clave:", problema["expression"])
        
        prompt = await build_prompt(problema["problem"])  
        respuesta_dic = await genera(prompt)

        print("Respuesta procesada:", respuesta_dic)
        
        # Búsqueda en el índice de personajes
        if "personajes_star_wars" in respuesta_dic:
            nombres_personajes = respuesta_dic["personajes_star_wars"]
            for nombre in nombres_personajes:
                personaje = indice.get(nombre.lower())
                print(f"Información de {nombre}: {personaje}")

    except Exception as e:
        print(f"Error al generar la solución del problema: {e}")
        
async def main():
    try:
        problema = await obtener_problema()
        print("Problema recibido:", problema)
        
        personajes = await obtener_personajes_star_war()
        indice = await indexar_personajes(personajes)

        print("Expresión clave:", problema["expression"])
        
        prompt = await build_prompt(problema["problem"])  
        respuesta_dic = await genera(prompt)

        print("Respuesta procesada:", respuesta_dic)

        nombres_personajes = respuesta_dic["personajes_star_wars"][0]
        
        print(nombres_personajes)
        
        personaje = indice.get(nombres_personajes.lower())
        print(personaje)
        
       

    except Exception as e:
        print(f"Error al generar la solución del problema: {e}")

if __name__ == "__main__":
    asyncio.run(main())
