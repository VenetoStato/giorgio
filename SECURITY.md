# Security policy

Giorgio is a design and simulation project. **Nothing has been built or deployed**, so there are no production systems
or user data at risk. Reports are still very welcome, because the code and the design are meant to be reused.

## What to report

- **Software**: vulnerabilities in `giorgio_os/` (operator web console, REST API, natural-language agent, HAL), scripts
  or CI workflows, e.g. command injection, unauthenticated control endpoints, unsafe deserialisation, leaked secrets.
- **Safety-related design errors**: mistakes in the electrical or safety chain (`amr/electrical/`, `electrical/`,
  `amr/CALC.md`, `amr/ce/`) that could make a robot built from these files unsafe, such as a wrong stop category, an
  unrated element in a safety function, an undersized fuse or a wrong ISO 13855 distance. Non-urgent design questions
  can go to a normal issue with the "Design question" form.

## How to report privately

1. Preferred: use GitHub private vulnerability reporting. Open the repository's **Security** tab and click
   **Report a vulnerability** (or go to https://github.com/VenetoStato/giorgio/security/advisories/new).
2. Fallback: contact the repository owner, [@VenetoStato](https://github.com/VenetoStato), privately via GitHub and
   ask for a private channel. Please do not put exploit details in a public issue.

Include what is affected (file, commit), how to reproduce it, and the impact you expect.

## What to expect

This is a small, volunteer-run project. We aim to acknowledge a report within about a week and to agree on a fix and
a disclosure date with you. We will credit you in the fix unless you prefer otherwise. There is no bug bounty.

## Supported versions

Only the latest commit on `master` is maintained.
