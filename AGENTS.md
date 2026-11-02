# Project hand-off instructions

## Current owner and scope

- Speak Persian with the owner. Keep progress reports short and truthful. The owner is concerned about elapsed time and network use: avoid redundant image uploads, polling, large dumps and repeated regeneration.
- The GitHub owner is `zuziai`; the owner completed GitHub and Git Credential Manager login and authorized this project transfer. The private repository is https://github.com/zuziai/excellent-advice-studio. Do not upload through another connected account or make the project public.
- Do not generate another wave or revise approved artwork merely because this folder was opened. First read the owner's current task and saved feedback.
- Current gallery wave: `wave-157-161-2026-10-19-v1-edits-9`. Read `wave.json` and saved feedback for exact pending/approved candidates; never infer approval from image readiness.
- Current final approvals: 151 = `151-o-v2`; 152 = `152-g-v5`; 153 = `153-g-v2`; 154 = `154-d-20261019-v2`; 155 = `155-b-20261019-v2`; 156 = `156-d-20261019-v2`; 157 = `157-d-20261019-v2`; 158 = `158-c-20261021-v2`; 161 = `161-a-20261021-v3`. Exact approved PNGs are in `Images/`; the ledger verifies their Excel prompts in column D.

## Data and run contract

- Run `python setup.py --check`; use the available Codex workspace dependency loader if runtimes are missing. `python setup.py` links local dependencies and performs no network installation. The review UI requires Python; the Excel writer additionally requires the Codex Node runtime and `@oai/artifact-tool`.
- Workbook: `Excellent-Advice-460-FA.xlsx`, worksheet `ترجمه‌ها`, 460 IDs in rows 2–461. A=ID, B=English sentence, C=Persian translation, D=complete English generation prompt. Find rows by ID rather than assuming order; 152 currently maps to D153.
- Use the spreadsheet skill and Artifact Tool for workbook authoring. Preserve all translations, native table, formats and RTL display. Do not use an edit-only instruction in place of a complete reusable generation prompt.
- `book-review/dist/wave.json` is the active gallery manifest. Images must load before publishing a wave. Use unique versioned candidate IDs and retain parent/request IDs.
- `review-data/feedback.json` holds the owner's decisions. `finalization-state.json` and `project-state.json` retain saved approvals and history. Only exact current explicit approvals may save artwork. Revised artwork always returns to pending review.
- Preserve histories and exact original image bytes. Keep saves hash-bound and idempotent. Surface failures; never report progress or completion that did not happen.

## Art direction

- Read `review-data/style-contract.md`, `style-study.md`, and `user-example-prompt-133.md`; later explicit owner corrections take precedence over older notes.
- Authentic moderate layered watercolor, including pigment variation inside the figures; translucent washes, paper luminosity and natural soft white borders. Avoid flat vectors, marker/pencil grain, embossed texture, glossy/3D rendering or excessive watercolor stains.
- Heads are perfect circles. Bodies have balanced simple adult proportions: no thick balloon limbs, skinny elongated figures, busts, pinched waists, prominent hips or buttocks. Gender is communicated mainly by a few fine eyelashes without changing the eye structure. Avoid selective clothing except a purposeful apron or scene-specific need.
- Contours are darker versions of each figure's local color, not black. Heads join the upper torso without a neck, with a soft local-color contact shadow.
- Exactly three fingers and one thumb on each visible hand. Minimal expressive eyes; no white sclera. A small white glint inside a dark oval eye is allowed. No frightening blank eyes or heavy lashes.
- Use varied figure colors appropriate to the scene, preserving identity between panels. The owner suggests red for anger, purple for waiting, yellow for energy, pink for sensitivity, green for positivity, blue for calm; these are useful choices, not mandatory universal symbols.
- Prefer square images. Use vertical/horizontal multi-panel layouts when they improve clarity. Horizontal Persian sequences read right to left. All in-image text is short, natural Persian.

## Storytelling and production

- Understand the underlying advice before proposing a scene. Show a clear concrete action, cause and consequence. A reader around age 12 should grasp the main idea quickly without a curator's explanation. If it needs an explanation to work, simplify the concept before generating it.
- Combine creative, memorable metaphors with visible logic and occasional gentle humor. Reference examples: #13 dropping ballast lets a balloon rise; #60 hatred poisons its holder first; #80 a parent turns the child's broken mirror into a colored mosaic. Original references 1,68,70,30,113,97,110,84,131,148,13,60,80 are in the separate full artwork archive, not all included here.
- Explain each idea in Persian in the gallery, but do not rely on that description to make an unclear image understandable.
- Use the image generation skill/tool for production and edits. Inspect the actual reference and target before editing. Save the complete English generation prompt, exact edit instruction, metadata and image hash for each candidate.
- Before presenting a result, inspect circles/proportions/eyes/eyelashes/hands/watercolor, text attribution, gaze/pointing, panel continuity, visible cause and effect, and cropping. Never invent a passed visual review.
- For revisions, read the exact submitted request. Report queued/in-progress/failed according to actual work, then publish the new image and keep approval pending. The gallery alone does not run an image generator.

## Transfer discipline

- This small copy includes current artwork and prompt/style/feedback history. Full historical image originals, Word/PDF, raw generation results, hosted-site credentials and machine runtimes were deliberately excluded from the initial transfer. State that limitation when relevant.
- Do not commit credentials, session tokens, dependency junctions, machine status/PIDs, locks, raw generation responses or large original archives. Do not expose the owner’s project publicly without an explicit instruction.

## Network efficiency

The owner requests lower internet usage while preserving all quality, context, originals, acceptance criteria and authorized scope. Summarize large local logs/data before returning focused tool output. Do not print image base64 or complete feedback histories. Reuse local artifacts and references, inspect the images needed for reliable judgment, batch independent checks, avoid unchanged polls and retransferring verified artifacts. Push only actual Git changes. Never reduce model capability, remove history, stop authorized work, restrict requested uploads or change VPN/sync settings merely to save traffic.
