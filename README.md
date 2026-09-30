🛒 E-Commerce Sales & Profitability Analysis (EDA with Python)

An end-to-end Exploratory Data Analysis of 3,200 online orders (Jan 2024 – Dec 2025, India) covering data cleaning, KPI analysis, time trends, customer RFM segmentation, geography, channels, discounts and actionable recommendations.

📌 Project Overview
	
Goal	Understand what drives revenue and profit, and where the business leaks value
Data	ecommerce_sales_analytics.xlsx – 3,200 rows × 22 columns, no duplicates
Tools	Python, Pandas, NumPy, Matplotlib, Seaborn
Period	01-Jan-2024 to 31-Dec-2025
🗂️ Repository Structure
├── data/
│   ├── ecommerce_sales_analytics.xlsx     # raw data
│   ├── cleaned_ecommerce_sales.csv        # cleaned + engineered features
│   └── rfm_segments.csv                   # customer RFM output
├── notebooks/
│   └── Data_Analysis_Python_Project.ipynb # original exploratory notebook
├── src/
│   └── eda_analysis.py                    # reproducible end-to-end script
├── charts/                                # 13 exported figures
├── reports/
│   ├── Ecommerce_EDA_Report.docx
│   └── Ecommerce_EDA_Presentation.pptx
├── requirements.txt
└── README.md
📖 Data Dictionary
Column	Description
Order_ID, Order_Date	Unique order id and order date
Customer_ID, Customer_Age, Customer_Gender	Customer identifiers and demographics
City, State, Region	Delivery geography (12 cities, 11 states, 5 regions)
Product_ID, Product_Name, Category	Product details (24 products, 6 categories)
Quantity, Unit_Price, Discount_Pct	Units, list price (₹), discount (0–25%)
Sales, Cost, Profit	Order revenue, cost and profit (Profit = Sales − Cost)
Payment_Method, Sales_Channel, Shipping_Type	UPI/Cards/etc., Website/App/Marketplace, Standard/Express/Same Day
Order_Status	Delivered / Returned / Cancelled
Customer_Rating	1–5 rating
🧹 Data Cleaning
Issue	Treatment
Customer_Gender – 25 nulls	Filled with "Unknown"
Discount_Pct – 32 nulls	Filled with 0 (assumed no discount)
Customer_Rating – 48 nulls	Kept as numeric NaN + Rating_Missing flag (avoids turning column into text)
Column names	Renamed for readability (Age, Gender, Discount, Product_Category)
New features	Year, Month, Quarter, Age_Group, Margin_Pct, Discount band

Validation: Profit = Sales − Cost holds for every row; 99.2% of Sales match Quantity × Unit_Price × (1 − Discount).

🔑 Key Findings

(Revenue/profit use delivered orders only unless stated.)

KPI	Value
Realised revenue	₹52.5M (gross incl. returns/cancels: ₹57.6M)
Profit / margin	₹10.5M / 19.96%
Orders / customers	2,933 / 823
Average order value	₹17,906
Electronics = 72% of revenue but only 15.1% margin. Laptop Pro 14 alone is 47% of revenue at 13.7% margin. Beauty (44.3%) and Fashion (35.6%) are the most profitable.
Revenue is flat: 2024 ₹26.4M vs 2025 ₹26.1M (−1.4%); margin edged up 19.7% → 20.2%. Peak month Nov 2025 (₹3.03M), lowest May 2025. Q4 is the strongest quarter (27%).
Discounts erode profit: correlation with margin % is −0.49; average margin falls from 38.6% (no discount) to 22.2% (16–25%).
8.3% of orders are returned/cancelled, worth ₹5.1M of gross sales.
Customers: 88% repeat buyers; top 20% of customers = 60.8% of revenue. RFM: Loyal 31.9%, Champions 28.3%, At Risk 18.6%, Lost 13.4%, New 7.7% of revenue.
Geography & channel: South leads (34.6%); Maharashtra is the top state. Website = 44.7% of revenue; UPI is the most used payment method; Standard shipping is 65% of orders.
💡 Recommendations
Diversify away from Electronics towards higher-margin categories.
Limit blanket discounts (~10% cap); use targeted offers.
Run win-back campaigns for the 146 At Risk customers.
Investigate return/cancellation drivers in Electronics and Home & Kitchen.
Plan inventory and marketing around Q4 / November peaks.
▶️ How to Run
bash
pip install -r requirements.txt
python src/eda_analysis.py data/ecommerce_sales_analytics.xlsx

Outputs: charts/*.png, metrics.json, cleaned_ecommerce_sales.csv, rfm_segments.csv. (Create a charts/ folder first.)

⚠️ Limitations
Only two years of data; no cost breakdown beyond total Cost.
Missing discounts assumed to be 0%.
RFM uses quintile scoring with rule-based segments.
🚀 Future Work

Forecasting (SARIMA/Prophet), churn prediction, product-level pricing/discount optimisation, interactive dashboard (Power BI / Streamlit).

👤 Author
Vaibhav Choudhary
