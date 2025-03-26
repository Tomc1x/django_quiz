import requests
from django.conf import settings


class PexelsProvider:

    @staticmethod
    def search(query, per_page=15):
        headers = {"Authorization": settings.PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={query}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        return response.json().get('photos', [])


class UnsplashProvider:

    @staticmethod
    def search(query, per_page=15):
        headers = {"Authorization": f"Client-ID {settings.UNSPLASH_API_KEY}"}
        url = f"https://api.unsplash.com/search/photos?query={query}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        return response.json().get('results', [])
