import requests
from django.conf import settings


class ImgurUploader:

    @staticmethod
    def upload_image(image_file):
        headers = {"Authorization": f"Client-ID {settings.IMGUR_CLIENT_ID}"}

        response = requests.post("https://api.imgur.com/3/image",
                                 headers=headers,
                                 files={'image': image_file})

        if response.status_code == 200:
            return response.json().get('data', {}).get('link')
        return None
