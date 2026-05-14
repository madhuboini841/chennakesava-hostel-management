const puppeteer = require('puppeteer');

(async () => {
    try {
        const browser = await puppeteer.launch({ headless: 'new' });
        const page = await browser.newPage();
        
        page.on('console', msg => {
            console.log(`[CONSOLE ${msg.type()}] ${msg.text()}`);
        });
        
        page.on('pageerror', err => {
            console.log(`[PAGE ERROR] ${err.toString()}`);
        });

        console.log("Attempting to log into React App...");
        await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' });
        await page.type('input[type="email"]', 'student@hostel.com');
        await page.type('input[type="password"]', 'student123');
        await page.click('button');
        
        await new Promise(r => setTimeout(r, 4000));
        
        console.log("Checking React App Dashboard DOM...");
        const html = await page.content();
        if (html.includes('StudentLayout')) {
             console.log("Layout exists in code.");
        }
        
        const mainContent = await page.$eval('main', el => el.innerHTML).catch(() => "NO MAIN TAG");
        console.log("MAIN CONTENT:", mainContent.substring(0, 500));

        await browser.close();
    } catch (e) {
        console.error("Puppeteer script failed:", e);
    }
})();
