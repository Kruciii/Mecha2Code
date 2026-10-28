BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS semester INTEGER,
    ADD COLUMN IF NOT EXISTS start_year INTEGER,
    ADD COLUMN IF NOT EXISTS major VARCHAR(50);

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

COMMIT;