import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import re

# Load CSVs
product_df = pd.read_csv(r"C:\Users\ABHISHEK\Desktop\JavaScript\amazon_products.csv")
categories_df = pd.read_csv(r"C:\Users\ABHISHEK\Desktop\JavaScript\amazon_categories.csv")

# Clean column names
product_df.columns = product_df.columns.str.strip().str.lower()
categories_df.columns = categories_df.columns.str.strip().str.lower()

# Convert and clean columns
product_df['price'] = product_df['price'].replace(r'[\$,]', '', regex=True).astype(float)
product_df['listprice'] = product_df['listprice'].replace(r'[\$,]', '', regex=True).astype(float)
product_df['reviews'] = pd.to_numeric(product_df['reviews'], errors='coerce')
product_df['stars'] = pd.to_numeric(product_df['stars'], errors='coerce')
product_df['isbestseller'] = product_df['isbestseller'].astype(bool)
product_df['boughtinlastmonth'] = product_df['boughtinlastmonth'].astype(bool)

# Create dimension and fact tables
dim_categories = categories_df.rename(columns={
    'id': 'category_id',
    'category_name': 'category_name'
}).drop_duplicates()

dim_products = product_df[['asin', 'title', 'imgurl', 'producturl']].drop_duplicates()

fact_products = product_df[[ 
    'asin', 'price', 'listprice', 'stars', 'reviews',
    'isbestseller', 'boughtinlastmonth', 'category_id'
]]

# Export to CSV
dim_categories.to_csv('DimCategory.csv', index=False)
dim_products.to_csv('DimProduct.csv', index=False)
fact_products.to_csv('FactProduct.csv', index=False)

# Analysis
top_best_sellers = product_df[product_df['isbestseller']].sort_values(by='reviews', ascending=False).head(10)
top_rated = product_df[product_df['reviews'] > 50].sort_values(by='stars', ascending=False).head(10)

category_counts = product_df.groupby('category_id')['asin'].count().reset_index(name='product_count')
category_summary = category_counts.merge(dim_categories, on='category_id')

avg_price_by_category = product_df.groupby('category_id')['price'].mean().reset_index(name='avg_price')
avg_price_summary = avg_price_by_category.merge(dim_categories, on='category_id')

# Category label cleaning function
def clean_short_name(name, max_len=25):
    name = re.sub(r'[^\w\s&-]', '', name)  # remove special chars
    return name if len(name) <= max_len else name[:max_len].rstrip() + '...'

category_summary['short_name'] = category_summary['category_name'].apply(clean_short_name)
avg_price_summary['short_name'] = avg_price_summary['category_name'].apply(clean_short_name)

# Limit top N categories for cleaner charts
top_n = 20
category_summary_sorted = category_summary.sort_values(by='product_count', ascending=False).head(top_n)
avg_price_summary_sorted = avg_price_summary.sort_values(by='avg_price', ascending=False).head(top_n)

bought_last_month = product_df[product_df['boughtinlastmonth']]
bought_last_month_count = len(bought_last_month)

# Visualizations
fig_best_sellers = px.bar(
    top_best_sellers,
    x='title',
    y='reviews',
    title='Top 10 Best Sellers',
    labels={'title': 'Product Title', 'reviews': 'Review Count'},
)
fig_best_sellers.update_traces(marker_color='teal')

fig_top_rated = px.bar(
    top_rated,
    x='title',
    y='stars',
    title='Top 10 Top Rated Products (50+ Reviews)',
    labels={'title': 'Product Title', 'stars': 'Stars'},
)
fig_top_rated.update_traces(marker_color='indigo')

fig_category_summary = px.bar(
    category_summary_sorted,
    x='short_name',
    y='product_count',
    hover_data=['category_name'],
    title='Top Categories by Product Count',
    labels={'short_name': 'Category', 'product_count': 'Number of Products'},
)
fig_category_summary.update_layout(xaxis_tickangle=45)

fig_avg_price = px.bar(
    avg_price_summary_sorted,
    x='short_name',
    y='avg_price',
    hover_data=['category_name'],
    title='Average Price by Category',
    labels={'short_name': 'Category', 'avg_price': 'Average Price'},
)
fig_avg_price.update_layout(xaxis_tickangle=45)

# Dash App Layout
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Amazon Product Dashboard"

app.layout = dbc.Container([
    html.H1("Amazon Product Analytics Dashboard", className="text-center my-4"),

    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(figure=fig_best_sellers)), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(figure=fig_top_rated)), md=6),
    ]),

    dbc.Row([
        dbc.Col(dcc.Loading(dcc.Graph(figure=fig_category_summary)), md=6),
        dbc.Col(dcc.Loading(dcc.Graph(figure=fig_avg_price)), md=6),
    ]),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Products Bought Last Month", className="card-title"),
                html.H2(f"{bought_last_month_count}", className="card-text text-success")
            ])
        ], color="light", inverse=False), width=4)
    ], className="my-4 justify-content-center")
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
