const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');
const { ditherImage, replaceColors } = require('epdoptimize');

async function procesar() {
    const inputPath = process.argv[2];
    let jsonPath = process.argv[3] || 'job_bwr_foto.json';

    if (!inputPath || !fs.existsSync(inputPath)) {
        console.error("\n[ERROR] Archivo de origen no encontrado.");
        process.exit(1);
    }

    const dirName = path.dirname(inputPath);
    const ext = path.extname(inputPath);
    const baseName = path.basename(inputPath, ext);

    // Tu regla estricta de nomenclatura:
    const outputPath = path.join(dirName, `${baseName}_obsv.png`);

    console.log(`\n[*] Procesando: ${baseName}${ext}`);

    const jobConfig = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    const img = await loadImage(inputPath);
    
    const canvasOriginal = createCanvas(img.width, img.height);
    const ctxOriginal = canvasOriginal.getContext('2d');
    ctxOriginal.drawImage(img, 0, 0);

    const canvasDestino = createCanvas(img.width, img.height);

    await ditherImage(canvasOriginal, canvasDestino, {
        palette: jobConfig.palette,
        ...jobConfig.epdOptions
    });

    replaceColors(canvasDestino, canvasDestino, jobConfig.palette);

    fs.writeFileSync(outputPath, canvasDestino.toBuffer('image/png'));

    console.log(`[OK] Observable generado: ${outputPath}\n`);
}

procesar().catch(err => console.error(err));