from consts.paths import SYSTEM


__all__ = "Binder"


if SYSTEM == "Windows":
    from global_hotkeys import start_checking_hotkeys, stop_checking_hotkeys, register_hotkeys

    class Binder:
        def __init__(self):
            self.bindings = []

        def bind(self, *key_seq, action):
            self.bindings.append(([i.lower() for i in key_seq], None, action))

        def start(self):
            register_hotkeys(self.bindings)
            start_checking_hotkeys()

        def stop(self):
            stop_checking_hotkeys()
else:
    from bindglobal import BindGlobal

    class Binder:
        def __init__(self):
            self.bg = BindGlobal()

        def bind(self, *key_seq, action):
            self.bg.gbind("<{}>".format("-".join(key_seq)), lambda _: action())

        def start(self):
            pass

        def stop(self):
            self.bg.stop()