# YOUNIQ: CHUNITHM Skill-Based Recommendation Tool
---

**YOUNIQ** is a **skill-based recommendation** tool designed for **experienced CHUNITHM** players. It analyzes your current **Best 50 (B50) records** and provides a calculated roadmap to your next rating goal by identifying the most efficient upscores and new charts to play based on your **unique skill profile**.

## 📝 Description

---

Unlike standard rating calculators, YOUNIQ doesn't just tell you your current rating; it projects your future progress. By dragging and dropping your play data via [tsaibee's CHUNI TOOLS](https://chuni.tsaibee.org), the tool:

*   **Identifies Rating Jumps**: Calculates the exact impact a specific target score will have on your overall B50 average.
*   **Smart Recommendations**: Uses a **K-Nearest Neighbors (KNN)** algorithm to suggest charts that match your historical skill strengths (e.g., **stamina**, **tech**, or **gimmicks**).
*   **Gap Analysis**: Automatically detects your **B50 floor** and suggests replacements for your weakest scores.

## 🛠️ Tools Used

---
*   **[Google Gemini 3 Flash (Paid Tier)](https://gemini.google.com/)**: An authentic, adaptive AI collaborator used for code optimization, architectural brainstorming, and technical documentation.

The application is built with **Python** and utilizes the following libraries:

*   **[Pandas](https://pandas.pydata.org) & [NumPy](https://numpy.org)**: For high-speed rating mathematics and data manipulation.
*   **[Scikit-Learn](https://scikit-learn.org/stable/)**: Powering the KNN model for skill-based song matching.
*   **[Tkinter](https://docs.python.org/3/library/tkinter.html) & [TkinterDnD2](https://pypi.org/project/tkinterdnd2/)**: Providing a modern, drag-and-drop graphical user interface.
*   **[Pillow (PIL)](https://pypi.org/project/pillow/)**: For handling high-quality asset rendering and icons.
*   **[PyInstaller](https://pypi.org/project/pyinstaller/)**: Used to compile the source into a standalone Windows executable.

## ⚙️ Installation

---

### For Users (Executable)
1.  Navigate to the **[Releases](https://github.com/TenshiSato69/YOUNIQ/releases)** section of this repository.
2.  Download the latest `YOUNIQ.zip`.
3.  Ensure `master.csv` is in the same folder as the executable.
> [!WARNING]
> The application will not work without `master.csv`

### For Developers (Source)
If you wish to run the script manually, ensure you have Python 3.10+ installed and run:

```bash
pip install pandas numpy scikit-learn Pillow tkinterdnd2
python chuni_gui.py
```

## 🚀 Instructions

---

1.  **Launch**: Open `youniq.exe`.
2.  **Import**: Drag your `player_data.csv` (exported from CHUNI TOOLS) into the dark blue drop zone.
3.  **Set Targets**:
    *   Choose **Target Rating** to see what scores are needed for a specific chart rating (e.g., 17.3).
    *   Choose **Target Score** to see how much your B50 moves if you hit a specific score (e.g., 1,007,500) on various charts.
4.  **Filter**: Use the Constant and Score range filters to narrow down your practice list.
5.  **Analyze**: Review the **Rating Jump** and **B50 After** columns to prioritize your next play session.

## 📚 References

---
*   **Score Evaluation**: This [link](https://chunithm.org/basic/evaluation/) from Codex's CHUNITHM English Guide
*   **Rating Formulas**: This [link](https://chunithm.org/intermediate/rating/#rating-formula-verse) from Codex's CHUNITHM English Guide
*   **Chart Constants**: [[CN7]CHUNITHM X-VERSE-X 譜面定数表 - Google スプレッドシート](https://docs.google.com/spreadsheets/d/1UgalRHELZBe4Wb4yKXffBJ6juj57bHgSdEWphCDsByE/edit?gid=1233839899#gid=1233839899)
*   **Skill Tags**: [CHUNITHM Chart Codex](https://docs.google.com/spreadsheets/d/1xP1huTSA-XWKZaDfmyNh-viRbUE777d2Rg54j5-2VAU/edit?usp=sharing) by Codex
*   **CHUNI TOOLS**: tsaibee's [CHUNI TOOLS](https://chuni.tsaibee.org)

