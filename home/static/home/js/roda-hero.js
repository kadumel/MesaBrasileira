(function () {
  "use strict";

  const CYCLE_MS = 15000;
  const hero = document.querySelector("[data-roda-hero]");
  if (!hero) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const stage = hero.querySelector("[data-roda-stage]");
  const orbit = hero.querySelector("[data-roda-orbit]");
  const mesa = hero.querySelector("[data-roda-mesa]");
  const logo = hero.querySelector("[data-roda-logo]");
  const rings = hero.querySelector("[data-roda-rings]");
  const copy = hero.querySelector("[data-roda-center]");
  const items = Array.from(hero.querySelectorAll("[data-roda-item]"));
  const sambistaItems = items.filter((el) => el.dataset.kind === "sambista");
  const publicoFaces = Array.from(hero.querySelectorAll("[data-roda-publico-face]"));
  const pool = readPool();

  function readPool() {
    const node = document.getElementById("roda-sambista-pool");
    if (!node) return [];
    try {
      const data = JSON.parse(node.textContent);
      return Array.isArray(data) ? data : [];
    } catch (_) {
      return [];
    }
  }

  function srcKey(url) {
    try {
      return new URL(url, window.location.origin).pathname;
    } catch (_) {
      return url;
    }
  }

  function shuffle(list) {
    const copy = list.slice();
    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = copy[i];
      copy[i] = copy[j];
      copy[j] = tmp;
    }
    return copy;
  }

  function currentSambistaKeys() {
    return sambistaItems
      .map((el) => {
        const img = el.querySelector("img");
        return img ? srcKey(img.getAttribute("src") || img.src) : "";
      })
      .filter(Boolean);
  }

  function pickSambistas(count) {
    if (pool.length < count) return pool.slice();
    const excluded = new Set(currentSambistaKeys());
    let bag = pool.filter((artist) => !excluded.has(srcKey(artist.src)));
    if (bag.length < count) bag = pool.slice();
    return shuffle(bag).slice(0, count);
  }

  function preload(artists) {
    artists.forEach((artist) => {
      if (!artist || !artist.src) return;
      const image = new Image();
      image.src = artist.src;
    });
  }

  function applySambistas(artists) {
    sambistaItems.forEach((el, i) => {
      const artist = artists[i];
      if (!artist) return;
      const img = el.querySelector("img");
      const caption = el.querySelector(".roda-item-caption");
      const link = el.querySelector(".roda-item-link");
      const tip = el.querySelector(".roda-item-tip");
      if (img) {
        img.src = artist.src;
        img.alt = artist.alt || "";
      }
      if (caption) caption.textContent = artist.caption || "";
      if (link) {
        const pageName = (tip && tip.textContent) || "";
        const name = artist.caption || pageName;
        link.setAttribute("aria-label", `${name} — ir para ${pageName.trim()}`);
      }
      el.classList.remove("roda-item--grupo", "roda-item--retrato");
      if (artist.extraClass) el.classList.add(artist.extraClass);
    });
  }

  function shufflePublico() {
    if (publicoFaces.length < 2) return;
    const images = publicoFaces.map((face) => face.querySelector("img"));
    const sources = images.map((img) => img && img.getAttribute("src")).filter(Boolean);
    const shuffled = shuffle(sources);
    images.forEach((img, i) => {
      if (img && shuffled[i]) img.setAttribute("src", shuffled[i]);
    });
  }

  shufflePublico();

  function markReady() {
    hero.classList.add("is-animated");
  }

  if (reduceMotion || typeof gsap === "undefined") {
    markReady();
    if (!reduceMotion) return;

    let nextPick = pickSambistas(sambistaItems.length);
    preload(nextPick);
    window.setInterval(() => {
      if (document.hidden) return;
      const pick = nextPick.length ? nextPick : pickSambistas(sambistaItems.length);
      applySambistas(pick);
      shufflePublico();
      nextPick = pickSambistas(sambistaItems.length);
      preload(nextPick);
    }, CYCLE_MS);
    return;
  }

  if (typeof ScrollTrigger !== "undefined") {
    gsap.registerPlugin(ScrollTrigger);
  }

  const sorted = items
    .slice()
    .sort((a, b) => Number(a.dataset.order || 0) - Number(b.dataset.order || 0));

  const motions = sorted.map((el) => el.querySelector(".roda-item-motion"));
  const publicoMotions = publicoFaces
    .map((face) => face.querySelector(".roda-publico-motion"))
    .filter(Boolean);

  function radialFrom(el) {
    const node = el.querySelector(".roda-item-slot") || el;
    const s = stage.getBoundingClientRect();
    const r = node.getBoundingClientRect();
    const cx = s.left + s.width / 2;
    const cy = s.top + s.height / 2;
    const ix = r.left + r.width / 2;
    const iy = r.top + r.height / 2;
    return {
      x: (ix - cx) * 0.78,
      y: (iy - cy) * 0.78,
    };
  }

  function killIdle() {
    motions.forEach((motion) => {
      if (motion) gsap.killTweensOf(motion);
    });
    publicoMotions.forEach((motion) => gsap.killTweensOf(motion));
  }

  function startIdle() {
    killIdle();
    motions.forEach((motion, i) => {
      if (!motion) return;
      const person = sorted[i] && sorted[i].dataset.kind === "sambista";
      gsap.to(motion, {
        y: person ? (i % 2 ? 8 : -6) : i % 2 ? 5 : -4,
        rotate: person ? 0 : i % 2 ? 1.2 : -1,
        duration: 2.8 + i * 0.18,
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut",
        delay: i * 0.12,
      });
    });

    publicoMotions.forEach((motion, i) => {
      gsap.to(motion, {
        y: i % 2 ? 7 : -5,
        duration: 3.2 + i * 0.2,
        yoyo: true,
        repeat: -1,
        ease: "sine.inOut",
        delay: i * 0.16,
      });
    });
  }

  let extrasStarted = false;

  function startParallax() {
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    if (!finePointer || !stage) return;

    const parallaxTargets = items
      .map((el) => ({
        node: el.querySelector(".roda-item-parallax"),
        depth: Number(el.dataset.depth || 0.3),
      }))
      .filter((item) => item.node);

    let frame = 0;
    let targetX = 0;
    let targetY = 0;

    function applyParallax() {
      frame = 0;
      parallaxTargets.forEach(({ node, depth }) => {
        gsap.to(node, {
          x: targetX * 52 * depth,
          y: targetY * 34 * depth,
          duration: 0.65,
          ease: "power2.out",
          overwrite: "auto",
        });
      });
    }

    stage.addEventListener(
      "mousemove",
      (event) => {
        const rect = stage.getBoundingClientRect();
        targetX = (event.clientX - rect.left) / rect.width - 0.5;
        targetY = (event.clientY - rect.top) / rect.height - 0.5;
        if (!frame) {
          frame = requestAnimationFrame(applyParallax);
        }
      },
      { passive: true }
    );

    stage.addEventListener("mouseleave", () => {
      targetX = 0;
      targetY = 0;
      if (!frame) {
        frame = requestAnimationFrame(applyParallax);
      }
    });
  }

  function startScroll() {
    if (typeof ScrollTrigger === "undefined") return;

    gsap.to(orbit, {
      rotate: 12,
      y: 36,
      ease: "none",
      scrollTrigger: {
        trigger: hero,
        start: "top top",
        end: "bottom top",
        scrub: 0.75,
      },
    });

    gsap.to(rings, {
      rotate: -8,
      ease: "none",
      scrollTrigger: {
        trigger: hero,
        start: "top top",
        end: "bottom top",
        scrub: 0.9,
      },
    });

    gsap.to(copy, {
      y: -24,
      ease: "none",
      scrollTrigger: {
        trigger: hero,
        start: "top top",
        end: "80% top",
        scrub: 0.6,
      },
    });

    gsap.to([mesa, logo], {
      y: -28,
      scale: 0.94,
      ease: "none",
      scrollTrigger: {
        trigger: hero,
        start: "top top",
        end: "bottom top",
        scrub: 0.65,
      },
    });
  }

  function startExtrasOnce() {
    if (extrasStarted) return;
    extrasStarted = true;
    startParallax();
    startScroll();
  }

  let introTl;

  function playItemsIntro() {
    if (introTl) introTl.kill();
    killIdle();

    const tl = gsap.timeline({
      defaults: { ease: "power3.out" },
      onComplete: startIdle,
    });
    introTl = tl;

    sorted.forEach((el, i) => {
      const motion = motions[i];
      if (!motion) return;
      const from = radialFrom(el);
      const person = el.dataset.kind === "sambista";
      const stretch = person ? 1.28 : 1;
      tl.fromTo(
        motion,
        {
          opacity: 0,
          x: from.x * stretch,
          y: from.y * stretch + (person ? 28 : 0),
          rotate: person ? 0 : i % 2 === 0 ? -14 : 14,
          scale: person ? 0.86 : 1,
        },
        {
          opacity: 1,
          x: 0,
          y: 0,
          rotate: 0,
          scale: 1,
          duration: person ? 0.95 : 0.82,
          ease: person ? "power3.out" : "back.out(1.08)",
        },
        0.08 + i * 0.16
      );
    });

    publicoFaces.forEach((face, i) => {
      const motion = face.querySelector(".roda-publico-motion");
      if (!motion) return;
      const fromLeft = face.closest("[data-roda-publico]")?.dataset.rodaPublico === "left";
      tl.fromTo(
        motion,
        {
          opacity: 0,
          x: fromLeft ? -46 : 46,
          y: 18,
          scale: 0.86,
        },
        {
          opacity: 1,
          x: 0,
          y: 0,
          scale: 1,
          duration: 0.75,
          ease: "power3.out",
        },
        0.04 + i * 0.08
      );
    });
  }

  gsap.set(motions, { opacity: 0 });
  gsap.set(publicoMotions, { opacity: 0 });
  gsap.set([mesa, logo, rings, copy], { opacity: 0 });
  markReady();

  const openingTl = gsap.timeline({
    defaults: { ease: "power3.out" },
    onComplete: function () {
      startIdle();
      startExtrasOnce();
    },
  });

  openingTl
    .fromTo(mesa, { opacity: 0, scale: 0.82 }, { opacity: 1, scale: 1, duration: 0.8 }, 0)
    .fromTo(logo, { opacity: 0, scale: 0.72 }, { opacity: 1, scale: 1, duration: 0.7 }, 0.18)
    .fromTo(rings, { opacity: 0 }, { opacity: 1, duration: 0.8 }, 0.1)
    .fromTo(copy, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.65 }, 0.28);

  sorted.forEach((el, i) => {
    const motion = motions[i];
    if (!motion) return;
    const from = radialFrom(el);
    const person = el.dataset.kind === "sambista";
    const stretch = person ? 1.28 : 1;
    openingTl.fromTo(
      motion,
      {
        opacity: 0,
        x: from.x * stretch,
        y: from.y * stretch + (person ? 28 : 0),
        rotate: person ? 0 : i % 2 === 0 ? -14 : 14,
        scale: person ? 0.86 : 1,
      },
      {
        opacity: 1,
        x: 0,
        y: 0,
        rotate: 0,
        scale: 1,
        duration: person ? 0.95 : 0.82,
        ease: person ? "power3.out" : "back.out(1.08)",
      },
      0.55 + i * 0.16
    );
  });

  publicoFaces.forEach((face, i) => {
    const motion = face.querySelector(".roda-publico-motion");
    if (!motion) return;
    const fromLeft = face.closest("[data-roda-publico]")?.dataset.rodaPublico === "left";
    openingTl.fromTo(
      motion,
      {
        opacity: 0,
        x: fromLeft ? -46 : 46,
        y: 18,
        scale: 0.86,
      },
      {
        opacity: 1,
        x: 0,
        y: 0,
        scale: 1,
        duration: 0.75,
        ease: "power3.out",
      },
      0.42 + i * 0.08
    );
  });

  let heroVisible = true;
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        heroVisible = entries.some((entry) => entry.isIntersecting);
      },
      { threshold: 0.32 }
    );
    observer.observe(hero);
  }

  let nextPick = pickSambistas(sambistaItems.length);
  preload(nextPick);

  window.setInterval(() => {
    if (document.hidden || !heroVisible) return;
    if (openingTl.isActive()) return;

    killIdle();
    gsap.set(motions, { opacity: 0, x: 0, y: 0, rotate: 0, scale: 1 });
    gsap.set(publicoMotions, { opacity: 0, x: 0, y: 0, scale: 1 });

    const pick = nextPick.length ? nextPick : pickSambistas(sambistaItems.length);
    applySambistas(pick);
    shufflePublico();
    nextPick = pickSambistas(sambistaItems.length);
    preload(nextPick);
    playItemsIntro();
  }, CYCLE_MS);
})();
