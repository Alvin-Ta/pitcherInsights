import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

const Stack = createNativeStackNavigator();

// ─── CONSTANTS ────────────────────────────────────────────────────

const MLB_API_BASE = "https://statsapi.mlb.com/api/v1";

const TEAM_ABBREVIATIONS = {
  108: "LAA", 109: "ARI", 110: "BAL", 111: "BOS", 112: "CHC",
  113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU",
  118: "KC",  119: "LAD", 120: "WSH", 121: "NYM", 133: "ATH",
  134: "PIT", 135: "SD",  136: "SEA", 137: "SF",  138: "STL",
  139: "TB",  140: "TEX", 141: "TOR", 142: "MIN", 143: "PHI",
  144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
};

// ─── HELPERS ──────────────────────────────────────────────────────

function toApiDate(date) {
  return date.toISOString().slice(0, 10);
}

function formatGameTime(gameDate) {
  if (!gameDate) return { time: "TBD", tz: "ET" };
  const formatter = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "America/New_York",
  });
  return { time: formatter.format(new Date(gameDate)), tz: "ET" };
}

function formatPitcherName(name) {
  if (!name) return "TBD";
  const parts = name.split(" ");
  if (parts.length < 2) return name;
  return `${parts[0][0]}. ${parts.slice(1).join(" ")}`;
}

function shortTeamName(name) {
  const replacements = {
    "Arizona Diamondbacks": "D-backs",   "Atlanta Braves": "Braves",
    "Boston Red Sox": "Red Sox",         "Chicago Cubs": "Cubs",
    "Chicago White Sox": "White Sox",    "Cincinnati Reds": "Reds",
    "Cleveland Guardians": "Guardians",  "Colorado Rockies": "Rockies",
    "Detroit Tigers": "Tigers",          "Houston Astros": "Astros",
    "Kansas City Royals": "Royals",      "Los Angeles Angels": "Angels",
    "Los Angeles Dodgers": "Dodgers",    "Miami Marlins": "Marlins",
    "Milwaukee Brewers": "Brewers",      "Minnesota Twins": "Twins",
    "New York Mets": "Mets",             "New York Yankees": "Yankees",
    "Philadelphia Phillies": "Phillies", "Pittsburgh Pirates": "Pirates",
    "San Diego Padres": "Padres",        "San Francisco Giants": "Giants",
    "Seattle Mariners": "Mariners",      "St. Louis Cardinals": "Cardinals",
    "Tampa Bay Rays": "Rays",            "Texas Rangers": "Rangers",
    "Toronto Blue Jays": "Blue Jays",    "Washington Nationals": "Nationals",
    "Athletics": "Athletics",
  };
  return replacements[name] || name;
}

function mapGameToMatch(game) {
  const away = game.teams.away;
  const home = game.teams.home;
  const { time, tz } = formatGameTime(game.gameDate);
  return {
    id: game.gamePk,
    awayTeam: shortTeamName(away.team.name),
    awayAbbr: TEAM_ABBREVIATIONS[away.team.id] || away.team.abbreviation || "",
    awayPitcher: formatPitcherName(away.probablePitcher?.fullName),
    homeTeam: shortTeamName(home.team.name),
    homeAbbr: TEAM_ABBREVIATIONS[home.team.id] || home.team.abbreviation || "",
    homePitcher: formatPitcherName(home.probablePitcher?.fullName),
    time,
    tz,
    awayTeamScore: away.score,
    homeTeamScore: home.score,
    venue: game.venue?.name || "Venue TBD",
    status: game.status?.detailedState.toLowerCase() === "in progress"
      ? "Live"
      : "View Analysis",
  };
}

async function fetchSchedule(date) {
  const params = new URLSearchParams({
    sportId: "1",
    date,
    hydrate: "probablePitcher,team",
  });
  const response = await fetch(`${MLB_API_BASE}/schedule?${params.toString()}`);
  if (!response.ok) throw new Error(`Schedule request failed: ${response.status}`);
  const data = await response.json();
  return (data.dates?.[0]?.games || []).map(mapGameToMatch);
}

// ─── MATCH CARD ───────────────────────────────────────────────────

