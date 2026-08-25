#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="${0:A:h}"
APP_PATH="${SCRIPT_DIR}/Boujoy知识库.app"
SOURCE_PATH="${SCRIPT_DIR}/macos-launcher.applescript"
DESKTOP_APP="${HOME}/Desktop/Boujoy知识库.app"
BUILD_DIR="$(/usr/bin/mktemp -d "/tmp/boujoy-app-build-${UID}.XXXXXX")"
TEMP_APP="${BUILD_DIR}/Boujoy知识库.app"
PREVIOUS_APP="${BUILD_DIR}/previous.app"

cleanup_build() {
  /bin/rm -rf -- "${BUILD_DIR}"
}

trap cleanup_build EXIT

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "此安装器仅用于 macOS。" >&2
  exit 2
fi

if [[ ! -f "${SOURCE_PATH}" ]]; then
  echo "找不到 AppleScript 源文件：${SOURCE_PATH}" >&2
  exit 1
fi

if [[ -e "${DESKTOP_APP}" && ! -L "${DESKTOP_APP}" ]]; then
  echo "桌面已存在非符号链接项目：${DESKTOP_APP}" >&2
  echo "为避免覆盖，请先手动改名或移动它。" >&2
  exit 1
fi

/usr/bin/osacompile -o "${TEMP_APP}" "${SOURCE_PATH}"
/usr/bin/codesign --force --deep --sign - "${TEMP_APP}"
/usr/bin/codesign --verify --deep --strict --verbose=2 "${TEMP_APP}"

if [[ -e "${APP_PATH}" || -L "${APP_PATH}" ]]; then
  /bin/mv "${APP_PATH}" "${PREVIOUS_APP}"
fi
if ! /bin/mv "${TEMP_APP}" "${APP_PATH}"; then
  if [[ -e "${PREVIOUS_APP}" ]]; then
    /bin/mv "${PREVIOUS_APP}" "${APP_PATH}"
  fi
  echo "无法替换 Boujoy知识库 App，已保留原版本。" >&2
  exit 1
fi

if [[ -L "${DESKTOP_APP}" ]]; then
  current_target="$(/usr/bin/readlink "${DESKTOP_APP}")"
  if [[ "${current_target}" != "${APP_PATH}" ]]; then
    /bin/ln -sfn "${APP_PATH}" "${DESKTOP_APP}"
  fi
else
  /bin/ln -s "${APP_PATH}" "${DESKTOP_APP}"
fi

/usr/bin/codesign --verify --deep --strict --verbose=2 "${APP_PATH}"

echo "Boujoy知识库已安装到桌面：${DESKTOP_APP}"
