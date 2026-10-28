# MechaCode

## Diagram ERD

```mermaid
---
config:
  layout: elk
---
erDiagram
    COURSE ||--o{ MODULE : "posiada"
    MODULE ||--o{ TASK : "zawiera"
    TASK ||--o{ TEST_CASE : "ma"
    USER ||--o{ TASK_SUBMISSION : "wysyła"
    TASK ||--o{ TASK_SUBMISSION : "zbiera"
    TASK_SUBMISSION ||--o{ SUBMISSION_TEST_RESULT : "ma wyniki"
    TEST_CASE ||--o{ SUBMISSION_TEST_RESULT : "jest sprawdzany"

    COURSE {
        int id PK
        string title
        text description
        string language "cpp, python, java"
        int language_id "np. 54, 71, 62"
    }

    MODULE {
        int id PK
        int course_id FK
        string title
        int order_index
    }

    TASK {
        int id PK
        int module_id FK
        string title
        text description
        float time_limit "sekundy"
        int memory_limit "kilobajty"
        string tags "łatwe, trudne itp."
        text solution "wzorcowe rozwiązanie"
    }

    TEST_CASE {
        int id PK
        int task_id FK
        text input_data
        text expected_output
        boolean is_hidden
    }

    USER {
        int id PK
        string email
        string hashed_password
        string role "student, admin, teacher"
        int semester "semestr studiów (1-10)"
        int start_year "rok rozpoczęcia (np. 2026)"
        string major "kierunek: mechatro, AIR"
    }

    TASK_SUBMISSION {
        int id PK
        int user_id FK
        int task_id FK
        text source_code
        int language_id "domyślnie 54 (C++)"
        string judge0_token "token zgodności"
        int status_id "np. 1 (In Queue), 3 (Accepted)"
        float score "procent zaliczonych testów"
        int total_tests
        int passed_tests
        int error_count
        float execution_time
        int memory_used
        int attempt_number "telemetria"
        float time_since_last_attempt "telemetria"
        boolean is_abandoned "telemetria"
        datetime created_at
    }

    SUBMISSION_TEST_RESULT {
        int id PK
        int submission_id FK
        int test_case_id FK
        string judge0_token
        int status_id "status wykonania testu"
        text stdout
        text stderr
        text compile_output
        float execution_time
        int memory_used
        boolean passed
    }
```

`TASK_SUBMISSION` reprezentuje jedno wysłanie rozwiązania przez użytkownika.
Judge0 wykonuje każdy przypadek testowy osobno, dlatego jeden submission może
mieć wiele rekordów `SUBMISSION_TEST_RESULT`. Każdy z nich przechowuje osobny
token Judge0 oraz wynik konkretnego testu.

Pole `solution` w tabeli `TASK` przechowuje oficjalne, wzorcowe rozwiązanie
zadania (kod źródłowy w języku danego kursu), które jest wyświetlane w zakładce
"Rozwiązania" na platformie.

## Migracje bazy danych

Wszystkie migracje schematu bazy danych znajdują się w katalogu `DB/migrations/`.
W przypadku aktualizacji schematu bazy na środowisku produkcyjnym, należy wykonać
odpowiedni skrypt SQL na kontenerze bazy danych `mechacode-db`, np.:

```bash
docker exec -i mechacode-db psql -U mechacode_user -d mechacode_db < DB/migrations/20261028_add_task_solution.sql
```

Dostępne migracje:
- `20261028_add_user_academic_fields.sql` – dodanie pól akademickich (`semester`, `start_year`, `major`) do tabeli `users`.
- `20261028_add_task_tags.sql` – dodanie kolumny `tags` (poziom trudności) do tabeli `tasks`.
- `20261028_add_course_language.sql` – dodanie kolumn `language` i `language_id` do tabeli `courses`.
- `20261028_add_task_solution.sql` – dodanie kolumny `solution` do tabeli `tasks`.

## Uprawnienia ról API

Platforma wspiera trzy role użytkowników:
- **`student`**: Przeglądanie katalogu kursów, zadań (z odfiltrowanymi ukrytymi testami), wysyłanie rozwiązań oraz przeglądanie wyłącznie własnych zgłoszeń i historii. Brak dostępu do endpointów modyfikujących strukturę kursów lub konta innych użytkowników.
- **`teacher`**: Wszystkie uprawnienia studenta oraz pełne zarządzanie kursami, modułami, zadaniami i przypadkami testowymi (`POST`, `PUT`, `DELETE` dla `/courses/`, `/modules/`, `/tasks/`, `/test-cases/`). Podgląd ukrytych testów oraz zgłoszeń dowolnego studenta.
- **`admin`**: Pełne uprawnienia w systemie, w tym zarządzanie użytkownikami (`GET`, `PUT`, `DELETE` na `/users/`) oraz zmiana ról.

## Wdrażanie frontendu na Azure

Na serwerze Azure, w katalogu projektu, uruchom:

```bash
chmod +x deploy_front.sh
./deploy_front.sh
```

Skrypt kopiuje pliki frontendu (`index.html`, `styles.css`, `app.js`, `marked.min.js`, `katex.min.js`, `katex.min.css`)
do `/var/www/mechacode-front`. Jeśli katalog docelowy ma inną lokalizację, można ją przekazać
przez zmienną:

```bash
WEB_ROOT=/www ./deploy_front.sh
```

Skrypt używa `sudo` do utworzenia katalogu i instalacji plików z prawami
`0644`.

## Pełne wdrożenie na Azure

Skrypt `deploy_all.sh` pobiera najnowszy kod, przebudowuje obraz API bez
cache, odtwarza wszystkie usługi Docker Compose oraz kopiuje frontend do
`/var/www/mechacode-front`:

```bash
cd ~/mechacode/Mecha2Code
chmod +x deploy_all.sh deploy_front.sh
./deploy_all.sh
```

Repozytorium Git powinno znajdować się w `~/mechacode/Mecha2Code` (albo
w katalogu `~/mechacode`). Jeśli projekt nie został jeszcze sklonowany:

```bash
cd ~/mechacode
git clone <URL_REPOZYTORIUM> Mecha2Code
cd Mecha2Code
./deploy_all.sh
```

Skrypt używa `docker compose up -d --force-recreate`, ale nie wykonuje
`docker compose down`, więc nie usuwa ani nie odłącza volume'ów baz danych.