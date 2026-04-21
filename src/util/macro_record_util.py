import ctypes
import ctypes.wintypes
import gc
import logging
import threading
import time
from collections import deque

from typing import Set

logger = logging.getLogger(__name__)

# =========================
# WinAPI
# =========================

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 声明函数签名
user32.SetWindowsHookExW.argtypes = (
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint
)
user32.SetWindowsHookExW.restype = ctypes.c_void_p

user32.CallNextHookEx.argtypes = (
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_ulonglong,
    ctypes.c_void_p
)
user32.CallNextHookEx.restype = ctypes.c_longlong

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208

# =========================
# 全局唯一 Hook 类型
# =========================

HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    ctypes.c_int,
    ctypes.c_ulonglong,
    ctypes.c_void_p
)


# =========================
# Hook结构体
# =========================

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.c_uint),
        ("scanCode", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("time", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


# =========================
# 默认键盘白名单
# =========================

def build_default_key_set() -> Set[int]:
    keys = set()

    for i in range(0x41, 0x5B):  # A-Z
        keys.add(i)

    for i in range(0x30, 0x3A):  # 0-9
        keys.add(i)

    for i in range(0x60, 0x6A):  # 小键盘
        keys.add(i)

    keys.update([
        0xBD, 0xBB, 0xDB, 0xDD, 0xDC,
        0xBA, 0xDE, 0xBC, 0xBE, 0xBF,
        0x20  # space
    ])

    return keys


# =========================
# Recorder
# =========================

class MacroRecorder:
    def __init__(
            self,
            enable_mouse=False,
            keyboard_whitelist=None,
            debug_print=False
    ):
        self.events = deque()
        self.start_time = 0
        self.recording = False
        self.trigger_wait = True

        self.kb_hook = None
        self.mouse_hook = None

        self.enable_mouse = enable_mouse
        self.debug_print = debug_print

        self.keyboard_whitelist = keyboard_whitelist or build_default_key_set()

        # 性能缓存
        self._perf = time.perf_counter
        self._append = self.events.append
        self._kb_struct = ctypes.POINTER(KBDLLHOOKSTRUCT)

        # 缓存WinAPI函数引用，减少属性查找开销
        self._CallNextHookEx = user32.CallNextHookEx
        self._cast = ctypes.cast

        # 按键状态跟踪（用于去重）
        self._key_states = {}  # 键值 -> bool (True=按下, False=弹起)

    # =========================
    # 记录事件
    # =========================

    def _add_event(self, vk, is_down):
        ms = int((self._perf() - self.start_time) * 1000)
        self._append((ms, vk, is_down))

        if self.debug_print:
            logger.info(f"REC vk={vk} down={is_down}")

    # =========================
    # Keyboard Hook（先传递消息再处理）
    # =========================

    def keyboard_proc(self, nCode, wParam, lParam):
        if nCode < 0 or not self.recording:
            return self._CallNextHookEx(None, nCode, wParam, lParam)

        # 先让消息继续传递，减少游戏延迟
        result = self._CallNextHookEx(None, nCode, wParam, lParam)

        # 然后处理录制逻辑
        kb = self._cast(lParam, self._kb_struct).contents
        vk = kb.vkCode

        if vk in self.keyboard_whitelist:
            is_down = (wParam == WM_KEYDOWN)
            # 只记录状态变化（去重）
            if self._key_states.get(vk) != is_down:
                self._key_states[vk] = is_down
                self._add_event(vk, is_down)

        return result

    # =========================
    # Mouse Hook
    # =========================

    def mouse_proc(self, nCode, wParam, lParam):
        if not self.enable_mouse or nCode < 0 or not self.recording:
            return self._CallNextHookEx(None, nCode, wParam, lParam)

        # 先传递消息
        result = self._CallNextHookEx(None, nCode, wParam, lParam)

        vk = None
        is_down = True

        if wParam == WM_LBUTTONDOWN:
            vk = "MOUSE_LEFT"
        elif wParam == WM_LBUTTONUP:
            vk = "MOUSE_LEFT"
            is_down = False
        elif wParam == WM_RBUTTONDOWN:
            vk = "MOUSE_RIGHT"
        elif wParam == WM_RBUTTONUP:
            vk = "MOUSE_RIGHT"
            is_down = False
        elif wParam == WM_MBUTTONDOWN:
            vk = "MOUSE_MIDDLE"
        elif wParam == WM_MBUTTONUP:
            vk = "MOUSE_MIDDLE"
            is_down = False

        if vk:
            # 只记录状态变化（去重）
            if self._key_states.get(vk) != is_down:
                self._key_states[vk] = is_down
                self._add_event(vk, is_down)

        return result

    # =========================
    # Hook安装
    # =========================

    def start_hook(self):
        if self.kb_hook:
            return

        self._kb_func = HOOKPROC(self.keyboard_proc)
        self._mouse_func = HOOKPROC(self.mouse_proc)

        self.kb_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._kb_func, None, 0)

        if self.enable_mouse:
            self.mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_func, None, 0)

        if not self.kb_hook:
            raise RuntimeError("键盘Hook失败")

    def stop_hook(self):
        if self.kb_hook:
            user32.UnhookWindowsHookEx(self.kb_hook)
            self.kb_hook = None

        if self.mouse_hook:
            user32.UnhookWindowsHookEx(self.mouse_hook)
            self.mouse_hook = None

    # =========================
    # 生命周期
    # =========================

    def start_record(self):
        self.events.clear()
        self._key_states.clear()  # 清空按键状态
        self.start_time = self._perf()
        self.recording = True

        gc.disable()
        gc.collect()

    def stop_record(self):
        self.recording = False
        self.trigger_wait = False
        gc.enable()
        logger.info(f"录制结束，共 {len(self.events)} 条事件")

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for ms, vk, is_down in self.events:
                f.write(f"{ms},{vk},{1 if is_down else 0}\n")

        logger.info(f"保存完成: {path}")


