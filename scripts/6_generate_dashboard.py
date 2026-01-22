#!/usr/bin/env python3
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from utils import print_section, print_success, print_error

# Load results
print("\n=== Script 6: Dashboard ===")
print("Incarcare date...")

performance_data = None
cap_data = None

try:
    with open("results/performance_results.json", "r") as f:
        performance_data = json.load(f)
    print("  performance_results.json - ok")
except FileNotFoundError:
    print("  performance_results.json - nu exista")
    performance_data = {"postgresql": {"total_avg_ms": 0}, "mongodb": {"total_avg_ms": 0}, "queries": []}

try:
    with open("results/cap_analysis.json", "r") as f:
        cap_data = json.load(f)
    print("  cap_analysis.json - ok")
except FileNotFoundError:
    print("  cap_analysis.json - nu exista")
    cap_data = {"postgresql": {}, "mongodb": {}, "analysis": {}}

# Build query rows
query_rows = ""
for q in performance_data.get('queries', []):
    pg_time = q['postgresql']
    mongo_time = q['mongodb']
    diff = abs(pg_time - mongo_time)
    pct = (diff / max(pg_time, mongo_time) * 100) if max(pg_time, mongo_time) > 0 else 0
    if pg_time < mongo_time:
        winner = f'<span class="winner-badge pg-bg">PostgreSQL +{diff:.2f}ms ({pct:.0f}%)</span>'
    else:
        winner = f'<span class="winner-badge mongo-bg">MongoDB +{diff:.2f}ms ({pct:.0f}%)</span>'
    query_rows += f"""
                    <tr>
                        <td><strong>{q['name']}</strong></td>
                        <td class="pg-color"><strong>{pg_time:.2f}ms</strong></td>
                        <td class="mongo-color"><strong>{mongo_time:.2f}ms</strong></td>
                        <td>{winner}</td>
                    </tr>"""

# Chart data
query_names = json.dumps([q['name'] for q in performance_data.get('queries', [])])
pg_times = json.dumps([q['postgresql'] for q in performance_data.get('queries', [])])
mongo_times = json.dumps([q['mongodb'] for q in performance_data.get('queries', [])])

pg_total = performance_data['postgresql']['total_avg_ms']
mongo_total = performance_data['mongodb']['total_avg_ms']
ratio = mongo_total / pg_total if pg_total > 0 else 1
pg_winner_class = 'winner' if pg_total < mongo_total else ''
mongo_winner_class = 'winner' if mongo_total < pg_total else ''
winner_text = f'PostgreSQL este ~{ratio:.0f}x mai rapid (local vs cloud)' if pg_total < mongo_total else 'MongoDB este mai rapid'

# CAP data extraction
pg_cap = cap_data.get('postgresql', {})
mongo_cap = cap_data.get('mongodb', {})
pg_tests = pg_cap.get('tests', {})
mongo_tests = mongo_cap.get('tests', {})
pg_avail = pg_tests.get('availability', {})
mongo_avail = mongo_tests.get('availability', {})
pg_response = pg_avail.get('avg_response_ms', 0)
mongo_response = mongo_avail.get('avg_response_ms', 0)
pg_max_response = pg_avail.get('max_response_ms', 0)
mongo_max_response = mongo_avail.get('max_response_ms', 0)

# Transaction test results
pg_rollback = pg_tests.get('transaction_rollback', {})
pg_fk = pg_tests.get('foreign_key_constraint', {})
mongo_atomic = mongo_tests.get('atomic_update', {})
mongo_write = mongo_tests.get('write_concern', {})

current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
test_date = cap_data.get('test_date', current_date)

# Analysis data
pg_analysis = cap_data.get('analysis', {}).get('postgresql', {})
mongo_analysis = cap_data.get('analysis', {}).get('mongodb', {})


