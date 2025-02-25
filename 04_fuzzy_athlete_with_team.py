from rapidfuzz import process, fuzz
import time
import re


def find_player_mentions_fuzzy(
    tweet_text,
    all_player_names,
    player_teams,
    team_info,
    threshold=30,
    scorer=fuzz.token_set_ratio,
    limit=5,
):
    """
    Returns a list of possible player name matches from the tweet_text, using
    fuzzy matching against all_player_names with team context awareness.

    Args:
        tweet_text (str): The text to search for player mentions
        all_player_names (list): List of all player names to match against
        player_teams (dict): Mapping of player names to their team codes
        team_info (dict): Information about teams (nicknames, locations, etc.)
        threshold (int): Minimum score (0-100) to consider a match
        scorer (callable): The scorer function to use for matching
        limit (int): Maximum number of matches to return

    Returns:
        list: List of matched player names that meet the threshold
        list: All potential matches with scores
    """
    # First, check for teams mentioned in the tweet
    mentioned_teams = find_team_mentions(tweet_text, team_info)
    team_boost = 20  # Score boost for players on mentioned teams

    # Initialize for player matching
    matched_players = set()
    player_scores = {}

    # Break tweet into words and check for player last names first
    words = re.findall(r"\b\w+\b", tweet_text.lower())

    # Extract last names from player full names and build nickname dictionary
    player_info = {}
    nicknames = {}

    for name in all_player_names:
        # Handle last names
        last_name = name.split()[-1].lower()
        if last_name not in player_info:
            player_info[last_name] = []
        player_info[last_name].append(name)

        # Handle first names
        first_name = name.split()[0].lower()
        if first_name not in player_info:
            player_info[first_name] = []
        player_info[first_name].append(name)

        # Add common nicknames and abbreviations
        if name == "LeBron James":
            nicknames["king"] = [name]
            nicknames["lebron"] = [name]
            nicknames["lbj"] = [name]
            nicknames["king james"] = [name]
        elif name == "Giannis Antetokounmpo":
            nicknames["greek"] = [name]
            nicknames["freak"] = [name]
            nicknames["greek freak"] = [name]
            nicknames["giannis"] = [name]
        elif name == "James Harden":
            nicknames["beard"] = [name]
            nicknames["the beard"] = [name]
        elif name == "Kevin Durant":
            nicknames["kd"] = [name]
            nicknames["slim reaper"] = [name]
            nicknames["durantula"] = [name]
        elif name == "Stephen Curry":
            nicknames["steph"] = [name]
            nicknames["chef curry"] = [name]
        elif name == "Anthony Davis":
            nicknames["ad"] = [name]
            nicknames["the brow"] = [name]
        elif name == "Luka Dončić":
            nicknames["luka"] = [name]
            nicknames["wonder boy"] = [name]
            nicknames["doncic"] = [name]
        elif name == "Russell Westbrook":
            nicknames["russ"] = [name]
            nicknames["brodie"] = [name]
            nicknames["westbrook"] = [name]
        elif name == "Jimmy Butler":
            nicknames["jimmy buckets"] = [name]
        elif name == "Kyrie Irving":
            nicknames["kyrie"] = [name]
            nicknames["uncle drew"] = [name]

    # Look for nickname matches in the tweet
    for nickname, players in nicknames.items():
        if nickname in tweet_text.lower():
            for player in players:
                matched_players.add(player)
                player_scores[player] = 90  # High confidence for nickname matches

    # Look for words that match player names
    for word in words:
        if word in player_info:
            for player in player_info[word]:
                matched_players.add(player)
                player_scores[player] = player_scores.get(
                    player, 80
                )  # High confidence for direct matches

    # Look for consecutive words that match player names
    for i in range(len(words) - 1):
        two_words = words[i] + " " + words[i + 1]
        if two_words in nicknames:
            for player in nicknames[two_words]:
                matched_players.add(player)
                player_scores[player] = 90

    # Second pass: fuzzy match on the entire text
    all_matches = process.extract(
        query=tweet_text, choices=all_player_names, scorer=scorer, limit=10
    )
    # print(all_matches)

    # Add players that match above threshold from fuzzy matching
    for name, score, _ in all_matches:
        if score >= threshold:
            matched_players.add(name)
            # If already matched by a direct name, keep the higher score
            player_scores[name] = max(player_scores.get(name, 0), score)

    # Apply team context boost
    if mentioned_teams:
        for player in matched_players:
            if player in player_teams:
                player_team = player_teams[player]
                if player_team in mentioned_teams:
                    player_scores[player] += team_boost

    # Sort by confidence score
    sorted_matches = sorted(
        [(name, player_scores.get(name, 0)) for name in matched_players],
        key=lambda x: x[1],
        reverse=True,
    )

    # Handle ambiguous cases (like "James" which could be LeBron or Harden)
    # If team context is available, use it to resolve
    if len(sorted_matches) > 1 and mentioned_teams:
        for i, (player, score) in enumerate(sorted_matches):
            # Check if this is an ambiguous case (e.g., same last name)
            same_name_players = []
            last_name = player.split()[-1].lower()

            for other_player, other_score in sorted_matches:
                if (
                    other_player != player
                    and other_player.split()[-1].lower() == last_name
                ):
                    same_name_players.append(other_player)

            if same_name_players:
                # If player's team is mentioned, boost their score significantly
                if player in player_teams and player_teams[player] in mentioned_teams:
                    player_scores[player] += 30

                # Also decrease score of other players with same last name if their team isn't mentioned
                for other_player in same_name_players:
                    if (
                        other_player in player_teams
                        and player_teams[other_player] not in mentioned_teams
                    ):
                        player_scores[other_player] -= 10

        # Re-sort after adjusting scores
        sorted_matches = sorted(
            [(name, player_scores.get(name, 0)) for name in matched_players],
            key=lambda x: x[1],
            reverse=True,
        )

    # Return the top matches limited by the limit parameter
    result = [name for name, _ in sorted_matches[:limit]]
    return result, all_matches


