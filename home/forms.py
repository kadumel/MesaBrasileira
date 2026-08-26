from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Pedido, PedidoMusica, Produto, TamanhoProduto, MotivoRejeicao


class EquipeLoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Email, utilizador ou palavra-passe incorrectos.",
        "inactive": "Confirme o seu email para activar a conta. Verifique a caixa de entrada.",
    }
    username = forms.CharField(
        label="Email ou utilizador",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Email ou utilizador",
                "autofocus": True,
                "autocomplete": "username",
            }
        ),
    )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if "@" in username:
            UserModel = get_user_model()
            user = (
                UserModel.objects.filter(Q(email__iexact=username) | Q(username__iexact=username))
                .order_by("-is_active")
                .first()
            )
            if user:
                return user.get_username()
            return username.lower()
        return username
    password = forms.CharField(
        label="Palavra-passe",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "Palavra-passe"}
        ),
    )



class CadastroUtilizadorForm(forms.Form):
    nome = forms.CharField(
        max_length=150,
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "O seu nome",
                "autocomplete": "name",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "seu@email.com",
                "autocomplete": "email",
            }
        ),
    )
    password1 = forms.CharField(
        label="Palavra-passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Palavra-passe",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmar palavra-passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Repita a palavra-passe",
                "autocomplete": "new-password",
            }
        ),
    )

    aceita_emails_promocionais = forms.BooleanField(
        required=False,
        initial=True,
        label="Quero receber emails promocionais e publicidade da Mesa Brasileira.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_nome(self):
        return (self.cleaned_data.get("nome") or "").strip()

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        UserModel = get_user_model()
        existente = UserModel.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).first()
        if existente and existente.is_active:
            raise ValidationError(
                "Já existe uma conta com este email. Inicie sessão."
            )
        self._utilizador_existente = existente
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "As palavras-passe não coincidem.")
        elif p1:
            try:
                password_validation.validate_password(p1)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        from .models import CadastroEmailToken, PerfilUtilizador

        email = self.cleaned_data["email"]
        nome = self.cleaned_data["nome"]
        password = self.cleaned_data["password1"]
        UserModel = get_user_model()
        user = getattr(self, "_utilizador_existente", None)
        if user:
            user.set_password(password)
            user.email = email
            user.username = email[:150]
            user.first_name = nome[:150]
            user.last_name = ""
            user.is_active = False
            user.save()
        else:
            user = UserModel.objects.create_user(
                username=email[:150],
                email=email,
                password=password,
                first_name=nome[:150],
                is_active=False,
            )
        CadastroEmailToken.renovar_para(user)
        PerfilUtilizador.objects.update_or_create(
            user=user,
            defaults={
                "aceita_emails_promocionais": bool(
                    self.cleaned_data.get("aceita_emails_promocionais")
                ),
            },
        )
        return user


class PedidoMusicaForm(forms.ModelForm):
    class Meta:
        model = PedidoMusica
        fields = ["musica", "artista", "mensagem"]
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


class ContatoForm(forms.Form):
    nome = forms.CharField(
        max_length=120,
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "autocomplete": "name",
                "placeholder": "O seu nome",
                "id": "contato-nome",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-input", "autocomplete": "email", "placeholder": "seu@email.com"}
        ),
    )
    assunto = forms.CharField(
        max_length=200,
        label="Assunto",
        widget=forms.TextInput(
            attrs={"class": "form-input", "placeholder": "Assunto da mensagem"}
        ),
    )
    mensagem = forms.CharField(
        max_length=3000,
        label="Mensagem",
        widget=forms.Textarea(
            attrs={
                "class": "form-input",
                "rows": 6,
                "placeholder": "Escreva a sua mensagem…",
            }
        ),
    )


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


class RejeitarPedidoMusicaForm(forms.Form):
    motivo_rejeicao = forms.ModelChoiceField(
        queryset=MotivoRejeicao.objects.none(),
        label="Motivo da rejeição",
        empty_label="Escolha o motivo",
        widget=forms.Select(attrs={"class": "form-input form-input--sm queue-motivo-select"}),
    )
    observacao_equipe = forms.CharField(
        required=False,
        max_length=300,
        label="Resposta da mesa",
        widget=forms.TextInput(
            attrs={
                "class": "form-input form-input--sm",
                "placeholder": "Resposta da mesa (opcional)",
                "maxlength": "300",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["motivo_rejeicao"].queryset = MotivoRejeicao.objects.filter(
            ativo=True
        )

    def clean_observacao_equipe(self):
        return (self.cleaned_data.get("observacao_equipe") or "").strip()[:300]
