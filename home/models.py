import secrets
import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

# URLs do Instagram/CDN costumam exceder 200 caracteres (limite padrão do URLField).
URL_MAX_LENGTH = 1000


class EventoDestaque(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    imagem = models.ImageField(upload_to="eventos/", blank=True, null=True)
    imagem_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        help_text="URL externa da imagem (ex.: Instagram) se não enviar ficheiro.",
    )
    data_evento = models.DateField(null=True, blank=True)
    local = models.CharField(max_length=200, blank=True)
    link = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
    )
    instagram_videos_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        verbose_name="Instagram (vídeos do evento)",
        help_text=(
            "Caminho/link do Instagram onde estão os vídeos deste evento "
            "(ex.: destaque, álbum ou publicação)."
        ),
    )
    ordem = models.PositiveIntegerField(default=0)
    destaque = models.BooleanField(
        default=True,
        help_text="Se marcado, aparece na página inicial. Todos os ativos aparecem em Eventos.",
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "-data_evento"]
        verbose_name = "Evento em destaque"
        verbose_name_plural = "Eventos em destaque"

    def __str__(self):
        return self.titulo

    @property
    def imagem_exibir(self):
        if self.imagem:
            return self.imagem.url
        return self.imagem_url or ""

    @property
    def instagram_videos_exibir(self):
        return (self.instagram_videos_url or "").strip()


class SlideHome(models.Model):
    """Slides do carrossel principal (eventos ou propagandas)."""

    TIPO_EVENTO = "evento"
    TIPO_PROPAGANDA = "propaganda"
    TIPOS = [
        (TIPO_EVENTO, "Evento"),
        (TIPO_PROPAGANDA, "Propaganda"),
    ]

    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300, blank=True)
    imagem = models.ImageField(upload_to="slides/", blank=True, null=True)
    imagem_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        help_text="Imagem do slide (recomendado 1920×600 px).",
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TIPO_EVENTO)
    evento = models.ForeignKey(
        "EventoDestaque",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="slides",
        help_text="Se escolher um evento, o clique abre a página desse evento.",
    )
    link = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        help_text="Link para propaganda ou página externa (se não houver evento).",
    )
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "-criado_em"]
        verbose_name = "Slide do carrossel"
        verbose_name_plural = "Slides do carrossel (home)"

    def __str__(self):
        return self.titulo

    @property
    def imagem_exibir(self):
        if self.imagem:
            return self.imagem.url
        return self.imagem_url or ""

    @property
    def url_destino(self):
        if self.evento_id:
            return reverse("home:evento_detail", kwargs={"pk": self.evento_id})
        return self.link or ""

    @property
    def tem_link(self):
        return bool(self.url_destino and self.url_destino != "#")


class Patrocinador(models.Model):
    nome = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="patrocinadores/", blank=True, null=True)
    logo_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        help_text=(
            "URL da logo (ex.: link do Instagram). Ao guardar, a imagem é copiada "
            "para o servidor — links do Instagram não funcionam direto no site."
        ),
    )
    site = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        help_text="Site ou rede social do parceiro.",
    )
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "Parceiro"
        verbose_name_plural = "Parceiros"

    def __str__(self):
        return self.nome

    @property
    def logo_exibir(self):
        if self.logo:
            return self.logo.url
        return self.logo_url or ""

    def _logo_url_mudou(self) -> bool:
        if not self.pk:
            return bool(self.logo_url)
        anterior = (
            Patrocinador.objects.filter(pk=self.pk)
            .values_list("logo_url", flat=True)
            .first()
        )
        return anterior != self.logo_url

    def precisa_baixar_logo(self) -> bool:
        if not (self.logo_url or "").strip():
            return False
        if self._logo_url_mudou():
            return True
        return not self.logo

    def baixar_logo_da_url(self) -> bool:
        from home.utils.link_preview import baixar_para_imagefield

        url = (self.logo_url or "").strip()
        if not url:
            return False
        return baixar_para_imagefield(self, "logo", url)

    def save(self, *args, **kwargs):
        if self.precisa_baixar_logo():
            self.baixar_logo_da_url()
        super().save(*args, **kwargs)


