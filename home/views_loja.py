from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .cart import (
    add_to_cart,
    cart_count,
    cart_subtotal,
    clear_cart,
    get_cart_lines,
    remove_line,
    update_line,
)
from .forms import AdicionarCarrinhoForm, CheckoutEntregaForm, CheckoutPagamentoForm
from .models import ItemPedido, Pedido, Produto
from .services.pedido_email import enviar_email_confirmacao


def _loja_context(request, **extra):
    return {
        "nav_active": "loja",
        "cart_count": cart_count(request.session),
        **extra,
    }


def carrinho(request):
    linhas = get_cart_lines(request.session)
    context = _loja_context(
        request,
        linhas=linhas,
        subtotal=cart_subtotal(request.session),
        vazio=not linhas,
    )
    return render(request, "home/carrinho.html", context)


@require_POST
def carrinho_adicionar(request, pk):
    produto = get_object_or_404(Produto, pk=pk, ativo=True)
    form = AdicionarCarrinhoForm(request.POST, produto=produto)
    if not form.is_valid():
        for field, errs in form.errors.items():
            for err in errs:
                messages.error(request, err)
        return redirect("home:produto_detail", pk=pk)

    tamanho = form.cleaned_data.get("tamanho") or ""
    erro = add_to_cart(
        request.session,
        produto.pk,
        form.cleaned_data["quantidade"],
        tamanho=tamanho,
    )
    if erro:
        messages.error(request, erro)
        return redirect("home:produto_detail", pk=pk)

    messages.success(request, f"«{produto.nome}» adicionado ao carrinho.")
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url == "carrinho":
        return redirect("home:carrinho")
    return redirect("home:produto_detail", pk=pk)


@require_POST
def carrinho_atualizar(request):
    line_id = request.POST.get("line_id")
    try:
        quantidade = int(request.POST.get("quantidade", 1))
    except (TypeError, ValueError):
        quantidade = 1
    erro = update_line(request.session, line_id, quantidade)
    if erro:
        messages.error(request, erro)
    return redirect("home:carrinho")


@require_POST
def carrinho_remover(request, line_id):
    if remove_line(request.session, line_id):
        messages.info(request, "Item removido do carrinho.")
    return redirect("home:carrinho")


def checkout(request):
    linhas = get_cart_lines(request.session)
    if not linhas:
        messages.warning(request, "O carrinho está vazio.")
        return redirect("home:loja")

    form = CheckoutEntregaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        subtotal = cart_subtotal(request.session)
        pedido = Pedido(
            numero=Pedido.gerar_numero(),
            nome=form.cleaned_data["nome"].strip(),
            email=form.cleaned_data["email"].strip().lower(),
            telefone=form.cleaned_data["telefone"].strip(),
            morada=form.cleaned_data["morada"].strip(),
            codigo_postal=form.cleaned_data["codigo_postal"].strip(),
            cidade=form.cleaned_data["cidade"].strip(),
            pais=form.cleaned_data["pais"].strip() or "Portugal",
            notas_entrega=form.cleaned_data.get("notas_entrega", "").strip(),
            subtotal=subtotal,
            total=subtotal,
            status=Pedido.STATUS_AGUARDA_EMAIL,
        )
        pedido.definir_expiracao_token()
        pedido.save()

        for linha in linhas:
            ItemPedido.objects.create(
                pedido=pedido,
                produto=linha.produto,
                nome_produto=linha.produto.nome,
                tamanho=linha.tamanho,
                quantidade=linha.quantidade,
                preco_unitario=linha.preco_unitario,
            )

        clear_cart(request.session)

        enviado, erro_email = enviar_email_confirmacao(pedido)
        if enviado:
            messages.success(
                request,
                f"Enviámos um email para {pedido.email}. Confirme o endereço "
                "para continuar com o pagamento (verifique também o spam).",
            )
        elif "console" in settings.EMAIL_BACKEND:
            messages.warning(
                request,
                f"Pedido {pedido.numero} registado. O servidor está em modo de email "
                "consola (desenvolvimento): o email não foi enviado de verdade. "
                "Configure SMTP no .env e reinicie o runserver.",
            )
        else:
            detalhe = f" ({erro_email})" if erro_email and settings.DEBUG else ""
            messages.warning(
                request,
                "Pedido registado, mas não foi possível enviar o email de confirmação. "
                f"Contacte-nos pelo Instagram com o número {pedido.numero}.{detalhe}",
            )

        request.session["ultimo_pedido_numero"] = pedido.numero
        return redirect("home:checkout_aguarda_email", numero=pedido.numero)

    context = _loja_context(
        request,
        form=form,
        linhas=linhas,
        subtotal=cart_subtotal(request.session),
    )
    return render(request, "home/checkout.html", context)


