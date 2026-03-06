def calculate_mapping(seed):
    state = seed

    def next_rand(max_val):
        nonlocal state
        state = (state * 6364136223846793005 + 1) & 0xFFFFFFFFFFFFFFFF
        return (state >> 33) % max_val

    pool = list(range(256))
    for i in range(255, 0, -1):
        j = next_rand(i + 1)
        pool[i], pool[j] = pool[j], pool[i]

    return {
        "拟合": pool[0], "矩阵": pool[1], "渲染": pool[2],
        "映射": pool[3], "铣削": pool[4], "寻路": pool[5], "归一": pool[6]
    }

def assemble_chinese(source_code, seed):
    ops_map = calculate_mapping(seed)
    reg_map = {"青龙": 0, "白虎": 1, "朱雀": 2, "玄武": 3}
    bytecode = []

    for line in source_code.strip().split('\n'):
        line = line.split('#')[0].strip()
        if not line: continue
        parts = line.replace(',', ' ').split()
        cmd = parts[0]

        if cmd == "拟合":
            bytecode.extend([ops_map["拟合"], reg_map[parts[1]], int(parts[2])])
        elif cmd == "矩阵":
            bytecode.extend([ops_map["矩阵"], reg_map[parts[1]], int(parts[2])])
        elif cmd == "渲染":
            bytecode.extend([ops_map["渲染"], reg_map[parts[1]], reg_map[parts[2]]])
        elif cmd == "映射":
            bytecode.extend([ops_map["映射"], reg_map[parts[1]], reg_map[parts[2]]])
        elif cmd == "铣削":
            bytecode.append(ops_map["铣削"])
        elif cmd == "寻路":
            bytecode.append(ops_map["寻路"])
        elif cmd == "归一":
            bytecode.extend([ops_map["归一"], reg_map[parts[1]]])

    return bytes(bytecode)