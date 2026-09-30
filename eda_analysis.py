"""E-commerce Sales & Profitability EDA - reproducible script.
Usage: python eda_analysis.py [path_to_xlsx]"""
import sys, json, warnings
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
warnings.filterwarnings("ignore")
SRC = sys.argv[1] if len(sys.argv) > 1 else "ecommerce_sales_analytics.xlsx"
OUT = "charts/"
sns.set_theme(style="whitegrid", palette="viridis")
PAL = "#0F4C5C"
M = {}

# 1. LOAD & AUDIT
df = pd.read_excel(SRC)
M["rows"], M["cols"] = df.shape
M["dups"] = int(df.duplicated().sum())
M["nulls"] = df.isna().sum()[lambda s: s > 0].to_dict()
M["date_min"], M["date_max"] = str(df.Order_Date.min().date()), str(df.Order_Date.max().date())
calc = (df.Quantity * df.Unit_Price * (1 - df.Discount_Pct.fillna(0))).round()
M["sales_formula_match_pct"] = round(float((calc == df.Sales).mean() * 100), 1)
M["profit_eq_sales_minus_cost"] = bool((df.Sales - df.Cost == df.Profit).all())

# 2. CLEAN (non-destructive: keep all rows)
df["Customer_Gender"] = df.Customer_Gender.fillna("Unknown")
df["Discount_Pct"] = df.Discount_Pct.fillna(0)          # assumption: missing = no discount
df["Rating_Missing"] = df.Customer_Rating.isna()        # keep numeric, flag missing
df = df.rename(columns={"Customer_Gender": "Gender", "Customer_Age": "Age", "Category": "Product_Category", "Discount_Pct": "Discount"})
df["Year"], df["Month"] = df.Order_Date.dt.year, df.Order_Date.dt.month
df["Quarter"] = df.Order_Date.dt.quarter
df["Margin_Pct"] = df.Profit / df.Sales * 100
df["Age_Group"] = pd.cut(df.Age, [17, 25, 35, 45, 55, 65], labels=["18-25", "26-35", "36-45", "46-55", "56-65"])
M["age_min"], M["age_max"] = int(df.Age.min()), int(df.Age.max())
M["neg_profit_rows"] = int((df.Profit < 0).sum())
dl = df[df.Order_Status == "Delivered"]

# 3. KPIs
def kp(d): return dict(sales=int(d.Sales.sum()), cost=int(d.Cost.sum()), profit=int(d.Profit.sum()), units=int(d.Quantity.sum()),
    orders=int(d.Order_ID.nunique()), customers=int(d.Customer_ID.nunique()), aov=round(d.Sales.sum()/d.Order_ID.nunique()), margin=round(d.Profit.sum()/d.Sales.sum()*100, 2))
M["kpi_all"], M["kpi_delivered"] = kp(df), kp(dl)
st = df.Order_Status.value_counts(); M["status"] = st.to_dict()
M["status_sales_lost"] = df[df.Order_Status != "Delivered"].groupby("Order_Status").Sales.sum().to_dict()
M["rating_mean"] = round(df.Customer_Rating.mean(), 2)
M["rating_dist"] = df.Customer_Rating.value_counts().sort_index().to_dict()

# 4. GROUPED TABLES (delivered orders = realised revenue)
def tbl(by, d=dl): 
    g = d.groupby(by).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order_ID", "nunique")).sort_values("Sales", ascending=False)
    g["Margin_Pct"] = (g.Profit / g.Sales * 100).round(2); return g
T = {k: tbl(k) for k in ["Product_Category", "Product_Name", "Region", "State", "City", "Sales_Channel", "Payment_Method", "Shipping_Type", "Gender", "Age_Group", "Year", "Quarter", "Month"]}
for k, v in T.items(): M["t_" + k] = v.round(2).reset_index().to_dict("records")
M["disc_corr"] = round(df[["Discount", "Sales", "Profit", "Margin_Pct"]].corr().loc["Discount"].drop("Discount"), 3).to_dict()
df["Disc_Band"] = pd.cut(df.Discount, [-.01, 0, .1, .15, .25], labels=["0%", "1-10%", "11-15%", "16-25%"])
M["disc_band"] = df.groupby("Disc_Band").agg(Orders=("Order_ID", "count"), Margin=("Margin_Pct", "mean")).round(2).reset_index().astype({"Disc_Band": str}).to_dict("records")
M["disc_vals"] = sorted(df.Discount.unique().tolist())
sc = df.groupby("Shipping_Type").Order_Status.apply(lambda s: (s != "Delivered").mean() * 100).round(2); M["fail_by_ship"] = sc.to_dict()
M["fail_by_cat"] = df.groupby("Product_Category").Order_Status.apply(lambda s: (s != "Delivered").mean() * 100).round(2).to_dict()
M["rating_by_ship"] = df.groupby("Shipping_Type").Customer_Rating.mean().round(2).to_dict()
M["rating_by_cat"] = df.groupby("Product_Category").Customer_Rating.mean().round(2).to_dict()
M["top_products_profit"] = dl.groupby("Product_Name").Profit.sum().nlargest(5).to_dict()
M["mean_by_cat_margin"] = dl.groupby("Product_Category").apply(lambda g: g.Profit.sum()/g.Sales.sum()*100).round(2).to_dict()

