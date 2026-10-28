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

## Wdrażanie frontendu na Azure

Na serwerze Azure, w katalogu projektu, uruchom:

```bash
chmod +x deploy_front.sh
./deploy_front.sh
```

Skrypt kopiuje `front/index.html`, `front/styles.css` oraz `front/app.js`
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