class Produto(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem = models.ImageField(upload_to="produtos/", blank=True, null=True)
    imagem_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
    )
    link_compra = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        help_text="Link externo opcional (a loja usa carrinho e checkout no site).",
    )
    requer_tamanho = models.BooleanField(
        default=False,
        verbose_name="Exige escolha de tamanho",
        help_text=(
            "Marque para artigos como camisolas. O cliente deve escolher um tamanho "
            "ao adicionar ao carrinho (configure os tamanhos disponíveis abaixo)."
        ),
    )
    destaque = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.nome

    @property
    def imagem_exibir(self):
        if self.imagem:
            return self.imagem.url
        return self.imagem_url or ""

    def tamanhos_ativos(self):
        return self.tamanhos.filter(ativo=True).order_by("ordem", "codigo")

    def tamanho_valido(self, codigo: str) -> bool:
        if not self.requer_tamanho:
            return not codigo
        codigo = (codigo or "").strip().upper()
        if not codigo:
            return False
        ativos = self.tamanhos_ativos()
        if ativos.exists():
            return ativos.filter(codigo=codigo).exists()
        return codigo in dict(TamanhoProduto.TAMANHOS)


class TamanhoProduto(models.Model):
    TAMANHO_S = "S"
    TAMANHO_M = "M"
    TAMANHO_L = "L"
    TAMANHO_XL = "XL"
    TAMANHO_XXL = "XXL"
    TAMANHOS = [
        (TAMANHO_S, "S"),
        (TAMANHO_M, "M"),
        (TAMANHO_L, "L"),
        (TAMANHO_XL, "XL"),
        (TAMANHO_XXL, "XXL"),
    ]
    ORDEM_TAMANHO = {
        TAMANHO_S: 1,
        TAMANHO_M: 2,
        TAMANHO_L: 3,
        TAMANHO_XL: 4,
        TAMANHO_XXL: 5,
    }

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="tamanhos",
    )
    codigo = models.CharField(max_length=5, choices=TAMANHOS)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "codigo"]
        verbose_name = "Tamanho do produto"
        verbose_name_plural = "Tamanhos do produto"
        constraints = [
            models.UniqueConstraint(
                fields=["produto", "codigo"],
                name="uniq_produto_tamanho",
            ),
        ]

    def __str__(self):
        return f"{self.produto.nome} — {self.codigo}"

    def save(self, *args, **kwargs):
        if not self.ordem:
            self.ordem = self.ORDEM_TAMANHO.get(self.codigo, 0)
        super().save(*args, **kwargs)