def find_team_mentions(tweet_text, team_info):
    """
    Find mentions of NBA teams in the tweet text.

    Args:
        tweet_text (str): The tweet text to analyze
        team_info (dict): Dictionary of team information

    Returns:
        list: List of team codes found in the tweet
    """
    mentioned_teams = set()
    lower_tweet = tweet_text.lower()

    # Check for each team's various names
    for team_code, info in team_info.items():
        # Check full team name (e.g., "Los Angeles Lakers")
        if info["full_name"].lower() in lower_tweet:
            mentioned_teams.add(team_code)
            continue

        # Check location (e.g., "Los Angeles")
        if info["location"].lower() in lower_tweet:
            # Additional check to disambiguate shared locations (LA has two teams)
            if info["location"].lower() == "los angeles":
                # Check if specifically Lakers or Clippers is mentioned
                if "lakers" in lower_tweet:
                    mentioned_teams.add("LAL")
                    continue
                elif "clippers" in lower_tweet:
                    mentioned_teams.add("LAC")
                    continue
                # If just "LA" or "Los Angeles", add both teams
                mentioned_teams.add(team_code)
            else:
                mentioned_teams.add(team_code)
            continue

        # Check nickname (e.g., "Lakers")
        if info["nickname"].lower() in lower_tweet:
            mentioned_teams.add(team_code)
            continue

        # Check abbreviation (e.g., "LAL")
        if team_code.lower() in lower_tweet:
            mentioned_teams.add(team_code)
            continue

        # Check alternate names and common references
        for alt_name in info.get("alternates", []):
            if alt_name.lower() in lower_tweet:
                mentioned_teams.add(team_code)
                break

    return mentioned_teams


