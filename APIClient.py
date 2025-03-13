import asyncio
import aiohttp

class APIClient:
    def __init__(self, token: str = None):
        self.token = token  

    async def fetch_data(self, url, headers=None):
        """Método genérico para obtener datos de cualquier API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        print(f"Error en la solicitud: {response.status}")
                        return None
                    return await response.json(content_type=None)
            except aiohttp.ClientError as e:
                print(f"Error de conexión: {e}")
                return None

    async def fetch_all_data(self, url):
        """Obtiene datos de una API paginada hasta que no haya más páginas."""
        async with aiohttp.ClientSession() as session:
            data_list = []
            while url:
                try:
                    async with session.get(url) as response:
                        if response.status != 200:
                            print(f"Error en la solicitud: {response.status}")
                            return []
                        data = await response.json()
                        data_list.extend(data.get("results", []))
                        url = data.get("next")  
                except aiohttp.ClientError as e:
                    print(f"Error de conexión: {e}")
                    return []
            return data_list

    async def obtener_pokemon(self):
        """Obtiene una lista de Pokémon."""
        url_pokemon = "https://pokeapi.co/api/v2/pokemon"
        data = await self.fetch_data(url_pokemon)
        return data.get("results", []) if data else []

    async def obtener_problema(self):
        """Obtiene los datos del problema desde la API."""
        url_problema = "https://recruiting.adere.so/challenge/start"
        headers = {"Authorization": f"Bearer {self.token}"}
        data = await self.fetch_data(url_problema, headers)
        return data

    async def obtener_pokemon_info(self, url):
        """Realiza una petición a la API de Pokémon para obtener detalles."""
        data = await self.fetch_data(url)
        if data:
            return {
                "name": data.get("name"),
                "base_experience": data.get("base_experience"),
                "height": data.get("height"),
                "weight": data.get("weight")
            }
        return "Información no disponible"

    async def obtener_personajes_star_war(self):
        """Obtiene todos los personajes de Star Wars."""
        return await self.fetch_all_data("https://swapi.dev/api/people/")
    
    async def obtener_planetas_star_war(self):
        """Obtiene todos los planetas de Star Wars."""
        return await self.fetch_all_data("https://swapi.dev/api/planets/")
