from unittest.mock import patch
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from home.models import EventoSamba, InscricaoPush
from home.services.pedido_push import _corpo_pedido, _instancia_vapid, gerar_par_vapid


class PedidoPushTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="mesa",
            password="senha-teste",
        )
        self.evento = EventoSamba.objects.create(
            titulo="Roda de teste",
            data=timezone.now(),
            local="Lisboa",
            ativo=True,
            aceita_pedidos=True,
        )
        self.payload = {
            "endpoint": "https://push.example/sub/abc",
            "keys": {"p256dh": "chave-p256dh", "auth": "chave-auth"},
        }

    def test_corpo_pedido_inclui_musica_e_artista(self):
        self.assertEqual(
            _corpo_pedido("Chega de saudade", "Tom Jobim"),
            "Chega de saudade — Tom Jobim",
        )
        self.assertEqual(_corpo_pedido("Canto de Ossanha", ""), "Canto de Ossanha")

    def test_par_vapid_compativel_com_pywebpush(self):
        public, private = gerar_par_vapid()
        self.assertGreater(len(public), 80)
        vapid = _instancia_vapid(private)
        self.assertTrue(hasattr(vapid, "sign"))

    def test_inscrever_exige_login(self):
        res = self.client.post(
            reverse("home:push_inscrever"),
            data=json.dumps(self.payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 302)

    def test_equipa_inscreve_e_desinscreve(self):
        self.client.force_login(self.user)
        res = self.client.post(
            reverse("home:push_inscrever"),
            data=json.dumps(self.payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(
            InscricaoPush.objects.filter(
                user=self.user,
                endpoint=self.payload["endpoint"],
            ).exists()
        )

        res = self.client.post(
            reverse("home:push_desinscrever"),
            data=json.dumps(self.payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(
            InscricaoPush.objects.filter(endpoint=self.payload["endpoint"]).exists()
        )

    @patch("home.views.notificar_novo_pedido")
    def test_novo_pedido_dispara_aviso_com_musica_e_artista(self, mock_push):
        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(
                reverse("home:pedido_musica"),
                {
                    "evento_id": self.evento.pk,
                    "musica": "O Mesa Chegou",
                    "artista": "Mesa Brasileira",
                    "pedido_por": "Daniel",
                },
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])
        mock_push.assert_called_once_with(
            musica="O Mesa Chegou",
            artista="Mesa Brasileira",
            pedido_id=res.json()["pedido"]["id"],
        )
