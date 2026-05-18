from playwright.sync_api import sync_playwright

URL = 'https://www.olx.com.br/autos-e-pecas/motos/estado-sp/sao-paulo-e-regiao'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(10000)
    cards = page.locator('section.olx-adcard')
    print('cards section.olx-adcard count=', cards.count())
    if cards.count() > 0:
        card = cards.nth(0)
        imgs = card.locator('img')
        print('img count', imgs.count())
        for j in range(min(20, imgs.count())):
            im = imgs.nth(j)
            print(j, im.get_attribute('src'), im.get_attribute('data-src'), im.get_attribute('srcset'))
    else:
        alt = page.locator('article, div').first
        print('first element tag', alt)
    browser.close()
