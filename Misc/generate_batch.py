"""
Generator and Verifier for MechaCode Python Tasks Batch
"""
import json
import codecs
import string
import copy
from typing import List, Dict, Any

# =====================================================================
# SOLVERS FOR MODULE 1: Zadania do Samokontroli
# =====================================================================

def solve_1_1(input_text: str) -> str:
    """Task 1.1: Liczby zespolone i operacje arytmetyczne"""
    parts = input_text.strip().split()
    if not parts:
        return ""
    def parse_num(s):
        try:
            val = float(s)
            if val.is_integer() and '.' not in s:
                return int(s)
            return val
        except ValueError:
            return float(s)
    re_val = parse_num(parts[0])
    im_val = parse_num(parts[1])
    k_val = parse_num(parts[2])
    z1 = complex(re_val, im_val)
    z2 = z1 * k_val
    return f"{z1}\n{type(z1)}\n{z2}\n{type(z2)}"

def solve_1_2(input_text: str) -> str:
    """Task 1.2: Wielokrotne potęgowanie operatorem przypisania (**=)"""
    parts = input_text.strip().split()
    if not parts:
        return ""
    z = int(parts[0])
    n = int(parts[1])
    for _ in range(n):
        z **= 2
    return str(z)

def solve_1_3(input_text: str) -> str:
    """Task 1.3: Referencje list: modyfikacja w miejscu a nowy obiekt"""
    lines = input_text.splitlines()
    line1 = lines[0].strip() if len(lines) > 0 else ""
    line2 = lines[1].strip() if len(lines) > 1 else ""
    line3 = lines[2].strip() if len(lines) > 2 else ""

    a = [int(v) for v in line1.split()] if line1 else []
    b = a
    x = int(line2)
    a.append(x)
    out = [
        f"a: {a}",
        f"b: {b}"
    ]
    a = [int(v) for v in line3.split()] if line3 else []
    out.append(f"a: {a}")
    out.append(f"b: {b}")
    return "\n".join(out)

def solve_1_4(input_text: str) -> str:
    """Task 1.4: Współdzielenie referencji w słownikach"""
    lines = [l.strip() for l in input_text.strip().splitlines() if l.strip()]
    if not lines:
        return ""
    n = int(lines[0])
    d1 = {}
    idx = 1
    for _ in range(n):
        k, v = lines[idx].split(maxsplit=1)
        d1[k] = int(v)
        idx += 1
    d2 = d1
    mod_k, mod_v = lines[idx].split(maxsplit=1)
    d2[mod_k] = int(mod_v)
    
    # Sort dictionaries for deterministic output
    sorted_d1 = {k: d1[k] for k in sorted(d1.keys())}
    sorted_d2 = {k: d2[k] for k in sorted(d2.keys())}
    return f"d1: {sorted_d1}\nd2: {sorted_d2}\nsame_object: {d1 is d2}"

def solve_1_5(input_text: str) -> str:
    """Task 1.5: Sekwencje ucieczki i surowe łańcuchy znaków (Raw String)"""
    raw_str = input_text.rstrip("\r\n")
    # Decode escape sequences as Python string literal would
    unescaped = codecs.decode(raw_str.encode('utf-8'), 'unicode_escape')
    out = [
        f"raw_str: {raw_str}",
        f"raw_len: {len(raw_str)}",
        f"unescaped_repr: {repr(unescaped)}",
        f"unescaped_len: {len(unescaped)}",
        f"has_escape: {len(raw_str) != len(unescaped)}"
    ]
    return "\n".join(out)

def solve_1_6(input_text: str) -> str:
    """Task 1.6: Kompleksowa manipulacja elementami listy"""
    lines = [l.rstrip("\r\n") for l in input_text.splitlines()]
    # line 0: initial sequence
    init_seq = lines[0] if len(lines) > 0 else ""
    L = list(init_seq)
    
    # line 1: append elem
    app_elem = lines[1] if len(lines) > 1 else ""
    L.append(app_elem)
    
    # line 2: extend items (space separated)
    ext_line = lines[2] if len(lines) > 2 else ""
    if ext_line.strip():
        L.extend(ext_line.split())
        
    # line 3: insert idx val
    ins_parts = lines[3].split() if len(lines) > 3 else []
    if len(ins_parts) >= 2:
        ins_idx = int(ins_parts[0])
        ins_val = ins_parts[1]
        L.insert(ins_idx, ins_val)
        
    # line 4: pop idx
    pop_idx = int(lines[4]) if len(lines) > 4 and lines[4].strip() else 0
    popped = L.pop(pop_idx) if 0 <= pop_idx < len(L) else ""
    
    # line 5: remove val
    rem_val = lines[5] if len(lines) > 5 else ""
    if rem_val in L:
        L.remove(rem_val)
        
    # line 6: del two indices i1 i2 (sorted i1 < i2)
    del_parts = lines[6].split() if len(lines) > 6 else []
    if len(del_parts) >= 2:
        i1 = int(del_parts[0])
        i2 = int(del_parts[1])
        # delete higher index first
        if i2 < len(L):
            del L[i2]
        if i1 < len(L):
            del L[i1]
            
    # line 7: slice assignment start stop
    slice_parts = lines[7].split() if len(lines) > 7 else []
    if len(slice_parts) >= 2:
        s_start = int(slice_parts[0])
        s_stop = int(slice_parts[1])
        L[s_start:s_stop] = []
        
    return f"popped: {popped}\nfinal: {L}\nlength: {len(L)}"

