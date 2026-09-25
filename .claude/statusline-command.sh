#!/usr/bin/env bash
# Claude Code statusLine command
# Left: where the session is (project, branch, open PR; branch is red in the primary checkout)
# Right: how the session is going (model, effort, context, cost, prompt cache)
# Healthy readings are dim; yellow wants attention soon, red wants it now.

# Thresholds
CTX_WARN=30 CTX_BAD=50        # context used, percent
BURN_WARN=15 BURN_BAD=30      # session cost, dollars per hour
CACHE_WARN_MINS=5             # minutes before the prompt cache goes cold
# Columns Claude Code's own edge spacing takes; raise it if the right side wraps
RIGHT_MARGIN=4

input=$(cat)

DIM=$'\e[2m' RED=$'\e[31;01m' YELLOW=$'\e[33m' GREEN=$'\e[32m' RESET=$'\e[0m'

# One jq pass; \x1f keeps empty fields in place where a tab would collapse them
IFS=$'\x1f' read -r cwd project_dir model effort fast used_pct cost duration_ms \
  cache_warm cache_seen cache_expires recache_cold misses miss_cause \
  pr_number pr_url pr_state pr_kind < <(
  echo "$input" | jq -r '[
    (.workspace.current_dir // .cwd // ""),
    (.workspace.project_dir // ""),
    (.model.display_name // ""),
    (.effort.level // ""),
    (.fast_mode // false),
    (.context_window.used_percentage // ""),
    (.cost.total_cost_usd // ""),
    (.cost.total_duration_ms // 0),
    (.prompt_cache.warm // ""),
    (.prompt_cache.caching_observed // false),
    (.prompt_cache.expires_at // ""),
    (.prompt_cache.recache_tokens_if_cold // ""),
    (.prompt_cache.misses // 0),
    ((.prompt_cache.last_miss_cause.causes // []) | join(",")),
    (.pr.number // ""),
    (.pr.url // ""),
    (.pr.review_state // ""),
    (.pr.kind // "")
  ] | map(tostring) | join("\u001f")'
)

# Terminal columns a styled string occupies: colors and links take none, ⚡ takes two
visible_width() {
  local plain chars wide
  plain=$(printf '%s' "$1" | sed -e $'s/\e\\[[0-9;]*m//g' -e $'s/\e]8;;[^\a]*\a//g')
  chars=$(printf '%s' "$plain" | LC_ALL=en_US.UTF-8 wc -m)
  wide=$(printf '%s' "$plain" | grep -o '⚡' | wc -l)
  echo $(( chars + wide ))
}

# Pick dim, yellow or red for a whole-number reading against two thresholds
severity() {
  if [ "$1" -ge "$3" ]; then
    printf '%s' "$RED"
  elif [ "$1" -ge "$2" ]; then
    printf '%s' "$YELLOW"
  else
    printf '%s' "$DIM"
  fi
}

# --- Left: project, branch and PR ---

git_dir=$(git -C "$cwd" rev-parse --path-format=absolute --git-dir 2>/dev/null)
if [ -n "$git_dir" ]; then
  common_dir=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir)
  project=$(basename "$(dirname "$common_dir")")
  branch=$(git -C "$cwd" branch --show-current)
  [ -z "$branch" ] && branch=$(git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
  # A linked worktree has its own git dir; the primary checkout's is the common one
  if [ "$git_dir" = "$common_dir" ]; then
    branch_color=$RED
  else
    branch_color=$GREEN
  fi
  left="$project  ${branch_color}⎇ ${branch}${RESET}"
else
  left=$(basename "${project_dir:-$cwd}")
fi

# Open PR, clickable (OSC 8): red when changes are requested, green once approved
if [ -n "$pr_number" ]; then
  case "$pr_state" in
    changes_requested) pr_color=$RED ;;
    approved) pr_color=$GREEN ;;
    *) pr_color=$DIM ;;
  esac
  pr_sigil="#"
  [ "$pr_kind" = "mr" ] && pr_sigil="!"
  pr_label="PR${pr_sigil}${pr_number}"
  [ -n "$pr_url" ] && pr_label=$'\e]8;;'"${pr_url}"$'\a'"${pr_label}"$'\e]8;;\a'
  left+="  ${pr_color}${pr_label}${RESET}"
fi

# --- Right: session health ---

segments=()

# Max effort and fast mode each multiply what a turn costs
model_seg="${DIM}${model}${RESET}"
if [ "$effort" = "max" ]; then
  model_seg+=" ${YELLOW}${effort}${RESET}"
elif [ -n "$effort" ]; then
  model_seg+=" ${DIM}${effort}${RESET}"
fi
[ "$fast" = "true" ] && model_seg+=" ${YELLOW}⚡${RESET}"
[ -n "$model$effort" ] && segments+=("$model_seg")

if [ -n "$used_pct" ]; then
  pct=$(printf "%.0f" "$used_pct")
  segments+=("$(severity "$pct" "$CTX_WARN" "$CTX_BAD")ctx ${pct}%${RESET}")
fi

# Session cost covers every API call in the session, subagents included.
# Burn rate waits five minutes, before which it is mostly noise.
if [ -n "$cost" ]; then
  cost_seg=$(printf '%s$%.2f%s' "$DIM" "$cost" "$RESET")
  if [ "${duration_ms%.*}" -ge 300000 ]; then
    burn=$(awk -v c="$cost" -v ms="$duration_ms" 'BEGIN { printf "%.2f", c / (ms / 3600000) }')
    cost_seg+="${DIM} · ${RESET}$(severity "${burn%.*}" "$BURN_WARN" "$BURN_BAD")\$${burn}/h${RESET}"
  fi
  segments+=("$cost_seg")
fi

# Cache countdown: minutes until the cached prefix goes cold.
# Once cold, show what the next prompt will re-cache at full price.
mins_left=-1
if [ "$cache_warm" = "true" ] && [ -n "$cache_expires" ]; then
  mins_left=$(( (${cache_expires%.*} - $(date +%s)) / 60 ))
fi
if [ "$mins_left" -ge "$CACHE_WARN_MINS" ]; then
  segments+=("${DIM}cache ${mins_left}m${RESET}")
elif [ "$mins_left" -ge 0 ]; then
  segments+=("${YELLOW}cache ${mins_left}m${RESET}")
elif [ "$cache_seen" = "true" ]; then
  cold_seg="cache cold"
  if [ -n "$recache_cold" ]; then
    cold_seg+=$(awk -v t="$recache_cold" 'BEGIN { printf " %dk", t / 1000 }')
  fi
  segments+=("${RED}${cold_seg}${RESET}")
fi

if [ "${misses%.*}" -gt 0 ]; then
  miss_seg="$misses miss"
  [ "$misses" -gt 1 ] && miss_seg+="es"
  [ -n "$miss_cause" ] && miss_seg+=" ($miss_cause)"
  segments+=("${RED}${miss_seg}${RESET}")
fi

right=""
for seg in "${segments[@]}"; do
  [ -n "$right" ] && right+="  "
  right+="$seg"
done

# --- Layout: left-justify the project, right-justify the rest ---

gap=$(( ${COLUMNS:-0} - RIGHT_MARGIN - $(visible_width "$left") - $(visible_width "$right") ))
[ "$gap" -lt 2 ] && gap=2
printf "%s%*s%s" "$left" "$gap" "" "$right"
