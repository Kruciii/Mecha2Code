"""
Full batch builder for MechaCode Python Tasks.
Builds, tests, and validates JSON batch according to the user schema.
"""
import json
import codecs
import string
import copy
from typing import List, Dict, Any

from generate_batch import (
    solve_1_1, solve_1_2, solve_1_3, solve_1_4,
    solve_1_5, solve_1_6, solve_1_7, solve_1_8,
    solve_2_1, solve_2_2, solve_2_3, solve_2_4,
    solve_2_5, solve_2_6, solve_2_7, solve_2_8
)

def build_tasks():
    items = []

    # =====================================================================
    # MODULE 1: Zadania do Samokontroli (module_id: 1)
    # =====================================================================

    # -----------------------------------------------------------------
    # Task 1.1: Liczby zespolone i operacje arytmetyczne (II.3.1)
    # -----------------------------------------------------------------
    desc_1_1 = """### Cel zadania
W języku Python liczby zespolone są typem wbudowanym (`complex`). Część urojona oznaczana jest literą `j` (np. `1 + 2j`) lub tworzona za pomocą konstruktora `complex(re, im)`.

### Wymagania
Napisz program, który wczytuje z wejścia trzy liczby: `re`, `im` oraz `k` oddzielone spacjami:
1. Utwórz liczbę zespoloną `z1` o części rzeczywistej `re` i części urojonej `im`.
2. Utwórz liczbę `z2 = z1 * k`.
3. Wypisz w kolejnych liniach:
   - wartość liczby `z1`
   - typ zmiennej `z1` (`<class 'complex'>`)
   - wartość liczby `z2`
   - typ zmiennej `z2` (`<class 'complex'>`)

Liczby całkowite na wejściu traktuj jako liczby całkowite, a zmiennoprzecinkowe jako float.

### Format wejścia
Jedna linia zawierająca trzy liczby oddzielone spacją: `re im k`.

### Format wyjścia
Cztery linie zawierające odpowiednio: `z1`, `type(z1)`, `z2`, `type(z2)`.

### Przykład
**Wejście:**
```
1 2 3
```
**Wyjście:**
```
(1+2j)
<class 'complex'>
(3+6j)
<class 'complex'>
```
"""
    inputs_1_1 = [
        # (input_data, is_hidden)
        ("1 2 3", False),
        ("0 0 1", False),
        ("2.5 1.5 2", True),
        ("-1 -2 -3", True),
        ("0 5 2", True),
        ("5 0 3", True),
        ("3 4 0", True),
        ("-2 3 -2", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Liczby zespolone i operacje arytmetyczne",
            "description": desc_1_1,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_1(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_1
        ]
    })

    # -----------------------------------------------------------------
    # Task 1.2: Wielokrotne potęgowanie operatorem przypisania (**=) (II.3.2)
    # -----------------------------------------------------------------
    desc_1_2 = """### Cel zadania
Zadanie sprawdza opanowanie operatorów rozszerzonego przypisania (augmented assignment), w szczególności operatora potęgowania `**=`.

### Wymagania
Napisz program, który wczytuje dwie liczby całkowite: liczbę początkową `z` oraz liczbę kroków `n` ($n \\ge 0$).
Program rozpoczyna ze zmienną `z`. Następnie dokładnie `n` razy wykonuje operację podniesienia do kwadratu przy użyciu operatora `**=`:
```python
z **= 2
```
Na końcu program wypisuje ostateczną wartość `z`.

### Format wejścia
Jedna linia zawierająca dwie liczby całkowite `z` oraz `n` oddzielone spacją.

### Format wyjścia
Pojedyncza liczba całkowita będąca wynikiem po `n` potęgowaniach.

### Przykład
**Wejście:**
```
3 3
```
**Wyjście:**
```
6561
```
*Wyjaśnienie:* Początkowo $z = 3$. Krok 1: $3^2 = 9$. Krok 2: $9^2 = 81$. Krok 3: $81^2 = 6561$.
"""
    inputs_1_2 = [
        ("3 3", False),
        ("2 0", False),
        ("0 5", True),
        ("1 10", True),
        ("-1 1", True),
        ("-1 2", True),
        ("-2 3", True),
        ("2 5", True),
        ("5 2", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Wielokrotne potęgowanie operatorem przypisania (**=)",
            "description": desc_1_2,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_2(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_2
        ]
    })

    # -----------------------------------------------------------------
    # Task 1.3: Referencje list: modyfikacja w miejscu a nowy obiekt (II.4.1)
    # -----------------------------------------------------------------
    desc_1_3 = """### Cel zadania
Zrozumienie różnicy między mutacją obiektu w miejscu a przypisaniem nowej referencji.
W języku Python instrukcja `b = a` kopiuje referencję do listy `a`, a nie jej zawartość. Modyfikacja listy w miejscu (np. `a.append(...)`) jest widoczna w obu zmiennych. Natomiast przypisanie `a = [...]` tworzy nowy obiekt i odwiązuje zmienną `a` od starej listy, podczas gdy `b` nadal wskazuje na pierwotną listę.

### Wymagania
Napisz program, który:
1. Wczytuje z 1. linii początkowe elementy listy `a` (liczby całkowite oddzielone spacjami) i tworzy referencję `b = a`.
2. Wczytuje z 2. linii liczbę całkowitą `x` i wykonuje `a.append(x)`.
3. Wypisuje aktualną zawartość `a` i `b`:
   `a: <lista>`
   `b: <lista>`
4. Wczytuje z 3. linii nowe elementy dla `a` (liczby całkowite oddzielone spacjami) i wykonuje przypisanie nowego obiektu do `a`.
5. Ponownie wypisuje aktualną zawartość `a` i `b`:
   `a: <lista>`
   `b: <lista>`

### Format wejścia
Linia 1: liczby początkowe dla `a` oddzielone spacją (linia może być pusta).
Linia 2: liczba `x` do dodania przez `append`.
Linia 3: liczby nowej listy dla `a` oddzielone spacją (linia może być pusta).

### Format wyjścia
Cztery linie w formacie `a: [...]` oraz `b: [...]`.

### Przykład
**Wejście:**
```
1 2 3
4
9 9 9
```
**Wyjście:**
```
a: [1, 2, 3, 4]
b: [1, 2, 3, 4]
a: [9, 9, 9]
b: [1, 2, 3, 4]
```
"""
    inputs_1_3 = [
        ("1 2 3\n4\n9 9 9", False),
        ("10\n20\n30", False),
        ("\n5\n1 2", True),
        ("1 2\n3\n", True),
        ("-5 -10\n-15\n0 0 0", True),
        ("7 8 9\n10\n7 8 9 10", True),
        ("100 200 300\n400\n-1 -2 -3 -4", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Referencje list: modyfikacja w miejscu a nowy obiekt",
            "description": desc_1_3,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_3(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_3
        ]
    })

    # -----------------------------------------------------------------
    # Task 1.4: Współdzielenie referencji w słownikach (II.4.2)
    # -----------------------------------------------------------------
    desc_1_4 = """### Cel zadania
Demonstracja współdzielenia referencji do słowników w Pythonie. Podobnie jak listy, słowniki są obiektami mutowalnymi. Przypisanie `d2 = d1` sprawia, że obie zmienne wskazują na ten sam słownik w pamięci (`d1 is d2` zwraca `True`).

### Wymagania
Napisz program, który:
1. Wczytuje liczbę $N$ początkowych par słownika `d1`.
2. W kolejnych $N$ liniach wczytuje pary `klucz wartosc` (klucz to ciąg znaków, wartość to liczba całkowita) i umieszcza je w `d1`.
3. Tworzy referencję `d2 = d1`.
4. W kolejnej linii wczytuje klucz `k` oraz nową wartość całkowitą `v` i modyfikuje drugi słownik: `d2[k] = v`.
5. Wypisuje:
   `d1: {posortowany alfabetycznie słownik}`
   `d2: {posortowany alfabetycznie słownik}`
   `same_object: True` (wartość `d1 is d2`)

### Format wejścia
Linia 1: liczba $N$ ($N \\ge 1$).
Następne $N$ linii: `klucz wartosc`.
Ostatnia linia: `k v` (klucz i nowa wartość do ustawienia w `d2`).

### Format wyjścia
Trzy linie zgodnie z opisem.

### Przykład
**Wejście:**
```
1
a 1
a 99
```
**Wyjście:**
```
d1: {'a': 99}
d2: {'a': 99}
same_object: True
```
"""
    inputs_1_4 = [
        ("1\na 1\na 99", False),
        ("2\nx 10\ny 20\nx 50", False),
        ("1\na 1\nb 2", True),
        ("3\napple 5\nbanana 3\norange 8\nbanana 10", True),
        ("2\nscore 100\nlevel 1\nscore -50", True),
        ("4\nk1 1\nk2 2\nk3 3\nk4 4\nk3 999", True),
        ("1\nz 0\nz 0", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Współdzielenie referencji w słownikach",
            "description": desc_1_4,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_4(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_4
        ]
    })

    # -----------------------------------------------------------------
    # Task 1.5: Sekwencje ucieczki i surowe łańcuchy znaków (Raw String) (II.5.1)
    # -----------------------------------------------------------------
    desc_1_5 = """### Cel zadania
Zrozumienie różnicy między standardową interpretacją sekwencji ucieczki (`\\n`, `\\t`, `\\\\`) a surowymi ciągami znaków (raw string, `r'...'`).

### Wymagania
W systemach operacyjnych takich jak Windows ścieżki plików zawierają ukośniki `\\`. W zwykłych stringach Pythona `\\n` oznacza znak nowej linii (jeden znak), a `\\t` tabulację. W raw stringach znak `\\` traktowany jest dosłownie jako zwykły znak.
Napisz program, który wczytuje ze standardowego wejścia jedną linię tekstu i analizuje ją w dwóch wariantach:
1. Jako surowy string (`raw_str` - tekst dokładnie w postaci wczytanej).
2. Jako string po zinterpretowaniu sekwencji ucieczki (`unescaped_str`, uzyskany np. przez `codecs.decode(raw_str.encode('utf-8'), 'unicode_escape')`).

Program wypisuje:
- `raw_str: <raw_str>`
- `raw_len: <długość tekstu surowego>`
- `unescaped_repr: <repr(unescaped_str)>`
- `unescaped_len: <długość tekstu zinterpretowanego>`
- `has_escape: <True jeśli unescaped_len != raw_len, inaczej False>`

### Format wejścia
Jedna linia tekstu reprezentująca ścieżkę lub napis.

### Format wyjścia
Pięć linii z podsumowaniem analizy.

### Przykład
**Wejście:**
```
c:\\nowy\\test.txt
```
**Wyjście:**
```
raw_str: c:\\nowy\\test.txt
raw_len: 16
unescaped_repr: 'c:\\nowy\\test.txt'
unescaped_len: 14
has_escape: True
```
*Uwaga:* Znak `\\n` w unescaped staje się pojedynczym bajtem nowej linii, a `\\t` tabulacją.
"""
    inputs_1_5 = [
        ("c:\\nowy\\test.txt", False),
        ("c:/nowy/test.txt", False),
        ("hello\\tworld", True),
        ("line1\\nline2\\nline3", True),
        ("plain_text_without_slashes", True),
        ("c:\\\\program files\\\\python", True),
        ("special\\a\\b\\f\\r", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Sekwencje ucieczki i surowe łańcuchy znaków (Raw String)",
            "description": desc_1_5,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_5(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_5
        ]
    })

    # -----------------------------------------------------------------
    # Task 1.6: Kompleksowa manipulacja elementami listy (II.5.2)
    # -----------------------------------------------------------------
    desc_1_6 = """### Cel zadania
Przećwiczenie kluczowych metod i operacji modyfikacji list w Pythonie: `append`, `extend`, `insert`, `pop`, `remove`, `del` oraz wycinków (`slice assignment`).

### Wymagania
Napisz program, który wykonuje na liście następującą sekwencję 8 kroków zdefiniowanych na wejściu:
1. Inicjalizuje listę `L = list(ciag)` ze znaków wczytanych z linii 1.
2. `append`: wczytuje znak z linii 2 i dodaje na koniec: `L.append(elem)`.
3. `extend`: wczytuje elementy z linii 3 (oddzielone spacją) i rozszerza listę: `L.extend(...)`.
4. `insert`: wczytuje indeks `idx` oraz element `val` z linii 4 i wstawia: `L.insert(idx, val)`.
5. `pop`: wczytuje indeks z linii 5, usuwa element przez `popped = L.pop(idx)` i zapamiętuje.
6. `remove`: wczytuje wartość z linii 6 i usuwa jej pierwsze wystąpienie przez `L.remove(val)` (jeśli element istnieje w liście).
7. `del`: wczytuje dwa indeksy `i1 i2` z linii 7 (gdzie $i1 < i2$). Usuwa z listy najpierw element o indeksie `i2`, a następnie o indeksie `i1` (`del L[i2]; del L[i1]`).
8. `slice assignment`: wczytuje zakres `start stop` z linii 8 i usuwa ten wycinek przez przypisanie pustej listy: `L[start:stop] = []`.

Na końcu program wypisuje:
- `popped: <popped>`
- `final: <L>`
- `length: <len(L)>`

### Format wejścia
8 linii zawierających kolejne instrukcje i argumenty.

### Format wyjścia
3 linie: usunięty element przez `pop`, finalna lista `L` oraz jej długość.

### Przykład
**Wejście:**
```
abcdef
g
1 2 3
2 0
3
e
0 2
1 3
```
**Wyjście:**
```
popped: c
final: ['b', 'g', '1', '2', '3']
length: 5
```
"""
    inputs_1_6 = [
        ("abcdef\ng\n1 2 3\n2 0\n3\ne\n0 2\n1 3", False),
        ("xyz\nw\n4 5\n1 A\n2\nz\n0 1\n0 1", False),
        ("python\n!\n3 1 4\n0 P\n1\ny\n0 3\n2 4", True),
        ("aaaaaa\nb\nc d e\n3 X\n0\na\n1 2\n0 2", True),
        ("123456789\n0\na b c d\n5 M\n4\n9\n0 5\n1 4", True),
        ("abcdef\nz\nx y\n0 0\n0\nnonexistent\n0 1\n0 2", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Kompleksowa manipulacja elementami listy",
            "description": desc_1_6,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_6(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_6
        ]
    })

    # -----------------------------------------------------------------
    # Task 1.7: Aktualizacja i modyfikacja słowników (II.6.1)
    # -----------------------------------------------------------------
    desc_1_7 = """### Cel zadania
Praca ze strukturą słownika (`dict`), dynamiczne dodawanie nowych par klucz-wartość oraz aktualizowanie istniejących kluczy.

### Wymagania
Napisz program, który:
1. Wczytuje liczbę $N$ początkowych wpisów słownika.
2. W kolejnych $N$ liniach wczytuje pary `klucz wartosc`. Jeśli `wartosc` składa się z samych cyfr (lub jest liczbą całkowitą ze znakiem minus), skonwertuj ją na typ `int`. W przeciwnym razie pozostaw jako `str`.
3. Wczytuje liczbę $M$ aktualizacji.
4. W kolejnych $M$ liniach wczytuje pary `klucz wartosc` (z taką samą konwersją na `int`) i wykonuje aktualizację `d[klucz] = wartosc` (nowy klucz zostaje dodany, a istniejący nadpisany).
5. Wypisuje zawartość wynikowego słownika posortowaną alfabetycznie po kluczach, w formacie:
   `<klucz>: <wartosc>`

### Format wejścia
Linia 1: $N$
Kolejne $N$ linii: `klucz wartosc`
Kolejna linia: $M$
Kolejne $M$ linii: `klucz wartosc`

### Format wyjścia
Pary `<klucz>: <wartosc>` posortowane rosnąco według klucza.

### Przykład
**Wejście:**
```
2
imie Jan
wiek 25
2
miasto Warszawa
wiek 26
```
**Wyjście:**
```
imie: Jan
miasto: Warszawa
wiek: 26
```
"""
    inputs_1_7 = [
        ("2\nimie Jan\nwiek 25\n2\nmiasto Warszawa\nwiek 26", False),
        ("1\nstan aktywne\n1\npunkty 100", False),
        ("0\n2\nx 10\ny 20", True),
        ("3\na 1\nb 2\nc 3\n0", True),
        ("2\nscore 100\nlevel 1\n2\nscore 150\nlevel 2", True),
        ("2\ntemp 21\nstatus ok\n1\ntemp -5", True),
        ("3\nk1 val1\nk2 val2\nk3 val3\n3\nk1 val1_updated\nk4 val4\nk2 2026", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Aktualizacja i modyfikacja słowników",
            "description": desc_1_7,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_7(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_7
        ]
    })

    # -----------------------------------------------------------------
    # Task 1.8: Symulacja zapisu do pliku: tryby 'w' i 'a' (II.6.2)
    # -----------------------------------------------------------------
    desc_1_8 = """### Cel zadania
Zrozumienie mechanizmu działania trybów otwierania plików w Pythonie:
- Tryb `'w'` (write) tworzy nowy plik lub czyści dotychczasową zawartość przed zapisem.
- Tryb `'a'` (append) zachowuje istniejącą treść i dopisuje nowe linie na końcu.

### Wymagania
Napisz program, który symuluje bufor plikowy i przetwarza ciąg poleceń ze standardowego wejścia:
- `WRITE <tekst>`: czyści dotychczasową zawartość pliku i zapisuje pojedynczą linię `<tekst>`.
- `APPEND <tekst>`: dopisuje linię `<tekst>` na końcu pliku.
- `READ`: wypisuje bieżącą zawartość pliku (jeśli plik nie zawiera żadnych linii, wypisuje `--- EMPTY ---`).
- `COUNT`: wypisuje liczbę linii w formacie `lines: <k>`.
- `EXIT`: kończy przetwarzanie poleceń.

### Format wejścia
Kolejne polecenia, po jednym w każdej linii.

### Format wyjścia
Odpowiedzi na polecenia `READ` oraz `COUNT`.

### Przykład
**Wejście:**
```
WRITE Pierwsza linijka
APPEND Druga linijka
READ
COUNT
EXIT
```
**Wyjście:**
```
Pierwsza linijka
Druga linijka
lines: 2
```
"""
    inputs_1_8 = [
        ("WRITE Pierwsza linijka\nAPPEND Druga linijka\nREAD\nCOUNT\nEXIT", False),
        ("READ\nCOUNT\nEXIT", False),
        ("WRITE Test 1\nWRITE Test 2\nREAD\nEXIT", True),
        ("APPEND Linia A\nAPPEND Linia B\nAPPEND Linia C\nREAD\nCOUNT\nWRITE Nowy Start\nREAD\nEXIT", True),
        ("WRITE Halo\nREAD\nWRITE Świat\nAPPEND 2026\nREAD\nCOUNT\nEXIT", True),
        ("WRITE Tylko jedna\nCOUNT\nEXIT", True),
    ]
    items.append({
        "module_id": 1,
        "task": {
            "title": "Symulacja zapisu do pliku: tryb 'w' i 'a'",
            "description": desc_1_8,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_1_8(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_1_8
        ]
    })

    # =====================================================================
    # MODULE 2: Zaawansowane mechanizmy i idiomy Pythona (module_id: 2)
    # =====================================================================

    # -----------------------------------------------------------------
    # Task 2.1: Płytka a głęboka kopia struktur zagnieżdżonych
    # -----------------------------------------------------------------
    desc_2_1 = """### Cel zadania
Zrozumienie działania modułu `copy`: różnicy między płytką kopią (`copy.copy`) a głęboką kopią (`copy.deepcopy`) przy zagnieżdżonych kolekcjach mutowalnych.

### Wymagania
Napisz program, który:
1. Wczytuje liczbę wierszy macierzy $R$, a następnie $R$ linii z liczbami całkowitymi tworząc macierz 2D `matrix`.
2. Tworzy płytką kopię macierzy: `shallow = copy.copy(matrix)`.
3. Tworzy głęboką kopię macierzy: `deep = copy.deepcopy(matrix)`.
4. Wczytuje linię z trzema liczbami: `row col new_val` i modyfikuje oryginalną macierz:
   `matrix[row][col] = new_val`
5. Wypisuje:
   - `original: <matrix>`
   - `shallow: <shallow>`
   - `deep: <deep>`
   - `shallow_modified: <True/False>` (czy element w `shallow` zmienił się na `new_val`)
   - `deep_modified: <True/False>` (czy element w `deep` zmienił się na `new_val`)

W płytkiej kopii zewnętrzna lista jest nowa, ale jej wiersze (wewnętrzne listy) są współdzielonymi referencjami, dlatego `shallow_modified` wyniesie `True`. W kopii głębokiej cała struktura została powielona niezależnie, więc `deep_modified` wyniesie `False`.

### Format wejścia
Linia 1: $R$
Kolejne $R$ linii: liczby w wierszu oddzielone spacjami
Ostatnia linia: `row col new_val`

### Format wyjścia
Pięć linii z raportem o stanie obiektów.

### Przykład
**Wejście:**
```
2
1 2
3 4
0 1 99
```
**Wyjście:**
```
original: [[1, 99], [3, 4]]
shallow: [[1, 99], [3, 4]]
deep: [[1, 2], [3, 4]]
shallow_modified: True
deep_modified: False
```
"""
    inputs_2_1 = [
        ("2\n1 2\n3 4\n0 1 99", False),
        ("3\n10 20\n30 40\n50 60\n2 0 777", False),
        ("1\n5 6 7 8\n0 3 -1", True),
        ("3\n1 1 1\n2 2 2\n3 3 3\n1 1 0", True),
        ("2\n0 0\n0 0\n0 0 1", True),
        ("4\n1\n2\n3\n4\n3 0 100", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Płytka a głęboka kopia struktur zagnieżdżonych",
            "description": desc_2_1,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_1(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_1
        ]
    })

    # -----------------------------------------------------------------
    # Task 2.2: Zaawansowane indeksowanie i wycinki sekwencji (Slicing)
    # -----------------------------------------------------------------
    desc_2_2 = """### Cel zadania
Opanowanie składni wycinków `sequence[start:stop:step]` w Pythonie, w tym kroków ujemnych i pomijania parametrów.

### Wymagania
Napisz program, który dla wczytanego napisu $S$ wyznacza:
1. `reversed`: pełne odwrócenie napisu (`s[::-1]`).
2. `evens`: co drugi znak od początku (`s[::2]`).
3. `rev_evens`: co drugi znak od końca (`s[::-2]`).
4. `trimmed`: napis bez pierwszego i ostatniego znaku (`s[1:-1]` jeśli $\\text{len} \\ge 2$, inaczej pusty napis).
5. `custom`: wycinek sparametryzowany wartościami `start stop step` z 2. linii wejścia (wartość `-` oznacza brak parametru, czyli `None`).

### Format wejścia
Linia 1: napis $S$.
Linia 2: trzy wartości `start stop step` (liczba całkowita lub znak `-`).

### Format wyjścia
Pięć linii w formacie:
`reversed: <wynik>`
`evens: <wynik>`
`rev_evens: <wynik>`
`trimmed: <wynik>`
`custom: <wynik>`

### Przykład
**Wejście:**
```
ABCDEFG
1 5 2
```
**Wyjście:**
```
reversed: GFEDCBA
evens: ACEG
rev_evens: GECA
trimmed: BCDEF
custom: BD
```
"""
    inputs_2_2 = [
        ("ABCDEFG\n1 5 2", False),
        ("Python\n- - -1", False),
        ("racecar\n- - -", True),
        ("K\n- - -", True),
        ("\n- - -", True),
        ("Hello, World!\n0 5 1", True),
        ("0123456789\n8 1 -2", True),
        ("abcdefghij\n-3 - -1", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Zaawansowane indeksowanie i wycinki sekwencji (Slicing)",
            "description": desc_2_2,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_2(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_2
        ]
    })

    # -----------------------------------------------------------------
    # Task 2.3: Analiza częstości słów z normalizacją tekstu
    # -----------------------------------------------------------------
    desc_2_3 = """### Cel zadania
Przetwarzanie tekstu, czyszczenie interpunkcji oraz zliczanie częstości słów przy użyciu słownika z sortowaniem wielokryterialnym.

### Wymagania
Napisz program, który:
1. Wczytuje tekst ze standardowego wejścia (wieloliniowy).
2. Sprowadza litery do małych znaków (`lower()`).
3. Usuwa wszystkie znaki interpunkcyjne (zdefiniowane w `string.punctuation`).
4. Dzieli tekst na słowa białymi znakami (`split()`).
5. Zlicza liczbę wystąpień każdego słowa za pomocą słownika.
6. Wypisuje statystyki posortowane:
   - w pierwszej kolejności **malejąco według liczby wystąpień**,
   - w drugiej kolejności **rosnąco alfabetycznie** (w przypadku tej samej częstości).

Jeśli po oczyszczeniu tekst nie zawiera żadnych słów, wypisz `--- NO WORDS ---`.

### Format wejścia
Tekst w jednej lub wielu liniach.

### Format wyjścia
Dla każdego słowa linia: `<slowo>: <liczba>`, lub `--- NO WORDS ---`.

### Przykład
**Wejście:**
```
To be, or not to be: that is the question.
```
**Wyjście:**
```
be: 2
to: 2
is: 1
not: 1
or: 1
question: 1
that: 1
the: 1
```
"""
    inputs_2_3 = [
        ("To be, or not to be: that is the question.", False),
        ("Python is great. Python is fast!", False),
        ("... --- !!! ???", True),
        ("apple BANANA Apple banana apple Orange", True),
        ("one ONE One oNe OnE", True),
        ("a b c d e f g", True),
        ("test! test? test, test. test: test; test", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Analiza częstości słów z normalizacją tekstu",
            "description": desc_2_3,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_3(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_3
        ]
    })

    # -----------------------------------------------------------------
    # Task 2.4: Transformacje danych za pomocą List i Dict Comprehensions
    # -----------------------------------------------------------------
    desc_2_4 = """### Cel zadania
Stosowanie idiomatycznych wyrażeń listowych (list comprehensions) oraz słownikowych (dict comprehensions) z filtrowaniem warunkowym.

### Wymagania
Napisz program, który:
1. Wczytuje listę liczb całkowitych z 1. linii wejścia.
2. Wczytuje z 2. linii dwie liczby: dzielnik $D$ oraz próg minimalny $P$.
3. Za pomocą **list comprehension** tworzy listę kwadratów tych liczb, które są większe lub równe $P$ i nie są podzielne przez $D$:
   `filtered_squares = [x**2 for x in nums if x >= P and x % D != 0]`
4. Za pomocą **dict comprehension** tworzy słownik odwzorowujący każdą taką unikalną liczbę $x$ na parę krotki `(kwadrat, czy_parzysta)`:
   `dict_mapping = {x: (x**2, x % 2 == 0) for x in nums if x >= P and x % D != 0}`
5. Wypisuje:
   `filtered_squares: <lista>`
   `dict_mapping: <słownik z kluczami posortowanymi rosnąco>`

### Format wejścia
Linia 1: liczby całkowite oddzielone spacjami.
Linia 2: dwie liczby całkowite `D P`.

### Format wyjścia
Dwie linie z wynikami.

### Przykład
**Wejście:**
```
1 2 3 4 5 6 7 8 9 10
3 4
```
**Wyjście:**
```
filtered_squares: [16, 25, 49, 64, 100]
dict_mapping: {4: (16, True), 5: (25, False), 7: (49, False), 8: (64, True), 10: (100, True)}
```
"""
    inputs_2_4 = [
        ("1 2 3 4 5 6 7 8 9 10\n3 4", False),
        ("10 20 30 40 50\n5 25", False),
        ("2 4 6 8\n2 1", True),
        ("1 3 5 7 9\n2 0", True),
        ("-5 -4 -3 -2 -1 0 1 2 3 4 5\n2 -2", True),
        ("100\n10 50", True),
        ("1 2 3 4\n5 100", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Transformacje danych za pomocą List i Dict Comprehensions",
            "description": desc_2_4,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_4(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_4
        ]
    })

    # -----------------------------------------------------------------
    # Task 2.5: Bezpieczna konwersja typów i kategoryzacja tokenów
    # -----------------------------------------------------------------
    desc_2_5 = """### Cel zadania
Obsługa wyjątków (`try...except`) i bezpieczne rzutowanie typów w łańcuchu parsowania danych.

### Wymagania
Napisz program, który wczytuje ciąg tokenów (oddzielonych białymi znakami) i dla każdego tokena określa jego najbardziej precyzyjny typ według hierarchii:
1. `int` - jeśli `int(token)` nie wyrzuca błędu.
2. `float` - jeśli nie jest int, ale `float(token)` kończy się sukcesem.
3. `complex` - jeśli nie jest int ani float, ale `complex(token)` kończy się sukcesem (np. `1+2j`, `5j`).
4. `str` - jeśli żadna z powyższych konwersji się nie powiedzie.

Program zlicza liczbę tokenów każdego typu oraz oblicza sumę wartości liczbowych dla `int` i `float`.

### Format wejścia
Linia z tokenami oddzielonymi spacjami.

### Format wyjścia
Cztery linie:
`int_count: <k>, int_sum: <s>`
`float_count: <k>, float_sum: <s z dwoma miejscami po przecinku>`
`complex_count: <k>`
`str_count: <k>`

### Przykład
**Wejście:**
```
42 3.14 1+2j hello 100 -5 2.5 python 0j
```
**Wyjście:**
```
int_count: 3, int_sum: 137
float_count: 2, float_sum: 5.64
complex_count: 2
str_count: 2
```
"""
    inputs_2_5 = [
        ("42 3.14 1+2j hello 100 -5 2.5 python 0j", False),
        ("1 2 3", False),
        ("hello world foo bar", True),
        ("0.5 0.25 -1.75", True),
        ("3j -2j 1-4j", True),
        ("0 0.0 0j 0text", True),
        ("-10 -2.5 -3-4j minus", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Bezpieczna konwersja typów i kategoryzacja tokenów",
            "description": desc_2_5,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_5(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_5
        ]
    })

    # -----------------------------------------------------------------
    # Task 2.6: Zaawansowane operacje na zbiorach (Sets)
    # -----------------------------------------------------------------
    desc_2_6 = """### Cel zadania
Przećwiczenie operacji teoriomnogościowych wbudowanych w typ `set`: suma (`|`), część wspólna (`&`), różnica (`-`) i różnica symetryczna (`^`).

### Wymagania
Napisz program, który:
1. Wczytuje z 1. linii liczby całkowite tworzące zbiór $A$.
2. Wczytuje z 2. linii liczby całkowite tworzące zbiór $B$.
3. Oblicza i wypisuje wyniki w postaci posortowanych rosnąco list:
   - Suma zbiorów: $A \\cup B$ (`union: [...]`)
   - Część wspólna: $A \\cap B$ (`intersection: [...]`)
   - Różnica zbiorów: $A \\setminus B$ (`difference: [...]`)
   - Różnica symetryczna: $A \\Delta B$ (`symmetric_difference: [...]`)

### Format wejścia
Linia 1: liczby zbioru $A$ oddzielone spacjami (może być pusta).
Linia 2: liczby zbioru $B$ oddzielone spacjami (może być pusta).

### Format wyjścia
Cztery linie zawierające posortowane listy elementów.

### Przykład
**Wejście:**
```
1 2 3 4 5
3 4 5 6 7
```
**Wyjście:**
```
union: [1, 2, 3, 4, 5, 6, 7]
intersection: [3, 4, 5]
difference: [1, 2]
symmetric_difference: [1, 2, 6, 7]
```
"""
    inputs_2_6 = [
        ("1 2 3 4 5\n3 4 5 6 7", False),
        ("1 2\n3 4", False),
        ("1 2 3\n1 2 3", True),
        ("\n1 2 3", True),
        ("10 20 30\n", True),
        ("\n", True),
        ("-5 0 5 10\n0 10 20", True),
        ("1 1 1 2 2 3\n3 3 4 4 5", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Zaawansowane operacje na zbiorach (Sets)",
            "description": desc_2_6,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_6(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_6
        ]
    })

    # -----------------------------------------------------------------
    # Task 2.7: Sortowanie wielopoziomowe rekordów z lambdą
    # -----------------------------------------------------------------
    desc_2_7 = """### Cel zadania
Zaawansowane sortowanie struktur danych w Pythonie za pomocą funkcji `sorted()` i wyrażeń lambda (`key=lambda x: (...)`).

### Wymagania
Napisz program sortujący rekordy studentów. Każdy rekord składa się z:
- `first_name` (str)
- `last_name` (str)
- `age` (int)
- `score` (int)

Kryteria sortowania (od najważniejszego):
1. **Wynik (`score`)** – malejąco (wyższy wynik wyżej).
2. **Wiek (`age`)** – rosnąco (młodsza osoba wyżej).
3. **Nazwisko (`last_name`)** – alfabetycznie rosnąco bez względu na wielkość liter (`lower()`).
4. **Imię (`first_name`)** – alfabetycznie rosnąco bez względu na wielkość liter (`lower()`).

Jeśli baza jest pusta ($K=0$), wypisz `--- NO RECORDS ---`.

### Format wejścia
Linia 1: liczba rekordów $K$ ($K \\ge 0$).
Kolejne $K$ linii: `first_name last_name age score`.

### Format wyjścia
Dla każdego studenta linia w formacie:
`<first_name> <last_name> (<age> yo) - <score> pts`
lub `--- NO RECORDS ---`.

### Przykład
**Wejście:**
```
4
Jan Kowalski 20 85
Anna Nowak 19 90
Piotr Kowalski 22 85
Ewa Nowak 19 90
```
**Wyjście:**
```
Anna Nowak (19 yo) - 90 pts
Ewa Nowak (19 yo) - 90 pts
Jan Kowalski (20 yo) - 85 pts
Piotr Kowalski (22 yo) - 85 pts
```
"""
    inputs_2_7 = [
        ("4\nJan Kowalski 20 85\nAnna Nowak 19 90\nPiotr Kowalski 22 85\nEwa Nowak 19 90", False),
        ("0", False),
        ("1\nAdam Mickiewicz 30 100", True),
        ("3\nBob Ross 40 50\nAlice Ross 40 50\nCharlie Ross 35 50", True),
        ("3\nTom Brown 21 70\ntom brown 20 70\nTim Brown 20 70", True),
        ("5\nA B 20 10\nC D 20 20\nE F 20 30\nG H 20 40\nI J 20 50", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Sortowanie wielopoziomowe rekordów z lambdą",
            "description": desc_2_7,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_7(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_7
        ]
    })

    # -----------------------------------------------------------------
    # Task 2.8: Haszowalność krotek i symulacja ruchów na siatce (Grid Walk)
    # -----------------------------------------------------------------
    desc_2_8 = """### Cel zadania
Zrozumienie wymogu haszowalności (`hashable`) kluczy w słownikach: krotki (`tuple`) jako obiekty niemutowalne mogą być kluczami, podczas gdy listy (`list`) powodują błąd `TypeError`.

### Wymagania
Napisz program symulujący ruch piona po siatce 2D:
1. Pion startuje w punkcie `(0, 0)`. Punkt początkowy jest rejestrowany jako 1. wizyta.
2. Wczytuje ciąg ruchów: `UP` ($y+1$), `DOWN` ($y-1$), `RIGHT` ($x+1$), `LEFT` ($x-1$).
3. Używając krotek `(x, y)` jako kluczy słownika, zlicza liczbę odwiedzin każdego pola.
4. Sprawdza zabezpieczenie typów: wykonuje próbę użycia mutowalnej listy jako klucza w bloku `try...except TypeError` (`test_dict = {[x, y]: 1}`).
5. Wypisuje:
   - `final_position: (x, y)`
   - `unique_positions: <liczba unikalnych odwiedzonych pól>`
   - `most_visited: (x, y) with <k> visits` (przy remisie wybierz punkt z mniejszym $x$, a przy równym $x$ z mniejszym $y$).
   - `unhashable_caught: True`

### Format wejścia
Linia zawierająca komendy ruchów oddzielone spacjami (może być pusta).

### Format wyjścia
Cztery linie z podsumowaniem.

### Przykład
**Wejście:**
```
UP RIGHT DOWN LEFT UP
```
**Wyjście:**
```
final_position: (0, 1)
unique_positions: 4
most_visited: (0, 0) with 2 visits
unhashable_caught: True
```
"""
    inputs_2_8 = [
        ("UP RIGHT DOWN LEFT UP", False),
        ("", False),
        ("UP UP UP UP", True),
        ("RIGHT RIGHT LEFT LEFT", True),
        ("UP RIGHT DOWN LEFT", True),
        ("DOWN LEFT DOWN LEFT UP UP RIGHT RIGHT", True),
        ("RIGHT DOWN LEFT UP RIGHT DOWN LEFT UP", True),
    ]
    items.append({
        "module_id": 2,
        "task": {
            "title": "Haszowalność krotek i symulacja ruchów na siatce (Grid Walk)",
            "description": desc_2_8,
            "time_limit": 2,
            "memory_limit": 128000
        },
        "test_cases": [
            {
                "input_data": inp,
                "expected_output": solve_2_8(inp),
                "is_hidden": hidden
            }
            for inp, hidden in inputs_2_8
        ]
    })

    return items

def main():
    items = build_tasks()
    batch_data = {
        "items": items,
        "dry_run": False
    }

    output_path = "tasks_batch.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(batch_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated {len(items)} tasks into {output_path}")
    total_tests = sum(len(item["test_cases"]) for item in items)
    hidden_tests = sum(sum(1 for tc in item["test_cases"] if tc["is_hidden"]) for item in items)
    sample_tests = total_tests - hidden_tests
    print(f"Total test cases: {total_tests} (Sample: {sample_tests}, Hidden: {hidden_tests})")
    
    # Validation
    for i, it in enumerate(items, 1):
        m_id = it["module_id"]
        t = it["task"]
        tcs = it["test_cases"]
        print(f"Task {i:02d} [Module {m_id}]: {t['title']} ({len(tcs)} test cases)")

if __name__ == "__main__":
    main()