class Pedido(models.Model):
    STATUS_AGUARDA_EMAIL = "aguarda_email"
    STATUS_AGUARDA_PAGAMENTO = "aguarda_pagamento"
    STATUS_PAGO = "pago"
    STATUS_CANCELADO = "cancelado"
    STATUS_EXPIRADO = "expirado"
    STATUS = [
        (STATUS_AGUARDA_EMAIL, "Aguarda confirmação de email"),
        (STATUS_AGUARDA_PAGAMENTO, "Aguarda pagamento"),
        (STATUS_PAGO, "Pago — a preparar entrega"),
        (STATUS_CANCELADO, "Cancelado"),
        (STATUS_EXPIRADO, "Expirado"),
    ]

    METODO_MBWAY = "mbway"
    METODO_TRANSFERENCIA = "transferencia"
    METODOS_PAGAMENTO = [
        (METODO_MBWAY, "MB Way"),
        (METODO_TRANSFERENCIA, "Transferência bancária"),
    ]

    numero = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default=STATUS_AGUARDA_EMAIL,
    )
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    telefone = models.CharField(max_length=30)
    morada = models.CharField(max_length=300)
    codigo_postal = models.CharField(max_length=20)
    cidade = models.CharField(max_length=120)
    pais = models.CharField(max_length=80, default="Portugal")
    notas_entrega = models.CharField(max_length=500, blank=True)
    email_confirmado = models.BooleanField(default=False)
    token_confirmacao = models.UUIDField(default=uuid.uuid4, editable=False)
    token_expira_em = models.DateTimeField()
    metodo_pagamento = models.CharField(
        max_length=20,
        choices=METODOS_PAGAMENTO,
        blank=True,
    )
    referencia_pagamento = models.CharField(
        max_length=120,
        blank=True,
        help_text="Telefone MB Way ou referência indicada pelo cliente.",
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    email_confirmado_em = models.DateTimeField(null=True, blank=True)
    pago_em = models.DateTimeField(null=True, blank=True)
    email_pagamento_confirmado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Email «pagamento recebido» enviado em",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Pedido da loja"
        verbose_name_plural = "Pedidos da loja"

    def __str__(self):
        return f"{self.numero} — {self.nome}"

    @classmethod
    def gerar_numero(cls) -> str:
        prefixo = timezone.now().strftime("%Y%m%d")
        for _ in range(20):
            sufixo = secrets.token_hex(3).upper()
            numero = f"MB-{prefixo}-{sufixo}"
            if not cls.objects.filter(numero=numero).exists():
                return numero
        return f"MB-{prefixo}-{uuid.uuid4().hex[:6].upper()}"

    def definir_expiracao_token(self, horas: int | None = None):
        horas = horas or getattr(settings, "LOJA_TOKEN_EMAIL_HORAS", 48)
        self.token_expira_em = timezone.now() + timedelta(hours=horas)

    def token_valido(self) -> bool:
        return timezone.now() < self.token_expira_em

    def confirmar_email(self):
        self.email_confirmado = True
        self.email_confirmado_em = timezone.now()
        self.status = self.STATUS_AGUARDA_PAGAMENTO
        self.save(
            update_fields=[
                "email_confirmado",
                "email_confirmado_em",
                "status",
                "atualizado_em",
            ]
        )

    def url_confirmacao_email(self) -> str:
        base = getattr(settings, "SITE_URL", "").rstrip("/")
        path = reverse(
            "home:confirmar_email_pedido",
            kwargs={"token": str(self.token_confirmacao)},
        )
        return f"{base}{path}"

    @property
    def pode_pagar(self) -> bool:
        return (
            self.email_confirmado
            and self.status == self.STATUS_AGUARDA_PAGAMENTO
        )

    @property
    def endereco_entrega(self) -> str:
        return (
            f"{self.morada}, {self.codigo_postal} {self.cidade}, {self.pais}"
        )

    def marcar_como_pago(self, enviar_email: bool = True) -> tuple[bool, str | None]:
        """
        Marca o pedido como pago e envia email ao cliente (se ainda não enviado).
        Retorna (houve_alteracao, erro_email ou None).
        """
        from home.services.pedido_email import enviar_email_pagamento_confirmado

        agora = timezone.now()
        mudou_status = self.status != self.STATUS_PAGO
        self.status = self.STATUS_PAGO
        if not self.pago_em:
            self.pago_em = agora

        erro_email = None
        deve_enviar = enviar_email and not self.email_pagamento_confirmado_em
        if deve_enviar:
            ok, erro_email = enviar_email_pagamento_confirmado(self)
            if ok:
                self.email_pagamento_confirmado_em = agora

        update_fields = ["status", "pago_em", "atualizado_em"]
        if self.email_pagamento_confirmado_em:
            update_fields.append("email_pagamento_confirmado_em")
        if mudou_status or deve_enviar:
            self.save(update_fields=update_fields)

        return (mudou_status or bool(deve_enviar and not erro_email)), erro_email


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_pedido",
    )
    nome_produto = models.CharField(max_length=200)
    tamanho = models.CharField(max_length=5, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Item do pedido"
        verbose_name_plural = "Itens do pedido"

    def __str__(self):
        tam = f" ({self.tamanho})" if self.tamanho else ""
        return f"{self.nome_produto}{tam} × {self.quantidade}"

    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade


class EventoSamba(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data = models.DateTimeField()
    local = models.CharField(max_length=200)
    imagem = models.ImageField(upload_to="samba/", blank=True, null=True)
    imagem_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
    )
    aceita_pedidos = models.BooleanField(
        default=True,
        help_text="Permite pedidos de música neste evento.",
    )
    ativo = models.BooleanField(
        default=True,
        help_text="Só pode haver um evento ativo. Ao marcar este, os outros são desativados.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]
        verbose_name = "Evento pedir música"
        verbose_name_plural = "Eventos pedir música"

    def __str__(self):
        return f"{self.titulo} — {self.data:%d/%m/%Y}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.ativo:
            EventoSamba.objects.filter(ativo=True).exclude(pk=self.pk).update(
                ativo=False
            )

    @property
    def imagem_exibir(self):
        if self.imagem:
            return self.imagem.url
        return self.imagem_url or ""

    @property
    def em_andamento(self):
        agora = timezone.now()
        return self.ativo and self.data <= agora and self.aceita_pedidos


class MotivoRejeicao(models.Model):
    """Motivos predefinidos para rejeitar um pedido de música."""

    nome = models.CharField(max_length=120, verbose_name="Motivo")
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "Motivo de rejeição"
        verbose_name_plural = "Motivos de rejeição"

    def __str__(self):
        return self.nome


class PedidoMusica(models.Model):
    evento = models.ForeignKey(
        EventoSamba,
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    musica = models.CharField(max_length=200, verbose_name="Música")
    artista = models.CharField(max_length=200, blank=True)
    pedido_por = models.CharField(max_length=120, verbose_name="O seu nome")
    mensagem = models.CharField(max_length=300, blank=True)
    observacao_equipe = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Resposta da mesa",
        help_text="Mensagem visível na fila para quem pediu (ex.: já tocamos antes).",
    )
    motivo_rejeicao = models.ForeignKey(
        MotivoRejeicao,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
        verbose_name="Motivo da rejeição",
    )
    tocado = models.BooleanField(default=False, verbose_name="Já tocámos")
    rejeitado = models.BooleanField(
        default=False,
        verbose_name="Rejeitado",
        help_text="Pedido recusado pela mesa (não entra na fila ativa).",
    )
    tocado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tocada em",
        help_text="Data/hora em que a música foi marcada como tocada (ordem na fila).",
    )
    rejeitado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Rejeitado em",
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Última atualização",
    )
    marcado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_musica_marcados",
        verbose_name="Marcado por (membro)",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tocado", "id"]
        verbose_name = "Pedido de música"
        verbose_name_plural = "Pedidos de música"

    def __str__(self):
        return f"{self.musica} — {self.pedido_por}"

    @classmethod
    def ordenar_para_fila(cls, queryset=None):
        """
        Em fila no topo, por id crescente (ordem do pedido).
        Tocadas e rejeitadas juntas abaixo, por atualizado_em decrescente
        (mais recente primeiro), sem separar por tipo.
        """
        from django.db.models import Q
        from itertools import chain

        qs = queryset if queryset is not None else cls.objects.all()
        em_fila = qs.filter(tocado=False, rejeitado=False).order_by("id")
        tratados = qs.filter(Q(tocado=True) | Q(rejeitado=True)).order_by(
            "-atualizado_em", "-id"
        )
        return list(chain(em_fila, tratados))

    @property
    def em_fila(self):
        return not self.tocado and not self.rejeitado

    @property
    def marcado_por_exibir(self):
        if not self.marcado_por_id:
            return ""
        user = self.marcado_por
        nome = (user.get_full_name() or "").strip()
        return nome or user.get_username()

    @property
    def motivo_rejeicao_exibir(self):
        if self.motivo_rejeicao_id and self.motivo_rejeicao:
            return self.motivo_rejeicao.nome
        return ""

    def marcar_tocado(self, observacao_equipe=None, user=None):
        if not self.em_fila:
            return
        self.tocado = True
        self.tocado_em = timezone.now()
        update_fields = ["tocado", "tocado_em", "marcado_por", "atualizado_em"]
        if user is not None and getattr(user, "is_authenticated", False):
            self.marcado_por = user
        if observacao_equipe is not None:
            self.observacao_equipe = (observacao_equipe or "").strip()[:300]
            update_fields.append("observacao_equipe")
        self.save(update_fields=update_fields)

    def marcar_rejeitado(self, observacao_equipe, motivo_rejeicao, user=None):
        if not self.em_fila:
            return
        if motivo_rejeicao is None:
            raise ValueError("Seleccione o motivo da rejeição.")
        obs = (observacao_equipe or "").strip()
        if not obs:
            raise ValueError("A resposta da mesa é obrigatória ao rejeitar um pedido.")
        self.rejeitado = True
        self.rejeitado_em = timezone.now()
        self.motivo_rejeicao = motivo_rejeicao
        self.observacao_equipe = obs[:300]
        update_fields = [
            "rejeitado",
            "rejeitado_em",
            "motivo_rejeicao",
            "observacao_equipe",
            "marcado_por",
            "atualizado_em",
        ]
        if user is not None and getattr(user, "is_authenticated", False):
            self.marcado_por = user
        self.save(update_fields=update_fields)


