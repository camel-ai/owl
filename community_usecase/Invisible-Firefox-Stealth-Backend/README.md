# Invisible Firefox Stealth Backend (proposal)

> Status: Draft proposal
> Created: 2026-05-27
> Tracking issue: TBD

## Goal

Optional Firefox-based stealth backend for `BrowserToolkit`, parallel to the default Chromium-via-Playwright path. Selected via an extra parameter, no change to defaults.

## Motivation

GAIA evaluation runs hit anti-bot walls on a growing share of target sites. Related issues:
- #544 GAIA 69 reproduction: anti-bot verification and MAX_TRY parameters
- #317 feature request: can owl fill in the captcha automatically?
- #427 infinite `scroll_down()` at the bottom of a page using BrowserToolkit

A Firefox build with fingerprint patches at the C++ source code level avoids the JS-shim detection surface that the standard playwright-stealth approach uses. The expected effect on GAIA is measurable: pages currently returning empty or 403 to the agent would render normally.

## Proposed change

Two options:

1. Add a `BrowserToolkit(backend="invisible_firefox", ...)` parameter that resolves to launching the patched binary instead of vanilla Chromium. This requires a corresponding addition in `camel-ai/camel` where `BrowserToolkit` lives.

2. Add an `examples/run_invisible_firefox.py` showing how to wire the existing `BrowserToolkit` to the patched binary via a small wrapper, without touching upstream `camel`.

Either path wraps `invisible_playwright` (https://github.com/feder-cr/invisible_playwright), which drives a patched Firefox 150 binary (https://github.com/feder-cr/invisible_firefox, MPL-2.0, same license as Firefox upstream).

## Out of scope

No change to the default `BrowserToolkit` behavior. No change to GAIA scoring scripts. Backend stays user-driven.

## Maintenance

Issues against the backend route to feder-cr/invisible_playwright. Only ask of this repo would be the example file or the small toolkit wrapper.

---

## 简介

可选的 Firefox 隐身后端，与默认的 Chromium Playwright 路径并行。通过参数选择，不影响默认行为。详细方案见上方英文部分。
