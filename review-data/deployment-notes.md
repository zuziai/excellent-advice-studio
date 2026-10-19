# Private review delivery

Published URL: https://excellent-advice-art-review.zuziai.chatgpt.site

Site: `appgprj_6ac09d17ae948191989be6498098593c`

Saved version: `appgprj_6ac09d17ae948191989be6498098593c~appgver_1178058c05348191acf2f44ac8c6546d`

Deployment: `appgdep_6ac0a33bd21c8191984ad535caf98284`, verified succeeded.

Source commit: `192c6ba1b8c8de7a8f4028c0a418b6b7ea6117b0`

The standard Sites workflow completed source commit/push and remote-head verification, but its packaging step failed because `package-site.mjs` invokes Bash, which this bundled Windows runtime does not contain. No source changes occurred after that pushed commit. `package-review-windows.py` invoked the same bundled `prepare-site-build.cjs` validator, staged only static output and normalized manifest, archived with Python tarfile, and validated all five image entries. The archive was saved and privately deployed with the native Sites operation. Future updates should retain this Site identity, follow normal source synchronization, and use this Windows packaging equivalent if Bash remains unavailable. Never store source credentials in files.

The private hosted version saves feedback in the browser; Download feedback gives the review JSON to return in chat. The local server offers direct file saves when explicitly running. UI navigation, note preservation, retry migration, export shape and non-overwriting approval copying were checked; all five generated images were visually inspected, with Persian wording verified. Ordinary gripping hands may naturally occlude a thumb; these are calibration candidates, not user-approved finals.

Pilot generation used built-in ImageGen, five distinct calls plus targeted edits. Drafts and exact prompts: `review-data/pilot-151/`. Final approvals alone may be copied into `Images` using `book-review/finish_review.py --apply-approved` after importing feedback. No pilot image was finalized by automated checks.

## Persian interface and edit requests — 2026-10-03

Updated the same private Site with Persian labels, an explicit edit-request button on each card and in the enlarged view, and Persian story/meaning explanations for all five candidates. Candidate IDs, wave ID and browser storage key are unchanged, preserving existing choices and comments. Clicking an edit request records `revise` and focuses the comment box; typing saves the requested changes. Final approval remains a separate action.

Source commit: `2c8b0bb6f8f786992e18bd60fc3ebbfab90657f0`

Saved version: `appgprj_6ac09d17ae948191989be6498098593c~appgver_f92db502b17c8191945193cedcb9b962`

Deployment: `appgdep_6ac0af609e6881918675ab7782d15173`, succeeded. URL remains https://excellent-advice-art-review.zuziai.chatgpt.site.

Validated JavaScript syntax and clean diff formatting, then tested the card and side-panel edit actions, note retention across idea navigation and reload, and arrow-key navigation in an isolated localhost static preview. Test feedback was cleared via the UI; production feedback and artwork were not altered by testing. Screenshot: `review-data/interface-preview-fa.png`. Explanation source: `review-data/pilot-151/explanations-fa.json`; the pilot builder now preserves these fields.

The standard workflow pushed and verified source; its Bash packaging step remains unavailable on Windows. Reused the bundled static validator with the existing Windows packaging equivalent and successfully published that exact source archive.

## Overall revision requests — 2026-10-03

Added an explicit overall edit action beside the existing reject action. `revise_all` requests revisions of all current candidates based on the sentence-level `note`; it has `chosenIdeaId: null` and retains individual `ideaNotes`. It is distinct from `rejected`, which requests replacement ideas. The UI shows a confirmation and offers cancellation while keeping notes. Browser reload preserves this status. Local validation, feedback import and `finish_review.py` reporting now accept this state; it never copies images to Images.

Source commit: `4a532ee537669706689923211dabe8bf56722f1c`

Saved version: `appgprj_6ac09d17ae948191989be6498098593c~appgver_76687035e95481918bee411d82e73ab1`

Deployment: `appgdep_6ac0b12516a08191adc55775a8848d3f`, succeeded at the same private URL. Standard source synchronization plus the existing Windows packaging equivalent were used.

Validation: UI action and reload retained both overall and individual feedback; temporary test notes were cleared. Synthetic backend/import checks accepted null selection, rejected non-null selection for revise_all, preserved Persian notes, distinguished revise/revise_all/rejected in reporting and copied no images even with --apply-approved. Real feedback, Images and project-state were untouched by tests. Screenshot: `review-data/interface-overall-edit.png`.