class VideoEvento(models.Model):
    titulo = models.CharField(max_length=200)
    evento = models.ForeignKey(
        EventoSamba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="videos",
    )
    instagram_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        help_text="Link do post ou reel no Instagram.",
    )
    thumbnail = models.ImageField(upload_to="videos/", blank=True, null=True)
    thumbnail_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        help_text="Preenchida automaticamente ao guardar o link do Instagram (pré-visualização).",
    )
    ordem = models.PositiveIntegerField(default=0)
    destaque = models.BooleanField(
        default=False,
        help_text="Se marcado, o vídeo pode aparecer na página inicial (secção de vídeos).",
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "-criado_em"]
        verbose_name = "Vídeo de evento"
        verbose_name_plural = "Vídeos de eventos"

    def __str__(self):
        return self.titulo

    @property
    def capa_exibir(self):
        if self.thumbnail:
            return self.thumbnail.url
        return self.thumbnail_url or ""

    def _instagram_url_mudou(self) -> bool:
        if not self.pk:
            return bool(self.instagram_url)
        anterior = (
            VideoEvento.objects.filter(pk=self.pk)
            .values_list("instagram_url", flat=True)
            .first()
        )
        return anterior != self.instagram_url

    def precisa_buscar_miniatura(self) -> bool:
        if not self.instagram_url or "instagram.com" not in self.instagram_url:
            return False
        if self._instagram_url_mudou():
            return True
        return not (self.thumbnail or self.thumbnail_url)

    def atualizar_miniatura_instagram(self) -> bool:
        from home.services.instagram_preview import aplicar_miniatura_instagram

        if not self.instagram_url:
            return False
        return aplicar_miniatura_instagram(self, self.instagram_url)

    def save(self, *args, **kwargs):
        if self.precisa_buscar_miniatura():
            self.atualizar_miniatura_instagram()
        super().save(*args, **kwargs)


