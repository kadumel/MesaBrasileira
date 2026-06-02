from django.urls import path

from django.contrib.auth.views import LoginView, LogoutView

from . import views
from .forms import EquipeLoginForm

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("eventos/", views.eventos, name="eventos"),
    path("eventos/<int:pk>/", views.evento_detail, name="evento_detail"),
    path("loja/", views.loja, name="loja"),
    path("loja/<int:pk>/", views.produto_detail, name="produto_detail"),
    path("pedir-musica/", views.pedir_musica, name="pedir_musica"),
    path("pedido-musica/", views.pedido_musica, name="pedido_musica"),
    path(
        "pedido-musica/<int:pk>/tocar/",
        views.marcar_pedido_tocado,
        name="marcar_pedido_tocado",
    ),
    path("api/fila/<int:evento_id>/", views.fila_pedidos_json, name="fila_pedidos"),
    path(
        "accounts/login/",
        LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=EquipeLoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
]
