
const { chromium } = require('playwright');
const fs = require('fs');

const FIXTURES_URL = 'https://www.whoscored.com/regions/252/tournaments/2/seasons/10743/stages/24533/fixtures/england-premier-league-2025-2026';
const AUTH_FILE = 'auth_state.json';

async function scrapeWhoScored() {
    if (!fs.existsSync(AUTH_FILE)) {
        console.error(`Error: El archivo de estado '${AUTH_FILE}' no fue encontrado.`);
        console.error("Por favor, ejecuta primero el script 'launch_browser.js' para generarlo.");
        return;
    }

    console.log(`Iniciando scraping usando el estado de '${AUTH_FILE}'`);
    const browser = await chromium.launch({ headless: false }); // headless: false como último intento
    const context = await browser.newContext({ storageState: AUTH_FILE }); // Cargar el estado guardado
    const page = await context.newPage();

    try {
        // Ir a la página y proceder directamente al scraping
        await page.goto(FIXTURES_URL, { waitUntil: 'networkidle' });

        const matches = await getMatchFixtures(page);
        console.log(`\nSe encontraron ${matches.length} partidos. Empezando a extraer estadísticas...`);

        const allMatchData = [];
        for (let i = 0; i < matches.length; i++) {
            const match = matches[i];
            console.log(`Procesando partido ${i + 1}/${matches.length}: ${match.homeTeam} vs ${match.awayTeam}`);
            try {
                const stats = await getMatchStats(page, match.link);
                allMatchData.push({ ...match, ...stats });
            } catch (error) {
                console.error(`  [!] Error al procesar el partido ${match.link}:`, error.message);
                allMatchData.push({ ...match, error: 'No se pudieron obtener las estadísticas.' });
            }
        }

        fs.writeFileSync('whoscored_data.json', JSON.stringify(allMatchData, null, 2));
        console.log('\nDatos guardados exitosamente en "whoscored_data.json"');

    } catch (error) {
        console.error('\n[!] Ocurrió un error general en el script:', error);
        await page.screenshot({ path: 'scraping_error_screenshot.png' });
        console.log('Se ha guardado una captura de pantalla del error en "scraping_error_screenshot.png"');
    } finally {
        await browser.close();
        console.log('Proceso de scraping finalizado.');
    }
}

async function getMatchFixtures(page) {
    console.log('- Esperando a que la tabla de partidos sea visible...');
    await page.waitForSelector('#live-match-table', { state: 'visible', timeout: 30000 });
    console.log('- Tabla de partidos encontrada.');

    await autoScroll(page);

    const matchRows = await page.locator('#live-match-table .divtable-body .divtable-row').all();
    const fixtures = [];
    let currentDate = 'Fecha no encontrada';

    for (const row of matchRows) {
        const isDateHeader = (await row.getAttribute('class')).includes('divtable-header');
        if (isDateHeader) {
            currentDate = await row.locator('.rowgroupheader-text').innerText();
        } else {
            try {
                const time = await row.locator('.time').innerText();
                const homeTeam = await row.locator('.home .team-name').innerText();
                const awayTeam = await row.locator('.away .team-name').innerText();
                const result = await row.locator('.result').innerText();
                const linkElement = await row.locator('a[href*="/Matches/"]').first();
                const relativeLink = await linkElement.getAttribute('href');
                const matchLink = `https://www.whoscored.com${relativeLink.replace('Live', 'Show')}`;

                fixtures.push({
                    date: currentDate.split(', ')[1] || currentDate,
                    time,
                    homeTeam,
                    awayTeam,
                    score: result.includes(':') ? result : 'No jugado',
                    link: matchLink,
                });
            } catch (err) {}
        }
    }
    return fixtures;
}

async function getMatchStats(page, matchUrl) {
    await page.goto(matchUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#match-centre-stats', { state: 'visible', timeout: 20000 });
    const stats = {};
    try {
        const possessionHome = await page.locator('.match-centre-stat-possession .home .stat-value').innerText();
        const possessionAway = await page.locator('.match-centre-stat-possession .away .stat-value').innerText();
        stats.possession = { home: possessionHome, away: possessionAway };
    } catch (e) {
        stats.possession = { home: 'N/A', away: 'N/A' };
    }
    const statRows = await page.locator('#live-match-data-options-container .stat-group-level .stat-value-wrapper').all();
    for(const row of statRows) {
        try {
            const statName = await row.locator('.stat-name').innerText();
            const homeValue = await row.locator('.home .stat-value').innerText();
            const awayValue = await row.locator('.away .stat-value').innerText();
            const cleanStatName = statName.replace(/\s+/g, '_').toLowerCase();
            stats[cleanStatName] = { home: homeValue, away: awayValue };
        } catch(e) {}
    }
    return { stats };
}

async function autoScroll(page) {
    console.log('- Haciendo scroll para cargar todos los partidos...');
    await page.evaluate(async () => {
        await new Promise((resolve) => {
            let totalHeight = 0;
            const distance = 100;
            const timer = setInterval(() => {
                const scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;
                if (totalHeight >= scrollHeight) {
                    clearInterval(timer);
                    resolve();
                }
            }, 100);
        });
    });
    console.log('- Scroll finalizado.');
}

scrapeWhoScored();
