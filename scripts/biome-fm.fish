# Fish wrapper for biome-fm — cd-on-exit (lf/yazi-style)
# Place this file in ~/.config/fish/functions/ (auto-loaded)
# or source it manually: source /path/to/biome-fm.fish

function bfm
    set tmp (mktemp)
    BIOME_LAST_DIR_FILE="$tmp" biome-fm $argv
    if test -s "$tmp"
        cd -- (cat $tmp)
    end
    rm -f $tmp
end
