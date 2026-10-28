BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS semester INTEGER,
    ADD COLUMN IF NOT EXISTS start_year INTEGER,
    ADD COLUMN IF NOT EXISTS major VARCHAR(50);

-- Usunięcie starych kont z fake_hashed_
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'submission_test_results') THEN
        DELETE FROM submission_test_results WHERE submission_id IN (
            SELECT id FROM task_submissions WHERE user_id IN (
                SELECT id FROM users WHERE hashed_password LIKE 'fake_hashed_%'
            )
        );
    END IF;

    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'task_submissions') THEN
        DELETE FROM task_submissions WHERE user_id IN (
            SELECT id FROM users WHERE hashed_password LIKE 'fake_hashed_%'
        );
    END IF;

    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        DELETE FROM users WHERE hashed_password LIKE 'fake_hashed_%';
    END IF;
END $$;

UPDATE users
SET
    semester = COALESCE(semester, 1),
    start_year = COALESCE(start_year, 2026),
    major = COALESCE(major, 'mechatro')
WHERE semester IS NULL
   OR start_year IS NULL
   OR major IS NULL;

ALTER TABLE users
    ALTER COLUMN semester SET NOT NULL,
    ALTER COLUMN start_year SET NOT NULL,
    ALTER COLUMN major SET NOT NULL;

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS users_semester_check,
    ADD CONSTRAINT users_semester_check CHECK (semester BETWEEN 1 AND 10);

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS users_start_year_check,
    ADD CONSTRAINT users_start_year_check CHECK (start_year BETWEEN 2000 AND 2100);

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS users_major_check,
    ADD CONSTRAINT users_major_check CHECK (major IN ('mechatro', 'AIR'));

-- Utworzenie lub aktualizacja konta administratora z prawdziwym hashem bcrypt dla hasła 'admin'
INSERT INTO users (email, hashed_password, role, semester, start_year, major)
VALUES (
    'admin@mechacode.local',
    crypt('admin', gen_salt('bf', 12)),
    'admin',
    1,
    2026,
    'mechatro'
)
ON CONFLICT (email) DO UPDATE
SET
    hashed_password = crypt('admin', gen_salt('bf', 12)),
    role = 'admin',
    semester = 1,
    start_year = 2026,
    major = 'mechatro';

COMMIT;
