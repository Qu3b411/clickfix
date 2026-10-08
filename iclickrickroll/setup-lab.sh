#!/usr/bin/env bash
# Guided acquisition and import of the prepared, infected iClickRickroll lab.
# Nothing is executed inside either guest; the researcher starts the demo later.
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
download_dir=${1:-"$script_dir/../../iclickrickroll-download"}
research_dir=${2:-"$script_dir/../../iclickrickroll-research"}
zip_name=iclickrickroll-lab-release.zip
acknowledgement=IAcknowledgeMaliciousContent

if [[ -t 1 && -z ${NO_COLOR:-} ]]; then
    red=$'\033[1;31m'; amber=$'\033[1;33m'; cyan=$'\033[1;36m'
    green=$'\033[1;32m'; reset=$'\033[0m'
else
    red=''; amber=''; cyan=''; green=''; reset=''
fi

say() { printf '%b\n' "$*"; }
die() { say "${red}Error:${reset} $*" >&2; exit 1; }
yes_no() {
    local reply
    while :; do
        read -r -p "$1 [y/n] " reply || exit 1
        case ${reply,,} in
            y|yes) return 0 ;;
            n|no) return 1 ;;
            *) say "Enter y or n." ;;
        esac
    done
}

[[ -t 0 ]] || die 'Run this script in an interactive terminal.'
for cmd in curl sha256sum stat awk unzip python3 realpath; do
    command -v "$cmd" >/dev/null || die "Missing $cmd. Install host prerequisites before setup."
done

say "${red}iClickRickroll — LIVE MALWARE research lab${reset}"
say 'Prepared infected Windows VM, isolated emulator VM, saved RAM, harness, and two ISOs.'
say 'Authorized researchers only. Use a dedicated Linux/VirtualBox host.'
say 'Keep the shipped internal network only; never add NAT, bridged, or host-only adapters.'
say 'Download: 12 release parts, 22,887,509,030 bytes assembled (~21.3 GiB).'
say 'Extraction: about 118.6 GB, plus space for disposable run clones.'
say "Warning: $script_dir/MALWARE-WARNING.txt"
say ''

if ! yes_no "${cyan}Download, verify, and assemble the encrypted archive now?${reset}"; then
    say 'Stopped before download.'
    exit 0
fi

bash "$script_dir/acquire-lab.sh" "$download_dir"
download_dir=$(cd -- "$download_dir" && pwd -P)
research_dir=$(realpath -m -- "$research_dir")
archive="$download_dir/$zip_name"
lab_dir="$research_dir/iclickrickroll-lab"
say ''
say "${amber}The archive has been verified. Extraction writes live malware and VM disks to:${reset}"
say "  $lab_dir"
if ! yes_no 'Continue to extraction and VirtualBox import?'; then
    say "Archive retained at $archive. No VM was imported."
    exit 0
fi

say "Type ${acknowledgement} to acknowledge the live-malware content."
read -r -p 'Acknowledgement: ' entered || exit 1
[[ "$entered" == "$acknowledgement" ]] || die 'Acknowledgement did not match. Nothing was extracted.'
unset entered
[[ ! -e "$research_dir" ]] || die "Research directory already exists: $research_dir. Choose a new second argument."
mkdir -p -- "$research_dir"

say "${cyan}Extracting the verified archive...${reset}"
say 'The acknowledgement is the archive password; it stays off the process command line.'
printf '%s\n' "$acknowledgement" | python3 "$script_dir/unzip-ack.py" "$archive" "$research_dir" || die "Extraction failed. Inspect $research_dir before retrying."
[[ -f "$lab_dir/SHA256SUMS" && -f "$lab_dir/import.sh" && -f "$lab_dir/packages.json" ]] || die 'Extracted lab is incomplete.'
say "${cyan}Verifying extracted files (this reads the entire package)...${reset}"
(cd -- "$lab_dir" && sha256sum -c --quiet SHA256SUMS) || die 'Extracted files failed SHA-256 verification.'
say "${green}All extracted checksums passed.${reset}"

# Show the host requirements from the verified package. Never install the
# emulator_guest packages on the host or execute a command from JSON.
python3 - "$lab_dir/packages.json" <<'PY'
import json
import sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
host = data['requirements']['host']
print('\nHost requirements listed in packages.json:')
for item in host['required']:
    print('  required:', item['pkg'])
for item in host['optional']:
    print('  optional:', item['pkg'])
PY
say ''
if yes_no 'Install the listed Debian/Ubuntu host packages, including optional recording tools?'; then
    command -v apt-get >/dev/null || die 'apt-get is unavailable; install the listed host packages manually.'
    say "${amber}Installing host tools through apt; sudo may prompt for your password.${reset}"
    if (( EUID == 0 )); then installer=(apt-get); else
        command -v sudo >/dev/null || die 'sudo is unavailable; install the listed host packages manually.'
        installer=(sudo apt-get)
    fi
    host_packages=(xorriso make python3 coreutils curl unzip
        gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good
        gstreamer1.0-libav imagemagick pulseaudio-utils)
    command -v VBoxManage >/dev/null || host_packages=(virtualbox "${host_packages[@]}")
    "${installer[@]}" install -y "${host_packages[@]}"
else
    say 'Host package installation skipped.'
fi

for cmd in VBoxManage make python3 sha256sum xorriso; do
    command -v "$cmd" >/dev/null || die "Required host command $cmd is missing; install it, then run $lab_dir/import.sh."
done

say "${cyan}Importing the two verified VM baselines into this VirtualBox user home...${reset}"
(cd -- "$lab_dir" && ./import.sh) || die "VM import failed. Inspect $lab_dir and the VirtualBox registry before retrying."

say ''
say "${green}Research directory ready: $lab_dir${reset}"
say 'To reproduce the demo in this isolated lab:'
printf '  cd %q && make iclickrickroll\n' "$lab_dir/reproducible-lab"
say 'After the emulator preflight passes, type send-rick in the C2 pane.'
say 'The setup script has not started either VM.'
