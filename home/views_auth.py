from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .forms import CadastroUtilizadorForm
from .models import CadastroEmailToken
from .services.cadastro_email import enviar_email_confirmacao_cadastro

User = get_user_model()


def cadastro(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("home:pedir_musica"))

    form = CadastroUtilizadorForm()
    if request.method == "POST":
        form = CadastroUtilizadorForm(request.POST)
        if form.is_valid():
            user = form.save()
            ok, _erro = enviar_email_confirmacao_cadastro(user)
            request.session["cadastro_email"] = user.email
            if ok:
                messages.success(
                    request,
                    "Cadastro recebido. Enviámos um email para confirmar o endereço.",
                )
            else:
                messages.warning(
                    request,
                    "A conta foi criada, mas o email de confirmação não saiu. "
                    "Use o botão para reenviar.",
                )
            return HttpResponseRedirect(reverse("home:cadastro_verifique_email"))

    return render(
        request,
        "registration/cadastro.html",
        {"form": form, "nav_active": "cadastro"},
    )


@require_GET
def cadastro_verifique_email(request):
    email = request.session.get("cadastro_email") or ""
    return render(
        request,
        "registration/cadastro_verifique_email.html",
        {"email": email, "nav_active": "cadastro"},
    )


@require_GET
def confirmar_cadastro(request, token):
    token_obj = (
        CadastroEmailToken.objects.filter(token=token).select_related("user").first()
    )
    if token_obj is None:
        messages.info(
            request,
            "Este link já foi usado ou não é válido. "
            "Inicie sessão se a conta já estiver activa.",
        )
        return HttpResponseRedirect(reverse("home:login"))

    user = token_obj.user
    if user.is_active:
        token_obj.delete()
        messages.info(request, "A conta já estava confirmada. Pode iniciar sessão.")
        return HttpResponseRedirect(reverse("home:login"))

    if not token_obj.valido():
        request.session["cadastro_email"] = user.email
        messages.error(
            request,
            "O link de confirmação expirou. Reenvie o email para obter um novo.",
        )
        return HttpResponseRedirect(reverse("home:cadastro_verifique_email"))

    token_obj.confirmar()
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.pop("cadastro_email", None)
    messages.success(
        request,
        "Email confirmado. Bem-vindo à roda — já pode pedir a sua música.",
    )
    return HttpResponseRedirect(reverse("home:pedir_musica"))


@require_POST
def reenviar_confirmacao_cadastro(request):
    email = (
        (request.POST.get("email") or request.session.get("cadastro_email") or "")
        .strip()
        .lower()
    )
    if not email:
        messages.error(request, "Indique o email da conta para reenviar a confirmação.")
        return HttpResponseRedirect(reverse("home:cadastro_verifique_email"))

    request.session["cadastro_email"] = email
    user = (
        User.objects.filter(email__iexact=email).order_by("-is_active").first()
        or User.objects.filter(username__iexact=email).first()
    )
    if user is None:
        messages.success(
            request,
            "Se existir uma conta com este email, enviámos um novo link de confirmação.",
        )
        return HttpResponseRedirect(reverse("home:cadastro_verifique_email"))

    if user.is_active:
        messages.info(request, "Esta conta já está confirmada. Inicie sessão.")
        return HttpResponseRedirect(reverse("home:login"))

    CadastroEmailToken.renovar_para(user)
    ok, _erro = enviar_email_confirmacao_cadastro(user)
    if ok:
        messages.success(request, "Enviámos um novo email de confirmação.")
    else:
        messages.error(
            request,
            "Não foi possível enviar o email agora. Tente novamente dentro de instantes.",
        )
    return HttpResponseRedirect(reverse("home:cadastro_verifique_email"))
