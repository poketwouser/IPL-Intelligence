import pytest
import pandas as pd
from utils.analytics import classify_player_role, batting_summary, valid_ball_mask

@pytest.fixture
def sample_deliveries():
    data = [
        # Batter: V Kohli (faces 40 balls, scores 60 runs)
        # Bowler: JJ Bumrah (bowls 40 balls, takes 2 wickets)
        # All-rounder: SP Narine (faces 35 balls, scores 50 runs, bowls 35 balls, takes 2 wickets)
    ]
    # To keep it simple, we construct a dataframe matching what's needed
    rows = []
    
    # V Kohli batting
    for i in range(40):
        rows.append({"Match_Id": 1, "Inning": 1, "Batter": "V Kohli", "Bowler": "JJ Bumrah", 
                     "Batsman_Runs": 1, "Total_Runs": 1, "Is_Wicket": 0, "Player_Dismissed": None, "Extras_Type": None})
    
    # SP Narine batting
    for i in range(35):
        rows.append({"Match_Id": 2, "Inning": 1, "Batter": "SP Narine", "Bowler": "JJ Bumrah", 
                     "Batsman_Runs": 2, "Total_Runs": 2, "Is_Wicket": 0, "Player_Dismissed": None, "Extras_Type": None})
                     
    # SP Narine bowling
    for i in range(35):
        rows.append({"Match_Id": 2, "Inning": 2, "Batter": "V Kohli", "Bowler": "SP Narine", 
                     "Batsman_Runs": 1, "Total_Runs": 1, "Is_Wicket": 1 if i < 2 else 0, 
                     "Player_Dismissed": "V Kohli" if i < 2 else None, "Dismissal_Kind": "Caught" if i < 2 else None, "Extras_Type": None})
                     
    # JJ Bumrah bowling more
    for i in range(40):
        rows.append({"Match_Id": 3, "Inning": 1, "Batter": "V Kohli", "Bowler": "JJ Bumrah", 
                     "Batsman_Runs": 1, "Total_Runs": 1, "Is_Wicket": 1 if i < 2 else 0, 
                     "Player_Dismissed": "V Kohli" if i < 2 else None, "Dismissal_Kind": "Bowled" if i < 2 else None, "Extras_Type": None})
                     
    return pd.DataFrame(rows)


def test_valid_ball_mask(sample_deliveries):
    # Add a wide ball
    sample_deliveries.loc[0, "Extras_Type"] = "Wides"
    mask = valid_ball_mask(sample_deliveries)
    assert not mask.iloc[0]
    assert mask.iloc[1]


def test_classify_player_role(sample_deliveries):
    # V Kohli faces a lot of balls, bowls 0 -> Batter
    assert classify_player_role("V Kohli", sample_deliveries) == "Batter"
    
    # JJ Bumrah bowls a lot, faces 0 -> Bowler
    assert classify_player_role("JJ Bumrah", sample_deliveries) == "Bowler"
    
    # SP Narine faces 35 balls, bowls 35 balls -> All-rounder
    assert classify_player_role("SP Narine", sample_deliveries) == "All-rounder"


def test_batting_summary(sample_deliveries):
    stats = batting_summary("V Kohli", sample_deliveries)
    assert stats["balls"] == 40 + 35 + 40  # 115 balls
    assert stats["runs"] == 40 * 1 + 35 * 1 + 40 * 1 # 115 runs
    assert stats["sr"] == 100.0