function MatchCard({ match, selected, onPress }) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.card,
        selected && styles.cardSelected,
        pressed && styles.cardPressed,
      ]}
      onPress={onPress}
    >
      <View style={styles.matchRow}>
        <View style={styles.teamLeft}>
          <Text style={styles.abbr}>{match.awayAbbr}</Text>
          <Text style={styles.teamName} numberOfLines={1}>{match.awayTeam}</Text>
          <Text style={styles.pitcher} numberOfLines={1}>{match.awayPitcher}</Text>
        </View>

        {match.status === "Live" ? (
          <View style={styles.timeBlock}>
            <Text style={styles.liveScore}>{match.awayTeamScore}</Text>
            <Text style={styles.scoreDash}>–</Text>
            <Text style={styles.liveScore}>{match.homeTeamScore}</Text>
          </View>
        ) : (
          <View style={styles.timeBlock}>
            <Text style={styles.vsLabel}>VS</Text>
            <Text style={styles.time}>{match.time}</Text>
            <Text style={styles.tz}>{match.tz}</Text>
          </View>
        )}

        <View style={styles.teamRight}>
          <Text style={styles.abbr}>{match.homeAbbr}</Text>
          <Text style={styles.teamName} numberOfLines={1}>{match.homeTeam}</Text>
          <Text style={styles.pitcher} numberOfLines={1}>{match.homePitcher}</Text>
        </View>
      </View>

      <View style={styles.footer}>
        <Text style={styles.venue} numberOfLines={1}>{match.venue}</Text>
        <Text style={[
          styles.status,
          match.status === "Live" && styles.statusLive,
        ]}>{match.status}</Text>
      </View>
    </Pressable>
  );
}

// ─── SCHEDULE SCREEN ──────────────────────────────────────────────