# monthly
ms = dl.groupby(["Year", "Month"]).Sales.sum().unstack(0); M["monthly"] = ms.to_dict()
M["year_sales"] = dl.groupby("Year").Sales.sum().to_dict()
M["year_orders"] = dl.groupby("Year").Order_ID.nunique().to_dict()
M["year_margin"] = dl.groupby("Year").apply(lambda g: round(g.Profit.sum()/g.Sales.sum()*100, 2)).to_dict()
mm = dl.groupby(dl.Order_Date.dt.to_period("M")).Sales.sum(); M["best_month"] = [str(mm.idxmax()), int(mm.max())]; M["worst_month"] = [str(mm.idxmin()), int(mm.min())]

# 5. RFM
ref = dl.Order_Date.max() + pd.Timedelta(days=1)
rfm = dl.groupby("Customer_ID").agg(Recency=("Order_Date", lambda x: (ref - x.max()).days), Frequency=("Order_ID", "nunique"), Monetary=("Sales", "sum")).reset_index()
rfm["R"] = pd.qcut(rfm.Recency, 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm.Frequency.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["M"] = pd.qcut(rfm.Monetary, 5, labels=[1, 2, 3, 4, 5]).astype(int)
def seg(r):
    if r.R >= 4 and r.F >= 4 and r.M >= 4: return "Champions"
    if r.R >= 3 and r.F >= 3: return "Loyal"
    if r.R >= 4 and r.F <= 2: return "New Customers"
    if r.R <= 2 and r.F >= 3: return "At Risk"
    return "Lost"
rfm["Segment"] = rfm.apply(seg, axis=1)
rs = rfm.groupby("Segment").agg(Customers=("Customer_ID", "count"), Revenue=("Monetary", "sum"), AvgOrders=("Frequency", "mean"), AvgRecency=("Recency", "mean")).round(1)
rs["Rev_Share"] = (rs.Revenue / rs.Revenue.sum() * 100).round(1); M["rfm"] = rs.reset_index().to_dict("records")
M["cust_orders"] = dl.groupby("Customer_ID").Order_ID.nunique().describe().round(2).to_dict()
top10 = dl.groupby("Customer_ID").Sales.sum().nlargest(10); M["top10_cust"] = top10.to_dict()
cs = dl.groupby("Customer_ID").Sales.sum().sort_values(ascending=False)
M["top20pct_share"] = round(float(cs.head(int(len(cs)*.2)).sum() / cs.sum() * 100), 1)
M["repeat_pct"] = round(float((dl.groupby("Customer_ID").Order_ID.nunique() > 1).mean() * 100), 1)
M["outliers_sales_iqr"] = int(((df.Sales > df.Sales.quantile(.75) + 1.5*(df.Sales.quantile(.75)-df.Sales.quantile(.25)))).sum())
M["corr"] = df[["Age", "Quantity", "Unit_Price", "Discount", "Sales", "Cost", "Profit", "Customer_Rating"]].corr().round(2).to_dict()

# 6. CHARTS
def save(n): plt.tight_layout(); plt.savefig(OUT + n, dpi=150, bbox_inches="tight"); plt.close()
def fmt(ax, ax_="x"): 
    f = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K")
    (ax.xaxis if ax_ == "x" else ax.yaxis).set_major_formatter(f)
c = T["Product_Category"]; fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
sns.barplot(x=c.Sales, y=c.index, color=PAL, ax=ax[0]); ax[0].set_title("Revenue by Category (Delivered)"); fmt(ax[0]); ax[0].set_ylabel("")
sns.barplot(x=c.Margin_Pct, y=c.index, color="#E36414", ax=ax[1]); ax[1].set_title("Profit Margin % by Category"); ax[1].set_ylabel("")
for a in ax:
    for b in a.containers: a.bar_label(b, fmt="%.1f" if a is ax[1] else "%.2s", padding=2, fontsize=8) if a is ax[1] else None
save("01_category.png")
fig, ax = plt.subplots(figsize=(8, 4.5)); p = T["Product_Name"].head(10).iloc[::-1]; ax.barh(p.index, p.Sales, color=PAL); fmt(ax); ax.set_title("Top 10 Products by Revenue"); save("02_top_products.png")
fig, ax = plt.subplots(figsize=(10, 4.2)); mt = dl.groupby(dl.Order_Date.dt.to_period("M")).Sales.sum(); ax.plot(mt.index.to_timestamp(), mt.values, marker="o", color=PAL); fmt(ax, "y"); ax.set_title("Monthly Revenue Trend (Delivered)"); save("03_monthly_trend.png")
fig, ax = plt.subplots(figsize=(10, 4.2)); mn = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
for y, col in zip(ms.columns, [PAL, "#E36414"]): ax.plot(range(1, 13), ms[y].values, marker="o", label=str(y), color=col)
ax.set_xticks(range(1, 13)); ax.set_xticklabels(mn); fmt(ax, "y"); ax.legend(); ax.set_title("Monthly Revenue: 2024 vs 2025"); save("04_yoy.png")
fig, ax = plt.subplots(1, 2, figsize=(11, 4)); q = T["Quarter"].sort_index(); ax[0].bar(q.index.astype(str), q.Sales, color=PAL); fmt(ax[0], "y"); ax[0].set_title("Revenue by Quarter"); ax[0].set_xlabel("Quarter")
pv = dl.groupby(["Year", "Quarter"]).Sales.sum().unstack(0); pv.plot(kind="bar", ax=ax[1], color=[PAL, "#E36414"]); fmt(ax[1], "y"); ax[1].set_title("Quarterly Revenue by Year"); ax[1].tick_params(axis="x", rotation=0); save("05_quarter.png")
fig, ax = plt.subplots(1, 2, figsize=(11, 4)); r = T["Region"]; sns.barplot(x=r.index, y=r.Sales, color=PAL, ax=ax[0]); fmt(ax[0], "y"); ax[0].set_title("Revenue by Region"); ax[0].set_xlabel("")
s = T["State"].sort_values("Profit", ascending=False).head(10).iloc[::-1]; ax[1].barh(s.index, s.Profit, color="#E36414"); fmt(ax[1]); ax[1].set_title("Top 10 States by Profit"); save("06_geo.png")
fig, ax = plt.subplots(1, 3, figsize=(14, 4)); ch = T["Sales_Channel"]; sns.barplot(x=ch.index, y=ch.Sales, color=PAL, ax=ax[0]); fmt(ax[0], "y"); ax[0].set_title("Revenue by Channel"); ax[0].set_xlabel("")
pm = df.Payment_Method.value_counts(); ax[1].pie(pm, labels=pm.index, autopct="%1.1f%%", startangle=90, colors=sns.color_palette("viridis", 5)); ax[1].set_title("Payment Methods (all orders)")
sh = df.Shipping_Type.value_counts(); ax[2].pie(sh, labels=sh.index, autopct="%1.1f%%", startangle=90, colors=sns.color_palette("viridis", 3)); ax[2].set_title("Shipping Types"); save("07_channel_payment_ship.png")
fig, ax = plt.subplots(1, 2, figsize=(11, 4)); sns.histplot(df.Age, bins=15, color=PAL, ax=ax[0]); ax[0].set_title("Customer Age Distribution")
g = df.Gender.value_counts(); ax[1].bar(g.index, g.values, color=PAL); ax[1].set_title("Orders by Gender"); [ax[1].bar_label(b) for b in ax[1].containers]; save("08_demographics.png")
fig, ax = plt.subplots(1, 2, figsize=(11, 4)); sns.scatterplot(data=df.sample(1200, random_state=1), x="Discount", y="Profit", alpha=.4, color=PAL, ax=ax[0]); ax[0].set_title("Discount vs Profit")
sns.boxplot(data=df, x="Disc_Band", y="Margin_Pct", color="#9FC5CE", ax=ax[1]); ax[1].set_title("Profit Margin % by Discount Band"); save("09_discount.png")
fig, ax = plt.subplots(figsize=(8, 6)); sns.heatmap(df[["Age", "Quantity", "Unit_Price", "Discount", "Sales", "Cost", "Profit", "Customer_Rating"]].corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax); ax.set_title("Correlation Heatmap"); save("10_corr.png")
fig, ax = plt.subplots(figsize=(9, 5)); sns.scatterplot(data=rfm, x="Recency", y="Frequency", hue="Segment", size="Monetary", sizes=(30, 400), alpha=.7, ax=ax); ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8); ax.set_title("RFM Customer Segmentation"); save("11_rfm.png")
fig, ax = plt.subplots(1, 2, figsize=(11, 4)); ax[0].pie(st, labels=st.index, autopct="%1.1f%%", startangle=90, colors=["#0F4C5C", "#E36414", "#9A031E"]); ax[0].set_title("Order Status")
rd = df.Customer_Rating.value_counts().sort_index(); ax[1].bar(rd.index.astype(int).astype(str), rd.values, color=PAL); ax[1].set_title("Customer Ratings (n=3,152)"); save("12_status_rating.png")
fig, ax = plt.subplots(1, 3, figsize=(14, 3.6)); sns.boxplot(y=df.Sales, ax=ax[0], color="#9FC5CE"); ax[0].set_title("Sales outliers"); sns.boxplot(y=df.Profit, ax=ax[1], color="#9FC5CE"); ax[1].set_title("Profit outliers"); sns.histplot(np.log10(df.Sales), bins=30, ax=ax[2], color=PAL); ax[2].set_title("log10(Sales) distribution"); save("13_outliers.png")

json.dump(M, open("metrics.json", "w"), indent=1, default=str)
rfm.to_csv("rfm_segments.csv", index=False); df.to_csv("cleaned_ecommerce_sales.csv", index=False)
print("done")