def solve_1_7(input_text: str) -> str:
    """Task 1.7: Aktualizacja i modyfikacja słowników"""
    lines = [l.strip() for l in input_text.strip().splitlines() if l.strip()]
    if not lines:
        return ""
    
    def parse_val(v):
        if v.isdigit() or (v.startswith('-') and v[1:].isdigit()):
            return int(v)
        return v
        
    n = int(lines[0])
    idx = 1
    d = {}
    for _ in range(n):
        parts = lines[idx].split(maxsplit=1)
        d[parts[0]] = parse_val(parts[1])
        idx += 1
        
    m = int(lines[idx])
    idx += 1
    for _ in range(m):
        parts = lines[idx].split(maxsplit=1)
        d[parts[0]] = parse_val(parts[1])
        idx += 1
        
    out = []
    for k in sorted(d.keys()):
        out.append(f"{k}: {d[k]}")
    return "\n".join(out)

def solve_1_8(input_text: str) -> str:
    """Task 1.8: Symulacja zapisu do pliku: tryby 'w' i 'a'"""
    lines = [l.rstrip("\r\n") for l in input_text.splitlines()]
    file_lines = []
    out = []
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str == "EXIT":
            break
        elif line_str.startswith("WRITE "):
            content = line[6:]
            file_lines = [content]
        elif line_str.startswith("APPEND "):
            content = line[7:]
            file_lines.append(content)
        elif line_str == "COUNT":
            out.append(f"lines: {len(file_lines)}")
        elif line_str == "READ":
            if not file_lines:
                out.append("--- EMPTY ---")
            else:
                out.extend(file_lines)
    return "\n".join(out)

# =====================================================================
# SOLVERS FOR MODULE 2: Zaawansowane mechanizmy i idiomy Pythona
# =====================================================================

def solve_2_1(input_text: str) -> str:
    """Task 2.1: Płytka a głęboka kopia struktur zagnieżdżonych"""
    lines = [l.strip() for l in input_text.strip().splitlines() if l.strip()]
    if not lines:
        return ""
    r = int(lines[0])
    matrix = []
    for i in range(1, r + 1):
        matrix.append([int(x) for x in lines[i].split()])
    
    shallow = copy.copy(matrix)
    deep = copy.deepcopy(matrix)
    
    mod_line = lines[r + 1].split()
    row = int(mod_line[0])
    col = int(mod_line[1])
    new_val = int(mod_line[2])
    
    orig_val_in_deep = deep[row][col]
    matrix[row][col] = new_val
    
    out = [
        f"original: {matrix}",
        f"shallow: {shallow}",
        f"deep: {deep}",
        f"shallow_modified: {shallow[row][col] == new_val}",
        f"deep_modified: {deep[row][col] == new_val}"
    ]
    return "\n".join(out)

def solve_2_2(input_text: str) -> str:
    """Task 2.2: Zaawansowane indeksowanie i wycinki sekwencji (Slicing)"""
    lines = input_text.splitlines()
    s = lines[0] if len(lines) > 0 else ""
    custom_params = lines[1].split() if len(lines) > 1 else ["-", "-", "-"]
    
    def parse_slice_param(p):
        return None if p == "-" else int(p)
        
    start = parse_slice_param(custom_params[0]) if len(custom_params) > 0 else None
    stop = parse_slice_param(custom_params[1]) if len(custom_params) > 1 else None
    step = parse_slice_param(custom_params[2]) if len(custom_params) > 2 else None
    
    rev = s[::-1]
    evens = s[::2]
    rev_evens = s[::-2]
    trimmed = s[1:-1] if len(s) >= 2 else ""
    custom = s[start:stop:step]
    
    out = [
        f"reversed: {rev}",
        f"evens: {evens}",
        f"rev_evens: {rev_evens}",
        f"trimmed: {trimmed}",
        f"custom: {custom}"
    ]
    return "\n".join(out)

def solve_2_3(input_text: str) -> str:
    """Task 2.3: Analiza częstości słów z normalizacją tekstu"""
    text = input_text.lower()
    # remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    cleaned = text.translate(translator)
    words = cleaned.split()
    if not words:
        return "--- NO WORDS ---"
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    # Sort by frequency descending, then alphabetically ascending
    sorted_words = sorted(freq.items(), key=lambda item: (-item[1], item[0]))
    out = [f"{w}: {c}" for w, c in sorted_words]
    return "\n".join(out)

