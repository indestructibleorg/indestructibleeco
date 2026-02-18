-- Test-only migration: Install pgTAP for unit testing
-- This extension is only needed for development and testing
-- Do NOT deploy to production

CREATE EXTENSION IF NOT EXISTS "pgtap" WITH SCHEMA pgtap;

-- Example pgtap test (uncomment to use)
-- SELECT plan(1);
-- SELECT is(1, 1, 'Basic math works');
-- SELECT finish();
