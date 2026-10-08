# Publication record and maintenance

The [repository](https://github.com/Qu3b411/clickfix) is public. The prepared
lab is published under [`iclickrickroll-lab-v1`](https://github.com/Qu3b411/clickfix/releases/tag/iclickrickroll-lab-v1).
The [article](https://blog.jacobmohrbutter.com/clickfix/) explains the incident
and embeds the [recorded demonstration](https://www.youtube.com/watch?v=VRApu5B4TR8).

The release contains twelve numbered ZIP parts and three small sidecars:
`ARCHIVE-SHA256SUMS`, `ARCHIVE-INSTRUCTIONS.txt`, and `MALWARE-WARNING.txt`.
They are GitHub Release assets, not Git objects. The repository contains the
acquisition scripts, checksum manifest, handling instructions, controller, and
research notes. The infected VM folders, raw incident captures, original
screenshots, mailbox records, and video source file are outside Git history.

Before changing a release asset, check its GitHub SHA-256 digest against
[`ARCHIVE-SHA256SUMS`](ARCHIVE-SHA256SUMS). The twelve parts must join to the
assembled ZIP hash in that manifest. Do not edit the checked-in sidecar text
without also replacing its release asset and recording the new digest.

[`../manifests/SHA256SUMS.txt`](../manifests/SHA256SUMS.txt) covers source files
in the repository. Update a line when its file changes, then run
`sha256sum -c manifests/SHA256SUMS.txt` from the repository root. The manifest
for the release parts is separate; source-document edits do not change the
published VM archive.
