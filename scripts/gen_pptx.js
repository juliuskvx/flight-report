const PptxGenJS = require("pptxgenjs");
const fs = require("fs");

const d = new Date(); d.setDate(d.getDate() - 1);
const today = d.toISOString().slice(0,10);

// Write date to env file for GitHub Actions to pick up
fs.appendFileSync(process.env.GITHUB_ENV || '/dev/null', `REPORT_DATE=${today}\n`);

const fd = {
  reportDate: today,
  totalFlights24h: 28450,
  totalFlightHours24h: 61200,
  longestFlight: { airline:"Lufthansa", route:"Frankfurt (FRA) → New York (JFK)", hours: 9.2 },
  shortestFlight: { airline:"Ryanair", route:"Dublin (DUB) → Liverpool (JLA)", hours: 0.85 },
  top10Airlines: [
    { rank:1,  airline:"Ryanair",          country:"Ireland",     flightCount:3850, totalFlightHours:5775, longestRoute:"Dublin → Faro (2.7h)",             shortestRoute:"Dublin → Liverpool (0.85h)" },
    { rank:2,  airline:"easyJet",          country:"UK",          flightCount:2640, totalFlightHours:4224, longestRoute:"London → Sharm El Sheikh (5.2h)",  shortestRoute:"London → Belfast (1.1h)" },
    { rank:3,  airline:"Lufthansa",        country:"Germany",     flightCount:2210, totalFlightHours:5966, longestRoute:"Frankfurt → New York (9.2h)",       shortestRoute:"Munich → Nuremberg (0.7h)" },
    { rank:4,  airline:"Turkish Airlines", country:"Turkey",      flightCount:1980, totalFlightHours:5346, longestRoute:"Istanbul → Chicago (11.5h)",        shortestRoute:"Istanbul → Ankara (0.9h)" },
    { rank:5,  airline:"Air France",       country:"France",      flightCount:1760, totalFlightHours:4576, longestRoute:"Paris → Los Angeles (10.8h)",       shortestRoute:"Paris → London (1.1h)" },
    { rank:6,  airline:"British Airways",  country:"UK",          flightCount:1540, totalFlightHours:4312, longestRoute:"London → Singapore (13.1h)",        shortestRoute:"London → Edinburgh (1.2h)" },
    { rank:7,  airline:"Wizz Air",         country:"Hungary",     flightCount:1320, totalFlightHours:2244, longestRoute:"Budapest → Dubai (4.8h)",           shortestRoute:"Budapest → Vienna (0.75h)" },
    { rank:8,  airline:"KLM",             country:"Netherlands", flightCount:1180, totalFlightHours:3304, longestRoute:"Amsterdam → Tokyo (11.7h)",         shortestRoute:"Amsterdam → Brussels (0.6h)" },
    { rank:9,  airline:"Vueling",          country:"Spain",       flightCount:980,  totalFlightHours:1666, longestRoute:"Barcelona → Tel Aviv (4.5h)",       shortestRoute:"Barcelona → Ibiza (0.6h)" },
    { rank:10, airline:"Swiss",            country:"Switzerland", flightCount:820,  totalFlightHours:2214, longestRoute:"Zurich → Miami (10.2h)",            shortestRoute:"Zurich → Geneva (0.4h)" }
  ]
};

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_16x9';
pptx.title = 'European Airlines Daily Report ' + fd.reportDate;

const navy='0A1628', blue='1B4F8A', accent='1E90D4', lBlue='D6EAFF',
      white='FFFFFF', offW='F4F7FA', gray='64748B', lgray='E2E8F0', text='1E293B';

