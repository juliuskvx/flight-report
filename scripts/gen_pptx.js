const PptxGenJS = require("pptxgenjs");
const fs = require("fs");

const fd = JSON.parse(fs.readFileSync('output/flight_data.json', 'utf8'));
const today = fd.reportDate;
const dayName = new Date(today).toLocaleDateString('en-GB', {weekday:'long',year:'numeric',month:'long',day:'numeric',timeZone:'UTC'});

fs.appendFileSync(process.env.GITHUB_ENV || '/dev/null', `REPORT_DATE=${today}\n`);

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_16x9';
pptx.title = 'European Airlines Intelligence Report ' + today;

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  navy:   '0D1F3C',  // dominant dark
  blue:   '1B3F6E',  // secondary
  mid:    '2474B5',  // mid blue
  accent: 'C9A84C',  // gold accent (#1 highlight)
  white:  'FFFFFF',
  offW:   'F8FAFC',
  slate:  '64748B',
  lgray:  'E2E8F0',
  text:   '1E293B',
  ice:    'D6E8FA',
};

const serif = 'Cambria';   // headers — personality
const sans  = 'Calibri';   // body — safe, reliable

// ── Helpers ──────────────────────────────────────────────────────────────────
function header(slide, title, sub) {
  slide.addShape(pptx.shapes.RECTANGLE, {x:0, y:0, w:10, h:0.8, fill:{color:C.navy}});
  slide.addText(title, {x:0.4, y:0.05, w:7, h:0.7, fontSize:22, bold:true, color:C.white, fontFace:serif, valign:'middle'});
  if (sub) slide.addText(sub, {x:7.2, y:0.05, w:2.6, h:0.7, fontSize:11, color:C.ice, fontFace:sans, valign:'middle', align:'right'});
  slide.addText('OpenSky ADS-B Sample · EuroAir Intel', {x:0, y:5.35, w:10, h:0.28, fontSize:9, color:C.slate, fontFace:sans, align:'center'});
}

function card(slide, x, y, w, h, col) {
  slide.addShape(pptx.shapes.RECTANGLE, {x, y, w, h, fill:{color:col||C.white}, shadow:{type:'outer', blur:4, offset:2, angle:45, color:'CBD5E1', opacity:0.3}});
}

// ── SLIDE 1: Title ────────────────────────────────────────────────────────────
const s1 = pptx.addSlide();
s1.background = {color:C.navy};

// Big diagonal accent block
s1.addShape(pptx.shapes.RECTANGLE, {x:6.2, y:0, w:3.8, h:5.625, fill:{color:C.blue}});
s1.addShape(pptx.shapes.RECTANGLE, {x:7.0, y:0, w:3.0, h:5.625, fill:{color:C.mid}});

// Gold top bar
s1.addShape(pptx.shapes.RECTANGLE, {x:0, y:0, w:6.5, h:0.06, fill:{color:C.accent}});

// Title text
s1.addText('EuroAir', {x:0.55, y:0.8, w:6, h:1.1, fontSize:58, bold:true, color:C.white, fontFace:serif});
s1.addText('Intel', {x:0.55, y:1.85, w:6, h:1.0, fontSize:58, bold:true, color:C.accent, fontFace:serif});
s1.addText('Daily Flight Activity Report', {x:0.55, y:3.0, w:5.8, h:0.5, fontSize:16, color:C.ice, fontFace:sans});
s1.addText(dayName, {x:0.55, y:3.6, w:5.8, h:0.4, fontSize:13, color:C.slate, fontFace:sans});

// Right side label
s1.addText('TOP 10\nEUROPEAN\nAIRLINES', {x:7.1, y:1.6, w:2.6, h:2.0, fontSize:20, bold:true, color:C.white, fontFace:serif, align:'center', lineSpacingMultiple:1.4});

// Bottom bar
s1.addShape(pptx.shapes.RECTANGLE, {x:0, y:5.15, w:10, h:0.475, fill:{color:C.blue}});
s1.addText('ADS-B FLIGHT ACTIVITY SAMPLE · OPENSKY NETWORK · GENERATED DAILY AT 10:00 VILNIUS TIME', {x:0.4, y:5.2, w:9, h:0.35, fontSize:10, color:C.ice, fontFace:sans, charSpacing:2});

// ── SLIDE 2: Key Metrics ──────────────────────────────────────────────────────
const s2 = pptx.addSlide();
s2.background = {color:C.offW};
header(s2, 'Key Metrics — Tracked Flight Activity', today);

