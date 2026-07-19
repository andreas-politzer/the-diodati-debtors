import reflex as rx

config = rx.Config(
    app_name="diodati_debtors",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)