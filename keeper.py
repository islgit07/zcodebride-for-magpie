# zcode-bridge-keeper
# magpie 的 zcode-bridge provider 守护: 哪个 agent 切到 zcode-bridge/* 就拉起
# 桥接, 全部切走(且无近期请求)就关掉; 发现 zcode-bridge 请求 401(JWT 过期)就
# 自动重启换新 JWT。codex 配置指向直连模式时, 可选地顺带管理 responses 代理。
#
# Windows 专用 (tasklist/taskkill/netstat)。全部路径可用环境变量覆盖:
#   ZCODE_BRIDGE_EXE   桥接程序路径   (默认 ~/tools/zcode-bridge/zcode-bridge.exe)
#   MAGPIE_CONFIG_DIR  magpie 配置目录 (默认 ~/.config/magpie)
#   CODEX_CONFIG       codex 配置文件  (默认 ~/.codex/config.toml)
#   RESPONSES_PROXY_JS responses 代理脚本路径 (不设则不管代理)
#   KEEPER_LOG         日志文件       (默认本脚本目录下 keeper.log)
#
# 开机自启: 建一个启动文件夹的 .vbs (见 README), 隐藏窗口运行本脚本。
# 由 ZCode (GLM-5.3-Flash) 编写。
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")

MAGPIE_DIR = os.environ.get("MAGPIE_CONFIG_DIR", os.path.join(HOME, ".config", "magpie"))
APPLIED = os.path.join(MAGPIE_DIR, "applied.json")
USAGE = os.path.join(MAGPIE_DIR, "usage.jsonl")
BRIDGE_EXE = os.environ.get("ZCODE_BRIDGE_EXE", os.path.join(HOME, "tools", "zcode-bridge", "zcode-bridge.exe"))
BRIDGE_DIR = os.path.dirname(BRIDGE_EXE)
CODEX_CONFIG = os.environ.get("CODEX_CONFIG", os.path.join(HOME, ".codex", "config.toml"))
PROXY_JS = os.environ.get("RESPONSES_PROXY_JS", "")  # 不设则不管代理
LOG = os.environ.get("KEEPER_LOG", os.path.join(HERE, "keeper.log"))

PROVIDER_PREFIX = "zcode-bridge/"
PROXY_PORT_MARK = "127.0.0.1:20132"

POLL_SECONDS = 2
GRACE_SECONDS = 600        # 没有任何 agent 选择 zcode-bridge 后, 有请求记录则多留 10 分钟
RESTART_COOLDOWN = 300     # 401 重启的最小间隔, 防止死循环

log_f = None
def log(msg):
    global log_f
    try:
        if log_f is None:
            log_f = open(LOG, "a", encoding="utf-8", buffering=1)
        log_f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + msg + "\n")
    except Exception:
        pass


NO_WINDOW = 0x08000000  # pythonw 无控制台, 不加它每个 tasklist/netstat 都会闪黑窗


def run_hidden(args, timeout=15):
    return subprocess.run(args, capture_output=True, text=True,
                          timeout=timeout, creationflags=NO_WINDOW)


def spawn(args, cwd=None, out=None):
    # DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP: keeper 自己挂掉也不带走孩子
    flags = 0x00000008 | 0x00000200
    target = out if out else subprocess.DEVNULL
    return subprocess.Popen(args, cwd=cwd, creationflags=flags,
                            stdout=target, stderr=target,
                            close_fds=True)


def pid_of(image):
    """按映像名找 PID; 没有则返回 None"""
    try:
        out = run_hidden(
            ["tasklist", "/FI", "IMAGENAME eq " + image, "/FO", "CSV", "/NH"],
            timeout=10,
        ).stdout
        if out:
            for line in out.splitlines():
                if image.lower() in line.lower():
                    return int(line.split('","')[1])
    except Exception:
        pass
    return None


def port_pids(port_mark):
    """netstat 里监听 port_mark 的 PID 集合; 查不清返回 None"""
    try:
        out = run_hidden(["netstat", "-ano"]).stdout
    except Exception:
        return None
    if not out:
        return None
    pids = set()
    for line in out.splitlines():
        if port_mark in line and "LISTENING" in line.upper():
            parts = line.split()
            if parts:
                pids.add(parts[-1])
    return pids


