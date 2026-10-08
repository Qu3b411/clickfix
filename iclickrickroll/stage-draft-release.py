#!/usr/bin/env python3
"""Check the iClickRickroll assets; optionally create a private repo + draft release.

The default mode is read-only. --upload-draft creates one source commit, pushes
it to a private GitHub repository, and uploads/resumes assets on a draft release.
It never makes the repository or release public.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPOSITORY = "qu3b411/clickfix"
TAG = "iclickrickroll-lab-v1"
PREFIX = "iclickrickroll-lab-release.zip.part"
ZIP_NAME = "iclickrickroll-lab-release.zip"
ZIP_SIZE = 22_887_509_030
ZIP_SHA256 = "69ba4260298d3b47fc10dc9c846b1084b4bc850601f833d7031784d5c1619394"
PART_COUNT = 12
SIDECARS = ("ARCHIVE-SHA256SUMS", "ARCHIVE-INSTRUCTIONS.txt", "MALWARE-WARNING.txt")
REPO_ROOT = Path(__file__).resolve().parent.parent


def run(*args: str, cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          capture_output=capture)


def optional(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True)


def asset_directory(value: str | None) -> Path:
    if value is None:
        config = Path(__file__).with_name(".release-assets-path")
        if not config.is_file():
            raise ValueError("pass ASSET_DIR or create iclickrickroll/.release-assets-path")
        value = config.read_text().strip()
    folder = Path(value).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError(f"asset directory not found: {folder}")
    return folder


def manifest(folder: Path) -> dict[str, str]:
    entries = {}
    for line in (folder / "ARCHIVE-SHA256SUMS").read_text().splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
        if not match or match.group(2) in entries:
            raise ValueError(f"invalid archive manifest line: {line!r}")
        entries[match.group(2)] = match.group(1)
    expected = {f"{PREFIX}{i:02d}" for i in range(PART_COUNT)} | {ZIP_NAME}
    if set(entries) != expected or entries[ZIP_NAME] != ZIP_SHA256:
        raise ValueError("archive manifest names or ZIP checksum do not match this package")
    return entries


def check_assets(folder: Path) -> list[Path]:
    names = [f"{PREFIX}{i:02d}" for i in range(PART_COUNT)]
    expected_files = set(names) | set(SIDECARS)
    actual_files = {p.name for p in folder.iterdir() if p.is_file()}
    if actual_files != expected_files:
        raise ValueError(f"release files differ: missing={sorted(expected_files-actual_files)}, "
                         f"extra={sorted(actual_files-expected_files)}")
    for name in SIDECARS:
        if (folder / name).read_bytes() != (REPO_ROOT / "iclickrickroll" / name).read_bytes():
            raise ValueError(f"release sidecar differs from repository copy: {name}")
    entries = manifest(folder)
    parts = [folder / name for name in names]
    sizes = [p.stat().st_size for p in parts]
    if any(size >= 2_000_000_000 for size in sizes) or sum(sizes) != ZIP_SIZE:
        raise ValueError(f"part sizes invalid: {sizes}")
    whole = hashlib.sha256()
    for index, part in enumerate(parts, 1):
        digest = hashlib.sha256()
        with part.open("rb") as stream:
            while chunk := stream.read(4 * 1024 * 1024):
                digest.update(chunk)
                whole.update(chunk)
        if digest.hexdigest() != entries[part.name]:
            raise ValueError(f"SHA-256 mismatch: {part.name}")
        print(f"Verified part {index}/{PART_COUNT}: {part.name}", flush=True)
    if whole.hexdigest() != ZIP_SHA256:
        raise ValueError("joined ZIP SHA-256 mismatch")
    run("sha256sum", "-c", "manifests/SHA256SUMS.txt", cwd=REPO_ROOT, capture=True)
    if list(REPO_ROOT.rglob("*.zip.part[0-9][0-9]")):
        raise ValueError("archive parts must not be inside the Git repository")
    print(f"PASS: {ZIP_SIZE:,} encrypted ZIP bytes, {PART_COUNT} release parts, source manifest")
    return parts


def git_output(*args: str) -> str:
    return run("git", "-C", str(REPO_ROOT), *args, capture=True).stdout.strip()


def prepare_source_commit() -> None:
    if not (REPO_ROOT / ".git").exists():
        run("git", "init", "-b", "main", str(REPO_ROOT))
    commit_email = os.environ.get("GIT_PUBLICATION_EMAIL", "")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", commit_email):
        raise ValueError("set GIT_PUBLICATION_EMAIL to the email address for the source commit")
    for key, expected in (("GIT_AUTHOR_NAME", "qu3b411"),
                          ("GIT_COMMITTER_NAME", "qu3b411"),
                          ("GIT_AUTHOR_EMAIL", commit_email),
                          ("GIT_COMMITTER_EMAIL", commit_email)):
        if os.environ.get(key, expected) != expected:
            raise ValueError(f"{key} would override the private commit identity")
    run("git", "-C", str(REPO_ROOT), "config", "--local", "user.name", "qu3b411")
    run("git", "-C", str(REPO_ROOT), "config", "--local", "user.email", commit_email)
    head = optional("git", "-C", str(REPO_ROOT), "rev-parse", "--verify", "HEAD")
    if head.returncode:
        run("git", "-C", str(REPO_ROOT), "add", "--all")
        tracked = git_output("ls-files").splitlines()
        if any(".zip.part" in name for name in tracked):
            raise ValueError("archive part would enter Git history")
        for name in tracked:
            if (REPO_ROOT / name).stat().st_size >= 100_000_000:
                raise ValueError(f"oversized Git object: {name}")
        run("git", "-C", str(REPO_ROOT), "diff", "--cached", "--check")
        run("git", "-C", str(REPO_ROOT), "-c", "commit.gpgsign=false", "commit", "-m",
            "Publish ClickFix research kit and prepared-lab release instructions")
    elif git_output("status", "--porcelain"):
        raise ValueError("source tree changed after its commit; review before publishing")
    if git_output("log", "-1", "--format=%an%n%ae%n%cn%n%ce").splitlines() != [
        "qu3b411", commit_email, "qu3b411", commit_email
    ]:
        raise ValueError("source commit exposes a different author or committer identity")
    if git_output("branch", "--show-current") != "main":
        raise ValueError("expected main branch")


def private_repository_and_push() -> None:
    viewed = optional("gh", "repo", "view", REPOSITORY, "--json", "isPrivate")
    if viewed.returncode:
        run("gh", "repo", "create", REPOSITORY, "--private", "--source",
            str(REPO_ROOT), "--remote", "origin", "--push",
            "--description", "ClickFix malware research and isolated replication kit")
        return
    if not json.loads(viewed.stdout).get("isPrivate"):
        raise ValueError("remote repository is public; refusing to upload a draft into it")
    remote = optional("git", "-C", str(REPO_ROOT), "remote", "get-url", "origin")
    if remote.returncode:
        run("git", "-C", str(REPO_ROOT), "remote", "add", "origin",
            f"https://github.com/{REPOSITORY}.git")
    elif REPOSITORY.lower() not in remote.stdout.lower():
        raise ValueError(f"origin points to another repository: {remote.stdout.strip()}")
    remote_head = optional("git", "ls-remote", "origin", "refs/heads/main", cwd=REPO_ROOT)
    if remote_head.returncode:
        raise ValueError(remote_head.stderr.strip())
    if remote_head.stdout.split("\t")[0] != git_output("rev-parse", "HEAD"):
        run("git", "-C", str(REPO_ROOT), "push", "-u", "origin", "main")


def draft_release() -> None:
    viewed = optional("gh", "release", "view", TAG, "-R", REPOSITORY,
                      "--json", "isDraft,assets")
    if viewed.returncode:
        run("gh", "release", "create", TAG, "--draft", "--target", "main",
            "--title", "iClickRickroll prepared lab",
            "--notes-file", str(REPO_ROOT / "iclickrickroll" / "RELEASE-NOTES.md"),
            "-R", REPOSITORY)
    elif not json.loads(viewed.stdout).get("isDraft"):
        raise ValueError("release is already public; refusing to modify it")


def upload_missing(folder: Path, parts: list[Path]) -> None:
    files = parts + [folder / name for name in SIDECARS]
    for asset in files:
        viewed = run("gh", "release", "view", TAG, "-R", REPOSITORY,
                     "--json", "isDraft,assets", capture=True)
        data = json.loads(viewed.stdout)
        if not data.get("isDraft"):
            raise ValueError("release is no longer a draft")
        existing = {item["name"]: item["size"] for item in data["assets"]}
        if asset.name in existing:
            if existing[asset.name] != asset.stat().st_size:
                raise ValueError(f"uploaded asset has wrong size: {asset.name}")
            print(f"Already uploaded: {asset.name}", flush=True)
            continue
        print(f"Uploading {asset.name} ({asset.stat().st_size:,} bytes)", flush=True)
        run("gh", "release", "upload", TAG, str(asset), "-R", REPOSITORY)
    final = json.loads(run("gh", "release", "view", TAG, "-R", REPOSITORY,
                           "--json", "isDraft,assets,url", capture=True).stdout)
    remote = {item["name"]: item["size"] for item in final["assets"]}
    for asset in files:
        if remote.get(asset.name) != asset.stat().st_size:
            raise ValueError(f"draft release missing or mismatching: {asset.name}")
    print("Draft upload complete:", final["url"])
    print("Repository is private; release is draft. Nothing is public yet.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_dir", nargs="?", help="directory with the 12 parts and 3 sidecars")
    parser.add_argument("--upload-draft", action="store_true",
                        help="create one commit, private repo, and resumable draft release upload")
    args = parser.parse_args()
    folder = asset_directory(args.asset_dir)
    parts = check_assets(folder)
    if not args.upload_draft:
        print("Read-only check complete. Add --upload-draft when ready to create the private repo.")
        return
    if not shutil.which("gh") or not shutil.which("git"):
        raise ValueError("git and GitHub CLI (gh) are required")
    run("gh", "auth", "status", capture=True)
    prepare_source_commit()
    private_repository_and_push()
    draft_release()
    upload_missing(folder, parts)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
