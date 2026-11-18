# ICA0024 concept glossary

Published on GitHub Pages: https://infra-as-code-ica0024-taltech.github.io/glossary/ (HTML, plus `glossary.pdf` and `moodle-glossary.xml`), rebuilt and validated on every push to `main`.

An editable, tool-neutral study reference for Infrastructure as Code Lectures 1-9. The glossary contains **122 terms**, grouped by the lecture that first explains them and alphabetized within each group. Each build records the current term, lecture and PDF page counts in [docs/validation.json](docs/validation.json).

This repository owns the glossary source, formatting code, generated exports, and VS Code tasks. The [questionnaires](https://github.com/Infra-as-code-ICA0024-TalTech/questionnaires) are maintained separately. Neither repository needs a checkout of the other to build.

## Files

- [source/Glossary.md](source/Glossary.md): the editable Markdown source.
- [exports/glossary.html](exports/glossary.html): a standalone browser reference with lecture navigation and a term search.
- [exports/glossary.pdf](exports/glossary.pdf): a printable A4 reference with a contents page.
- [exports/moodle-glossary.xml](exports/moodle-glossary.xml): terms and lecture categories for a Moodle Glossary activity.
- [docs/validation.json](docs/validation.json): results of the local export checks, including terms per lecture.
- [assets/](assets): the eXtreme Automation (XA) logo inlined into the HTML, and the PT Sans and JetBrains Mono fonts embedded into the PDF, each with its SIL Open Font License (`OFL.txt`).

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

The converter uses Python Markdown and ReportLab, with pypdf for verification. It checks unique terms, consecutive lecture numbering, italic cross-references, full HTML/XML agreement with the source, XML term/category round trips, the presence of every lecture heading, term and definition in the PDF, and that the PDF uses only the bundled fonts. The PDF was visually reviewed after the Lectures 1-9 update. **Live Moodle glossary import has not yet been tested.**

## Design

The HTML and PDF follow the [eXtreme Automation (XA) design system](https://ui.extremeautomation.io/): PT Sans and JetBrains Mono, navy headings, rose accents and muted secondary text on a light canvas. The HTML inlines the XA logo and its CSS so it can be opened as a single file; it loads the fonts from Google Fonts and falls back to system fonts offline. Search and the highlighted lecture in the navigation need JavaScript; without it, all terms are shown. The PDF embeds the fonts from `assets/fonts`.

## Edit the glossary

Use one `#` title followed by an introduction, lecture headings `## Lecture 1: ...`, `## Lecture 2: ...` and so on, numbered consecutively, and a `### Term` heading followed by its definition for each entry. Term names must be unique across lectures: define a concept once, under the lecture that first explains it. Use prose paragraphs and `**bold**` where needed. The exporter sorts terms alphabetically within each lecture.

Italic text (`*Term*`) is reserved for cross-references: it must match another term's name (case-insensitive), becomes a link in the HTML, and stays italic in the PDF and Moodle. Explain concepts and useful distinctions without requiring product-specific syntax.

Adding a lecture needs no code changes: the HTML navigation, PDF contents and footer, Moodle categories and validation follow the lecture headings.

## Import into Moodle

Create or open a **Glossary** activity, choose **Import entries**, upload `exports/moodle-glossary.xml`, and enable category import to retain the lecture groups. Use the glossary importer, not the quiz question-bank importer. The definitions use HTML; automatic linking is disabled in the exported entries. Preview the imported terms before sharing the activity.

Reference: [Moodle glossary import documentation](https://docs.moodle.org/501/en/Import_glossary_entries).

The HTML and PDF are reading materials. Microsoft Forms Quick Import is for questionnaires and is not needed for the glossary.

## Origin and access

The glossary was moved from the questionnaires repository after [commit 91bde2e](https://github.com/Infra-as-code-ICA0024-TalTech/questionnaires/commit/91bde2e). Its content and exported documents were preserved during the move.

The repository is private in `Infra-as-code-ICA0024-TalTech` and uses the organization's existing member permissions.
