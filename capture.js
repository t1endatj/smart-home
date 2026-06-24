const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 900, deviceScaleFactor: 2 });
  await page.goto('file://' + __dirname + '/diagram.html');
  await page.screenshot({ path: 'So_Do_Kien_Truc_4_Lop_Vuong.png', fullPage: true });
  await browser.close();
})();
