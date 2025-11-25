const { chromium } = require('playwright');
const fs = require('fs');

// Volvemos a la URL original
const FIXTURES_URL = 'https://www.whoscored.com/regions/252/tournaments/2/seasons/10743/stages/24533/fixtures/england-premier-league-2025-2026';
const AUTH_FILE = 'auth_state.json';

async function launchAndSaveState() {
    console.log('Iniciando el navegador para configuración manual...');
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        await page.goto(FIXTURES_URL);
        console.log('\n------------------------------------------------------------------');
        console.log('¡ATENCIÓN! Tienes 60 segundos para actuar.');
        console.log('1. En la ventana del navegador, cierra el banner de cookies.');
        console.log('2. Cierra CUALQUIER otro pop-up o anuncio que aparezca.');
        console.log('3. Cuando la página esté limpia, simplemente espera.');
        console.log('   El navegador se cerrará solo y guardará la sesión.');
        console.log('------------------------------------------------------------------\n');

        // Esperar 60 segundos para que el usuario actúe
        await page.waitForTimeout(60000);

        console.log('Tiempo finalizado. Guardando estado de la sesión...');
        await context.storageState({ path: AUTH_FILE });
        console.log(`Estado guardado en: ${AUTH_FILE}`);

    } catch (error) {
        console.error('Ocurrió un error durante la configuración manual:', error.message);
    } finally {
        await browser.close();
        console.log('Navegador de configuración cerrado.');
    }
}

launchAndSaveState();