def checkout_aguarda_email(request, numero):
    pedido = get_object_or_404(Pedido, numero=numero)
    context = _loja_context(request, pedido=pedido)
    return render(request, "home/checkout_aguarda_email.html", context)


def confirmar_email_pedido(request, token):
    pedido = get_object_or_404(Pedido, token_confirmacao=token)
    if pedido.email_confirmado:
        messages.info(request, "Este pedido já foi confirmado.")
        return redirect("home:checkout_pagamento", numero=pedido.numero)

    if not pedido.token_valido():
        pedido.status = Pedido.STATUS_EXPIRADO
        pedido.save(update_fields=["status", "atualizado_em"])
        messages.error(
            request,
            "O link de confirmação expirou. Faça um novo pedido ou contacte-nos.",
        )
        return redirect("home:loja")

    pedido.confirmar_email()
    messages.success(
        request,
        "Email confirmado. Complete o pagamento para finalizar a encomenda.",
    )
    return redirect("home:checkout_pagamento", numero=pedido.numero)


def checkout_pagamento(request, numero):
    pedido = get_object_or_404(Pedido, numero=numero)
    if not pedido.email_confirmado:
        messages.warning(
            request,
            "Confirme o email antes de pagar. Verifique a sua caixa de entrada.",
        )
        return redirect("home:checkout_aguarda_email", numero=numero)

    if pedido.status == Pedido.STATUS_PAGO:
        return redirect("home:pedido_confirmado", numero=numero)

    if pedido.status not in (
        Pedido.STATUS_AGUARDA_PAGAMENTO,
        Pedido.STATUS_AGUARDA_EMAIL,
    ):
        messages.error(request, "Este pedido já não aceita pagamento.")
        return redirect("home:loja")

    form = CheckoutPagamentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        pedido.metodo_pagamento = form.cleaned_data["metodo_pagamento"]
        pedido.referencia_pagamento = (
            form.cleaned_data.get("referencia_pagamento") or ""
        ).strip()
        pedido.save(
            update_fields=[
                "metodo_pagamento",
                "referencia_pagamento",
                "atualizado_em",
            ]
        )
        messages.success(
            request,
            "Instruções de pagamento registadas. Assim que recebermos o pagamento, "
            "entraremos em contacto para enviar a encomenda.",
        )
        return redirect("home:pedido_confirmado", numero=numero)

    context = _loja_context(
        request,
        pedido=pedido,
        form=form,
        mbway_telefone=getattr(settings, "LOJA_MBWAY_TELEFONE", ""),
        iban=getattr(settings, "LOJA_IBAN", ""),
    )
    return render(request, "home/checkout_pagamento.html", context)


def pedido_confirmado(request, numero):
    pedido = get_object_or_404(Pedido, numero=numero)
    context = _loja_context(
        request,
        pedido=pedido,
        mbway_telefone=getattr(settings, "LOJA_MBWAY_TELEFONE", ""),
        iban=getattr(settings, "LOJA_IBAN", ""),
    )
    return render(request, "home/pedido_confirmado.html", context)
