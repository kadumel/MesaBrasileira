from django.urls import path

from django.contrib.auth.views import LoginView, LogoutView

from . import views
from . import views_auth
from . import views_loja
from .forms import EquipeLoginForm

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("manifest.webmanifest", views.web_manifest, name="web_manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("eventos/", views.eventos, name="eventos"),
    path("eventos/<int:pk>/", views.evento_detail, name="evento_detail"),
    path("sobre/", views.sobre, name="sobre"),
    path("contato/", views.contato, name="contato"),
    path("videos/", views.videos, name="videos"),
    path("videos/evento/<int:evento_pk>/", views.videos, name="videos_evento"),
    path("loja/", views.loja, name="loja"),
    path("loja/<int:pk>/", views.produto_detail, name="produto_detail"),
    path("loja/carrinho/", views_loja.carrinho, name="carrinho"),
    path(
        "loja/carrinho/adicionar/<int:pk>/",
        views_loja.carrinho_adicionar,
        name="carrinho_adicionar",
    ),
    path(
        "loja/carrinho/atualizar/",
        views_loja.carrinho_atualizar,
        name="carrinho_atualizar",
    ),
    path(
        "loja/carrinho/remover/<str:line_id>/",
        views_loja.carrinho_remover,
        name="carrinho_remover",
    ),
    path("loja/checkout/", views_loja.checkout, name="checkout"),
    path(
        "loja/checkout/aguarda-email/<str:numero>/",
        views_loja.checkout_aguarda_email,
        name="checkout_aguarda_email",
    ),
    path(
        "loja/checkout/confirmar-email/<uuid:token>/",
        views_loja.confirmar_email_pedido,
        name="confirmar_email_pedido",
    ),
    path(
        "loja/checkout/pagamento/<str:numero>/",
        views_loja.checkout_pagamento,
        name="checkout_pagamento",
    ),
    path(
        "loja/pedido/<str:numero>/",
        views_loja.pedido_confirmado,
        name="pedido_confirmado",
    ),
    path("pedir-musica/", views.pedir_musica, name="pedir_musica"),
    path("pedido-musica/", views.pedido_musica, name="pedido_musica"),
    path(
        "pedido-musica/<int:pk>/tocar/",
        views.marcar_pedido_tocado,
        name="marcar_pedido_tocado",
    ),
    path(
        "pedido-musica/<int:pk>/rejeitar/",
        views.marcar_pedido_rejeitado,
        name="marcar_pedido_rejeitado",
    ),
    path("api/fila/<int:evento_id>/", views.fila_pedidos_json, name="fila_pedidos"),
    path("api/push/inscrever/", views.push_inscrever, name="push_inscrever"),
    path("api/push/desinscrever/", views.push_desinscrever, name="push_desinscrever"),
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
    path("accounts/cadastro/", views_auth.cadastro, name="cadastro"),
    path(
        "accounts/cadastro/verifique-email/",
        views_auth.cadastro_verifique_email,
        name="cadastro_verifique_email",
    ),
    path(
        "accounts/confirmar-email/<uuid:token>/",
        views_auth.confirmar_cadastro,
        name="confirmar_cadastro",
    ),
    path(
        "accounts/reenviar-confirmacao/",
        views_auth.reenviar_confirmacao_cadastro,
        name="reenviar_confirmacao_cadastro",
    ),
]
