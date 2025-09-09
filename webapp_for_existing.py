from flask import Flask, render_template_string, send_file, redirect, url_for
import os
import base64
import io
import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import warnings
warnings.filterwarnings('ignore')

# Import your existing analyzer
from portfolio_analyzer import WebPortfolioRiskAnalyzer

app = Flask(__name__)

# HTML Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Risk Analyzer</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .hero { 
            padding: 100px 0; 
            text-align: center; 
            color: white; 
        }
        .card { 
            background: rgba(255,255,255,0.95); 
            backdrop-filter: blur(10px); 
            border: none; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
            transition: transform 0.3s ease;
            border-radius: 15px;
        }
        .card:hover { transform: translateY(-5px); }
        .btn-primary { 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            border: none; 
            padding: 15px 30px; 
            font-weight: 600;
            border-radius: 10px;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .feature-icon { 
            font-size: 3rem; 
            color: #667eea; 
            margin-bottom: 20px; 
        }
        .sample-table {
            font-size: 0.9rem;
        }
        .loading {
            display: none;
        }
        .loading.show {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #ffffff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="container">
            <h1 class="display-3 fw-bold mb-4">
                <i class="fas fa-chart-line me-3"></i>
                Portfolio Risk Analyzer
            </h1>
            <p class="lead fs-4 mb-5">Professional Investment Analytics & Risk Management Platform</p>
            <button onclick="startAnalysis()" class="btn btn-primary btn-lg me-3" id="analyzeBtn">
                <i class="fas fa-chart-bar me-2"></i>
                <span class="btn-text">Start Analysis</span>
                <span class="loading"></span>
            </button>
            <button class="btn btn-outline-light btn-lg" data-bs-toggle="modal" data-bs-target="#infoModal">
                <i class="fas fa-info-circle me-2"></i>
                Project Info
            </button>
        </div>
    </div>
    
    <div class="container py-5">
        <div class="row text-center mb-5">
            <div class="col">
                <h2 class="display-5 fw-bold text-white mb-3">Professional Analytics Features</h2>
                <p class="lead text-light opacity-75">Institutional-grade risk management tools</p>
            </div>
        </div>
        
        <div class="row g-4 mb-5">
            <div class="col-md-3">
                <div class="card h-100 text-center p-4">
                    <div class="feature-icon"><i class="fas fa-shield-alt"></i></div>
                    <h5 class="fw-bold">Risk Analytics</h5>
                    <p class="text-muted">VaR, Volatility, Drawdown Analysis</p>
                    <small class="text-success">✓ 95% Value at Risk</small><br>
                    <small class="text-success">✓ Sharpe Ratio</small><br>
                    <small class="text-success">✓ Maximum Drawdown</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card h-100 text-center p-4">
                    <div class="feature-icon"><i class="fas fa-chart-pie"></i></div>
                    <h5 class="fw-bold">Visual Analytics</h5>
                    <p class="text-muted">Interactive Charts & Dashboards</p>
                    <small class="text-primary">📊 Portfolio Allocation</small><br>
                    <small class="text-primary">📈 Performance Trends</small><br>
                    <small class="text-primary">🔥 Correlation Matrix</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card h-100 text-center p-4">
                    <div class="feature-icon"><i class="fas fa-exclamation-triangle"></i></div>
                    <h5 class="fw-bold">Risk Compliance</h5>
                    <p class="text-muted">Automated Monitoring & Alerts</p>
                    <small class="text-warning">⚠️ Position Size Limits</small><br>
                    <small class="text-warning">⚠️ Sector Concentration</small><br>
                    <small class="text-warning">⚠️ Risk Threshold Alerts</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card h-100 text-center p-4">
                    <div class="feature-icon"><i class="fas fa-file-pdf"></i></div>
                    <h5 class="fw-bold">Professional Reports</h5>
                    <p class="text-muted">Executive-Level Documentation</p>
                    <small class="text-danger">📄 PDF Generation</small><br>
                    <small class="text-danger">📊 Executive Summary</small><br>
                    <small class="text-danger">📋 Holdings Analysis</small>
                </div>
            </div>
        </div>
        
        <!-- Sample Portfolio Section -->
        <div class="row">
            <div class="col">
                <div class="card p-4">
                    <div class="row">
                        <div class="col-lg-6">
                            <h3 class="text-primary mb-4">
                                <i class="fas fa-briefcase me-2"></i>
                                Pre-loaded Sample Portfolio
                            </h3>
                            <p class="lead mb-4">Ready-to-analyze diversified portfolio with live market data:</p>
                            
                            <div class="row mb-4">
                                <div class="col-6">
                                    <h6 class="text-success">🏢 Tech Stocks</h6>
                                    <ul class="list-unstyled ms-3">
                                        <li>• AAPL - Apple Inc.</li>
                                        <li>• MSFT - Microsoft</li>
                                        <li>• GOOGL - Alphabet</li>
                                        <li>• TSLA - Tesla</li>
                                    </ul>
                                </div>
                                <div class="col-6">
                                    <h6 class="text-info">📈 Diversified ETFs</h6>
                                    <ul class="list-unstyled ms-3">
                                        <li>• SPY - S&P 500 ETF</li>
                                        <li>• BND - Bond ETF</li>
                                        <li>• GLD - Gold ETF</li>
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="alert alert-info">
                                <i class="fas fa-rocket me-2"></i>
                                <strong>Total Portfolio Value:</strong> ~$13,000+ with real-time pricing
                            </div>
                        </div>
                        <div class="col-lg-6">
                            <div class="card bg-light">
                                <div class="card-header bg-primary text-white">
                                    <h6 class="mb-0">
                                        <i class="fas fa-table me-2"></i>
                                        Sample Holdings Preview
                                    </h6>
                                </div>
                                <div class="card-body p-2">
                                    <div class="table-responsive">
                                        <table class="table table-sm sample-table mb-0">
                                            <thead class="table-light">
                                                <tr>
                                                    <th>Symbol</th>
                                                    <th>Shares</th>
                                                    <th>Purchase $</th>
                                                    <th>Type</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <td><strong class="text-primary">AAPL</strong></td>
                                                    <td>10</td>
                                                    <td>$150</td>
                                                    <td><span class="badge bg-primary">Stock</span></td>
                                                </tr>
                                                <tr>
                                                    <td><strong class="text-primary">MSFT</strong></td>
                                                    <td>8</td>
                                                    <td>$300</td>
                                                    <td><span class="badge bg-primary">Stock</span></td>
                                                </tr>
                                                <tr>
                                                    <td><strong class="text-success">SPY</strong></td>
                                                    <td>20</td>
                                                    <td>$400</td>
                                                    <td><span class="badge bg-success">ETF</span></td>
                                                </tr>
                                                <tr>
                                                    <td><strong class="text-warning">BND</strong></td>
                                                    <td>15</td>
                                                    <td>$80</td>
                                                    <td><span class="badge bg-warning">Bond</span></td>
                                                </tr>
                                                <tr>
                                                    <td><strong class="text-info">GLD</strong></td>
                                                    <td>5</td>
                                                    <td>$180</td>
                                                    <td><span class="badge bg-info">Gold</span></td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Info Modal -->
    <div class="modal fade" id="infoModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-graduation-cap me-2"></i>
                        Student Portfolio Risk Analyzer Project
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-primary"><i class="fas fa-code me-2"></i>Technical Stack</h6>
                            <ul class="list-unstyled small">
                                <li>• <strong>Backend:</strong> Python + Flask</li>
                                <li>• <strong>Database:</strong> SQLite</li>
                                <li>• <strong>Analytics:</strong> Pandas + NumPy</li>
                                <li>• <strong>Visualization:</strong> Matplotlib + Seaborn</li>
                                <li>• <strong>Data Source:</strong> Yahoo Finance API</li>
                                <li>• <strong>Reports:</strong> ReportLab PDF</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-success"><i class="fas fa-chart-bar me-2"></i>Financial Metrics</h6>
                            <ul class="list-unstyled small">
                                <li>• <strong>VaR:</strong> 95% Value at Risk</li>
                                <li>• <strong>Volatility:</strong> Annualized std dev</li>
                                <li>• <strong>Sharpe Ratio:</strong> Risk-adjusted returns</li>
                                <li>• <strong>Max Drawdown:</strong> Peak-to-trough loss</li>
                                <li>• <strong>Correlation:</strong> Asset relationships</li>
                                <li>• <strong>Attribution:</strong> Performance breakdown</li>
                            </ul>
                        </div>
                    </div>
                    <hr>
                    <div class="alert alert-success">
                        <i class="fas fa-lightbulb me-2"></i>
                        <strong>Business Problem Solved:</strong> Individual investors lack professional-grade risk monitoring tools, leading to poor investment decisions and unexpected losses. This system provides institutional-level analytics for personal portfolios.
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary" onclick="startAnalysis()" data-bs-dismiss="modal">
                        Try Analysis
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script>
        function startAnalysis() {
            const btn = document.getElementById('analyzeBtn');
            const btnText = btn.querySelector('.btn-text');
            const loading = btn.querySelector('.loading');
            
            btnText.textContent = 'Analyzing...';
            loading.classList.add('show');
            btn.disabled = true;
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        }
    </script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar { 
            background: rgba(255,255,255,0.95) !important; 
            backdrop-filter: blur(10px); 
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        .card { 
            background: rgba(255,255,255,0.95); 
            border: none; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
            border-radius: 15px;
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-2px); }
        .metric-card { 
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 15px; 
            padding: 25px; 
            text-align: center; 
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid;
        }
        .metric-value { 
            font-size: 2.2rem; 
            font-weight: 700; 
            margin-bottom: 5px; 
            line-height: 1.2;
        }
        .metric-label { 
            color: #6b7280; 
            font-weight: 600; 
            font-size: 0.85rem; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .chart-container { 
            background: white; 
            border-radius: 15px; 
            padding: 25px; 
            margin-bottom: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .chart-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #374151;
        }
        .alert { border-radius: 10px; border: none; }
        .btn { border-radius: 8px; font-weight: 500; }
        .table th { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-weight: 600;
        }
        .positive { color: #059669; font-weight: 600; }
        .negative { color: #dc2626; font-weight: 600; }
        .status-good { border-left-color: #059669; }
        .status-warning { border-left-color: #d97706; }
        .status-danger { border-left-color: #dc2626; }
        .status-info { border-left-color: #2563eb; }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light fixed-top">
        <div class="container-fluid px-4">
            <a class="navbar-brand fw-bold text-primary" href="/">
                <i class="fas fa-chart-line me-2"></i>Portfolio Risk Analyzer
            </a>
            <div class="d-flex gap-2">
                <a href="/view-pdf" target="_blank" class="btn btn-outline-info btn-sm">
                    <i class="fas fa-eye me-1"></i>View PDF
                </a>
                <a href="/download-pdf" class="btn btn-success btn-sm">
                    <i class="fas fa-download me-1"></i>Download
                </a>
                <a href="/" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-home me-1"></i>Home
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid" style="margin-top: 80px; padding: 20px;">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold text-primary mb-2">
                    <i class="fas fa-dashboard me-2"></i>Portfolio Risk Dashboard
                </h1>
                <p class="lead text-muted">Real-time analysis with professional risk metrics</p>
                <p class="text-success">
                    <i class="fas fa-sync-alt me-1"></i>
                    Last updated: {{ last_updated }}
                </p>
            </div>
        </div>

        <!-- Risk Alerts -->
        {% if alerts %}
        <div class="row mb-4">
            <div class="col-12">
                <div class="alert alert-warning border-0">
                    <h5 class="alert-heading">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Risk Compliance Alerts ({{ alerts|length }})
                    </h5>
                    {% for alert in alerts %}
                    <div class="d-flex align-items-center mb-2">
                        <i class="fas fa-arrow-right me-2 text-warning"></i>
                        <span>{{ alert }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Key Metrics Dashboard -->
        <div class="row mb-4">
            <div class="col-12 mb-3">
                <h3 class="text-primary">
                    <i class="fas fa-chart-bar me-2"></i>Key Performance Metrics
                </h3>
            </div>
            
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="metric-card status-info">
                    <div class="metric-value text-primary">${{ "{:,.0f}".format(total_value) }}</div>
                    <div class="metric-label">Portfolio Value</div>
                    <small class="text-muted">Current market value</small>
                </div>
            </div>
            
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="metric-card {% if volatility < 0.15 %}status-good{% elif volatility < 0.25 %}status-warning{% else %}status-danger{% endif %}">
                    <div class="metric-value {% if volatility < 0.15 %}text-success{% elif volatility < 0.25 %}text-warning{% else %}text-danger{% endif %}">
                        {{ "{:.1f}%".format(volatility * 100) }}
                    </div>
                    <div class="metric-label">Annual Volatility</div>
                    <small class="text-muted">Risk measure</small>
                </div>
            </div>
            
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="metric-card {% if var_95|abs < 0.02 %}status-good{% elif var_95|abs < 0.03 %}status-warning{% else %}status-danger{% endif %}">
                    <div class="metric-value {% if var_95|abs < 0.02 %}text-success{% elif var_95|abs < 0.03 %}text-warning{% else %}text-danger{% endif %}">
                        {{ "{:.1f}%".format(var_95|abs * 100) }}
                    </div>
                    <div class="metric-label">95% VaR</div>
                    <small class="text-muted">Daily risk</small>
                </div>
            </div>
            
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="metric-card {% if sharpe_ratio > 1 %}status-good{% elif sharpe_ratio > 0.5 %}status-warning{% else %}status-danger{% endif %}">
                    <div class="metric-value {% if sharpe_ratio > 1 %}text-success{% elif sharpe_ratio > 0.5 %}text-warning{% else %}text-danger{% endif %}">
                        {{ "{:.2f}".format(sharpe_ratio) }}
                    </div>
                    <div class="metric-label">Sharpe Ratio</div>
                    <small class="text-muted">Risk-adjusted return</small>
                </div>
            </div>
            
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="metric-card status-warning">
                    <div class="metric-value text-warning">{{ "{:.1f}%".format(max_drawdown|abs * 100) }}</div>
                    <div class="metric-label">Max Drawdown</div>
                    <small class="text-muted">Worst decline</small>
                </div>
            </div>
            
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="metric-card status-info">
                    <div class="metric-value text-info">{{ holdings_count }}</div>
                    <div class="metric-label">Total Holdings</div>
                    <small class="text-muted">Positions</small>
                </div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="row mb-4">
            <div class="col-12 mb-3">
                <h3 class="text-primary">
                    <i class="fas fa-chart-pie me-2"></i>Visual Portfolio Analytics
                </h3>
            </div>

            <!-- Check if static images exist first, then show embedded charts -->
            {% if use_static_images %}
            <!-- Portfolio Allocation -->
            <div class="col-lg-6 mb-4">
                <div class="chart-container">
                    <h5 class="chart-title text-center">
                        <i class="fas fa-pie-chart me-2 text-primary"></i>Portfolio Allocation
                    </h5>
                    <div class="text-center">
                        <img src="/static/portfolio_dashboard.png" class="img-fluid" alt="Portfolio Dashboard" style="max-height: 400px;">
                    </div>
                </div>
            </div>
            
            <!-- Correlation Matrix -->
            <div class="col-lg-6 mb-4">
                <div class="chart-container">
                    <h5 class="chart-title text-center">
                        <i class="fas fa-network-wired me-2 text-danger"></i>Correlation Matrix
                    </h5>
                    <div class="text-center">
                        <img src="/static/correlation_matrix.png" class="img-fluid" alt="Correlation Matrix" style="max-height: 400px;">
                    </div>
                </div>
            </div>
            {% else %}
            <!-- Embedded Charts -->
            <div class="col-lg-6 mb-4">
                <div class="chart-container">
                    <h5 class="chart-title text-center">
                        <i class="fas fa-pie-chart me-2 text-primary"></i>Portfolio Allocation
                    </h5>
                    <div class="text-center">
                        <img src="{{ allocation_chart }}" class="img-fluid" alt="Portfolio Allocation" style="max-height: 400px;">
                    </div>
                </div>
            </div>

            <div class="col-lg-6 mb-4">
                <div class="chart-container">
                    <h5 class="chart-title text-center">
                        <i class="fas fa-building me-2 text-success"></i>Sector Distribution
                    </h5>
                    <div class="text-center">
                        <img src="{{ sector_chart }}" class="img-fluid" alt="Sector Allocation" style="max-height: 400px;">
                    </div>
                </div>
            </div>

            {% if performance_chart %}
            <div class="col-lg-6 mb-4">
                <div class="chart-container">
                    <h5 class="chart-title text-center">
                        <i class="fas fa-line-chart me-2 text-info"></i>Performance Trend
                    </h5>
                    <div class="text-center">
                        <img src="{{ performance_chart }}" class="img-fluid" alt="Performance" style="max-height: 400px;">
                    </div>
                </div>
            </div>
            {% endif %}

            <div class="col-lg-6 mb-4">
                <div class="chart-container">
                    <h5 class="chart-title text-center">
                        <i class="fas fa-shield-alt me-2 text-warning"></i>Risk Metrics
                    </h5>
                    <div class="text-center">
                        <img src="{{ risk_chart }}" class="img-fluid" alt="Risk Metrics" style="max-height: 400px;">
                    </div>
                </div>
            </div>

            {% if correlation_chart %}
            <div class="col-12 mb-4">
                <div class="chart-container">
                    <h5 class="chart-title text-center">
                        <i class="fas fa-network-wired me-2 text-danger"></i>Asset Correlation Matrix
                    </h5>
                    <div class="text-center">
                        <img src="{{ correlation_chart }}" class="img-fluid" alt="Correlation Matrix" style="max-height: 500px;">
                    </div>
                    <p class="text-muted text-center mt-3">
                        <small>
                            <i class="fas fa-info-circle me-1"></i>
                            <strong>Red</strong> = High Positive Correlation | 
                            <strong>Blue</strong> = Negative Correlation | 
                            <strong>White</strong> = No Correlation
                        </small>
                    </p>
                </div>
            </div>
            {% endif %}
            {% endif %}
        </div>

        <!-- Holdings Table -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0 text-white">
                            <i class="fas fa-list me-2"></i>Portfolio Holdings Detail
                        </h5>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-tag me-1"></i>Symbol</th>
                                        <th><i class="fas fa-layer-group me-1"></i>Asset Class</th>
                                        <th><i class="fas fa-calculator me-1"></i>Quantity</th>
                                        <th><i class="fas fa-shopping-cart me-1"></i>Buy Price</th>
                                        <th><i class="fas fa-dollar-sign me-1"></i>Current Price</th>
                                        <th><i class="fas fa-wallet me-1"></i>Market Value</th>
                                        <th><i class="fas fa-percentage me-1"></i>Weight</th>
                                        <th><i class="fas fa-chart-line me-1"></i>P&L ($)</th>
                                        <th><i class="fas fa-percent me-1"></i>P&L (%)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for holding in holdings %}
                                    <tr>
                                        <td>
                                            <strong class="text-primary fs-6">{{ holding.symbol }}</strong>
                                        </td>
                                        <td>
                                            <span class="badge {% if holding.asset_class == 'Equity' %}bg-primary{% elif 'ETF' in holding.asset_class %}bg-success{% else %}bg-info{% endif %}">
                                                {{ holding.asset_class }}
                                            </span>
                                        </td>
                                        <td class="fw-semibold">{{ "{:.0f}".format(holding.quantity) }}</td>
                                        <td>${{ "{:.2f}".format(holding.purchase_price) }}</td>
                                        <td class="fw-semibold">${{ "{:.2f}".format(holding.current_price) }}</td>
                                        <td>
                                            <strong>${{ "{:,.2f}".format(holding.current_value) }}</strong>
                                        </td>
                                        <td>
                                            <span class="badge fs-6 {% if holding.weight > 20 %}bg-danger{% elif holding.weight > 15 %}bg-warning text-dark{% else %}bg-success{% endif %}">
                                                {{ "{:.1f}%".format(holding.weight) }}
                                            </span>
                                        </td>
                                        <td class="{% if holding.pnl >= 0 %}positive{% else %}negative{% endif %}">
                                            ${{ "{:+,.2f}".format(holding.pnl) }}
                                        </td>
                                        <td class="{% if holding.pnl_pct >= 0 %}positive{% else %}negative{% endif %}">
                                            {{ "{:+.1f}%".format(holding.pnl_pct) }}
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer Summary -->
        <div class="row mt-4">
            <div class="col text-center">
                <div class="card bg-primary text-white">
                    <div class="card-body py-3">
                        <p class="mb-0">
                            <i class="fas fa-check-circle me-2"></i>
                            Analysis Complete - Portfolio contains {{ holdings_count }} holdings worth ${{ "{:,.0f}".format(total_value) }}
                            {% if alerts %}
                            | <i class="fas fa-exclamation-triangle me-1"></i>{{ alerts|length }} Risk Alert(s)
                            {% else %}
                            | <i class="fas fa-shield-check me-1"></i>All Risk Limits Compliant
                            {% endif %}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Extended Web Analyzer Class
class WebAnalyzer(WebPortfolioRiskAnalyzer):
    def create_embedded_charts(self, metrics):
        """Create charts as base64 embedded images"""
        charts = {}
        plt.style.use('default')
        
        # 1. Portfolio Allocation
        fig, ax = plt.subplots(figsize=(8, 6))
        portfolio_df = metrics['portfolio_df']
        colors = plt.cm.Set3(np.linspace(0, 1, len(portfolio_df)))
        
        wedges, texts, autotexts = ax.pie(
            portfolio_df['current_value'], 
            labels=portfolio_df['symbol'], 
            autopct='%1.1f%%',
            colors=colors,
            explode=[0.05]*len(portfolio_df)
        )
        
        ax.set_title('Portfolio Allocation by Holdings', fontsize=14, fontweight='bold', pad=20)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        charts['allocation'] = self.fig_to_data_url(fig)
        plt.close()

        # 2. Sector Allocation
        fig, ax = plt.subplots(figsize=(8, 6))
        # Create better sector mapping
        portfolio_df['sector_mapped'] = portfolio_df['symbol'].map({
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'TSLA': 'Technology',
            'SPY': 'Broad Market ETF', 'BND': 'Fixed Income', 'GLD': 'Commodities'
        })
        
        sector_data = portfolio_df.groupby('sector_mapped')['current_value'].sum()
        colors = plt.cm.Set2(np.linspace(0, 1, len(sector_data)))
        
        wedges, texts, autotexts = ax.pie(sector_data.values, labels=sector_data.index, 
                                         autopct='%1.1f%%', colors=colors)
        ax.set_title('Sector Distribution', fontsize=14, fontweight='bold', pad=20)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        charts['sector'] = self.fig_to_data_url(fig)
        plt.close()

        # 3. Performance Chart
        if not metrics['price_data'].empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            price_data = metrics['price_data']
            weights = portfolio_df['weight'].values / 100
            portfolio_performance = (price_data * weights).sum(axis=1)
            portfolio_performance = (portfolio_performance / portfolio_performance.iloc[0] - 1) * 100
            
            ax.plot(portfolio_performance.index, portfolio_performance.values, 
                   linewidth=2, color='#2E86C1')
            ax.fill_between(portfolio_performance.index, portfolio_performance.values, 
                           alpha=0.3, color='#2E86C1')
            ax.set_title('Portfolio Performance Over Time', fontsize=14, fontweight='bold')
            ax.set_ylabel('Return (%)')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
            charts['performance'] = self.fig_to_data_url(fig)
            plt.close()

        # 4. Risk Metrics Bar Chart
        fig, ax = plt.subplots(figsize=(8, 5))
        risk_data = {
            'Volatility': metrics['portfolio_volatility'] * 100,
            'VaR 95%': abs(metrics['portfolio_var_95']) * 100,
            'Max Drawdown': abs(metrics['max_drawdown']) * 100,
            'Sharpe Ratio': metrics['sharpe_ratio']
        }
        
        colors = ['#E74C3C', '#F39C12', '#8E44AD', '#27AE60']
        bars = ax.bar(risk_data.keys(), risk_data.values(), color=colors)
        ax.set_title('Risk Metrics Overview', fontsize=14, fontweight='bold')
        
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45)
        charts['risk'] = self.fig_to_data_url(fig)
        plt.close()

        # 5. Correlation Heatmap
        if not metrics['correlation_matrix'].empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(metrics['correlation_matrix'], 
                       annot=True, cmap='RdYlBu_r', center=0,
                       square=True, fmt='.2f')
            ax.set_title('Asset Correlation Matrix', fontsize=14, fontweight='bold')
            
            charts['correlation'] = self.fig_to_data_url(fig)
            plt.close()

        return charts
    
    def fig_to_data_url(self, fig):
        """Convert matplotlib figure to data URL"""
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

# Initialize the analyzer
analyzer = WebAnalyzer()

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    try:
        print("🔄 Running portfolio analysis...")
        
        # Run the full analysis
        metrics = analyzer.calculate_portfolio_metrics()
        if not metrics:
            return "❌ No portfolio data found! Please check if portfolio.db exists.", 404
        
        # Check compliance
        alerts = analyzer.check_risk_compliance(metrics)
        alert_messages = []
        for alert in alerts:
            if isinstance(alert, dict):
                alert_messages.append(alert.get('message', str(alert)))
            else:
                alert_messages.append(str(alert))
        
        # Generate PDF report
        analyzer.generate_pdf_report(metrics, alerts)
        
        # Check if static images exist (from your original run)
        static_images_exist = (
            os.path.exists('portfolio_dashboard.png') or 
            os.path.exists('correlation_matrix.png')
        )
        
        if static_images_exist:
            # Move images to static folder if they exist
            if not os.path.exists('static'):
                os.makedirs('static')
            
            for img_file in ['portfolio_dashboard.png', 'correlation_matrix.png']:
                if os.path.exists(img_file):
                    import shutil
                    shutil.copy(img_file, f'static/{img_file}')
        
        # Create embedded charts as backup
        charts = analyzer.create_embedded_charts(metrics)
        
        # Prepare template data
        from datetime import datetime
        template_data = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_value': metrics['total_value'],
            'volatility': metrics['portfolio_volatility'], 
            'var_95': metrics['portfolio_var_95'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown': metrics['max_drawdown'],
            'holdings_count': len(metrics['portfolio_df']),
            'holdings': metrics['portfolio_df'].to_dict('records'),
            'alerts': alert_messages,
            'use_static_images': static_images_exist,
            'allocation_chart': charts.get('allocation', ''),
            'sector_chart': charts.get('sector', ''),
            'performance_chart': charts.get('performance', ''),
            'risk_chart': charts.get('risk', ''),
            'correlation_chart': charts.get('correlation', '')
        }
        
        print("✅ Analysis complete! Rendering dashboard...")
        return render_template_string(DASHBOARD_TEMPLATE, **template_data)
        
    except Exception as e:
        error_msg = f"❌ Analysis failed: {str(e)}"
        print(error_msg)
        return f"""
        <div style="padding: 50px; text-align: center; font-family: Arial;">
            <h2 style="color: #dc2626;">Analysis Error</h2>
            <p>{error_msg}</p>
            <a href="/" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Back to Home</a>
        </div>
        """, 500

@app.route('/static/<filename>')
def static_files(filename):
    """Serve static files"""
    try:
        return send_file(filename)
    except:
        return "File not found", 404

@app.route('/download-pdf')
def download_pdf():
    """Download the PDF report"""
    try:
        return send_file('portfolio_risk_report.pdf', as_attachment=True, 
                        download_name=f'portfolio_report_{pd.Timestamp.now().strftime("%Y%m%d")}.pdf')
    except Exception as e:
        return f"PDF not found: {str(e)}. Please run analysis first.", 404

@app.route('/view-pdf')
def view_pdf():
    """View the PDF report in browser"""
    try:
        return send_file('portfolio_risk_report.pdf')
    except Exception as e:
        return f"PDF not found: {str(e)}. Please run analysis first.", 404

if __name__ == '__main__':
    print("🚀 Portfolio Risk Analyzer - Web Interface")
    print("=" * 50)
    print("📂 Project Structure Detected:")
    
    # Check existing files
    files_found = []
    if os.path.exists('portfolio_analyzer.py'):
        files_found.append("✅ portfolio_analyzer.py")
    if os.path.exists('portfolio.db'):
        files_found.append("✅ portfolio.db")
    if os.path.exists('portfolio_dashboard.png'):
        files_found.append("✅ portfolio_dashboard.png")
    if os.path.exists('correlation_matrix.png'):
        files_found.append("✅ correlation_matrix.png")
    if os.path.exists('portfolio_risk_report.pdf'):
        files_found.append("✅ portfolio_risk_report.pdf")
        
    for file in files_found:
        print(f"   {file}")
    
    print(f"\n🌐 Starting web server...")
    print(f"📊 Open your browser to: http://localhost:5000")
    print(f"💡 The app will use existing charts if available, or generate new ones")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)