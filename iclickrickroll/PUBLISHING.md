# Maintainer: publishing the repository

The prepared lab release is published under `iclickrickroll-lab-v1`, but the
`qu3b411/clickfix` repository is still private. Repository collaborators can
inspect the release and download its assets. Other readers will be able to use
the release links after the repository becomes public.

The twelve archive parts and three sidecars are GitHub Release assets. They are
not Git objects. The encrypted ZIP is about 21.3 GiB, so it was divided into
parts below GitHub's per-asset limit. The source checkout contains the
acquisition script, SHA-256 manifest, handling warning, and instructions.

The initial source commit used the research identity `qu3b411` and the
publication address supplied for that commit. Its author metadata will be
visible when the repository becomes public. The lab VM folders, raw incident
captures, original screenshots, mailbox records, and video source file are not
tracked in this repository.

## Before changing visibility

Check the repository, the published release, and the companion article as one
set. The release must contain `part00` through `part11` plus
`ARCHIVE-SHA256SUMS`, `ARCHIVE-INSTRUCTIONS.txt`, and `MALWARE-WARNING.txt`.
GitHub's asset digests must match the checked-in manifest, and the twelve-part
stream must match the assembled ZIP hash. The guide in
[`README.md`](README.md) uses the release tag in its download URLs.

The article's YouTube slot is still pending. Insert the video ID only after
uploading the intended cut and checking its caption. The video is a viewing
copy; the VM release is the replayable artifact.

When the publication review is complete, the remaining visibility change is:

```sh
gh repo edit qu3b411/clickfix --visibility public --accept-visibility-change-consequences
```

The release is already published. Keep the repository private until you are
ready for the source, release assets, and their links to become public together.
