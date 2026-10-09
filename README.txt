El-Sharnouby BI & AI dashboard (Streamlit)

1) Put this "dashboard" folder inside HVIA-task2 (next to the "clean" folder).
2) In the VS Code terminal:
      cd dashboard
      streamlit run app.py
3) The browser opens at http://localhost:8501

Files
  app.py          the menu (which pages exist)
  utils.py        data loading + every calculation (one place only)
  views/*.py      one file per page
  .streamlit/     colors / theme
  requirements.txt  libraries needed (for Streamlit Cloud later)