const metrics = [
  {label:'Flights Tracked (Sample)', value: Number(fd.totalFlights24h).toLocaleString(),          unit:'ADS-B detections',  col:C.blue},
  {label:'Total Block Hours (Sample)',  value: Number(fd.totalFlightHours24h).toLocaleString(),       unit:'hours, tracked flights',    col:C.mid},
  {label:'Airlines Ranked',   value: String(fd.top10Airlines.length),                       unit:'carriers', col:C.accent},
  {label:'#1 by Activity',        value: fd.top10Airlines[0].airline,                           unit:'most tracked flights',col:C.navy},
];

metrics.forEach((m, i) => {
  const x = 0.3 + (i % 2) * 4.85;
  const y = 1.0 + Math.floor(i / 2) * 1.85;
  card(s2, x, y, 4.5, 1.55);
  s2.addShape(pptx.shapes.RECTANGLE, {x, y, w:4.5, h:0.06, fill:{color:m.col}});
  s2.addText(m.label, {x:x+0.2, y:y+0.2, w:4.1, h:0.3, fontSize:11, color:C.slate, fontFace:sans});
  s2.addText(m.value, {x:x+0.2, y:y+0.55, w:4.1, h:0.7, fontSize:m.value.length > 10 ? 18 : 28, bold:true, color:C.text, fontFace:serif});
  s2.addText(m.unit, {x:x+0.2, y:y+1.25, w:4.1, h:0.25, fontSize:10, color:C.slate, fontFace:sans});
});

// Route highlight box
s2.addShape(pptx.shapes.RECTANGLE, {x:0.3, y:4.55, w:9.4, h:0.65, fill:{color:C.navy}});
s2.addText(
  `✈  Longest tracked: ${fd.longestFlight.airline}  ${fd.longestFlight.route}  (${fd.longestFlight.hours}h)        ✈  Shortest tracked: ${fd.shortestFlight.airline}  ${fd.shortestFlight.route}  (${fd.shortestFlight.hours}h)`,
  {x:0.5, y:4.58, w:9.0, h:0.58, fontSize:11, color:C.ice, fontFace:sans, valign:'middle', align:'center'}
);

// ── SLIDE 3: Flight Count Bar Chart ──────────────────────────────────────────
const s3 = pptx.addSlide();
s3.background = {color:C.white};
header(s3, 'Top 10 Airlines by Tracked Flight Activity', today);
s3.addImage({path:'output/chart_flights.png', x:0.2, y:0.88, w:9.6, h:4.42});

// ── SLIDE 4: Market Share Pie ─────────────────────────────────────────────────
const s4 = pptx.addSlide();
s4.background = {color:C.offW};
header(s4, 'Relative Activity Share — Tracked Flight Volume', today);

s4.addImage({path:'output/chart_pie.png', x:0.1, y:0.88, w:5.5, h:4.42});

// Right side: top 5 ranked list
s4.addText('Rankings', {x:5.9, y:1.0, w:3.8, h:0.5, fontSize:16, bold:true, color:C.navy, fontFace:serif});
fd.top10Airlines.slice(0,5).forEach((a, i) => {
  const y = 1.6 + i * 0.72;
  const isFirst = i === 0;
  card(s4, 5.9, y, 3.8, 0.62, isFirst ? C.navy : C.white);
  s4.addText(`${a.rank}`, {x:6.0, y:y+0.08, w:0.4, h:0.45, fontSize:16, bold:true, color: isFirst ? C.accent : C.mid, fontFace:serif, align:'center'});
  s4.addText(a.airline, {x:6.45, y:y+0.08, w:2.4, h:0.25, fontSize:11, bold:true, color: isFirst ? C.white : C.text, fontFace:sans});
  s4.addText(`${Number(a.flightCount).toLocaleString()} tracked flights`, {x:6.45, y:y+0.33, w:2.4, h:0.22, fontSize:9, color: isFirst ? C.ice : C.slate, fontFace:sans});
});

// ── SLIDE 5: Block Hours Chart ────────────────────────────────────────────────
const s5 = pptx.addSlide();
s5.background = {color:C.white};
header(s5, 'Total Tracked Block Hours by Airline', today);
s5.addImage({path:'output/chart_hours.png', x:0.2, y:0.88, w:9.6, h:4.42});

// ── SLIDE 6: Full Data Table ──────────────────────────────────────────────────
const s6 = pptx.addSlide();
s6.background = {color:C.white};
header(s6, 'Full Activity Breakdown (Tracked Sample)', today);

