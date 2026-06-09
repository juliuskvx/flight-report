const PptxGenJS = require("pptxgenjs");
const fs = require("fs");

// Load real data from fetch_data.py output
const fd = JSON.parse(fs.readFileSync('output/flight_data.json', 'utf8'));
const today = fd.reportDate;

// Write date to env file for GitHub Actions
fs.appendFileSync(process.env.GITHUB_ENV || '/dev/null', `REPORT_DATE=${today}\n`);

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_16x9';
pptx.title = 'European Airlines Daily Report ' + today;

const navy='0A1628', blue='1B4F8A', accent='1E90D4', lBlue='D6EAFF',
      white='FFFFFF', offW='F4F7FA', gray='64748B', lgray='E2E8F0', text='1E293B';

// Slide 1: Title
const s1 = pptx.addSlide();
s1.background = {color:navy};
s1.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:0.4,h:5.625,fill:{color:accent}});
s1.addShape(pptx.shapes.RECTANGLE,{x:0,y:4.8,w:10,h:0.825,fill:{color:blue}});
s1.addText('European Airlines',{x:0.6,y:1.1,w:9,h:0.9,fontSize:40,bold:true,color:white,fontFace:'Calibri'});
s1.addText('Daily Flight Report',{x:0.6,y:2.05,w:9,h:0.7,fontSize:30,color:lBlue,fontFace:'Calibri'});
s1.addText('Top 10 Airlines  Â·  Live Operations  Â·  '+today,{x:0.6,y:2.9,w:9,h:0.45,fontSize:15,color:gray,fontFace:'Calibri'});
s1.addText('SOURCE: AVIATIONSTACK LIVE API  Â·  GENERATED 10:00 UTC',{x:0.6,y:4.92,w:8,h:0.35,fontSize:11,color:lBlue,fontFace:'Calibri',charSpacing:3});