def run_test_cases(
    test_cases,
    all_players,
    player_teams,
    team_info,
    threshold=30,
    scorer=fuzz.token_set_ratio,
    limit=5,
):
    """
    Run a series of test cases and display the results.

    Args:
        test_cases (list): List of test case dictionaries
        all_players (list): List of all player names
        player_teams (dict): Mapping of player names to their team codes
        team_info (dict): Information about teams
        threshold (int): Score threshold for matching
        scorer (callable): Scoring function to use
        limit (int): Maximum number of matches to return
    """
    print(f"\n{'='*80}")
    print(
        f"FUZZY MATCHING TEST RESULTS (Threshold: {threshold}, Scorer: {scorer.__name__}, Limit: {limit})"
    )
    print(f"{'='*80}")

    results = []

    for i, test in enumerate(test_cases, 1):
        tweet = test["tweet"]
        expected = set(test.get("expected_matches", []))

        # Find team mentions first for debugging
        mentioned_teams = find_team_mentions(tweet, team_info)

        start_time = time.time()
        matches, all_match_data = find_player_mentions_fuzzy(
            tweet, all_players, player_teams, team_info, threshold, scorer, limit
        )
        elapsed = (time.time() - start_time) * 1000  # convert to ms

        # Determine if test passed
        actual_set = set(matches)
        passed = all(name in actual_set for name in expected)

        results.append(
            {
                "id": i,
                "passed": passed,
                "tweet": tweet,
                "expected": expected,
                "actual": actual_set,
                "teams_mentioned": mentioned_teams,
                "all_matches": all_match_data,
                "elapsed_ms": elapsed,
            }
        )

    # Display results
    total_passed = sum(1 for r in results if r["passed"])

    for i, result in enumerate(results, 1):
        print(f"\nTest Case #{i}: {'✓ PASSED' if result['passed'] else '✗ FAILED'}")
        print(f"Tweet: \"{result['tweet']}\"")

        if result["teams_mentioned"]:
            print(f"Teams Mentioned: {result['teams_mentioned']}")

        print("\nAll potential matches (Name, Score, Index):")
        for name, score, idx in result["all_matches"]:
            match_status = ""
            if name in result["actual"]:
                if name in result["expected"]:
                    match_status = "✓ CORRECT MATCH"
                else:
                    match_status = "! FALSE POSITIVE"
            elif name in result["expected"]:
                match_status = "! FALSE NEGATIVE"

            print(f"  {name:<25} {score:>6.2f}  {idx:>3}  {match_status}")

        if not result["passed"]:
            print("\nExpected:", sorted(list(result["expected"])))
            print("Actual:  ", sorted(list(result["actual"])))

        print(f"Time: {result['elapsed_ms']:.2f}ms")
        print("-" * 80)

    print(
        f"\nSummary: {total_passed}/{len(results)} tests passed ({total_passed/len(results)*100:.1f}%)"
    )
    return results