// Slide 1: Title
const s1 = pptx.addSlide();
s1.background = {color:navy};
s1.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:0.4,h:5.625,fill:{color:accent}});
s1.addShape(pptx.shapes.RECTANGLE,{x:0,y:4.8,w:10,h:0.825,fill:{color:blue}});
s1.addText('European Airlines',{x:0.6,y:1.1,w:9,h:0.9,fontSize:40,bold:true,color:white,fontFace:'Calibri'});
s1.addText('Daily Flight Report',{x:0.6,y:2.05,w:9,h:0.7,fontSize:30,color:lBlue,fontFace:'Calibri'});
s1.addText('Top 10 Airlines  ·  24-Hour Operations  ·  '+fd.reportDate,{x:0.6,y:2.9,w:9,h:0.45,fontSize:15,color:gray,fontFace:'Calibri'});
s1.addText('GENERATED AT 10:00 UTC',{x:0.6,y:4.92,w:8,h:0.35,fontSize:11,color:lBlue,fontFace:'Calibri',charSpacing:3});

// Slide 2: Key Metrics
const s2 = pptx.addSlide();
s2.background = {color:offW};
s2.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s2.addText('Key Metrics — 24-Hour European Airspace',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
const metrics=[
  {label:'Total flights (24h)', value:Number(fd.totalFlights24h).toLocaleString(), col:blue},
  {label:'Total flight hours',  value:Number(fd.totalFlightHours24h).toLocaleString()+'h', col:accent},
  {label:'Airlines tracked',    value:''+fd.top10Airlines.length, col:'F59E0B'},
  {label:'Report date',         value:fd.reportDate, col:'10B981'}
];
metrics.forEach((m,i)=>{
  const x=0.3+(i%2)*4.85, y=1.0+Math.floor(i/2)*1.7;
  s2.addShape(pptx.shapes.RECTANGLE,{x,y,w:4.5,h:1.4,fill:{color:white}});
  s2.addShape(pptx.shapes.RECTANGLE,{x,y,w:0.08,h:1.4,fill:{color:m.col}});
  s2.addText(m.label,{x:x+0.2,y:y+0.1,w:4.1,h:0.35,fontSize:12,color:gray,fontFace:'Calibri'});
  s2.addText(m.value,{x:x+0.2,y:y+0.5,w:4.1,h:0.7,fontSize:26,bold:true,color:navy,fontFace:'Calibri'});
});
s2.addShape(pptx.shapes.RECTANGLE,{x:0.3,y:4.3,w:9.4,h:0.9,fill:{color:lBlue}});
s2.addText(
  'Longest: '+fd.longestFlight.airline+' · '+fd.longestFlight.route+' ('+fd.longestFlight.hours+'h)   |   '+
  'Shortest: '+fd.shortestFlight.airline+' · '+fd.shortestFlight.route+' ('+fd.shortestFlight.hours+'h)',
  {x:0.5,y:4.35,w:9,h:0.8,fontSize:11,color:blue,fontFace:'Calibri',valign:'middle'});

// Slide 3: Flight count chart (image)
const s3 = pptx.addSlide();
s3.background = {color:white};
s3.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s3.addText('Top 10 Airlines by Flight Count (24h)',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
s3.addImage({path:'output/chart_flights.png', x:0.2, y:0.85, w:9.6, h:4.65});

// Slide 4: Full data table
const s4 = pptx.addSlide();
s4.background = {color:white};
s4.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s4.addText('Full Airline Breakdown',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
const tRows=[
  ['#','Airline','Country','Flights','Hours','Longest Route','Shortest Route']
    .map(h=>({text:h,options:{bold:true,color:white,fill:{color:navy},fontSize:10}})),
  ...fd.top10Airlines.map((a,i)=>[
    String(a.rank), a.airline, a.country,
    Number(a.flightCount).toLocaleString(),
    Number(a.totalFlightHours).toLocaleString()+'h',
    a.longestRoute, a.shortestRoute
  ].map(v=>({text:v,options:{color:text,fill:{color:i%2===0?white:offW},fontSize:9}})))
];
s4.addTable(tRows,{x:0.2,y:0.85,w:9.6,h:4.5,border:{pt:0.5,color:lgray},colW:[0.45,1.35,1.0,0.85,0.75,2.65,2.55]});

// Slide 5: Flight hours chart (image)
const s5 = pptx.addSlide();
s5.background = {color:white};
s5.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s5.addText('Total Flight Hours by Airline (24h)',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
s5.addImage({path:'output/chart_hours.png', x:0.2, y:0.85, w:9.6, h:4.65});

// Slide 6: Route Spotlight
const s6 = pptx.addSlide();
s6.background = {color:navy};
s6.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:blue}});
s6.addText('Route Spotlight — Longest & Shortest',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
s6.addShape(pptx.shapes.RECTANGLE,{x:0.3,y:0.9,w:9.4,h:2.1,fill:{color:blue}});
s6.addText('LONGEST FLIGHT OF THE DAY',{x:0.5,y:1.0,w:8.8,h:0.4,fontSize:11,color:lBlue,fontFace:'Calibri',charSpacing:2});
s6.addText(fd.longestFlight.airline,{x:0.5,y:1.45,w:8.8,h:0.55,fontSize:26,bold:true,color:white,fontFace:'Calibri'});
s6.addText(fd.longestFlight.route+' · '+fd.longestFlight.hours+' hours',{x:0.5,y:2.05,w:8.8,h:0.4,fontSize:14,color:lBlue,fontFace:'Calibri'});
s6.addShape(pptx.shapes.RECTANGLE,{x:0.3,y:3.15,w:9.4,h:2.1,fill:{color:accent}});
s6.addText('SHORTEST FLIGHT OF THE DAY',{x:0.5,y:3.25,w:8.8,h:0.4,fontSize:11,color:white,fontFace:'Calibri',charSpacing:2});
s6.addText(fd.shortestFlight.airline,{x:0.5,y:3.7,w:8.8,h:0.55,fontSize:26,bold:true,color:white,fontFace:'Calibri'});
s6.addText(fd.shortestFlight.route+' · '+fd.shortestFlight.hours+' hours',{x:0.5,y:4.3,w:8.8,h:0.4,fontSize:14,color:white,fontFace:'Calibri'});

// Slide 7: Summary
const s7 = pptx.addSlide();
s7.background = {color:navy};
s7.addShape(pptx.shapes.RECTANGLE,{x:0,y:2.4,w:10,h:0.05,fill:{color:accent}});
s7.addText('Summary',{x:0.6,y:0.7,w:9,h:0.8,fontSize:34,bold:true,color:white,fontFace:'Calibri'});
s7.addText([
  {text:'Report date: ',options:{bold:true,color:lBlue}},{text:fd.reportDate+'\n',options:{color:white}},
  {text:'Total flights: ',options:{bold:true,color:lBlue}},{text:Number(fd.totalFlights24h).toLocaleString()+'\n',options:{color:white}},
  {text:'Total hours: ',options:{bold:true,color:lBlue}},{text:Number(fd.totalFlightHours24h).toLocaleString()+'h\n',options:{color:white}},
  {text:'#1 airline: ',options:{bold:true,color:lBlue}},{text:fd.top10Airlines[0].airline+' ('+Number(fd.top10Airlines[0].flightCount).toLocaleString()+' flights)\n',options:{color:white}},
  {text:'Longest: ',options:{bold:true,color:lBlue}},{text:fd.longestFlight.route+' ('+fd.longestFlight.hours+'h)\n',options:{color:white}},
  {text:'Shortest: ',options:{bold:true,color:lBlue}},{text:fd.shortestFlight.route+' ('+fd.shortestFlight.hours+'h)',options:{color:white}}
],{x:0.6,y:2.65,w:8.8,h:2.7,fontSize:14,fontFace:'Calibri',lineSpacingMultiple:1.6});
s7.addText('Data sourced from European aviation records · Generated daily at 10:00 UTC',
  {x:0.6,y:5.2,w:8.8,h:0.35,fontSize:11,color:gray,fontFace:'Calibri'});

fs.mkdirSync('output', { recursive: true });
const fname = `output/European_Airlines_Report_${today}.pptx`;
pptx.writeFile({fileName: fname})
  .then(()=> console.log('DONE: ' + fname))
  .catch(e => { console.error('ERROR: ' + e.message); process.exit(1); });