function ScheduleScreen({ navigation }) {
  const [matches, setMatches]     = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]         = useState(null);

  const date = useMemo(() => toApiDate(new Date()), []);

  const loadSchedule = useCallback(async ({ refresh = false } = {}) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setError(null);
    try {
      const nextMatches = await fetchSchedule(date);
      setMatches(nextMatches);
      setSelectedId((cur) => cur || nextMatches[0]?.id || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [date]);

  useEffect(() => { loadSchedule(); }, [loadSchedule]);

  const handleCardPress = (match) => {
    setSelectedId(match.id);
    // Pass the full match object to the detail screen
    navigation.navigate("GameDetail", { match });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <ScrollView
        contentContainerStyle={styles.wrapper}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => loadSchedule({ refresh: true })}
            tintColor="#d0d0e8"
          />
        }
      >
        <View style={styles.container}>
          <Text style={styles.heading}>Upcoming Matches · {date}</Text>

          {loading && (
            <View style={styles.stateBlock}>
              <ActivityIndicator color="#d0d0e8" />
              <Text style={styles.stateText}>Loading schedule</Text>
            </View>
          )}

          {!loading && error && (
            <View style={styles.stateBlock}>
              <Text style={styles.errorText}>{error}</Text>
              <Pressable style={styles.retryButton} onPress={() => loadSchedule()}>
                <Text style={styles.retryText}>Retry</Text>
              </Pressable>
            </View>
          )}

          {!loading && !error && matches.length === 0 && (
            <View style={styles.stateBlock}>
              <Text style={styles.stateText}>No MLB games scheduled.</Text>
            </View>
          )}

          {!loading && !error && matches.map((match) => (
            <MatchCard
              key={match.id}
              match={match}
              selected={selectedId === match.id}
              onPress={() => handleCardPress(match)}
            />
          ))}

          {!loading && !error && matches.length > 0 && (
            <View style={styles.dots}>
              {matches.slice(0, 8).map((match) => (
                <Pressable
                  key={match.id}
                  style={[styles.dot, selectedId === match.id && styles.dotActive]}
                  onPress={() => handleCardPress(match)}
                />
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

// ─── PITCHER SELECTOR ────────────────────────────────────────────

function PitcherSelector({ match, selected, onSelect }) {
  // Options are the two actual pitchers from the game
  const options = [
    { key: "away", label: match.awayPitcher, abbr: match.awayAbbr },
    { key: "home", label: match.homePitcher, abbr: match.homeAbbr },
  ];

  return (
    <View style={styles.segmentTrack}>
      {options.map((option) => {
        const isActive = selected === option.key;
        return (
          <Pressable
            key={option.key}
            style={[styles.segmentButton, isActive && styles.activeButton]}
            onPress={() => onSelect(option.key)}
          >
            {/* Team abbreviation above name — helps distinguish at a glance */}
            <Text style={[styles.segmentAbbr, isActive && styles.segmentAbbrActive]}>
              {option.abbr}
            </Text>
            <Text
              style={[styles.segmentText, isActive && styles.activeText]}
              numberOfLines={1}
            >
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

// ─── GAME DETAIL SCREEN ───────────────────────────────────────────

function GameDetailScreen({ route }) {
  const { match } = route.params;

  // Track which pitcher is selected — "away" or "home"
  // Default to whichever is pitching (away starts, so "away" is a safe default)
  const [selectedPitcher, setSelectedPitcher] = useState("away");

  // Derive the currently selected pitcher's display data
  const activePitcher = selectedPitcher === "away"
    ? { name: match.awayPitcher, abbr: match.awayAbbr, team: match.awayTeam }
    : { name: match.homePitcher, abbr: match.homeAbbr, team: match.homeTeam };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.detailWrapper}>

        {/* Scoreboard */}
        <View style={styles.scoreCard}>
          <View style={styles.scoreTeam}>
            <Text style={styles.scoreAbbr}>{match.awayAbbr}</Text>
            <Text style={styles.scoreNum}>
              {match.status === "Live" ? match.awayTeamScore : "–"}
            </Text>
          </View>

          <View style={styles.scoreMid}>
            <Text style={styles.scoreInning}>
              {match.status === "Live" ? "LIVE" : match.time}
            </Text>
            <Text style={styles.scoreSep}>·</Text>
            <Text style={styles.scoreVenue} numberOfLines={1}>
              {match.venue}
            </Text>
          </View>

          <View style={styles.scoreTeam}>
            <Text style={styles.scoreAbbr}>{match.homeAbbr}</Text>
            <Text style={styles.scoreNum}>
              {match.status === "Live" ? match.homeTeamScore : "–"}
            </Text>
          </View>
        </View>

        {/* Pitcher selector */}
        <PitcherSelector
          match={match}
          selected={selectedPitcher}
          onSelect={setSelectedPitcher}
        />

        {/* Active pitcher display */}
        <View style={styles.activePitcherCard}>
          <Text style={styles.activePitcherLabel}>{activePitcher.abbr} · Starting pitcher</Text>
          <Text style={styles.activePitcherName}>{activePitcher.name}</Text>
        </View>

        {/* Placeholder — replace with your analytics components */}
        <View style={styles.placeholder}>
          <Text style={styles.placeholderTitle}>
            {activePitcher.name} analytics
          </Text>
          <Text style={styles.placeholderSub}>
            Live insights · Velocity trends · Expected vs actual · Fatigue indicator
          </Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

// ─── ROOT ─────────────────────────────────────────────────────────

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: "#111118" },
          headerTintColor: "#ffffff",
          headerTitleStyle: { fontWeight: "700", fontSize: 15 },
          headerShadowVisible: false,
          contentStyle: { backgroundColor: "#111118" },
        }}
      >
        <Stack.Screen
          name="Schedule"
          component={ScheduleScreen}
          options={{ headerShown: false }}     // keeps your existing full-screen look
        />
        <Stack.Screen
          name="GameDetail"
          component={GameDetailScreen}
          options={({ route }) => ({
            title: `${route.params.match.awayAbbr} @ ${route.params.match.homeAbbr}`,
            headerBackTitle: "Schedule",
          })}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

// ─── STYLES ───────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#111118",
  },

  // ── Schedule screen
  wrapper: {
    minHeight: "100%",
    backgroundColor: "#111118",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16,
    paddingVertical: 24,
  },
  container: {
    width: "100%",
    maxWidth: 420,
  },
  heading: {
    color: "#9191a8",
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 1.3,
    textTransform: "uppercase",
    marginBottom: 14,
    paddingLeft: 2,
  },
  card: {
    backgroundColor: "#1c1c28",
    borderRadius: 16,
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.04)",
  },
  cardSelected: {
    backgroundColor: "#22223a",
    borderColor: "rgba(124,92,232,0.36)",
  },
  cardPressed: {
    opacity: 0.88,
  },
  matchRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginBottom: 16,
  },
  teamLeft: {
    flex: 1,
    alignItems: "flex-start",
    minWidth: 0,
  },
  teamRight: {
    flex: 1,
    alignItems: "flex-end",
    minWidth: 0,
  },
  abbr: {
    color: "#9191a8",
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 0.7,
    textTransform: "uppercase",
    marginBottom: 1,
  },
  teamName: {
    color: "#ffffff",
    fontSize: 22,
    fontWeight: "700",
    lineHeight: 25,
    marginBottom: 4,
    maxWidth: "100%",
  },
  pitcher: {
    color: "#c5c5d8",
    fontSize: 13,
    fontWeight: "500",
    maxWidth: "100%",
  },
  timeBlock: {
    width: 78,
    alignItems: "center",
    gap: 2,
  },
  vsLabel: {
    color: "#55556a",
    fontSize: 10,
    fontWeight: "600",
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  time: {
    color: "#d0d0e8",
    fontSize: 17,
    fontWeight: "700",
    lineHeight: 22,
  },
  tz: {
    color: "#55556a",
    fontSize: 10,
    fontWeight: "500",
    letterSpacing: 0.4,
  },
  liveScore: {
    color: "#ffffff",
    fontSize: 22,
    fontWeight: "800",
  },
  scoreDash: {
    color: "#55556a",
    fontSize: 16,
    fontWeight: "500",
  },
  footer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
  },
  venue: {
    flex: 1,
    color: "#55556a",
    fontSize: 12,
    fontWeight: "400",
  },
  status: {
    color: "#8f7dff",
    fontSize: 11,
    fontWeight: "600",
  },
  statusLive: {
    color: "#ff3b30",
  },
  dots: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 6,
    marginTop: 18,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#33334a",
  },
  dotActive: {
    backgroundColor: "#7c5ce8",
  },
  stateBlock: {
    backgroundColor: "#1c1c28",
    borderRadius: 16,
    padding: 20,
    alignItems: "center",
    gap: 10,
  },
  stateText: {
    color: "#9191a8",
    fontSize: 13,
  },
  errorText: {
    color: "#ffb0b0",
    fontSize: 13,
    textAlign: "center",
  },
  retryButton: {
    backgroundColor: "#7c5ce8",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  retryText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "700",
  },

  // ── Pitcher selector
  segmentTrack: {
    flexDirection: "row",
    backgroundColor: "#13131f",
    borderRadius: 14,
    padding: 4,
    borderWidth: 0.5,
    borderColor: "rgba(255,255,255,0.05)",
  },
  segmentButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 8,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 10,
    gap: 2,
  },
  activeButton: {
    backgroundColor: "#22223a",
  },
  segmentAbbr: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.7,
    textTransform: "uppercase",
    color: "rgba(255,255,255,0.2)",
  },
  segmentAbbrActive: {
    color: "#8f7dff",
  },
  segmentText: {
    fontSize: 13,
    fontWeight: "600",
    color: "rgba(255,255,255,0.4)",
  },
  activeText: {
    color: "#ffffff",
  },
  activePitcherCard: {
    backgroundColor: "#1c1c28",
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: "rgba(124,92,232,0.2)",
    gap: 4,
  },
  activePitcherLabel: {
    color: "#8f7dff",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.7,
    textTransform: "uppercase",
  },
  activePitcherName: {
    color: "#ffffff",
    fontSize: 20,
    fontWeight: "800",
    letterSpacing: -0.3,
  },

  // ── Game detail screen
  detailWrapper: {
    padding: 16,
    gap: 12,
  },
  scoreCard: {
    backgroundColor: "#1c1c28",
    borderRadius: 18,
    padding: 20,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)",
  },
  scoreTeam: {
    alignItems: "center",
    gap: 4,
  },
  scoreAbbr: {
    color: "#9191a8",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  scoreNum: {
    color: "#ffffff",
    fontSize: 44,
    fontWeight: "900",
    letterSpacing: -2,
    lineHeight: 48,
  },
  scoreMid: {
    alignItems: "center",
    gap: 2,
    flex: 1,
    paddingHorizontal: 8,
  },
  scoreInning: {
    color: "#d0d0e8",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.6,
    textTransform: "uppercase",
  },
  scoreSep: {
    color: "#33334a",
    fontSize: 18,
  },
  scoreVenue: {
    color: "#55556a",
    fontSize: 11,
    textAlign: "center",
  },
  pitcherRow: {
    flexDirection: "row",
    gap: 8,
  },
  pitcherChip: {
    flex: 1,
    backgroundColor: "#1c1c28",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    gap: 4,
  },
  pitcherChipLabel: {
    color: "#55556a",
    fontSize: 10,
    fontWeight: "600",
    letterSpacing: 0.6,
    textTransform: "uppercase",
  },
  pitcherChipName: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "700",
  },
  placeholder: {
    backgroundColor: "#1c1c28",
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderColor: "rgba(124,92,232,0.2)",
    marginTop: 4,
  },
  placeholderTitle: {
    color: "#8f7dff",
    fontSize: 14,
    fontWeight: "700",
  },
  placeholderSub: {
    color: "#55556a",
    fontSize: 12,
    textAlign: "center",
    lineHeight: 18,
  },
});