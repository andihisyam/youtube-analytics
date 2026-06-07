# YouTube Analytics Dashboard

React dashboard for the YouTube social media analytics pipeline.

## Refresh Data

From the project root:

```powershell
python src\export_dashboard_data.py
```

This regenerates:

```text
dashboard/public/data/dashboard-data.json
```

## Run Dashboard

From this dashboard folder:

```powershell
npm install
npm run dev
```

The app reads the generated JSON file and renders KPI, sentiment, comment, keyword, and model comparison views.
