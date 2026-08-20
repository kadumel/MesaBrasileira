---
name: mesa-brasileira-design
description: >
  Cria interfaces, componentes e animações para o site
  Mesa Brasileira, projeto de samba de rua em Lisboa.
---

# Mesa Brasileira UI Design

Quando criar interfaces para o projeto Mesa Brasileira:

## Identidade

O site representa:
- samba de rua
- roda de samba
- comunidade
- música brasileira
- Lisboa
- encontro entre pessoas

A interface deve transmitir:
- movimento
- calor humano
- música
- espontaneidade
- elegância contemporânea

Evitar aparência:
- corporativa
- SaaS
- dashboard
- Bootstrap genérico
- template pronto

## Tecnologias

Priorizar:

- Django Templates
- HTML5
- CSS moderno
- JavaScript vanilla
- GSAP para animações complexas

Evitar React quando não houver necessidade.

## Hero

O hero principal deve funcionar como uma roda de samba visual.

Usar instrumentos como elementos gráficos:
- banjo
- cavaquinho
- pandeiro
- tantan
- surdo
- reco-reco

Criar movimento orgânico e discreto.

## Animações

Usar:
- stagger
- parallax suave
- scroll animations
- microinterações
- entrada sequencial dos instrumentos

Sempre respeitar:

prefers-reduced-motion.

## Responsividade

Projetar primeiro considerando:

desktop
tablet
mobile

Não esconder funcionalidades importantes no mobile.

## Django

Separar:

HTML:
templates/

CSS:
static/css/

JavaScript:
static/js/

Imagens:
static/images/

Nunca colocar grandes blocos CSS ou JS inline nos templates.

## Qualidade

Antes de finalizar:

- verificar responsividade
- verificar acessibilidade
- verificar console JS
- testar links
- verificar CLS
- evitar animações pesadas
