from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    ConfiguracaoHome,
    EventoDestaque,
    EventoSamba,
    Patrocinador,
    PedidoMusica,
    Produto,
    SlideHome,
    VideoEvento,
)


@admin.register(ConfiguracaoHome)
class ConfiguracaoHomeAdmin(admin.ModelAdmin):
    readonly_fields = ("preview_intro",)

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
            "Pedir música",
            {
                "fields": ("limite_pedidos_em_fila",),
                "description": (
                    "Limite de pedidos com estado «Em fila» na página pública. "
                    "Ao atingir o máximo, o formulário de novos pedidos fica bloqueado."
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
            return "Guarde o patrocinador para importar a imagem da URL."
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


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "destaque", "ordem", "ativo")
    list_editable = ("ordem", "ativo", "destaque")
    list_filter = ("ativo", "destaque")
    search_fields = ("nome",)


class PedidoMusicaInline(admin.TabularInline):
    model = PedidoMusica
    extra = 0
    readonly_fields = ("criado_em", "tocado_em")
    fields = (
        "musica",
        "artista",
        "pedido_por",
        "mensagem",
        "observacao_equipe",
        "tocado",
        "criado_em",
    )


@admin.register(EventoSamba)
class EventoSambaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data", "local", "aceita_pedidos", "ativo")
    list_filter = ("ativo", "aceita_pedidos")
    search_fields = ("titulo", "local")
    inlines = [PedidoMusicaInline]

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
                "Os outros eventos de samba foram desativados — só pode haver um ativo.",
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
        "observacao_equipe",
        "criado_em",
    )
    list_filter = ("tocado", "evento")
    search_fields = ("musica", "pedido_por", "artista")
    actions = ["marcar_como_tocados"]

    @admin.action(description="Marcar selecionados como já tocados")
    def marcar_como_tocados(self, request, queryset):
        for pedido in queryset.filter(tocado=False):
            pedido.marcar_tocado()


@admin.register(VideoEvento)
class VideoEventoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "evento", "ordem", "ativo", "preview")
    list_editable = ("ordem", "ativo")
    list_filter = ("ativo",)
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