class SobrePagina(models.Model):
    """Textos da página «Sobre» (singleton)."""

    subtitulo = models.TextField(
        blank=True,
        verbose_name="Introdução",
        help_text="Texto introdutório da página (primeira secção). Deixe linha em branco entre parágrafos.",
    )
    texto_samba_na_rua = models.TextField(
        blank=True,
        verbose_name="Samba na rua, do jeito que tem que ser.",
        help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
    )
    texto_nossa_essencia = models.TextField(
        blank=True,
        verbose_name="Nossa essência",
        help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
    )
    texto_ponto_encontro = models.TextField(
        blank=True,
        verbose_name="O samba é o nosso ponto de encontro",
        help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
    )
    texto_mais_que_musica = models.TextField(
        blank=True,
        verbose_name="Mais que música",
        help_text="Texto desta secção. Deixe linha em branco entre parágrafos.",
    )

    TOPICOS = (
        ("Samba na rua, do jeito que tem que ser.", "texto_samba_na_rua"),
        ("Nossa essência", "texto_nossa_essencia"),
        ("O samba é o nosso ponto de encontro", "texto_ponto_encontro"),
        ("Mais que música", "texto_mais_que_musica"),
    )

    TEXTO_PADRAO_SUBTITULO = "Em respeito ao nosso samba."

    TEXTO_PADRAO_SAMBA_NA_RUA = (
        "O nosso projeto nasceu da vontade de fazer aquilo que o samba sempre soube fazer: "
        "juntar pessoas.\n\n"
        "Mais do que uma apresentação musical, queremos criar encontros. Levar o samba para a "
        "rua, aproximar músicos e público e transformar cada roda num espaço de alegria, amizade, "
        "cultura e celebração."
    )
    TEXTO_PADRAO_NOSSA_ESSENCIA = (
        "Acreditamos no samba feito perto das pessoas.\n\n"
        "Sem distância entre quem toca e quem canta. Aqui, o público também faz parte da roda: "
        "canta, bate palma, dança e ajuda a construir a energia de cada encontro.\n\n"
        "Cavaquinho, banjo, pandeiro, surdo, tantan, repique, reco-reco e muitas vozes se "
        "encontram para manter viva uma das maiores expressões da cultura popular brasileira."
    )
    TEXTO_PADRAO_PONTO_ENCONTRO = (
        "Nosso repertório passeia por diferentes gerações do samba, celebrando grandes "
        "compositores e intérpretes e mantendo espaço para novas histórias e novas músicas.\n\n"
        "Do partido-alto ao samba de roda, dos clássicos que todo mundo conhece às músicas que "
        "merecem ser redescobertas, queremos preservar a essência sem deixar o samba parar no tempo."
    )
    TEXTO_PADRAO_MAIS_QUE_MUSICA = (
        "Para nós, samba é encontro.\n\n"
        "É chegar sem conhecer ninguém e terminar cantando junto.\n\n"
        "É a palma da mão marcando o ritmo.\n\n"
        "É a mesa cercada de amigos.\n\n"
        "É a rua virando palco.\n\n"
        "É aquele refrão que começa com poucos e, quando percebemos, todo mundo está cantando.\n\n"
        "É isso que queremos construir a cada roda.\n\n"
        "Enquanto houver gente para cantar, haverá samba para acontecer.\n\n"
        "Vem pra roda."
    )

    class Meta:
        verbose_name = "Página Sobre"
        verbose_name_plural = "Página Sobre"

    def __str__(self):
        return "Página Sobre"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def subtitulo_exibir(self):
        texto = (self.subtitulo or "").strip()
        return texto or self.TEXTO_PADRAO_SUBTITULO

    def _texto_topico(self, field_name, padrao):
        valor = (getattr(self, field_name) or "").strip()
        return valor or padrao

    @property
    def topicos_exibir(self):
        padroes = {
            "texto_samba_na_rua": self.TEXTO_PADRAO_SAMBA_NA_RUA,
            "texto_nossa_essencia": self.TEXTO_PADRAO_NOSSA_ESSENCIA,
            "texto_ponto_encontro": self.TEXTO_PADRAO_PONTO_ENCONTRO,
            "texto_mais_que_musica": self.TEXTO_PADRAO_MAIS_QUE_MUSICA,
        }
        topicos = [
            {
                "titulo": "",
                "conteudo": self.subtitulo_exibir,
                "intro": True,
            }
        ]
        topicos.extend(
            {
                "titulo": titulo,
                "conteudo": self._texto_topico(campo, padroes[campo]),
                "intro": False,
            }
            for titulo, campo in self.TOPICOS
        )
        return topicos


