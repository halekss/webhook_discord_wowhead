import asyncio
import os
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from config import CLASSES_SPECS
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

async def check_delves_update():
    async with async_playwright() as p:
        # CloudFront renvoie 403 au Chromium headless par défaut : on imite un vrai Chrome
        # (navigator.webdriver=false, user-agent, langue, fuseau, taille d'écran)
        browser = await p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            locale="fr-FR",
            timezone_id="Europe/Paris",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"},
        )
        page = await context.new_page()

        for item in CLASSES_SPECS:
            spec = item["spec"]
            role = item["role"]
            url = f"https://www.wowhead.com/guide/classes/{spec}/talent-builds-pve-{role}#delve-talents"
            print(f"Vérification de : {spec}...")
            
            try:
                # Chargement de la page (sans attendre pubs/trackers, trop lents sur certaines pages)
                response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                if not response.ok:
                    print(f"HTTP {response.status} sur {spec} (blocage ?), on passe...")
                    continue
                
                # Ciblage de la section Delve avec les 3 variantes d'ID possibles
                h2_delve = page.locator("#delve-talents, #delves, #delve-talent-builds").first
                # Le guide est rendu en JS : on laisse jusqu'à 15 s à la section pour apparaître
                try:
                    await h2_delve.wait_for(state="attached", timeout=15000)
                except PlaywrightTimeout:
                    pass

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