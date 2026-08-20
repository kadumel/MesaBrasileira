/* Avisos PWA da equipa — novos pedidos de música */
(function () {
  "use strict";

  const panel = document.getElementById("push-equipe");
  if (!panel) {
    return;
  }

  const btn = document.getElementById("push-equipe-btn");
  const texto = document.getElementById("push-equipe-texto");
  const vapid = panel.dataset.vapid || "";
  const subscribeUrl = panel.dataset.subscribeUrl || "";
  const unsubscribeUrl = panel.dataset.unsubscribeUrl || "";

  function csrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const raw = atob(base64);
    const output = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i += 1) {
      output[i] = raw.charCodeAt(i);
    }
    return output;
  }

  function isStandalone() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  function isIos() {
    return /iphone|ipad|ipod/i.test(navigator.userAgent);
  }

  function supported() {
    return (
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window
    );
  }

  function setEstado(estado, mensagem, rotuloBotao) {
    panel.hidden = false;
    panel.dataset.estado = estado;
    if (texto && mensagem) {
      texto.textContent = mensagem;
    }
    if (btn && rotuloBotao) {
      btn.textContent = rotuloBotao;
      btn.hidden = estado === "indisponivel";
    }
  }

  async function postJson(url, body) {
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error("Falha ao guardar a subscrição.");
    }
  }

  async function registration() {
    await navigator.serviceWorker.register("/sw.js", { scope: "/" });
    return navigator.serviceWorker.ready;
  }

  async function currentSubscription() {
    const reg = await registration();
    return reg.pushManager.getSubscription();
  }

  function subscriptionPayload(subscription) {
    const json = subscription.toJSON();
    return {
      endpoint: json.endpoint,
      keys: {
        p256dh: json.keys && json.keys.p256dh,
        auth: json.keys && json.keys.auth,
      },
    };
  }

  async function ativar() {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      setEstado(
        "inativo",
        "Os avisos ficam bloqueados neste aparelho. Autorize notificações nas definições do sistema para receber os pedidos.",
        "Ativar avisos"
      );
      return;
    }
    const reg = await registration();
    let subscription = await reg.pushManager.getSubscription();
    if (!subscription) {
      subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapid),
      });
    }
    await postJson(subscribeUrl, subscriptionPayload(subscription));
    setEstado(
      "ativo",
      "Avisos ativos neste aparelho. Quando pedirem uma música, vê o título e o artista.",
      "Desativar avisos"
    );
  }

  async function desativar() {
    const subscription = await currentSubscription();
    if (subscription) {
      try {
        await postJson(unsubscribeUrl, subscriptionPayload(subscription));
      } catch (_) {
        /* mesmo sem o servidor, remove localmente */
      }
      await subscription.unsubscribe();
    } else if (unsubscribeUrl) {
      await postJson(unsubscribeUrl, {});
    }
    setEstado(
      "inativo",
      "Receba o nome da música e o artista quando alguém pedir na roda.",
      "Ativar avisos"
    );
  }

  async function syncGranted() {
    try {
      await ativar();
    } catch (_) {
      setEstado(
        "inativo",
        "Não foi possível ativar os avisos. Tente de novo ou reinstale a aplicação MB.pt.",
        "Ativar avisos"
      );
    }
  }

  if (!supported() || !vapid) {
    if (isIos() && !isStandalone()) {
      setEstado(
        "indisponivel",
        "No iPhone, toque em Partilhar e escolha Adicionar ao ecrã inicial. Depois abra o MB.pt a partir do ícone para ativar os avisos.",
        ""
      );
    }
    return;
  }

  if (isIos() && !isStandalone()) {
    setEstado(
      "indisponivel",
      "No iPhone, adicione o MB.pt ao ecrã inicial (Partilhar → Adicionar ao ecrã inicial) e abra a partir do ícone para receber avisos.",
      ""
    );
    return;
  }

  if (btn) {
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        if (panel.dataset.estado === "ativo") {
          await desativar();
        } else {
          await ativar();
        }
      } catch (_) {
        setEstado(
          "inativo",
          "Não foi possível alterar os avisos. Tente novamente.",
          "Ativar avisos"
        );
      } finally {
        btn.disabled = false;
      }
    });
  }

  if (Notification.permission === "granted") {
    syncGranted();
  } else if (Notification.permission === "denied") {
    setEstado(
      "inativo",
      "Os avisos estão bloqueados neste aparelho. Autorize notificações nas definições para a mesa receber os pedidos.",
      "Ativar avisos"
    );
  } else {
    setEstado(
      "inativo",
      "Receba o nome da música e o artista quando alguém pedir na roda.",
      "Ativar avisos"
    );
  }
})();
