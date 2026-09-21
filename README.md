# ICA0024 concept glossary

An editable, tool-neutral study reference for the first three Infrastructure as Code lectures. The glossary contains **45 terms**, grouped by lecture and alphabetized within each group.

This repository owns the glossary source, formatting code, generated exports, and VS Code tasks. The [questionnaires](https://github.com/Infra-as-code-ICA0024-TalTech/questionnaires) are maintained separately. Neither repository needs a checkout of the other to build.

## Files

- [source/Glossary.md](source/Glossary.md): the editable Markdown source.
- [exports/glossary.html](exports/glossary.html): a formatted browser reference.
- [exports/glossary.pdf](exports/glossary.pdf): a six-page printable reference.
- [exports/moodle-glossary.xml](exports/moodle-glossary.xml): terms and lecture categories for a Moodle Glossary activity.
- [docs/validation.json](docs/validation.json): results of the local export checks.

## Build with VS Code

Open this repository folder and choose **Terminal > Run Task**:

1. Run **Glossary: Set up dependencies** once after cloning, and after dependency changes. It creates `.venv` and installs the pinned requirements. Python 3.12+ and internet access are required for setup.
2. Edit `source/Glossary.md`.
3. Run **Glossary: Convert all formats** to generate HTML, PDF, and Moodle XML. This is also the default build task.
4. Run **Glossary: Validate exports** to check the existing outputs without rebuilding them.

Tasks support macOS/Linux and Windows. The Windows setup task uses the `py` launcher. Conversion uses the repository's own `.venv` directly; it does not reinstall packages on every run.

## Build from the command line

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py
.venv/bin/python scripts/build.py --check
```

On Windows, use `py -3 -m venv .venv` and `.venv\Scripts\python.exe` for the remaining commands. Edit the source, then commit it together with regenerated exports. Do not edit generated files directly.

The converter uses Python Markdown and ReportLab, with pypdf for verification. It checks unique terms, lecture structure, full HTML/XML agreement with the source, XML term/category round trips, and the presence of every definition in the PDF. The existing six PDF pages were visually reviewed. **Live Moodle glossary import has not yet been tested.**

## Edit the glossary

Use one `#` title followed by an introduction, headings `## Lecture 1: ...` through `## Lecture 3: ...`, and a `### Term` heading followed by its definition for each entry. Term names must be unique across lectures. Use prose paragraphs; inline Markdown emphasis is supported. The exporter sorts terms alphabetically within each lecture.

Explain concepts and useful distinctions without requiring product-specific syntax. The current converter expects the three lecture groups; extending the course scope requires updating that validation and the HTML navigation and PDF footer in `scripts/glossary.py`.

## Import into Moodle

Create or open a **Glossary** activity, choose **Import entries**, upload `exports/moodle-glossary.xml`, and enable category import to retain the lecture groups. Use the glossary importer, not the quiz question-bank importer. The definitions use HTML; automatic linking is disabled in the exported entries. Preview the imported terms before sharing the activity.

Reference: [Moodle glossary import documentation](https://docs.moodle.org/501/en/Import_glossary_entries).

The HTML and PDF are reading materials. Microsoft Forms Quick Import is for questionnaires and is not needed for the glossary.

## Origin and access

The glossary was moved from the questionnaires repository after [commit 91bde2e](https://github.com/Infra-as-code-ICA0024-TalTech/questionnaires/commit/91bde2e). Its content and exported documents were preserved during the move.

The repository is private in `Infra-as-code-ICA0024-TalTech` and uses the organization's existing member permissions.
