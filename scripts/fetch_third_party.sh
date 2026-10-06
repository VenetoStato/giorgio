#!/usr/bin/env bash
# Fetch the third-party robot models Giorgio uses into third_party/ (git-ignored), at the exact commits used for the
# published results. Their licences travel with them (see NOTICE.md). Re-running is safe: existing checkouts are moved
# to the pinned commit.
#
#   scripts/fetch_third_party.sh            # everything Giorgio uses (~400 MB on disk, sparse where possible)
#   scripts/fetch_third_party.sh --minimal  # only what the simulation needs by default (OpenArm MJCF, ~25 MB)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TP="$ROOT/third_party"
mkdir -p "$TP"
MINIMAL=0; [[ "${1:-}" == "--minimal" ]] && MINIMAL=1

# name | url | commit | sparse paths ("" = whole repository)
REPOS=(
  "openarm_mujoco|https://github.com/enactic/openarm_mujoco.git|f37a98ac2d75fdbc77768e9694f36c54b621ff1b|v2 LICENSE README.md"
  "orcahand_description|https://github.com/orcahand/orcahand_description.git|b9b349a21ee0238c62b6cf92ae7597027867adf8|v2 LICENSE README.md"
  "AmazingHand|https://github.com/pollen-robotics/AmazingHand.git|3e8241074df3436a3044ced4881e3bb2133aa725|Demo/AHSimulation LICENSE README.md"
  "mujoco_menagerie|https://github.com/google-deepmind/mujoco_menagerie.git|4d038b3feae26ec82b46a4d586379114012a8ac7|leap_hand LICENSE README.md"
  "openarm_description|https://github.com/enactic/openarm_description.git|14ff67b638ff1c738a1b9a6be8aaa5ce5ed2c831|"
)

fetch() {
  local name=$1 url=$2 sha=$3 sparse=$4 dir="$TP/$1"
  echo "==> $name @ ${sha:0:10}"
  if [[ ! -d "$dir/.git" ]]; then
    git clone --quiet --filter=blob:none --no-checkout "$url" "$dir"
  fi
  if [[ -n "$sparse" ]]; then
    git -C "$dir" sparse-checkout set --no-cone $(for p in $sparse; do echo "/$p"; done)
  fi
  git -C "$dir" fetch --quiet origin "$sha" 2>/dev/null || git -C "$dir" fetch --quiet origin
  git -C "$dir" -c advice.detachedHead=false checkout --quiet "$sha"
}

for r in "${REPOS[@]}"; do
  IFS='|' read -r name url sha sparse <<<"$r"
  if [[ $MINIMAL == 1 && $name != openarm_mujoco ]]; then continue; fi
  fetch "$name" "$url" "$sha" "$sparse"
done

# Small wrappers that mount an ORCA v2 hand on an OpenArm flange (used by giorgio_model.py, hand option "orca").
ORCA="$TP/orcahand_description/v2"
if [[ -d "$ORCA" ]]; then
  for side in right left; do
    cat > "$ORCA/giorgio_orca_$side.xml" <<XML
<mujoco model="orca_$side giorgio">
  <include file="models/assets/options.xml"/>
  <include file="models/mjcf/orcahand_$side.mjcf"/>
  <worldbody>
    <body name="${side}_mount" pos="0 0 0" euler="1.5708 0 0">
      <include file="models/mjcf/orcahand_${side}_body.xml"/>
    </body>
  </worldbody>
</mujoco>
XML
  done
fi
echo "Done. third_party/ now holds: $(ls "$TP" | tr '\n' ' ')"
