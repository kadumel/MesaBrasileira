from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    ConfiguracaoHome,
    Contato,
    EventoDestaque,
    EventoSamba,
    InscricaoPush,
    ItemPedido,
    MotivoRejeicao,
    Patrocinador,
    Pedido,
    PedidoMusica,
    Produto,
    SlideHome,
    SobrePagina,
    TamanhoProduto,
    VideoEvento,
)


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email", "ordem", "ativo")
    list_editable = ("ordem", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "telefone", "email")
    ordering = ("ordem", "nome")


@admin.register(MotivoRejeicao)
class MotivoRejeicaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem", "ativo")
    list_editable = ("ordem", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)
    ordering = ("ordem", "nome")


@admin.register(ConfiguracaoHome)
class ConfiguracaoHomeAdmin(admin.ModelAdmin):
    readonly_fields = ("preview_intro", "preview_audio_roda")

    fieldsets = (
        (
            "Modo de exibição",
            {
                "fields": ("modo_intro", "preview_intro"),
                "description": (
                    "Escolha o que aparece ao lado do texto de boas-vindas: "
                    "logo, Instagram (imagem clicável ou player) ou vídeo enviado."
                ),
            },
        ),
        (
            "Logo",
            {
                "fields": ("logo_arquivo",),
                "description": "Usado quando o modo é «Logo». Deixe vazio para a logo padrão do site.",
            },
        ),
        (
            "Instagram",
            {
                "fields": (
                    "video_instagram_url",
                    "instagram_imagem",
                    "instagram_imagem_url",
                ),
                "description": (
                    "Link do post/reel (obrigatório). "
                    "Se enviar imagem de capa (upload ou URL), ela aparece clicável "
                    "e abre o Instagram; sem imagem, usa o player incorporado."
                ),
            },
        ),
        (
            "Vídeo no servidor (Railway / volume)",
            {
                "fields": ("video_arquivo", "video_poster"),
                "description": (
                    "Usado quando o modo é «Vídeo enviado». "
                    "Os ficheiros ficam em MEDIA_ROOT (configure o volume no Railway)."
                ),
            },
        ),
        (
            "Samba da página inicial",
            {
                "fields": ("audio_roda", "preview_audio_roda"),
                "description": (
                    "MP3 tocado automaticamente no hero da roda de samba. "
                    "Se vazio, usa o ficheiro padrão do site. "
                    "O ficheiro fica em MEDIA_ROOT (configure o volume no Railway)."
                ),
            },
        ),
        (
            "Pedir música",
            {
                "fields": ("pedir_musica_descricao", "limite_pedidos_em_fila"),
                "description": (
                    "Texto introdutório e limite da fila na página pública «Pedir música»."
                ),
            },
        ),
        (
            "Vídeos",
            {
                "fields": ("videos_descricao",),
                "description": "Texto introdutório da página pública «Vídeos» (/videos/).",
            },
        ),
        (
            "Contato",
            {
                "fields": ("contato_descricao", "contato_email"),
                "description": (
                    "Texto introdutório da página pública «Contato» (/contato/). "
                    "Os contactos (nome, telefone, email) gerem-se em Admin → Contactos. "
                    "O email abaixo recebe as mensagens do formulário "
                    "(fallback: CONTATO_EMAIL no .env / Railway)."
                ),
            },
        ),
        (
            "Vendas",
            {
                "fields": ("loja_mbway_telefone", "loja_iban"),
                "description": (
                    "Dados de pagamento na loja (checkout e confirmação do pedido). "
                    "Deixe vazio para ocultar essa forma de pagamento na página."
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return not ConfiguracaoHome.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Pré-visualização")
    def preview_intro(self, obj):
        if not obj:
            return "—"
        if obj.modo_intro == ConfiguracaoHome.MODO_VIDEO and obj.video_arquivo:
            return format_html(
                '<video src="{}" controls style="max-width:280px;max-height:160px"></video>',
                obj.video_arquivo.url,
            )
        if obj.instagram_usar_imagem_link:
            return format_html(
                '<img src="{}" style="max-width:280px;border-radius:8px"/>'
                '<p style="margin:.5rem 0 0">Modo: imagem clicável → Instagram</p>',
                obj.instagram_imagem_exibir,
            )
        if obj.instagram_usar_embed:
            return "Modo: player incorporado do Instagram (sem imagem de capa)."
        if obj.modo_intro == ConfiguracaoHome.MODO_INSTAGRAM and not obj.instagram_permalink:
            return mark_safe(
                '<span style="color:#c45a1a">Falta o link do Instagram.</span>'
            )
        if obj.logo_personalizada_url:
            return format_html(
                '<img src="{}" style="max-width:120px;border-radius:50%"/>',
                obj.logo_personalizada_url,
            )
        return "Logo padrão do site"

    @admin.display(description="Pré-visualização do MP3")
    def preview_audio_roda(self, obj):
        if not obj or not obj.audio_roda:
            return "Nenhum MP3 enviado — a home usa o samba padrão."
        return format_html(
            '<audio src="{}" controls style="max-width:320px;width:100%"></audio>',
            obj.audio_roda.url,
        )

    def save_model(self, request, obj, form, change):
        capa_ok = False
        if obj.precisa_buscar_capa_instagram():
            capa_ok = obj.atualizar_capa_instagram()
        super().save_model(request, obj, form, change)
        if obj.modo_intro == ConfiguracaoHome.MODO_INSTAGRAM:
            if not obj.instagram_permalink:
                self.message_user(
                    request,
                    "Modo Instagram ativo mas falta o link do post/reel.",
                    level="warning",
                )
            elif capa_ok:
                self.message_user(
                    request,
                    "Capa obtida automaticamente do Instagram (estilo pré-visualização).",
                    level="success",
                )
            elif not obj.instagram_imagem_exibir:
                self.message_user(
                    request,
                    "Sem imagem de capa: será usado o player incorporado do Instagram.",
                    level="info",
                )


@admin.register(EventoDestaque)
class EventoDestaqueAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data_evento", "local", "destaque", "ordem", "ativo")
    list_editable = ("destaque", "ordem", "ativo")
    list_filter = ("ativo", "destaque")
    search_fields = ("titulo", "local")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "titulo",
                    "descricao",
                    "data_evento",
                    "local",
                    "link",
                ),
            },
        ),
        (
            "Vídeos e galeria",
            {
                "fields": ("instagram_videos_url", "midias_url"),
                "description": (
                    "Links opcionais. Quando preenchidos, aparecem no cartão "
                    "(página Eventos e início) e na página de detalhe do evento."
                ),
            },
        ),
        (
            "Imagem",
            {"fields": ("imagem", "imagem_url")},
        ),
        (
            "Publicação",
            {
                "fields": ("destaque", "ativo", "ordem"),
                "description": (
                    "Destaque: visível na página inicial. "
                    "Ativo: visível na página Eventos (e na inicial se destaque)."
                ),
            },
        ),
    )


