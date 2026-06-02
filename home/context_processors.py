from .constants import INSTAGRAM_URL


def site(request):
    return {"instagram_url": INSTAGRAM_URL}
