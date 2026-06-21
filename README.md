# Automated Testing Suite for State Employment Portal (gsz.gov.by)

This repository contains a production-ready test automation framework for the state employment website. The project is built using **Python**, **Playwright**, and **Pytest**, following top industry practices like the **Page Object Model (POM)** and dynamic data-driven testing.

---

## 🛠️ Tech Stack & Architecture

*   **Language**: Python 3.11+
*   **Core Framework**: Playwright (Sync API) — for fast, modern, and headless browser automation.
*   **Test Runner**: Pytest — for scalable test suites and fixtures management.
*   **Design Pattern**: Page Object Model (POM) — isolates page structure from test logic.
*   **Reporting**: Allure Framework — provides rich, visual HTML reports with steps and screenshots.
*   **Logging**: Built-in Python `logging` module — records real-time XHR/Fetch network traffic during execution.

---

## 📋 Key Features & Test Coverage

### 🧑‍💼 Job Seeker Profile Management
*   **FIO & Personal Data**: Validates default account values, handles profile updates, and covers multi-step rollback.
*   **Cascading Select2 Filtering**: Automated verification of linked drop-downs (Region ➡️ District ➡️ City) with dynamic AJAX wait times.
*   **Dynamic Formsets**: Robust tests for adding and removing extra contact fields (phones, emails) and workspace history rows.

### 📄 Resume Lifecycle
*   **Draft Creation**: Automates data entry for multi-tab forms including skills tags, education, languages, and salary targets.
*   **Publication Workflow**: Verifies state triggers, status transitions, and enforces the platform limit of maximum 3 published resumes.

### 🔍 Guest-Mode Vacancy Search
*   **Partial Text Matching**: Validates search engine behaviors using root word queries.
*   **Complex Filtering**: Automated end-to-end checks for wage ranges, working modes, and age-restricted job criteria.
*   **Access Control Security**: Confirms server-side locks and disabled UI elements for unauthenticated guests.

---

## ⚙️ CI/CD & Configuration Stability

*   **Global Session Auth**: Features a pre-test authentication hook that saves cookies to a local JSON state, cutting suite runtime by avoiding repeated logins.
*   **Robust Flakiness Defense**: Overrides test delays with custom `slow_mo` flags to ensure test stability on slower environments.
*   **Automated Artifacts**: Captures video recordings and snaps full-page screenshots attached directly to Allure on any test failure.

---

## 🚀 Quick Start

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Alegri1989/Test_rep.git
    cd Test_rep
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

3.  **Setup Configuration**:
    Create a `config.json` file in the root directory based on the provided sample template.

4.  **Run the entire test suite**:
    ```bash
    pytest --alluredir=allure-results
    ```

5.  **Generate and view report**:
    ```bash
    allure serve allure-results
    ```