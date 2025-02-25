def initialize():
    # Connect to database
    db = connect_to_database()
    
    # Load data structures
    players = query_players_table(db)  # Map player_id -> player data
    teams = query_teams_table(db)      # Map team_id -> team data
    
    # Build lookup dictionaries
    player_teams = {}      # player_name -> team_id
    last_name_map = {}     # last_name -> list of player_ids
    first_name_map = {}    # first_name -> list of player_ids
    nicknames = {}         # nickname -> list of player_ids
    team_lookup = {}       # various team names -> team_id
    
    # Populate dictionaries from player and team data
    for each player:
        add to appropriate dictionaries
        
    for each team:
        add to team_lookup dictionary
        
    # Add known nicknames manually or from a separate table
    add_known_nicknames_to_dictionary()

def find_players_in_text(text):
    # 1. Check for team mentions first
    mentioned_teams = find_team_mentions(text)
    
    matched_players = {}  # player_id -> confidence score
    
    # 2. First pass: Direct name matching
    for word in extract_words(text):
        if word in last_name_map:
            add_players_to_matches(last_name_map[word], score=80)
        if word in first_name_map:
            add_players_to_matches(first_name_map[word], score=70)
        if word in nicknames:
            add_players_to_matches(nicknames[word], score=90)
    
    # 3. Second pass: Fuzzy matching for misspelled names
    fuzzy_matches = fuzzy_match_players(text)
    for each match, score in fuzzy_matches:
        if score > THRESHOLD:
            add_player_to_matches(match, score)
    
    # 4. Apply team context if available
    if mentioned_teams:
        for player_id in matched_players:
            if player_team[player_id] in mentioned_teams:
                matched_players[player_id] += 20  # Boost score
    
    # 5. Resolve ambiguous cases
    if has_ambiguous_matches(matched_players):
        resolve_ambiguities(matched_players, mentioned_teams)
    
    # 6. Return results
    sorted_matches = sort_by_confidence(matched_players)
    
    if highest_confidence > 85:
        return [highest_confidence_match]  # Return just the best match
    elif llm_available:
        # Use LLM to disambiguate
        return llm_disambiguation(sorted_matches[:5], text)
    else:
        return sorted_matches[:5]  # Return top 5 matches

def process_player_mention(text, llm_service=None):
    # Main function for external API
    
    # 1. Check for team mentions
    teams = find_team_mentions(text)
    
    # 2. If teams found, get roster for context
    roster_context = ""
    if teams:
        roster_context = get_team_rosters(teams)
    
    # 3. Find player mentions
    players = find_players_in_text(text)
    
    # 4. Handle results based on confidence
    if not players:
        return None
    elif players[0].confidence > 85:
        return players[0]  # High confidence match
    elif multiple_matches and llm_service:
        # Use LLM for disambiguation
        context = format_player_context(players, roster_context)
        llm_result = llm_service.query(text, context)
        return process_llm_result(llm_result, players)
    else:
        # Return best match with note about confidence
        return players[0]