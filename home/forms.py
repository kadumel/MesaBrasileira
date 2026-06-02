from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import PedidoMusica


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
