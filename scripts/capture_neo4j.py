import os
import time
from playwright.sync_api import sync_playwright

def main():
    os.makedirs("report/img", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 950})
        page = context.new_page()

        print("Navigating to Neo4j Browser...")
        page.goto("http://localhost:7474/browser/")
        page.wait_for_timeout(3000)

        # Check if connect modal is visible
        pw_input = page.locator('input[type="password"]')
        if pw_input.is_visible():
            print("Connecting to Neo4j...")
            pw_input.fill("password123")
            connect_btn = page.locator('[data-testid="connection-form-submit"]')
            connect_btn.click()
            page.wait_for_timeout(5000)

        # Dismiss tooltip / guided tour popup
        dismiss_btn = page.locator('button:has-text("Dismiss")')
        if dismiss_btn.count() > 0 and dismiss_btn.first.is_visible():
            print("Dismissing guided tour...")
            dismiss_btn.first.click()
            page.wait_for_timeout(1000)

        # Collapse left sidebar if open
        sidebar_collapse = page.locator('button[aria-label*="collapse" i], button[title*="collapse" i], button[data-testid*="sidebar-toggle"]')
        if sidebar_collapse.count() > 0 and sidebar_collapse.first.is_visible():
            sidebar_collapse.first.click()
            page.wait_for_timeout(500)

        def run_query(query: str):
            print(f"Running query: {query}")
            editor = page.locator('.view-lines, .monaco-editor, [data-testid="cypher-editor"], textarea.inputarea, .cm-editor')
            if editor.count() > 0:
                editor.first.click()
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            # Using insert_text to avoid encoding / character issues with Vietnamese accents
            page.keyboard.insert_text(query)
            page.wait_for_timeout(500)
            page.keyboard.press("Control+Enter")
            page.wait_for_timeout(4000)

            # Ensure dismiss is clicked if it appeared again
            if dismiss_btn.count() > 0 and dismiss_btn.first.is_visible():
                dismiss_btn.first.click()
                page.wait_for_timeout(500)

        # Clear any initial frames
        run_query(":clear")
        page.wait_for_timeout(1000)

        # 1. Q-A: Count nodes
        print("Capturing kg_count.png...")
        run_query("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;")
        page.wait_for_timeout(2000)
        table_btn = page.locator('button[title*="table" i], button:has-text("Table"), [data-testid*="table"]')
        if table_btn.count() > 0 and table_btn.first.is_visible():
            table_btn.first.click()
            page.wait_for_timeout(1000)
        page.screenshot(path="report/img/kg_count.png")
        print("Saved report/img/kg_count.png")

        # 2. Q-B: Cross KB bridge
        print("Capturing kg_cross_kb.png...")
        run_query(":clear")
        page.wait_for_timeout(1000)
        run_query("MATCH p=(:Person)-[:INVOLVED_IN]->(:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article) RETURN p LIMIT 25;")
        page.wait_for_timeout(3000)
        graph_btn = page.locator('button[title*="graph" i], button:has-text("Graph"), [data-testid*="graph"]')
        if graph_btn.count() > 0 and graph_btn.first.is_visible():
            graph_btn.first.click()
            page.wait_for_timeout(1000)
        page.screenshot(path="report/img/kg_cross_kb.png")
        print("Saved report/img/kg_cross_kb.png")

        # 3. Q-D: My case (Cái Quang Huy)
        print("Capturing kg_my_case.png...")
        run_query(":clear")
        page.wait_for_timeout(1000)
        run_query("MATCH p=(:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article) OPTIONAL MATCH q=(k)-[:INVOLVES|LOCATED_IN]->() RETURN p, q;")
        page.wait_for_timeout(3000)
        if graph_btn.count() > 0 and graph_btn.first.is_visible():
            graph_btn.first.click()
            page.wait_for_timeout(1000)
        page.screenshot(path="report/img/kg_my_case.png")
        print("Saved report/img/kg_my_case.png")

        browser.close()
        print("All screenshots captured cleanly!")

if __name__ == "__main__":
    main()