const hOpts = {bold:true, color:C.white, fill:{color:C.navy}, fontSize:10, fontFace:sans, align:'center'};
const tRows = [
  ['#','Airline','Tracked Flights','Block Hrs','Longest Route','Shortest Route'].map(h=>({text:h, options:hOpts})),
  ...fd.top10Airlines.map((a, i) => {
    const isFirst = i === 0;
    const bg = isFirst ? 'FFF8E7' : (i % 2 === 0 ? C.white : C.offW);
    return [
      String(a.rank), a.airline,
      Number(a.flightCount).toLocaleString(),
      Number(a.totalFlightHours).toLocaleString()+'h',
      a.longestRoute, a.shortestRoute
    ].map((v, ci) => ({
      text: v,
      options: {
        color: isFirst && ci===0 ? C.accent : C.text,
        fill: {color: bg},
        fontSize: 9.5,
        fontFace: sans,
        bold: isFirst,
        align: ci >= 2 && ci <= 3 ? 'center' : 'left'
      }
    }));
  })
];

s6.addTable(tRows, {
  x:0.2, y:0.88, w:9.6, h:4.18,
  border:{pt:0.5, color:C.lgray},
  colW:[0.4, 1.7, 0.95, 0.85, 2.9, 2.7]
});

s6.addText('Tracked flights represent an ADS-B sample (~10–15% of actual European air traffic). Rankings and trends are directionally reliable; absolute counts are not total flight volumes.', {x:0.2, y:5.08, w:9.6, h:0.28, fontSize:8, italic:true, color:C.slate, fontFace:sans, align:'center'});

// ── SLIDE 7: Route Spotlight ──────────────────────────────────────────────────
const s7 = pptx.addSlide();
s7.background = {color:C.navy};
header(s7, 'Route Spotlight (Tracked Sample)', today);

// Longest
card(s7, 0.3, 0.95, 9.4, 2.05, C.blue);
s7.addText('LONGEST TRACKED ROUTE OF THE DAY', {x:0.55, y:1.05, w:8.8, h:0.35, fontSize:10, color:C.accent, fontFace:sans, charSpacing:2, bold:true});
s7.addText(fd.longestFlight.route, {x:0.55, y:1.42, w:8.8, h:0.75, fontSize:34, bold:true, color:C.white, fontFace:serif});
s7.addText(`${fd.longestFlight.airline}   ·   ${fd.longestFlight.hours} hours in the air (ADS-B estimate)`, {x:0.55, y:2.18, w:8.8, h:0.35, fontSize:13, color:C.ice, fontFace:sans});

// Shortest
card(s7, 0.3, 3.2, 9.4, 2.05, C.mid);
s7.addText('SHORTEST TRACKED ROUTE OF THE DAY', {x:0.55, y:3.3, w:8.8, h:0.35, fontSize:10, color:C.navy, fontFace:sans, charSpacing:2, bold:true});
s7.addText(fd.shortestFlight.route, {x:0.55, y:3.67, w:8.8, h:0.75, fontSize:34, bold:true, color:C.white, fontFace:serif});
s7.addText(`${fd.shortestFlight.airline}   ·   ${fd.shortestFlight.hours} hours in the air (ADS-B estimate)`, {x:0.55, y:4.43, w:8.8, h:0.35, fontSize:13, color:C.white, fontFace:sans});

// ── SLIDE 8: Airline Profiles (top 5 cards) ───────────────────────────────────
const s8 = pptx.addSlide();
s8.background = {color:C.offW};
header(s8, 'Top 5 Airline Profiles (Tracked Sample)', today);

