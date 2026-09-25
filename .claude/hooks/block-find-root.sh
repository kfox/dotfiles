#!/usr/bin/env bash
# PreToolUse(Bash) hook: block any "find" invocation rooted at filesystem root
# (e.g. "find /", "sudo find / -name foo"). Never allow it.
cmd=$(jq -r '.tool_input.command // empty')

if [ -n "$cmd" ] && echo "$cmd" | grep -Eq '\bfind\b[^|;&]*[[:space:]]/([[:space:]]|$)'; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked: find rooted at filesystem root (find /) is never allowed. Scope find to a specific directory, e.g. find . or find /path/to/dir."}}
EOF
fi
