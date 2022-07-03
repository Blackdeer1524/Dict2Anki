from typing import Any


def validate_json(checking_scheme: dict[Any, Any],
                  default_scheme: dict[Any, Any]):
    check_queue: list[tuple[dict[Any, Any], dict[Any, Any]], ...] = [(checking_scheme, default_scheme)]
    for (checking_part, default_part) in check_queue:
        checking_keys = list(checking_part)
        default_keys = set(default_part)

        for c_key in checking_keys:
            if c_key in default_keys:
                if type(checking_part[c_key]) != type(default_part[c_key]):
                    checking_part[c_key] = default_part[c_key]
                elif isinstance(checking_part[c_key], dict):
                    check_queue.append((checking_part[c_key], default_part[c_key]))
                default_keys.remove(c_key)
            else:
                checking_part.pop(c_key)
        del checking_keys

        for d_key in default_keys:
            c_value = checking_part.get(d_key)
            d_value = default_part[d_key]
            if isinstance(d_value, dict) and isinstance(c_value, dict):
                check_queue.append((c_value, d_value))
            elif type(c_value) != type(default_part[d_key]):
                checking_part[d_key] = default_part[d_key]
    return None


def remove_empty_keys(data: dict):
    keys = list(data.keys())
    for key in keys:
        if isinstance((value := data[key]), dict):
            remove_empty_keys(value)
        elif not value:
            data.pop(key)