class ConfiguracaoHome(models.Model):
    """Configurações únicas da página inicial (singleton)."""

    MODO_LOGO = "logo"
    MODO_INSTAGRAM = "instagram"
    MODO_VIDEO = "video"
    MODOS_INTRO = [
        (MODO_LOGO, "Logo"),
        (MODO_INSTAGRAM, "Vídeo do Instagram (incorporado)"),
        (MODO_VIDEO, "Vídeo enviado (ficheiro no servidor)"),
    ]

    modo_intro = models.CharField(
        max_length=20,
        choices=MODOS_INTRO,
        default=MODO_LOGO,
        verbose_name="O que mostrar ao lado do texto",
    )
    logo_arquivo = models.ImageField(
        upload_to="home/intro/",
        blank=True,
        null=True,
        verbose_name="Logo personalizada",
        help_text="Opcional. Se vazio, usa a logo padrão do site (ficheiro estático).",
    )
    video_instagram_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        verbose_name="Link do post/reel no Instagram",
        help_text="Usado quando o modo é «Instagram». Ex.: https://www.instagram.com/reel/xxxxx/",
    )
    instagram_imagem = models.ImageField(
        upload_to="home/intro/instagram/",
        blank=True,
        null=True,
        verbose_name="Imagem de capa (Instagram)",
        help_text=(
            "Opcional. Se enviar, a imagem aparece clicável e abre o link do Instagram "
            "(em vez do player incorporado)."
        ),
    )
    instagram_imagem_url = models.URLField(
        max_length=URL_MAX_LENGTH,
        blank=True,
        verbose_name="URL da imagem de capa",
        help_text=(
            "Opcional. Se vazio, é preenchida automaticamente a partir do link do Instagram "
            "(miniatura estilo WhatsApp)."
        ),
    )
    video_arquivo = models.FileField(
        upload_to="home/intro/videos/",
        blank=True,
        null=True,
        verbose_name="Vídeo (upload)",
        help_text="MP4, WebM ou MOV. Gravado no volume MEDIA_ROOT (Railway).",
    )
    video_poster = models.ImageField(
        upload_to="home/intro/posters/",
        blank=True,
        null=True,
        verbose_name="Capa do vídeo",
        help_text="Imagem exibida antes de dar play (opcional).",
    )
    limite_pedidos_em_fila = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        verbose_name="Máximo de pedidos «Em fila»",
        help_text=(
            "Na página «Pedir música», quando existir este número de músicas "
            "à espera (não tocadas), o formulário de novos pedidos fica bloqueado."
        ),
    )
    pedir_musica_descricao = models.TextField(
        blank=True,
        verbose_name="Descrição da página «Pedir música»",
        help_text=(
            "Texto exibido abaixo do título em /pedir-musica/ (classe page-hero-lead). "
            "Deixe vazio para usar o texto predefinido."
        ),
    )
    videos_descricao = models.TextField(
        blank=True,
        verbose_name="Descrição da página «Vídeos»",
        help_text=(
            "Texto exibido abaixo do título em /videos/ (classe page-hero-lead). "
            "Deixe vazio para usar o texto predefinido."
        ),
    )
    contato_descricao = models.TextField(
        blank=True,
        verbose_name="Introdução da página «Contato»",
        help_text="Texto abaixo do título em /contato/. Deixe vazio para usar o texto predefinido.",
    )
    contato_email = models.EmailField(
        blank=True,
        verbose_name="Email de contacto",
        help_text=(
            "Destino das mensagens enviadas pelo formulário da página «Contato». "
            "Se vazio, usa a variável de ambiente CONTATO_EMAIL."
        ),
    )
    loja_mbway_telefone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Telefone MB Way",
        help_text="Exibido na página de pagamento e confirmação do pedido.",
    )
    loja_iban = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="IBAN (transferência)",
        help_text="IBAN para pagamento por transferência bancária.",
    )

    TEXTO_PADRAO_PEDIR_MUSICA = (
        "Peça a música que quer ouvir e acompanhe a fila ao vivo. Quando a mesa responder "
        "ao seu pedido, a mensagem aparece em «Resposta da mesa» no seu lugar na fila."
    )
    TEXTO_PADRAO_VIDEOS = (
        "Escolha um evento para ver os vídeos publicados no Instagram. Os marcados como destaque "
        "também aparecem na página inicial."
    )
    TEXTO_PADRAO_CONTATO = (
        "Fale connosco para parcerias, eventos ou qualquer questão sobre o projeto."
    )

    class Meta:
        verbose_name = "Configuração da página inicial"
        verbose_name_plural = "Configuração da página inicial"

    def __str__(self):
        return "Configuração da página inicial"

    def _instagram_link_mudou(self) -> bool:
        if not self.pk:
            return bool(self.video_instagram_url)
        anterior = (
            ConfiguracaoHome.objects.filter(pk=self.pk)
            .values_list("video_instagram_url", flat=True)
            .first()
        )
        return anterior != self.video_instagram_url

    def precisa_buscar_capa_instagram(self) -> bool:
        if self.modo_intro != self.MODO_INSTAGRAM or not self.video_instagram_url:
            return False
        if self._instagram_link_mudou():
            return True
        return not self.instagram_imagem_exibir

    def atualizar_capa_instagram(self) -> bool:
        from home.services.instagram_preview import aplicar_miniatura_instagram

        if not self.video_instagram_url:
            return False
        return aplicar_miniatura_instagram(
            self,
            self.video_instagram_url,
            url_field="instagram_imagem_url",
            image_field="instagram_imagem",
            guardar_ficheiro=True,
        )

    def save(self, *args, **kwargs):
        self.pk = 1
        if self.precisa_buscar_capa_instagram():
            self.atualizar_capa_instagram()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def pedir_musica_lead_exibir(self):
        texto = (self.pedir_musica_descricao or "").strip()
        return texto or self.TEXTO_PADRAO_PEDIR_MUSICA

    @property
    def videos_lead_exibir(self):
        texto = (self.videos_descricao or "").strip()
        return texto or self.TEXTO_PADRAO_VIDEOS

    @property
    def contato_lead_exibir(self):
        texto = (self.contato_descricao or "").strip()
        return texto or self.TEXTO_PADRAO_CONTATO

    @property
    def mbway_telefone_exibir(self):
        return (self.loja_mbway_telefone or "").strip()

    @property
    def iban_exibir(self):
        return (self.loja_iban or "").strip()

    @property
    def instagram_permalink(self):
        url = (self.video_instagram_url or "").strip()
        if not url or "instagram.com" not in url:
            return ""
        base = url.split("?")[0].rstrip("/")
        return f"{base}/"

    @property
    def exibir_instagram(self):
        return self.modo_intro == self.MODO_INSTAGRAM and bool(self.instagram_permalink)

    @property
    def instagram_imagem_exibir(self):
        if self.instagram_imagem and self.instagram_imagem.name:
            return self.instagram_imagem.url
        if self.instagram_imagem_url:
            return self.instagram_imagem_url
        return ""

    @property
    def instagram_usar_imagem_link(self):
        return self.exibir_instagram and bool(self.instagram_imagem_exibir)

    @property
    def instagram_usar_embed(self):
        return self.exibir_instagram and not self.instagram_imagem_exibir

    @property
    def exibir_video_arquivo(self):
        return self.modo_intro == self.MODO_VIDEO and bool(self.video_arquivo)

    @property
    def exibir_logo(self):
        return self.modo_intro == self.MODO_LOGO or (
            self.modo_intro == self.MODO_INSTAGRAM and not self.instagram_permalink
        ) or (self.modo_intro == self.MODO_VIDEO and not self.video_arquivo)

    @property
    def logo_personalizada_url(self):
        if self.logo_arquivo:
            return self.logo_arquivo.url
        return ""

    @property
    def video_content_type(self):
        name = (self.video_arquivo.name or "").lower()
        if name.endswith(".webm"):
            return "video/webm"
        if name.endswith(".mov"):
            return "video/quicktime"
        return "video/mp4"


class Contato(models.Model):
    """Contacto cadastrado (nome, telefone, email) — página «Contato»."""

    nome = models.CharField(max_length=120, verbose_name="Nome")
    telefone = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Telefone",
    )
    email = models.EmailField(
        blank=True,
        verbose_name="Email",
    )
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "Contacto"
        verbose_name_plural = "Contactos"

    def __str__(self):
        return self.nome

    @property
    def telefone_exibir(self):
        return (self.telefone or "").strip()

    @property
    def email_exibir(self):
        return (self.email or "").strip()