@admin.register(SlideHome)
class SlideHomeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "evento", "ordem", "ativo", "preview")
    list_editable = ("ordem", "ativo")
    list_filter = ("ativo", "tipo")
    search_fields = ("titulo", "subtitulo")
    autocomplete_fields = ("evento",)

    @admin.display(description="Imagem")
    def preview(self, obj):
        url = obj.imagem_exibir
        if not url:
            return "—"
        return format_html('<img src="{}" height="36" style="border-radius:4px"/>', url)


@admin.register(SobrePagina)
class SobrePaginaAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Quem Somos",
            {
                "fields": ("texto_quem_somos",),
            },
        ),
        (
            "Uma roda feita por todos",
            {
                "fields": ("texto_roda_por_todos",),
            },
        ),
        (
            "Em respeito ao nosso samba",
            {
                "fields": ("texto_respeito_samba",),
            },
        ),
        (
            "Cultura em primeiro lugar",
            {
                "fields": ("texto_cultura_primeiro",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not SobrePagina.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Patrocinador)
class PatrocinadorAdmin(admin.ModelAdmin):
    list_display = ("nome", "site", "ordem", "ativo", "preview")
    list_editable = ("ordem", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)
    actions = ["baixar_logos_das_urls"]
    readonly_fields = ("preview_logo",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "nome",
                    "logo",
                    "logo_url",
                    "preview_logo",
                    "site",
                    "ordem",
                    "ativo",
                ),
            },
        ),
    )

    @admin.display(description="Logo")
    def preview(self, obj):
        url = obj.logo_exibir
        if not url:
            return "—"
        return format_html('<img src="{}" height="32" style="object-fit:contain"/>', url)

    @admin.display(description="Pré-visualização")
    def preview_logo(self, obj):
        if not obj or not obj.pk:
            return "Guarde o parceiro para importar a imagem da URL."
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width:200px;max-height:100px;object-fit:contain"/>'
                "<p style='margin:.5rem 0 0'>Logo guardada no servidor.</p>",
                obj.logo.url,
            )
        if obj.logo_url:
            return mark_safe(
                '<span style="color:#c45a1a">Só há URL — clique em Guardar para importar, '
                "ou use a ação «Baixar logos das URLs».</span>"
            )
        return "Sem logo."

    def save_model(self, request, obj, form, change):
        ok = False
        if obj.precisa_baixar_logo():
            ok = obj.baixar_logo_da_url()
        super().save_model(request, obj, form, change)
        if ok:
            self.message_user(
                request,
                f"Logo de «{obj.nome}» importada para o servidor com sucesso.",
                level="success",
            )
        elif (obj.logo_url or "").strip() and not obj.logo:
            self.message_user(
                request,
                "Não foi possível importar a imagem dessa URL (link expirado ou bloqueado). "
                "Envie o ficheiro em «Logo» ou use outra URL.",
                level="warning",
            )

    @admin.action(description="Baixar logos das URLs (selecionados)")
    def baixar_logos_das_urls(self, request, queryset):
        ok = 0
        for pat in queryset:
            if pat.baixar_logo_da_url():
                pat.save(update_fields=["logo"])
                ok += 1
        self.message_user(request, f"{ok} logo(s) importada(s) para o servidor.", level="success")


