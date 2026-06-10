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
                # Chargement de la page
                await page.goto(url, timeout=30000)
                
                # Ciblage de la section Delve avec les 3 variantes d'ID possibles
                h2_delve = page.locator("#delve-talents, #delves, #delve-talent-builds").first
                
                if await h2_delve.count() > 0:
                    # Correction adaptative : on cherche le premier lien "Open in Calculator" suivant directement le H2
                    button = h2_delve.locator("xpath=following::a").filter(has_text="Open in Calculator").first
                    content = await button.get_attribute("href", timeout=5000)
                    
                    file_name = f"last_content_{spec.replace('/', '_')}.txt"
                    old_content = ""
                    
                    if os.path.exists(file_name):
                        with open(file_name, "r", encoding="utf-8") as f:
                            old_content = f.read()
                    
                    # Comparaison de l'URL du build
                    if content != old_content:
                        print(f"Changement détecté pour {spec} !")
                        if WEBHOOK_URL:
                            requests.post(WEBHOOK_URL, json={"content": f"MàJ Delves détectée : {spec} -> {url}"})
                        
                        with open(file_name, "w", encoding="utf-8") as f:
                            f.write(content)
                else:
                    print(f"Aucune section Delve trouvée pour {spec}, on passe...")
                    
            except Exception as e:
                print(f"Erreur sur {spec} : {e}")
                continue 
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_delves_update())