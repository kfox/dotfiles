override_git_prompt_colors() {
  GIT_PROMPT_THEME_NAME="Custom"

  GIT_PROMPT_MASTER_BRANCH="${Yellow}"
  GIT_PROMPT_UPSTREAM=" (${DimBlue}_UPSTREAM_${ResetColor})"

  GIT_PROMPT_START=$STARTPROMPT
  GIT_PROMPT_END=$ENDPROMPT

  GIT_PROMPT_STAGED=" ${Yellow}●${DimWhite}·${ResetColor}"
  GIT_PROMPT_CHANGED=" ${Blue}Δ${DimWhite}·${ResetColor}"
  GIT_PROMPT_CONFLICTS=" ${Red}✖${DimWhite}·${ResetColor}"
  GIT_PROMPT_UNTRACKED=" ${BoldCyan}?${DimWhite}·${ResetColor}"
  GIT_PROMPT_STASHED=" ${BoldMagenta}⚑${DimWhite}·${ResetColor}"
  GIT_PROMPT_CLEAN=" ${Green}✔${ResetColor}"
  GIT_PROMPT_SEPARATOR=" ${DimWhite}»${ResetColor}"
  GIT_PROMPT_PREFIX="${DimWhite}${ResetColor} "
  GIT_PROMPT_SUFFIX=""
  GIT_PROMPT_SYMBOLS_NO_REMOTE_TRACKING="${BrightYellow}✭${ResetColor}"

  GIT_PROMPT_MASTER_BRANCHES="@(master|main)"
}

reload_git_prompt_colors "Custom"
