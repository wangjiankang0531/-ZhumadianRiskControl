# Reservation edit: synchronize end time and roll back partial writes

Editing a synthetic local reservation updated its end time while the special-work ledger retained the old value after reload. The original shared edit omitted the typed work end-time assignment. Actual SQL verification additionally showed partial changes after a later write failed during an unproxied call.

The V2 pinned-source adapter adds only the missing end-time assignment and an explicit rollbackFor=Exception transaction annotation to the shared reservation edit. It preserves original identifiers, eight typed entities, personnel replacement order, statuses, notification logic and the save path. Reference is read-only; no schema or historical data migration is included.

The real original and candidate methods pass eight and sixteen strict in-memory capture cases respectively, including candidate annotation and executed-class byte checks. Using original MyBatis mappers/XML and ten connection-local MySQL tables, the original ten cases characterize the stale time and unproxied partial write; the candidate eleven cases verify typed time persistence and real Spring annotation-driven rollback. Permanent ten-table row multisets and schemas remain unchanged; temporary tables are dropped. The first fixture time comparison failed and is preserved; typed LocalDateTime reads passed the revised execution. Null assignment is not proof of SQL field clearance.

These SQL/proxy checks do not prove the running application's transaction advisor, authenticated HTTP, roles, page persistence or complete workflows. The five-file V2 local delivery is prepared and all retained payload hashes preflighted. Seven reservation-scope checks and six existing inspection-scope checks passed. V1 is sealed and retired; V2 has not been installed or started.

After the pending Excel handoff, normal owned shutdown, code backup, precise update, startup, same-data restart, actual class/advisor verification and cross-entry page testing remain required. Keep the discrepancy sample as evidence; do not repair it with direct SQL. Public finding persistence, role workflows, original attachments, other modules and H5 remain open. B/S replication stays ahead of LOD work and full clone readiness remains false.

Keep SDK/Reference sources, classes, credentials, database files, runtime packages, screenshots and private execution records out of Git.
