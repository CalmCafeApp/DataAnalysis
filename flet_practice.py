import flet as ft

def main(page:ft.page):
    page.add(ft.SafeArea(ft.Text("Hello")))

ft.app(main)