def solve_2_4(input_text: str) -> str:
    """Task 2.4: Transformacje danych za pomocą List i Dict Comprehensions"""
    lines = [l.strip() for l in input_text.strip().splitlines() if l.strip()]
    if not lines:
        return ""
    nums = [int(x) for x in lines[0].split()]
    d_val, p_val = [int(x) for x in lines[1].split()]
    
    # List comprehension: squares of numbers >= P and not divisible by D
    filtered_squares = [x**2 for x in nums if x >= p_val and x % d_val != 0]
    
    # Dict comprehension: mapping x -> (x**2, x % 2 == 0)
    dict_mapping = {x: (x**2, x % 2 == 0) for x in nums if x >= p_val and x % d_val != 0}
    # Sort dictionary by key
    sorted_dict = {k: dict_mapping[k] for k in sorted(dict_mapping.keys())}
    
    return f"filtered_squares: {filtered_squares}\ndict_mapping: {sorted_dict}"

def solve_2_5(input_text: str) -> str:
    """Task 2.5: Bezpieczna konwersja typów i kategoryzacja tokenów"""
    tokens = input_text.strip().split()
    int_count = 0
    int_sum = 0
    float_count = 0
    float_sum = 0.0
    complex_count = 0
    str_count = 0
    
    for t in tokens:
        # Check int
        try:
            val = int(t)
            int_count += 1
            int_sum += val
            continue
        except ValueError:
            pass
            
        # Check float
        try:
            val = float(t)
            float_count += 1
            float_sum += val
            continue
        except ValueError:
            pass
            
        # Check complex
        try:
            val = complex(t)
            complex_count += 1
            continue
        except ValueError:
            pass
            
        str_count += 1
        
    out = [
        f"int_count: {int_count}, int_sum: {int_sum}",
        f"float_count: {float_count}, float_sum: {float_sum:.2f}",
        f"complex_count: {complex_count}",
        f"str_count: {str_count}"
    ]
    return "\n".join(out)

def solve_2_6(input_text: str) -> str:
    """Task 2.6: Zaawansowane operacje na zbiorach (Sets)"""
    lines = input_text.splitlines()
    line1 = lines[0].strip() if len(lines) > 0 else ""
    line2 = lines[1].strip() if len(lines) > 1 else ""
    
    set_a = set(int(x) for x in line1.split()) if line1 else set()
    set_b = set(int(x) for x in line2.split()) if line2 else set()
    
    u = sorted(list(set_a | set_b))
    inter = sorted(list(set_a & set_b))
    diff = sorted(list(set_a - set_b))
    sym_diff = sorted(list(set_a ^ set_b))
    
    out = [
        f"union: {u}",
        f"intersection: {inter}",
        f"difference: {diff}",
        f"symmetric_difference: {sym_diff}"
    ]
    return "\n".join(out)

def solve_2_7(input_text: str) -> str:
    """Task 2.7: Sortowanie wielopoziomowe rekordów z lambdą"""
    lines = [l.strip() for l in input_text.strip().splitlines() if l.strip()]
    if not lines:
        return "--- NO RECORDS ---"
    k = int(lines[0])
    if k == 0:
        return "--- NO RECORDS ---"
        
    records = []
    for i in range(1, k + 1):
        parts = lines[i].split()
        first_name = parts[0]
        last_name = parts[1]
        age = int(parts[2])
        score = int(parts[3])
        records.append({
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "score": score
        })
        
    # Sort rules:
    # 1. score descending -> -score
    # 2. age ascending -> age
    # 3. last_name ascending case-insensitive -> last_name.lower()
    # 4. first_name ascending case-insensitive -> first_name.lower()
    sorted_rec = sorted(
        records,
        key=lambda r: (-r["score"], r["age"], r["last_name"].lower(), r["first_name"].lower())
    )
    
    out = []
    for r in sorted_rec:
        out.append(f"{r['first_name']} {r['last_name']} ({r['age']} yo) - {r['score']} pts")
    return "\n".join(out)

def solve_2_8(input_text: str) -> str:
    """Task 2.8: Haszowalność krotek i symulacja ruchów na siatce (Grid Walk)"""
    moves = input_text.strip().split()
    x, y = 0, 0
    visits = {(0, 0): 1}
    
    for m in moves:
        m = m.upper()
        if m == "UP":
            y += 1
        elif m == "DOWN":
            y -= 1
        elif m == "RIGHT":
            x += 1
        elif m == "LEFT":
            x -= 1
        pos = (x, y)
        visits[pos] = visits.get(pos, 0) + 1
        
    # Test unhashability of list
    unhashable_caught = False
    try:
        bad_dict = {[x, y]: 1}
    except TypeError:
        unhashable_caught = True
        
    # Find most visited: max count, tie-breaker: min x, then min y
    most_visited_pos = sorted(visits.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))[0]
    
    out = [
        f"final_position: {(x, y)}",
        f"unique_positions: {len(visits)}",
        f"most_visited: {most_visited_pos[0]} with {most_visited_pos[1]} visits",
        f"unhashable_caught: {unhashable_caught}"
    ]
    return "\n".join(out)

print("All solvers defined successfully.")
