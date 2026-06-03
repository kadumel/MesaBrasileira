"""Carrinho de compras em sessão Django."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import uuid4

from django.shortcuts import get_object_or_404

from .models import Produto

CART_SESSION_KEY = "carrinho"


@dataclass
class LinhaCarrinho:
    id: str
    produto: Produto
    quantidade: int
    tamanho: str
    preco_unitario: Decimal
    subtotal: Decimal

    @property
    def tamanho_exibir(self) -> str:
        return self.tamanho or "—"


def _cart_raw(session) -> list[dict[str, Any]]:
    return list(session.get(CART_SESSION_KEY) or [])


def _save_cart(session, items: list[dict[str, Any]]) -> None:
    session[CART_SESSION_KEY] = items
    session.modified = True


def cart_count(session) -> int:
    return sum(int(i.get("quantidade") or 0) for i in _cart_raw(session))


def clear_cart(session) -> None:
    session.pop(CART_SESSION_KEY, None)
    session.modified = True


def get_cart_lines(session) -> list[LinhaCarrinho]:
    raw = _cart_raw(session)
    if not raw:
        return []
    ids = {int(i["produto_id"]) for i in raw if i.get("produto_id")}
    produtos = {p.pk: p for p in Produto.objects.filter(pk__in=ids, ativo=True)}
    linhas: list[LinhaCarrinho] = []
    for item in raw:
        produto = produtos.get(int(item.get("produto_id") or 0))
        if not produto:
            continue
        qty = max(1, int(item.get("quantidade") or 1))
        tamanho = (item.get("tamanho") or "").strip().upper()
        linhas.append(
            LinhaCarrinho(
                id=str(item.get("id") or ""),
                produto=produto,
                quantidade=qty,
                tamanho=tamanho,
                preco_unitario=produto.preco,
                subtotal=produto.preco * qty,
            )
        )
    return linhas


def cart_subtotal(session) -> Decimal:
    return sum((l.subtotal for l in get_cart_lines(session)), Decimal("0"))


def _validar_linha(produto: Produto, quantidade: int, tamanho: str) -> str | None:
    if quantidade < 1 or quantidade > 99:
        return "Quantidade inválida."
    if produto.requer_tamanho:
        if not tamanho:
            return "Escolha um tamanho."
        if not produto.tamanho_valido(tamanho):
            return "Tamanho não disponível para este produto."
    elif tamanho:
        return "Este produto não usa tamanhos."
    return None


def add_to_cart(session, produto_id: int, quantidade: int = 1, tamanho: str = "") -> str | None:
    produto = get_object_or_404(Produto, pk=produto_id, ativo=True)
    tamanho = (tamanho or "").strip().upper()
    erro = _validar_linha(produto, quantidade, tamanho)
    if erro:
        return erro

    items = _cart_raw(session)
    for item in items:
        if (
            int(item.get("produto_id")) == produto.pk
            and (item.get("tamanho") or "").upper() == tamanho
        ):
            item["quantidade"] = min(99, int(item.get("quantidade") or 0) + quantidade)
            _save_cart(session, items)
            return None

    items.append(
        {
            "id": uuid4().hex,
            "produto_id": produto.pk,
            "quantidade": quantidade,
            "tamanho": tamanho,
        }
    )
    _save_cart(session, items)
    return None


def update_line(session, line_id: str, quantidade: int) -> str | None:
    items = _cart_raw(session)
    for item in items:
        if str(item.get("id")) == str(line_id):
            produto = get_object_or_404(Produto, pk=int(item["produto_id"]), ativo=True)
            tamanho = (item.get("tamanho") or "").upper()
            erro = _validar_linha(produto, quantidade, tamanho)
            if erro:
                return erro
            if quantidade < 1:
                items.remove(item)
            else:
                item["quantidade"] = quantidade
            _save_cart(session, items)
            return None
    return "Item não encontrado no carrinho."


def remove_line(session, line_id: str) -> bool:
    items = _cart_raw(session)
    novo = [i for i in items if str(i.get("id")) != str(line_id)]
    if len(novo) == len(items):
        return False
    _save_cart(session, novo)
    return True
