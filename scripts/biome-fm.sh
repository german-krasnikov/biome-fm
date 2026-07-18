# Shell wrapper for biome-fm — cd-on-exit (lf/yazi-style)
# Source this file in your .bashrc / .zshrc:
#   source /path/to/biome-fm.sh
#
# Then use `bfm` instead of `biome-fm`.

bfm() {
    local tmp
    tmp=$(mktemp)
    BIOME_LAST_DIR_FILE="$tmp" biome-fm "$@"
    if [ -s "$tmp" ]; then
        # shellcheck disable=SC2164
        cd -- "$(cat "$tmp")"
    fi
    rm -f "$tmp"
}
