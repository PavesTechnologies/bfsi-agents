def debug_node(name, fn):
    def wrapper(state):
        print(f"\n--- NODE: {name} ---")
        print("Incoming state keys:", list(state.keys()))
        out = fn(state)
        print("Outgoing update:", out)
        return out
    return wrapper
