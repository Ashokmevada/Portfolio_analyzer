# 🎯 Portfolio Risk Monitor - Project Walkthrough for Interviewers

📌 **Live Preview:** [Portfolio Risk Monitor](https://portfolio-analyzer-z9u7.onrender.com/)  

This project demonstrates how I designed and implemented a **portfolio risk management system** that makes risk visible, measurable, and actionable.  

---

## 📋 The Business Problem

Imagine Sarah, a young professional, investing in Apple, Microsoft, Tesla, and SPY ETF. She doesn’t know:
- How much risk she’s actually taking  
- Whether her portfolio is over-concentrated  
- What her potential losses could look like  
- If her investments are diversified enough  

👉 **This system solves exactly that problem.**

---

## 🔄 System Workflow

### 1. Portfolio Data Collection & Storage
- Stores holdings, purchase dates, and quantities in a **SQL database**.  
- Tracks personal **risk tolerance rules** (limits on VaR, concentration, etc.).  
- Maintains **performance history** over time.  

### 2. Real-Time Market Data Integration
- Uses **Yahoo Finance API** to fetch live prices.  
- Updates portfolio valuations automatically.  

### 3. Valuation & Performance Attribution
- Calculates current portfolio value, daily gains/losses.  
- Computes weight distribution across holdings.  
- Identifies **concentration risks** (e.g., SPY = 63% of portfolio).  

### 4. Advanced Risk Metrics
- **VaR (95% confidence)** – potential worst-case daily loss.  
- **Volatility** – expected swings in portfolio value.  
- **Sharpe Ratio** – risk-adjusted return quality.  
- **Max Drawdown** – worst historical peak-to-trough loss.  
- **Correlation Analysis** – diversification assessment.  

### 5. Compliance Monitoring
- Checks portfolio against user-defined limits:  
  - Max position size  
  - Sector exposure  
  - Daily VaR threshold  
- Flags **violations** and **warnings**.  

### 6. Alerts & Notifications
- Generates critical alerts for violations (e.g., overexposure).  
- Provides diversification warnings and performance updates.  

### 7. Reporting & Visualization
- **Dashboard**: allocation pie charts, risk metrics, performance trends.  
- **Correlation heatmap**: visual insight into diversification gaps.  
- **PDF Executive Report**: professional risk summary with alerts.  

---

## 🎯 Real-World Impact

**Before system**:  
- Sarah didn’t realize SPY was 63% of her portfolio.  
- Had no quantifiable measure of risk.  
- Made emotional, uninformed decisions.  

**After system**:  
- Knows her potential daily losses (VaR).  
- Gets alerts when risk limits are breached.  
- Makes informed, data-driven decisions.  
- Discusses risks with advisors using clear reports.  

💡 **Example**: A 30% tech crash would cost her ~$1,400, but the system’s early alerts cut losses to ~$800 → **$600 saved**.  

---

## 🔧 Technical Architecture

- **Database**: SQL for holdings, limits, performance tracking.  
- **Pipeline**:  
  1. Input (manual or CSV)  
  2. Processing (market data, metrics)  
  3. Analysis (risk measures, compliance)  
  4. Output (reports, alerts)  
- **Error Handling**: API fallback, missing data handling, input validation.  

---

## 💼 Why This Matters

This project bridges **finance and technology**, showing my ability to:  
- Quantify and monitor investment risks.  
- Build automated reporting & compliance tools.  
- Communicate complex risk metrics in a simple way.  

### Relevant to Roles:
- **Performance Reporting (e.g., OMERS)**: attribution analysis, reporting design.  
- **Risk Services (e.g., Definity)**: compliance monitoring, risk analytics.  

---

## 🛠️ Tech Stack

- **Python**: Pandas, NumPy, Matplotlib, Seaborn  
- **APIs**: Yahoo Finance  
- **Databases**: SQL  
- **Reporting**: ReportLab (PDF), visualization dashboards  
- **Version Control**: Git/GitHub  

---

## 🚀 Key Takeaway

This isn’t just a coding exercise — it’s a **practical risk management system** that helps investors understand and control risk, prevents costly mistakes, and produces professional, advisor-ready reports.  

📌 **Try it here:** [Portfolio Risk Monitor](https://portfolio-analyzer-z9u7.onrender.com/)  