if __name__ == "__main__":
    # Expanded list of players
    all_players = [
        "LeBron James",
        "Stephen Curry",
        "Kevin Durant",
        "Giannis Antetokounmpo",
        "James Harden",
        "Anthony Davis",
        "Nikola Jokić",
        "Luka Dončić",
        "Joel Embiid",
        "Jayson Tatum",
        "Damian Lillard",
        "Jimmy Butler",
        "Kawhi Leonard",
        "Kyrie Irving",
        "Devin Booker",
        "Paul George",
        "Ja Morant",
        "Zion Williamson",
        "Trae Young",
        "Donovan Mitchell",
        "Bam Adebayo",
        "Jaylen Brown",
        "Rudy Gobert",
        "Karl-Anthony Towns",
        "Draymond Green",
        "Russell Westbrook",
        "Chris Paul",
        "Klay Thompson",
        "Ben Simmons",
    ]

    # Player to team mapping (as of early 2023 - would need updates for trades)
    player_teams = {
        "LeBron James": "LAL",
        "Anthony Davis": "LAL",
        "Stephen Curry": "GSW",
        "Klay Thompson": "GSW",
        "Draymond Green": "GSW",
        "Kevin Durant": "PHX",
        "Giannis Antetokounmpo": "MIL",
        "James Harden": "PHI",
        "Joel Embiid": "PHI",
        "Ben Simmons": "BKN",
        "Kyrie Irving": "DAL",
        "Luka Dončić": "DAL",
        "Nikola Jokić": "DEN",
        "Jayson Tatum": "BOS",
        "Jaylen Brown": "BOS",
        "Jimmy Butler": "MIA",
        "Bam Adebayo": "MIA",
        "Kawhi Leonard": "LAC",
        "Paul George": "LAC",
        "Devin Booker": "PHX",
        "Chris Paul": "PHX",
        "Damian Lillard": "MIL",
        "Ja Morant": "MEM",
        "Zion Williamson": "NOP",
        "Trae Young": "ATL",
        "Donovan Mitchell": "CLE",
        "Rudy Gobert": "MIN",
        "Karl-Anthony Towns": "MIN",
        "Russell Westbrook": "LAC",
    }

    # Team information including names, locations, and alternate references
    team_info = {
        "ATL": {
            "full_name": "Atlanta Hawks",
            "location": "Atlanta",
            "nickname": "Hawks",
            "alternates": ["ATL", "The Hawks"],
        },
        "BOS": {
            "full_name": "Boston Celtics",
            "location": "Boston",
            "nickname": "Celtics",
            "alternates": ["BOS", "The Celtics", "The C's"],
        },
        "BKN": {
            "full_name": "Brooklyn Nets",
            "location": "Brooklyn",
            "nickname": "Nets",
            "alternates": ["BKN", "The Nets"],
        },
        "CHA": {
            "full_name": "Charlotte Hornets",
            "location": "Charlotte",
            "nickname": "Hornets",
            "alternates": ["CHA", "The Hornets"],
        },
        "CHI": {
            "full_name": "Chicago Bulls",
            "location": "Chicago",
            "nickname": "Bulls",
            "alternates": ["CHI", "The Bulls"],
        },
        "CLE": {
            "full_name": "Cleveland Cavaliers",
            "location": "Cleveland",
            "nickname": "Cavaliers",
            "alternates": ["CLE", "The Cavs", "Cavaliers", "The Cavaliers"],
        },
        "DAL": {
            "full_name": "Dallas Mavericks",
            "location": "Dallas",
            "nickname": "Mavericks",
            "alternates": ["DAL", "The Mavs", "Mavs", "The Mavericks"],
        },
        "DEN": {
            "full_name": "Denver Nuggets",
            "location": "Denver",
            "nickname": "Nuggets",
            "alternates": ["DEN", "The Nuggets"],
        },
        "DET": {
            "full_name": "Detroit Pistons",
            "location": "Detroit",
            "nickname": "Pistons",
            "alternates": ["DET", "The Pistons"],
        },
        "GSW": {
            "full_name": "Golden State Warriors",
            "location": "Golden State",
            "nickname": "Warriors",
            "alternates": ["GSW", "The Warriors", "Golden State", "Dubs"],
        },
        "HOU": {
            "full_name": "Houston Rockets",
            "location": "Houston",
            "nickname": "Rockets",
            "alternates": ["HOU", "The Rockets"],
        },
        "IND": {
            "full_name": "Indiana Pacers",
            "location": "Indiana",
            "nickname": "Pacers",
            "alternates": ["IND", "The Pacers"],
        },
        "LAC": {
            "full_name": "Los Angeles Clippers",
            "location": "Los Angeles",
            "nickname": "Clippers",
            "alternates": ["LAC", "The Clippers", "LA Clippers", "The LA Clippers"],
        },
        "LAL": {
            "full_name": "Los Angeles Lakers",
            "location": "Los Angeles",
            "nickname": "Lakers",
            "alternates": ["LAL", "The Lakers", "LA Lakers", "The LA Lakers"],
        },
        "MEM": {
            "full_name": "Memphis Grizzlies",
            "location": "Memphis",
            "nickname": "Grizzlies",
            "alternates": ["MEM", "The Grizzlies", "Grizz"],
        },
        "MIA": {
            "full_name": "Miami Heat",
            "location": "Miami",
            "nickname": "Heat",
            "alternates": ["MIA", "The Heat"],
        },
        "MIL": {
            "full_name": "Milwaukee Bucks",
            "location": "Milwaukee",
            "nickname": "Bucks",
            "alternates": ["MIL", "The Bucks"],
        },
        "MIN": {
            "full_name": "Minnesota Timberwolves",
            "location": "Minnesota",
            "nickname": "Timberwolves",
            "alternates": ["MIN", "The Timberwolves", "Wolves", "T-Wolves"],
        },
        "NOP": {
            "full_name": "New Orleans Pelicans",
            "location": "New Orleans",
            "nickname": "Pelicans",
            "alternates": ["NOP", "The Pelicans", "Pels"],
        },
        "NYK": {
            "full_name": "New York Knicks",
            "location": "New York",
            "nickname": "Knicks",
            "alternates": ["NYK", "The Knicks"],
        },
        "OKC": {
            "full_name": "Oklahoma City Thunder",
            "location": "Oklahoma City",
            "nickname": "Thunder",
            "alternates": ["OKC", "The Thunder"],
        },
        "ORL": {
            "full_name": "Orlando Magic",
            "location": "Orlando",
            "nickname": "Magic",
            "alternates": ["ORL", "The Magic"],
        },
        "PHI": {
            "full_name": "Philadelphia 76ers",
            "location": "Philadelphia",
            "nickname": "76ers",
            "alternates": ["PHI", "The 76ers", "Sixers", "The Sixers"],
        },
        "PHX": {
            "full_name": "Phoenix Suns",
            "location": "Phoenix",
            "nickname": "Suns",
            "alternates": ["PHX", "The Suns"],
        },
        "POR": {
            "full_name": "Portland Trail Blazers",
            "location": "Portland",
            "nickname": "Trail Blazers",
            "alternates": ["POR", "The Trail Blazers", "Blazers", "The Blazers"],
        },
        "SAC": {
            "full_name": "Sacramento Kings",
            "location": "Sacramento",
            "nickname": "Kings",
            "alternates": ["SAC", "The Kings"],
        },
        "SAS": {
            "full_name": "San Antonio Spurs",
            "location": "San Antonio",
            "nickname": "Spurs",
            "alternates": ["SAS", "The Spurs"],
        },
        "TOR": {
            "full_name": "Toronto Raptors",
            "location": "Toronto",
            "nickname": "Raptors",
            "alternates": ["TOR", "The Raptors", "Raps"],
        },
        "UTA": {
            "full_name": "Utah Jazz",
            "location": "Utah",
            "nickname": "Jazz",
            "alternates": ["UTA", "The Jazz"],
        },
        "WAS": {
            "full_name": "Washington Wizards",
            "location": "Washington",
            "nickname": "Wizards",
            "alternates": ["WAS", "The Wizards"],
        },
    }

    # Test cases with expected matches
    test_cases = [
        {
            "tweet": "Lebron is questionable tonight with a sore ankle",
            "expected_matches": ["LeBron James"],
        },
        # {
        #     "tweet": "King James dropped 35 points in the comeback win",
        #     "expected_matches": ["LeBron James"],
        # },
        # {
        #     "tweet": "Curry with another deep three! He's on fire tonight.",
        #     "expected_matches": ["Stephen Curry"],
        # },
        # {
        #     "tweet": "The Greek Freak is dominating in the paint again",
        #     "expected_matches": ["Giannis Antetokounmpo"],
        # },
        # {
        #     "tweet": "KD and Kyrie combined for 75 points in Brooklyn's win",
        #     "expected_matches": ["Kevin Durant", "Kyrie Irving"],
        # },
        # {
        #     "tweet": "Giannis antetokounpo is unstoppable this season",  # Misspelled name
        #     "expected_matches": ["Giannis Antetokounmpo"],
        # },
        # {
        #     "tweet": "Amazing performance by Jimmy Buckets last night!",
        #     "expected_matches": ["Jimmy Butler"],
        # },
        # {
        #     "tweet": "Can't believe Luka got another triple-double",
        #     "expected_matches": ["Luka Dončić"],
        # },
        # {
        #     "tweet": "The Beard doing what he does best. 40 points and 15 assists!",
        #     "expected_matches": ["James Harden"],
        # },
        # {
        #     "tweet": "Who is better - Embiid or Jokic?",
        #     "expected_matches": ["Joel Embiid", "Nikola Jokić"],
        # },
        # {
        #     "tweet": "Westbrook with another record-breaking performance",
        #     "expected_matches": ["Russell Westbrook"],
        # },
        # {
        #     "tweet": "Watching LBJ and AD dominate tonight",
        #     "expected_matches": ["LeBron James", "Anthony Davis"],
        # },
        # {
        #     "tweet": "Tatum and Brown combined for 65 in the Celtics win",
        #     "expected_matches": ["Jayson Tatum", "Jaylen Brown"],
        # },
        # {
        #     "tweet": "just watched a great game with no particular star players",
        #     "expected_matches": [],
        # },
        # {
        #     "tweet": "James playing tonight?",  # Ambiguous
        #     "expected_matches": [],  # Setting to empty as it's ambiguous
        # },
        # # New test cases with team context
        # {
        #     "tweet": "James scored 30 in the Lakers win over the Knicks",
        #     "expected_matches": ["LeBron James"],  # Should be LeBron, not Harden
        # },
        # {
        #     "tweet": "James had a triple-double in the Sixers game",
        #     "expected_matches": ["James Harden"],  # Should be Harden, not LeBron
        # },
        # {
        #     "tweet": "AD went off for 40 points for LA",
        #     "expected_matches": ["Anthony Davis"],
        # },
        # {
        #     "tweet": "Warriors win as Curry and Klay combine for 60 points",
        #     "expected_matches": ["Stephen Curry", "Klay Thompson"],
        # },
        # {
        #     "tweet": "Mitchell scored 35 for the Cavs in the win over Atlanta",
        #     "expected_matches": ["Donovan Mitchell"],
        # },
    ]

    # Run tests with improved hybrid approach and team context
    print("\n=== TESTING WITH HYBRID APPROACH AND TEAM CONTEXT ===")
    run_test_cases(
        test_cases,
        all_players,
        player_teams,
        team_info,
        threshold=30,
        scorer=fuzz.token_set_ratio,
    )

    # Comprehensive benchmark example
    print("\n=== COMPREHENSIVE BENCHMARK WITH TEAM CONTEXT ===")
    test_tweet = "James scored 32 points as the Lakers beat the Bucks, while Giannis had 30 for Milwaukee"
    expected = ["LeBron James", "Giannis Antetokounmpo"]

    print(f'\nBenchmark tweet: "{test_tweet}"')
    print(f"Expected matches: {expected}")

    # First check team mentions
    mentioned_teams = find_team_mentions(test_tweet, team_info)
    print(f"Teams mentioned: {mentioned_teams}")

    start_time = time.time()
    matches, all_match_data = find_player_mentions_fuzzy(
        test_tweet,
        all_players,
        player_teams,
        team_info,
        threshold=30,
        scorer=fuzz.token_set_ratio,
    )
    elapsed = (time.time() - start_time) * 1000

    print(f"\nMatches found: {matches}")
    print(f"Time taken: {elapsed:.2f}ms")

    print("\nAll potential matches (Name, Score):")
    for name, score, idx in all_match_data[:10]:
        match_status = "✓ MATCH" if name in matches else ""
        expected_status = "✓ EXPECTED" if name in expected else ""
        print(f"  {name:<25} {score:>6.2f}  {match_status:12} {expected_status}")
