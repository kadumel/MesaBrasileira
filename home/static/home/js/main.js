(function () {
  "use strict";

  const header = document.querySelector(".site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");

  if (header) {
    window.addEventListener(
      "scroll",
      () => {
        header.classList.toggle("scrolled", window.scrollY > 40);
      },
      { passive: true }
    );
  }

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      const open = navLinks.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open);
    });

    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        navLinks.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  const revealEls = document.querySelectorAll(".reveal, .reveal-stagger");
  if (revealEls.length && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      // threshold 0: any pixel in view is enough. A ratio like 0.12 never
      // fires for tall stacked grids on mobile (event cards stay opacity: 0).
      { threshold: 0, rootMargin: "0px 0px -8% 0px" }
    );
    revealEls.forEach((el) => observer.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("visible"));
  }

  if (typeof Swiper !== "undefined" && document.querySelector(".banner-swiper")) {
    const bannerMobile = window.matchMedia("(max-width: 900px)");
    const bannerSwiper = new Swiper(".banner-swiper", {
      slidesPerView: 1,
      loop: true,
      speed: 600,
      autoHeight: bannerMobile.matches,
      autoplay: {
        delay: 5500,
        disableOnInteraction: false,
      },
      pagination: {
        el: ".banner-pagination",
        clickable: true,
      },
      navigation: {
        nextEl: ".banner-next",
        prevEl: ".banner-prev",
      },
    });
    bannerMobile.addEventListener("change", (event) => {
      bannerSwiper.params.autoHeight = event.matches;
      bannerSwiper.update();
    });
  }

  const videoModal = document.getElementById("intro-video-modal");
  const videoModalOpen = document.querySelector("[data-video-modal-open]");
  if (videoModal && videoModalOpen) {
    const videoModalPlayer = videoModal.querySelector(".video-modal-player");
    const siteAudio = document.querySelector("[data-site-audio]");
    const supportsDialog = typeof videoModal.showModal === "function";

    if (videoModal.parentElement !== document.body) {
      document.body.appendChild(videoModal);
    }

    function pauseSiteAudioForVideo() {
      if (siteAudio && !siteAudio.paused) {
        siteAudio.dataset.videoPause = "1";
        siteAudio.pause();
      }
    }

    function resumeSiteAudioAfterVideo() {
      if (!siteAudio || siteAudio.dataset.videoPause !== "1") return;
      delete siteAudio.dataset.videoPause;
      const play = siteAudio.play();
      if (play && typeof play.catch === "function") {
        play.catch(() => {});
      }
    }

    function isVideoModalOpen() {
      return videoModal.open || videoModal.classList.contains("is-open");
    }

    function openVideoModal() {
      pauseSiteAudioForVideo();
      if (supportsDialog) {
        if (!videoModal.open) videoModal.showModal();
      } else {
        videoModal.setAttribute("open", "");
        videoModal.classList.add("is-open");
        document.body.style.overflow = "hidden";
      }
      if (videoModalPlayer) {
        const play = videoModalPlayer.play();
        if (play && typeof play.catch === "function") {
          play.catch(() => {});
        }
      }
    }

    function closeVideoModal() {
      if (videoModalPlayer) {
        videoModalPlayer.pause();
      }
      if (supportsDialog) {
        if (videoModal.open) videoModal.close();
      } else {
        videoModal.removeAttribute("open");
        videoModal.classList.remove("is-open");
        document.body.style.overflow = "";
        resumeSiteAudioAfterVideo();
      }
    }

    videoModalOpen.addEventListener("click", openVideoModal);
    videoModal.querySelectorAll("[data-video-modal-close]").forEach((el) => {
      el.addEventListener("click", closeVideoModal);
    });
    videoModal.addEventListener("click", (event) => {
      if (event.target === videoModal) closeVideoModal();
    });
    videoModal.addEventListener("close", () => {
      if (videoModalPlayer) videoModalPlayer.pause();
      resumeSiteAudioAfterVideo();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isVideoModalOpen() && !supportsDialog) {
        closeVideoModal();
      }
    });
  }

  document.querySelectorAll("[data-tilt]").forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform = `perspective(800px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) translateY(-6px)`;
    });
    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });

  const form = document.getElementById("form-pedido");
  const queueList = document.getElementById("queue-list");
  const queuePanel = document.getElementById("queue-panel");
  const feedback = document.getElementById("form-feedback");

  let refreshPaused = false;

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function getCsrfToken() {
    const src = document.getElementById("queue-csrf-source");
    const fromQueue = src && src.querySelector("[name=csrfmiddlewaretoken]");
    if (fromQueue && fromQueue.value) {
      return fromQueue.value;
    }
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  function equipeAtiva() {
    return !!(queuePanel && queuePanel.dataset.podeMarcar === "1");
  }

  function isTocado(p) {
    return p.tocado === true || p.tocado === 1 || p.tocado === "1" || p.tocado === "true";
  }

  function isRejeitado(p) {
    return (
      p.rejeitado === true ||
      p.rejeitado === 1 ||
      p.rejeitado === "1" ||
      p.rejeitado === "true"
    );
  }

  function emFila(p) {
    return !isTocado(p) && !isRejeitado(p);
  }

  function fetchFila(url) {
    const sep = url.includes("?") ? "&" : "?";
    return fetch(`${url}${sep}_=${Date.now()}`, {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
    });
  }

  function marcarPedidoUrl(id) {
    const sample = queuePanel && queuePanel.dataset.marcarUrlSample;
    if (sample) {
      return sample.replace("/0/", `/${id}/`);
    }
    return `/pedido-musica/${id}/tocar/`;
  }

  function rejeitarPedidoUrl(id) {
    const sample = queuePanel && queuePanel.dataset.rejeitarUrlSample;
    if (sample) {
      return sample.replace("/0/", `/${id}/`);
    }
    return `/pedido-musica/${id}/rejeitar/`;
  }

  function renderQueueItemNotes(p) {
    let html = "";
    if (p.mensagem) {
      html += `<p class="queue-item-note queue-item-note--public"><span class="queue-item-note-label">Mensagem:</span> ${escapeHtml(p.mensagem)}</p>`;
    }
    if (p.motivo_rejeicao_exibir) {
      html += `<p class="queue-item-note queue-item-note--motivo" role="status"><span class="queue-item-note-label">Motivo:</span> ${escapeHtml(p.motivo_rejeicao_exibir)}</p>`;
    }
    if (p.observacao_equipe) {
      html += `<p class="queue-item-note queue-item-note--resposta" role="status"><span class="queue-item-note-label">Resposta da mesa:</span> ${escapeHtml(p.observacao_equipe)}</p>`;
    }
    if (!emFila(p) && p.marcado_por_exibir) {
      html += `<p class="queue-item-note queue-item-note--marcador"><span class="queue-item-note-label">Tratado por:</span> ${escapeHtml(p.marcado_por_exibir)}</p>`;
    }
    return html;
  }

  function renderStatusBadge(p) {
    if (isTocado(p)) {
      return '<span class="badge badge-queue badge-queue--tocada">Já tocada</span>';
    }
    if (isRejeitado(p)) {
      return '<span class="badge badge-queue badge-queue--rejeitada">Rejeitada</span>';
    }
    return '<span class="badge badge-queue badge-queue--fila">Em fila</span>';
  }

  function renderQueueBodyHtml(p) {
    const artistaVal = p.artista
      ? escapeHtml(p.artista)
      : '<span class="queue-td-empty">—</span>';
    return `<div class="queue-item-grid">
        <div class="queue-col-status">${renderStatusBadge(p)}</div>
        <div class="queue-col-musica">
          <span class="queue-field-label">Música:</span>
          <span class="queue-field-value">${escapeHtml(p.musica)}</span>
        </div>
        <div class="queue-col-artista">
          <span class="queue-field-label">Artista:</span>
          <span class="queue-field-value">${artistaVal}</span>
        </div>
        <div class="queue-col-por">
          <span class="queue-field-label">Pedido por:</span>
          <span class="queue-field-value">${escapeHtml(p.pedido_por)}</span>
        </div>
      </div>
      ${renderQueueItemNotes(p)}`;
  }

  function respostaInputDoPedido(formEl) {
    const wrap = formEl && formEl.closest(".queue-equipe-actions");
    return wrap ? wrap.querySelector(".queue-resposta-input") : null;
  }

  function motivoSelectDoPedido(formEl) {
    const wrap = formEl && formEl.closest(".queue-equipe-actions");
    return wrap ? wrap.querySelector(".queue-motivo-select") : null;
  }

  function motivosRejeicaoOpcoes() {
    if (!queuePanel) {
      return [];
    }
    try {
      const raw = queuePanel.dataset.motivosRejeicao || "[]";
      const list = JSON.parse(raw);
      return Array.isArray(list) ? list : [];
    } catch (_) {
      return [];
    }
  }

  function renderMotivoSelectHtml(pedidoId) {
    const options = motivosRejeicaoOpcoes()
      .map(
        (m) =>
          `<option value="${escapeHtml(String(m.id))}">${escapeHtml(m.nome)}</option>`
      )
      .join("");
    return `<label class="visually-hidden" for="motivo-js-${pedidoId}">Motivo da rejeição</label>
      <select id="motivo-js-${pedidoId}" class="form-input form-input--sm queue-motivo-select">
        <option value="">Motivo da rejeição</option>
        ${options}
      </select>`;
  }

  function renderEquipeActionsHtml(p) {
    const token = getCsrfToken();
    return `<div class="queue-equipe-actions">
      ${renderMotivoSelectHtml(p.id)}
      <label class="visually-hidden" for="resp-js-${p.id}">Resposta da mesa</label>
      <input type="text" id="resp-js-${p.id}" class="form-input form-input--sm queue-resposta-input" placeholder="Resposta da mesa (opcional)" maxlength="300">
      <div class="queue-equipe-buttons">
        <form method="post" action="${marcarPedidoUrl(p.id)}" class="marcar-tocado-form">
          <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(token)}">
          <button type="submit" class="queue-btn queue-btn--tocada" title="Marcar como tocada">Tocada</button>
        </form>
        <form method="post" action="${rejeitarPedidoUrl(p.id)}" class="rejeitar-pedido-form">
          <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(token)}">
          <button type="submit" class="queue-btn queue-btn--rejeitada" title="Rejeitar pedido">Rejeitada</button>
        </form>
      </div>
    </div>`;
  }

  function renderQueueActionHtml(p, equipe) {
    if (isTocado(p)) {
      return '<span class="queue-status ok" aria-label="Já tocada">✓</span>';
    }
    if (isRejeitado(p)) {
      return '<span class="queue-status rejected" aria-label="Pedido rejeitado">✕</span>';
    }
    if (equipe) {
      return renderEquipeActionsHtml(p);
    }
    return '<span class="queue-status wait" aria-label="Na fila">♪</span>';
  }

  function renderQueueItemHtml(p, equipe) {
    const classes = ["queue-item"];
    if (isTocado(p)) {
      classes.push("queue-item--done");
    } else if (isRejeitado(p)) {
      classes.push("queue-item--rejected");
    } else if (equipe) {
      classes.push("queue-item--equipe");
    }
    return `<li class="${classes.join(" ")}" data-id="${escapeHtml(String(p.id))}" data-tocado="${isTocado(p) ? "1" : "0"}" data-rejeitado="${isRejeitado(p) ? "1" : "0"}">
      <div class="queue-item-body">${renderQueueBodyHtml(p)}</div>
      <div class="queue-item-action">${renderQueueActionHtml(p, equipe)}</div>
    </li>`;
  }

  function formularioFilaEmEdicao(target) {
    return (
      target &&
      target.closest(
        ".marcar-tocado-form, .rejeitar-pedido-form, .queue-equipe-actions .queue-resposta-input, .queue-equipe-actions .queue-motivo-select"
      )
    );
  }

  function sincronizarRespostaNoForm(formEl) {
    const input = respostaInputDoPedido(formEl);
    if (input) {
      let hidden = formEl.querySelector('input[name="observacao_equipe"]');
      if (!hidden) {
        hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "observacao_equipe";
        formEl.appendChild(hidden);
      }
      hidden.value = input.value;
    }

    const motivo = motivoSelectDoPedido(formEl);
    if (motivo) {
      let hiddenMotivo = formEl.querySelector('input[name="motivo_rejeicao"]');
      if (!hiddenMotivo) {
        hiddenMotivo = document.createElement("input");
        hiddenMotivo.type = "hidden";
        hiddenMotivo.name = "motivo_rejeicao";
        formEl.appendChild(hiddenMotivo);
      }
      hiddenMotivo.value = motivo.value;
    }
  }

  async function enviarFormularioFila(formEl) {
    sincronizarRespostaNoForm(formEl);
    const formData = new FormData(formEl);
    const res = await fetch(formEl.action, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
      cache: "no-store",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const contentType = res.headers.get("Content-Type") || "";
    if (!res.ok) {
      if (contentType.includes("application/json")) {
        const data = await res.json();
        const msg =
          data.errors?.motivo_rejeicao?.[0] ||
          data.errors?.observacao_equipe?.[0] ||
          data.error ||
          "Não foi possível concluir a ação.";
        const motivo = motivoSelectDoPedido(formEl);
        const input = respostaInputDoPedido(formEl);
        const alvo =
          data.errors?.motivo_rejeicao && motivo
            ? motivo
            : input || motivo;
        if (alvo) {
          alvo.setCustomValidity(msg);
          alvo.reportValidity();
        } else {
          window.alert(msg);
        }
        return;
      }
      formEl.submit();
      return;
    }
    if (contentType.includes("application/json")) {
      const data = await res.json();
      if (data.ok) {
        refreshPaused = false;
        await refreshQueue();
        return;
      }
    }
    refreshPaused = false;
    await refreshQueue();
  }

  function atualizarFila(pedidos) {
    if (!queueList || !Array.isArray(pedidos)) return;

    const equipe = equipeAtiva();
    const scrollTop = queueList.scrollTop;

    if (!pedidos.length) {
      queueList.innerHTML =
        '<li class="queue-empty" id="queue-empty">A fila está vazia — seja o primeiro!</li>';
      return;
    }

    queueList.innerHTML = pedidos.map((p) => renderQueueItemHtml(p, equipe)).join("");
    queueList.scrollTop = scrollTop;
  }

  function valorCampo(data, ...keys) {
    for (const key of keys) {
      if (data && data[key] !== undefined) return data[key];
    }
    return undefined;
  }

  function eVerdade(valor) {
    return valor === true || valor === 1 || valor === "1";
  }

  function aplicarLimiteFila(data) {
    const aviso = document.getElementById("pedido-fila-aviso");
    const avisoProprio = document.getElementById("pedido-proprio-aviso");
    const resumo = document.getElementById("pedido-fila-resumo");
    if (!form) return;

    const limiteVal = valorCampo(data, "limite_em_fila", "limite_em_fila");
    const totalVal = valorCampo(data, "total_em_fila", "total_em_fila");
    const limite =
      limiteVal !== undefined
        ? Number(limiteVal)
        : Number(form.dataset.limiteEmFila || 0);
    const total =
      totalVal !== undefined
        ? Number(totalVal)
        : Number(document.getElementById("pedido-fila-total")?.textContent || 0);
    const cheiaFlag = valorCampo(data, "fila_cheia", "fila_cheia");
    const cheia =
      eVerdade(cheiaFlag) ||
      (cheiaFlag === undefined && limite > 0 && total >= limite);

    const temPedidoFlag = valorCampo(
      data,
      "ja_tem_pedido_em_fila",
      "ja_tem_pedido_em_fila"
    );
    const temPedido =
      temPedidoFlag !== undefined
        ? eVerdade(temPedidoFlag)
        : form.dataset.jaTemPedido === "1";

    form.dataset.filaCheia = cheia ? "1" : "0";
    form.dataset.jaTemPedido = temPedido ? "1" : "0";
    const bloqueado = cheia || temPedido;
    form.classList.toggle("pedido-form--bloqueado", bloqueado);
    if (resumo) {
      resumo.classList.toggle("pedido-fila-resumo--cheia", cheia);
    }

    const fieldset = form.querySelector(".pedido-form-fieldset");
    const btn = form.querySelector('button[type="submit"]');
    if (fieldset) fieldset.disabled = bloqueado;
    if (btn) btn.disabled = bloqueado;

    const totalEl = document.getElementById("pedido-fila-total");
    const limiteEl = document.getElementById("pedido-fila-limite");
    if (totalEl) totalEl.textContent = String(total);
    if (limiteEl) limiteEl.textContent = String(limite);
    if (aviso) {
      aviso.hidden = !cheia;
    }
    if (avisoProprio) {
      avisoProprio.hidden = !temPedido;
      const pedidoAtivo = valorCampo(data, "pedido_ativo", "pedido_ativo");
      const musica = pedidoAtivo && pedidoAtivo.musica;
      const musicaEl = document.getElementById("pedido-ativo-musica");
      const wrap = document.getElementById("pedido-ativo-musica-wrap");
      if (musica && musicaEl) {
        musicaEl.textContent = musica;
        if (wrap) wrap.hidden = false;
      } else if (!temPedido && wrap) {
        wrap.hidden = true;
      }
    }
  }

  function aplicarStatsAdmin(data) {
    const stats = valorCampo(data, "stats_admin");
    const wrap = document.getElementById("equipe-stats");
    if (!wrap || !stats) return;

    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = String(value);
    };
    const setWidth = (id, pct) => {
      const el = document.getElementById(id);
      if (el) el.style.width = `${Number(pct) || 0}%`;
    };

    setText("stat-clientes", stats.total_clientes);
    setText("stat-pedidos", stats.total_pedidos);
    setText("stat-tocados", stats.pedidos_tocados);
    setText("stat-rejeitados", stats.pedidos_rejeitados);
    setText("stat-percentual", `${stats.percentual_tocados}%`);

    const hint = document.getElementById("stat-percentual-hint");
    if (hint) {
      hint.textContent = `${stats.percentual_tocados}% tocados · ${stats.percentual_rejeitados}% rejeitados`;
    }

    setWidth("stat-bar-tocados", stats.percentual_tocados);
    setWidth("stat-bar-rejeitados", stats.percentual_rejeitados);
    setWidth("stat-bar-fila", stats.percentual_em_fila);
  }

  async function refreshQueue() {
    if (!form || refreshPaused || !queueList) return;
    const url = form.dataset.filaUrl;
    if (!url) return;

    try {
      const res = await fetchFila(url);
      const contentType = res.headers.get("Content-Type") || "";
      if (!res.ok || !contentType.includes("application/json")) {
        return;
      }
      const data = await res.json();
      const pedidos = valorCampo(data, "pedidos", "pedidos");
      if (!Array.isArray(pedidos)) {
        return;
      }
      const podeMarcar = valorCampo(data, "pode_marcar", "pode_marcar");
      if (queuePanel && podeMarcar !== undefined) {
        queuePanel.dataset.podeMarcar = eVerdade(podeMarcar) ? "1" : "0";
      }
      aplicarLimiteFila(data);
      aplicarStatsAdmin(data);
      atualizarFila(pedidos);
    } catch (_) {
      /* ignore polling errors */
    }
  }

  if (queueList) {
    queueList.addEventListener(
      "focusin",
      (e) => {
        if (
          e.target.closest(".queue-resposta-input") ||
          e.target.closest(".queue-motivo-select")
        ) {
          refreshPaused = true;
        }
      },
      true
    );
    queueList.addEventListener(
      "focusout",
      (e) => {
        if (formularioFilaEmEdicao(e.target)) {
          window.setTimeout(() => {
            refreshPaused = false;
          }, 200);
        }
      },
      true
    );

    queueList.addEventListener("submit", async (e) => {
      const formEl = e.target.closest(".marcar-tocado-form, .rejeitar-pedido-form");
      if (!formEl) return;
      e.preventDefault();
      const obs = respostaInputDoPedido(formEl);
      const motivo = motivoSelectDoPedido(formEl);
      if (formEl.classList.contains("rejeitar-pedido-form")) {
        if (motivo) {
          motivo.setCustomValidity("");
        }
        if (obs) {
          obs.setCustomValidity("");
        }
        if (!motivo || !motivo.value) {
          if (motivo) {
            motivo.setCustomValidity("Seleccione o motivo da rejeição.");
            motivo.reportValidity();
          }
          return;
        }
      } else {
        if (motivo) {
          motivo.setCustomValidity("");
        }
        if (obs) {
          obs.setCustomValidity("");
        }
      }
      try {
        await enviarFormularioFila(formEl);
      } catch (_) {
        sincronizarRespostaNoForm(formEl);
        formEl.submit();
      }
    });
  }

  if (form) {
    aplicarLimiteFila({
      limite_em_fila: form.dataset.limiteEmFila,
      total_em_fila: document.getElementById("pedido-fila-total")?.textContent,
      fila_cheia: form.dataset.filaCheia === "1",
      ja_tem_pedido_em_fila: form.dataset.jaTemPedido === "1",
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (form.dataset.jaTemPedido === "1") {
        if (feedback) {
          feedback.textContent =
            "Já tem um pedido na fila. Aguarde a roda tocar ou a mesa tratar esse pedido.";
          feedback.classList.add("error");
        }
        return;
      }
      if (form.dataset.filaCheia === "1") {
        if (feedback) {
          feedback.textContent =
            "A fila está cheia. Aguarde a roda tocar mais músicas.";
          feedback.classList.add("error");
        }
        return;
      }
      if (feedback) {
        feedback.textContent = "";
        feedback.className = "form-hint";
      }

      const formData = new FormData(form);
      try {
        const res = await fetch(form.action, {
          method: "POST",
          body: formData,
          credentials: "same-origin",
          cache: "no-store",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        });
        const data = await res.json();
        if (data.ok) {
          if (feedback) {
            feedback.textContent = "Pedido enviado! A roda vai considerar a sua música.";
            feedback.classList.add("success");
          }
          form.reset();
          await refreshQueue();
        } else if (data.ja_tem_pedido_em_fila || data.ja_tem_pedido_em_fila) {
          aplicarLimiteFila(data);
          if (feedback) {
            feedback.textContent =
              data.error ||
              "Já tem um pedido na fila. Aguarde a roda tocar ou a mesa tratar esse pedido.";
            feedback.classList.add("error");
          }
        } else if (data.fila_cheia || data.fila_cheia) {
          aplicarLimiteFila(data);
          if (feedback) {
            feedback.textContent =
              data.error || "A fila está cheia. Aguarde mais músicas serem tocadas.";
            feedback.classList.add("error");
          }
        } else if (feedback) {
          feedback.textContent = data.error || "Verifique os campos e tente novamente.";
          feedback.classList.add("error");
        }
      } catch (_) {
        if (feedback) {
          feedback.textContent = "Erro ao enviar. Tente novamente.";
          feedback.classList.add("error");
        }
      }
    });

    setInterval(refreshQueue, 12000);
  }

  function focusHashField() {
    const id = decodeURIComponent((window.location.hash || "").replace(/^#/, ""));
    if (!id) return;
    const field = document.getElementById(id);
    if (!field || !field.matches("input, textarea, select")) return;
    const focus = () => field.focus({ preventScroll: false });
    focus();
    window.setTimeout(focus, 300);
  }

  focusHashField();
  window.addEventListener("hashchange", focusHashField);
  window.addEventListener("pageshow", focusHashField);

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {});
    });
  }
})();
