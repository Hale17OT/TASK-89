-- MedRights Database Initialization
-- This runs automatically on first Docker MySQL startup.
-- Django migrations handle table creation; this handles MySQL-level grants.

-- Ensure proper character set
ALTER DATABASE medrights CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant full access to application user (Django manages schema)
GRANT ALL PRIVILEGES ON medrights.* TO 'medrights_app'@'%';
FLUSH PRIVILEGES;

-- Note: DELETE revocations on financial/audit tables are applied
-- via Django migrations after those tables are created (Module 5/6).

-- ================================================================
-- Audit Log Partitioning
-- ================================================================
-- After Django migrations create the audit_log table, apply RANGE
-- partitioning for the 180-day active / 7-year archive retention
-- policy.  This must run AFTER the initial migration completes.
--
-- The partition boundaries use TO_DAYS() on the created_at column.
-- The Celery Beat task `maintain_partitions` inspects and logs the
-- current partition state monthly.
--
-- Example (adjust dates for actual deployment):
--
-- ALTER TABLE audit_log PARTITION BY RANGE (TO_DAYS(created_at)) (
--     PARTITION p_active VALUES LESS THAN (TO_DAYS('2027-01-01')),
--     PARTITION p_archive VALUES LESS THAN (TO_DAYS('2034-01-01')),
--     PARTITION p_future VALUES LESS THAN MAXVALUE
-- );
--
-- Note: Django's ORM does not natively support partitioned tables.
-- The above DDL should be applied as a post-migration step during
-- initial deployment.  Subsequent partition management is handled
-- by the `maintain_partitions` Celery task.
-- ================================================================
