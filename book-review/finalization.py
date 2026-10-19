"""Finalize only current explicit approvals, preserving original art and complete prompts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, subprocess, uuid
from runtime_support import writer_environment

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def prompt_cell_hash(prompt):
    # Match the writer's paragraph compaction without dropping any prompt words.
    compact = re.sub(r"\s*\r?\n\s*", " ", prompt.strip())
    compact = re.sub(r"[ \t]{2,}", " ", compact)
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".new")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()

def load_json(path, default):
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if Path(path).exists() else default

class Finalizer:
    def __init__(self, project, writer=None):
        self.project = Path(project).resolve()
        self.data = self.project.parent / "review-data"
        self.images = self.project.parent / "Images"
        self.ledger_path = self.data / "finalization-state.json"
        self.project_state_path = self.data / "project-state.json"
        self.writer = writer or self.write_excel

    def ledger(self):
        return load_json(self.ledger_path, {"format":"excellent-advice-finalization", "version":1, "entries":[], "pending":{}})

    def project_path(self, value):
        path = Path(value)
        return (path if path.is_absolute() else self.project.parent / path).resolve()

    def current_approvals(self, feedback):
        wave = load_json(self.project / "dist" / "wave.json", {})
        mapping = {s["id"]:{i["id"]:i for i in s["ideas"]} for s in wave.get("sentences", [])}
        return [(r, mapping[r["sentenceId"]][r["chosenIdeaId"]]) for r in feedback.get("records", [])
                if r.get("status") == "approved" and r.get("sentenceId") in mapping
                and r.get("chosenIdeaId") in mapping[r["sentenceId"]]
                and r.get("waveId", feedback.get("waveId")) == wave.get("id")]

    def source(self, candidate):
        relative = candidate.get("image", "")
        source = (self.project / "dist" / relative).resolve()
        art = (self.project / "dist" / "art").resolve()
        if not source.is_relative_to(art) or not source.is_file() or source.suffix.lower() != ".png":
            raise ValueError("Approved PNG unavailable")
        if source.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Source is not a PNG")
        image_hash = digest(source)
        if candidate.get("imageHash") and candidate["imageHash"] != image_hash:
            raise ValueError("Approved image hash mismatch")
        return source, image_hash

    def full_prompt(self, sid, candidate, image_hash):
        cid = candidate["id"]
        manifest_path = self.data / "finalization-2026-10-10" / "approved-prompts.json"
        manifest = load_json(manifest_path, {})
        items = manifest if isinstance(manifest, list) else manifest.get("jobs", manifest.get("items", []))
        for item in items:
            if item.get("sentenceId") == sid and item.get("ideaId", item.get("id")) == cid:
                if item.get("imageHash") and item["imageHash"] != image_hash:
                    continue
                prompt = item.get("prompt") or item.get("fullGenerationPromptEnglish")
                prompt_path = item.get("promptPath") or item.get("fullGenerationPromptEnglishPath")
                if not prompt and prompt_path:
                    prompt = self.project_path(prompt_path).read_text(encoding="utf-8-sig")
                if isinstance(prompt, str) and len(prompt.strip()) >= 100 and re.search(r"[A-Za-z]", prompt):
                    return prompt, prompt_path, str(manifest_path)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", cid):
            raise ValueError("Invalid candidate ID")
        metadata_paths = sorted(self.data.rglob(cid + ".metadata.json"))
        explicit_paths = candidate.get("metadataPaths", [])
        if isinstance(explicit_paths, str): explicit_paths = [explicit_paths]
        for value in explicit_paths:
            path = Path(value)
            if not path.is_absolute(): path = self.project.parent / path
            path = path.resolve()
            if path.is_relative_to(self.data.resolve()) and path.is_file() and path not in metadata_paths:
                metadata_paths.append(path)
        for metadata_path in reversed(metadata_paths):
            meta = load_json(metadata_path, {})
            if meta.get("sha256") and meta["sha256"] != image_hash:
                continue
            prompt = meta.get("fullGenerationPromptEnglish")
            prompt_path = meta.get("fullGenerationPromptEnglishPath")
            if not prompt and prompt_path:
                prompt = self.project_path(prompt_path).read_text(encoding="utf-8-sig")
            mode = str(meta.get("generation", {}).get("mode", "")).lower()
            # A local edit instruction is never a complete reusable generation prompt.
            if not prompt and "edit" not in mode and not meta.get("originalGeneration") and not meta.get("originalGenerationSourcePath") and not meta.get("parentIdeaId"):
                prompt = meta.get("prompt")
                prompt_path = meta.get("promptPath")
            if isinstance(prompt, str) and len(prompt.strip()) >= 100 and re.search(r"[A-Za-z]", prompt):
                return prompt, prompt_path, str(metadata_path)
        raise ValueError("Complete standalone English generation prompt unavailable")

    def write_excel(self, jobs):
        writer = self.data / "save-approved-prompts.mjs"
        if not writer.is_file():
            raise RuntimeError("Excel writer unavailable")
        node, environment = writer_environment(self.project.parent)
        directory = self.data / "finalization-requests"
        directory.mkdir(parents=True, exist_ok=True)
        request = directory / ("approved-" + uuid.uuid4().hex + ".json")
        atomic_json(request, {"jobs":jobs})
        try:
            process = subprocess.run([str(node), str(writer), "--input", str(request)], cwd=str(self.project.parent), env=environment,
                                     capture_output=True, text=True, encoding="utf-8", timeout=120,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            output = process.stdout.strip()
            last = output.splitlines()[-1] if output else ""
            result = json.loads(last) if last else {}
            if process.returncode != 0 or result.get("saved") is not True:
                raise RuntimeError((result.get("error") or process.stderr or output or "Excel writer failed")[-1500:])
            results = result.get("jobs", result.get("results", []))
            if not isinstance(results, list):
                raise RuntimeError("Excel writer did not verify saved jobs")
            for job in jobs:
                matched = next((r for r in results if r.get("sentenceId") == job["sentenceId"] and r.get("ideaId") == job["ideaId"]), None)
                if not matched or matched.get("column") != "D" or not matched.get("row") or not matched.get("workbookPath") or matched.get("sourcePromptSha256") != job["promptSha256"] or matched.get("promptSha256") != job["promptCellSha256"]:
                    raise RuntimeError("Excel writer did not verify exact approved prompt")
            return result
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as error:
            raise RuntimeError("Excel writer did not complete verification") from error

    def pending(self, ledger, sid, cid, reason, error, **details):
        value = {"sentenceId":sid, "ideaId":cid, "status":"pending", "messageFa":reason,
                 "lastAttemptUtc":now(), "error":str(error)[-1500:], **details}
        ledger.setdefault("pending", {})[str(sid)] = value
        return value

    def inspect(self, feedback):
        ledger = self.ledger()
        output = []
        for record, candidate in self.current_approvals(feedback):
            sid, cid = record["sentenceId"], candidate["id"]
            target = self.images / (str(sid) + ".png")
            try:
                _, image_hash = self.source(candidate)
                prompt, _, _ = self.full_prompt(sid, candidate, image_hash)
                prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                existing = next((e for e in reversed(ledger.get("entries", [])) if e.get("sentenceId") == sid
                                 and e.get("ideaId") == cid and e.get("imageHash") == image_hash
                                 and e.get("promptSha256") == prompt_hash and e.get("status") == "finalized"), None)
                if existing and target.is_file() and digest(target) == image_hash:
                    output.append(self.public(existing))
                    continue
            except (ValueError, OSError):
                pass
            pending = ledger.get("pending", {}).get(str(sid), {})
            output.append({"sentenceId":sid, "ideaId":cid, "status":"pending", "messageFa":(pending.get("messageFa") if pending.get("ideaId") == cid else None) or "انتخاب نهایی ثبت شده؛ ذخیرهٔ تصویر و پرامپت هنوز کامل نشده است."})
        return output

    def public(self, entry):
        output = {key:entry.get(key) for key in ("sentenceId","ideaId","status","imageHash","promptSha256","sourcePromptSha256","promptCellSha256","savedPath","finalizedAt","messageFa","downloadUrl","excel")}
        if output.get("savedPath"):
            output["savedPath"] = str(self.project_path(output["savedPath"]))
        if isinstance(output.get("excel"), dict):
            output["excel"] = dict(output["excel"])
            if output["excel"].get("workbookPath"):
                output["excel"]["workbookPath"] = str(self.project_path(output["excel"]["workbookPath"]))
        return output

    def finalize(self, feedback):
        ledger = self.ledger()
        outcomes, jobs = [], []
        for record, candidate in self.current_approvals(feedback):
            sid, cid = record["sentenceId"], candidate["id"]
            try:
                source, image_hash = self.source(candidate)
                prompt, prompt_path, prompt_source = self.full_prompt(sid, candidate, image_hash)
                prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                target = self.images / (str(sid) + ".png")
                existing = next((e for e in reversed(ledger.get("entries", [])) if e.get("sentenceId") == sid and e.get("ideaId") == cid
                                 and e.get("imageHash") == image_hash and e.get("promptSha256") == prompt_hash and e.get("status") == "finalized"), None)
                if existing and target.is_file() and digest(target) == image_hash:
                    outcomes.append(self.public(existing))
                    ledger.setdefault("pending", {}).pop(str(sid), None)
                    continue
                jobs.append({"sentenceId":sid,"ideaId":cid,"prompt":prompt,"promptPath":prompt_path,"promptSource":prompt_source,
                             "promptSha256":prompt_hash,"sourcePromptSha256":prompt_hash,"promptCellSha256":prompt_cell_hash(prompt),"imageHash":image_hash,"source":str(source),"savedPath":str(target),
                             "approvedAt":record.get("updatedAt"),"feedback":record})
            except (OSError, ValueError, TypeError) as error:
                reason = "انتخاب نهایی ثبت شد؛ پرامپت کامل انگلیسی یا فایل تصویر برای ذخیرهٔ نهایی آماده نیست."
                outcomes.append(self.pending(ledger, sid, cid, reason, error))
        if jobs:
            try:
                excel_result = self.writer(jobs)
                if excel_result.get("saved") is not True:
                    raise RuntimeError("Excel writer did not confirm saving")
                excel_jobs = excel_result.get("jobs", excel_result.get("results", []))
                for job in jobs:
                    excel = next((r for r in excel_jobs if r.get("sentenceId") == job["sentenceId"] and r.get("ideaId") == job["ideaId"]), None)
                    if not excel or excel.get("column") != "D" or not excel.get("row") or not excel.get("workbookPath") or excel.get("sourcePromptSha256") != job["promptSha256"] or excel.get("promptSha256") != job["promptCellSha256"]:
                        raise RuntimeError("Excel result does not match approved prompt")
            except Exception as error:
                reason = "انتخاب و نظرها ذخیره شدند؛ ذخیرهٔ نهایی کامل نشد. اگر اکسل باز است، آن را ببندید و دوباره تلاش کنید."
                outcomes.extend(self.pending(ledger, j["sentenceId"], j["ideaId"], reason, error) for j in jobs)
                jobs = []
        if jobs:
            state = load_json(self.project_state_path, {"approved":[]})
            history = state.setdefault("approved", [])
            successes = []
            for job in jobs:
                sid, cid = job["sentenceId"], job["ideaId"]
                try:
                    self.images.mkdir(parents=True, exist_ok=True)
                    target, source = Path(job["savedPath"]), Path(job["source"])
                    backup = None
                    if target.exists() and digest(target) != job["imageHash"]:
                        old_hash = digest(target)
                        backup = self.data / "finalization-backups" / "images" / str(sid) / (old_hash + ".png")
                        backup.parent.mkdir(parents=True, exist_ok=True)
                        if backup.exists():
                            if digest(backup) != old_hash:
                                raise RuntimeError("Previous approved image backup mismatch")
                        else:
                            with backup.open("xb") as output:
                                output.write(target.read_bytes())
                        if digest(backup) != old_hash:
                            raise RuntimeError("Previous approved image backup failed")
                        for earlier in history + ledger.get("entries", []):
                            if earlier.get("sentenceId") == sid and earlier.get("imageHash") == old_hash and earlier.get("savedPath") and self.project_path(earlier["savedPath"]) == target.resolve():
                                earlier.setdefault("originalSavedPath", earlier["savedPath"])
                                earlier["savedPath"] = str(backup)
                                earlier["supersededByIdeaId"] = cid
                    temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".new")
                    try:
                        with temporary.open("xb") as output:
                            output.write(source.read_bytes())
                        if digest(temporary) != job["imageHash"]:
                            raise RuntimeError("Original image bytes mismatch")
                        os.replace(temporary, target)
                    finally:
                        if temporary.exists():
                            temporary.unlink()
                    excel = next(r for r in excel_jobs if r.get("sentenceId") == sid and r.get("ideaId") == cid)
                    entry = {**job,"status":"finalized","finalizedAt":now(),"copiedAt":now(),"backupPath":str(backup) if backup else None,
                             "excel":excel,"downloadUrl":"/download/" + source.name,
                             "messageFa":"تصویر اصلی در پوشهٔ Images و پرامپت کامل انگلیسی در ستون D اکسل ذخیره شدند."}
                    previous = next((h for h in history if h.get("sentenceId") == sid and h.get("ideaId") == cid and h.get("imageHash") == job["imageHash"] and h.get("promptSha256") == job["promptSha256"] and h.get("status") == "finalized"), None)
                    if previous:
                        entry["finalizedAt"] = previous.get("finalizedAt", entry["finalizedAt"])
                        entry["backupPath"] = entry["backupPath"] or previous.get("backupPath")
                        previous.update(entry)
                    else: history.append(entry)
                    successes.append(entry)
                except Exception as error:
                    outcomes.append(self.pending(ledger,sid,cid,"نظرها ذخیره شدند؛ پرامپت در اکسل ثبت شد، اما ذخیرهٔ تصویر کامل نشد. دوباره تلاش کنید.",error,excelSaved=True,imageSaved=False))
            if successes:
                try:
                    state["activeWave"] = load_json(self.project / "dist" / "wave.json", {}).get("id")
                    atomic_json(self.project_state_path, state)
                    for entry in successes:
                        previous = next((e for e in ledger.setdefault("entries", []) if e.get("sentenceId") == entry["sentenceId"] and e.get("ideaId") == entry["ideaId"] and e.get("imageHash") == entry["imageHash"] and e.get("promptSha256") == entry["promptSha256"] and e.get("status") == "finalized"), None)
                        if previous: previous.update(entry)
                        else: ledger["entries"].append(entry)
                        ledger.setdefault("pending", {}).pop(str(entry["sentenceId"]), None)
                        outcomes.append(self.public(entry))
                except Exception as error:
                    outcomes.extend(self.pending(ledger,e["sentenceId"],e["ideaId"],"تصویر و پرامپت نوشته شدند؛ ثبت سابقهٔ نهایی کامل نشد. دوباره تلاش کنید.",error,excelSaved=True,imageSaved=True) for e in successes)
        ledger["updatedAt"] = now()
        atomic_json(self.ledger_path, ledger)
        return outcomes

