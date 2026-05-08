const fs = require('fs');
const path = require('path');

function parseCSV(content) {
  const lines = content.split('\n').filter(l => l.trim());
  if (lines.length === 0) return [];
  
  // Parse header
  const headers = parseCSVLine(lines[0]);
  const rows = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    if (values.length !== headers.length) continue;
    const row = {};
    headers.forEach((h, idx) => {
      let val = values[idx];
      // Try numeric conversion
      if (val !== '' && val !== undefined && !isNaN(val) && val !== null) {
        val = Number(val);
      }
      row[h] = val;
    });
    rows.push(row);
  }
  return rows;
}

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

const dataDir = path.join(__dirname, '..', '..', 'data', 'cleaned');
const outDir = path.join(__dirname, '..', 'public', 'data');

// Short key mapping for deliveries
const DEL_MAP = {
  'Match_Id': 'mid',
  'Inning': 'inn',
  'Batting_Team': 'bt',
  'Bowling_Team': 'bot',
  'Over': 'o',
  'Ball': 'b',
  'Batter': 'bat',
  'Bowler': 'bwl',
  'Batsman_Runs': 'r',
  'Total_Runs': 'tr',
  'Extras_Type': 'et',
  'Is_Wicket': 'w',
  'Player_Dismissed': 'pd',
  'Dismissal_Kind': 'dk'
};

const ESSENTIAL_COLS = new Set(Object.keys(DEL_MAP));

// Convert matches
console.log('Converting matches.csv...');
const matchesRaw = fs.readFileSync(path.join(dataDir, 'matches.csv'), 'utf-8');
const matches = parseCSV(matchesRaw);
fs.writeFileSync(path.join(outDir, 'matches.json'), JSON.stringify(matches));
console.log(`  ${matches.length} matches converted`);

// Convert deliveries (optimized)
console.log('Converting deliveries.csv (optimizing for size)...');
const deliveriesRaw = fs.readFileSync(path.join(dataDir, 'deliveries.csv'), 'utf-8');
const deliveriesLines = deliveriesRaw.split('\n').filter(l => l.trim());
const delHeaders = parseCSVLine(deliveriesLines[0]);
const optimizedDeliveries = [];

for (let i = 1; i < deliveriesLines.length; i++) {
  const values = parseCSVLine(deliveriesLines[i]);
  if (values.length !== delHeaders.length) continue;
  const row = {};
  delHeaders.forEach((h, idx) => {
    if (ESSENTIAL_COLS.has(h)) {
      let val = values[idx];
      if (val === '' || val === undefined || val === null) return;
      if (!isNaN(val)) val = Number(val);
      row[DEL_MAP[h]] = val;
    }
  });
  optimizedDeliveries.push(row);
}

fs.writeFileSync(path.join(outDir, 'deliveries.json'), JSON.stringify(optimizedDeliveries));
console.log(`  ${optimizedDeliveries.length} deliveries optimized and converted`);

// Convert venue coords
console.log('Converting venue_coords.csv...');
const venueRaw = fs.readFileSync(path.join(dataDir, 'venue_coords.csv'), 'utf-8');
const venues = parseCSV(venueRaw);
fs.writeFileSync(path.join(outDir, 'venue_coords.json'), JSON.stringify(venues));
console.log(`  ${venues.length} venues converted`);

console.log('Done!');
