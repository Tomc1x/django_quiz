class CookieConsentMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Si l'utilisateur a refusé les cookies et n'est pas déjà sur la page privacy
        if (request.COOKIES.get('cookie_consent') == 'rejected'
                and not request.path.startswith('/privacy')):
            from django.shortcuts import redirect
            return redirect('privacy')

        return response
