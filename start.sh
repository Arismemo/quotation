#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="${SCRIPT_DIR}"

VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-}"
LOGFILE="${PROJECT_ROOT}/app.log"
PIDFILE="${PROJECT_ROOT}/.uvicorn.pid"

info()  { echo -e "[INFO] $*"; }
warn()  { echo -e "[WARN] $*" >&2; }
err()   { echo -e "[ERR ] $*" >&2; }

is_running() {
  if [[ -f "${PIDFILE}" ]]; then
    local pid
    pid=$(cat "${PIDFILE}" || true)
    if [[ -n "${pid:-}" ]] && ps -p "${pid}" >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

install_deps() {
  cd "${PROJECT_ROOT}"
  if [[ ! -d "${VENV_DIR}" ]]; then
    info "创建虚拟环境 ${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  fi
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  pip install -U pip wheel >/dev/null
  if [[ -f requirements.txt ]]; then
    info "安装依赖"
    pip install -r requirements.txt
  fi
}

ensure_dirs() {
  mkdir -p "${PROJECT_ROOT}/app/static/uploads"
}

init_db() {
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  "${PYTHON_BIN}" - <<'PY'
from app.db.session import init_db
init_db()
print("DB initialized")
PY
}

start_bg() {
  if is_running; then
    info "已在运行 (PID=$(cat "${PIDFILE}"))"
    return 0
  fi
  install_deps
  ensure_dirs
  # 可选：提前初始化数据库（应用启动时也会自动执行）
  # init_db
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  EXTRA_ARGS=""
  if [[ -n "${RELOAD}" ]]; then EXTRA_ARGS="--reload"; fi
  nohup "${PYTHON_BIN}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" ${EXTRA_ARGS} >> "${LOGFILE}" 2>&1 &
  echo $! > "${PIDFILE}"
  sleep 1
  if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    info "服务已启动: http://localhost:${PORT}"
  else
    warn "服务已启动但健康检查失败，查看日志: ${LOGFILE}"
  fi
}

start_dev() {
  export RELOAD=true
  install_deps
  ensure_dirs
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  exec "${PYTHON_BIN}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
}

stop_srv() {
  if is_running; then
    local pid
    pid=$(cat "${PIDFILE}")
    info "停止服务 PID=${pid}"
    kill "${pid}" 2>/dev/null || true
    sleep 1
    if ps -p "${pid}" >/dev/null 2>&1; then
      warn "进程未退出，尝试强制结束"
      kill -9 "${pid}" 2>/dev/null || true
    fi
    rm -f "${PIDFILE}"
    info "已停止"
  else
    warn "未检测到运行中的服务"
  fi
}

status_srv() {
  if is_running; then
    echo "running (PID=$(cat \"${PIDFILE}\")) on port ${PORT}"
  else
    echo "stopped"
  fi
}

usage() {
  cat <<EOF
用法: $(basename "$0") [命令]

命令:
  install      创建虚拟环境并安装依赖
  start        后台启动服务 (默认端口: ${PORT})
  stop         停止后台服务
  restart      重启后台服务
  status       显示服务状态
  dev          前台开发模式(自动重载)

环境变量:
  PYTHON_BIN   指定 Python 解释器 (默认: python3)
  HOST         绑定地址 (默认: 0.0.0.0)
  PORT         端口 (默认: 8000)
  RELOAD       非空则启用 --reload
EOF
}

case "${1:-}" in
  install) install_deps ;;
  start) start_bg ;;
  stop) stop_srv ;;
  restart) stop_srv || true; start_bg ;;
  status) status_srv ;;
  dev) start_dev ;;
  ""|-h|--help|help) usage ;;
  *) err "未知命令: $1"; usage; exit 1 ;;
esac


