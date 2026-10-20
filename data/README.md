# Dataset: Quillmoor Software (fictional)

All companies, people, customers, vendors and figures in this dataset are **fictional**.
Email addresses use the reserved `.example` domain.

## The company

**Quillmoor Software** is a mid-size B2B SaaS company (182 employees in mid-2026) with offices
in Milan and Lisbon. It sells **Ledgerline**, an accounts-payable automation platform, and
**Ledgerline Insights**, a spend-analytics add-on.

## Contents

| Path | Description |
|---|---|
| `documents` | 42 documents in Markdown, PDF and DOCX, grouped by department |
| `manifest.yaml` | Metadata for every document: id, title, department, format, `allowed_groups`, effective date, `current`/`superseded` status |
| `users.yaml` | Groups and 8 users with different permissions |

### Documents by department

| Folder | Documents | Formats |
|---|---|---|
| `company/` | 15 company-wide policies and guides | 13 MD, 1 PDF, 1 DOCX |
| `hr/` | 6 People & Culture documents | 4 MD, 1 PDF, 1 DOCX |
| `sales/` | 8 Sales documents | 7 MD, 1 PDF |
| `finance/` | 5 Finance documents | 2 MD, 2 PDF, 1 DOCX |
| `engineering/` | 7 Engineering documents | 7 MD |
| `leadership/` | 1 board document | 1 DOCX |

## Access model

A user can read a document only if they belong to **at least one** of the document's
`allowed_groups`. There is no implicit inheritance: being a manager or an executive does
not grant access to everything. For example, the CEO cannot read the HR employee
relations summary, and managers cannot read salary bands.

| User | Role | Groups |
|---|---|---|
| alice.moretti | HR Business Partner | all_staff, hr |
| ben.okafor | Account Executive | all_staff, sales |
| carla.jensen | Finance Controller | all_staff, finance |
| david.lindqvist | Backend Engineer | all_staff, engineering |
| elena.rossi | Engineering Manager | all_staff, engineering, managers |
| grace.tanaka | Sales Director | all_staff, sales, managers |
| frank.adeyemi | CEO | all_staff, managers, executives |
| henry.walsh | Marketing Associate | all_staff |

## Built-in challenges

The corpus is designed to test a retrieval-augmented assistant on purpose:

- **Superseded versions.** Four policies exist in a 2025 and a 2026 version with different
  values (remote work, annual leave, travel and expenses, pricing and discounts). The assistant
  must use the current version unless the question asks about the past.
- **Confidential information.** Salary bands, financial results, board decisions and employee
  relations data are restricted to small groups.
- **Cross-document answers.** Some answers require combining two documents, such as a price
  list and a commission plan.
- **Mixed formats.** PDFs contain tables; DOCX files contain tables and bullet lists.
- **Missing information.** Some plausible questions have no answer in the corpus.

The evaluation questions are in `evals/questions.yaml`.
