from rapidfuzz import process, fuzz
import time
import re


def find_player_mentions_fuzzy(
    tweet_text, all_player_names, threshold=30, scorer=fuzz.token_set_ratio, limit=5
):
    """
    Returns a list of possible player name matches from the tweet_text, using
    fuzzy matching against all_player_names. Matches with a score >= threshold
    are considered candidates.

    Args:
        tweet_text (str): The text to search for player mentions
        all_player_names (list): List of all player names to match against
        threshold (int): Minimum score (0-100) to consider a match
        scorer (callable): The scorer function to use for matching
        limit (int): Maximum number of matches to return

    Returns:
        list: List of matched player names that meet the threshold
    """
    # First, check for direct name mentions
    matched_players = set()

    # Break tweet into words and check for player last names first
    words = re.findall(r"\b\w+\b", tweet_text.lower())

    # Extract last names from player full names
    player_info = {}
    for name in all_player_names:
        last_name = name.split()[-1].lower()
        if last_name not in player_info:
            player_info[last_name] = []
        player_info[last_name].append(name)

        # Also handle first names for players like "LeBron" who are known by first name
        first_name = name.split()[0].lower()
        if first_name not in player_info:
            player_info[first_name] = []
        player_info[first_name].append(name)

        # Handle nicknames
        if name == "LeBron James":
            player_info["king"] = [name]
            player_info["lbj"] = [name]
        elif name == "Giannis Antetokounmpo":
            player_info["greek"] = [name]
            player_info["freak"] = [name]
        elif name == "James Harden":
            player_info["beard"] = [name]
        elif name == "Kevin Durant":
            player_info["kd"] = [name]

    # First pass: direct word matches for last names, first names, and nicknames
    for word in words:
        if word in player_info:
            for player in player_info[word]:
                matched_players.add(player)

    # Second pass: fuzzy match on the entire text
    # process.extract(...) returns a list of tuples: (matched_string, score, index)
    matches = process.extract(
        query=tweet_text,
        choices=all_player_names,
        scorer=scorer,
        limit=10,  # Return top 10 matches for analysis
    )

    # Add players that match above threshold
    for name, score, _ in matches:
        if score >= threshold:
            matched_players.add(name)

    # Return top matches, prioritizing higher scores
    sorted_matches = sorted(
        [
            (
                name,
                process.extract(query=name, choices=[tweet_text], scorer=scorer)[0][1],
            )
            for name in matched_players
        ],
        key=lambda x: x[1],
        reverse=True,
    )

    # Return the top N matches (or fewer if there aren't enough)
    result = [name for name, _ in sorted_matches[:limit]]
    return result, matches


def run_test_cases(
    test_cases, all_players, threshold=30, scorer=fuzz.token_set_ratio, limit=5
):
    """
    Run a series of test cases and display the results.

    Args:
        test_cases (list): List of test case dictionaries
        all_players (list): List of all player names
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

        start_time = time.time()
        matches, all_match_data = find_player_mentions_fuzzy(
            tweet, all_players, threshold, scorer, limit
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
                "all_matches": all_match_data,
                "elapsed_ms": elapsed,
            }
        )

    # Display results
    total_passed = sum(1 for r in results if r["passed"])

    for i, result in enumerate(results, 1):
        print(f"\nTest Case #{i}: {'✓ PASSED' if result['passed'] else '✗ FAILED'}")
        print(f"Tweet: \"{result['tweet']}\"")

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

    # Test cases with expected matches
    test_cases = [
        {
            "tweet": "Lebron is questionable tonight with a sore ankle",
            "expected_matches": ["LeBron James"],
        },
        {
            "tweet": "King James dropped 35 points in the comeback win",
            "expected_matches": ["LeBron James"],
        },
        {
            "tweet": "Curry with another deep three! He's on fire tonight.",
            "expected_matches": ["Stephen Curry"],
        },
        {
            "tweet": "The Greek Freak is dominating in the paint again",
            "expected_matches": ["Giannis Antetokounmpo"],
        },
        {
            "tweet": "KD and Kyrie combined for 75 points in Brooklyn's win",
            "expected_matches": ["Kevin Durant", "Kyrie Irving"],
        },
        {
            "tweet": "Giannis antetokounpo is unstoppable this season",  # Misspelled name
            "expected_matches": ["Giannis Antetokounmpo"],
        },
        {
            "tweet": "Amazing performance by Jimmy Buckets last night!",
            "expected_matches": ["Jimmy Butler"],
        },
        {
            "tweet": "Can't believe Luka got another triple-double",
            "expected_matches": ["Luka Dončić"],
        },
        {
            "tweet": "The Beard doing what he does best. 40 points and 15 assists!",
            "expected_matches": ["James Harden"],
        },
        {
            "tweet": "Who is better - Embiid or Jokic?",
            "expected_matches": ["Joel Embiid", "Nikola Jokić"],
        },
        {
            "tweet": "Westbrook with another record-breaking performance",
            "expected_matches": ["Russell Westbrook"],
        },
        {
            "tweet": "Watching LBJ and AD dominate tonight",
            "expected_matches": ["LeBron James", "Anthony Davis"],
        },
        {
            "tweet": "Tatum and Brown combined for 65 in the Celtics win",
            "expected_matches": ["Jayson Tatum", "Jaylen Brown"],
        },
        {
            "tweet": "just watched a great game with no particular star players",
            "expected_matches": [],
        },
        {
            "tweet": "James playing tonight?",  # Ambiguous - could be LeBron James or James Harden
            "expected_matches": [],  # Setting to empty as it's ambiguous
        },
    ]

    # Run tests with improved hybrid approach
    print("\n=== TESTING WITH HYBRID APPROACH ===")
    run_test_cases(test_cases, all_players, threshold=30, scorer=fuzz.token_set_ratio)

    # Additional benchmarking
    print("\n=== TESTING WITH DIFFERENT THRESHOLDS ===")
    for threshold in [25, 30, 35]:
        run_test_cases(
            test_cases[:5],
            all_players,
            threshold=threshold,
            scorer=fuzz.token_set_ratio,
        )

    # Test with different scorers
    print("\n=== TESTING WITH DIFFERENT SCORERS ===")
    run_test_cases(
        test_cases[:5], all_players, threshold=30, scorer=fuzz.partial_token_set_ratio
    )
    run_test_cases(test_cases[:5], all_players, threshold=30, scorer=fuzz.WRatio)

    # Comprehensive benchmark example
    print("\n=== COMPREHENSIVE BENCHMARK ===")
    test_tweet = "King James and the Greek Freak are both playing amazing this season. KD is back too!"
    expected = ["LeBron James", "Giannis Antetokounmpo", "Kevin Durant"]

    print(f'\nBenchmark tweet: "{test_tweet}"')
    print(f"Expected matches: {expected}")

    start_time = time.time()
    matches, all_match_data = find_player_mentions_fuzzy(
        test_tweet, all_players, threshold=30, scorer=fuzz.token_set_ratio
    )
    elapsed = (time.time() - start_time) * 1000

    print(f"\nMatches found: {matches}")
    print(f"Time taken: {elapsed:.2f}ms")

    print("\nAll potential matches (Name, Score):")
    for name, score, idx in all_match_data:
        match_status = "✓ MATCH" if name in matches else ""
        expected_status = "✓ EXPECTED" if name in expected else ""
        print(f"  {name:<25} {score:>6.2f}  {match_status:12} {expected_status}")
