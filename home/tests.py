from unittest.mock import patch
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from home.models import EventoSamba, InscricaoPush, PedidoMusica
from home.services.pedido_push import _corpo_pedido, _instancia_vapid, gerar_par_vapid


class PedidoPushTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="mesa",
            password="senha-teste",
            is_staff=True,
        )
        grupo, _ = Group.objects.get_or_create(name="Equipe")
        self.user.groups.add(grupo)
        self.publico = User.objects.create_user(
            username="publico@example.com",
            email="publico@example.com",
            password="senha-teste",
            first_name="Daniel",
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

    def test_pedido_anonimo_e_recusado(self):
        res = self.client.post(
            reverse("home:pedido_musica"),
            {
                "evento_id": self.evento.pk,
                "musica": "O Mesa Chegou",
                "artista": "Mesa Brasileira",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(res.status_code, 403)

    @patch("home.views.notificar_novo_pedido")
    def test_novo_pedido_dispara_aviso_com_musica_e_artista(self, mock_push):
        self.client.force_login(self.publico)
        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(
                reverse("home:pedido_musica"),
                {
                    "evento_id": self.evento.pk,
                    "musica": "O Mesa Chegou",
                    "artista": "Mesa Brasileira",
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



class CadastroUtilizadorTests(TestCase):
    def test_cadastro_cria_utilizador_inactivo_e_envia_email(self):
        res = self.client.post(
            reverse("home:cadastro"),
            {
                "nome": "Maria Samba",
                "email": "maria@example.com",
                "password1": "senha-segura-123",
                "password2": "senha-segura-123",
            },
        )
        self.assertEqual(res.status_code, 302)
        User = get_user_model()
        user = User.objects.get(email="maria@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Confirme", mail.outbox[0].subject)
        from home.models import PerfilUtilizador

        perfil = PerfilUtilizador.objects.get(user=user)
        self.assertFalse(perfil.aceita_emails_promocionais)

    def test_cadastro_guarda_opt_in_promocional(self):
        res = self.client.post(
            reverse("home:cadastro"),
            {
                "nome": "Ana",
                "email": "ana@example.com",
                "password1": "senha-segura-123",
                "password2": "senha-segura-123",
                "aceita_emails_promocionais": "on",
            },
        )
        self.assertEqual(res.status_code, 302)
        from home.models import PerfilUtilizador

        perfil = PerfilUtilizador.objects.get(user__email="ana@example.com")
        self.assertTrue(perfil.aceita_emails_promocionais)

    def test_confirmar_email_activa_conta(self):
        from home.models import CadastroEmailToken

        self.client.post(
            reverse("home:cadastro"),
            {
                "nome": "Joao",
                "email": "joao@example.com",
                "password1": "senha-segura-123",
                "password2": "senha-segura-123",
            },
        )
        token = CadastroEmailToken.objects.get(user__email="joao@example.com")
        res = self.client.get(
            reverse("home:confirmar_cadastro", kwargs={"token": token.token})
        )
        self.assertEqual(res.status_code, 302)
        User = get_user_model()
        user = User.objects.get(email="joao@example.com")
        self.assertTrue(user.is_active)


class PedidoMusicaLimitePorUtilizadorTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.publico = User.objects.create_user(
            username="ouvinte@example.com",
            email="ouvinte@example.com",
            password="senha-teste",
            first_name="Rita",
        )
        self.outro = User.objects.create_user(
            username="outro@example.com",
            email="outro@example.com",
            password="senha-teste",
            first_name="Leo",
        )
        self.evento = EventoSamba.objects.create(
            titulo="Roda limite",
            data=timezone.now(),
            local="Lisboa",
            ativo=True,
            aceita_pedidos=True,
        )

    def _pedir(self, musica):
        return self.client.post(
            reverse("home:pedido_musica"),
            {
                "evento_id": self.evento.pk,
                "musica": musica,
                "artista": "Beth Carvalho",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_segundo_pedido_ativo_e_recusado(self):
        self.client.force_login(self.publico)
        primeiro = self._pedir("Coisinha do Pai")
        self.assertEqual(primeiro.status_code, 200)
        self.assertTrue(primeiro.json()["ok"])

        segundo = self._pedir("Andança")
        self.assertEqual(segundo.status_code, 403)
        data = segundo.json()
        self.assertFalse(data["ok"])
        self.assertTrue(data["ja_tem_pedido_em_fila"])
        self.assertEqual(
            PedidoMusica.objects.filter(
                utilizador=self.publico, tocado=False, rejeitado=False
            ).count(),
            1,
        )

    def test_outro_utilizador_pode_pedir_em_paralelo(self):
        self.client.force_login(self.publico)
        self.assertEqual(self._pedir("Coisinha do Pai").status_code, 200)
        self.client.force_login(self.outro)
        res = self._pedir("Andança")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])

    def test_pode_pedir_de_novo_depois_de_tocado(self):
        self.client.force_login(self.publico)
        self.assertEqual(self._pedir("Coisinha do Pai").status_code, 200)
        pedido = PedidoMusica.objects.get(utilizador=self.publico, tocado=False)
        pedido.marcar_tocado()
        res = self._pedir("Andança")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])
        self.assertEqual(
            PedidoMusica.objects.filter(utilizador=self.publico).count(),
            2,
        )
