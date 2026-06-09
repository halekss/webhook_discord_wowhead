import asyncio
import os
import requests
from playwright.async_api import async_playwright
from config import CLASSES_SPECS
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

async def check_delves_update():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        for item in CLASSES_SPECS:
            spec = item["spec"]
            role = item["role"]
            url = f"https://www.wowhead.com/guide/classes/{spec}/talent-builds-pve-{role}#delve-talents"
            print(f"Vérification de : {spec}...")
            
            try:
                await page.goto(url, timeout=30000)
                # On attend l'élément avec un timeout court
                h2_delve = page.locator("h2:has-text('Delve')")

                # On récupère le conteneur associé
                # On utilise 'locator' pour naviguer dans le DOM
                # Si le h2 est juste avant le div tabpanel, on peut tenter de le localiser dynamiquement
                content = await h2_delve.locator("xpath=following::div[@role='tabpanel'][1]").inner_text()
                
                file_name = f"last_content_{spec.replace('/', '_')}.txt"
                
                old_content = ""
                if os.path.exists(file_name):
                    with open(file_name, "r", encoding="utf-8") as f:
                        old_content = f.read()
                
                if content != old_content:
                    print(f"Changement détecté pour {spec} !")
                    if WEBHOOK_URL:
                        requests.post(WEBHOOK_URL, json={"content": f"MàJ Delves détectée : {spec} -> {url}"})
                    
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(content)
                        
            except Exception as e:
                print(f"Erreur sur {spec} : {e}")
                continue # Passe à la classe suivante même en cas d'erreur
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_delves_update())