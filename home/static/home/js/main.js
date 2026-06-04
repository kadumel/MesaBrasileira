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
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach((el) => observer.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("visible"));
  }

  if (typeof Swiper !== "undefined" && document.querySelector(".banner-swiper")) {
    new Swiper(".banner-swiper", {
      slidesPerView: 1,
      loop: true,
      speed: 600,
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

  function renderQueueItemNotes(p) {
    let html = "";
    if (p.mensagem) {
      html += `<p class="queue-item-note queue-item-note--public"><span class="queue-item-note-label">Mensagem:</span> ${escapeHtml(p.mensagem)}</p>`;
    }
    if (p.observacao_equipe) {
      html += `<p class="queue-item-note queue-item-note--resposta" role="status"><span class="queue-item-note-label">Resposta da mesa:</span> ${escapeHtml(p.observacao_equipe)}</p>`;
    }
    if (isTocado(p) && p.marcado_por_exibir) {
      html += `<p class="queue-item-note queue-item-note--marcador"><span class="queue-item-note-label">Marcado por:</span> ${escapeHtml(p.marcado_por_exibir)}</p>`;
    }
    return html;
  }

  function renderStatusBadge(p) {
    if (isTocado(p)) {
      return '<span class="badge badge-queue badge-queue--tocada">Já tocada</span>';
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

  function renderMarcarFormHtml(p) {
    const token = getCsrfToken();
    return `<form method="post" action="${marcarPedidoUrl(p.id)}" class="marcar-tocado-form">
      <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(token)}">
      <label class="visually-hidden" for="obs-js-${p.id}">Observação (opcional)</label>
      <input type="text" id="obs-js-${p.id}" name="observacao_equipe" class="form-input form-input--sm" placeholder="Resposta visível na fila (opcional)" maxlength="300">
      <button type="submit" class="btn btn-xs btn-primary" title="Marcar como tocada">Tocada</button>
    </form>`;
  }

  function renderQueueActionHtml(p, equipe) {
    const done = isTocado(p);
    if (done) {
      return '<span class="queue-status ok" aria-label="Já tocada">✓</span>';
    }
    if (equipe) {
      return renderMarcarFormHtml(p);
    }
    return '<span class="queue-status wait" aria-label="Na fila">♪</span>';
  }

  function renderQueueItemHtml(p, equipe) {
    const done = isTocado(p);
    const classes = ["queue-item"];
    if (done) {
      classes.push("queue-item--done");
    } else if (equipe) {
      classes.push("queue-item--equipe");
    }
    return `<li class="${classes.join(" ")}" data-id="${escapeHtml(String(p.id))}" data-tocado="${done ? "1" : "0"}">
      <div class="queue-item-body">${renderQueueBodyHtml(p)}</div>
      <div class="queue-item-action">${renderQueueActionHtml(p, equipe)}</div>
    </li>`;
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

  function aplicarLimiteFila(data) {
    const aviso = document.getElementById("pedido-fila-aviso");
    const resumo = document.getElementById("pedido-fila-resumo");
    if (!form) return;

    const limite =
      data.limite_em_fila !== undefined
        ? Number(data.limite_em_fila)
        : Number(form.dataset.limiteEmFila || 0);
    const total =
      data.total_em_fila !== undefined
        ? Number(data.total_em_fila)
        : Number(document.getElementById("pedido-fila-total")?.textContent || 0);
    const cheia =
      data.fila_cheia === true ||
      data.fila_cheia === 1 ||
      data.fila_cheia === "1" ||
      (limite > 0 && total >= limite);

    form.dataset.filaCheia = cheia ? "1" : "0";
    form.classList.toggle("pedido-form--bloqueado", cheia);
    if (resumo) {
      resumo.classList.toggle("pedido-fila-resumo--cheia", cheia);
    }

    const fieldset = form.querySelector(".pedido-form-fieldset");
    const btn = form.querySelector('button[type="submit"]');
    if (fieldset) fieldset.disabled = cheia;
    if (btn) btn.disabled = cheia;

    const totalEl = document.getElementById("pedido-fila-total");
    const limiteEl = document.getElementById("pedido-fila-limite");
    if (totalEl) totalEl.textContent = String(total);
    if (limiteEl) limiteEl.textContent = String(limite);
    if (aviso) {
      aviso.hidden = !cheia;
    }
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
      if (!Array.isArray(data.pedidos)) {
        return;
      }
      if (queuePanel && data.pode_marcar !== undefined) {
        queuePanel.dataset.podeMarcar = data.pode_marcar ? "1" : "0";
      }
      aplicarLimiteFila(data);
      atualizarFila(data.pedidos);
    } catch (_) {
      /* ignore polling errors */
    }
  }

  if (queueList) {
    queueList.addEventListener(
      "focusin",
      (e) => {
        if (e.target.closest(".marcar-tocado-form input, .marcar-tocado-form textarea")) {
          refreshPaused = true;
        }
      },
      true
    );
    queueList.addEventListener(
      "focusout",
      (e) => {
        if (e.target.closest(".marcar-tocado-form")) {
          window.setTimeout(() => {
            refreshPaused = false;
          }, 200);
        }
      },
      true
    );

    queueList.addEventListener("submit", async (e) => {
      const formEl = e.target.closest(".marcar-tocado-form");
      if (!formEl) return;
      e.preventDefault();
      const li = formEl.closest(".queue-item");
      const formData = new FormData(formEl);
      try {
        const res = await fetch(formEl.action, {
          method: "POST",
          body: formData,
          credentials: "same-origin",
          cache: "no-store",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        const contentType = res.headers.get("Content-Type") || "";
        if (!res.ok) {
          formEl.submit();
          return;
        }
        if (contentType.includes("application/json")) {
          const data = await res.json();
          if (data.ok && data.pedido) {
            refreshPaused = false;
            await refreshQueue();
            return;
          }
        }
        refreshPaused = false;
        await refreshQueue();
      } catch (_) {
        formEl.submit();
      }
    });
  }

  if (form) {
    aplicarLimiteFila({
      limite_em_fila: form.dataset.limiteEmFila,
      total_em_fila: document.getElementById("pedido-fila-total")?.textContent,
      fila_cheia: form.dataset.filaCheia === "1",
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
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
        } else if (data.fila_cheia) {
          aplicarLimiteFila(data);
          if (feedback) {
            feedback.textContent =
              data.error || "A fila está cheia. Aguarde mais músicas serem tocadas.";
            feedback.classList.add("error");
          }
        } else if (feedback) {
          feedback.textContent = "Verifique os campos e tente novamente.";
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
})();
