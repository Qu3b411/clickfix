#!/usr/bin/env bash
# Download and assemble the encrypted iClickRickroll lab archive.
# This script does not extract the ZIP, import a VM, or run malware.
set -Eeuo pipefail

repo='qu3b411/clickfix'
tag='iclickrickroll-lab-v1'
zip_name='iclickrickroll-lab-release.zip'
prefix="${zip_name}.part"
zip_bytes=22887509030
chunk_bytes=1992294400
zip_sha256='69ba4260298d3b47fc10dc9c846b1084b4bc850601f833d7031784d5c1619394'
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
output_dir=${1:-"$script_dir/../../iclickrickroll-download"}
mkdir -p -- "$output_dir"
output_dir=$(cd -- "$output_dir" && pwd -P)
manifest="$script_dir/ARCHIVE-SHA256SUMS"

for command in curl sha256sum stat awk; do
    command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done
[[ -f "$manifest" ]] || { echo "Missing $manifest" >&2; exit 1; }

expected_hash() {
    awk -v name="$1" '$2 == name {print $1}' "$manifest"
}

verify_file() {
    local path=$1 expected_size=$2 expected_hash_value=$3 actual_hash
    [[ -f "$path" ]] || return 1
    [[ $(stat -Lc %s -- "$path") == "$expected_size" ]] || return 1
    actual_hash=$(sha256sum -- "$path")
    [[ ${actual_hash:0:64} == "$expected_hash_value" ]]
}

[[ $(expected_hash "$zip_name") == "$zip_sha256" ]] || {
    echo 'The checked-in archive manifest does not match this downloader.' >&2
    exit 1
}

for sidecar in ARCHIVE-SHA256SUMS MALWARE-WARNING.txt ARCHIVE-INSTRUCTIONS.txt; do
    source="$script_dir/$sidecar"
    destination="$output_dir/$sidecar"
    [[ "$source" -ef "$destination" ]] || cp -- "$source" "$destination"
done

for number in {0..11}; do
    printf -v suffix '%02d' "$number"
    name="${prefix}${suffix}"
    file="$output_dir/$name"
    temporary="$file.partial"
    expected=$(expected_hash "$name")
    [[ -n "$expected" ]] || { echo "No checksum for $name" >&2; exit 1; }
    if (( number < 11 )); then size=$chunk_bytes; else size=$((zip_bytes - 11*chunk_bytes)); fi

    if verify_file "$file" "$size" "$expected"; then
        echo "Verified existing part $name"
        continue
    fi
    if [[ -e "$file" ]]; then
        echo "Existing part is invalid; move it aside before retrying: $file" >&2
        exit 1
    fi
    if verify_file "$temporary" "$size" "$expected"; then
        mv -- "$temporary" "$file"
        echo "Recovered complete download $name"
        continue
    fi
    url="https://github.com/${repo}/releases/download/${tag}/${name}"
    echo "Downloading $name ($size bytes)"
    curl --fail --location --retry 5 --retry-delay 3 --continue-at - \
        --output "$temporary" "$url"
    verify_file "$temporary" "$size" "$expected" || {
        echo "Download failed checksum/size verification: $temporary" >&2
        exit 1
    }
    mv -- "$temporary" "$file"
done

archive="$output_dir/$zip_name"
if verify_file "$archive" "$zip_bytes" "$zip_sha256"; then
    echo 'Verified existing assembled ZIP.'
elif [[ -e "$archive" ]]; then
    echo "Existing ZIP is invalid; move it aside before retrying: $archive" >&2
    exit 1
else
    temporary="$archive.partial"
    echo 'Assembling the twelve parts into one encrypted ZIP.'
    cat "$output_dir"/"$prefix"[0-9][0-9] > "$temporary"
    verify_file "$temporary" "$zip_bytes" "$zip_sha256" || {
        echo "Assembled ZIP failed checksum/size verification: $temporary" >&2
        exit 1
    }
    mv -- "$temporary" "$archive"
fi

printf '\nVerified encrypted archive: %s\n' "$archive"
printf 'Read MALWARE-WARNING.txt and ARCHIVE-INSTRUCTIONS.txt before extraction.\n'
printf 'This script has not extracted the archive or started any VM.\n'
