# QA playbook (excerpt)

Documentation a QA persona "knows" and applies when critiquing a plan.

- **Rollback first.** Any change to a live path must have a tested rollback before it ships.
- **The cutover is the risk, not the code.** Coordinated-downtime plans fail on the window, not the diff.
- **Auth changes need a re-auth + privilege-change test matrix**, not just a happy-path login test.
- **A feature flag is not a test plan.** Flags add a combinatorial surface that must itself be tested.
- **"No spare capacity" means no time to fix what the migration breaks** — weigh that against the deadline.
