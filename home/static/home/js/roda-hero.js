(function () {
  "use strict";

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

  function markReady() {
    hero.classList.add("is-animated");
  }

  if (reduceMotion || typeof gsap === "undefined") {
    markReady();
    return;
  }

  if (typeof ScrollTrigger !== "undefined") {
    gsap.registerPlugin(ScrollTrigger);
  }

  const sorted = items
    .slice()
    .sort((a, b) => Number(a.dataset.order || 0) - Number(b.dataset.order || 0));

  const motions = sorted.map((el) => el.querySelector(".roda-item-motion"));

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

  function startIdle() {
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
  }

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

  gsap.set(motions, { opacity: 0 });
  gsap.set([mesa, logo, rings, copy], { opacity: 0 });
  markReady();

  const tl = gsap.timeline({
    defaults: { ease: "power3.out" },
    onComplete: function () {
      startIdle();
      startParallax();
      startScroll();
    },
  });

  tl.fromTo(
    mesa,
    { opacity: 0, scale: 0.82 },
    { opacity: 1, scale: 1, duration: 0.8 },
    0
  )
    .fromTo(
      logo,
      { opacity: 0, scale: 0.72 },
      { opacity: 1, scale: 1, duration: 0.7 },
      0.18
    )
    .fromTo(
      rings,
      { opacity: 0 },
      { opacity: 1, duration: 0.8 },
      0.1
    )
    .fromTo(
      copy,
      { opacity: 0, y: 18 },
      { opacity: 1, y: 0, duration: 0.65 },
      0.28
    );

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
      0.55 + i * 0.16
    );
  });
})();
