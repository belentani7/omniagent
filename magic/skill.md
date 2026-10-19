---
name: belentani-magic
description: Create or refine an optional BELENTANI creative layer—visual atmosphere, WebGL, procedural audio, lore, or a local agent plugin—when the user explicitly asks for it. Keep each effect purposeful and the underlying product fully functional.
---

# BELENTANI Magic Skill

Use this skill only when a creative layer is requested or clearly fits the product. It must complement working software, not disguise missing functionality.

## Choose deliverables by purpose

The `magic/` directory may include any relevant subset of:

- `shader.html` — a self-contained WebGL study.
- `sfx.html` — procedural sound via WebAudio.
- `immersive.html` — a coherent visual/audio experience.
- `lore.md` — world-building for a creative project.
- `ai-instructions.md` — accurate, project-specific agent guidance.
- `plugin.js` — a plugin only when the host runtime supports it.
- `README.md` — explain which files are optional and how to open them.

Do not generate every item by default. Do not require 3D, animation, audio, or lore for a business product.

## Rules

- Preserve the real product workflow and test it after visual changes.
- Never present a static mock, unimplemented control, or invented metric as a working feature.
- Keep effects lightweight, accessible, and self-contained unless a dependency is justified.
- Avoid shell interpolation and never embed credentials, prompts, or personal data.
- Use the `belentani.eu / noiacore.com` signature only as part of this optional creative layer.

## Verification

- Check JavaScript syntax and inspect the page at narrow and wide viewports.
- Respect reduced-motion preferences and provide usable controls for sound.
- Confirm the underlying application still builds and its tests pass.
- Disclose any browser or external service behavior that was not tested.
