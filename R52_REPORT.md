# R52: unseen real-checkout source question

Date: 2026-09-11

Kairo's `Questioner` was run read-only against the authoritative Kairo
checkout with the question `what does this program do?`. It returned
`status=answered`, `scope=source summary only; runtime behavior requires
execution evidence`, and 268 Python files were summarized. Evidence included
the new N0/R0 modules and source operations such as `sqlite3.connect`,
`subprocess.Popen`, `subprocess.run`, `unlink`, and `write_text`.

The result correctly separated source evidence from runtime proof, but its
answer aggregated the whole research checkout and included potentially
dangerous operations from source summaries. This is useful as a base-path
stress result, not a claim that those operations were executed. The next
base improvement is scope-aware entry-point selection and clearer grouping of
research harnesses versus the public question layer.