def start_bridge():
    if pid_of(os.path.basename(BRIDGE_EXE)):
        return
    log("bridge: starting")
    out = open(os.path.join(BRIDGE_DIR, "bridge-keeper.out"), "a", encoding="utf-8")
    spawn([BRIDGE_EXE], cwd=BRIDGE_DIR, out=out)


def stop_bridge():
    if not pid_of(os.path.basename(BRIDGE_EXE)):
        return
    log("bridge: stopping")
    run_hidden(["taskkill", "/F", "/IM", os.path.basename(BRIDGE_EXE)])


def start_proxy():
    if not PROXY_JS:
        return
    pids = port_pids(PROXY_PORT_MARK)
    if pids:
        return
    log("proxy: starting")
    spawn(["node", PROXY_JS])


def stop_proxy():
    if not PROXY_JS:
        return
    pids = port_pids(PROXY_PORT_MARK)
    if not pids:
        return
    for pid in pids:
        log("proxy: stopping pid " + pid)
        run_hidden(["taskkill", "/F", "/PID", pid])


def bridge_selected():
    """applied.json 里任一 agent 的模型是否为 zcode-bridge/*"""
    try:
        with open(APPLIED, encoding="utf-8") as f:
            applied = json.load(f)
    except Exception:
        return False
    for agent, cfg in applied.items():
        if isinstance(cfg, dict):
            model = cfg.get("fields", {}).get("model", "")
            if isinstance(model, str) and model.startswith(PROVIDER_PREFIX):
                return True
    return False


def proxy_wanted():
    """codex 配置是否指向 20132 直连模式"""
    try:
        with open(CODEX_CONFIG, encoding="utf-8") as f:
            return PROXY_PORT_MARK in f.read()
    except Exception:
        return False


def parse_ts(s):
    """'2026-11-14T02:33:57.4397765+08:00' -> epoch 秒"""
    if not s:
        return None
    try:
        from datetime import datetime, timezone, timedelta
        base, _, off = s[:-1].rpartition("+") if "+" in s else (s, "", "")
        hh = int(off[:2]) if off else 0
        mm = int(off[3:5]) if len(off) >= 5 else 0
        dt = datetime.strptime(base[:26].rstrip("."), "%Y-%m-%dT%H:%M:%S.%f") if "." in base else \
             datetime.strptime(base[:19], "%Y-%m-%dT%H:%M:%S")
        return dt.replace(tzinfo=timezone(timedelta(hours=hh, minutes=mm))).timestamp()
    except Exception:
        return time.time()  # 解析不了就当是现在, 宁可保守


class UsageTail:
    """增量读 usage.jsonl, 记录 zcode-bridge 最后请求时间与 401 时间"""
    def __init__(self):
        self.pos = 0
        self.last_req = 0.0
        self.last_401 = 0.0

    def poll(self):
        try:
            size = os.path.getsize(USAGE)
            if size < self.pos:  # 日志轮转/重写
                self.pos = 0
            if size == self.pos:
                return
            with open(USAGE, encoding="utf-8", errors="replace") as f:
                f.seek(self.pos)
                data = f.read()
                self.pos = f.tell()
        except Exception:
            return
        for line in data.splitlines():
            if '"zcode-bridge"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts = parse_ts(d.get("t"))
            if ts:
                self.last_req = max(self.last_req, ts)
                if d.get("status") == 401:
                    self.last_401 = max(self.last_401, ts)


def main():
    log("keeper started (pid %d)" % os.getpid())
    usage = UsageTail()
    last_restart = 0.0
    while True:
        try:
            usage.poll()
            selected = bridge_selected()
            fresh = (time.time() - usage.last_req) < GRACE_SECONDS
            want_bridge = selected or fresh
            now = time.time()

            if want_bridge:
                start_bridge()
            else:
                stop_bridge()

            # 注意: 不要因为 401 就重启桥接 —— 账号环模式下重启不能换票,
            # 只会杀掉在途的流式响应、清空轮换状态, 把单次 401 放大成连环事故。
            # 401 一般是并发槽瞬间被占(账号环自会冷却重试), 等 it 过去即可。
            if usage.last_401 > last_restart:
                log("bridge: 401 seen (no action; rotation will retry)")
                last_restart = usage.last_401

            if PROXY_JS:
                if proxy_wanted():
                    start_proxy()
                else:
                    stop_proxy()
        except Exception as e:
            import traceback
            log("error: %s\n%s" % (e, traceback.format_exc()))
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