// Slide 2: Key Metrics
const s2 = pptx.addSlide();
s2.background = {color:offW};
s2.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s2.addText('Key Metrics â€” Live European Airspace',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
const metrics=[
  {label:'Active flights tracked', value:Number(fd.totalFlights24h).toLocaleString(), col:blue},
  {label:'Total flight hours',     value:Number(fd.totalFlightHours24h).toLocaleString()+'h', col:accent},
  {label:'Airlines tracked',       value:''+fd.top10Airlines.length, col:'F59E0B'},
  {label:'Report date',            value:today, col:'10B981'}
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
  'Longest: '+fd.longestFlight.airline+' Â· '+fd.longestFlight.route+' ('+fd.longestFlight.hours+'h)   |   '+
  'Shortest: '+fd.shortestFlight.airline+' Â· '+fd.shortestFlight.route+' ('+fd.shortestFlight.hours+'h)',
  {x:0.5,y:4.35,w:9,h:0.8,fontSize:11,color:blue,fontFace:'Calibri',valign:'middle'});

// Slide 3: Flight count chart
const s3 = pptx.addSlide();
s3.background = {color:white};
s3.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s3.addText('Top 10 Airlines by Active Flight Count',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
s3.addImage({path:'output/chart_flights.png', x:0.2, y:0.85, w:9.6, h:4.65});

// Slide 4: Full data table
const s4 = pptx.addSlide();
s4.background = {color:white};
s4.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s4.addText('Full Airline Breakdown',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
const tRows=[
  ['#','Airline','Flights','Hours','Longest Route','Shortest Route']
    .map(h=>({text:h,options:{bold:true,color:white,fill:{color:navy},fontSize:10}})),
  ...fd.top10Airlines.map((a,i)=>[
    String(a.rank), a.airline,
    Number(a.flightCount).toLocaleString(),
    Number(a.totalFlightHours).toLocaleString()+'h',
    a.longestRoute, a.shortestRoute
  ].map(v=>({text:v,options:{color:text,fill:{color:i%2===0?white:offW},fontSize:9}})))
];
s4.addTable(tRows,{x:0.2,y:0.85,w:9.6,h:4.5,border:{pt:0.5,color:lgray},colW:[0.45,1.5,0.85,0.75,3.05,2.95]});

// Slide 5: Flight hours chart
const s5 = pptx.addSlide();
s5.background = {color:white};
s5.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:navy}});
s5.addText('Total Flight Hours by Airline',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
s5.addImage({path:'output/chart_hours.png', x:0.2, y:0.85, w:9.6, h:4.65});

// Slide 6: Route Spotlight
const s6 = pptx.addSlide();
s6.background = {color:navy};
s6.addShape(pptx.shapes.RECTANGLE,{x:0,y:0,w:10,h:0.75,fill:{color:blue}});
s6.addText('Route Spotlight â€” Longest & Shortest',{x:0.3,y:0.1,w:9,h:0.55,fontSize:18,bold:true,color:white,fontFace:'Calibri',valign:'middle'});
s6.addShape(pptx.shapes.RECTANGLE,{x:0.3,y:0.9,w:9.4,h:2.1,fill:{color:blue}});
s6.addText('LONGEST FLIGHT',{x:0.5,y:1.0,w:8.8,h:0.4,fontSize:11,color:lBlue,fontFace:'Calibri',charSpacing:2});
s6.addText(fd.longestFlight.airline,{x:0.5,y:1.45,w:8.8,h:0.55,fontSize:26,bold:true,color:white,fontFace:'Calibri'});
s6.addText(fd.longestFlight.route+' Â· '+fd.longestFlight.hours+' hours',{x:0.5,y:2.05,w:8.8,h:0.4,fontSize:14,color:lBlue,fontFace:'Calibri'});
s6.addShape(pptx.shapes.RECTANGLE,{x:0.3,y:3.15,w:9.4,h:2.1,fill:{color:accent}});
s6.addText('SHORTEST FLIGHT',{x:0.5,y:3.25,w:8.8,h:0.4,fontSize:11,color:white,fontFace:'Calibri',charSpacing:2});
s6.addText(fd.shortestFlight.airline,{x:0.5,y:3.7,w:8.8,h:0.55,fontSize:26,bold:true,color:white,fontFace:'Calibri'});
s6.addText(fd.shortestFlight.route+' Â· '+fd.shortestFlight.hours+' hours',{x:0.5,y:4.3,w:8.8,h:0.4,fontSize:14,color:white,fontFace:'Calibri'});

// Slide 7: Summary
const s7 = pptx.addSlide();
s7.background = {color:navy};
s7.addShape(pptx.shapes.RECTANGLE,{x:0,y:2.4,w:10,h:0.05,fill:{color:accent}});
s7.addText('Summary',{x:0.6,y:0.7,w:9,h:0.8,fontSize:34,bold:true,color:white,fontFace:'Calibri'});
s7.addText([
  {text:'Report date: ',options:{bold:true,color:lBlue}},{text:today+'\n',options:{color:white}},
  {text:'Active flights: ',options:{bold:true,color:lBlue}},{text:Number(fd.totalFlights24h).toLocaleString()+'\n',options:{color:white}},
  {text:'Total hours: ',options:{bold:true,color:lBlue}},{text:Number(fd.totalFlightHours24h).toLocaleString()+'h\n',options:{color:white}},
  {text:'#1 airline: ',options:{bold:true,color:lBlue}},{text:fd.top10Airlines[0].airline+' ('+Number(fd.top10Airlines[0].flightCount).toLocaleString()+' flights)\n',options:{color:white}},
  {text:'Longest: ',options:{bold:true,color:lBlue}},{text:fd.longestFlight.route+' ('+fd.longestFlight.hours+'h)\n',options:{color:white}},
  {text:'Shortest: ',options:{bold:true,color:lBlue}},{text:fd.shortestFlight.route+' ('+fd.shortestFlight.hours+'h)',options:{color:white}}
],{x:0.6,y:2.65,w:8.8,h:2.7,fontSize:14,fontFace:'Calibri',lineSpacingMultiple:1.6});
s7.addText('Data sourced from AviationStack Live API Â· Generated daily at 10:00 UTC',
  {x:0.6,y:5.2,w:8.8,h:0.35,fontSize:11,color:gray,fontFace:'Calibri'});

fs.mkdirSync('output', { recursive: true });
const fname = `output/European_Airlines_Report_${today}.pptx`;
pptx.writeFile({fileName: fname})
  .then(()=> console.log('DONE: ' + fname))
  .catch(e => { console.error('ERROR: ' + e.message); process.exit(1); });
