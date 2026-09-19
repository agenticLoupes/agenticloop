"""SQLite access. [OWNER: A]  One connection per request, WAL mode.

init_db(path) runs db/schema.sql then db/seed.sql if the patients table is empty.
Every tool in tools/ uses get_conn(). Persistence across sessions is the file.
"""
