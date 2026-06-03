"""Gera PDF com o fluxo completo de vendas da loja Mesa Brasileira."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class Command(BaseCommand):
    help = "Gera o PDF «Fluxo de Vendas — Mesa Brasileira» em docs/"

    def handle(self, *args, **options):
        docs_dir = Path(settings.BASE_DIR) / "docs"
        docs_dir.mkdir(exist_ok=True)
        output = docs_dir / "fluxo-vendas-mesa-brasileira.pdf"

        site_url = getattr(settings, "SITE_URL", "https://mesabrasileira.pt").rstrip("/")

        doc = SimpleDocTemplate(
            str(output),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title="Fluxo de Vendas — Mesa Brasileira",
            author="Mesa Brasileira",
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "MBTitle",
            parent=styles["Heading1"],
            fontSize=22,
            textColor=colors.HexColor("#4b3621"),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        h2 = ParagraphStyle(
            "MBH2",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#009739"),
            spaceBefore=16,
            spaceAfter=8,
        )
        h3 = ParagraphStyle(
            "MBH3",
            parent=styles["Heading3"],
            fontSize=11,
            textColor=colors.HexColor("#4b3621"),
            spaceBefore=10,
            spaceAfter=6,
        )
        body = ParagraphStyle(
            "MBBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4b3621"),
        )
        small = ParagraphStyle(
            "MBSmall",
            parent=body,
            fontSize=9,
            textColor=colors.HexColor("#6b5344"),
        )

        story = []

        # Capa
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph("Mesa Brasileira", title_style))
        story.append(Paragraph("Fluxo de Vendas — Loja Online", h2))
        story.append(Spacer(1, 0.5 * cm))
        story.append(
            Paragraph(
                f"Documento gerado automaticamente a partir do sistema.<br/>"
                f"Site: <b>{site_url}</b>",
                body,
            )
        )
        story.append(PageBreak())

        # Visão geral
        story.append(Paragraph("1. Visão geral", h2))
        story.append(
            Paragraph(
                "A loja funciona como e-commerce integrado no site Django: catálogo de produtos, "
                "carrinho em sessão, checkout com dados de entrega, confirmação de email, "
                "pagamento (MB Way ou transferência) e gestão de pedidos no painel de administração.",
                body,
            )
        )

        story.append(Paragraph("1.1 Diagrama do fluxo", h3))
        fluxo_data = [
            ["Etapa", "Quem", "Ação", "Estado do pedido"],
            ["1", "Cliente", "Navega na Loja e escolhe produto", "—"],
            ["2", "Cliente", "Adiciona ao carrinho (tamanho se necessário)", "—"],
            ["3", "Cliente", "Revisa carrinho e vai ao Checkout", "—"],
            ["4", "Sistema", "Cria pedido e envia email de confirmação", "Aguarda email"],
            ["5", "Cliente", "Clica no link do email (48 h)", "Aguarda pagamento"],
            ["6", "Cliente", "Escolhe MB Way ou transferência", "Aguarda pagamento"],
            ["7", "Admin", "Confirma pagamento recebido no /admin/", "Pago — entrega"],
            ["8", "Sistema", "Envia email «pagamento recebido»", "Pago — entrega"],
        ]
        story.append(_tabela(fluxo_data, col_widths=[1.2 * cm, 2.2 * cm, 7.5 * cm, 4.5 * cm]))
        story.append(Spacer(1, 0.3 * cm))

        # Cliente
        story.append(Paragraph("2. Fluxo do cliente (passo a passo)", h2))

        passos_cliente = [
            (
                "Loja",
                f"{site_url}/loja/",
                "Lista de produtos ativos. Produtos com «Exige tamanho» pedem S/M/L/XL/XXL ao adicionar.",
            ),
            (
                "Detalhe do produto",
                f"{site_url}/loja/&lt;id&gt;/",
                "Formulário: quantidade, tamanho (se aplicável), «Adicionar ao carrinho».",
            ),
            (
                "Carrinho",
                f"{site_url}/loja/carrinho/",
                "Alterar quantidades, remover itens, «Finalizar compra». Ícone no menu.",
            ),
            (
                "Checkout",
                f"{site_url}/loja/checkout/",
                "Nome, email (duplo), telefone, morada, CP, cidade, país, notas. Submete pedido.",
            ),
            (
                "Aguarda email",
                f"{site_url}/loja/checkout/aguarda-email/&lt;numero&gt;/",
                "Mensagem: verificar caixa de entrada e spam. Link válido 48 horas.",
            ),
            (
                "Confirmar email",
                f"{site_url}/loja/checkout/confirmar-email/&lt;token&gt;/",
                "Link único no email. Passa pedido para «Aguarda pagamento».",
            ),
            (
                "Pagamento",
                f"{site_url}/loja/checkout/pagamento/&lt;numero&gt;/",
                "Instruções MB Way / IBAN. Cliente indica método e telefone MB Way se aplicável.",
            ),
            (
                "Pedido registado",
                f"{site_url}/loja/pedido/&lt;numero&gt;/",
                "Resumo final. Aguarda confirmação manual do pagamento pela equipa.",
            ),
        ]
        for titulo, url, desc in passos_cliente:
            story.append(Paragraph(f"<b>{titulo}</b>", h3))
            story.append(Paragraph(f"URL: {url}", small))
            story.append(Paragraph(desc, body))
            story.append(Spacer(1, 0.15 * cm))

        story.append(PageBreak())

        # Admin
        story.append(Paragraph("3. Fluxo do administrador", h2))
        story.append(
            Paragraph(
                "Acesso: <b>/admin/</b> → secção <b>Pedidos da loja</b>. "
                "Cada pedido mostra cliente, morada, itens, método de pagamento e estado.",
                body,
            )
        )
        story.append(Spacer(1, 0.2 * cm))

        admin_passos = [
            [
                "Verificar pagamento",
                "Confirmar MB Way ou transferência na conta bancária (referência = número do pedido).",
            ],
            [
                "Marcar como pago",
                "Alterar estado para «Pago — a preparar entrega» OU usar a ação em massa "
                "«Marcar como pago e enviar email ao cliente».",
            ],
            [
                "Email automático",
                "O cliente recebe email HTML com confirmação de pagamento e morada de entrega.",
            ],
            [
                "Preparar envio",
                "Preparar encomenda e expedir. Campo «Email pagamento confirmado» indica se o email foi enviado.",
            ],
            [
                "Reenviar email",
                "Ação «Reenviar email pagamento recebido» se o cliente não tiver recebido.",
            ],
        ]
        story.append(
            _tabela(
                [["Ação", "Descrição"]] + admin_passos,
                col_widths=[4.5 * cm, 12 * cm],
            )
        )

        story.append(Paragraph("3.1 Estados do pedido", h3))
        estados = [
            ["Código", "Nome no admin", "Significado"],
            ["aguarda_email", "Aguarda confirmação de email", "Pedido criado; à espera do clique no link"],
            ["aguarda_pagamento", "Aguarda pagamento", "Email confirmado; cliente deve pagar"],
            ["pago", "Pago — a preparar entrega", "Pagamento confirmado pela equipa"],
            ["cancelado", "Cancelado", "Pedido anulado manualmente"],
            ["expirado", "Expirado", "Link de confirmação expirou (> 48 h)"],
        ]
        story.append(_tabela(estados, col_widths=[4 * cm, 5.5 * cm, 7 * cm]))

        story.append(PageBreak())

        # Produtos
        story.append(Paragraph("4. Configuração de produtos (admin)", h2))
        story.append(
            Paragraph(
                "<b>Produtos</b> em /admin/: preço, imagem, ativo, destaque.<br/>"
                "<b>Exige escolha de tamanho</b>: ativar para camisolas, etc.<br/>"
                "<b>Tamanhos do produto</b> (inline): definir quais tamanhos estão disponíveis (S, M, L, XL, XXL).",
                body,
            )
        )

        # Emails
        story.append(Paragraph("5. Emails automáticos", h2))
        emails = [
            ["Momento", "Assunto (exemplo)", "Conteúdo principal"],
            [
                "Após checkout",
                "Confirme o seu pedido MB-…",
                "Link de confirmação (48 h), total, logo e cores da marca",
            ],
            [
                "Admin marca pago",
                "Pagamento recebido — pedido MB-…",
                "Confirmação de pagamento, morada de entrega, preparação do envio",
            ],
            [
                "Teste (comando)",
                "Teste de email — Mesa Brasileira",
                "python manage.py testar_email email@exemplo.com",
            ],
        ]
        story.append(_tabela(emails, col_widths=[3.5 * cm, 5 * cm, 8 * cm]))

        story.append(Paragraph("5.1 Envio de email em produção (n8n)", h3))
        story.append(
            Paragraph(
                "<b>Problema:</b> Railway bloqueia SMTP (Gmail porta 587).<br/>"
                "<b>Solução:</b> webhook <b>n8n</b> — variável <b>N8N_WEBHOOK_URL</b> no Railway. "
                "O Django envia JSON (assunto, html, destinatário); o workflow n8n envia via Gmail. "
                "Guia completo: docs/n8n-emails.md<br/>"
                "Em local: omitir N8N_WEBHOOK_URL e usar Gmail SMTP no .env.",
                body,
            )
        )

        env_vars = [
            ["Variável", "Onde", "Função"],
            ["SITE_URL", "Railway / .env", "Links nos emails (confirmação)"],
            ["N8N_WEBHOOK_URL", "Railway", "URL do webhook n8n (envio em produção)"],
            ["N8N_WEBHOOK_SECRET", "Opcional", "Header X-Webhook-Secret"],
            ["DEFAULT_FROM_EMAIL", "Railway / .env", "Campo «de» no JSON para o n8n"],
            ["LOJA_MBWAY_TELEFONE", "Railway / .env", "Instruções na página de pagamento"],
            ["LOJA_IBAN", "Railway / .env", "IBAN na página de pagamento"],
            ["EMAIL_HOST_*", "Apenas local", "SMTP Gmail (desenvolvimento)"],
        ]
        story.append(Paragraph("5.2 Variáveis de ambiente", h3))
        story.append(_tabela(env_vars, col_widths=[4 * cm, 3 * cm, 9.5 * cm]))

        story.append(PageBreak())

        # Número pedido
        story.append(Paragraph("6. Identificação e dados técnicos", h2))
        story.append(
            Paragraph(
                "<b>Número do pedido:</b> formato MB-AAAAMMDD-XXXXXX (ex.: MB-20260603-8E2658).<br/>"
                "<b>Carrinho:</b> guardado na sessão do browser (sem login obrigatório).<br/>"
                "<b>Itens do pedido:</b> guardam nome, preço e tamanho no momento da compra.<br/>"
                "<b>Token de email:</b> UUID único; expira em 48 h (LOJA_TOKEN_EMAIL_HORAS).",
                body,
            )
        )

        story.append(Spacer(1, 1 * cm))
        story.append(
            Paragraph(
                "<i>Para regenerar este PDF: python manage.py gerar_pdf_fluxo_vendas</i>",
                small,
            )
        )

        doc.build(story)
        self.stdout.write(self.style.SUCCESS(f"PDF criado: {output}"))


def _tabela(dados, col_widths=None):
    t = Table(dados, colWidths=col_widths, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6d5b8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#4b3621")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d4c4a8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf6ef")]),
    ]
    t.setStyle(TableStyle(estilo))
    return t
