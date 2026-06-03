from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Pedido, PedidoMusica, Produto, TamanhoProduto


class EquipeLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Utilizador",
        widget=forms.TextInput(
            attrs={"class": "form-input", "placeholder": "Utilizador", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Palavra-passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "Palavra-passe"}
        ),
    )


class PedidoMusicaForm(forms.ModelForm):
    class Meta:
        model = PedidoMusica
        fields = ["musica", "artista", "pedido_por", "mensagem"]
        widgets = {
            "musica": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nome da música",
                    "required": True,
                }
            ),
            "artista": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Artista (opcional)",
                }
            ),
            "pedido_por": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "O seu nome",
                    "required": True,
                }
            ),
            "mensagem": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Mensagem para a roda (opcional)",
                }
            ),
        }


class AdicionarCarrinhoForm(forms.Form):
    quantidade = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        label="Quantidade",
        widget=forms.NumberInput(attrs={"class": "form-input", "min": "1", "max": "99"}),
    )
    tamanho = forms.ChoiceField(
        required=False,
        label="Tamanho",
        widget=forms.Select(attrs={"class": "form-input"}),
    )

    def __init__(self, *args, produto: Produto | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.produto = produto
        if not produto or not produto.requer_tamanho:
            self.fields.pop("tamanho", None)
        else:
            tamanhos = produto.tamanhos_ativos()
            if not tamanhos.exists():
                self.fields["tamanho"].choices = TamanhoProduto.TAMANHOS
            else:
                self.fields["tamanho"].choices = [("", "Escolha o tamanho")] + [
                    (t.codigo, t.codigo) for t in tamanhos
                ]
            self.fields["tamanho"].required = True

    def clean(self):
        cleaned = super().clean()
        if self.produto and self.produto.requer_tamanho:
            tamanho = (cleaned.get("tamanho") or "").strip()
            if not tamanho:
                self.add_error("tamanho", "Escolha um tamanho.")
            elif not self.produto.tamanho_valido(tamanho):
                self.add_error("tamanho", "Tamanho não disponível.")
        return cleaned


class CheckoutEntregaForm(forms.Form):
    nome = forms.CharField(
        max_length=120,
        label="Nome completo",
        widget=forms.TextInput(attrs={"class": "form-input", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-input", "autocomplete": "email"}),
    )
    email_confirmacao = forms.EmailField(
        label="Confirmar email",
        widget=forms.EmailInput(
            attrs={"class": "form-input", "autocomplete": "email"}
        ),
    )
    telefone = forms.CharField(
        max_length=30,
        label="Telefone",
        widget=forms.TextInput(attrs={"class": "form-input", "autocomplete": "tel"}),
    )
    morada = forms.CharField(
        max_length=300,
        label="Morada",
        widget=forms.TextInput(attrs={"class": "form-input", "autocomplete": "street-address"}),
    )
    codigo_postal = forms.CharField(
        max_length=20,
        label="Código postal",
        widget=forms.TextInput(attrs={"class": "form-input", "autocomplete": "postal-code"}),
    )
    cidade = forms.CharField(
        max_length=120,
        label="Cidade",
        widget=forms.TextInput(attrs={"class": "form-input", "autocomplete": "address-level2"}),
    )
    pais = forms.CharField(
        max_length=80,
        initial="Portugal",
        label="País",
        widget=forms.TextInput(attrs={"class": "form-input", "autocomplete": "country-name"}),
    )
    notas_entrega = forms.CharField(
        required=False,
        max_length=500,
        label="Notas para entrega (opcional)",
        widget=forms.Textarea(
            attrs={"class": "form-input", "rows": 3, "placeholder": "Ex.: portão azul, entregar ao porteiro…"}
        ),
    )

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        conf = (cleaned.get("email_confirmacao") or "").strip().lower()
        if email and conf and email != conf:
            self.add_error("email_confirmacao", "Os emails não coincidem.")
        return cleaned


class CheckoutPagamentoForm(forms.Form):
    metodo_pagamento = forms.ChoiceField(
        choices=Pedido.METODOS_PAGAMENTO,
        label="Forma de pagamento",
        widget=forms.RadioSelect(attrs={"class": "checkout-radio"}),
    )
    referencia_pagamento = forms.CharField(
        required=False,
        max_length=120,
        label="Telefone MB Way (se aplicável)",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Número associado ao MB Way",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        metodo = cleaned.get("metodo_pagamento")
        ref = (cleaned.get("referencia_pagamento") or "").strip()
        if metodo == Pedido.METODO_MBWAY and not ref:
            self.add_error(
                "referencia_pagamento",
                "Indique o telefone para recebermos o pedido de pagamento MB Way.",
            )
        return cleaned


class MarcarPedidoTocadoForm(forms.Form):
    observacao_equipe = forms.CharField(
        required=False,
        max_length=300,
        label="Resposta da mesa",
        widget=forms.TextInput(
            attrs={
                "class": "form-input form-input--sm",
                "placeholder": "Resposta visível na fila (opcional)",
                "maxlength": "300",
            }
        ),
    )