## Original image downloads and user ideas — 2026-10-03

Every card and the enlarged view now offer a direct same-origin download of the original image file. Card labels show actual source pixel dimensions, and download names include the candidate revision ID. The file is never resized or re-encoded. A real browser download of candidate A was byte-identical to its original (SHA-256 comparison; 2,887,363 bytes). Enlarged-view download targets update when navigating to another idea.

The custom idea panel saves drafts separately and registers an explicit `custom_idea` request with `customIdea`, `requestedVariants: 5` and `chosenIdeaId: null`. Overall and per-image notes are preserved. Empty submissions are blocked. The page clearly tells users to export feedback and send it in the chat for generation. Import and processing report these requests under `custom_ideas` without treating them as approved images.

Source commit: `539577976c7f0459e7689b305f34c3ee6c3cf61c`

Saved version: `appgprj_6ac09d17ae948191989be6498098593c~appgver_203861f8e63081919d131953efe9d5c2`

Deployment: `appgdep_6ac0b51992e881918b49bda2a5cb4c9b`, succeeded at the same private URL. Source synchronization and the existing Windows packaging equivalent were used.

Validation: JavaScript syntax and diff formatting passed. UI draft/submit distinction, empty-input error, reload persistence and download target navigation were checked. Backend/import fixtures accepted valid custom requests, rejected invalid text/count/selection, preserved notes and copied no images for non-final requests. Temporary UI feedback was cleared. Screenshot: `review-data/interface-custom-idea.png`. No source artwork, real review feedback or approved-image history was changed by testing.

### Explicit revision submission and repeat edits — 2026-10-03
- Published private Site at the unchanged review URL.
- Commit: ed92c19331232a858b811b9fcf0d49b8f4eb3ef9
- Deployment: appgdep_6ac0b9d080088191b74bba9612164bcf (succeeded)
- Version: appgprj_6ac09d17ae948191989be6498098593c~appgver_62861aee9adc8191accfbb16a3faca47
- Explicit submit button follows image feedback; opening or typing only saves a draft. Submitted request includes target candidate/version, immutable comment, UUID and timestamp. Updated requests preserve prior snapshots; duplicate submission is idempotent.
- Same viewer provides feedback JSON download and explains manual chat handoff before image editing.
- Browser QA on isolated localhost: blank validation, draft vs submission, changing/resubmitting comments, duplicate submission, persistence after reload, actual exported JSON verified. Screenshot: interface-submit-revision.png. Test download moved out of Downloads to interface-submit-revision-feedback-test.json; no production feedback changed.
- Independent temporary tests passed: server validation and submitted-comment reporting; revision import never copies an unapproved image; builder v1-to-v2-to-v3 immutable assets/manifest history and idempotent rerun; frontend migration archives v1 and explicit resubmission targets v2.
- Existing five pilot images remain unchanged. No approvals or new artwork produced in this UI update.
- Bundled workflow committed and verified source; known Windows packaging failure handled by the documented native packaging helper using the same bundled static validator.

### Actual idea 3 revision delivered — 2026-10-03
- Read the user's submitted request directly from the open Site via WebMCP; no feedback upload was needed.
- Source request: ea5d1a22-c866-4fc5-997c-198f790be95f for 151-c-v1.
- Built-in ImageGen edit applied all four requested changes: removed wall shadow, shorter figures, green eyelashes and domestic interior without carpentry. Exact Persian dialogue retained. Independent visual review passed.
- Result: review-data/pilot-151/151-c-v2.png (1122 x 1402); full prompt/request/output lineage stored in revision-151-c-v2.json and prompts.json. Original image and v1 manifest retained.
- Active wave pilot-151-v2; A/B/D/E metadata and image bytes unchanged. User notes retained, completed request archived, new artwork pending explicit review. No image copied to Images.
- Site now shows version badges, a revision-ready message and applied-change summary. Static/local start instructions explicitly say generation requires a message in this chat; WebMCP read-back avoids mandatory JSON export.
- Local browser verified a second edit request targets 151-c-v2/version2. QA decision cleared; no production feedback mutated by that test. Screenshot: interface-idea3-v2.png.
- Commit: dd66e0592fbc5cd722159c5875f0981ee6b9777e
- Deployment: appgdep_6ac0bcf11d588191a48fcad9c7323157 (succeeded; same owner-private audience)
- Version: appgprj_6ac09d17ae948191989be6498098593c~appgver_7eb7c76cb2b4819195351316abe16802
- Known Windows packaging failure used the documented bundled-validator/native-tar fallback after committing and verifying source.

