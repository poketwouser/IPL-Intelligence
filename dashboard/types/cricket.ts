// Type definitions for IPL Cricket data

export interface Match {
  Id: number;
  Season: number;
  Match_No: string;
  City: string;
  Date: string;
  Time: string;
  Match_Type: string;
  Player_Of_Match: string;
  Venue: string;
  Team1: string;
  Team2: string;
  Toss_Winner: string;
  Toss_Decision: string;
  Winner: string;
  Result: string;
  Result_Margin: number;
  Target_Runs: number;
  Target_Overs: number;
  Super_Over: string;
  Method: string;
  Umpire1: string;
  Umpire2: string;
}

export interface Delivery {
  mid: number; // Match_Id
  inn: number; // Inning
  bt: string;  // Batting_Team
  bot: string; // Bowling_Team
  o: number;   // Over
  b: number;   // Ball
  bat: string; // Batter
  bwl: string; // Bowler
  r: number;   // Batsman_Runs
  tr: number;  // Total_Runs
  et?: string; // Extras_Type
  w: number;   // Is_Wicket
  pd?: string; // Player_Dismissed
  dk?: string; // Dismissal_Kind
}

export interface VenueCoord {
  Venue: string;
  lat: number;
  lon: number;
  Home: string;
}

export interface TeamInfo {
  name: string;
  abbr: string;
  color: string;
  gradient: string;
}

export interface KPI {
  label: string;
  value: string | number;
  color: string;
  icon?: string;
  subtitle?: string;
}

export interface BattingSummary {
  innings: number;
  runs: number;
  balls: number;
  fours: number;
  sixes: number;
  strikeRate: number;
  boundaryPct: number;
  average: number;
  highScore: number;
  fifties: number;
  hundreds: number;
}

export interface BowlingSummary {
  innings: number;
  wickets: number;
  economy: number;
  strikeRate: number | string;
  dotPct: number;
  runsConceded: number;
  bestFigures: string;
}

export interface MatchupKPIs {
  balls: number;
  runs: number;
  sr: number;
  dots: number;
  dotPct: number;
  fours: number;
  sixes: number;
  dismissals: number;
  ballsPerDismissal: number | null;
}