fd.top10Airlines.slice(0,5).forEach((a, i) => {
  const x = 0.2 + (i % 5) * 1.94;
  const isFirst = i === 0;
  card(s8, x, 0.95, 1.82, 4.3, isFirst ? C.navy : C.white);
  // Rank badge
  s8.addShape(pptx.shapes.RECTANGLE, {x:x+0.65, y:1.05, w:0.52, h:0.52, fill:{color: isFirst ? C.accent : C.mid}});
  s8.addText(`#${a.rank}`, {x:x+0.65, y:1.05, w:0.52, h:0.52, fontSize:16, bold:true, color:C.white, fontFace:serif, align:'center', valign:'middle'});
  // Airline name
  s8.addText(a.airline, {x:x+0.08, y:1.68, w:1.66, h:0.55, fontSize:11, bold:true, color: isFirst ? C.white : C.navy, fontFace:serif, align:'center', wrap:true});
  // Stats
  s8.addText('Tracked Flights', {x:x+0.08, y:2.35, w:1.66, h:0.25, fontSize:9, color: isFirst ? C.ice : C.slate, fontFace:sans, align:'center'});
  s8.addText(Number(a.flightCount).toLocaleString(), {x:x+0.08, y:2.6, w:1.66, h:0.45, fontSize:22, bold:true, color: isFirst ? C.accent : C.mid, fontFace:serif, align:'center'});
  s8.addText('Block Hours', {x:x+0.08, y:3.1, w:1.66, h:0.25, fontSize:9, color: isFirst ? C.ice : C.slate, fontFace:sans, align:'center'});
  s8.addText(Number(a.totalFlightHours).toLocaleString()+'h', {x:x+0.08, y:3.35, w:1.66, h:0.4, fontSize:17, bold:true, color: isFirst ? C.white : C.text, fontFace:serif, align:'center'});
  s8.addText(a.longestRoute, {x:x+0.08, y:3.85, w:1.66, h:0.3, fontSize:9, color: isFirst ? C.ice : C.slate, fontFace:sans, align:'center'});
  s8.addText('top tracked route', {x:x+0.08, y:4.15, w:1.66, h:0.22, fontSize:8, color: isFirst ? C.accent : C.mid, fontFace:sans, align:'center'});
});

// ── SLIDE 9: Summary / Back Cover ────────────────────────────────────────────
const s9 = pptx.addSlide();
s9.background = {color:C.navy};

s9.addShape(pptx.shapes.RECTANGLE, {x:0, y:0, w:4, h:5.625, fill:{color:C.blue}});
s9.addShape(pptx.shapes.RECTANGLE, {x:0, y:0, w:0.08, h:5.625, fill:{color:C.accent}});

s9.addText('Summary', {x:0.25, y:0.6, w:3.5, h:0.7, fontSize:28, bold:true, color:C.white, fontFace:serif});
s9.addText(dayName, {x:0.25, y:1.35, w:3.5, h:0.35, fontSize:10, color:C.ice, fontFace:sans});

const summaryItems = [
  ['Flights tracked', Number(fd.totalFlights24h).toLocaleString()],
  ['Total block hours', Number(fd.totalFlightHours24h).toLocaleString()+'h'],
  ['#1 by activity', fd.top10Airlines[0].airline],
  ['#1 tracked flights', Number(fd.top10Airlines[0].flightCount).toLocaleString()],
  ['Longest tracked route', fd.longestFlight.route+' ('+fd.longestFlight.hours+'h)'],
  ['Shortest tracked route', fd.shortestFlight.route+' ('+fd.shortestFlight.hours+'h)'],
];

summaryItems.forEach(([label, val], i) => {
  const y = 1.9 + i * 0.52;
  s9.addText(label, {x:0.3, y, w:1.7, h:0.35, fontSize:10, color:C.ice, fontFace:sans});
  s9.addText(val, {x:2.05, y, w:1.75, h:0.35, fontSize:10, bold:true, color:C.accent, fontFace:sans});
});

// Right side — big closing statement
s9.addText('European\nAirlines\nActivity', {x:4.3, y:1.2, w:5.4, h:2.4, fontSize:38, bold:true, color:C.white, fontFace:serif, lineSpacingMultiple:1.3});
s9.addText('Daily briefing based on an ADS-B sample of European flight activity (OpenSky Network, ~10-15% of actual traffic). Figures support relative ranking and trend analysis, not total flight volumes.', {x:4.3, y:3.8, w:5.4, h:0.9, fontSize:11, color:C.ice, fontFace:sans, lineSpacingMultiple:1.3});
s9.addShape(pptx.shapes.RECTANGLE, {x:4.3, y:4.75, w:5.4, h:0.06, fill:{color:C.accent}});
s9.addText('EuroAir Intel · Generated daily at 10:00 Vilnius Time', {x:4.3, y:4.85, w:5.4, h:0.3, fontSize:10, color:C.slate, fontFace:sans});

// ── Write file ────────────────────────────────────────────────────────────────
fs.mkdirSync('output', {recursive:true});
const fname = `output/European_Airlines_Report_${today}.pptx`;
pptx.writeFile({fileName: fname})
  .then(() => console.log('DONE: ' + fname))
  .catch(e => { console.error('ERROR: ' + e.message); process.exit(1); });