### Real edit activity and precise download labels — 2026-10-03
- UI commit 554852c29c4ba2e73dd5c64e0473308e9e161855; deployment appgdep_6ac0c33159a4819194b4417ea808d9b3 succeeded, owner-private audience unchanged.
- Submission immediately shows queued status; only an explicit marker for the matching active request starts the spinner. Working/failed status persists and completion requires a newer published image with the exact request ID and parent. Polling loads and decodes the image before changing the viewer, protects newer feedback and other active requests, then clears busy state.
- Card/viewer download labels identify the displayed version and full source quality. An actual C-v2 download was byte-identical to its edited PNG; local UI and independent progress/validation/race fixtures passed. No approvals introduced.

### Actual idea 3 second revision delivered — 2026-10-03
- Read active request 03e3f29e-0cf5-45f6-9177-c028866b19e4 for 151-c-v2 from the user's open page. Actual working status was set immediately before generation and updated during publication.
- Built-in ImageGen edited C-v2 into C-v3: both necks removed; cream wall separated from sky by the outer wall edge and roof eave. Independent visual review passed; all earlier corrections, dialogue and watercolor style retained.
- Prompt/input/output stored in review-data/pilot-151/revision-151-c-v3.json. No-necks recorded as the user's global character rule; scene-specific architecture correction kept scoped.
- Source commit aecca3607e0cb94fa5b35f6c139d287161c452b0; deployment appgdep_6ac0c558b6e081918b066b35dc965dbc succeeded at the same owner-private URL; saved version appgprj_6ac09d17ae948191989be6498098593c~appgver_81c2f8554860819182bcf96bc77b8900.
- Live open page received pilot-151-v3 without a reload, replaced the image, stopped activity, showed the ready message and linked download to art/151-c-v3.png. Screenshots: interface-actual-edit-progress.png and interface-version-3-ready.png.
- Independent lineage checks passed: A/B/D/E exactly unchanged, C-v1/C-v2 preserved, both requests and notes retained. New artwork pending review; no approval or final Images copy. Windows stdout Unicode issue in finish_review.py fixed and importer report verified.
- Owned temporary localhost QA server stopped; no user tabs closed. Production feedback snapshots are preserved separately from isolated UI test feedback.

### All five pilot candidates recalibrated to moderate body watercolor — 2026-10-03
- Direct user request supplied the office/hourglass JPG as medium and head-to-torso-shadow reference, explicitly excluding its incorrect three-digit hands. Copied stable reference to review-data/references/watercolor-medium-2026-10-03.jpg; original user attachment untouched.
- Revisited the five current candidates and prior book references. Built-in ImageGen edited each asset independently, with extra targeted passes for C's wash/contact shadow and A's missing wooden finger/wooden neck. A/B/D/E are v2; C is v4.
- Full prompt sets, input/output and iteration provenance are saved in review-data/pilot-151/watercolor-batch-2026-10-03.json and five standalone revision-*-watercolor.json files. New medium constraints and the soft contact shadow without a neck are recorded in style-contract.md and style-study.md for future work.
- Independent visual QA passed all five: moderate watercolor visibly inside bodies, round heads, no neck segments, locally colored soft shadow below heads, correct four-total-digit design where visible, Persian text, lashes, story/panels and earlier corrections preserved. Natural hand occlusion remains at some tool/clay/glove grips. Background texture is finer than the reference; final medium preference awaits user review.
- Independent data QA passed: exact five IDs/versions/parents, full prompts/refinements in wave, source/dist/final original bytes identical; every one of seven prior published PNGs preserved; wave3 archived; feedback notes/history preserved, pending new IDs, no approvals or Images copies.
- Published source b900a00d6d0b456ef77a5e3c15e7675a13c850d6; saved version appgprj_6ac09d17ae948191989be6498098593c~appgver_96d7c3b6e89c819194ae8c9a104ca2b3; deployment appgdep_6ac0ccf048388191976b751a37c26190 succeeded at the unchanged owner-private URL. Used existing Windows native packaging fallback after bundled source workflow push/verification.
- Refreshed the user's existing tab and opened C-v4 for review; verified new labels/download targets for all five and C's full-quality v4 link. Screenshot interface-watercolor-ready.png; feedback-before-watercolor.json and feedback-after-watercolor.json saved as direct page snapshots. No extra browser tabs or QA servers created.