class TamanhoProdutoInline(admin.TabularInline):
    model = TamanhoProduto
    extra = 0
    fields = ("codigo", "ativo", "ordem")


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("nome_produto", "tamanho", "quantidade", "preco_unitario", "produto")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "requer_tamanho", "destaque", "ordem", "ativo")
    list_editable = ("ordem", "ativo", "destaque", "requer_tamanho")
    list_filter = ("ativo", "destaque", "requer_tamanho")
    search_fields = ("nome",)
    inlines = [TamanhoProdutoInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "nome",
                    "descricao",
                    "preco",
                    "requer_tamanho",
                    "imagem",
                    "imagem_url",
                    "link_compra",
                ),
            },
        ),
        ("Publicação", {"fields": ("destaque", "ativo", "ordem")}),
    )


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "nome",
        "email",
        "status",
        "metodo_pagamento",
        "total",
        "pago_em",
        "criado_em",
    )
    list_filter = ("status", "email_confirmado", "metodo_pagamento")
    search_fields = ("numero", "nome", "email", "telefone")
    readonly_fields = (
        "numero",
        "token_confirmacao",
        "token_expira_em",
        "subtotal",
        "total",
        "criado_em",
        "atualizado_em",
        "email_confirmado_em",
        "pago_em",
        "email_pagamento_confirmado_em",
    )
    inlines = [ItemPedidoInline]
    actions = ["marcar_como_pago", "reenviar_email_pagamento"]
    fieldsets = (
        (
            "Pedido",
            {
                "fields": ("numero", "status", "subtotal", "total"),
                "description": (
                    "Quando receber o MB Way ou transferência, altere o estado para "
                    "«Pago — a preparar entrega» ou use a ação em massa. "
                    "O cliente recebe email automaticamente."
                ),
            },
        ),
        (
            "Cliente e entrega",
            {
                "fields": (
                    "nome",
                    "email",
                    "telefone",
                    "morada",
                    "codigo_postal",
                    "cidade",
                    "pais",
                    "notas_entrega",
                ),
            },
        ),
        (
            "Pagamento",
            {
                "fields": (
                    "metodo_pagamento",
                    "referencia_pagamento",
                    "pago_em",
                    "email_pagamento_confirmado_em",
                ),
            },
        ),
        (
            "Confirmação de email (checkout)",
            {
                "classes": ("collapse",),
                "fields": (
                    "email_confirmado",
                    "email_confirmado_em",
                    "token_confirmacao",
                    "token_expira_em",
                ),
            },
        ),
        (
            "Datas",
            {
                "classes": ("collapse",),
                "fields": ("criado_em", "atualizado_em"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        status_anterior = None
        if change and obj.pk:
            status_anterior = (
                Pedido.objects.filter(pk=obj.pk)
                .values_list("status", flat=True)
                .first()
            )
        super().save_model(request, obj, form, change)
        if (
            obj.status == Pedido.STATUS_PAGO
            and status_anterior != Pedido.STATUS_PAGO
        ):
            _, erro = obj.marcar_como_pago(enviar_email=True)
            if erro:
                self.message_user(
                    request,
                    f"Pedido {obj.numero} marcado como pago, mas o email falhou: {erro}",
                    level="warning",
                )
            else:
                self.message_user(
                    request,
                    f"Pedido {obj.numero} pago — email enviado para {obj.email}.",
                    level="success",
                )

    @admin.action(description="Marcar como pago e enviar email ao cliente")
    def marcar_como_pago(self, request, queryset):
        pagos = 0
        emails = 0
        falhas = []
        for pedido in queryset.select_related():
            alterado, erro = pedido.marcar_como_pago(enviar_email=True)
            if pedido.status == Pedido.STATUS_PAGO:
                pagos += 1
            if pedido.email_pagamento_confirmado_em:
                emails += 1
            if erro:
                falhas.append(f"{pedido.numero}: {erro}")
        msg = f"{pagos} pedido(s) como pago(s). {emails} email(s) de confirmação enviado(s)."
        if falhas:
            self.message_user(
                request,
                f"{msg} Falhas: {'; '.join(falhas[:3])}",
                level="warning",
            )
        else:
            self.message_user(request, msg, level="success")

    @admin.action(description="Reenviar email «pagamento recebido»")
    def reenviar_email_pagamento(self, request, queryset):
        from home.services.pedido_email import enviar_email_pagamento_confirmado
        from django.utils import timezone

        ok = 0
        for pedido in queryset.filter(status=Pedido.STATUS_PAGO):
            enviado, erro = enviar_email_pagamento_confirmado(pedido)
            if enviado:
                pedido.email_pagamento_confirmado_em = timezone.now()
                pedido.save(update_fields=["email_pagamento_confirmado_em", "atualizado_em"])
                ok += 1
            elif erro:
                self.message_user(
                    request,
                    f"{pedido.numero}: {erro}",
                    level="warning",
                )
        self.message_user(request, f"{ok} email(s) reenviado(s).", level="success")


class PedidoMusicaInline(admin.TabularInline):
    model = PedidoMusica
    extra = 0
    readonly_fields = (
        "criado_em",
        "tocado_em",
        "rejeitado_em",
        "atualizado_em",
        "marcado_por",
    )
    fields = (
        "musica",
        "artista",
        "pedido_por",
        "mensagem",
        "observacao_equipe",
        "motivo_rejeicao",
        "tocado",
        "rejeitado",
        "marcado_por",
        "criado_em",
    )


@admin.register(EventoSamba)
class EventoSambaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data", "local", "aceita_pedidos", "ativo")
    list_filter = ("ativo", "aceita_pedidos")
    search_fields = ("titulo", "local")
    inlines = [PedidoMusicaInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "titulo",
                    "descricao",
                    "data",
                    "local",
                    "imagem",
                    "imagem_url",
                ),
            },
        ),
        (
            "Pedidos e estado",
            {
                "fields": ("aceita_pedidos", "ativo"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        outros_ativos = (
            EventoSamba.objects.filter(ativo=True).exclude(pk=obj.pk).count()
            if obj.pk
            else EventoSamba.objects.filter(ativo=True).count()
        )
        super().save_model(request, obj, form, change)
        if obj.ativo and outros_ativos:
            self.message_user(
                request,
                "Os outros eventos «pedir música» foram desativados — só pode haver um ativo.",
                level="success",
            )


@admin.register(PedidoMusica)
class PedidoMusicaAdmin(admin.ModelAdmin):
    list_display = (
        "musica",
        "artista",
        "pedido_por",
        "evento",
        "tocado",
        "rejeitado",
        "motivo_rejeicao",
        "tocado_em",
        "rejeitado_em",
        "marcado_por",
        "observacao_equipe",
        "criado_em",
    )
    list_filter = ("tocado", "rejeitado", "motivo_rejeicao", "evento")
    search_fields = ("musica", "pedido_por", "artista")
    autocomplete_fields = ("motivo_rejeicao",)
    actions = ["marcar_como_tocados"]

    @admin.action(description="Marcar selecionados como já tocados")
    def marcar_como_tocados(self, request, queryset):
        for pedido in queryset.filter(tocado=False, rejeitado=False):
            pedido.marcar_tocado(user=request.user)


@admin.register(InscricaoPush)
class InscricaoPushAdmin(admin.ModelAdmin):
    list_display = ("user", "endpoint_curto", "atualizado_em", "criado_em")
    list_filter = ("user",)
    search_fields = ("user__username", "endpoint")
    readonly_fields = (
        "user",
        "endpoint",
        "p256dh",
        "auth",
        "user_agent",
        "criado_em",
        "atualizado_em",
    )

    @admin.display(description="Endpoint")
    def endpoint_curto(self, obj):
        if len(obj.endpoint) <= 64:
            return obj.endpoint
        return f"{obj.endpoint[:64]}…"


@admin.register(VideoEvento)
class VideoEventoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "evento", "destaque", "ordem", "ativo", "preview")
    list_editable = ("destaque", "ordem", "ativo")
    list_filter = ("ativo", "destaque", "evento")
    actions = ["buscar_miniaturas_instagram"]
    readonly_fields = ("preview_capa",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "titulo",
                    "evento",
                    "instagram_url",
                    "preview_capa",
                    "thumbnail",
                    "thumbnail_url",
                    "ordem",
                    "destaque",
                    "ativo",
                ),
            },
        ),
    )

    @admin.display(description="Capa")
    def preview(self, obj):
        url = obj.capa_exibir
        if not url:
            return "—"
        return format_html('<img src="{}" height="40" style="border-radius:4px"/>', url)

    @admin.display(description="Pré-visualização (automática)")
    def preview_capa(self, obj):
        if not obj or not obj.pk:
            return "Guarde o vídeo com o link do Instagram para buscar a miniatura."
        url = obj.capa_exibir
        if not url:
            return mark_safe(
                '<span style="color:#c45a1a">Miniatura não encontrada. '
                "Use a ação «Buscar miniaturas do Instagram».</span>"
            )
        return format_html(
            '<img src="{}" style="max-width:220px;border-radius:8px"/>'
            "<p style='margin:.5rem 0 0'>Atualizada automaticamente ao guardar o link.</p>",
            url,
        )

    def save_model(self, request, obj, form, change):
        ok = False
        if obj.instagram_url and obj.precisa_buscar_miniatura():
            ok = obj.atualizar_miniatura_instagram()
        super().save_model(request, obj, form, change)
        if ok:
            self.message_user(request, "Miniatura do Instagram obtida com sucesso.", level="success")
        elif obj.instagram_url and not obj.capa_exibir:
            self.message_user(
                request,
                "Não foi possível obter a miniatura. O Instagram pode bloquear — "
                "tente de novo ou envie a imagem manualmente.",
                level="warning",
            )

    @admin.action(description="Buscar miniaturas do Instagram (selecionados)")
    def buscar_miniaturas_instagram(self, request, queryset):
        ok = 0
        for video in queryset:
            if video.atualizar_miniatura_instagram():
                video.save(update_fields=["thumbnail", "thumbnail_url"])
                ok += 1
        self.message_user(request, f"{ok} miniatura(s) atualizada(s).", level="success")
