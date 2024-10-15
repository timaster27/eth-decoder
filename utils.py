def unpack_list(lst):
    res = []
    for i in lst:
        if isinstance(i, bytes):
            res.append('0x' + ''.join(c[2:] for c in map(hex, list(i))))
        elif isinstance(i, list):
            res.append(unpack_list(i))
        elif isinstance(i, dict):
            res.append(unpack_dict(i))
        else:
            res.append(i)
    return res


def unpack_dict(d):
    res = dict()
    for k, v in d.items():
        if isinstance(v, bytes):
            res[k] = '0x' + ''.join(c[2:] for c in map(hex, list(v)))
        elif isinstance(v, list):
            res[k] = unpack_list(v)
        elif isinstance(v, dict):
            res[k] = unpack_dict(v)
        else:
            res[k] = v
    return res


def create_buttons(lst, func):
    buttons = []
    for i, k in enumerate(lst):
        if i % 2 == 0:
            buttons.append([func(k, k)])
        else:
            buttons[-1].append(func(k, k))
    return buttons
