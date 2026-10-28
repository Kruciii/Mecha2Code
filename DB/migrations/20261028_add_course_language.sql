BEGIN;

ALTER TABLE courses
    ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'cpp',
    ADD COLUMN IF NOT EXISTS language_id INTEGER DEFAULT 54;

UPDATE courses
SET
    language = COALESCE(language, 'cpp'),
    language_id = COALESCE(language_id, 54)
WHERE language IS NULL OR language_id IS NULL;

-- Aktualizacja dla kursu Pythona
UPDATE courses
SET
    language = 'python',
    language_id = 71
WHERE id = 3 OR lower(title) LIKE '%python%';

ALTER TABLE courses
    ALTER COLUMN language SET NOT NULL,
    ALTER COLUMN language_id SET NOT NULL;

COMMIT;
