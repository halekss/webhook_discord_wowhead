import asyncio
import os
import requests
from playwright.async_api import async_playwright
from config import CLASSES_SPECS
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# Logique d'interception : on bloque tout ce qui n'est pas du texte/HTML
async def route_intercept(route):
    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
        await route.abort()
    else:
        await route.continue_()

async def check_delves_update():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # Application de l'intercepteur à toutes les requêtes réseau de la page
        await page.route("**/*", route_intercept)

        for item in CLASSES_SPECS:
            spec = item["spec"]
            role = item["role"]
            url = f"https://www.wowhead.com/guide/classes/{spec}/talent-builds-pve-{role}#delve-talents"
            print(f"Vérification de : {spec}...")
            
            try:
                # On demande explicitement à s'arrêter au chargement du DOM (le squelette)
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                
                h2_delve = page.locator("h2:has-text('Delve')")
                
                if await h2_delve.count() > 0:
                    content = await h2_delve.locator("xpath=following::div[@role='tabpanel'][1]").inner_text(timeout=5000)
                    
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
                else:
                    print(f"Aucune section Delve trouvée pour {spec}, on passe...")
                    
            except Exception as e:
                print(f"Erreur sur {spec} : {e}")
                continue 
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_delves_update())