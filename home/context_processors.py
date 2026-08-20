from .cart import cart_count
from .constants import INSTAGRAM_URL
from .models import Produto


def site(request):
    return {
        "instagram_url": INSTAGRAM_URL,
        "cart_count": cart_count(request.session),
        "loja_disponivel": Produto.objects.filter(ativo=True).exists(),
    }