html_content = f'''<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostgreSQL vs MongoDB - Studiu Comparativ | BDNV</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --pg-color: #336791;
            --pg-light: #4a8dbd;
            --mongo-color: #4DB33D;
            --mongo-light: #6dd55d;
            --bg-dark: #0f0f1a;
            --bg-card: rgba(255,255,255,0.05);
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --accent: #4facfe;
            --accent-secondary: #00f2fe;
            --success: #4caf50;
            --warning: #ff9800;
            --danger: #f44336;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-dark);
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        /* Navigation */
        .navbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(15, 15, 26, 0.95);
            backdrop-filter: blur(20px);
            padding: 12px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .nav-brand {{
            font-size: 1.2rem;
            font-weight: bold;
            background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .nav-links {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }}
        
        .nav-btn {{
            background: var(--bg-card);
            border: 1px solid rgba(255,255,255,0.1);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.3s ease;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .nav-btn:hover {{
            background: rgba(79, 172, 254, 0.2);
            border-color: var(--accent);
            transform: translateY(-2px);
        }}
        
        .nav-btn.active {{
            background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
            border-color: transparent;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 90px 30px 30px;
        }}
        
        /* Hero */
        .hero {{
            text-align: center;
            padding: 50px 20px;
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.1), rgba(0, 242, 254, 0.05));
            border-radius: 30px;
            margin-bottom: 40px;
            border: 1px solid rgba(79, 172, 254, 0.2);
            position: relative;
            overflow: hidden;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(79, 172, 254, 0.1) 0%, transparent 50%);
            animation: rotate 20s linear infinite;
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        .hero-content {{ position: relative; z-index: 1; }}
        
        .hero h1 {{
            font-size: 2.8rem;
            margin-bottom: 15px;
            background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .hero .subtitle {{
            font-size: 1.3rem;
            color: var(--text-secondary);
            margin-bottom: 15px;
        }}
        
        .hero .meta {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 20px;
        }}
        
        .hero .meta-item {{
            background: rgba(0,0,0,0.3);
            padding: 8px 16px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }}
        
        .hero .meta-item i {{ color: var(--accent); }}
        
        /* Sections */
        .section {{
            margin-bottom: 40px;
            scroll-margin-top: 80px;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(79, 172, 254, 0.3);
        }}
        
        .section-header i {{
            font-size: 1.6rem;
            color: var(--accent);
        }}
        
        .section-header h2 {{
            font-size: 1.6rem;
            background: linear-gradient(90deg, var(--accent), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .section-header .badge {{
            margin-left: auto;
            background: rgba(79, 172, 254, 0.2);
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
            color: var(--accent);
        }}
        
        /* Grids */
        .grid-2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; }}
        .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; }}
        .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
        .grid-6 {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 15px; }}
        
        @media (max-width: 1200px) {{
            .grid-3, .grid-4, .grid-6 {{ grid-template-columns: repeat(3, 1fr); }}
        }}
        @media (max-width: 900px) {{
            .grid-2, .grid-3, .grid-4, .grid-6 {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @media (max-width: 600px) {{
            .grid-2, .grid-3, .grid-4, .grid-6 {{ grid-template-columns: 1fr; }}
            .nav-links {{ display: none; }}
            .hero h1 {{ font-size: 1.8rem; }}
        }}
        
        /* Cards */
        .card {{
            background: var(--bg-card);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.08);
            transition: all 0.3s ease;
        }}
        
        .card:hover {{
            border-color: rgba(79, 172, 254, 0.3);
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.3);
        }}
        
        .card-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }}
        
        .card-header i {{ font-size: 1.3rem; }}
        .card-header h3 {{ font-size: 1.1rem; color: var(--text-primary); }}
        
        .card.pg-card {{ border-left: 4px solid var(--pg-color); }}
        .card.mongo-card {{ border-left: 4px solid var(--mongo-color); }}
        
        /* Stat Cards */
        .stat-card {{
            background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-3px);
            border-color: var(--accent);
        }}
        
        .stat-card .icon {{
            font-size: 1.8rem;
            margin-bottom: 12px;
            color: var(--accent);
        }}
        
        .stat-card .value {{
            font-size: 2.2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-card .label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        .stat-card.winner {{
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.2), rgba(0, 242, 254, 0.1));
            border: 2px solid var(--accent);
            animation: glow 2s ease-in-out infinite alternate;
        }}
        
        @keyframes glow {{
            from {{ box-shadow: 0 0 15px rgba(79, 172, 254, 0.3); }}
            to {{ box-shadow: 0 0 30px rgba(79, 172, 254, 0.5); }}
        }}
        
        /* Colors */
        .pg-color {{ color: var(--pg-light) !important; }}
        .mongo-color {{ color: var(--mongo-light) !important; }}
        .pg-bg {{ background: var(--pg-color) !important; }}
        .mongo-bg {{ background: var(--mongo-color) !important; }}
        .success {{ color: var(--success) !important; }}
        .warning {{ color: var(--warning) !important; }}
        .danger {{ color: var(--danger) !important; }}
        
        /* Tables */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        .data-table th, .data-table td {{
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        
        .data-table th {{
            background: rgba(79, 172, 254, 0.15);
            color: var(--accent);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }}
        
        .data-table tr:hover {{ background: rgba(255,255,255,0.03); }}
        .data-table tr:last-child td {{ border-bottom: none; }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        .badge.pg {{
            background: rgba(51, 103, 145, 0.3);
            color: var(--pg-light);
            border: 1px solid var(--pg-color);
        }}
        
        .badge.mongo {{
            background: rgba(77, 179, 61, 0.3);
            color: var(--mongo-light);
            border: 1px solid var(--mongo-color);
        }}
        
        .badge.success {{
            background: rgba(76, 175, 80, 0.3);
            color: var(--success);
            border: 1px solid var(--success);
        }}
        
        .winner-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.7rem;
            font-weight: bold;
            color: white;
        }}
        
        /* Charts */
        .chart-container {{
            position: relative;
            height: 320px;
            margin: 15px 0;
        }}
        
        .chart-container.small {{ height: 220px; }}
        .chart-container.large {{ height: 400px; }}
        
        /* Feature Lists */
        .feature-list {{
            list-style: none;
            padding: 0;
        }}
        
        .feature-list li {{
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 0.95rem;
        }}
        
        .feature-list li:last-child {{ border-bottom: none; }}
        .feature-list li i {{ color: var(--accent); width: 18px; margin-top: 3px; }}
        .feature-list li.check i {{ color: var(--success); }}
        .feature-list li.cross i {{ color: var(--danger); }}
        .feature-list li.partial i {{ color: var(--warning); }}
        
        /* Schema Boxes */
        .schema-box {{
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 18px;
            margin-top: 12px;
        }}
        
        .schema-box h4 {{
            color: var(--accent);
            margin-bottom: 12px;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .schema-code {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.8rem;
            color: #e0e0e0;
            line-height: 1.7;
        }}
        
        .schema-code .keyword {{ color: #c792ea; }}
        .schema-code .type {{ color: #82aaff; }}
        .schema-code .comment {{ color: #546e7a; }}
        
        /* Comparison */
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }}
        
        .comparison-column {{
            background: rgba(0,0,0,0.2);
            border-radius: 15px;
            padding: 22px;
        }}
        
        .comparison-column.pg {{ border-top: 4px solid var(--pg-color); }}
        .comparison-column.mongo {{ border-top: 4px solid var(--mongo-color); }}
        
        .comparison-column h4 {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 18px;
            font-size: 1.2rem;
        }}
        
        /* Progress Bars */
        .progress-bar {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin-top: 6px;
        }}
        
        .progress-bar .fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 1s ease;
        }}
        
        .progress-bar .fill.pg {{ background: linear-gradient(90deg, var(--pg-color), var(--pg-light)); }}
        .progress-bar .fill.mongo {{ background: linear-gradient(90deg, var(--mongo-color), var(--mongo-light)); }}
        
        /* Metrics */
        .metrics-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        
        .metrics-row:last-child {{ border-bottom: none; }}
        .metrics-row .label {{ color: var(--text-secondary); font-size: 0.9rem; }}
        .metrics-row .value {{ font-weight: bold; font-size: 1rem; }}
        
        /* Tabs */
        .tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .tab-btn {{
            background: var(--bg-card);
            border: 1px solid rgba(255,255,255,0.1);
            color: var(--text-secondary);
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .tab-btn:hover {{
            border-color: var(--accent);
            color: var(--text-primary);
        }}
        
        .tab-btn.active {{
            background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
            border-color: transparent;
            color: white;
        }}
        
        .tab-content {{ display: none; }}
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.4s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Info Boxes */
        .info-box {{
            background: rgba(79, 172, 254, 0.1);
            border: 1px solid rgba(79, 172, 254, 0.3);
            border-radius: 12px;
            padding: 18px;
            margin: 15px 0;
        }}
        
        .info-box.success {{
            background: rgba(76, 175, 80, 0.1);
            border-color: rgba(76, 175, 80, 0.3);
        }}
        
        .info-box.warning {{
            background: rgba(255, 152, 0, 0.1);
            border-color: rgba(255, 152, 0, 0.3);
        }}
        
        .info-box h4 {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            color: var(--accent);
        }}
        
        .info-box.success h4 {{ color: var(--success); }}
        .info-box.warning h4 {{ color: var(--warning); }}
        
        .info-box p {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.6;
        }}
        
        /* Summary Card */
        .summary-card {{
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.1), rgba(0, 242, 254, 0.05));
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(79, 172, 254, 0.2);
            text-align: center;
        }}
        
        .summary-card h3 {{
            color: var(--accent);
            font-size: 1.2rem;
            margin-bottom: 18px;
        }}
        
        /* Code Block */
        .code-block {{
            background: rgba(0,0,0,0.4);
            border-radius: 10px;
            padding: 15px;
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            margin: 10px 0;
        }}
        
        /* Test Result Card */
        .test-result {{
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 18px;
            margin: 10px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .test-result .icon {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }}
        
        .test-result .icon.success {{
            background: rgba(76, 175, 80, 0.2);
            color: var(--success);
        }}
        
        .test-result .icon.failed {{
            background: rgba(244, 67, 54, 0.2);
            color: var(--danger);
        }}
        
        .test-result .details {{
            flex: 1;
        }}
        
        .test-result .details h4 {{
            font-size: 1rem;
            margin-bottom: 5px;
        }}
        
        .test-result .details p {{
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
        
        /* Timeline */
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        
        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: rgba(79, 172, 254, 0.3);
        }}
        
        .timeline-item {{
            position: relative;
            padding: 15px 0;
        }}
        
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -24px;
            top: 20px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent);
        }}
        
        .timeline-item h4 {{
            font-size: 1rem;
            margin-bottom: 5px;
        }}
        
        .timeline-item p {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            padding: 35px;
            margin-top: 40px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: var(--text-secondary);
        }}
        
        footer .links {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 12px;
        }}
        
        footer a {{
            color: var(--accent);
            text-decoration: none;
        }}
        
        footer a:hover {{ text-decoration: underline; }}
        
        @media print {{
            .navbar {{ display: none; }}
            .container {{ padding-top: 0; }}
            body {{ background: white; color: black; }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-brand">
            <i class="fas fa-database"></i>
            BDNV - Studiu Comparativ
        </div>
        <div class="nav-links">
            <a href="#overview" class="nav-btn active"><i class="fas fa-home"></i> Overview</a>
            <a href="#performance" class="nav-btn"><i class="fas fa-tachometer-alt"></i> Performanta</a>
            <a href="#cap" class="nav-btn"><i class="fas fa-project-diagram"></i> CAP</a>
            <a href="#acid" class="nav-btn"><i class="fas fa-atom"></i> ACID/BASE</a>
            <a href="#schema" class="nav-btn"><i class="fas fa-sitemap"></i> Schema</a>
            <a href="#indexing" class="nav-btn"><i class="fas fa-search"></i> Indexare</a>
            <a href="#scaling" class="nav-btn"><i class="fas fa-expand-arrows-alt"></i> Scalare</a>
            <a href="#tests" class="nav-btn"><i class="fas fa-vial"></i> Teste</a>
            <a href="#recommendations" class="nav-btn"><i class="fas fa-check-circle"></i> Concluzii</a>
        </div>
    </nav>

    <div class="container">
        <!-- Hero Section -->
        <div class="hero">
            <div class="hero-content">
                <h1>🐘 PostgreSQL vs 🍃 MongoDB</h1>
                <p class="subtitle">Studiu Comparativ Complet pentru Platforma E-Commerce</p>
                <p style="color: var(--text-secondary); font-size: 0.95rem;">
                    Analiza detaliata: Performanta • CAP Theorem • ACID vs BASE • Scalabilitate • Indexare • Recomandari
                </p>
                <div class="meta">
                    <div class="meta-item">
                        <i class="fas fa-calendar-alt"></i>
                        {current_date}
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-server"></i>
                        PostgreSQL 16.3 (Local)
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-cloud"></i>
                        MongoDB Atlas 8.0.17 (Cloud)
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-code"></i>
                        Python 3.10 + pg8000 + pymongo
                    </div>
                </div>
            </div>
        </div>

        <!-- ==================== OVERVIEW SECTION ==================== -->
        <section id="overview" class="section">
            <div class="section-header">
                <i class="fas fa-chart-pie"></i>
                <h2>Overview - Sumar Executiv</h2>
                <span class="badge">Date de Test</span>
            </div>
            
            <!-- Quick Summary -->
            <div class="grid-2" style="margin-bottom: 25px;">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-bullseye" style="color: var(--accent);"></i>
                        <h3>Obiectivul Studiului</h3>
                    </div>
                    <p style="color: var(--text-secondary); line-height: 1.8;">
                        Comparatia detaliata intre <strong>PostgreSQL</strong> (baza de date relationala SQL) si 
                        <strong>MongoDB</strong> (baza de date NoSQL orientata pe documente) pentru un caz de utilizare 
                        <strong>E-Commerce</strong>, evaluand performanta, consistenta, scalabilitatea si potrivirea 
                        pentru diferite tipuri de operatiuni.
                    </p>
                </div>
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-flask" style="color: var(--accent);"></i>
                        <h3>Metodologia de Testare</h3>
                    </div>
                    <p style="color: var(--text-secondary); line-height: 1.8;">
                        <strong>Date identice</strong> in ambele baze (Faker seed=42) pentru comparatie echitabila.
                        Teste de performanta pentru 5 tipuri de query-uri, analiza CAP Theorem cu teste de 
                        tranzactii, rollback si integritate referentiala. Masuratori multiple pentru acuratete.
                    </p>
                </div>
            </div>
            
            <!-- Data Stats -->
            <div class="grid-6">
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-tags"></i></div>
                    <div class="value" style="color: var(--accent);">8</div>
                    <div class="label">Categorii</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-users"></i></div>
                    <div class="value" style="color: var(--accent);">100</div>
                    <div class="label">Utilizatori</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-box"></i></div>
                    <div class="value" style="color: var(--accent);">200</div>
                    <div class="label">Produse</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-shopping-cart"></i></div>
                    <div class="value" style="color: var(--accent);">150</div>
                    <div class="label">Comenzi</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-list"></i></div>
                    <div class="value" style="color: var(--accent);">363</div>
                    <div class="label">Order Items</div>
                </div>
                <div class="stat-card">
                    <div class="icon"><i class="fas fa-star"></i></div>
                    <div class="value" style="color: var(--accent);">80</div>
                    <div class="label">Review-uri</div>
                </div>
            </div>
            
            <div class="info-box success" style="margin-top: 20px;">
                <h4><i class="fas fa-check-circle"></i> Date Identice Garantate</h4>
                <p>Toate datele au fost generate cu <code>Faker.seed(42)</code> si <code>random.seed(42)</code>, 
                   asigurand reproducibilitate completa si comparatie echitabila intre cele doua baze de date.</p>
            </div>
        </section>

        <!-- Quick Performance Results -->
        <section class="section">
            <div class="grid-2">
                <div class="stat-card {pg_winner_class}">
                    <div class="icon"><i class="fas fa-elephant" style="color: var(--pg-color);"></i></div>
                    <div class="value pg-color">{pg_total:.2f}ms</div>
                    <div class="label">PostgreSQL - Timp Total</div>
                    <p style="margin-top: 8px; font-size: 0.8rem; color: var(--text-secondary);">
                        Deployment: Local Installation
                    </p>
                </div>
                <div class="stat-card {mongo_winner_class}">
                    <div class="icon"><i class="fas fa-leaf" style="color: var(--mongo-color);"></i></div>
                    <div class="value mongo-color">{mongo_total:.2f}ms</div>
                    <div class="label">MongoDB - Timp Total</div>
                    <p style="margin-top: 8px; font-size: 0.8rem; color: var(--text-secondary);">
                        Deployment: Atlas Cloud Cluster
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px; padding: 18px; background: rgba(255,255,255,0.05); border-radius: 15px;">
                <span style="font-size: 1.2rem; color: var(--accent);">
                    <i class="fas fa-trophy" style="margin-right: 10px;"></i>
                    {winner_text}
                </span>
                <p style="margin-top: 8px; color: var(--text-secondary); font-size: 0.85rem;">
                     Diferenta se datoreaza in principal deployment-ului diferit: PostgreSQL ruleaza local vs MongoDB in cloud
                </p>
            </div>
        </section>

        <!-- ==================== PERFORMANCE SECTION ==================== -->
        <section id="performance" class="section">
            <div class="section-header">
                <i class="fas fa-tachometer-alt"></i>
                <h2>Analiza Performanta Detaliata</h2>
                <span class="badge">5 Query Types</span>
            </div>
            
            <div class="tabs">
                <button class="tab-btn active" onclick="showTab('chart-tab')">
                    <i class="fas fa-chart-bar"></i> Grafic Comparativ
                </button>
                <button class="tab-btn" onclick="showTab('table-tab')">
                    <i class="fas fa-table"></i> Tabel Detaliat
                </button>
                <button class="tab-btn" onclick="showTab('pie-tab')">
                    <i class="fas fa-chart-pie"></i> Distributie
                </button>
                <button class="tab-btn" onclick="showTab('radar-tab')">
                    <i class="fas fa-spider"></i> Radar Chart
                </button>
            </div>
            
            <div id="chart-tab" class="tab-content active">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-chart-bar" style="color: var(--accent);"></i>
                        <h3>Comparatie Timp de Executie (ms) - Bar Chart</h3>
                    </div>
                    <div class="chart-container large">
                        <canvas id="performanceChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="table-tab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-table" style="color: var(--accent);"></i>
                        <h3>Rezultate Detaliate per Query</h3>
                    </div>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th><i class="fas fa-code"></i> Tip Query</th>
                                <th><i class="fas fa-elephant"></i> PostgreSQL</th>
                                <th><i class="fas fa-leaf"></i> MongoDB</th>
                                <th><i class="fas fa-trophy"></i> Castigator</th>
                            </tr>
                        </thead>
                        <tbody>
                            {query_rows}
                            <tr style="background: rgba(79, 172, 254, 0.1); font-weight: bold;">
                                <td><strong>TOTAL</strong></td>
                                <td class="pg-color"><strong>{pg_total:.2f}ms</strong></td>
                                <td class="mongo-color"><strong>{mongo_total:.2f}ms</strong></td>
                                <td><span class="badge {'pg' if pg_total < mongo_total else 'mongo'}">{'PostgreSQL' if pg_total < mongo_total else 'MongoDB'}</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div id="pie-tab" class="tab-content">
                <div class="grid-2">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-elephant" style="color: var(--pg-color);"></i>
                            <h3>PostgreSQL - Distributie Timp</h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="pgPieChart"></canvas>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-leaf" style="color: var(--mongo-color);"></i>
                            <h3>MongoDB - Distributie Timp</h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="mongoPieChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="radar-tab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-spider" style="color: var(--accent);"></i>
                        <h3>Comparatie Radar - Toate Dimensiunile</h3>
                    </div>
                    <div class="chart-container large">
                        <canvas id="radarChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Response Time Details -->
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-clock" style="color: var(--accent);"></i>
                    <h3>Metrici de Raspuns (din Teste CAP)</h3>
                </div>
                <div class="grid-4">
                    <div class="stat-card">
                        <div class="icon"><i class="fas fa-bolt pg-color"></i></div>
                        <div class="value pg-color">{pg_response:.2f}ms</div>
                        <div class="label">PostgreSQL Avg</div>
                    </div>
                    <div class="stat-card">
                        <div class="icon"><i class="fas fa-arrow-up pg-color"></i></div>
                        <div class="value pg-color">{pg_max_response:.2f}ms</div>
                        <div class="label">PostgreSQL Max</div>
                    </div>
                    <div class="stat-card">
                        <div class="icon"><i class="fas fa-bolt mongo-color"></i></div>
                        <div class="value mongo-color">{mongo_response:.2f}ms</div>
                        <div class="label">MongoDB Avg</div>
                    </div>
                    <div class="stat-card">
                        <div class="icon"><i class="fas fa-arrow-up mongo-color"></i></div>
                        <div class="value mongo-color">{mongo_max_response:.2f}ms</div>
                        <div class="label">MongoDB Max</div>
                    </div>
                </div>
            </div>
            
            <!-- Query Type Explanations -->
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-info-circle" style="color: var(--accent);"></i>
                    <h3>Explicatii Tipuri de Query-uri</h3>
                </div>
                <div class="grid-2" style="margin-top: 15px;">
                    <div>
                        <ul class="feature-list">
                            <li class="check">
                                <i class="fas fa-check-circle"></i>
                                <span><strong>Select All:</strong> Citire completa a unei colectii/tabele</span>
                            </li>
                            <li class="check">
                                <i class="fas fa-check-circle"></i>
                                <span><strong>JOIN/Aggregation:</strong> Combinare date din multiple tabele</span>
                            </li>
                            <li class="check">
                                <i class="fas fa-check-circle"></i>
                                <span><strong>Filter:</strong> Cautare cu conditii WHERE/find</span>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <ul class="feature-list">
                            <li class="check">
                                <i class="fas fa-check-circle"></i>
                                <span><strong>Insert:</strong> Adaugare date noi</span>
                            </li>
                            <li class="check">
                                <i class="fas fa-check-circle"></i>
                                <span><strong>Update:</strong> Modificare date existente</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        <!-- ==================== CAP THEOREM SECTION ==================== -->
        <section id="cap" class="section">
            <div class="section-header">
                <i class="fas fa-project-diagram"></i>
                <h2>CAP Theorem - Analiza Completa</h2>
                <span class="badge">Brewer's Theorem</span>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-question-circle" style="color: var(--accent);"></i>
                        <h3>Ce este Teorema CAP?</h3>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 15px; line-height: 1.7;">
                        Teorema CAP (Brewer, 2000) afirma ca un sistem de date distribuit poate garanta 
                        <strong>simultan doar 2 din 3</strong> proprietati:
                    </p>
                    <ul class="feature-list">
                        <li class="check">
                            <i class="fas fa-lock"></i>
                            <div>
                                <strong>Consistency (C)</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Toate nodurile vad aceleasi date in acelasi moment. Orice citire returneaza 
                                    cea mai recenta scriere sau o eroare.
                                </span>
                            </div>
                        </li>
                        <li class="check">
                            <i class="fas fa-server"></i>
                            <div>
                                <strong>Availability (A)</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Fiecare cerere primeste un raspuns (success/failure), fara garantia ca 
                                    contine cea mai recenta scriere.
                                </span>
                            </div>
                        </li>
                        <li class="check">
                            <i class="fas fa-network-wired"></i>
                            <div>
                                <strong>Partition Tolerance (P)</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Sistemul continua sa functioneze chiar daca mesajele dintre noduri sunt 
                                    pierdute sau intarziate (network partition).
                                </span>
                            </div>
                        </li>
                    </ul>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-map-marker-alt" style="color: var(--accent);"></i>
                        <h3>Pozitionare in Triunghiul CAP</h3>
                    </div>
                    <div style="text-align: center; padding: 15px;">
                        <div style="display: inline-block; position: relative; width: 260px; height: 240px;">
                            <svg width="260" height="240" style="position: absolute; top: 0; left: 0;">
                                <polygon points="130,15 15,220 245,220" fill="none" stroke="rgba(79, 172, 254, 0.4)" stroke-width="2"/>
                                <!-- Lines -->
                                <line x1="130" y1="15" x2="15" y2="220" stroke="rgba(79, 172, 254, 0.2)" stroke-width="1"/>
                                <line x1="130" y1="15" x2="245" y2="220" stroke="rgba(79, 172, 254, 0.2)" stroke-width="1"/>
                                <line x1="15" y1="220" x2="245" y2="220" stroke="rgba(79, 172, 254, 0.2)" stroke-width="1"/>
                            </svg>
                            <!-- C node -->
                            <div style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); background: rgba(79, 172, 254, 0.25); border: 2px solid var(--accent); border-radius: 50%; width: 55px; height: 55px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.9rem;">
                                <strong>C</strong>
                            </div>
                            <!-- A node -->
                            <div style="position: absolute; bottom: 0; left: 0; background: rgba(77, 179, 61, 0.25); border: 2px solid var(--mongo-color); border-radius: 50%; width: 55px; height: 55px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.9rem;">
                                <strong>A</strong>
                            </div>
                            <!-- P node -->
                            <div style="position: absolute; bottom: 0; right: 0; background: rgba(255, 193, 7, 0.25); border: 2px solid #ffc107; border-radius: 50%; width: 55px; height: 55px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.9rem;">
                                <strong>P</strong>
                            </div>
                            <!-- PostgreSQL -->
                            <div style="position: absolute; top: 85px; left: 50%; transform: translateX(-50%); background: var(--pg-color); color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; white-space: nowrap;">
                                🐘 PostgreSQL (CP)
                            </div>
                            <!-- MongoDB -->
                            <div style="position: absolute; top: 125px; left: 50%; transform: translateX(-50%); background: var(--mongo-color); color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; white-space: nowrap;">
                                🍃 MongoDB (CP*)
                            </div>
                        </div>
                    </div>
                    <div class="info-box" style="margin-top: 10px;">
                        <p style="font-size: 0.85rem;">
                            <strong>*</strong> MongoDB este CP by default, dar poate fi configurat pentru 
                            eventual consistency cu <code>readConcern: "local"</code> si <code>writeConcern: 1</code>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- CAP Combinations -->
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-puzzle-piece" style="color: var(--accent);"></i>
                    <h3>Combinatii CAP si Exemple de Sisteme</h3>
                </div>
                <div class="grid-3" style="margin-top: 15px;">
                    <div style="background: rgba(79, 172, 254, 0.1); padding: 18px; border-radius: 12px; border-left: 4px solid var(--accent);">
                        <h4 style="color: var(--accent); margin-bottom: 10px;">CP - Consistency + Partition</h4>
                        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 10px;">
                            Sacrifica Availability pentru a garanta Consistency
                        </p>
                        <ul style="color: var(--text-secondary); font-size: 0.85rem; margin-left: 15px;">
                            <li>PostgreSQL, MySQL</li>
                            <li>MongoDB (default)</li>
                            <li>HBase, Redis</li>
                            <li>Zookeeper</li>
                        </ul>
                    </div>
                    <div style="background: rgba(77, 179, 61, 0.1); padding: 18px; border-radius: 12px; border-left: 4px solid var(--mongo-color);">
                        <h4 style="color: var(--mongo-light); margin-bottom: 10px;">AP - Availability + Partition</h4>
                        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 10px;">
                            Sacrifica Consistency pentru Availability
                        </p>
                        <ul style="color: var(--text-secondary); font-size: 0.85rem; margin-left: 15px;">
                            <li>Cassandra</li>
                            <li>CouchDB</li>
                            <li>DynamoDB</li>
                            <li>Riak</li>
                        </ul>
                    </div>
                    <div style="background: rgba(255, 193, 7, 0.1); padding: 18px; border-radius: 12px; border-left: 4px solid #ffc107;">
                        <h4 style="color: #ffd54f; margin-bottom: 10px;">CA - Consistency + Availability</h4>
                        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 10px;">
                            Nu tolereaza partition-uri (single node)
                        </p>
                        <ul style="color: var(--text-secondary); font-size: 0.85rem; margin-left: 15px;">
                            <li>Single-node RDBMS</li>
                            <li>Oracle RAC</li>
                            <li>In-memory databases</li>
                            <li><em>(Teoretic imposibil in sisteme distribuite reale)</em></li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Detailed Comparison -->
            <div class="comparison-grid" style="margin-top: 25px;">
                <div class="comparison-column pg">
                    <h4><i class="fas fa-elephant" style="color: var(--pg-color);"></i> PostgreSQL (CP)</h4>
                    <ul class="feature-list">
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Strong Consistency</strong> - SERIALIZABLE isolation level disponibil</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>ACID Complet</strong> - Tranzactii atomice garantate</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>WAL (Write-Ahead Log)</strong> - Durabilitate garantata</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Foreign Keys</strong> - Integritate referentiala</li>
                        <li class="partial"><i class="fas fa-exclamation-circle"></i> <strong>Replication</strong> - Necesita configurare externa (Patroni, repmgr)</li>
                        <li class="cross"><i class="fas fa-times-circle"></i> <strong>Sharding nativ</strong> - Limitata (necesita Citus extension)</li>
                    </ul>
                </div>
                <div class="comparison-column mongo">
                    <h4><i class="fas fa-leaf" style="color: var(--mongo-color);"></i> MongoDB (CP tunable)</h4>
                    <ul class="feature-list">
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Tunable Consistency</strong> - writeConcern/readConcern configurabile</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Multi-doc Transactions</strong> - ACID din versiunea 4.0+</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Replica Sets</strong> - High Availability nativ</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Sharding nativ</strong> - Scalare orizontala built-in</li>
                        <li class="partial"><i class="fas fa-exclamation-circle"></i> <strong>Eventual Consistency</strong> - Posibila cu secondary reads</li>
                        <li class="partial"><i class="fas fa-exclamation-circle"></i> <strong>No Foreign Keys</strong> - Validare la nivel de aplicatie</li>
                    </ul>
                </div>
            </div>
        </section>

        <!-- ==================== ACID/BASE SECTION ==================== -->
        <section id="acid" class="section">
            <div class="section-header">
                <i class="fas fa-atom"></i>
                <h2>ACID vs BASE - Modele de Consistenta</h2>
                <span class="badge">Fundamental</span>
            </div>
            
            <div class="grid-2">
                <div class="card pg-card">
                    <div class="card-header">
                        <i class="fas fa-shield-alt" style="color: var(--pg-color);"></i>
                        <h3>ACID (PostgreSQL)</h3>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 15px;">
                        Model traditional pentru baze de date relationale, focusat pe <strong>consistenta stricta</strong>.
                    </p>
                    <ul class="feature-list">
                        <li class="check">
                            <i class="fas fa-atom"></i>
                            <div>
                                <strong>Atomicity</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Tranzactia se executa complet sau deloc. "All or nothing."
                                </span>
                            </div>
                        </li>
                        <li class="check">
                            <i class="fas fa-check-double"></i>
                            <div>
                                <strong>Consistency</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Baza de date trece doar din stare valida in stare valida.
                                </span>
                            </div>
                        </li>
                        <li class="check">
                            <i class="fas fa-user-shield"></i>
                            <div>
                                <strong>Isolation</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Tranzactiile concurente nu se afecteaza reciproc.
                                </span>
                            </div>
                        </li>
                        <li class="check">
                            <i class="fas fa-save"></i>
                            <div>
                                <strong>Durability</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Datele persista chiar si in caz de crash.
                                </span>
                            </div>
                        </li>
                    </ul>
                    <div class="code-block" style="margin-top: 15px;">
                        <span style="color: #c792ea;">BEGIN</span>;<br>
                        <span style="color: #82aaff;">UPDATE</span> accounts <span style="color: #82aaff;">SET</span> balance = balance - 100 <span style="color: #82aaff;">WHERE</span> id = 1;<br>
                        <span style="color: #82aaff;">UPDATE</span> accounts <span style="color: #82aaff;">SET</span> balance = balance + 100 <span style="color: #82aaff;">WHERE</span> id = 2;<br>
                        <span style="color: #c792ea;">COMMIT</span>; <span style="color: #546e7a;">-- Both or neither</span>
                    </div>
                </div>
                
                <div class="card mongo-card">
                    <div class="card-header">
                        <i class="fas fa-balance-scale" style="color: var(--mongo-color);"></i>
                        <h3>BASE (MongoDB - optional)</h3>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 15px;">
                        Model alternativ pentru sisteme distribuite, focusat pe <strong>availability si scalabilitate</strong>.
                    </p>
                    <ul class="feature-list">
                        <li class="check">
                            <i class="fas fa-server"></i>
                            <div>
                                <strong>Basically Available</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Sistemul garanteaza disponibilitatea (poate returna date stale).
                                </span>
                            </div>
                        </li>
                        <li class="check">
                            <i class="fas fa-sync-alt"></i>
                            <div>
                                <strong>Soft State</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Starea sistemului poate evolua in timp, chiar fara input.
                                </span>
                            </div>
                        </li>
                        <li class="check">
                            <i class="fas fa-hourglass-half"></i>
                            <div>
                                <strong>Eventual Consistency</strong><br>
                                <span style="color: var(--text-secondary); font-size: 0.85rem;">
                                    Datele vor fi consistente... eventual (nu imediat).
                                </span>
                            </div>
                        </li>
                    </ul>
                    <div class="code-block" style="margin-top: 15px;">
                        <span style="color: #546e7a;">// MongoDB cu writeConcern relaxat</span><br>
                        db.collection.<span style="color: #82aaff;">insertOne</span>(doc, {{<br>
                        &nbsp;&nbsp;writeConcern: {{ w: <span style="color: #f78c6c;">1</span> }}, <span style="color: #546e7a;">// Only primary</span><br>
                        &nbsp;&nbsp;readConcern: {{ level: <span style="color: #c3e88d;">"local"</span> }}<br>
                        }});
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-balance-scale-right" style="color: var(--accent);"></i>
                    <h3>Cand sa alegi ACID vs BASE?</h3>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Criteriu</th>
                            <th>ACID (PostgreSQL)</th>
                            <th>BASE (MongoDB/Cassandra)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Tranzactii financiare</td>
                            <td><span class="badge success">✅ Obligatoriu</span></td>
                            <td><span class="badge" style="background: rgba(244,67,54,0.3); color: #ff6b6b;">❌ Risc</span></td>
                        </tr>
                        <tr>
                            <td>Social media feeds</td>
                            <td><span class="badge" style="background: rgba(255,152,0,0.3); color: #ffb74d;">⚠️ Overkill</span></td>
                            <td><span class="badge success">✅ Perfect</span></td>
                        </tr>
                        <tr>
                            <td>E-commerce orders</td>
                            <td><span class="badge success">✅ Recomandat</span></td>
                            <td><span class="badge" style="background: rgba(255,152,0,0.3); color: #ffb74d;">⚠️ Cu atentie</span></td>
                        </tr>
                        <tr>
                            <td>User sessions/cache</td>
                            <td><span class="badge" style="background: rgba(255,152,0,0.3); color: #ffb74d;">⚠️ Overkill</span></td>
                            <td><span class="badge success">✅ Perfect</span></td>
                        </tr>
                        <tr>
                            <td>Analytics/Logging</td>
                            <td><span class="badge" style="background: rgba(255,152,0,0.3); color: #ffb74d;">⚠️ Ok</span></td>
                            <td><span class="badge success">✅ Mai bun</span></td>
                        </tr>
                        <tr>
                            <td>Inventory management</td>
                            <td><span class="badge success">✅ Obligatoriu</span></td>
                            <td><span class="badge" style="background: rgba(244,67,54,0.3); color: #ff6b6b;">❌ Periculos</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- ==================== SCHEMA SECTION ==================== -->
        <section id="schema" class="section">
            <div class="section-header">
                <i class="fas fa-sitemap"></i>
                <h2>Schema si Modelare Date</h2>
                <span class="badge">6 Entitati</span>
            </div>
            
            <div class="grid-2">
                <div class="card pg-card">
                    <div class="card-header">
                        <i class="fas fa-elephant" style="color: var(--pg-color);"></i>
                        <h3>PostgreSQL - Model Relational</h3>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 12px; font-size: 0.9rem;">
                        Schema normalizata (3NF) cu foreign keys si constraints.
                    </p>
                    <div class="schema-box">
                        <h4><i class="fas fa-table"></i> Tabele DDL</h4>
                        <div class="schema-code">
                            <span class="keyword">CREATE TABLE</span> <span class="type">categories</span> (<br>
                            &nbsp;&nbsp;id <span class="type">SERIAL PRIMARY KEY</span>,<br>
                            &nbsp;&nbsp;name <span class="type">VARCHAR(100)</span>, description <span class="type">TEXT</span><br>
                            );<br><br>
                            <span class="keyword">CREATE TABLE</span> <span class="type">products</span> (<br>
                            &nbsp;&nbsp;id <span class="type">SERIAL PRIMARY KEY</span>,<br>
                            &nbsp;&nbsp;name <span class="type">VARCHAR(200)</span>, price <span class="type">DECIMAL(10,2)</span>,<br>
                            &nbsp;&nbsp;category_id <span class="type">INT REFERENCES categories(id)</span><br>
                            );<br><br>
                            <span class="keyword">CREATE TABLE</span> <span class="type">orders</span> (<br>
                            &nbsp;&nbsp;id <span class="type">SERIAL PRIMARY KEY</span>,<br>
                            &nbsp;&nbsp;user_id <span class="type">INT REFERENCES users(id)</span>,<br>
                            &nbsp;&nbsp;total <span class="type">DECIMAL(10,2)</span>, status <span class="type">VARCHAR(20)</span><br>
                            );
                        </div>
                    </div>
                </div>
                
                <div class="card mongo-card">
                    <div class="card-header">
                        <i class="fas fa-leaf" style="color: var(--mongo-color);"></i>
                        <h3>MongoDB - Model Document</h3>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 12px; font-size: 0.9rem;">
                        Documente JSON flexibile, schema-less by default.
                    </p>
                    <div class="schema-box">
                        <h4><i class="fas fa-file-code"></i> Document Structure</h4>
                        <div class="schema-code">
                            <span class="comment">// products collection</span><br>
                            {{<br>
                            &nbsp;&nbsp;<span class="keyword">"_id"</span>: ObjectId("..."),<br>
                            &nbsp;&nbsp;<span class="keyword">"name"</span>: "Laptop Pro",<br>
                            &nbsp;&nbsp;<span class="keyword">"price"</span>: 1299.99,<br>
                            &nbsp;&nbsp;<span class="keyword">"category_id"</span>: 1,<br>
                            &nbsp;&nbsp;<span class="keyword">"specs"</span>: {{ <span class="comment">// Embedded doc</span><br>
                            &nbsp;&nbsp;&nbsp;&nbsp;"ram": "16GB",<br>
                            &nbsp;&nbsp;&nbsp;&nbsp;"storage": "512GB SSD"<br>
                            &nbsp;&nbsp;}}<br>
                            }}<br><br>
                            <span class="comment">// orders collection</span><br>
                            {{<br>
                            &nbsp;&nbsp;<span class="keyword">"user_id"</span>: 42,<br>
                            &nbsp;&nbsp;<span class="keyword">"items"</span>: [{{ ... }}] <span class="comment">// Can embed</span><br>
                            }}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- ER Diagram -->
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-project-diagram" style="color: var(--accent);"></i>
                    <h3>Entity-Relationship Diagram</h3>
                </div>
                <div style="text-align: center; padding: 25px; background: rgba(0,0,0,0.2); border-radius: 12px; margin-top: 12px; overflow-x: auto;">
                    <pre style="font-size: 0.8rem; line-height: 1.5; color: var(--text-secondary); display: inline-block; text-align: left;">
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  CATEGORIES  │       │   PRODUCTS   │       │   REVIEWS    │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄─────┐│ id (PK)      │◄─────┐│ id (PK)      │
│ name         │      ││ name         │      ││ product_id(FK)│
│ description  │      ││ price        │      ││ user_id (FK) │──┐
└──────────────┘      ││ stock        │      ││ rating       │  │
                      │├──────────────┤      ││ comment      │  │
                      └┤ category_id  │      │└──────────────┘  │
                       └──────────────┘      │                  │
                                             │                  │
┌──────────────┐       ┌──────────────┐      │┌──────────────┐  │
│    USERS     │       │    ORDERS    │      ││ ORDER_ITEMS  │  │
├──────────────┤       ├──────────────┤      │├──────────────┤  │
│ id (PK)      │◄─────┐│ id (PK)      │◄────┐││ id (PK)      │  │
│ email        │      ││ status       │     │││ order_id (FK)│  │
│ name         │      ││ total        │     │└┤ product_id   │──┤
│ address      │      ││ created_at   │     │ │ quantity     │  │
│ created_at   │      │├──────────────┤     │ │ price        │  │
└──────────────┘      └┤ user_id (FK) │     │ └──────────────┘  │
        ▲              └──────────────┘     │                   │
        │                                   └───────────────────┘
        └───────────────────────────────────────────────────────┘
                    </pre>
                </div>
            </div>
            
            <!-- Schema Comparison -->
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-exchange-alt" style="color: var(--accent);"></i>
                    <h3>Comparatie Abordari de Modelare</h3>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Aspect</th>
                            <th>PostgreSQL (Relational)</th>
                            <th>MongoDB (Document)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Schema</strong></td>
                            <td>Strict definita (DDL)</td>
                            <td>Flexibila (schema-less)</td>
                        </tr>
                        <tr>
                            <td><strong>Relatii</strong></td>
                            <td>Foreign Keys + JOINs</td>
                            <td>Embedded docs sau referinte manuale</td>
                        </tr>
                        <tr>
                            <td><strong>Normalizare</strong></td>
                            <td>3NF recomandat</td>
                            <td>Denormalizare incurajata</td>
                        </tr>
                        <tr>
                            <td><strong>Migrari</strong></td>
                            <td>ALTER TABLE (necesare)</td>
                            <td>Optionale, la nivel de aplicatie</td>
                        </tr>
                        <tr>
                            <td><strong>Data Types</strong></td>
                            <td>Strict (INT, VARCHAR, etc.)</td>
                            <td>BSON types (flexibile)</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- ==================== INDEXING SECTION ==================== -->
        <section id="indexing" class="section">
            <div class="section-header">
                <i class="fas fa-search"></i>
                <h2>Indexare si Optimizare Query-uri</h2>
                <span class="badge">Performance</span>
            </div>
            
            <div class="grid-2">
                <div class="card pg-card">
                    <div class="card-header">
                        <i class="fas fa-elephant" style="color: var(--pg-color);"></i>
                        <h3>PostgreSQL Indexes</h3>
                    </div>
                    <ul class="feature-list">
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>B-tree</strong> - Default, pentru =, <, >, BETWEEN
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>Hash</strong> - Rapid pentru egalitate exacta
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>GiST</strong> - Geometrie, full-text search
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>GIN</strong> - Arrays, JSONB, full-text
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>Partial Indexes</strong> - Index pe subset de date
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>Covering Indexes</strong> - INCLUDE columns
                        </li>
                    </ul>
                    <div class="code-block" style="margin-top: 12px;">
                        <span style="color: #c792ea;">CREATE INDEX</span> idx_products_category<br>
                        <span style="color: #82aaff;">ON</span> products(category_id);<br><br>
                        <span style="color: #c792ea;">CREATE INDEX</span> idx_orders_status<br>
                        <span style="color: #82aaff;">ON</span> orders(status) <span style="color: #82aaff;">WHERE</span> status = 'pending';
                    </div>
                </div>
                
                <div class="card mongo-card">
                    <div class="card-header">
                        <i class="fas fa-leaf" style="color: var(--mongo-color);"></i>
                        <h3>MongoDB Indexes</h3>
                    </div>
                    <ul class="feature-list">
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>Single Field</strong> - Index pe un camp
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>Compound</strong> - Multiple campuri
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>Multikey</strong> - Pentru arrays
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>Text</strong> - Full-text search
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>2dsphere</strong> - Geospatial
                        </li>
                        <li class="check">
                            <i class="fas fa-check-circle"></i>
                            <strong>TTL</strong> - Auto-expire documents
                        </li>
                    </ul>
                    <div class="code-block" style="margin-top: 12px;">
                        db.products.<span style="color: #82aaff;">createIndex</span>({{ category_id: 1 }});<br><br>
                        db.orders.<span style="color: #82aaff;">createIndex</span>(<br>
                        &nbsp;&nbsp;{{ status: 1, created_at: -1 }}<br>
                        );
                    </div>
                </div>
            </div>
            
            <div class="info-box warning" style="margin-top: 20px;">
                <h4><i class="fas fa-exclamation-triangle"></i> Best Practices Indexare</h4>
                <p>
                    • Nu indexa totul - indexurile consuma spatiu si incetinesc write-urile<br>
                    • Foloseste EXPLAIN/explain() pentru a analiza query plans<br>
                    • Compound indexes: ordinea campurilor conteaza!<br>
                    • Monitorizeaza index usage si elimina indexurile nefolosite
                </p>
            </div>
        </section>

        <!-- ==================== SCALING SECTION ==================== -->
        <section id="scaling" class="section">
            <div class="section-header">
                <i class="fas fa-expand-arrows-alt"></i>
                <h2>Scalabilitate si Arhitectura</h2>
                <span class="badge">Enterprise</span>
            </div>
            
            <div class="grid-2">
                <div class="card pg-card">
                    <div class="card-header">
                        <i class="fas fa-elephant" style="color: var(--pg-color);"></i>
                        <h3>PostgreSQL Scaling</h3>
                    </div>
                    <h4 style="margin-bottom: 10px; color: var(--accent);">Scalare Verticala (Scale Up)</h4>
                    <ul class="feature-list" style="margin-bottom: 15px;">
                        <li class="check"><i class="fas fa-check-circle"></i> Mai mult RAM, CPU, storage</li>
                        <li class="check"><i class="fas fa-check-circle"></i> Connection pooling (PgBouncer)</li>
                        <li class="check"><i class="fas fa-check-circle"></i> Query optimization, indexare</li>
                    </ul>
                    
                    <h4 style="margin-bottom: 10px; color: var(--accent);">Scalare Orizontala (Scale Out)</h4>
                    <ul class="feature-list">
                        <li class="partial"><i class="fas fa-exclamation-circle"></i> Read replicas (streaming replication)</li>
                        <li class="partial"><i class="fas fa-exclamation-circle"></i> Partitioning (table partitions)</li>
                        <li class="partial"><i class="fas fa-exclamation-circle"></i> Sharding via Citus extension</li>
                        <li class="cross"><i class="fas fa-times-circle"></i> No native auto-sharding</li>
                    </ul>
                </div>
                
                <div class="card mongo-card">
                    <div class="card-header">
                        <i class="fas fa-leaf" style="color: var(--mongo-color);"></i>
                        <h3>MongoDB Scaling</h3>
                    </div>
                    <h4 style="margin-bottom: 10px; color: var(--accent);">Scalare Verticala (Scale Up)</h4>
                    <ul class="feature-list" style="margin-bottom: 15px;">
                        <li class="check"><i class="fas fa-check-circle"></i> Mai mult RAM pentru working set</li>
                        <li class="check"><i class="fas fa-check-circle"></i> SSD storage pentru IOPS</li>
                    </ul>
                    
                    <h4 style="margin-bottom: 10px; color: var(--accent);">Scalare Orizontala (Scale Out)</h4>
                    <ul class="feature-list">
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Replica Sets</strong> - HA built-in</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Sharding nativ</strong> - Auto-balancing</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Config servers</strong> - Metadata management</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>mongos routers</strong> - Query routing</li>
                    </ul>
                </div>
            </div>
            
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-server" style="color: var(--accent);"></i>
                    <h3>Arhitectura MongoDB Sharded Cluster</h3>
                </div>
                <div style="text-align: center; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 12px; margin-top: 12px;">
                    <pre style="font-size: 0.8rem; line-height: 1.5; color: var(--text-secondary); display: inline-block; text-align: left;">
                    ┌─────────────────────────────────────────────────────────┐
                    │                     APPLICATION                         │
                    └─────────────────────────┬───────────────────────────────┘
                                              │
                    ┌─────────────────────────▼───────────────────────────────┐
                    │                    mongos ROUTERS                        │
                    │            (Query routing & aggregation)                 │
                    └──────┬──────────────────┬──────────────────┬────────────┘
                           │                  │                  │
          ┌────────────────▼────┐  ┌──────────▼────────┐  ┌──────▼────────────┐
          │    Shard 1          │  │    Shard 2        │  │    Shard 3        │
          │  ┌─────────────┐    │  │  ┌─────────────┐  │  │  ┌─────────────┐  │
          │  │ Primary     │    │  │  │ Primary     │  │  │  │ Primary     │  │
          │  │ Secondary   │    │  │  │ Secondary   │  │  │  │ Secondary   │  │
          │  │ Secondary   │    │  │  │ Secondary   │  │  │  │ Secondary   │  │
          │  └─────────────┘    │  │  └─────────────┘  │  │  └─────────────┘  │
          └─────────────────────┘  └───────────────────┘  └───────────────────┘
                    </pre>
                </div>
            </div>
        </section>

        <!-- ==================== TESTS SECTION ==================== -->
        <section id="tests" class="section">
            <div class="section-header">
                <i class="fas fa-vial"></i>
                <h2>Rezultate Teste Detaliate</h2>
                <span class="badge">Verificare</span>
            </div>
            
            <div class="grid-2">
                <div class="card pg-card">
                    <div class="card-header">
                        <i class="fas fa-elephant" style="color: var(--pg-color);"></i>
                        <h3>Teste PostgreSQL</h3>
                    </div>
                    
                    <div class="test-result">
                        <div class="icon {'success' if pg_rollback.get('passed') else 'failed'}">
                            <i class="fas {'fa-check' if pg_rollback.get('passed') else 'fa-times'}"></i>
                        </div>
                        <div class="details">
                            <h4>Transaction Rollback Test</h4>
                            <p>
                                Initial: {pg_rollback.get('initial_value', 'N/A')} → 
                                After rollback: {pg_rollback.get('after_rollback', 'N/A')}<br>
                                <span class="{'success' if pg_rollback.get('passed') else 'danger'}">
                                    {' PASSED - Rollback functioneaza corect' if pg_rollback.get('passed') else ' FAILED'}
                                </span>
                            </p>
                        </div>
                    </div>
                    
                    <div class="test-result">
                        <div class="icon {'success' if pg_fk.get('passed') else 'failed'}">
                            <i class="fas {'fa-check' if pg_fk.get('passed') else 'fa-times'}"></i>
                        </div>
                        <div class="details">
                            <h4>Foreign Key Constraint Test</h4>
                            <p>
                                <span class="{'success' if pg_fk.get('passed') else 'danger'}">
                                    {' PASSED - FK constraints enforced' if pg_fk.get('passed') else ' FAILED'}
                                </span>
                            </p>
                        </div>
                    </div>
                    
                    <div class="test-result">
                        <div class="icon success">
                            <i class="fas fa-clock"></i>
                        </div>
                        <div class="details">
                            <h4>Availability Test</h4>
                            <p>
                                Avg: <strong class="pg-color">{pg_response:.3f}ms</strong> | 
                                Max: <strong>{pg_max_response:.3f}ms</strong> | 
                                Queries: {pg_avail.get('queries_executed', 20)}
                            </p>
                        </div>
                    </div>
                </div>
                
                <div class="card mongo-card">
                    <div class="card-header">
                        <i class="fas fa-leaf" style="color: var(--mongo-color);"></i>
                        <h3>Teste MongoDB</h3>
                    </div>
                    
                    <div class="test-result">
                        <div class="icon {'success' if mongo_atomic.get('passed') else 'failed'}">
                            <i class="fas {'fa-check' if mongo_atomic.get('passed') else 'fa-times'}"></i>
                        </div>
                        <div class="details">
                            <h4>Atomic Update Test</h4>
                            <p>
                                Modified count: {mongo_atomic.get('modified_count', 'N/A')}<br>
                                <span class="{'success' if mongo_atomic.get('passed') else 'danger'}">
                                    {' PASSED - Atomic operations work' if mongo_atomic.get('passed') else ' FAILED'}
                                </span>
                            </p>
                        </div>
                    </div>
                    
                    <div class="test-result">
                        <div class="icon {'success' if mongo_write.get('passed') else 'failed'}">
                            <i class="fas {'fa-check' if mongo_write.get('passed') else 'fa-times'}"></i>
                        </div>
                        <div class="details">
                            <h4>Write Concern Test</h4>
                            <p>
                                Write time: {mongo_write.get('write_time_ms', 'N/A'):.2f}ms<br>
                                <span class="{'success' if mongo_write.get('passed') else 'danger'}">
                                    {' PASSED - Write acknowledged' if mongo_write.get('passed') else ' FAILED'}
                                </span>
                            </p>
                        </div>
                    </div>
                    
                    <div class="test-result">
                        <div class="icon success">
                            <i class="fas fa-clock"></i>
                        </div>
                        <div class="details">
                            <h4>Availability Test</h4>
                            <p>
                                Avg: <strong class="mongo-color">{mongo_response:.3f}ms</strong> | 
                                Max: <strong>{mongo_max_response:.3f}ms</strong> | 
                                Queries: {mongo_avail.get('queries_executed', 20)}<br>
                                <span style="font-size: 0.8rem; color: var(--text-secondary);">
                                    (Higher latency due to cloud network)
                                </span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ==================== RECOMMENDATIONS SECTION ==================== -->
        <section id="recommendations" class="section">
            <div class="section-header">
                <i class="fas fa-check-circle"></i>
                <h2>Concluzii si Recomandari Finale</h2>
                <span class="badge">Decision Matrix</span>
            </div>
            
            <div class="grid-2">
                <div class="card pg-card">
                    <div class="card-header">
                        <i class="fas fa-elephant" style="color: var(--pg-color);"></i>
                        <h3>Alege PostgreSQL pentru:</h3>
                    </div>
                    <ul class="feature-list">
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Tranzactii financiare</strong> - Orders, payments, refunds</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Rapoarte complexe</strong> - Multi-table JOINs, agregari</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Integritate stricta</strong> - Inventory, pricing, accounts</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Schema stabila</strong> - Date structurate, predictibile</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Complianta</strong> - GDPR, audit, regulatory</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Full-text search avansat</strong> - Cu tsearch2</li>
                    </ul>
                </div>
                
                <div class="card mongo-card">
                    <div class="card-header">
                        <i class="fas fa-leaf" style="color: var(--mongo-color);"></i>
                        <h3>Alege MongoDB pentru:</h3>
                    </div>
                    <ul class="feature-list">
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Product catalogs</strong> - Atribute variabile per categorie</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>User sessions</strong> - Cache, preferences, carts</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Content management</strong> - CMS, blog posts, articles</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Real-time analytics</strong> - Event streams, metrics</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Rapid prototyping</strong> - Schema-less development</li>
                        <li class="check"><i class="fas fa-check-circle"></i> <strong>Horizontal scaling</strong> - Sharding pentru big data</li>
                    </ul>
                </div>
            </div>
            
            <!-- Final Verdict -->
            <div class="summary-card" style="margin-top: 25px;">
                <h3><i class="fas fa-gavel" style="margin-right: 10px;"></i> VERDICT FINAL: Polyglot Persistence</h3>
                <p style="margin: 15px 0; color: var(--text-secondary); font-size: 1rem;">
                    Pentru o platforma E-Commerce moderna, recomandam o <strong>arhitectura hibrida</strong>:
                </p>
                <div class="grid-3" style="text-align: left; margin-top: 20px;">
                    <div style="background: rgba(51, 103, 145, 0.2); padding: 18px; border-radius: 12px; border-left: 4px solid var(--pg-color);">
                        <h4 style="color: var(--pg-light); margin-bottom: 8px;"><i class="fas fa-database"></i> Tier 1: PostgreSQL</h4>
                        <p style="font-size: 0.85rem; color: var(--text-secondary);">
                            <strong>Date critice:</strong> Orders, Payments, Users, Inventory, Audit logs
                        </p>
                    </div>
                    <div style="background: rgba(77, 179, 61, 0.2); padding: 18px; border-radius: 12px; border-left: 4px solid var(--mongo-color);">
                        <h4 style="color: var(--mongo-light); margin-bottom: 8px;"><i class="fas fa-file-code"></i> Tier 2: MongoDB</h4>
                        <p style="font-size: 0.85rem; color: var(--text-secondary);">
                            <strong>Date flexibile:</strong> Product catalog, Sessions, Recommendations, Analytics
                        </p>
                    </div>
                    <div style="background: rgba(220, 53, 69, 0.2); padding: 18px; border-radius: 12px; border-left: 4px solid #dc3545;">
                        <h4 style="color: #ff6b7a; margin-bottom: 8px;"><i class="fas fa-bolt"></i> Tier 3: Redis Cache</h4>
                        <p style="font-size: 0.85rem; color: var(--text-secondary);">
                            <strong>Hot data:</strong> Sessions, Rate limiting, Real-time counters
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Trade-off Matrix -->
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-balance-scale" style="color: var(--accent);"></i>
                    <h3>Matricea Trade-off-urilor (1-10)</h3>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Criteriu</th>
                            <th>PostgreSQL</th>
                            <th>MongoDB</th>
                            <th>Winner</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><i class="fas fa-lock" style="color: var(--accent); margin-right: 8px;"></i> Consistency</td>
                            <td><strong class="pg-color">9/10</strong></td>
                            <td><strong class="mongo-color">6/10</strong></td>
                            <td><span class="badge pg">PostgreSQL</span></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-server" style="color: var(--accent); margin-right: 8px;"></i> Availability</td>
                            <td><strong class="pg-color">7/10</strong></td>
                            <td><strong class="mongo-color">9/10</strong></td>
                            <td><span class="badge mongo">MongoDB</span></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-expand-arrows-alt" style="color: var(--accent); margin-right: 8px;"></i> Scalability</td>
                            <td><strong class="pg-color">6/10</strong></td>
                            <td><strong class="mongo-color">9/10</strong></td>
                            <td><span class="badge mongo">MongoDB</span></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-tachometer-alt" style="color: var(--accent); margin-right: 8px;"></i> Read Performance</td>
                            <td><strong class="pg-color">8/10</strong></td>
                            <td><strong class="mongo-color">8/10</strong></td>
                            <td><span class="badge" style="background: rgba(79,172,254,0.3); color: var(--accent);">Tie</span></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-pencil-alt" style="color: var(--accent); margin-right: 8px;"></i> Write Performance</td>
                            <td><strong class="pg-color">7/10</strong></td>
                            <td><strong class="mongo-color">8/10</strong></td>
                            <td><span class="badge mongo">MongoDB</span></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-code" style="color: var(--accent); margin-right: 8px;"></i> Dev Experience</td>
                            <td><strong class="pg-color">7/10</strong></td>
                            <td><strong class="mongo-color">9/10</strong></td>
                            <td><span class="badge mongo">MongoDB</span></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-shield-alt" style="color: var(--accent); margin-right: 8px;"></i> Data Integrity</td>
                            <td><strong class="pg-color">10/10</strong></td>
                            <td><strong class="mongo-color">7/10</strong></td>
                            <td><span class="badge pg">PostgreSQL</span></td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-dollar-sign" style="color: var(--accent); margin-right: 8px;"></i> Cost (OSS)</td>
                            <td><strong class="pg-color">9/10</strong></td>
                            <td><strong class="mongo-color">8/10</strong></td>
                            <td><span class="badge pg">PostgreSQL</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Key Takeaways -->
            <div class="card" style="margin-top: 25px;">
                <div class="card-header">
                    <i class="fas fa-lightbulb" style="color: var(--accent);"></i>
                    <h3>Key Takeaways</h3>
                </div>
                <div class="grid-2" style="margin-top: 15px;">
                    <div>
                        <h4 style="color: var(--accent); margin-bottom: 10px;"> Din acest studiu am invatat:</h4>
                        <ul class="feature-list">
                            <li class="check"><i class="fas fa-check"></i> Nu exista "best database" - depinde de use case</li>
                            <li class="check"><i class="fas fa-check"></i> ACID vs BASE: alege in functie de cerinte de consistenta</li>
                            <li class="check"><i class="fas fa-check"></i> Deployment-ul afecteaza major performanta (local vs cloud)</li>
                            <li class="check"><i class="fas fa-check"></i> Polyglot persistence este viitorul arhitecturilor moderne</li>
                        </ul>
                    </div>
                    <div>
                        <h4 style="color: var(--accent); margin-bottom: 10px;"> Pentru E-Commerce specific:</h4>
                        <ul class="feature-list">
                            <li class="check"><i class="fas fa-check"></i> Orders & Payments → PostgreSQL (ACID obligatoriu)</li>
                            <li class="check"><i class="fas fa-check"></i> Product Catalog → MongoDB (flexibilitate schema)</li>
                            <li class="check"><i class="fas fa-check"></i> User Sessions → Redis/MongoDB (speed)</li>
                            <li class="check"><i class="fas fa-check"></i> Analytics → MongoDB/ClickHouse (write-heavy)</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer>
            <p style="font-size: 1.05rem; margin-bottom: 8px;">
                <strong>Proiect BDNV</strong> - Baze de Date NoSQL Variationale
            </p>
            <p>Studiu Comparativ Complet: PostgreSQL vs MongoDB pentru E-Commerce</p>
            <div class="links">
                <a href="https://www.postgresql.org/docs/"><i class="fas fa-external-link-alt"></i> PostgreSQL Docs</a>
                <a href="https://www.mongodb.com/docs/"><i class="fas fa-external-link-alt"></i> MongoDB Docs</a>
                <a href="https://github.com"><i class="fab fa-github"></i> Source Code</a>
            </div>
            <p style="margin-top: 15px; font-size: 0.8rem;">
                Dashboard generat automat cu Python • {current_date}
            </p>
        </footer>
    </div>

    <script>
        // Tab functionality
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.closest('.tab-btn').classList.add('active');
        }}
        
        // Navbar scroll
        window.addEventListener('scroll', () => {{
            const navbar = document.querySelector('.navbar');
            navbar.style.background = window.scrollY > 50 ? 'rgba(15, 15, 26, 0.98)' : 'rgba(15, 15, 26, 0.95)';
        }});
        
        // Active nav link
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-btn');
        
        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(section => {{
                if (scrollY >= section.offsetTop - 120) current = section.getAttribute('id');
            }});
            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) link.classList.add('active');
            }});
        }});
        
        // Chart.js
        Chart.defaults.color = '#aaa';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.1)';
        
        // Bar Chart
        new Chart(document.getElementById('performanceChart').getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: {query_names},
                datasets: [
                    {{
                        label: 'PostgreSQL (ms)',
                        data: {pg_times},
                        backgroundColor: 'rgba(51, 103, 145, 0.8)',
                        borderColor: '#336791',
                        borderWidth: 2,
                        borderRadius: 6
                    }},
                    {{
                        label: 'MongoDB (ms)',
                        data: {mongo_times},
                        backgroundColor: 'rgba(77, 179, 61, 0.8)',
                        borderColor: '#4DB33D',
                        borderWidth: 2,
                        borderRadius: 6
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top', labels: {{ padding: 15, usePointStyle: true }} }},
                    tooltip: {{ backgroundColor: 'rgba(0,0,0,0.8)', padding: 10, cornerRadius: 6 }}
                }},
                scales: {{
                    x: {{ grid: {{ display: false }} }},
                    y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, title: {{ display: true, text: 'Timp (ms)' }} }}
                }}
            }}
        }});
        
        // PostgreSQL Pie
        new Chart(document.getElementById('pgPieChart').getContext('2d'), {{
            type: 'doughnut',
            data: {{
                labels: {query_names},
                datasets: [{{
                    data: {pg_times},
                    backgroundColor: ['rgba(51,103,145,0.9)', 'rgba(51,103,145,0.7)', 'rgba(51,103,145,0.5)', 'rgba(51,103,145,0.3)', 'rgba(74,141,189,0.9)'],
                    borderColor: '#336791',
                    borderWidth: 2
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 12 }} }} }} }}
        }});
        
        // MongoDB Pie
        new Chart(document.getElementById('mongoPieChart').getContext('2d'), {{
            type: 'doughnut',
            data: {{
                labels: {query_names},
                datasets: [{{
                    data: {mongo_times},
                    backgroundColor: ['rgba(77,179,61,0.9)', 'rgba(77,179,61,0.7)', 'rgba(77,179,61,0.5)', 'rgba(77,179,61,0.3)', 'rgba(109,213,93,0.9)'],
                    borderColor: '#4DB33D',
                    borderWidth: 2
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 12 }} }} }} }}
        }});
        
        // Radar Chart
        new Chart(document.getElementById('radarChart').getContext('2d'), {{
            type: 'radar',
            data: {{
                labels: ['Consistency', 'Availability', 'Scalability', 'Performance', 'Dev Speed', 'Data Integrity', 'Cost'],
                datasets: [
                    {{
                        label: 'PostgreSQL',
                        data: [9, 7, 6, 8, 7, 10, 9],
                        backgroundColor: 'rgba(51, 103, 145, 0.3)',
                        borderColor: '#336791',
                        borderWidth: 2,
                        pointBackgroundColor: '#336791'
                    }},
                    {{
                        label: 'MongoDB',
                        data: [6, 9, 9, 8, 9, 7, 8],
                        backgroundColor: 'rgba(77, 179, 61, 0.3)',
                        borderColor: '#4DB33D',
                        borderWidth: 2,
                        pointBackgroundColor: '#4DB33D'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'top', labels: {{ padding: 15 }} }} }},
                scales: {{
                    r: {{
                        angleLines: {{ color: 'rgba(255,255,255,0.1)' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        pointLabels: {{ color: '#aaa', font: {{ size: 11 }} }},
                        ticks: {{ display: false }},
                        suggestedMin: 0,
                        suggestedMax: 10
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''

os.makedirs("results", exist_ok=True)
with open("results/dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Dashboard salvat in results/dashboard.html")
print("Gata!\n")
