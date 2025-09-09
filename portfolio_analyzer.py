import os
import io
import base64
import sqlite3
from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import warnings
warnings.filterwarnings('ignore')

class WebPortfolioRiskAnalyzer:
    def __init__(self, db_name='portfolio.db'):
        self.db_name = db_name
        self.setup_database()

    def setup_database(self):
        """Create database tables for portfolio tracking"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                asset_class TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_limits (
                id INTEGER PRIMARY KEY,
                metric TEXT NOT NULL,
                limit_value REAL NOT NULL,
                alert_threshold REAL NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                total_value REAL NOT NULL,
                daily_return REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def add_holding(self, symbol, quantity, purchase_price, purchase_date, asset_class):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO holdings (symbol, quantity, purchase_price, purchase_date, asset_class)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, quantity, purchase_price, purchase_date, asset_class))
        conn.commit()
        conn.close()

    def set_risk_limits(self, max_portfolio_var=0.05, max_individual_weight=0.15, max_sector_concentration=0.30):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM risk_limits')
        limits = [
            ('portfolio_var_95', max_portfolio_var, max_portfolio_var * 0.8),
            ('individual_weight', max_individual_weight, max_individual_weight * 0.9),
            ('sector_concentration', max_sector_concentration, max_sector_concentration * 0.9)
        ]
        cursor.executemany('INSERT INTO risk_limits VALUES (NULL, ?, ?, ?)', limits)
        conn.commit()
        conn.close()

    def get_current_portfolio(self):
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query('SELECT * FROM holdings', conn)
        conn.close()
        return df

    def fetch_market_data(self, symbols, period='1y'):
        data = {}
        try:
            price_data = yf.download(symbols, period=period)['Close']
            for symbol in symbols:
                hist = price_data[symbol] if symbol in price_data else pd.Series([0])
                data[symbol] = {
                    'current_price': hist.iloc[-1] if not hist.empty else 0,
                    'price_history': hist,
                    'sector': 'Technology' if symbol in ['AAPL', 'MSFT', 'GOOGL', 'TSLA'] else 'ETF',
                    'industry': 'Unknown',
                    'market_cap': 0
                }
        except Exception as e:
            print(f"Error fetching data: {e}")
        return data

    def calculate_portfolio_metrics(self):
        holdings = self.get_current_portfolio()
        if holdings.empty:
            return None

        symbols = holdings['symbol'].unique().tolist()
        market_data = self.fetch_market_data(symbols)

        portfolio_data = []
        total_value = 0
        for _, holding in holdings.iterrows():
            symbol = holding['symbol']
            current_price = market_data[symbol]['current_price']
            current_value = holding['quantity'] * current_price
            cost_basis = holding['quantity'] * holding['purchase_price']
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0

            portfolio_data.append({
                'symbol': symbol,
                'quantity': holding['quantity'],
                'purchase_price': holding['purchase_price'],
                'current_price': current_price,
                'cost_basis': cost_basis,
                'current_value': current_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'asset_class': holding['asset_class'],
                'sector': market_data[symbol]['sector'],
                'weight': 0
            })
            total_value += current_value

        for item in portfolio_data:
            item['weight'] = (item['current_value'] / total_value) * 100 if total_value > 0 else 0

        portfolio_df = pd.DataFrame(portfolio_data)

        # Risk calculations
        price_data_df = pd.DataFrame({s: market_data[s]['price_history'] for s in symbols}).dropna()
        if len(price_data_df) > 1:
            returns = price_data_df.pct_change().dropna()
            weights = np.array([item['weight']/100 for item in portfolio_data])
            portfolio_returns = (returns * weights).sum(axis=1)
            portfolio_volatility = portfolio_returns.std() * np.sqrt(252)
            portfolio_var_95 = np.percentile(portfolio_returns, 5)
            max_drawdown = self.calculate_max_drawdown(price_data_df, weights)
            sharpe_ratio = self.calculate_sharpe_ratio(portfolio_returns)
            correlation_matrix = returns.corr()
        else:
            portfolio_volatility = portfolio_var_95 = max_drawdown = sharpe_ratio = 0
            correlation_matrix = pd.DataFrame()

        return {
            'portfolio_df': portfolio_df,
            'total_value': total_value,
            'portfolio_volatility': portfolio_volatility,
            'portfolio_var_95': portfolio_var_95,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'correlation_matrix': correlation_matrix,
            'price_data': price_data_df
        }

    def calculate_max_drawdown(self, price_data, weights):
        portfolio_values = (price_data * weights).sum(axis=1)
        running_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - running_max) / running_max
        return drawdown.min()

    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.02):
        excess_returns = returns.mean() * 252 - risk_free_rate
        volatility = returns.std() * np.sqrt(252)
        return excess_returns / volatility if volatility > 0 else 0

    def check_risk_compliance(self, metrics):
        conn = sqlite3.connect(self.db_name)
        limits_df = pd.read_sql_query('SELECT * FROM risk_limits', conn)
        conn.close()
        alerts = []

        for _, limit in limits_df.iterrows():
            metric_name = limit['metric']
            limit_value = limit['limit_value']
            alert_threshold = limit['alert_threshold']

            if metric_name == 'portfolio_var_95':
                current_value = abs(metrics['portfolio_var_95'])
                if current_value > limit_value:
                    alerts.append({'type': 'danger', 'message': f"Portfolio VaR ({current_value:.2%}) exceeds limit ({limit_value:.2%})"})
                elif current_value > alert_threshold:
                    alerts.append({'type': 'warning', 'message': f"Portfolio VaR ({current_value:.2%}) approaching limit ({limit_value:.2%})"})
            elif metric_name == 'individual_weight':
                max_weight = metrics['portfolio_df']['weight'].max() / 100
                if max_weight > limit_value:
                    symbol = metrics['portfolio_df'].loc[metrics['portfolio_df']['weight'].idxmax(), 'symbol']
                    alerts.append({'type': 'danger', 'message': f"{symbol} weight ({max_weight:.2%}) exceeds limit ({limit_value:.2%})"})
                elif max_weight > alert_threshold:
                    symbol = metrics['portfolio_df'].loc[metrics['portfolio_df']['weight'].idxmax(), 'symbol']
                    alerts.append({'type': 'warning', 'message': f"{symbol} weight ({max_weight:.2%}) approaching limit ({limit_value:.2%})"})

        return alerts

    def create_web_visualizations(self, metrics):
        """Create visualizations and save them to static folder"""
        charts = {}
        
        # Ensure static directory exists
        os.makedirs('static', exist_ok=True)
        
        # Set style for better web display
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            plt.style.use('default')
        
        # 1. Portfolio Allocation Pie Chart
        fig, ax = plt.subplots(figsize=(10, 8))
        portfolio_df = metrics['portfolio_df']
        colors_palette = plt.cm.Set3(np.linspace(0, 1, len(portfolio_df)))
        wedges, texts, autotexts = ax.pie(portfolio_df['current_value'], 
                                         labels=portfolio_df['symbol'], 
                                         autopct='%1.1f%%',
                                         colors=colors_palette,
                                         explode=[0.05]*len(portfolio_df))
        ax.set_title('Portfolio Allocation by Holdings', fontsize=16, fontweight='bold', pad=20)
        
        # Make text more readable
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        plt.savefig('static/portfolio_allocation.png', dpi=300, bbox_inches='tight')
        charts['allocation'] = 'static/portfolio_allocation.png'
        plt.close()

        # 2. Sector Allocation
        fig, ax = plt.subplots(figsize=(10, 8))
        sector_allocation = portfolio_df.groupby('sector')['current_value'].sum()
        colors_palette = plt.cm.Pastel1(np.linspace(0, 1, len(sector_allocation)))
        wedges, texts, autotexts = ax.pie(sector_allocation.values, 
                                         labels=sector_allocation.index, 
                                         autopct='%1.1f%%',
                                         colors=colors_palette)
        ax.set_title('Sector Allocation', fontsize=16, fontweight='bold', pad=20)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        plt.savefig('static/sector_allocation.png', dpi=300, bbox_inches='tight')
        charts['sector'] = 'static/sector_allocation.png'
        plt.close()

        # 3. Performance Chart  
        if not metrics['price_data'].empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            price_data = metrics['price_data']
            weights = portfolio_df['weight'].values / 100
            portfolio_performance = (price_data * weights).sum(axis=1)
            portfolio_performance = (portfolio_performance / portfolio_performance.iloc[0] - 1) * 100
            
            ax.plot(portfolio_performance.index, portfolio_performance.values, 
                   linewidth=3, color='#2E86C1', alpha=0.8)
            ax.fill_between(portfolio_performance.index, portfolio_performance.values, 
                           alpha=0.3, color='#2E86C1')
            ax.set_title('Portfolio Performance (%)', fontsize=16, fontweight='bold')
            ax.set_ylabel('Performance (%)', fontsize=12)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('static/portfolio_performance.png', dpi=300, bbox_inches='tight')
            charts['performance'] = 'static/portfolio_performance.png'
            plt.close()

        # 4. Risk Metrics Bar Chart
        fig, ax = plt.subplots(figsize=(10, 6))
        risk_metrics = {
            'Volatility (%)': metrics['portfolio_volatility'] * 100,
            'VaR 95% (%)': abs(metrics['portfolio_var_95']) * 100,
            'Max Drawdown (%)': abs(metrics['max_drawdown']) * 100,
            'Sharpe Ratio': metrics['sharpe_ratio']
        }
        
        bars = ax.bar(risk_metrics.keys(), risk_metrics.values(), 
                     color=['#E74C3C', '#F39C12', '#8E44AD', '#27AE60'])
        ax.set_title('Risk Metrics Dashboard', fontsize=16, fontweight='bold')
        ax.set_ylabel('Value', fontsize=12)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/risk_metrics.png', dpi=300, bbox_inches='tight')
        charts['risk_metrics'] = 'static/risk_metrics.png'
        plt.close()

        # 5. Correlation Heatmap
        if not metrics['correlation_matrix'].empty:
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(metrics['correlation_matrix'], 
                       annot=True, 
                       cmap='RdYlBu_r', 
                       center=0,
                       square=True,
                       fmt='.2f',
                       cbar_kws={"shrink": .8})
            ax.set_title('Asset Correlation Matrix', fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()
            plt.savefig('static/correlation_matrix.png', dpi=300, bbox_inches='tight')
            charts['correlation'] = 'static/correlation_matrix.png'
            plt.close()

        return charts

    def generate_pdf_report(self, metrics, alerts):
        """Generate PDF report and save to static folder"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        # Ensure static directory exists
        os.makedirs('static', exist_ok=True)
        
        doc = SimpleDocTemplate("static/portfolio_risk_report.pdf", pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                   fontSize=18, spaceAfter=30, textColor=colors.darkblue)
        story.append(Paragraph("Portfolio Risk Analytics Report", title_style))
        story.append(Spacer(1, 12))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        
        portfolio_df = metrics['portfolio_df']
        total_pnl = portfolio_df['pnl'].sum()
        total_pnl_pct = (total_pnl / portfolio_df['cost_basis'].sum()) * 100 if portfolio_df['cost_basis'].sum() > 0 else 0
        
        summary_text = f"""
        <b>Portfolio Value:</b> ${metrics['total_value']:,.2f}<br/>
        <b>Total P&L:</b> ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%)<br/>
        <b>Portfolio Volatility:</b> {metrics['portfolio_volatility']:.2%}<br/>
        <b>95% VaR:</b> {metrics['portfolio_var_95']:.2%}<br/>
        <b>Sharpe Ratio:</b> {metrics['sharpe_ratio']:.2f}<br/>
        <b>Max Drawdown:</b> {metrics['max_drawdown']:.2%}
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Risk Alerts
        if alerts:
            story.append(Paragraph("Risk Alerts", styles['Heading2']))
            for alert in alerts:
                message = alert['message'] if isinstance(alert, dict) else str(alert)
                story.append(Paragraph(f"• {message}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Holdings Table
        story.append(Paragraph("Current Holdings", styles['Heading2']))
        
        table_data = [['Symbol', 'Quantity', 'Current Price', 'Value', 'Weight', 'P&L', 'P&L %']]
        for _, row in portfolio_df.iterrows():
            table_data.append([
                row['symbol'],
                f"{row['quantity']:.0f}",
                f"${row['current_price']:.2f}",
                f"${row['current_value']:,.2f}",
                f"{row['weight']:.1f}%",
                f"${row['pnl']:,.2f}",
                f"{row['pnl_pct']:+.1f}%"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        
        doc.build(story)
        return True

# Initialize sample data function
def initialize_sample_data(analyzer):
    conn = sqlite3.connect('portfolio.db')
    conn.execute('DELETE FROM holdings')
    conn.commit()
    conn.close()
    
    sample_holdings = [
        ('AAPL', 10, 150.00, '2024-01-15', 'Equity'),
        ('MSFT', 8, 300.00, '2024-02-01', 'Equity'),
        ('GOOGL', 5, 140.00, '2024-01-20', 'Equity'),
        ('TSLA', 3, 200.00, '2024-03-01', 'Equity'),
        ('SPY', 20, 400.00, '2024-01-10', 'ETF'),
        ('BND', 15, 80.00, '2024-02-15', 'Bond ETF'),
        ('GLD', 5, 180.00, '2024-03-15', 'Commodity ETF')
    ]
    
    for holding in sample_holdings:
        analyzer.add_holding(*holding)
    
    analyzer.set_risk_limits(max_portfolio_var=0.03,
                           max_individual_weight=0.20,
                           max_sector_concentration=0.40)