# =========================
# ESC检测（优化：降低线程优先级）
# =========================

def start_esc(recorder):
    def loop():
        # 降低ESC检测线程优先级，减少对游戏的影响
        try:
            kernel32.SetThreadPriority(
                kernel32.GetCurrentThread(),
                0xFFFFFFFE  # THREAD_PRIORITY_LOWEST = -2
            )
        except:
            pass

        while True:
            if user32.GetAsyncKeyState(0x1B) & 0x8000:
                logger.info("ESC触发，停止并保存")
                recorder.stop_record()
                return
            time.sleep(0.1)  # ✔ 减少调度抖动

    threading.Thread(target=loop, daemon=True).start()


# =========================
# message loop（优化：使用MsgWaitForMultipleObjects降低CPU）
# =========================

def message_loop(recorder):
    msg = ctypes.wintypes.MSG()

    # 使用 MsgWaitForMultipleObjects 实现零CPU等待
    while recorder.recording:
        # 等待消息，超时50ms，允许定期检查recording状态
        ret = user32.MsgWaitForMultipleObjects(0, None, False, 50, 0x000000FF)  # QS_ALLINPUT

        if ret == 0xFFFFFFFF:  # 错误
            break

        # 处理所有待处理消息
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


# =========================
# main
# =========================

def run(path: str, hwnd=None, points=None):
    recorder = MacroRecorder(enable_mouse=False, debug_print=False)
    from .macro_replay_util import TriggerController
    trigger = TriggerController(hwnd, points)

    try:
        recorder.start_hook()
        start_esc(recorder)

        logger.info("准备就绪，等待开始")
        wait_result = trigger.wait_color(should_stop=lambda: not recorder.trigger_wait)

        if wait_result:
            logger.info("开始录制（按ESC保存退出）")
            recorder.start_record()

            message_loop(recorder)

            recorder.stop_hook()
            recorder.save(path)
            return True
        else:
            logger.info("录制开始前退出，无文件生成")
            recorder.stop_hook()
            return False
    finally:
        recorder.recording = False
        recorder.trigger_wait = False
        recorder.stop_hook()


if __name__ == "__main__":
    from src.util import file_util

    path = file_util.get_assets_macro_SoarToTheBeat("05_星云漫游_《致那暖明黄金》_困难.txt")

    run(path)
